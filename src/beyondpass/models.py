"""Datenmodell fuer Iterationsergebnisse (Requirements Abschnitt 8.2)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class IterationResult:
    task_id: str
    iteration: int
    mode: str
    plan: str | None
    candidate_code: str
    bss: int
    tests_passed: int
    tests_total: int
    error_message: str | None
    pos: float
    pps: float
    pss: float
    pes: float
    diagnosis: str
    feedback_text: str | None
    flags: list[str] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    duration_s: float = 0.0

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
