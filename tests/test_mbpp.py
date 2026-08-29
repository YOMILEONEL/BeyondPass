"""MBPP-Loader (FR-105, Kann-Ziel): Adapter-Muster analog HumanEval."""

import pytest

from beyondpass.benchmarks.mbpp import load_mbpp
from beyondpass.sandbox.docker_runner import run_in_sandbox


def test_load_respects_limit():
    tasks = load_mbpp(limit=5)
    assert len(tasks) == 5


def test_load_single_task_by_id():
    tasks = load_mbpp(task_ids=["MBPP/11"])

    assert len(tasks) == 1
    task = tasks[0]
    assert task.task_id == "MBPP/11"
    assert task.entry_point == "remove_Occ"
    assert "def remove_Occ" in task.prompt
    assert task.reference_solution.strip()


def test_test_code_is_self_executing():
    """test_code besteht bei MBPP aus direkten Asserts, kein check()-Wrapper noetig."""
    task = load_mbpp(task_ids=["MBPP/11"])[0]

    assert "assert" in task.test_code
    assert task.entry_point in task.test_code


def test_preamble_before_function_is_preserved_in_prompt():
    """MBPP/13 braucht `from collections import Counter`, das *vor* der
    Funktion im Rohcode steht -- ein fruehere Version dieses Loaders hat das
    stillschweigend verworfen und dadurch NameError in der Referenzloesung
    produziert."""
    task = load_mbpp(task_ids=["MBPP/13"])[0]

    assert "Counter" in task.prompt
    assert task.reference_program.count("def count_common") == 1


def test_test_code_contains_partial_correctness_harness():
    """FR-406: test_code zaehlt Asserts einzeln statt beim ersten
    Fehlschlag abzubrechen -- Struktur-Check ohne Docker."""
    task = load_mbpp(task_ids=["MBPP/11"])[0]

    assert "@@BEYONDPASS_TESTS@@" in task.test_code
    assert "except Exception" in task.test_code


@pytest.mark.docker
def test_canonical_solution_passes_its_own_tests():
    """Analog zu T-6/M1 fuer HumanEval: die MBPP-Referenzloesung muss ihre
    eigenen Tests bestehen, wenn Prompt (inkl. etwaiger Imports) und
    Referenzloesung zu einem vollstaendigen Programm zusammengefuegt werden."""
    task = load_mbpp(task_ids=["MBPP/13"])[0]
    candidate_code = task.prompt + task.reference_solution

    result = run_in_sandbox(candidate_code, task.test_code, timeout_s=10)

    assert result.bss == 1
    assert result.tests_total > 0
    assert result.tests_passed == result.tests_total


@pytest.mark.docker
def test_partial_correctness_is_tracked_for_mbpp():
    """FR-406: eine Loesung, die nur einen Teil der Asserts besteht, muss
    das auch in tests_passed/tests_total widerspiegeln, nicht nur BSS=0."""
    task = load_mbpp(task_ids=["MBPP/11"])[0]
    # remove_Occ: nur der dritte Testfall ("PHP", "P") -> "H" wird hartkodiert bedient.
    partial_solution = (
        'def remove_Occ(s, ch):\n'
        '    if s == "PHP" and ch == "P":\n'
        '        return "H"\n'
        '    return s\n'
    )

    result = run_in_sandbox(partial_solution, task.test_code, timeout_s=10)

    assert result.bss == 0
    assert result.tests_total == 3
    assert result.tests_passed == 1
