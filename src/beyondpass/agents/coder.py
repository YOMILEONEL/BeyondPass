"""Coder-Agent (FR-301 bis FR-306).

Sieht Aufgaben-Prompt, Loesungsplan und ab dem zweiten Versuch das
Feedback zum vorherigen Code -- niemals die Referenzloesung (FR-305, INV-1).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from beyondpass.agents.llm_client import LLMClient
from beyondpass.benchmarks.base import Task
from beyondpass.prompts import load_template

_INITIAL_TEMPLATE = load_template("coder_initial.txt")
_RETRY_TEMPLATE = load_template("coder_retry.txt")
_CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


@dataclass
class CoderAttempt:
    code: str
    feedback_text: str


def extract_code(text: str) -> str:
    """Extrahiert reinen Python-Code aus der LLM-Antwort (FR-303)."""
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def try_parse_error(code: str) -> str | None:
    """None wenn `code` gueltiges Python ist, sonst die SyntaxError-Meldung (FR-304)."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return str(exc)


def preserves_signature(code: str, entry_point: str) -> bool:
    """Prueft, ob `entry_point` weiterhin als Funktionsname vorkommt (FR-306, Soll)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
        for node in ast.walk(tree)
    )


def run_coder(
    task: Task, plan: str, history: list[CoderAttempt], llm: LLMClient
) -> tuple[str, int, int]:
    """Generiert Kandidat-Code fuer die aktuelle Iteration (FR-301 bis FR-303).

    Gibt (code, tokens_in, tokens_out) zurueck. `history` enthaelt die
    bisherigen Versuche dieser Aufgabe (FR-302); ist sie leer, wird der
    Initial-Prompt verwendet, sonst der Retry-Prompt mit dem letzten Versuch.
    """
    if not history:
        user_prompt = _INITIAL_TEMPLATE.format(prompt=task.prompt, plan=plan)
    else:
        last = history[-1]
        user_prompt = _RETRY_TEMPLATE.format(
            prompt=task.prompt, previous_code=last.code, feedback_text=last.feedback_text
        )

    response = llm.complete(system="", user=user_prompt)
    code = extract_code(response.text)
    return code, response.tokens_in, response.tokens_out
