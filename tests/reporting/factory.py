"""Baut synthetische IterationResult-JSONL-Dateien fuer die Report-Tests.

Kein LLM-Call, kein Docker noetig -- reine Datei-Fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path


def make_row(
    task_id: str,
    iteration: int,
    mode: str,
    bss: int,
    pos: float,
    pps: float,
    pss: float,
    pes: float,
    flags: list[str] | None = None,
    tokens_in: int = 100,
    tokens_out: int = 50,
) -> dict:
    return {
        "task_id": task_id,
        "iteration": iteration,
        "mode": mode,
        "plan": "1. Do it." if iteration == 1 else None,
        "candidate_code": "def f():\n    pass\n",
        "bss": bss,
        "tests_passed": bss,
        "tests_total": 1,
        "error_message": None if bss == 1 else "AssertionError",
        "pos": pos,
        "pps": pps,
        "pss": pss,
        "pes": pes,
        "diagnosis": "SUCCESS" if bss == 1 else "GENERIC_FAIL",
        "feedback_text": None if bss == 1 else "Die Tests schlagen fehl: ...",
        "flags": flags or [],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "duration_s": 1.0,
    }


def default_two_task_rows(mode: str, solved_pos: float = 0.9) -> list[dict]:
    """T/0 wird sofort geloest (mit TRIVIAL-Flag), T/1 bleibt nach 2 Iterationen ungeloest."""
    return [
        make_row(
            "T/0", 1, mode, bss=1, pos=solved_pos, pps=0.9, pss=0.9, pes=1.0, flags=["TRIVIAL"]
        ),
        make_row("T/1", 1, mode, bss=0, pos=0.3, pps=0.2, pss=0.1, pes=0.2),
        make_row("T/1", 2, mode, bss=0, pos=0.5, pps=0.3, pss=0.2, pes=0.3),
    ]


def write_run_file(
    path: Path, rows: list[dict], mode: str, seed: int, model: str = "claude-haiku-4-5"
) -> Path:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    meta = {
        "run_id": f"test-{seed}",
        "created_at": "2026-08-27T00:00:00+00:00",
        "config": {"run": {"mode": mode, "seed": seed}, "llm": {"model": model}},
    }
    path.with_suffix(".meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return path
