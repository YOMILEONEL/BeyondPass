"""Planner-Agent (FR-201 bis FR-205).

Sieht ausschliesslich den Aufgaben-Prompt, niemals die Referenzloesung
(INV-1, siehe Requirements Abschnitt 5.3 und Komponentenverantwortlichkeiten).
"""

from __future__ import annotations

from beyondpass.agents.llm_client import LLMClient
from beyondpass.benchmarks.base import Task
from beyondpass.prompts import load_template

_TEMPLATE = load_template("planner.txt")
_CODE_MARKERS = ("```", "\ndef ")


class PlannerCodeLeakError(RuntimeError):
    """Der Planner hat entgegen der Anweisung Code statt eines Plans geliefert (FR-203)."""


def run_planner(task: Task, llm: LLMClient) -> tuple[str, int, int]:
    """Erzeugt einen Loesungsplan in natuerlicher Sprache (FR-201, FR-202).

    Gibt (plan_text, tokens_in, tokens_out) zurueck.

    TODO (FR-205, Kann-Ziel): bei niedrigem POS in Iteration >= 2 koennte
    der Planner erneut aufgerufen werden (Neuplanung) -- noch nicht
    implementiert.
    """
    user_prompt = _TEMPLATE.format(prompt=task.prompt)
    response = llm.complete(system="", user=user_prompt)

    if any(marker in response.text for marker in _CODE_MARKERS):
        raise PlannerCodeLeakError("Planner-Antwort enthaelt Code statt eines Loesungsplans")

    return response.text, response.tokens_in, response.tokens_out
