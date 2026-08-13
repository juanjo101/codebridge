"""Unit tests for DocumentService and document conversion API."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from codebridge.api.app import create_app
from codebridge.services.document import DocumentService, get_document_service


def test_document_service_convert_text(tmp_path: Path):
    service = get_document_service()
    test_file = tmp_path / "sample.html"
    test_file.write_text("<h1>Title</h1><p>Hello world from test HTML</p>", encoding="utf-8")

    result = service.convert_file(test_file)
    assert "Title" in result or "Hello world" in result


def test_document_service_convert_bytes():
    service = get_document_service()
    html_content = b"<h2>Document Subtitle</h2><p>Content inside bytes</p>"

    result = service.convert_bytes(html_content, "sample.html")
    assert "Subtitle" in result or "Content inside" in result


def test_document_service_missing_file():
    service = get_document_service()
    with pytest.raises(FileNotFoundError):
        service.convert_file("/nonexistent/file/path.pdf")


def test_convert_api_endpoint(tmp_path: Path):
    app = create_app()
    client = TestClient(app)

    # Missing token -> 401
    resp = client.post("/v1/documents/convert")
    assert resp.status_code == 401

    # Valid token
    from codebridge.config import get_settings
    token = get_settings().effective_token
    headers = {"Authorization": f"Bearer {token}"}

    test_file = tmp_path / "doc.html"
    test_file.write_text("<p>Testing API endpoint document conversion</p>", encoding="utf-8")

    # Convert by file path
    payload = {"file_path": str(test_file)}
    resp = client.post("/v1/documents/convert", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
    assert "Testing API endpoint" in data.get("markdown", "")
