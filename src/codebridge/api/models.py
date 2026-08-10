"""GET /v1/models endpoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from codebridge.models.catalog import get_catalog
from codebridge.providers.nvidia import NvidiaProviderError, get_provider
from codebridge.responses.errors import error_response
from codebridge.security.auth import validate_local_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/models")
async def list_models(
    request: Request,
    refresh: bool = False,
    _auth: None = Depends(validate_local_token),
) -> Any:
    """
    GET /v1/models

    Returns available NVIDIA models in OpenAI format.
    Uses TTL-cached catalog; pass ?refresh=true to force refresh.
    """
    catalog = get_catalog()
    provider = get_provider()

    if refresh or catalog.is_stale():
        try:
            raw_models = await provider.list_models()
            catalog.update(raw_models)
        except NvidiaProviderError as exc:
            if exc.status_code == 503:
                # API key not configured — return empty list with explanation
                return JSONResponse(
                    status_code=200,
                    content={
                        "object": "list",
                        "data": [],
                        "message": "NVIDIA_API_KEY not configured. Set it in .env to list models.",
                    },
                )
            logger.error("Failed to refresh model catalog: %s", exc.message)
            if catalog.count() == 0:
                return error_response(exc.code, exc.message, exc.status_code)
            # Return stale cache on error
            logger.warning("Returning stale model cache due to refresh error")

    return JSONResponse(content=catalog.to_openai_format())
