"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from codebridge import __version__
from codebridge.api.chat import router as chat_router
from codebridge.api.diagnostics import router as diag_router
from codebridge.api.documents import router as documents_router
from codebridge.api.health import router as health_router
from codebridge.api.mcp import router as mcp_router
from codebridge.api.models import router as models_router
from codebridge.api.responses import router as responses_router
from codebridge.api.usage import router as usage_router
from codebridge.config import get_settings
from codebridge.providers.nvidia import reset_provider
from codebridge.security.auth import AuthError, auth_error_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(
        "CodeBridge Gateway v%s starting on %s:%s",
        __version__,
        settings.codebridge_host,
        settings.codebridge_port,
    )

    if not settings.nvidia_api_key_configured:
        logger.warning(
            "⚠️  NVIDIA_API_KEY is not configured. "
            "Set it in .env to enable NVIDIA requests."
        )
    else:
        logger.info("NVIDIA API: configured (key present)")

    logger.info(
        "Local token: %s...%s",
        settings.effective_token[:4],
        settings.effective_token[-4:],
    )

    if settings.nvidia_default_model:
        logger.info("Default model: %s", settings.nvidia_default_model)
    else:
        logger.warning("NVIDIA_DEFAULT_MODEL not set. Run 'codebridge models' after setup.")

    yield  # Server runs here

    # Shutdown
    logger.info("CodeBridge Gateway shutting down...")
    await reset_provider()
    logger.info("CodeBridge Gateway stopped.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CodeBridge Gateway",
        description="Local gateway connecting Codex to NVIDIA NIM",
        version=__version__,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    # CORS — localhost only by default
    allowed_origins = [
        f"http://127.0.0.1:{settings.codebridge_port}",
        f"http://localhost:{settings.codebridge_port}",
        "http://localhost",
        "http://127.0.0.1",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        return response

    # Root info endpoint
    @app.get("/")
    async def root() -> Any:
        return JSONResponse(
            content={
                "service": "CodeBridge Gateway",
                "version": __version__,
                "provider": "nvidia",
                "chat": "/chat",
                "mcp": "/mcp/sse",
                "docs": "/docs",
                "health": "/health",
                "diagnostics": "/diagnostics",
                "usage": "/usage",
                "models": "/v1/models",
            }
        )

    # Mount routers
    app.include_router(chat_router)
    app.include_router(mcp_router)
    app.include_router(responses_router)
    app.include_router(documents_router)
    app.include_router(models_router)
    app.include_router(health_router)
    app.include_router(diag_router)
    app.include_router(usage_router)

    # Auth error handler (must come before global handler)
    app.add_exception_handler(AuthError, auth_error_handler)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "type": "api_error",
                }
            },
        )

    return app
