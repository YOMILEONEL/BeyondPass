"""Critic-Agent (FR-701 bis FR-706).

Einziger Agent, der die Referenzloesung sieht (Komponentenverantwort-
lichkeiten, Requirements Abschnitt 5.3). Berechnet die vier Metriken aus
AP2, leitet daraus eine Diagnose ab und flaggt Trivial-/Suspicious-Faelle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beyondpass.benchmarks.base import Task
from beyondpass.config import DiagnosisConfig
from beyondpass.feedback.diagnosis import DiagnosisCategory, diagnose
from beyondpass.feedback.trivial import uses_any_argument
from beyondpass.metrics import MetricResult, all_metrics


@dataclass
class CriticResult:
    """Ergebnis einer Critic-Bewertung: Metriken, Diagnose-Kategorie und Flags."""

    metrics: MetricResult
    diagnosis: DiagnosisCategory
    flags: list[str] = field(default_factory=list)


def run_critic(
    task: Task,
    candidate_code: str,
    bss: int,
    syntax_error: bool,
    thresholds: DiagnosisConfig,
) -> CriticResult:
    """Berechnet Metriken + Diagnose fuer einen Kandidaten (FR-701, FR-702)."""
    metrics = all_metrics(task.reference_program, candidate_code)
    category = diagnose(
        bss=bss,
        pos=metrics.pos,
        pps=metrics.pps,
        pss=metrics.pss,
        pes=metrics.pes,
        syntax_error=syntax_error,
        thresholds=thresholds,
    )

    flags: list[str] = []
    if bss == 1:
        if not uses_any_argument(candidate_code, task.entry_point):
            flags.append("TRIVIAL")
        if metrics.pos < thresholds.suspicious_pos:
            flags.append("SUSPICIOUS")

    return CriticResult(metrics=metrics, diagnosis=category, flags=flags)
