"""LLM-Client-Abstraktion mit Retry und Kostenzaehlung (FR-907, NFR-04).

Agenten (planner.py, coder.py) haengen nur von `LLMClient` (Protocol) ab,
nie von einer konkreten SDK-Klasse -- dadurch lassen sie sich in Tests
durch einen Fake ersetzen, ganz ohne echten API-Key oder Netzwerkzugriff
(siehe tests/agents/fake_llm.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

# Naeherungswerte in USD pro 1 Million Tokens. Dienen nur der groben
# Budgetkontrolle (NFR-04) und sollten bei Bedarf an die aktuelle
# Preisliste des Anbieters angepasst werden.
_PRICING_USD_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-5": (15.0, 75.0),
}
_DEFAULT_PRICING = (3.0, 15.0)


class BudgetExceededError(RuntimeError):
    """Wird ausgeloest, wenn ein Run das konfigurierte Budget ueberschreitet."""


@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> LLMResponse: ...


@dataclass
class CostTracker:
    """Summiert Tokenverbrauch und geschaetzte Kosten ueber einen Run (NFR-04)."""

    model: str
    max_usd: float | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    total_usd: float = field(default=0.0)

    def record(self, tokens_in: int, tokens_out: int) -> None:
        price_in, price_out = _PRICING_USD_PER_MILLION_TOKENS.get(self.model, _DEFAULT_PRICING)
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.total_usd += (tokens_in * price_in + tokens_out * price_out) / 1_000_000

        if self.max_usd is not None and self.total_usd > self.max_usd:
            raise BudgetExceededError(
                f"Budget von ${self.max_usd:.2f} ueberschritten (aktuell ${self.total_usd:.4f})"
            )


class AnthropicLLMClient:
    """Echte Anbindung an die Anthropic-API.

    Liest den API-Key ausschliesslich aus der Umgebungsvariable
    ANTHROPIC_API_KEY (SEC-7) -- niemals hartkodiert oder aus dem Repo.
    """

    def __init__(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
        max_retries: int,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._cost_tracker = cost_tracker

    def complete(self, system: str, user: str) -> LLMResponse:
        import anthropic

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                text = "".join(block.text for block in response.content if block.type == "text")
                tokens_in = response.usage.input_tokens
                tokens_out = response.usage.output_tokens
                if self._cost_tracker is not None:
                    self._cost_tracker.record(tokens_in, tokens_out)
                return LLMResponse(text=text, tokens_in=tokens_in, tokens_out=tokens_out)
            except anthropic.APIStatusError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    time.sleep(2**attempt)

        raise RuntimeError(
            f"LLM-Aufruf nach {self._max_retries + 1} Versuchen fehlgeschlagen"
        ) from last_error
