"""
POST /v1/images/generations — OpenAI compatible image generation endpoint.

Routes requests to NVIDIA NIM GenAI image models (e.g. FLUX.1 [dev], SDXL).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from codebridge.providers.nvidia import NvidiaProviderError, get_provider
from codebridge.security.auth import validate_local_token

logger = logging.getLogger(__name__)

router = APIRouter()


class ImageGenerationRequest(BaseModel):
    """OpenAI compatible image generation request model."""

    prompt: str = Field(..., description="Text description of the desired image(s)")
    model: str | None = Field(
        default="black-forest-labs/flux.1-dev",
        description="NVIDIA NIM image model ID (e.g. black-forest-labs/flux.1-dev, stabilityai/sdxl-turbo)",
    )
    n: int | None = Field(default=1, ge=1, le=4, description="Number of images to generate")
    size: str | None = Field(default="1024x1024", description="Size of generated images")
    response_format: str | None = Field(
        default="b64_json",
        description="Format of generated images: 'b64_json' or 'url'",
    )


@router.post("/v1/images/generations", dependencies=[Depends(validate_local_token)])
async def generate_images(request: ImageGenerationRequest) -> Any:
    """Generate realistic images using NVIDIA NIM image models (FLUX.1, SDXL, etc.)."""
    try:
        provider = get_provider()
        result = await provider.generate_image(
            prompt=request.prompt,
            model=request.model,
            size=request.size,
            response_format=request.response_format,
        )
        return JSONResponse(content=result)
    except NvidiaProviderError as exc:
        logger.error("Image generation error [%s]: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "type": "invalid_request_error" if exc.status_code < 500 else "api_error",
                }
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during image generation")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "type": "api_error",
                }
            },
        )
