"""Error normalization — consistent error responses for clients."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def error_response(
    code: str,
    message: str,
    status_code: int = 500,
    extra: dict | None = None,
) -> JSONResponse:
    """Return a normalized JSON error response compatible with OpenAI error format."""
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "type": _code_to_type(code),
        }
    }
    if extra:
        body["error"].update(extra)
    return JSONResponse(status_code=status_code, content=body)


def _code_to_type(code: str) -> str:
    mapping = {
        "NVIDIA_API_KEY_NOT_CONFIGURED": "configuration_error",
        "NVIDIA_AUTH_FAILED": "auth_error",
        "NVIDIA_RATE_LIMITED": "rate_limit_error",
        "MODEL_NOT_FOUND": "invalid_request_error",
        "RESPONSES_NOT_SUPPORTED": "provider_error",
        "STREAM_FAILED": "provider_error",
        "TOOL_CALL_INCOMPATIBLE": "provider_error",
        "NVIDIA_UNAVAILABLE": "provider_error",
        "CODEBRIDGE_AUTH_FAILED": "auth_error",
    }
    return mapping.get(code, "api_error")
