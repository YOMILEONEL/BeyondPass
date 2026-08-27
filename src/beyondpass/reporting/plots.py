"""Balkendiagramm Baseline vs. Structural (FR-1005), analog Abb. 6.1/6.2 der Thesis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from beyondpass.reporting.aggregate import ComparisonRow

_METRICS = [
    ("solve_rate_mean", "solve_rate_std", "Solve Rate"),
    ("pos", "pos", "POS"),
    ("pps", "pps", "PPS"),
    ("pss", "pss", "PSS"),
    ("pes", "pes", "PES"),
]


def _values_for(row: ComparisonRow) -> tuple[list[float], list[float]]:
    values = [row.solve_rate_mean]
    errors = [row.solve_rate_std]
    for key in ("pos", "pps", "pss", "pes"):
        values.append(row.metrics_solved_mean[key])
        errors.append(row.metrics_solved_std[key])
    return values, errors


def plot_comparison(comparison: dict[str, ComparisonRow], out_path: Path) -> None:
    """Zeichnet Solve Rate + POS/PPS/PSS/PES je Bedingung und speichert als PNG."""
    modes = sorted(comparison)
    labels = [name for _, _, name in _METRICS]

    fig, ax = plt.subplots(figsize=(8, 5))
    bar_width = 0.8 / max(len(modes), 1)

    for i, mode in enumerate(modes):
        values, errors = _values_for(comparison[mode])
        positions = [x + i * bar_width for x in range(len(labels))]
        ax.bar(positions, values, bar_width, yerr=errors, capsize=3, label=mode)

    offset = bar_width * (len(modes) - 1) / 2
    ax.set_xticks([x + offset for x in range(len(labels))])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Wert")
    ax.set_title("Baseline vs. Structural")
    ax.legend()
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
