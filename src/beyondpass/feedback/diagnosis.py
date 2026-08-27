"""Diagnose-Modul: leitet aus dem Metrik-Muster eine Kategorie ab (FR-702).

Diagnose-Matrix (Requirements Abschnitt 6.7). Die Fehlschlag-Kategorien
werden in der vorgegebenen Reihenfolge geprueft (SYNTAX_ERROR ->
WRONG_APPROACH -> WRONG_ORDER -> FRAGMENTED -> NEAR_MISS -> GENERIC_FAIL);
die erste zutreffende gewinnt.
"""

from __future__ import annotations

from enum import Enum

from beyondpass.config import DiagnosisConfig


class DiagnosisCategory(str, Enum):
    """Eine der acht Kategorien der Diagnose-Matrix (Requirements Abschnitt 6.7)."""

    SUCCESS = "SUCCESS"
    SUSPICIOUS_PASS = "SUSPICIOUS_PASS"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    WRONG_APPROACH = "WRONG_APPROACH"
    WRONG_ORDER = "WRONG_ORDER"
    FRAGMENTED = "FRAGMENTED"
    NEAR_MISS = "NEAR_MISS"
    GENERIC_FAIL = "GENERIC_FAIL"


def diagnose(
    bss: int,
    pos: float,
    pps: float,
    pss: float,
    pes: float,
    syntax_error: bool,
    thresholds: DiagnosisConfig,
) -> DiagnosisCategory:
    """Leitet aus BSS und den vier Metriken die Diagnose-Kategorie ab (FR-702).

    Bei `bss == 1` wird nur zwischen SUCCESS und SUSPICIOUS_PASS
    unterschieden; bei `bss == 0` wird die Fehlschlag-Reihenfolge aus dem
    Modul-Docstring geprueft, erste zutreffende Kategorie gewinnt.
    """
    if bss == 1:
        if pos < thresholds.suspicious_pos:
            return DiagnosisCategory.SUSPICIOUS_PASS
        return DiagnosisCategory.SUCCESS

    if syntax_error:
        return DiagnosisCategory.SYNTAX_ERROR
    if pos < thresholds.pos_low:
        return DiagnosisCategory.WRONG_APPROACH
    if pos >= thresholds.pos_high and pps < thresholds.pps_low:
        return DiagnosisCategory.WRONG_ORDER
    if pos >= thresholds.pos_high and pss < thresholds.pss_low and pps >= thresholds.pps_low:
        return DiagnosisCategory.FRAGMENTED
    if pes >= thresholds.pes_near_miss:
        return DiagnosisCategory.NEAR_MISS
    return DiagnosisCategory.GENERIC_FAIL
