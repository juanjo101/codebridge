"""Unit tests for model catalog and router."""

import time

from codebridge.models.catalog import ModelCatalog, _infer_capabilities


def test_catalog_update_and_list():
    catalog = ModelCatalog(ttl=300)
    raw = [
        {"id": "nvidia/llama-3.1-70b-instruct", "object": "model"},
        {"id": "nvidia/deepseek-coder-v2", "object": "model"},
    ]
    catalog.update(raw)
    assert catalog.count() == 2
    models = catalog.list_models()
    ids = [m.id for m in models]
    assert "nvidia/llama-3.1-70b-instruct" in ids


def test_catalog_has_model():
    catalog = ModelCatalog()
    catalog.update([{"id": "nvidia/test-model"}])
    assert catalog.has_model("nvidia/test-model")
    assert not catalog.has_model("nonexistent/model")


def test_catalog_staleness():
    catalog = ModelCatalog(ttl=0)
    catalog.update([{"id": "test"}])
    # With TTL=0, it's immediately stale
    time.sleep(0.01)
    assert catalog.is_stale()


def test_catalog_openai_format():
    catalog = ModelCatalog()
    catalog.update([{"id": "nvidia/test-model"}])
    result = catalog.to_openai_format()
    assert result["object"] == "list"
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "nvidia/test-model"
    assert result["data"][0]["owned_by"] == "nvidia"


def test_capability_inference_coding():
    caps = _infer_capabilities("nvidia/deepseek-coder-v2")
    assert "coding" in caps


def test_capability_inference_reasoning():
    caps = _infer_capabilities("nvidia/nemotron-think-8b")
    assert "reasoning" in caps


def test_capability_inference_large():
    caps = _infer_capabilities("meta/llama-3.1-70b-instruct")
    assert "large" in caps


def test_capability_inference_fast():
    caps = _infer_capabilities("meta/llama-3.2-8b-instruct")
    assert "fast" in caps


def test_resolve_model_openai_fallback():
    from codebridge.routing.router import resolve_model
    from codebridge.config import reset_settings
    reset_settings()
    catalog = ModelCatalog()
    catalog.update([{"id": "meta/llama-3.3-70b-instruct"}])
    resolved = resolve_model("gpt-5.6-sol", catalog=catalog)
    assert resolved == "meta/llama-3.3-70b-instruct"

