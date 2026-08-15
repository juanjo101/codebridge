"""NVIDIA NIM provider — the core backend abstraction."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx

from codebridge.config import Settings, get_settings

logger = logging.getLogger(__name__)

# NVIDIA returns 404 for /v1/responses on hosted service
# We track this so we can auto-enable fallback
_RESPONSES_NOT_SUPPORTED_CODES = {404, 501}

# Headers to strip from Codex request before forwarding to NVIDIA
_STRIP_REQUEST_HEADERS = {
    "authorization",
    "host",
    "content-length",
    "transfer-encoding",
    "connection",
}

# Headers to strip from NVIDIA response before forwarding to Codex
_STRIP_RESPONSE_HEADERS = {
    "content-length",
    "transfer-encoding",
    "connection",
}

IMAGE_MODEL_ENDPOINTS = {
    "black-forest-labs/flux.1-dev": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-1-dev",
    "black-forest-labs/flux.1-schnell": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-1-schnell",
    "flux.1-dev": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-1-dev",
    "flux.1-schnell": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-1-schnell",
    "stabilityai/stable-diffusion-3-medium": "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium",
    "stabilityai/sdxl-turbo": "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo",
    "stabilityai/stable-diffusion-xl": "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl",
    "sdxl": "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl",
}



class NvidiaProviderError(Exception):
    """Error from NVIDIA provider."""

    def __init__(self, code: str, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NvidiaProvider:
    """
    NVIDIA NIM provider.

    Architecture:
      Codex /v1/responses → CodeBridge → NVIDIA /v1/chat/completions (primary)
      Optionally: NVIDIA /v1/responses if supported and fallback=false

    The Responses→ChatCompletions adapter is always active because
    NVIDIA hosted service does not support /v1/responses reliably.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._responses_supported: bool | None = None  # None = unknown

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self._settings.codebridge_connect_timeout,
                    read=self._settings.codebridge_read_timeout,
                    write=30.0,
                    pool=5.0,
                ),
                headers={
                    "Authorization": f"Bearer {self._settings.nvidia_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "CodeBridge/1.0.0",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health(self) -> dict:
        """Check NVIDIA API reachability via /v1/models."""
        if not self._settings.nvidia_api_key_configured:
            return {"status": "unconfigured", "message": "NVIDIA_API_KEY not set"}
        try:
            client = self._get_client()
            resp = await client.get(
                f"{self._settings.nvidia_base_url_clean}/models",
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("data", []))
                return {"status": "ok", "models": count}
            elif resp.status_code == 401:
                return {"status": "auth_failed", "message": "Invalid NVIDIA API key"}
            else:
                return {"status": "error", "http_status": resp.status_code}
        except httpx.ConnectError:
            return {"status": "unreachable", "message": "Cannot connect to NVIDIA API"}
        except httpx.TimeoutException:
            return {"status": "timeout", "message": "NVIDIA API timeout"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    async def list_models(self) -> list[dict]:
        """Fetch model list from NVIDIA /v1/models."""
        if not self._settings.nvidia_api_key_configured:
            raise NvidiaProviderError(
                "NVIDIA_API_KEY_NOT_CONFIGURED",
                "NVIDIA_API_KEY is not set in .env",
                status_code=503,
            )
        try:
            client = self._get_client()
            resp = await client.get(f"{self._settings.nvidia_base_url_clean}/models")
            _raise_for_nvidia_error(resp)
            data = resp.json()
            return data.get("data", [])
        except NvidiaProviderError:
            raise
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc) from exc
        except httpx.ConnectError as exc:
            raise NvidiaProviderError(
                "NVIDIA_UNAVAILABLE", f"Cannot connect to NVIDIA: {exc}", 503
            ) from exc

    async def chat_completions(self, payload: dict) -> httpx.Response:
        """POST to NVIDIA /v1/chat/completions (non-streaming)."""
        if not self._settings.nvidia_api_key_configured:
            raise NvidiaProviderError("NVIDIA_API_KEY_NOT_CONFIGURED", "API key not set", 503)
        try:
            client = self._get_client()
            resp = await client.post(
                f"{self._settings.nvidia_base_url_clean}/chat/completions",
                json=payload,
            )
            _raise_for_nvidia_error(resp)
            return resp
        except NvidiaProviderError:
            raise
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc) from exc
        except httpx.ConnectError as exc:
            raise NvidiaProviderError("NVIDIA_UNAVAILABLE", str(exc), 503) from exc

    async def chat_completions_stream(
        self, payload: dict
    ) -> AsyncIterator[bytes]:
        """Stream from NVIDIA /v1/chat/completions."""
        if not self._settings.nvidia_api_key_configured:
            raise NvidiaProviderError("NVIDIA_API_KEY_NOT_CONFIGURED", "API key not set", 503)
        client = self._get_client()
        try:
            async with client.stream(
                "POST",
                f"{self._settings.nvidia_base_url_clean}/chat/completions",
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise NvidiaProviderError(
                        "STREAM_FAILED",
                        f"NVIDIA returned {response.status_code}: {body.decode()}",
                        response.status_code,
                    )
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
        except NvidiaProviderError:
            raise
        except httpx.ConnectError as exc:
            raise NvidiaProviderError("NVIDIA_UNAVAILABLE", str(exc), 503) from exc
        except httpx.RemoteProtocolError as exc:
            raise NvidiaProviderError("STREAM_FAILED", f"Stream error: {exc}", 500) from exc

    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        size: str | None = "1024x1024",
        response_format: str | None = "b64_json",
        cfg_scale: float | None = 3.5,
        steps: int | None = 28,
    ) -> dict:
        """Generate images via NVIDIA GenAI API endpoints."""
        if not self._settings.nvidia_api_key_configured:
            raise NvidiaProviderError("NVIDIA_API_KEY_NOT_CONFIGURED", "API key not set", 503)

        model_name = model or "black-forest-labs/flux.1-dev"
        endpoint = IMAGE_MODEL_ENDPOINTS.get(model_name)
        if not endpoint:
            # Fallback to constructing NVIDIA GenAI URL
            cleaned = model_name.replace(".", "-")
            endpoint = f"https://ai.api.nvidia.com/v1/genai/{cleaned}"

        client = self._get_client()
        payload = {
            "prompt": prompt,
            "mode": "base64",
        }
        if cfg_scale is not None:
            payload["cfg_scale"] = cfg_scale
        if steps is not None:
            payload["steps"] = steps

        try:
            resp = await client.post(endpoint, json=payload)
            _raise_for_nvidia_error(resp)
            data = resp.json()
            
            # Extract image base64 from NVIDIA response variations
            b64_data = (
                data.get("b64_json")
                or data.get("image")
                or (data.get("artifacts", [{}])[0].get("base64"))
            )
            if not b64_data and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                b64_data = data["data"][0].get("b64_json") or data["data"][0].get("b64")

            if not b64_data:
                raise NvidiaProviderError(
                    "IMAGE_GEN_FAILED",
                    "NVIDIA response did not contain image data",
                    500,
                )

            import time
            item: dict[str, str] = {}
            if response_format == "url":
                # Data URL format if caller requested url
                item["url"] = f"data:image/png;base64,{b64_data}"
            else:
                item["b64_json"] = b64_data

            return {
                "created": int(time.time()),
                "data": [item],
            }
        except NvidiaProviderError:
            raise
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc) from exc
        except httpx.ConnectError as exc:
            raise NvidiaProviderError("NVIDIA_UNAVAILABLE", str(exc), 503) from exc



