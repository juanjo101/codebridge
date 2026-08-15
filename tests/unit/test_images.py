"""Unit tests for POST /v1/images/generations endpoint and NvidiaProvider.generate_image."""

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from codebridge.api.app import create_app
from codebridge.config import get_settings
from codebridge.providers.nvidia import NvidiaProvider, reset_provider


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def auth_headers():
    settings = get_settings()
    return {"Authorization": f"Bearer {settings.effective_token}"}


@pytest.mark.asyncio
async def test_generate_image_provider_success():
    """Test NvidiaProvider.generate_image returns formatted OpenAI image dictionary."""
    await reset_provider()
    provider = NvidiaProvider()

    with respx.mock:
        respx.post("https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev").mock(

            return_value=Response(
                200,
                json={"b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="},
            )
        )

        result = await provider.generate_image(
            prompt="A realistic cat astronaut",
            model="black-forest-labs/flux.1-dev",
        )

        assert "created" in result
        assert "data" in result
        assert len(result["data"]) == 1
        assert "b64_json" in result["data"][0]
        assert result["data"][0]["b64_json"].startswith("iVBORw0KGgo")

    await provider.close()


@pytest.mark.asyncio
async def test_images_endpoint_unauthorized(app):
    """Test /v1/images/generations rejects requests without local token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/images/generations",
            json={"prompt": "A realistic tiger in the snow"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_images_endpoint_success(app, auth_headers):
    """Test /v1/images/generations returns 200 and image payload with valid token."""
    await reset_provider()
    with respx.mock:
        respx.post("https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev").mock(

            return_value=Response(
                200,
                json={"b64_json": "FAKE_B64_IMAGE_STRING"},
            )
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/images/generations",
                headers=auth_headers,
                json={
                    "prompt": "A realistic photo of mountains at sunset",
                    "model": "black-forest-labs/flux.1-dev",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "data" in data
            assert data["data"][0]["b64_json"] == "FAKE_B64_IMAGE_STRING"
