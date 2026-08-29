"""Kostenzaehlung und strukturiertes Logging (NFR-04, NFR-09) fuer llm_client.py.

Kein echter API-Call: `AnthropicLLMClient` wird mit einem Dummy-Key
konstruiert (die SDK validiert den Key nicht bei der Konstruktion), und
`messages.create` wird direkt gemonkeypatcht, um Fehlschlaege/Retries zu
simulieren.
"""

from __future__ import annotations

import logging

import pytest

from beyondpass.agents.llm_client import (
    AnthropicLLMClient,
    BudgetExceededError,
    CostTracker,
)


def test_cost_tracker_raises_and_logs_on_budget_exceeded(caplog):
    tracker = CostTracker(model="claude-haiku-4-5", max_usd=0.000001)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BudgetExceededError):
            tracker.record(tokens_in=10_000, tokens_out=10_000)

    assert any("Budget ueberschritten" in record.message for record in caplog.records)


def test_cost_tracker_does_not_raise_within_budget():
    tracker = CostTracker(model="claude-haiku-4-5", max_usd=10.0)
    tracker.record(tokens_in=100, tokens_out=50)
    assert tracker.total_usd > 0


@pytest.fixture
def anthropic_client(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-test-key-not-real")
    return AnthropicLLMClient(
        model="claude-haiku-4-5", temperature=0.0, max_tokens=100, max_retries=2
    )


def _fake_status_error(message: str):
    import anthropic
    import httpx2

    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(status_code=529, request=request)
    return anthropic.APIStatusError(message, response=response, body=None)


def test_complete_logs_warning_on_retry_then_succeeds(anthropic_client, monkeypatch, caplog):
    calls = {"count": 0}

    def fake_create(**kwargs):
        calls["count"] += 1
        if calls["count"] < 2:
            raise _fake_status_error("overloaded")

        class FakeBlock:
            type = "text"
            text = "ok"

        class FakeUsage:
            input_tokens = 5
            output_tokens = 3

        class FakeResponse:
            content = [FakeBlock()]
            usage = FakeUsage()

        return FakeResponse()

    monkeypatch.setattr(anthropic_client._client.messages, "create", fake_create)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with caplog.at_level(logging.WARNING):
        response = anthropic_client.complete(system="", user="hi")

    assert response.text == "ok"
    assert calls["count"] == 2
    assert any("fehlgeschlagen (Versuch" in record.message for record in caplog.records)


def test_complete_logs_error_when_retries_exhausted(anthropic_client, monkeypatch, caplog):
    def always_fails(**kwargs):
        raise _fake_status_error("overloaded")

    monkeypatch.setattr(anthropic_client._client.messages, "create", always_fails)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="Versuchen fehlgeschlagen"):
            anthropic_client.complete(system="", user="hi")

    assert any("endgueltig fehlgeschlagen" in record.message for record in caplog.records)
