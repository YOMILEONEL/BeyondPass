"""T-4: Referenz-Leak (INV-1).

Planner- und Coder-Prompts duerfen die Referenzloesung niemals enthalten.
"""

from beyondpass.agents.coder import run_coder
from beyondpass.agents.planner import run_planner
from beyondpass.benchmarks.humaneval import load_humaneval
from tests.agents.fake_llm import FakeLLMClient


def test_planner_prompt_never_contains_reference_solution():
    task = load_humaneval(task_ids=["HumanEval/0"])[0]
    llm = FakeLLMClient(responses=["1. Iterate over the pairs.\n2. Compare distances."])

    plan, _, _ = run_planner(task, llm)

    _, sent_prompt = llm.calls[0]
    assert task.reference_solution not in sent_prompt
    assert task.reference_solution not in plan


def test_coder_initial_prompt_never_contains_reference_solution():
    task = load_humaneval(task_ids=["HumanEval/0"])[0]
    fake_code = "```python\ndef has_close_elements(numbers, threshold):\n    return False\n```"
    llm = FakeLLMClient(responses=[fake_code])

    code, _, _ = run_coder(task, "1. Do it.", [], llm)

    _, sent_prompt = llm.calls[0]
    assert task.reference_solution not in sent_prompt
    assert task.reference_solution not in code


def test_coder_retry_prompt_never_contains_reference_solution():
    from beyondpass.agents.coder import CoderAttempt

    task = load_humaneval(task_ids=["HumanEval/0"])[0]
    fake_code = "```python\ndef has_close_elements(numbers, threshold):\n    return True\n```"
    llm = FakeLLMClient(responses=[fake_code])
    previous_code = "def has_close_elements(n, t):\n    return False\n"
    history = [CoderAttempt(code=previous_code, feedback_text="Tests failed.")]

    code, _, _ = run_coder(task, "1. Do it.", history, llm)

    _, sent_prompt = llm.calls[0]
    assert task.reference_solution not in sent_prompt
    assert task.reference_solution not in code
