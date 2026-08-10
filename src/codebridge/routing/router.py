"""
Deterministic model router.

Selection order:
  1. Model explicitly requested in the request body
  2. NVIDIA_DEFAULT_MODEL from settings
  3. NVIDIA_FALLBACK_MODEL from settings
  4. First available model in catalog (last resort)

No AI-based selection in V1 — purely deterministic.
"""

from __future__ import annotations

import logging

from codebridge.config import get_settings
from codebridge.models.catalog import ModelCatalog, get_catalog

logger = logging.getLogger(__name__)


def resolve_model(
    requested_model: str | None = None,
    catalog: ModelCatalog | None = None,
) -> str:
    """
    Resolve the model to use for a request.

    Returns the model ID string. Never returns empty string.
    Raises ValueError if no model can be resolved.
    """
    settings = get_settings()
    cat = catalog or get_catalog()

    # 1. Explicitly requested model
    if requested_model and requested_model.strip():
        model = requested_model.strip()
        if cat.count() > 0 and not cat.has_model(model):
            logger.warning("model_not_in_catalog model=%s (using anyway)", model)
        logger.debug("model_resolved source=explicit model=%s", model)
        return model

    # 2. Configured default
    if settings.nvidia_default_model.strip():
        model = settings.nvidia_default_model.strip()
        logger.debug("model_resolved source=default model=%s", model)
        return model

    # 3. Configured fallback
    if settings.nvidia_fallback_model.strip():
        model = settings.nvidia_fallback_model.strip()
        logger.debug("model_resolved source=fallback_config model=%s", model)
        return model

    # 4. First available in catalog
    models = cat.list_models()
    if models:
        model = models[0].id
        logger.warning(
            "model_resolved source=catalog_first model=%s "
            "(set NVIDIA_DEFAULT_MODEL in .env to avoid this)",
            model,
        )
        return model

    raise ValueError(
        "No model available. Set NVIDIA_DEFAULT_MODEL in .env "
        "or run: codebridge models"
    )
