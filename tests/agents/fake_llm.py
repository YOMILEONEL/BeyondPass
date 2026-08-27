"""Gefakete LLM-Clients fuer Tests -- kein echter API-Call, kein API-Key
noetig."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from beyondpass.agents.llm_client import LLMResponse


@dataclass
class FakeLLMClient:
    """Gibt vorskriptete Antworten der Reihe nach zurueck.

    Nur fuer sequenzielle Nutzung gedacht: die Aufrufreihenfolge muss
    deterministisch sein, damit Index i garantiert zu Antwort i passt.
    Fuer parallele Tests (mehrere Tasks gleichzeitig) siehe
    `KeyedFakeLLMClient`.
    """

    responses: list[str]
    calls: list[tuple[str, str]] = field(default_factory=list)
    _index: int = field(default=0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def complete(self, system: str, user: str) -> LLMResponse:
        with self._lock:
            self.calls.append((system, user))
            text = self.responses[min(self._index, len(self.responses) - 1)]
            self._index += 1
        return LLMResponse(text=text, tokens_in=len(user.split()), tokens_out=len(text.split()))


_CODER_PROMPT_MARKERS = ("Loesungsplan:", "bisheriger Code:")


@dataclass
class KeyedFakeLLMClient:
    """Waehlt die Code-Antwort anhand eines Stichworts (z. B. `entry_point`)
    im Prompt statt anhand der Aufrufreihenfolge -- noetig fuer Tests mit
    mehreren parallelen Workern (FR-908), bei denen die Reihenfolge der
    Aufrufe nicht deterministisch ist.

    Die Stichwort-Suche greift nur bei Coder-Prompts (erkennbar an den
    Textbausteinen aus config/prompts/coder_initial.txt bzw.
    coder_retry.txt). Planner-Prompts enthalten zwar ebenfalls den
    `entry_point` (er steckt in der Funktionssignatur des Aufgaben-Prompts),
    sollen aber immer `default_response` erhalten -- sonst wuerde der
    Planner faelschlich Code statt eines Plans zurueckbekommen.
    """

    default_response: str
    responses_by_keyword: dict[str, str]
    calls: list[tuple[str, str]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def complete(self, system: str, user: str) -> LLMResponse:
        with self._lock:
            self.calls.append((system, user))

        text = self.default_response
        if any(marker in user for marker in _CODER_PROMPT_MARKERS):
            for keyword, response in self.responses_by_keyword.items():
                if keyword in user:
                    text = response
                    break

        return LLMResponse(text=text, tokens_in=len(user.split()), tokens_out=len(text.split()))
