from structcoder.benchmarks.humaneval import load_humaneval


def test_load_single_task_by_id():
    tasks = load_humaneval(task_ids=["HumanEval/0"])

    assert len(tasks) == 1
    task = tasks[0]
    assert task.task_id == "HumanEval/0"
    assert task.entry_point
    assert "def " in task.reference_solution or task.reference_solution.strip()
    assert "check" in task.test_code


def test_load_respects_limit():
    tasks = load_humaneval(limit=3)

    assert len(tasks) == 3
