"""Tester-Agent: duenner Wrapper um die Docker-Sandbox aus AP1 (FR-401 ff.).

Bewusst benchmark-unabhaengig: `task.test_code` ist laut Adapter-Muster
(FR-105) bereits vollstaendig selbst-ausfuehrbar (der jeweilige Loader,
z. B. `benchmarks/humaneval.py`, haengt benchmark-spezifische Aufrufe wie
`check(entry_point)` bereits selbst an). Der Tester haengt hier nichts mehr
an, damit neue Benchmarks (z. B. MBPP) ohne Aenderung an dieser Datei
funktionieren.
"""

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
    return run_in_sandbox(candidate_code, task.test_code, timeout_s=timeout_s, memory_mb=memory_mb)
