from structcoder.config import load_settings


def test_default_config_loads_expected_values():
    settings = load_settings()

    assert settings.run.mode == "structural"
    assert settings.run.max_iterations == 5
    assert settings.benchmark.name == "humaneval"
    assert settings.llm.provider == "anthropic"
    assert settings.sandbox.timeout_s == 10
    assert settings.sandbox.network is False
