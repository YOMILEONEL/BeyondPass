"""MBPP-Loader (FR-105, Kann-Ziel): zweiter Benchmark ueber dieselbe
`Task`-Schnittstelle wie HumanEval (Adapter-Muster).

MBPP liefert anders als HumanEval keine getrennte Signatur/Body-Struktur
und keinen `check(candidate)`-Wrapper: `code` ist eine vollstaendige
Funktion, und `test_list` sind direkte `assert`-Aufrufe gegen den
Funktionsnamen. Um Task.prompt/reference_solution im selben Format wie
HumanEval zu halten (Signatur+Docstring im Prompt, nur der Body als
Referenzloesung), wird die erste Zeile von `code` als Signatur abgetrennt.

Annahme: die Funktionssignatur passt auf eine Zeile (bei MBPP durchgaengig
der Fall).

Anders als bei HumanEval sind MBPPs Asserts bereits diskret und
unabhaengig -- das generierte `test_code` fuehrt deshalb jeden Assert
einzeln in einem try/except aus, zaehlt bestandene/gesamt und gibt eine
Marker-Zeile aus, die `sandbox/docker_runner.py` zusaetzlich (rein additiv,
ohne bestehendes Verhalten zu aendern) parst, um partielle Korrektheit zu
protokollieren (FR-406). Die BSS-Semantik bleibt exakt gleich: Exit-Code 0
genau dann, wenn alle Asserts bestanden wurden.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable

from datasets import load_dataset

from beyondpass.benchmarks.base import Task

DATASET_NAME = "google-research-datasets/mbpp"
DATASET_CONFIG = "full"


def _split_signature_and_body(code: str) -> tuple[str, str, str, str, str]:
    """Trennt `code` in (Preamble, Signaturzeile, Body, Name, Body-Einrueckung).

    `code` beginnt gelegentlich mit Modul-Level-Statements vor der Funktion
    (typischerweise Imports, z. B. `from collections import Counter`), die
    auch die Referenzloesung braucht -- deshalb landen sie in `prompt` statt
    stillschweigend zu verschwinden.
    """
    tree = ast.parse(code)
    func = next(
        (node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))),
        None,
    )
    if func is None:
        raise ValueError("Kein Funktionsname im MBPP-Referenzcode gefunden")

    lines = code.splitlines(keepends=True)
    preamble = "".join(lines[: func.lineno - 1])
    signature_line = lines[func.lineno - 1]
    body_lines = lines[func.lineno :]
    body_source = "".join(body_lines)

    # Manche MBPP-Loesungen nutzen Tabs statt Leerzeichen. Eine hartkodierte
    # Einrueckung fuer die eingefuegte Docstring-Zeile wuerde dann zu einem
    # TabError fuehren -- also die tatsaechliche Einrueckung des Bodys uebernehmen.
    indent_match = re.match(r"[ \t]*", body_lines[0]) if body_lines else None
    indent = indent_match.group(0) if indent_match and indent_match.group(0) else "    "

    return preamble, signature_line, body_source, func.name, indent


_TESTS_MARKER = "@@BEYONDPASS_TESTS@@"


def _build_test_code(test_setup_code: str, test_list: list[str]) -> str:
    """Baut ein Skript, das jeden Assert einzeln zaehlt statt beim ersten
    Fehlschlag abzubrechen (FR-406), aber dieselbe BSS-Semantik behaelt:
    Exit-Code 0 genau dann, wenn alle Asserts bestanden wurden.

    Jeder Assert-String wird per `exec` ausgefuehrt (im selben Modul-
    Namensraum wie Kandidat-Code und `test_setup_code`, da alles zu einem
    gemeinsamen Skript zusammengefuegt wird). `repr(test_list)` erzeugt ein
    sicheres, wieder einlesbares Python-Listenliteral, unabhaengig von
    Anfuehrungszeichen/Escapes in den einzelnen Assert-Strings.
    """
    setup = f"{test_setup_code}\n" if test_setup_code.strip() else ""
    return (
        f"{setup}"
        "__bp_total__ = 0\n"
        "__bp_passed__ = 0\n"
        f"for __bp_stmt__ in {test_list!r}:\n"
        "    __bp_total__ += 1\n"
        "    try:\n"
        "        exec(__bp_stmt__)\n"
        "        __bp_passed__ += 1\n"
        "    except Exception:\n"
        "        pass\n"
        f'print(f"{_TESTS_MARKER} {{__bp_passed__}}/{{__bp_total__}}")\n'
        "import sys as __bp_sys__\n"
        "if __bp_passed__ != __bp_total__:\n"
        "    __bp_sys__.exit(1)\n"
    )


def _to_task(row: dict) -> Task:
    preamble, signature_line, body_source, entry_point, indent = _split_signature_and_body(
        row["code"]
    )
    prompt = f'{preamble}{signature_line}{indent}"""{row["text"]}"""\n'
    test_code = _build_test_code(row["test_setup_code"], row["test_list"])

    return Task(
        task_id=f"MBPP/{row['task_id']}",
        prompt=prompt,
        test_code=test_code,
        reference_solution=body_source,
        entry_point=entry_point,
    )


def load_mbpp(
    limit: int | None = None,
    task_ids: Iterable[str] | None = None,
) -> list[Task]:
    """Laedt MBPP-Aufgaben (FR-105). Verhaelt sich analog `load_humaneval`."""
    dataset = load_dataset(DATASET_NAME, DATASET_CONFIG, split="test")

    tasks: list[Task] = []
    for row in dataset:
        try:
            tasks.append(_to_task(row))
        except (SyntaxError, ValueError):
            continue

    if task_ids is not None:
        wanted = set(task_ids)
        tasks = [t for t in tasks if t.task_id in wanted]
    elif limit is not None:
        tasks = tasks[:limit]

    return tasks
