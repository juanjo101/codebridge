"""Model catalog with in-memory cache."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    id: str
    provider: str = "nvidia"
    available: bool = True
    capabilities: list[str] = field(default_factory=list)
    last_checked: float = field(default_factory=time.time)
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "available": self.available,
            "capabilities": self.capabilities,
            "last_checked": self.last_checked,
        }


class ModelCatalog:
    """In-memory model catalog with TTL-based cache."""

    def __init__(self, ttl: int = 300) -> None:
        self._ttl = ttl
        self._models: dict[str, ModelInfo] = {}
        self._last_refresh: float = 0.0

    def is_stale(self) -> bool:
        return time.time() - self._last_refresh > self._ttl

    def update(self, raw_models: list[dict]) -> None:
        """Parse and store models from NVIDIA /v1/models response."""
        new_catalog: dict[str, ModelInfo] = {}
        for raw in raw_models:
            model_id = raw.get("id", "")
            if not model_id:
                continue
            capabilities = _infer_capabilities(model_id)
            new_catalog[model_id] = ModelInfo(
                id=model_id,
                provider="nvidia",
                available=True,
                capabilities=capabilities,
                last_checked=time.time(),
                raw=raw,
            )
        self._models = new_catalog
        self._last_refresh = time.time()
        logger.info("model_catalog_updated count=%d", len(new_catalog))

    def get_model(self, model_id: str) -> ModelInfo | None:
        return self._models.get(model_id)

    def list_models(self) -> list[ModelInfo]:
        return list(self._models.values())

    def has_model(self, model_id: str) -> bool:
        return model_id in self._models

    def count(self) -> int:
        return len(self._models)

    def to_openai_format(self) -> dict:
        """Return model list in OpenAI /v1/models format."""
        return {
            "object": "list",
            "data": [
                {
                    "id": m.id,
                    "object": "model",
                    "created": int(m.last_checked),
                    "owned_by": "nvidia",
                    "capabilities": m.capabilities,
                }
                for m in self._models.values()
            ],
        }


def _infer_capabilities(model_id: str) -> list[str]:
    """Infer model capabilities from its ID string."""
    caps = ["chat"]
    mid = model_id.lower()
    if any(k in mid for k in ("instruct", "chat", "nemotron")):
        caps.append("instruction-following")
    if any(k in mid for k in ("code", "coder", "deepseek", "starcoder", "qwen-coder")):
        caps.append("coding")
    if any(k in mid for k in ("reason", "think", "r1", "o1", "o3")):
        caps.append("reasoning")
    if any(k in mid for k in ("70b", "72b", "405b", "671b")):
        caps.append("large")
    elif any(k in mid for k in ("7b", "8b", "14b")):
        caps.append("fast")
    return caps


# Singleton
_catalog: ModelCatalog | None = None


def get_catalog() -> ModelCatalog:
    global _catalog
    if _catalog is None:
        from codebridge.config import get_settings

        settings = get_settings()
        _catalog = ModelCatalog(ttl=settings.codebridge_model_cache_ttl)
    return _catalog


def reset_catalog() -> None:
    global _catalog
    _catalog = None
