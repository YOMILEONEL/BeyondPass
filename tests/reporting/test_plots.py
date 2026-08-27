"""plot_comparison() erzeugt eine gueltige PNG-Datei (FR-1005)."""

from beyondpass.reporting.aggregate import compare_conditions
from beyondpass.reporting.plots import plot_comparison
from tests.reporting.factory import default_two_task_rows, write_run_file

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_plot_comparison_writes_png(tmp_path):
    path = write_run_file(
        tmp_path / "run.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )
    comparison = compare_conditions([path])

    out_path = tmp_path / "plot.png"
    plot_comparison(comparison, out_path)

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == _PNG_MAGIC


def test_plot_comparison_with_both_modes(tmp_path):
    baseline = write_run_file(
        tmp_path / "baseline.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )
    structural = write_run_file(
        tmp_path / "structural.jsonl",
        default_two_task_rows("structural"),
        mode="structural",
        seed=0,
    )
    comparison = compare_conditions([baseline, structural])

    out_path = tmp_path / "plot.png"
    plot_comparison(comparison, out_path)

    assert out_path.read_bytes()[:8] == _PNG_MAGIC
