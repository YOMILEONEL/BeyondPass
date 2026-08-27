"""Tester-Agent: duenner Wrapper um die Docker-Sandbox aus AP1 (FR-401 ff.)."""

from __future__ import annotations

from beyondpass.benchmarks.base import Task
from beyondpass.sandbox.docker_runner import SandboxResult, run_in_sandbox


def run_tester(
    task: Task,
    candidate_code: str,
    timeout_s: int = 10,
    memory_mb: int = 512,
) -> SandboxResult:
    """Fuehrt Kandidat + Tests der Aufgabe isoliert aus (FR-401, FR-402)."""
    test_code = f"{task.test_code}\ncheck({task.entry_point})\n"
    return run_in_sandbox(candidate_code, test_code, timeout_s=timeout_s, memory_mb=memory_mb)
