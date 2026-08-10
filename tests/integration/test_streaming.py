"""Integration tests for SSE streaming."""

import json

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
    monkeypatch.setattr(
        "codebridge.config._settings",
        Settings(
            _env_file=None,
            nvidia_api_key="nvapi-testkey",
            nvidia_base_url=NVIDIA_BASE,
            nvidia_default_model=TEST_MODEL,
            codebridge_local_token=TEST_TOKEN,
        ),
    )
    reset_catalog()
    reset_telemetry()
    yield
    reset_telemetry()
    reset_catalog()


@pytest.fixture
def client(reset_singletons):
    import codebridge.providers.nvidia as nvidia_mod
    nvidia_mod._provider = None
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


def _build_sse_chunk(content: str) -> bytes:
    """Build a fake NVIDIA SSE chunk."""
    data = {
        "choices": [{"delta": {"content": content}, "finish_reason": None}]
    }
    return f"data: {json.dumps(data)}\n\n".encode()


def _build_sse_done() -> bytes:
    return b"data: [DONE]\n\n"


@respx.mock
def test_streaming_produces_sse_events(client):
    """Streaming request returns SSE events in Responses API format."""
    chunks = [
        _build_sse_chunk("Hello"),
        _build_sse_chunk(" world"),
        _build_sse_done(),
    ]
    stream_content = b"".join(chunks)

    respx.post(f"{NVIDIA_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            content=stream_content,
            headers={"content-type": "text/event-stream"},
        )
    )

    with client.stream(
        "POST",
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "Say hello", "stream": True},
        headers=AUTH_HEADERS,
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        raw = resp.read()
        text = raw.decode()

        # Should have response.created and response.completed
        assert "response.created" in text
        assert "response.completed" in text
        # Should have text deltas
        assert "response.output_text.delta" in text
        # Content must be present
        assert "Hello" in text
        assert "world" in text


@respx.mock
def test_streaming_tool_calls_preserved(client):
    """Tool call deltas accumulate and appear in response.completed."""
    chunks = [
        b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_XYZ","type":"function","function":{"name":"read_file","arguments":""}}]},"finish_reason":null}]}\n\n',
        b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"path\\": \\"/tmp\\"}"}}]},"finish_reason":null}]}\n\n',
        b"data: [DONE]\n\n",
    ]

    respx.post(f"{NVIDIA_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            content=b"".join(chunks),
            headers={"content-type": "text/event-stream"},
        )
    )

    with client.stream(
        "POST",
        "/v1/responses",
        json={"model": TEST_MODEL, "input": "List files", "stream": True},
        headers=AUTH_HEADERS,
    ) as resp:
        raw = resp.read().decode()
        # The completed event should contain the function call info
        assert "response.completed" in raw
        # Should have the function name
        assert "read_file" in raw
