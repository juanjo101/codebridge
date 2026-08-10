"""
POST /v1/responses — main endpoint.

Codex sends OpenAI Responses API format.
CodeBridge translates to NVIDIA /v1/chat/completions (primary path).
Streaming is fully supported via SSE.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from codebridge.providers.nvidia import NvidiaProvider, NvidiaProviderError, get_provider
from codebridge.responses.compatibility import (
    chat_to_responses,
    responses_to_chat,
    stream_chat_to_responses,
)
from codebridge.responses.errors import error_response
from codebridge.routing.router import resolve_model
from codebridge.security.auth import validate_local_token
from codebridge.telemetry.storage import get_telemetry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/responses")
async def create_response(
    request: Request,
    _auth: None = Depends(validate_local_token),
) -> Any:
    """
    POST /v1/responses

    Accept Codex Responses API requests.
    Translate to NVIDIA /v1/chat/completions.
    Return Responses API format responses.
    """
    request_id = f"cb_{uuid.uuid4().hex[:16]}"
    start = time.monotonic()

    # Parse request body
    try:
        body: dict = await request.json()
    except Exception:
        return error_response("INVALID_REQUEST", "Could not parse JSON body", 400)

    # Resolve model
    try:
        model = resolve_model(body.get("model"))
    except ValueError as exc:
        return error_response("MODEL_NOT_FOUND", str(exc), 404)

    is_streaming = bool(body.get("stream", False))

    logger.info(
        "request id=%s model=%s stream=%s",
        request_id,
        model,
        is_streaming,
    )

    # Inject resolved model back into body
    body["model"] = model

    # Translate Responses → Chat Completions
    try:
        chat_payload = responses_to_chat(body)
    except Exception as exc:
        logger.exception("Translation error")
        return error_response("TRANSLATION_ERROR", str(exc), 500)

    provider: NvidiaProvider = get_provider()

    if is_streaming:
        return await _handle_streaming(
            provider, chat_payload, model, request_id, start
        )
    else:
        return await _handle_non_streaming(
            provider, chat_payload, model, request_id, start
        )


async def _handle_non_streaming(
    provider: NvidiaProvider,
    chat_payload: dict,
    model: str,
    request_id: str,
    start: float,
) -> Any:
    telemetry = get_telemetry()
    try:
        resp = await provider.chat_completions(chat_payload)
        chat_json = resp.json()

        # Convert to Responses format
        responses_json = chat_to_responses(chat_json, original_model=model)

        latency_ms = (time.monotonic() - start) * 1000
        usage = chat_json.get("usage", {})

        logger.info(
            "response id=%s model=%s status=200 duration=%.2fs",
            request_id,
            model,
            latency_ms / 1000,
        )

        telemetry.record_request(
            model=model,
            success=True,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
        return JSONResponse(content=responses_json)

    except NvidiaProviderError as exc:
        latency_ms = (time.monotonic() - start) * 1000
        logger.error("nvidia_error id=%s code=%s status=%d", request_id, exc.code, exc.status_code)
        telemetry.record_request(model=model, success=False, latency_ms=latency_ms)
        return error_response(exc.code, exc.message, exc.status_code)
    except Exception:
        latency_ms = (time.monotonic() - start) * 1000
        logger.exception("unexpected_error id=%s", request_id)
        telemetry.record_request(model=model, success=False, latency_ms=latency_ms)
        return error_response("INTERNAL_ERROR", "Internal gateway error", 500)


async def _handle_streaming(
    provider: NvidiaProvider,
    chat_payload: dict,
    model: str,
    request_id: str,
    start: float,
) -> StreamingResponse:
    telemetry = get_telemetry()

    async def generate():
        success = False
        try:
            nvidia_stream = provider.chat_completions_stream(chat_payload)
            async for chunk in stream_chat_to_responses(nvidia_stream, model, request_id):
                yield chunk
            success = True
        except NvidiaProviderError as exc:
            logger.error("stream_error id=%s code=%s", request_id, exc.code)
            import json

            err_event = {
                "type": "response.error",
                "error": {"code": exc.code, "message": exc.message},
            }
            yield f"event: error\ndata: {json.dumps(err_event)}\n\n".encode()
        except Exception:
            logger.exception("stream_unexpected_error id=%s", request_id)
            import json

            err_event = {"type": "response.error", "error": {"message": "Stream failed"}}
            yield f"event: error\ndata: {json.dumps(err_event)}\n\n".encode()
        finally:
            latency_ms = (time.monotonic() - start) * 1000
            logger.info(
                "stream_done id=%s model=%s success=%s duration=%.2fs",
                request_id,
                model,
                success,
                latency_ms / 1000,
            )
            telemetry.record_request(
                model=model,
                success=success,
                latency_ms=latency_ms,
                streaming=True,
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Request-Id": request_id,
        },
    )
