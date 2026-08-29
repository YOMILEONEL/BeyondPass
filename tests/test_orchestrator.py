"""T-7: Orchestrator-Mini-Lauf ueber 2 Aufgaben mit gemocktem LLM.

Nutzt die echte Docker-Sandbox aus AP1 (kein LLM-API-Call, aber echte
Testausfuehrung) -- daher wie test_sandbox.py als Docker-Test markiert.
"""

import json
import logging

import pytest

from beyondpass.benchmarks.humaneval import load_humaneval
from beyondpass.config import load_settings
from beyondpass.orchestrator import run
from tests.agents.fake_llm import FakeLLMClient, KeyedFakeLLMClient

pytestmark = pytest.mark.docker


def _correct_code_response(task) -> str:
    return f"```python\n{task.prompt}{task.reference_solution}\n```"


def test_orchestrator_mini_run_writes_valid_jsonl(tmp_path, caplog):
    tasks = load_humaneval(task_ids=["HumanEval/0", "HumanEval/1"])
    settings = load_settings()
    settings.run.mode = "structural"
    settings.run.max_iterations = 2

    responses: list[str] = []
    for task in tasks:
        responses.append("1. Do it.\n2. Return the result.")
        responses.append(_correct_code_response(task))

    llm = FakeLLMClient(responses=responses)
    out_path = tmp_path / "run.jsonl"

    with caplog.at_level(logging.INFO, logger="beyondpass.orchestrator"):
        run(settings, tasks, llm, out_path)

    messages = [record.message for record in caplog.records]
    assert any("Run gestartet" in m for m in messages)
    assert any("Run beendet" in m for m in messages)
    assert any("geloest nach" in m for m in messages)

    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    seen_task_ids = set()
    for line in lines:
        record = json.loads(line)
        assert record["bss"] == 1
        assert record["mode"] == "structural"
        assert record["iteration"] == 1
        assert 0.0 <= record["pos"] <= 1.0
        assert 0.0 <= record["pps"] <= 1.0
        assert 0.0 <= record["pss"] <= 1.0
        assert 0.0 <= record["pes"] <= 1.0
        assert record["diagnosis"] in {"SUCCESS", "SUSPICIOUS_PASS"}
        seen_task_ids.add(record["task_id"])

    assert seen_task_ids == {"HumanEval/0", "HumanEval/1"}


def test_orchestrator_resumes_and_skips_completed_tasks(tmp_path):
    tasks = load_humaneval(task_ids=["HumanEval/0", "HumanEval/1"])
    settings = load_settings()
    settings.run.max_iterations = 1

    out_path = tmp_path / "run.jsonl"
    out_path.write_text(json.dumps({"task_id": "HumanEval/0"}) + "\n", encoding="utf-8")

    llm = FakeLLMClient(responses=["1. Do it.", _correct_code_response(tasks[1])])
    run(settings, tasks, llm, out_path)

    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    task_ids_in_output = [json.loads(line)["task_id"] for line in lines]

    assert task_ids_in_output.count("HumanEval/0") == 1
    assert task_ids_in_output.count("HumanEval/1") == 1
    assert len(llm.calls) == 2


def test_orchestrator_baseline_mode_uses_generic_feedback_and_exhausts_budget(tmp_path):
    tasks = load_humaneval(task_ids=["HumanEval/0"])
    task = tasks[0]
    settings = load_settings()
    settings.run.mode = "baseline"
    settings.run.max_iterations = 2

    wrong_code = f"```python\ndef {task.entry_point}(*args, **kwargs):\n    return None\n```"
    llm = FakeLLMClient(responses=["1. Do it.", wrong_code, wrong_code])

    out_path = tmp_path / "run.jsonl"
    run(settings, tasks, llm, out_path)

    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    for line in lines:
        record = json.loads(line)
        assert record["bss"] == 0
        assert record["mode"] == "baseline"
        assert record["feedback_text"].startswith("Die Tests schlagen fehl")


def test_orchestrator_parallel_workers_process_all_tasks(tmp_path):
    """FR-908: mehrere Worker verarbeiten Aufgaben nebenlaeufig, ohne dass
    Antworten zwischen Aufgaben vertauscht werden (KeyedFakeLLMClient waehlt
    die Antwort anhand des entry_point im Prompt, nicht anhand der
    Aufrufreihenfolge)."""
    tasks = load_humaneval(task_ids=["HumanEval/0", "HumanEval/1"])
    settings = load_settings()
    settings.run.mode = "structural"
    settings.run.max_iterations = 1
    settings.run.parallel_workers = 2

    llm = KeyedFakeLLMClient(
        default_response="1. Do it.",
        responses_by_keyword={task.entry_point: _correct_code_response(task) for task in tasks},
    )
    out_path = tmp_path / "run.jsonl"

    run(settings, tasks, llm, out_path)

    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    results = {json.loads(line)["task_id"]: json.loads(line) for line in lines}
    assert set(results) == {"HumanEval/0", "HumanEval/1"}
    for record in results.values():
        assert record["bss"] == 1
