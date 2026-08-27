"""RunSummary-Berechnung und Seed-Mittelung (FR-1002, FR-1003, FR-1006)."""

import pytest

from beyondpass.reporting.aggregate import compare_conditions, summarize_file
from tests.reporting.factory import default_two_task_rows, write_run_file


def test_summarize_file_computes_solve_rate_and_metrics(tmp_path):
    path = write_run_file(
        tmp_path / "run.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )

    summary = summarize_file(path)

    assert summary.mode == "baseline"
    assert summary.seed == 0
    assert summary.model == "claude-haiku-4-5"
    assert summary.task_count == 2
    assert summary.solve_rate == pytest.approx(0.5)
    assert summary.avg_iterations_to_solve == pytest.approx(1.0)
    assert summary.metrics_solved["pos"] == pytest.approx(0.9)
    assert summary.metrics_all["pos"] == pytest.approx((0.9 + 0.5) / 2)
    assert summary.exact_match_rate == pytest.approx(0.5)
    assert summary.trivial_count == 1
    assert summary.suspicious_count == 0
    assert summary.total_cost_usd > 0


def test_compare_conditions_averages_pos_across_seeds(tmp_path):
    path0 = write_run_file(
        tmp_path / "run_seed0.jsonl",
        default_two_task_rows("baseline", solved_pos=0.9),
        mode="baseline",
        seed=0,
    )
    path1 = write_run_file(
        tmp_path / "run_seed1.jsonl",
        default_two_task_rows("baseline", solved_pos=0.7),
        mode="baseline",
        seed=1,
    )

    comparison = compare_conditions([path0, path1])

    row = comparison["baseline"]
    assert row.seed_count == 2
    assert row.metrics_solved_mean["pos"] == pytest.approx(0.8)
    assert row.metrics_solved_std["pos"] == pytest.approx(0.1)


def test_compare_conditions_groups_by_mode_separately(tmp_path):
    baseline_path = write_run_file(
        tmp_path / "baseline.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )
    structural_path = write_run_file(
        tmp_path / "structural.jsonl",
        default_two_task_rows("structural"),
        mode="structural",
        seed=0,
    )

    comparison = compare_conditions([baseline_path, structural_path])

    assert set(comparison) == {"baseline", "structural"}
    assert comparison["baseline"].seed_count == 1
    assert comparison["structural"].seed_count == 1


def test_summarize_file_raises_on_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        summarize_file(path)
