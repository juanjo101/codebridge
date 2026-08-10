"""Security: authentication and token validation."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from codebridge.config import get_settings

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication error — handled by the app's exception handler."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """FastAPI exception handler for AuthError."""
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "type": "auth_error",
            }
        },
    )


def validate_local_token(request: Request) -> None:
    """
    Validate the CodeBridge local token from the Authorization header.

    Raises AuthError (→ HTTP 401) if the token is missing or invalid.
    The local token is NEVER forwarded to NVIDIA.
    """
    settings = get_settings()
    expected = settings.effective_token

    auth_header: str | None = request.headers.get("Authorization") or request.headers.get(
        "authorization"
    )

    if not auth_header:
        logger.warning("auth_failed=missing_token client=%s", _client_ip(request))
        raise AuthError(
            "CODEBRIDGE_AUTH_FAILED",
            "Missing Authorization header. Use: Authorization: Bearer <CODEBRIDGE_LOCAL_TOKEN>",
        )

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("auth_failed=malformed_header client=%s", _client_ip(request))
        raise AuthError(
            "CODEBRIDGE_AUTH_FAILED",
            "Authorization header must be: Bearer <token>",
        )

    token = parts[1].strip()
    # Constant-time comparison to avoid timing attacks
    import hmac

    if not hmac.compare_digest(token.encode(), expected.encode()):
        logger.warning("auth_failed=invalid_token client=%s", _client_ip(request))
        raise AuthError(
            "CODEBRIDGE_AUTH_FAILED",
            "Invalid local token. Check CODEBRIDGE_LOCAL_TOKEN in .env",
        )


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
