import pytest
from pydantic import ValidationError

from scraper.settings import AISettings


def _clear_ai_env(monkeypatch):
    for var in (
        "AI_PROVIDER",
        "OPENAI_MODEL",
        "GEMINI_MODEL",
        "OLLAMA_MODEL",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "OLLAMA_BASE_URL",
        "OLLAMA_STARTUP_TIMEOUT",
    ):
        monkeypatch.delenv(var, raising=False)


def test_loads_provider_and_models_from_env(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_API_KEY", "key-123")

    settings = AISettings()

    assert settings.provider == "openai"
    assert settings.openai_model == "gpt-4o"
    assert settings.openai_api_key == "key-123"


def test_model_defaults_apply_when_unset(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    settings = AISettings()

    assert settings.ollama_model == "llama3"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_startup_timeout_seconds == 15.0


def test_ollama_startup_timeout_overridable_from_env(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_STARTUP_TIMEOUT", "30")

    settings = AISettings()

    assert settings.ollama_startup_timeout_seconds == 30.0


def test_inactive_provider_fields_are_still_readable(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "key-456")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3:8b")

    settings = AISettings()

    assert settings.provider == "gemini"
    assert settings.openai_model == "gpt-4o"
    assert settings.ollama_model == "llama3:8b"


def test_missing_provider_raises_validation_error(monkeypatch):
    _clear_ai_env(monkeypatch)

    with pytest.raises(ValidationError):
        AISettings()


def test_invalid_provider_raises_validation_error(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "claude")

    with pytest.raises(ValidationError):
        AISettings()


def test_openai_provider_without_api_key_raises_validation_error(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")

    with pytest.raises(ValidationError):
        AISettings()


def test_gemini_provider_without_api_key_raises_validation_error(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "gemini")

    with pytest.raises(ValidationError):
        AISettings()


def test_ollama_provider_requires_no_api_key(monkeypatch):
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    settings = AISettings()

    assert settings.provider == "ollama"
