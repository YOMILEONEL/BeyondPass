"""Iterationsschleife: Planner -> Coder -> Tester -> Critic -> Feedback (FR-900).

`run_task_loop` verarbeitet eine einzelne Aufgabe; `run` iteriert ueber ein
komplettes Benchmark-Subset und schreibt JSONL (FR-1001), mit Resume-Support
(FR-906): bereits verarbeitete Task-IDs im Output werden uebersprungen.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from beyondpass.agents.coder import CoderAttempt, preserves_signature, run_coder, try_parse_error
from beyondpass.agents.critic import run_critic
from beyondpass.agents.llm_client import LLMClient
from beyondpass.agents.planner import run_planner
from beyondpass.agents.tester import run_tester
from beyondpass.benchmarks.base import Task
from beyondpass.config import Settings
from beyondpass.feedback.templates import baseline_feedback_text, feedback_text_for
from beyondpass.models import IterationResult
from beyondpass.sandbox.docker_runner import SandboxResult


def run_task_loop(
    task: Task, mode: str, settings: Settings, llm: LLMClient
) -> list[IterationResult]:
    """Fuehrt den Feedback-Loop fuer eine Aufgabe aus (FR-901 bis FR-905).

    Bricht ab bei BSS = 1 oder Erreichen von `max_iterations`. Der Planner
    wird nur in Iteration 1 aufgerufen, sein Plan danach wiederverwendet
    (FR-204).
    """
    results: list[IterationResult] = []
    plan: str | None = None
    history: list[CoderAttempt] = []

    for iteration in range(1, settings.run.max_iterations + 1):
        start = time.monotonic()
        tokens_in = 0
        tokens_out = 0

        if plan is None:
            plan, p_tokens_in, p_tokens_out = run_planner(task, llm)
            tokens_in += p_tokens_in
            tokens_out += p_tokens_out

        candidate_code, c_tokens_in, c_tokens_out = run_coder(task, plan, history, llm)
        tokens_in += c_tokens_in
        tokens_out += c_tokens_out

        syntax_error_message = try_parse_error(candidate_code)
        if syntax_error_message is not None:
            sandbox_result = SandboxResult(
                bss=0, tests_passed=0, tests_total=0, error_message=syntax_error_message
            )
        else:
            sandbox_result = run_tester(
                task,
                candidate_code,
                timeout_s=settings.sandbox.timeout_s,
                memory_mb=settings.sandbox.memory_mb,
            )

        critic_result = run_critic(
            task,
            candidate_code,
            bss=sandbox_result.bss,
            syntax_error=syntax_error_message is not None,
            thresholds=settings.diagnosis,
        )

        if mode == "baseline":
            feedback_text = baseline_feedback_text(sandbox_result.bss, sandbox_result.error_message)
        else:
            feedback_text = feedback_text_for(critic_result.diagnosis, sandbox_result.error_message)

        flags = list(critic_result.flags)
        if not preserves_signature(candidate_code, task.entry_point):
            flags.append("SIGNATURE_MISMATCH")

        results.append(
            IterationResult(
                task_id=task.task_id,
                iteration=iteration,
                mode=mode,
                plan=plan if iteration == 1 else None,
                candidate_code=candidate_code,
                bss=sandbox_result.bss,
                tests_passed=sandbox_result.tests_passed,
                tests_total=sandbox_result.tests_total,
                error_message=sandbox_result.error_message,
                pos=critic_result.metrics.pos,
                pps=critic_result.metrics.pps,
                pss=critic_result.metrics.pss,
                pes=critic_result.metrics.pes,
                diagnosis=critic_result.diagnosis.value,
                feedback_text=feedback_text,
                flags=flags,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                duration_s=time.monotonic() - start,
            )
        )

        if sandbox_result.bss == 1:
            break

        history.append(CoderAttempt(code=candidate_code, feedback_text=feedback_text or ""))

    return results


def _load_completed_task_ids(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()

    completed: set[str] = set()
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                completed.add(json.loads(line)["task_id"])
    return completed


def _write_run_meta(out_path: Path, settings: Settings) -> None:
    """Schreibt die Run-Konfiguration inkl. Modell und Datum einmalig (NFR-02)."""
    meta_path = out_path.with_suffix(".meta.json")
    if meta_path.exists():
        return
    meta = {
        "run_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": settings.model_dump(),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def run(settings: Settings, tasks: list[Task], llm: LLMClient, out_path: Path) -> None:
    """Fuehrt den Loop ueber alle Aufgaben aus und haengt JSONL an (FR-1001, FR-906).

    Bei `settings.run.parallel_workers > 1` werden Aufgaben nebenlaeufig ueber
    einen Thread-Pool verarbeitet (FR-908); das Schreiben in die Ausgabedatei
    ist ueber einen Lock serialisiert. Mit dem Default (1) laeuft alles wie
    zuvor rein sequenziell ueber einen einzigen, dauerhaft offenen Handle.
    """
    completed_task_ids = _load_completed_task_ids(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_run_meta(out_path, settings)

    pending = [task for task in tasks if task.task_id not in completed_task_ids]
    write_lock = threading.Lock()

    with out_path.open("a", encoding="utf-8") as f:

        def _process(task: Task) -> None:
            for result in run_task_loop(task, settings.run.mode, settings, llm):
                with write_lock:
                    f.write(result.to_json_line() + "\n")
                    f.flush()

        workers = max(1, settings.run.parallel_workers)
        if workers == 1:
            for task in pending:
                _process(task)
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(_process, task) for task in pending]
                for future in as_completed(futures):
                    future.result()
