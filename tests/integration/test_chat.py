"""Integration tests for Web GUI Chat endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from codebridge.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_chat_ui(client: TestClient):
    """GET /chat returns the HTML SPA."""
    res = client.get("/chat")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "CodeBridge Web Chat" in res.text
    assert "meta/llama-3.3-70b-instruct" in res.text


def test_root_info(client: TestClient):
    """GET / returns JSON with /chat and /mcp links."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["chat"] == "/chat"
    assert data["mcp"] == "/mcp/sse"
