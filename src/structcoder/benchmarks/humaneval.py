"""HumanEval-Loader (FR-101 bis FR-104).

Lädt den Datensatz über die `datasets`-Bibliothek (nutzt deren Standard-
Cache unter ~/.cache/huggingface, erfüllt FR-104 ohne Zusatzcode) und
bildet jede Zeile auf ein `Task`-Objekt ab.
"""

from __future__ import annotations

from collections.abc import Iterable

from datasets import load_dataset

from structcoder.benchmarks.base import Task

DATASET_NAME = "openai/openai_humaneval"


def _to_task(row: dict) -> Task:
    return Task(
        task_id=row["task_id"],
        prompt=row["prompt"],
        test_code=row["test"],
        reference_solution=row["canonical_solution"],
        entry_point=row["entry_point"],
    )


def load_humaneval(
    limit: int | None = None,
    task_ids: Iterable[str] | None = None,
) -> list[Task]:
    """Lädt HumanEval-Aufgaben (FR-101, FR-102).

    Genau eines von `limit` oder `task_ids` steuert das Subset (FR-103).
    `task_ids` hat Vorrang, falls beides gesetzt ist.
    """
    dataset = load_dataset(DATASET_NAME, split="test")
    tasks = [_to_task(row) for row in dataset]

    if task_ids is not None:
        wanted = set(task_ids)
        tasks = [t for t in tasks if t.task_id in wanted]
    elif limit is not None:
        tasks = tasks[:limit]

    return tasks
