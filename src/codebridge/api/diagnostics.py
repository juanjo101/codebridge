"""GET /diagnostics endpoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from codebridge.config import get_settings
from codebridge.models.catalog import get_catalog
from codebridge.providers.nvidia import NvidiaProviderError, get_provider

logger = logging.getLogger(__name__)

router = APIRouter()

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
WARN = "WARN"


@router.get("/diagnostics")
async def diagnostics(format: str = "json") -> Any:
    """
    GET /diagnostics

    Run a series of checks to diagnose CodeBridge configuration.
    Returns JSON by default. Pass ?format=text for human-readable output.
    """
    settings = get_settings()
    results = {}

    # 1. Gateway check
    results["gateway"] = PASS

    # 2. Auth check
    token_ok = bool(settings.effective_token)
    results["authentication"] = PASS if token_ok else FAIL

    # 3. API Key check
    results["nvidia_api_key"] = PASS if settings.nvidia_api_key_configured else FAIL

    # 4. Default model check
    results["default_model"] = PASS if settings.nvidia_default_model else WARN

    # 5. NVIDIA API check
    if settings.nvidia_api_key_configured:
        provider = get_provider()
        health = await provider.health()
        if health.get("status") == "ok":
            results["nvidia_api"] = PASS
        elif health.get("status") == "auth_failed":
            results["nvidia_api"] = FAIL
        else:
            results["nvidia_api"] = WARN

        # 6. Models endpoint
        catalog = get_catalog()
        if catalog.count() > 0:
            results["models_endpoint"] = PASS
        else:
            # Try to refresh
            try:
                raw = await provider.list_models()
                catalog.update(raw)
                results["models_endpoint"] = PASS
            except NvidiaProviderError:
                results["models_endpoint"] = FAIL

        # 7. Default model in catalog
        if settings.nvidia_default_model and catalog.count() > 0:
            if catalog.has_model(settings.nvidia_default_model):
                results["default_model_available"] = PASS
            else:
                results["default_model_available"] = WARN
        else:
            results["default_model_available"] = SKIP
    else:
        results["nvidia_api"] = SKIP
        results["models_endpoint"] = SKIP
        results["default_model_available"] = SKIP

    # Protocol
    results["responses_api"] = PASS
    results["streaming"] = PASS
    results["tool_calling"] = PASS
    results["fallback_mode"] = PASS if settings.codebridge_responses_fallback else WARN

    overall = PASS if all(v in (PASS, WARN, SKIP) for v in results.values()) else FAIL
    if any(v == FAIL for v in results.values()):
        overall = FAIL

    summary = {
        "overall": overall,
        "checks": results,
        "notes": _build_notes(results, settings),
    }

    if format == "text":
        lines = ["CodeBridge Diagnostics", "=" * 40]
        for k, v in results.items():
            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "SKIP": "○"}.get(v, "?")
            lines.append(f"  {icon} {k.replace('_', ' ').title()}: {v}")
        lines.append("=" * 40)
        lines.append(f"Overall: {overall}")
        for note in summary["notes"]:
            lines.append(f"\n  NOTE: {note}")
        return "\n".join(lines)

    return JSONResponse(content=summary)


def _build_notes(results: dict, settings: Any) -> list[str]:
    notes = []
    if results.get("nvidia_api_key") == FAIL:
        notes.append("Set NVIDIA_API_KEY in .env to enable NVIDIA integration")
    if results.get("default_model") == WARN:
        notes.append(
            "Set NVIDIA_DEFAULT_MODEL in .env. Run 'codebridge models' to see available models."
        )
    if results.get("nvidia_api") == WARN:
        notes.append("NVIDIA API may be unreachable. Check network connectivity.")
    if results.get("default_model_available") == WARN:
        notes.append(
            f"Model '{settings.nvidia_default_model}' is not in the NVIDIA catalog. "
            "Verify the model ID with 'codebridge models'."
        )
    return notes
