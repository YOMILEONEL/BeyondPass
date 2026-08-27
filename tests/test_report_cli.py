"""T-9 (automatisiert statt manuell): `report` erzeugt aus vorhandenen
JSONL fehlerfrei eine Zusammenfassung und ein Diagramm."""

from beyondpass.__main__ import main
from tests.reporting.factory import default_two_task_rows, write_run_file


def test_report_cli_generates_summary_and_plot(tmp_path):
    baseline = write_run_file(
        tmp_path / "run_baseline_seed0.jsonl",
        default_two_task_rows("baseline"),
        mode="baseline",
        seed=0,
    )
    structural = write_run_file(
        tmp_path / "run_structural_seed0.jsonl",
        default_two_task_rows("structural"),
        mode="structural",
        seed=0,
    )
    out_path = tmp_path / "summary.md"

    exit_code = main(["report", "--runs", str(baseline), str(structural), "--out", str(out_path)])

    assert exit_code == 0
    content = out_path.read_text(encoding="utf-8")
    assert "baseline" in content
    assert "structural" in content
    assert (tmp_path / "summary.png").exists()


def test_report_cli_raises_on_unmatched_glob(tmp_path):
    out_path = tmp_path / "summary.md"

    try:
        main(["report", "--runs", str(tmp_path / "nothing_here_*.jsonl"), "--out", str(out_path)])
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
