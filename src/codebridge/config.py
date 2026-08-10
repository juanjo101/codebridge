"""CodeBridge Gateway - Configuration."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Project root (codebridge/ directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """CodeBridge configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── NVIDIA ──────────────────────────────────────────────────────
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_default_model: str = ""
    nvidia_fallback_model: str = ""

    # ── CodeBridge server ───────────────────────────────────────────
    codebridge_host: str = "127.0.0.1"
    codebridge_port: int = 8787
    codebridge_local_token: str = ""

    # ── Protocol ────────────────────────────────────────────────────
    codebridge_responses_fallback: bool = True

    # ── Model cache ─────────────────────────────────────────────────
    codebridge_model_cache_ttl: int = 300

    # ── Logging ─────────────────────────────────────────────────────
    codebridge_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    codebridge_log_prompts: bool = False

    # ── Telemetry (local only) ───────────────────────────────────────
    codebridge_telemetry: bool = True

    # ── Timeouts ────────────────────────────────────────────────────
    codebridge_connect_timeout: float = 10.0
    codebridge_read_timeout: float = 300.0

    @field_validator("codebridge_host")
    @classmethod
    def warn_non_localhost(cls, v: str) -> str:
        if v not in ("127.0.0.1", "localhost", "::1"):
            logger.warning(
                "⚠️  SECURITY WARNING: CodeBridge is bound to '%s'. "
                "This may expose the gateway beyond localhost. "
                "Set CODEBRIDGE_HOST=127.0.0.1 for local-only access.",
                v,
            )
        return v

    @field_validator("codebridge_log_prompts")
    @classmethod
    def warn_log_prompts(cls, v: bool) -> bool:
        if v:
            logger.warning(
                "⚠️  SECURITY WARNING: CODEBRIDGE_LOG_PROMPTS=true — "
                "prompt content will be logged. Do not use in shared environments."
            )
        return v

    @property
    def nvidia_api_key_configured(self) -> bool:
        return bool(self.nvidia_api_key.strip())

    @property
    def effective_token(self) -> str:
        """Return the local auth token, generating + persisting one if absent."""
        if self.codebridge_local_token.strip():
            return self.codebridge_local_token.strip()
        return _load_or_generate_token()

    @property
    def nvidia_base_url_clean(self) -> str:
        return self.nvidia_base_url.rstrip("/")


_TOKEN_FILE = PROJECT_ROOT / ".codebridge_token"


def _load_or_generate_token() -> str:
    """Load persisted token or generate + save a new one."""
    if _TOKEN_FILE.exists():
        tok = _TOKEN_FILE.read_text().strip()
        if tok:
            return tok
    tok = secrets.token_urlsafe(32)
    try:
        _TOKEN_FILE.write_text(tok)
        _TOKEN_FILE.chmod(0o600)
    except OSError as exc:
        logger.warning("Could not persist local token: %s", exc)
    return tok


# Singleton — imported everywhere else
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset singleton (for testing)."""
    global _settings
    _settings = None
