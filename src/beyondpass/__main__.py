"""CLI-Einstiegspunkt (Requirements Abschnitt 9.3)."""

from __future__ import annotations

import argparse
import logging
import sys


def _configure_logging(level: str, force: bool = False) -> None:
    """Strukturiertes Logging mit Log-Level (NFR-09).

    Konfiguriert bewusst nur den `beyondpass`-Logger-Namespace, nicht den
    Root-Logger (`logging.basicConfig`) -- sonst wuerden Drittanbieter-
    Bibliotheken (httpx, huggingface_hub, urllib3, ...) bei INFO/DEBUG ihre
    eigene, sehr geschwaetzige HTTP-Logs mit ausgeben.
    """
    beyondpass_logger = logging.getLogger("beyondpass")
    if force:
        beyondpass_logger.handlers.clear()
    if not beyondpass_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
        beyondpass_logger.addHandler(handler)
    beyondpass_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    beyondpass_logger.propagate = False


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser fuer `run` und `report` (Requirements Abschnitt 9.3)."""
    parser = argparse.ArgumentParser(prog="beyondpass")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fuehrt einen Evaluationslauf aus")
    run_parser.add_argument("--mode", choices=["baseline", "structural"], default="structural")
    run_parser.add_argument("--benchmark", choices=["humaneval", "mbpp"], default="humaneval")
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
    from beyondpass.benchmarks.mbpp import load_mbpp
    from beyondpass.config import load_settings

    loaders = {"humaneval": load_humaneval, "mbpp": load_mbpp}
    load_tasks = loaders[args.benchmark]

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

    _configure_logging(settings.output.log_level, force=True)

    if settings.llm.provider != "anthropic":
        raise NotImplementedError(
            f"LLM-Provider '{settings.llm.provider}' wird noch nicht unterstuetzt"
        )

    tasks = load_tasks(limit=settings.benchmark.limit, task_ids=settings.benchmark.task_ids)

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


def _expand_run_patterns(patterns: list[str]) -> list:
    import glob as glob_module
    from pathlib import Path

    paths: list[Path] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            matched = sorted(Path(p) for p in glob_module.glob(pattern))
            if not matched:
                raise FileNotFoundError(f"Kein Run passt zu Muster: {pattern}")
            paths.extend(matched)
        else:
            paths.append(Path(pattern))
    return paths


def _report_command(args: argparse.Namespace) -> int:
    from pathlib import Path

    from beyondpass.reporting.aggregate import compare_conditions, render_markdown
    from beyondpass.reporting.plots import plot_comparison

    paths = _expand_run_patterns(args.runs)
    comparison = compare_conditions(paths)
    markdown = render_markdown(comparison)

    out_path = Path(args.out) if args.out else Path("results") / "summary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    plot_path = out_path.with_suffix(".png")
    plot_comparison(comparison, plot_path)

    print(markdown)
    print(f"Diagramm: {plot_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstiegspunkt; `argv=None` liest von `sys.argv` (fuer Tests explizit uebergeben)."""
    _configure_logging("INFO")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_command(args)
    if args.command == "report":
        return _report_command(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
