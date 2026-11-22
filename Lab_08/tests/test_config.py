from sport_results.config import load_settings


def test_defaults() -> None:
    settings = load_settings({})
    assert settings.database_url == "sqlite:///data/api.db"
    assert (settings.retries, settings.concurrency) == (3, 2)


def test_environment_overrides() -> None:
    settings = load_settings({
        "SPORT_API_TIMEOUT": "0.5",
        "SPORT_API_RETRIES": "5",
        "SPORT_API_CONCURRENCY": "4",
        "SPORT_API_BASE_URL": "http://api.local",
    })
    assert settings.timeout == 0.5
    assert settings.retries == 5
    assert settings.concurrency == 4
    assert settings.api_base_url == "http://api.local"
