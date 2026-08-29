"""Docker-Sandbox fuer die isolierte Ausfuehrung von LLM-generiertem Code.

Erfuellt FR-401 bis FR-407 sowie SEC-1 bis SEC-6 (FR-406, partielle
Testfall-Korrektheit, nur wenn der jeweilige Benchmark-Loader eine
`@@BEYONDPASS_TESTS@@`-Marker-Zeile ausgibt -- siehe `_parse_test_counts`):
- kein `exec`/`eval` im Host-Prozess (SEC-1)
- Container ohne Netzwerkzugang (SEC-2, FR-405)
- Ausfuehrung als nicht-privilegierter Nutzer (SEC-3)
- Ressourcenlimits: Memory, CPU, PID-Anzahl (SEC-4, FR-407)
- einziges Volume ist ein temporaeres Arbeitsverzeichnis (SEC-5)
- Container wird nach jeder Ausfuehrung entfernt, kein Zustand zwischen
  Aufgaben (SEC-6)
"""

from __future__ import annotations

import logging
import re
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import DockerException, ImageNotFound, NotFound

logger = logging.getLogger(__name__)

IMAGE_TAG = "beyondpass-sandbox:latest"
_DOCKERFILE_DIR = Path(__file__).resolve().parent
_CONTAINER_WORKDIR = "/sandbox"
_PIDS_LIMIT = 64
_NANO_CPUS = 1_000_000_000  # 1 CPU-Kern (FR-407, SEC-4)

# Optionale Partial-Correctness-Marker-Zeile (FR-406), z. B. von
# benchmarks/mbpp.py erzeugt. Rein additiv: Benchmarks, deren test_code
# diese Zeile nicht ausgibt (z. B. HumanEval), sind unbetroffen.
_TESTS_MARKER_RE = re.compile(r"@@BEYONDPASS_TESTS@@ (\d+)/(\d+)")


def _parse_test_counts(logs: str, default_passed: int, default_total: int) -> tuple[int, int]:
    """Liest tests_passed/tests_total aus der Marker-Zeile, falls vorhanden,
    sonst bleiben die uebergebenen Default-Werte (bisheriges Verhalten)."""
    match = _TESTS_MARKER_RE.search(logs)
    if match:
        return int(match.group(1)), int(match.group(2))
    return default_passed, default_total


@dataclass
class SandboxResult:
    """Ergebnis einer Sandbox-Ausfuehrung (siehe Requirements Abschnitt 9.2)."""

    bss: int
    tests_passed: int
    tests_total: int
    error_message: str | None


def is_docker_available() -> bool:
    """Prueft, ob ein Docker-Daemon erreichbar ist."""
    try:
        docker.from_env().ping()
        return True
    except DockerException:
        return False


def _ensure_image(client: docker.DockerClient) -> None:
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(path=str(_DOCKERFILE_DIR), tag=IMAGE_TAG, rm=True)


def run_in_sandbox(
    candidate_code: str,
    test_code: str,
    timeout_s: int = 10,
    memory_mb: int = 512,
) -> SandboxResult:
    """Fuehrt Kandidat + Tests isoliert aus.

    Wirft niemals -- Fehler landen in SandboxResult.error_message.
    `test_code` ist bereits vollstaendig ausfuehrbar (inkl. eines etwaigen
    Aufrufs wie `check(entry_point)`); die Sandbox selbst kennt keine
    Benchmark-Konventionen.
    """
    script = f"{candidate_code}\n\n{test_code}\n"

    try:
        client = docker.from_env()
    except DockerException as exc:
        logger.error("Docker nicht erreichbar: %s", exc)
        return SandboxResult(
            bss=0, tests_passed=0, tests_total=1, error_message=f"Docker nicht erreichbar: {exc}"
        )

    with tempfile.TemporaryDirectory(prefix="beyondpass-sandbox-") as tmp_dir:
        script_path = Path(tmp_dir) / "script.py"
        script_path.write_text(script, encoding="utf-8")

        container = None
        try:
            _ensure_image(client)
            logger.debug(
                "Starte Sandbox-Container (timeout=%ds, memory=%dmb)", timeout_s, memory_mb
            )
            container = client.containers.run(
                IMAGE_TAG,
                command=["python", f"{_CONTAINER_WORKDIR}/script.py"],
                volumes={tmp_dir: {"bind": _CONTAINER_WORKDIR, "mode": "ro"}},
                working_dir=_CONTAINER_WORKDIR,
                network_disabled=True,
                user="nobody",
                mem_limit=f"{memory_mb}m",
                pids_limit=_PIDS_LIMIT,
                nano_cpus=_NANO_CPUS,
                detach=True,
                name=f"beyondpass-{uuid.uuid4().hex[:12]}",
            )

            try:
                result = container.wait(timeout=timeout_s)
                exit_code = result.get("StatusCode", 1)
                logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                if exit_code == 0:
                    tests_passed, tests_total = _parse_test_counts(logs, 1, 1)
                    return SandboxResult(
                        bss=1,
                        tests_passed=tests_passed,
                        tests_total=tests_total,
                        error_message=None,
                    )
                tests_passed, tests_total = _parse_test_counts(logs, 0, 1)
                return SandboxResult(
                    bss=0,
                    tests_passed=tests_passed,
                    tests_total=tests_total,
                    error_message=logs.strip() or None,
                )
            except Exception:
                logger.warning("Sandbox-Timeout nach %ds erreicht, kille Container", timeout_s)
                try:
                    container.kill()
                except DockerException:
                    pass
                return SandboxResult(
                    bss=0,
                    tests_passed=0,
                    tests_total=1,
                    error_message=f"Timeout nach {timeout_s}s erreicht",
                )
        except DockerException as exc:
            logger.error("Sandbox-Fehler: %s", exc)
            return SandboxResult(bss=0, tests_passed=0, tests_total=1, error_message=str(exc))
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except NotFound:
                    pass
                except DockerException:
                    pass
