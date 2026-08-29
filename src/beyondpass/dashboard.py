"""Streamlit-Dashboard zur interaktiven Exploration der Ergebnisse
(FR-1007, Requirements Abschnitt 2.2, Z7 -- Kann-Ziel).

Start: `streamlit run src/beyondpass/dashboard.py`

Nutzt ausschliesslich bereits getestete Aggregationslogik aus
`reporting/aggregate.py`; der Mehrwert dieses Moduls ist der
Pro-Aufgabe-Explorer (Iterationsverlauf, Code, Feedback), den der
Markdown-Report nicht bietet.
"""

from __future__ import annotations

import glob as glob_module
import json
from collections import Counter
from pathlib import Path

from beyondpass.reporting.aggregate import compare_conditions

_METRIC_KEYS = ("pos", "pps", "pss", "pes")
_METRIC_LABELS = ("POS", "PPS", "PSS", "PES")
_CHART_METRICS = [("solve_rate", "Solve Rate"), *zip(_METRIC_KEYS, _METRIC_LABELS, strict=True)]


def discover_run_files(pattern: str) -> list[Path]:
    """Loest ein Glob-Muster zu einer sortierten Liste vorhandener JSONL-Dateien auf.

    Anders als `__main__.py::_expand_run_patterns` wirft dies bei einem
    leeren Treffer keine Exception -- die Seite soll einen Leerzustand
    anzeigen, nicht abstuerzen.
    """
    return sorted(Path(p) for p in glob_module.glob(pattern))


def load_all_iterations(paths: list[Path]) -> list[dict]:
    """Laedt alle Iterationszeilen mehrerer JSONL-Dateien, je annotiert mit
    ihrer Quelldatei (Feld `_source_file`)."""
    rows: list[dict] = []
    for path in paths:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                row["_source_file"] = path.name
                rows.append(row)
    return rows


def _render() -> None:
    import streamlit as st

    st.set_page_config(page_title="BeyondPass Dashboard", layout="wide")
    st.title("BeyondPass -- Ergebnis-Explorer")

    pattern = st.text_input("JSONL-Runs (Glob-Muster)", value="results/*.jsonl")
    paths = discover_run_files(pattern)

    if not paths:
        st.info(f"Keine Dateien gefunden fuer Muster `{pattern}`.")
        return

    st.caption(f"{len(paths)} Datei(en) gefunden: " + ", ".join(p.name for p in paths))

    st.subheader("Baseline vs. Structural")
    try:
        comparison = compare_conditions(paths)
    except ValueError as exc:
        st.error(f"Konnte Runs nicht auswerten: {exc}")
        return

    def fmt(mean: float, std: float) -> str:
        return f"{mean:.2f} +/- {std:.2f}"

    table_rows = [
        {
            "Modus": f"{mode} (n={row.seed_count})",
            "Solve Rate": fmt(row.solve_rate_mean, row.solve_rate_std),
            "Ø Iterationen": fmt(row.avg_iterations_mean, row.avg_iterations_std),
            "POS": fmt(row.metrics_solved_mean["pos"], row.metrics_solved_std["pos"]),
            "PPS": fmt(row.metrics_solved_mean["pps"], row.metrics_solved_std["pps"]),
            "PSS": fmt(row.metrics_solved_mean["pss"], row.metrics_solved_std["pss"]),
            "PES": fmt(row.metrics_solved_mean["pes"], row.metrics_solved_std["pes"]),
            "Trivial": row.trivial_count,
            "Suspicious": row.suspicious_count,
            "Kosten (USD)": f"${row.total_cost_usd:.4f}",
        }
        for mode, row in sorted(comparison.items())
    ]
    st.dataframe(table_rows, use_container_width=True)

    def metric_value(mode_row, key: str) -> float:
        if key == "solve_rate":
            return mode_row.solve_rate_mean
        return mode_row.metrics_solved_mean[key]

    chart_rows = [
        {"Metrik": label, **{mode: metric_value(row, key) for mode, row in comparison.items()}}
        for key, label in _CHART_METRICS
    ]
    st.bar_chart(chart_rows, x="Metrik", y=sorted(comparison.keys()))

    all_rows = load_all_iterations(paths)

    st.subheader("Diagnose-Kategorien (alle Iterationen)")
    diagnosis_counts = Counter(r["diagnosis"] for r in all_rows)
    st.bar_chart(dict(sorted(diagnosis_counts.items())))

    st.subheader("Aufgabe im Detail")
    task_ids = sorted({r["task_id"] for r in all_rows})
    selected_task = st.selectbox("Aufgabe waehlen", task_ids)

    task_rows = [r for r in all_rows if r["task_id"] == selected_task]
    task_rows.sort(key=lambda r: (r["_source_file"], r["iteration"]))

    for row in task_rows:
        title = (
            f"{row['_source_file']} -- Iteration {row['iteration']} "
            f"(BSS={row['bss']}, {row['diagnosis']})"
        )
        with st.expander(title):
            cols = st.columns(4)
            for col, key, label in zip(cols, _METRIC_KEYS, _METRIC_LABELS, strict=True):
                col.metric(label, f"{row[key]:.2f}")

            st.code(row["candidate_code"], language="python")

            if row.get("feedback_text"):
                st.markdown(f"**Feedback:** {row['feedback_text']}")
            if row.get("flags"):
                st.markdown(f"**Flags:** {', '.join(row['flags'])}")


if __name__ == "__main__":
    _render()
