"""Gefaketer LLM-Client fuer Tests -- kein echter API-Call, kein API-Key
noetig. Gibt vorskriptete Antworten der Reihe nach zurueck."""

from __future__ import annotations

from dataclasses import dataclass, field

from beyondpass.agents.llm_client import LLMResponse


@dataclass
class FakeLLMClient:
    responses: list[str]
    calls: list[tuple[str, str]] = field(default_factory=list)
    _index: int = field(default=0, repr=False)

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls.append((system, user))
        text = self.responses[min(self._index, len(self.responses) - 1)]
        self._index += 1
        return LLMResponse(text=text, tokens_in=len(user.split()), tokens_out=len(text.split()))
