"""T-6: Sandbox-Integrationstests + Meilenstein M1.

M1 (Requirements Abschnitt 17, AP1): eine hartkodierte korrekte HumanEval-
Loesung wird geladen, in der Sandbox getestet und liefert BSS = 1.
"""

import pytest

from beyondpass.sandbox.docker_runner import run_in_sandbox

pytestmark = pytest.mark.docker


def test_timeout_kills_infinite_loop():
    candidate = "def candidate():\n    pass\n"
    test_code = "while True:\n    pass\n"

    result = run_in_sandbox(candidate, test_code, timeout_s=3)

    assert result.bss == 0
    assert result.error_message is not None


def test_no_network_access():
    candidate = "def candidate():\n    pass\n"
    test_code = (
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.settimeout(3)\n"
        "s.connect(('8.8.8.8', 53))\n"
    )

    result = run_in_sandbox(candidate, test_code, timeout_s=8)

    assert result.bss == 0


def test_exception_does_not_crash_host():
    candidate = "def candidate():\n    raise ValueError('boom')\n"
    test_code = "candidate()\n"

    result = run_in_sandbox(candidate, test_code, timeout_s=8)

    assert result.bss == 0
    assert result.error_message is not None
    assert "ValueError" in result.error_message


def test_correct_solution_passes():
    candidate = "def add(a, b):\n    return a + b\n"
    test_code = "assert add(2, 3) == 5\n"

    result = run_in_sandbox(candidate, test_code, timeout_s=8)

    assert result.bss == 1
    assert result.error_message is None


def test_no_marker_falls_back_to_binary_counts():
    """FR-406-Regressionsschutz: ohne @@BEYONDPASS_TESTS@@-Marker-Zeile
    (z. B. HumanEval, oder hier ein simples Skript ohne Zaehl-Harness)
    bleibt tests_passed/tests_total exakt 1/1 bzw. 0/1 wie vor FR-406."""
    candidate = "def add(a, b):\n    return a + b\n"

    ok = run_in_sandbox(candidate, "assert add(2, 3) == 5\n", timeout_s=8)
    assert (ok.tests_passed, ok.tests_total) == (1, 1)

    fail = run_in_sandbox(candidate, "assert add(2, 3) == 999\n", timeout_s=8)
    assert (fail.tests_passed, fail.tests_total) == (0, 1)


def test_marker_line_overrides_default_counts():
    """FR-406: gibt test_code selbst eine @@BEYONDPASS_TESTS@@-Zeile aus
    (wie benchmarks/mbpp.py es tut), uebernimmt die Sandbox diese Werte."""
    candidate = "def noop():\n    pass\n"
    test_code = 'print("@@BEYONDPASS_TESTS@@ 2/5")\n'

    result = run_in_sandbox(candidate, test_code, timeout_s=8)

    assert result.bss == 1
    assert result.tests_passed == 2
    assert result.tests_total == 5


def test_milestone_1_correct_humaneval_solution():
    """M1: HumanEval/0 mit der kanonischen Loesung muss BSS = 1 liefern."""
    from beyondpass.benchmarks.humaneval import load_humaneval

    tasks = load_humaneval(task_ids=["HumanEval/0"])
    assert len(tasks) == 1
    task = tasks[0]

    candidate_code = task.prompt + task.reference_solution

    result = run_in_sandbox(candidate_code, task.test_code, timeout_s=10)

    assert result.bss == 1
