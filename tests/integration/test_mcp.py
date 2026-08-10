"""Integration tests for MCP SSE server endpoints."""

from __future__ import annotations

import respx
import pytest
from fastapi.testclient import TestClient

from codebridge.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_mcp_sse_endpoint(client: TestClient):
    """GET /mcp/sse returns SSE stream with endpoint notification."""
    res = client.get("/mcp/sse")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert "event: endpoint" in res.text
    assert "data: /mcp/messages" in res.text


def test_mcp_initialize(client: TestClient):
    """POST /mcp/messages with initialize method returns MCP info."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    res = client.post("/mcp/messages", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert data["result"]["serverInfo"]["name"] == "CodeBridge MCP Gateway"


def test_mcp_tools_list(client: TestClient):
    """POST /mcp/messages with tools/list method returns available tools."""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }
    res = client.post("/mcp/messages", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) >= 1
    assert tools[0]["name"] == "codebridge_generate_code"


@respx.mock
def test_mcp_tools_call(client: TestClient):
    """POST /mcp/messages with tools/call executes tool via provider."""
    respx.post("https://integrate.api.nvidia.com/v1/chat/completions").respond(
        json={
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "def hello(): print('MCP CodeBridge')"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        }
    )

    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "codebridge_generate_code",
            "arguments": {"prompt": "Create a hello function"},
        },
    }
    res = client.post("/mcp/messages", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "result" in data
    content = data["result"]["content"]
    assert content[0]["type"] == "text"
    assert "def hello():" in content[0]["text"]
