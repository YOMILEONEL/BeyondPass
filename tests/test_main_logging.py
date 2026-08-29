"""NFR-09: strukturiertes Logging mit konfigurierbarem Log-Level.

Konfiguriert bewusst nur den `beyondpass`-Logger-Namespace (nicht den
Root-Logger), damit Drittanbieter-Bibliotheken (httpx, huggingface_hub, ...)
bei INFO/DEBUG nicht mit-geloggt werden.
"""

import logging

from beyondpass.__main__ import _configure_logging


def test_configure_logging_sets_beyondpass_logger_level():
    beyondpass_logger = logging.getLogger("beyondpass")
    original_level = beyondpass_logger.level
    try:
        _configure_logging("DEBUG", force=True)
        assert beyondpass_logger.level == logging.DEBUG

        _configure_logging("WARNING", force=True)
        assert beyondpass_logger.level == logging.WARNING
    finally:
        beyondpass_logger.setLevel(original_level)


def test_configure_logging_falls_back_to_info_for_unknown_level():
    beyondpass_logger = logging.getLogger("beyondpass")
    try:
        _configure_logging("NOT_A_REAL_LEVEL", force=True)
        assert beyondpass_logger.level == logging.INFO
    finally:
        _configure_logging("WARNING", force=True)


def test_configure_logging_does_not_touch_root_logger():
    """Verhindert Rueckfall auf `logging.basicConfig`, das Drittanbieter-
    Bibliotheken (httpx, huggingface_hub, ...) mit-konfigurieren wuerde."""
    root_level_before = logging.root.level
    _configure_logging("DEBUG", force=True)
    assert logging.root.level == root_level_before
    _configure_logging("WARNING", force=True)


def test_configure_logging_does_not_duplicate_handlers_without_force():
    """`main()` ruft dies ungeforct auf, `_run_command` danach mit `force=True`
    -- ohne den `if not handlers`-Guard wuerden wiederholte Aufrufe (z. B. in
    Tests, die `main()` mehrfach im selben Prozess aufrufen) Handler stapeln
    und jede Log-Zeile mehrfach ausgeben."""
    beyondpass_logger = logging.getLogger("beyondpass")
    beyondpass_logger.handlers.clear()
    try:
        _configure_logging("INFO")
        _configure_logging("INFO")
        assert len(beyondpass_logger.handlers) == 1
    finally:
        beyondpass_logger.handlers.clear()
        _configure_logging("WARNING", force=True)
