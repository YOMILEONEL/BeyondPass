"""CLI-Einstiegspunkt (Requirements Abschnitt 9.3).

`report` wird erst in AP4 implementiert.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="beyondpass")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fuehrt einen Evaluationslauf aus")
    run_parser.add_argument("--mode", choices=["baseline", "structural"], default="structural")
    run_parser.add_argument("--benchmark", default="humaneval")
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--model", default=None)
    run_parser.add_argument("--max-iterations", type=int, default=None)
    run_parser.add_argument("--seed", type=int, default=None)
    run_parser.add_argument("--out", default=None)

    report_parser = subparsers.add_parser("report", help="Wertet vorhandene Runs aus")
    report_parser.add_argument("--runs", nargs="+", required=True)
    report_parser.add_argument("--out", default=None)

    return parser


def _run_command(args: argparse.Namespace) -> int:
    from pathlib import Path

    from beyondpass import orchestrator
    from beyondpass.agents.llm_client import AnthropicLLMClient, CostTracker
    from beyondpass.benchmarks.humaneval import load_humaneval
    from beyondpass.config import load_settings

    if args.benchmark != "humaneval":
        raise NotImplementedError(f"Benchmark '{args.benchmark}' wird noch nicht unterstuetzt")

    settings = load_settings()
    settings.run.mode = args.mode
    if args.max_iterations is not None:
        settings.run.max_iterations = args.max_iterations
    if args.seed is not None:
        settings.run.seed = args.seed
    if args.model is not None:
        settings.llm.model = args.model
    if args.limit is not None:
        settings.benchmark.limit = args.limit

    if settings.llm.provider != "anthropic":
        raise NotImplementedError(
            f"LLM-Provider '{settings.llm.provider}' wird noch nicht unterstuetzt"
        )

    tasks = load_humaneval(limit=settings.benchmark.limit, task_ids=settings.benchmark.task_ids)

    cost_tracker = CostTracker(model=settings.llm.model, max_usd=settings.budget.max_usd)
    llm = AnthropicLLMClient(
        model=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
        max_retries=settings.llm.max_retries,
        cost_tracker=cost_tracker,
    )

    out_path = Path(args.out) if args.out else Path(settings.output.results_dir) / "run.jsonl"
    orchestrator.run(settings, tasks, llm, out_path)
    print(f"Fertig. Geschaetzte Kosten: ${cost_tracker.total_usd:.4f}. Ergebnisse: {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_command(args)
    if args.command == "report":
        raise NotImplementedError("report wird in AP4 implementiert")
    return 1


if __name__ == "__main__":
    sys.exit(main())