def _raise_for_nvidia_error(resp: httpx.Response) -> None:
    """Raise NvidiaProviderError for error HTTP responses."""
    if resp.status_code < 400:
        return
    try:
        body = resp.json()
        err = body.get("error", {})
        message = err.get("message", resp.text)
        code = err.get("code", "NVIDIA_ERROR")
    except Exception:
        message = resp.text
        code = "NVIDIA_ERROR"

    if resp.status_code == 401:
        raise NvidiaProviderError("NVIDIA_AUTH_FAILED", message, 401)
    elif resp.status_code == 429:
        raise NvidiaProviderError("NVIDIA_RATE_LIMITED", message, 429)
    elif resp.status_code == 404:
        raise NvidiaProviderError("MODEL_NOT_FOUND", message, 404)
    else:
        raise NvidiaProviderError(code or "NVIDIA_ERROR", message, resp.status_code)


def _map_http_error(exc: httpx.HTTPStatusError) -> NvidiaProviderError:
    return NvidiaProviderError("NVIDIA_ERROR", str(exc), exc.response.status_code)


# Singleton
_provider: NvidiaProvider | None = None


def get_provider() -> NvidiaProvider:
    global _provider
    if _provider is None:
        _provider = NvidiaProvider()
    return _provider


async def reset_provider() -> None:
    global _provider
    if _provider:
        await _provider.close()
    _provider = None
