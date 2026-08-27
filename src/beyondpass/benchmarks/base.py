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

    @property
    def reference_program(self) -> str:
        """Vollstaendiges, eigenstaendig parsbares Referenzprogramm.

        `reference_solution` (HumanEval's `canonical_solution`) ist nur der
        eingerueckte Funktionskoerper und fuer sich genommen kein gueltiges
        Python. Fuer den AST-Tokenizer (AP2) wird die Signatur aus `prompt`
        vorangestellt.
        """
        return self.prompt + self.reference_solution
