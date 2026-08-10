"""Unit tests for config module."""


from codebridge.config import Settings


def test_default_settings():
    """Settings have secure defaults."""
    settings = Settings(
        _env_file=None,
        nvidia_api_key="",
    )
    assert settings.codebridge_host == "127.0.0.1"
    assert settings.codebridge_port == 8787
    assert settings.codebridge_responses_fallback is True
    assert settings.codebridge_log_prompts is False


def test_nvidia_key_configured():
    settings = Settings(_env_file=None, nvidia_api_key="nvapi-testkey123")
    assert settings.nvidia_api_key_configured is True


def test_nvidia_key_not_configured():
    settings = Settings(_env_file=None, nvidia_api_key="")
    assert settings.nvidia_api_key_configured is False


def test_base_url_strip_trailing_slash():
    settings = Settings(
        _env_file=None,
        nvidia_base_url="https://integrate.api.nvidia.com/v1/",
    )
    assert not settings.nvidia_base_url_clean.endswith("/")


def test_effective_token_generated():
    """Token is auto-generated if not set."""
    settings = Settings(_env_file=None, codebridge_local_token="")
    token = settings.effective_token
    assert len(token) > 20


def test_effective_token_from_config():
    settings = Settings(_env_file=None, codebridge_local_token="mysecrettoken123")
    assert settings.effective_token == "mysecrettoken123"
