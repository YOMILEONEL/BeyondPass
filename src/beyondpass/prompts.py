"""Laedt Prompt-Templates aus config/prompts/ (NFR-07: keine hartkodierten
Prompts im Ablaufcode)."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "config" / "prompts"


def load_template(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")
