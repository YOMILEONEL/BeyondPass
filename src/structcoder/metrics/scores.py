"""POS/PPS/PSS/PES (Requirements Abschnitt 4.2 und FR-601 bis FR-608).

Identische Semantik wie die Bachelorarbeit (Kap. 4.2) und die DeepCoder-
Pipeline (`step07_calculate_metrics.py`): Konvention "leere Sequenz auf
einer Seite -> 0.0" fuer alle vier Metriken (FR-605); alle Werte in [0, 1]
(FR-606); Invariante POS >= max(PPS, PSS, PES) (FR-607, siehe T-3).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from structcoder.metrics.tokenizer import tokenize


@dataclass
class MetricResult:
    pos: float
    pps: float
    pss: float
    pes: float


def program_operation_score(ref: list[str], cand: list[str]) -> float:
    """POS: Multiset-Ueberlappung der Tokens, unabhaengig von Position (FR-601)."""
    if not ref or not cand:
        return 0.0

    ref_counter = Counter(ref)
    cand_counter = Counter(cand)

    overlap = sum(min(count, cand_counter.get(token, 0)) for token, count in ref_counter.items())
    return overlap / max(len(ref), len(cand))


def program_position_score(ref: list[str], cand: list[str]) -> float:
    """PPS: positionsweise Uebereinstimmung, ohne Alignment (FR-602)."""
    if not ref or not cand:
        return 0.0

    matches = sum(1 for i in range(min(len(ref), len(cand))) if ref[i] == cand[i])
    return matches / max(len(ref), len(cand))


def longest_common_contiguous_length(ref: list[str], cand: list[str]) -> int:
    """Laenge des laengsten gemeinsamen zusammenhaengenden Token-Blocks."""
    if not ref or not cand:
        return 0

    dp = [[0] * (len(cand) + 1) for _ in range(len(ref) + 1)]
    best = 0

    for i in range(1, len(ref) + 1):
        for j in range(1, len(cand) + 1):
            if ref[i - 1] == cand[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                best = max(best, dp[i][j])

    return best


def program_sequence_score(ref: list[str], cand: list[str]) -> float:
    """PSS: laengster gemeinsamer zusammenhaengender Block, normalisiert (FR-603)."""
    if not ref or not cand:
        return 0.0

    return longest_common_contiguous_length(ref, cand) / max(len(ref), len(cand))


def levenshtein_distance(ref: list[str], cand: list[str]) -> int:
    """Token-Level Levenshtein-Distanz (Einfuegen, Loeschen, Ersetzen)."""
    n, m = len(ref), len(cand)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == cand[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[n][m]


def program_edit_score(ref: list[str], cand: list[str]) -> float:
    """PES: 1 - normalisierte Levenshtein-Distanz (FR-604)."""
    if not ref or not cand:
        return 0.0

    max_len = max(len(ref), len(cand))
    return 1.0 - (levenshtein_distance(ref, cand) / max_len)


def all_metrics(ref_source: str, cand_source: str) -> MetricResult:
    """Tokenisiert beide Quellen und berechnet alle vier Metriken (Abschnitt 9.1)."""
    ref_tokens = tokenize(ref_source)
    cand_tokens = tokenize(cand_source)
    return MetricResult(
        pos=program_operation_score(ref_tokens, cand_tokens),
        pps=program_position_score(ref_tokens, cand_tokens),
        pss=program_sequence_score(ref_tokens, cand_tokens),
        pes=program_edit_score(ref_tokens, cand_tokens),
    )
