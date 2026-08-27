"""Kategorie -> parametrisierter Feedback-Text (FR-703 bis FR-706).

Die Texte sind fest vorgegeben (Requirements Abschnitt 6.7) und enthalten
niemals Tokens, Struktur oder Inhalte der Referenzloesung (FR-704) -- sie
werden nur um die Testfehlermeldung ergaenzt (FR-705).
"""

from __future__ import annotations

from beyondpass.feedback.diagnosis import DiagnosisCategory

_CORE_TEXT: dict[DiagnosisCategory, str] = {
    DiagnosisCategory.SYNTAX_ERROR: "Der Code ist syntaktisch ungueltig: {error}",
    DiagnosisCategory.WRONG_APPROACH: (
        "Der grundlegende Loesungsansatz scheint nicht zu passen. "
        "Ueberdenke die Strategie neu, statt Details zu korrigieren."
    ),
    DiagnosisCategory.WRONG_ORDER: (
        "Die verwendeten Operationen wirken passend, aber ihre Reihenfolge "
        "bzw. Verschachtelung stimmt nicht. Pruefe die Abfolge der Schritte."
    ),
    DiagnosisCategory.FRAGMENTED: (
        "Zusammengehoerige Teilschritte sind auseinandergerissen. Pruefe, "
        "ob Operationen zusammengehoeren, die du getrennt hast."
    ),
    DiagnosisCategory.NEAR_MISS: (
        "Die Loesung ist strukturell fast korrekt, es fehlt vermutlich ein "
        "kleines Detail. Pruefe Randfaelle und einzelne Operatoren."
    ),
    DiagnosisCategory.GENERIC_FAIL: "Die Tests schlagen fehl: {error}",
}


def feedback_text_for(category: DiagnosisCategory, error_message: str | None) -> str | None:
    """Diagnose-basiertes Feedback fuer den `structural`-Modus (FR-904).

    None fuer SUCCESS/SUSPICIOUS_PASS -- dort ist kein Feedback noetig,
    da der Loop bereits abbricht (Requirements Abschnitt 6.7).
    """
    core = _CORE_TEXT.get(category)
    if core is None:
        return None

    error_text = error_message or ""
    if "{error}" in core:
        return core.format(error=error_text)
    if error_text:
        return f"{core}\n\nTestfehler: {error_text}"
    return core


def baseline_feedback_text(bss: int, error_message: str | None) -> str | None:
    """Rein binaeres Pass/Fail-Feedback fuer den `baseline`-Modus (FR-903)."""
    if bss == 1:
        return None
    return f"Die Tests schlagen fehl: {error_message or ''}".strip()
