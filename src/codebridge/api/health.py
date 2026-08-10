"""GET /health and /health/nvidia endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from codebridge import __version__
from codebridge.config import get_settings
from codebridge.models.catalog import get_catalog
from codebridge.providers.nvidia import get_provider

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health() -> Any:
    """GET /health — quick liveness check."""
    settings = get_settings()
    catalog = get_catalog()

    return JSONResponse(
        content={
            "status": "ok",
            "service": "CodeBridge Gateway",
            "version": __version__,
            "provider": "nvidia",
            "nvidia_api_key": "configured" if settings.nvidia_api_key_configured else "NOT CONFIGURED",
            "nvidia_base_url": settings.nvidia_base_url_clean,
            "models_cached": catalog.count(),
            "default_model": settings.nvidia_default_model or "(not set)",
            "fallback_model": settings.nvidia_fallback_model or "(not set)",
            "responses_fallback": settings.codebridge_responses_fallback,
            "log_level": settings.codebridge_log_level,
        }
    )


@router.get("/health/nvidia")
async def health_nvidia() -> Any:
    """GET /health/nvidia — check NVIDIA API reachability."""
    provider = get_provider()
    result = await provider.health()
    status_code = 200 if result.get("status") == "ok" else 503
    return JSONResponse(content=result, status_code=status_code)
