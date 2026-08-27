"""Ergebnisauswertung: aggregiert JSONL-Runs zu Zusammenfassungen
(FR-1001 bis FR-1006).

Absichtlich ohne `pandas` -- die Aggregation ist mit der Standardbibliothek
(`statistics`, Dict-Gruppierung) einfach genug, das spart eine Abhaengigkeit.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

from beyondpass.agents.llm_client import estimate_cost_usd
from beyondpass.config import load_settings

_METRIC_KEYS = ("pos", "pps", "pss", "pes")


@dataclass
class RunSummary:
    """Zusammenfassung eines einzelnen Runs (Datenmodell Requirements 8.3)."""

    source_path: Path
    mode: str
    seed: int | None
    model: str
    task_count: int
    solve_rate: float
    avg_iterations_to_solve: float
    metrics_all: dict[str, float]
    metrics_solved: dict[str, float]
    exact_match_rate: float
    trivial_count: int
    suspicious_count: int
    total_cost_usd: float


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _read_meta(path: Path) -> dict:
    meta_path = path.with_suffix(".meta.json")
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _final_iteration_per_task(rows: list[dict]) -> list[dict]:
    """Die zuletzt geschriebene Iteration je task_id ist der finale Zustand."""
    final: dict[str, dict] = {}
    for row in rows:
        existing = final.get(row["task_id"])
        if existing is None or row["iteration"] >= existing["iteration"]:
            final[row["task_id"]] = row
    return list(final.values())


def _mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def summarize_file(path: Path) -> RunSummary:
    """Berechnet die RunSummary fuer eine einzelne JSONL-Datei (FR-1002, FR-1003)."""
    rows = _read_jsonl(path)
    if not rows:
        raise ValueError(f"{path} enthaelt keine Ergebniszeilen")

    config = _read_meta(path).get("config", {})
    seed = config.get("run", {}).get("seed")
    model = config.get("llm", {}).get("model") or load_settings().llm.model

    final_rows = _final_iteration_per_task(rows)
    solved_rows = [r for r in final_rows if r["bss"] == 1]

    tokens_in = sum(r.get("tokens_in", 0) for r in rows)
    tokens_out = sum(r.get("tokens_out", 0) for r in rows)

    return RunSummary(
        source_path=path,
        mode=final_rows[0]["mode"],
        seed=seed,
        model=model,
        task_count=len(final_rows),
        solve_rate=len(solved_rows) / len(final_rows),
        avg_iterations_to_solve=_mean([r["iteration"] for r in solved_rows]),
        metrics_all={key: _mean([r[key] for r in final_rows]) for key in _METRIC_KEYS},
        metrics_solved={key: _mean([r[key] for r in solved_rows]) for key in _METRIC_KEYS},
        exact_match_rate=sum(1 for r in final_rows if r["pes"] == 1.0) / len(final_rows),
        trivial_count=sum(1 for r in final_rows if "TRIVIAL" in r.get("flags", [])),
        suspicious_count=sum(1 for r in final_rows if "SUSPICIOUS" in r.get("flags", [])),
        total_cost_usd=estimate_cost_usd(model, tokens_in, tokens_out),
    )


@dataclass
class ComparisonRow:
    """Mittelwert +/- Standardabweichung ueber mehrere Seeds derselben Bedingung (FR-1006)."""

    mode: str
    seed_count: int
    solve_rate_mean: float
    solve_rate_std: float
    avg_iterations_mean: float
    avg_iterations_std: float
    metrics_solved_mean: dict[str, float]
    metrics_solved_std: dict[str, float]
    total_cost_usd: float
    trivial_count: int
    suspicious_count: int


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = statistics.mean(values)
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    return mean, std


def compare_conditions(paths: list[Path]) -> dict[str, ComparisonRow]:
    """Gruppiert RunSummaries nach `mode` und mittelt ueber Seeds (FR-1004, FR-1006)."""
    by_mode: dict[str, list[RunSummary]] = {}
    for path in paths:
        summary = summarize_file(path)
        by_mode.setdefault(summary.mode, []).append(summary)

    comparison: dict[str, ComparisonRow] = {}
    for mode, runs in by_mode.items():
        solve_rate_mean, solve_rate_std = _mean_std([r.solve_rate for r in runs])
        iter_mean, iter_std = _mean_std([r.avg_iterations_to_solve for r in runs])

        metrics_mean: dict[str, float] = {}
        metrics_std: dict[str, float] = {}
        for key in _METRIC_KEYS:
            metrics_mean[key], metrics_std[key] = _mean_std([r.metrics_solved[key] for r in runs])

        comparison[mode] = ComparisonRow(
            mode=mode,
            seed_count=len(runs),
            solve_rate_mean=solve_rate_mean,
            solve_rate_std=solve_rate_std,
            avg_iterations_mean=iter_mean,
            avg_iterations_std=iter_std,
            metrics_solved_mean=metrics_mean,
            metrics_solved_std=metrics_std,
            total_cost_usd=sum(r.total_cost_usd for r in runs),
            trivial_count=sum(r.trivial_count for r in runs),
            suspicious_count=sum(r.suspicious_count for r in runs),
        )

    return comparison


def _fmt(mean: float, std: float) -> str:
    return f"{mean:.2f} +/- {std:.2f}"


def render_markdown(comparison: dict[str, ComparisonRow]) -> str:
    """Rendert die Vergleichstabelle im Format aus Requirements Abschnitt 10.4."""
    lines = [
        "# BeyondPass - Auswertung",
        "",
        "| Bedingung | Solve Rate | Iter. (Mittel) | POS (gelöst) | PPS (gelöst) "
        "| PSS (gelöst) | PES (gelöst) |",
        "|---|---|---|---|---|---|---|",
    ]

    for mode in sorted(comparison):
        row = comparison[mode]
        m, s = row.metrics_solved_mean, row.metrics_solved_std
        lines.append(
            "| {mode} (n={n}) | {solve} | {iters} | {pos} | {pps} | {pss} | {pes} |".format(
                mode=mode,
                n=row.seed_count,
                solve=_fmt(row.solve_rate_mean, row.solve_rate_std),
                iters=_fmt(row.avg_iterations_mean, row.avg_iterations_std),
                pos=_fmt(m["pos"], s["pos"]),
                pps=_fmt(m["pps"], s["pps"]),
                pss=_fmt(m["pss"], s["pss"]),
                pes=_fmt(m["pes"], s["pes"]),
            )
        )

    lines += [
        "",
        "| Bedingung | Trivial-Flags | Suspicious-Flags | Geschaetzte Kosten (USD) |",
        "|---|---|---|---|",
    ]
    for mode in sorted(comparison):
        row = comparison[mode]
        lines.append(
            f"| {mode} | {row.trivial_count} | {row.suspicious_count} | ${row.total_cost_usd:.4f} |"
        )

    return "\n".join(lines) + "\n"
