"""T-5: jede Diagnose-Kategorie wird durch mindestens einen konstruierten
Metrik-Vektor ausgeloest; die Priorisierung ist deterministisch."""

from beyondpass.config import DiagnosisConfig
from beyondpass.feedback.diagnosis import DiagnosisCategory, diagnose

THRESHOLDS = DiagnosisConfig()


def _diagnose(bss, pos, pps, pss, pes, syntax_error=False):
    return diagnose(
        bss=bss,
        pos=pos,
        pps=pps,
        pss=pss,
        pes=pes,
        syntax_error=syntax_error,
        thresholds=THRESHOLDS,
    )


def test_success():
    assert _diagnose(bss=1, pos=0.9, pps=0.9, pss=0.9, pes=0.9) == DiagnosisCategory.SUCCESS


def test_suspicious_pass():
    result = _diagnose(bss=1, pos=0.1, pps=0.1, pss=0.1, pes=0.1)
    assert result == DiagnosisCategory.SUSPICIOUS_PASS


def test_syntax_error():
    result = _diagnose(bss=0, pos=0.0, pps=0.0, pss=0.0, pes=0.0, syntax_error=True)
    assert result == DiagnosisCategory.SYNTAX_ERROR


def test_wrong_approach():
    result = _diagnose(bss=0, pos=0.2, pps=0.0, pss=0.0, pes=0.0)
    assert result == DiagnosisCategory.WRONG_APPROACH


def test_wrong_order():
    result = _diagnose(bss=0, pos=0.7, pps=0.2, pss=0.9, pes=0.2)
    assert result == DiagnosisCategory.WRONG_ORDER


def test_fragmented():
    result = _diagnose(bss=0, pos=0.7, pps=0.5, pss=0.2, pes=0.2)
    assert result == DiagnosisCategory.FRAGMENTED


def test_near_miss():
    result = _diagnose(bss=0, pos=0.5, pps=0.5, pss=0.5, pes=0.8)
    assert result == DiagnosisCategory.NEAR_MISS


def test_generic_fail():
    result = _diagnose(bss=0, pos=0.5, pps=0.5, pss=0.5, pes=0.2)
    assert result == DiagnosisCategory.GENERIC_FAIL


def test_priority_syntax_error_wins_over_wrong_approach():
    result = _diagnose(bss=0, pos=0.1, pps=0.1, pss=0.1, pes=0.1, syntax_error=True)
    assert result == DiagnosisCategory.SYNTAX_ERROR


def test_priority_wrong_approach_wins_over_near_miss():
    # pos < pos_low (WRONG_APPROACH) und pes >= pes_near_miss (NEAR_MISS) gleichzeitig erfuellt.
    result = _diagnose(bss=0, pos=0.1, pps=0.1, pss=0.1, pes=0.9)
    assert result == DiagnosisCategory.WRONG_APPROACH


def test_priority_wrong_order_wins_over_fragmented():
    # pos >= pos_high, pps < pps_low (WRONG_ORDER) und pss < pss_low (FRAGMENTED)
    # gleichzeitig erfuellt.
    result = _diagnose(bss=0, pos=0.9, pps=0.1, pss=0.1, pes=0.0)
    assert result == DiagnosisCategory.WRONG_ORDER
