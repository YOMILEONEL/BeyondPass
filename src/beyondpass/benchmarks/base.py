"""Task-Datenmodell (Requirements Abschnitt 8.1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """Eine einzelne Benchmark-Aufgabe.

    `reference_solution` darf niemals an Planner- oder Coder-Agent
    weitergereicht werden (INV-1, siehe Requirements Abschnitt 5.3).
    """

    task_id: str
    prompt: str
    test_code: str
    reference_solution: str
    entry_point: str
