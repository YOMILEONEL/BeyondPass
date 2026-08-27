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


def test_milestone_1_correct_humaneval_solution():
    """M1: HumanEval/0 mit der kanonischen Loesung muss BSS = 1 liefern."""
    from beyondpass.benchmarks.humaneval import load_humaneval

    tasks = load_humaneval(task_ids=["HumanEval/0"])
    assert len(tasks) == 1
    task = tasks[0]

    candidate_code = task.prompt + task.reference_solution
    test_code = f"{task.test_code}\ncheck({task.entry_point})\n"

    result = run_in_sandbox(candidate_code, test_code, timeout_s=10)

    assert result.bss == 1
