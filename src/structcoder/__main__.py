"""CLI-Einstiegspunkt (Requirements Abschnitt 9.3).

`run` und `report` werden in AP3/AP4 implementiert; dieser Stub stellt nur
die Kommandostruktur bereit, damit `python -m structcoder --help` funktioniert.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="structcoder")
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        raise NotImplementedError("run wird in AP3 implementiert")
    if args.command == "report":
        raise NotImplementedError("report wird in AP4 implementiert")
    return 1


if __name__ == "__main__":
    sys.exit(main())
