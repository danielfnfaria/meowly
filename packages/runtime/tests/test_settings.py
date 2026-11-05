import pytest

from purr_runtime import ServerSettings, cached_settings


def test_the_defaults_are_the_container_defaults() -> None:
    settings = ServerSettings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.shutdown_timeout_seconds == 20


def test_the_environment_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PURR_PORT", "9000")
    assert ServerSettings().port == 9000


def test_cached_settings_reads_the_environment_once(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings = cached_settings(ServerSettings)
    monkeypatch.setenv("PURR_PORT", "9001")
    first = get_settings()
    monkeypatch.setenv("PURR_PORT", "9002")
    assert get_settings() is first
