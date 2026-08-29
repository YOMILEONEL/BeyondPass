"""Dashboard-Hilfsfunktionen (Z7, FR-1007).

`discover_run_files`/`load_all_iterations` sind reine Funktionen ohne
Streamlit-Abhaengigkeit und direkt testbar. Der Smoke-Test unten braucht
`streamlit.testing.v1.AppTest` und wird uebersprungen, wenn Streamlit nicht
installiert ist (Kann-Ziel, kein Pflichtbestandteil von `pip install -e ".[dev]"`).
"""

from pathlib import Path

import pytest

from beyondpass.dashboard import discover_run_files, load_all_iterations
from tests.reporting.factory import default_two_task_rows, write_run_file

_DASHBOARD_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "beyondpass" / "dashboard.py"


def test_discover_run_files_returns_empty_list_for_no_match(tmp_path):
    assert discover_run_files(str(tmp_path / "nothing_*.jsonl")) == []


def test_discover_run_files_finds_matching_files(tmp_path):
    write_run_file(
        tmp_path / "run_a.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )
    write_run_file(
        tmp_path / "run_b.jsonl", default_two_task_rows("structural"), mode="structural", seed=0
    )

    found = discover_run_files(str(tmp_path / "*.jsonl"))

    assert [p.name for p in found] == ["run_a.jsonl", "run_b.jsonl"]


def test_load_all_iterations_annotates_source_file(tmp_path):
    path = write_run_file(
        tmp_path / "run.jsonl", default_two_task_rows("baseline"), mode="baseline", seed=0
    )

    rows = load_all_iterations([path])

    assert len(rows) == 3
    assert all(r["_source_file"] == "run.jsonl" for r in rows)
    assert {r["task_id"] for r in rows} == {"T/0", "T/1"}


def test_dashboard_shows_empty_state_for_no_files():
    st_testing = pytest.importorskip("streamlit.testing.v1")

    at = st_testing.AppTest.from_file(str(_DASHBOARD_SCRIPT)).run()
    at.text_input[0].set_value("no_such_directory/*.jsonl").run()

    assert not at.exception
    assert any("Keine Dateien gefunden" in info.value for info in at.info)


def test_dashboard_renders_comparison_and_task_explorer(tmp_path):
    st_testing = pytest.importorskip("streamlit.testing.v1")
    write_run_file(
        tmp_path / "run_baseline_seed0.jsonl",
        default_two_task_rows("baseline"),
        mode="baseline",
        seed=0,
    )

    at = st_testing.AppTest.from_file(str(_DASHBOARD_SCRIPT)).run()
    at.text_input[0].set_value(str(tmp_path / "*.jsonl")).run()

    assert not at.exception
    assert at.dataframe
    assert at.selectbox[0].options == ["T/0", "T/1"]
