"""Integration tests for API endpoints using TestClient with mocked NVIDIA."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from codebridge.api.app import create_app
from codebridge.config import Settings
from codebridge.models.catalog import reset_catalog
from codebridge.telemetry.storage import reset_telemetry

TEST_TOKEN = "testtoken123456789012345678901234"
TEST_MODEL = "nvidia/test-model"
NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch):
    """Reset all singletons before each test."""
    # Patch settings
    monkeypatch.setattr(
        "codebridge.config._settings",
        Settings(
            _env_file=None,
            nvidia_api_key="nvapi-testkey",
            nvidia_base_url=NVIDIA_BASE,
            nvidia_default_model=TEST_MODEL,
            codebridge_local_token=TEST_TOKEN,
            codebridge_responses_fallback=True,
        ),
    )
    reset_catalog()
    reset_telemetry()
    yield
    reset_telemetry()
    reset_catalog()


@pytest.fixture
def client(reset_singletons):
    """Create test client with fresh app."""
    # Need to reset provider after settings are patched
    import codebridge.providers.nvidia as nvidia_mod
    nvidia_mod._provider = None
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


# ── Health endpoint ────────────────────────────────────────────────────────


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["provider"] == "nvidia"
    assert "version" in data


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "CodeBridge" in data["service"]


# ── Auth tests ─────────────────────────────────────────────────────────────


def test_auth_missing_token(client):
    resp = client.post("/v1/responses", json={"model": TEST_MODEL, "input": "hi"})
    assert resp.status_code == 401
    body = resp.json()
    # Error is either at body["error"] or body["detail"]["error"]
    err = body.get("error") or body.get("detail", {}).get("error", {})
    assert err.get("code") == "CODEBRIDGE_AUTH_FAILED"


def test_auth_wrong_token(client):
    resp = client.post(
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "hi"},
        headers={"Authorization": "Bearer wrongtoken"},
    )
    assert resp.status_code == 401


def test_auth_malformed_header(client):
    resp = client.post(
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "hi"},
        headers={"Authorization": "InvalidScheme token"},
    )
    assert resp.status_code == 401


# ── Models endpoint ────────────────────────────────────────────────────────


@respx.mock
def test_models_endpoint(client):
    respx.get(f"{NVIDIA_BASE}/models").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": "nvidia/llama-3.1-70b-instruct", "object": "model"},
                    {"id": "nvidia/deepseek-coder", "object": "model"},
                ]
            },
        )
    )
    resp = client.get("/v1/models", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 2


# ── Responses endpoint (non-streaming) ────────────────────────────────────


@respx.mock
def test_responses_simple(client):
    respx.post(f"{NVIDIA_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "chatcmpl-123",
                "model": TEST_MODEL,
                "created": 1700000000,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "Hello from NVIDIA!"},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )
    )

    resp = client.post(
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "Say hello"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["output_text"] == "Hello from NVIDIA!"


@respx.mock
def test_responses_tool_call_preserved(client):
    """Tool call ID and function name must survive the round trip."""
    respx.post(f"{NVIDIA_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "chatcmpl-456",
                "model": TEST_MODEL,
                "created": 1700000000,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_PRESERVE_ME",
                                    "type": "function",
                                    "function": {
                                        "name": "shell",
                                        "arguments": '{"command":"ls"}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )
    )

    resp = client.post(
        "/v1/responses",
        json={
            "model": TEST_MODEL,
            "input": "List files",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "shell",
                        "description": "Run shell command",
                        "parameters": {
                            "type": "object",
                            "properties": {"command": {"type": "string"}},
                        },
                    },
                }
            ],
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    fc_items = [o for o in data["output"] if o["type"] == "function_call"]
    assert len(fc_items) == 1
    assert fc_items[0]["call_id"] == "call_PRESERVE_ME"
    assert fc_items[0]["name"] == "shell"


@respx.mock
def test_nvidia_auth_error_returns_401(client):
    respx.post(f"{NVIDIA_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"message": "Invalid API key", "code": "NVIDIA_AUTH_FAILED"}},
        )
    )
    resp = client.post(
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "test"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "NVIDIA_AUTH_FAILED"


# ── Usage endpoint ─────────────────────────────────────────────────────────


def test_usage_endpoint(client):
    resp = client.get("/usage")
    assert resp.status_code == 200
    data = resp.json()
    assert "requests" in data
    assert "provider" in data
    assert data["provider"] == "nvidia"
