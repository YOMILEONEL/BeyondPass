"""Typisierte, validierte Konfiguration (NFR-07): lädt config/default.yaml
und erlaubt Overrides über Umgebungsvariablen mit dem Prefix STRUCTCODER_.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "default.yaml"


class RunConfig(BaseModel):
    mode: str = "structural"
    seed: int = 0
    max_iterations: int = 5
    parallel_workers: int = 1


class BenchmarkConfig(BaseModel):
    name: str = "humaneval"
    limit: int | None = 50
    task_ids: list[str] | None = None


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-haiku-4-5"
    temperature: float = 0.7
    max_tokens: int = 2000
    max_retries: int = 3


class SandboxConfig(BaseModel):
    timeout_s: int = 10
    memory_mb: int = 512
    network: bool = False


class DiagnosisConfig(BaseModel):
    pos_low: float = 0.4
    pos_high: float = 0.6
    pps_low: float = 0.4
    pss_low: float = 0.4
    pes_near_miss: float = 0.7
    suspicious_pos: float = 0.3


class BudgetConfig(BaseModel):
    max_usd: float = 10.0


class OutputConfig(BaseModel):
    results_dir: str = "results/"
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Vollständige Konfiguration eines Runs (siehe Requirements Abschnitt 13)."""

    model_config = SettingsConfigDict(env_prefix="STRUCTCODER_", env_nested_delimiter="__")

    run: RunConfig = RunConfig()
    benchmark: BenchmarkConfig = BenchmarkConfig()
    llm: LLMConfig = LLMConfig()
    sandbox: SandboxConfig = SandboxConfig()
    diagnosis: DiagnosisConfig = DiagnosisConfig()
    budget: BudgetConfig = BudgetConfig()
    output: OutputConfig = OutputConfig()


def load_settings(config_path: Path | str | None = None) -> Settings:
    """Lädt die Konfiguration aus einer YAML-Datei (Default: config/default.yaml).

    Umgebungsvariablen mit Prefix STRUCTCODER_ überschreiben einzelne Werte,
    z. B. STRUCTCODER_RUN__SEED=1.
    """
    path = Path(config_path) if config_path else Path(
        os.environ.get("STRUCTCODER_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return Settings(**data)
