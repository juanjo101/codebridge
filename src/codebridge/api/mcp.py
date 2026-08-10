"""
MCP Server protocol implementation (SSE transport).

Allows IDEs and MCP clients to connect to CodeBridge as an MCP server.
Endpoints:
  GET  /mcp/sse       - Establish SSE connection
  POST /mcp/messages  - Post JSON-RPC messages (initialize, tools/list, tools/call)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from codebridge.providers.nvidia import NvidiaProvider, get_provider
from codebridge.routing.router import resolve_model

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/mcp/sse")
@router.get("/sse")
async def mcp_sse_endpoint(request: Request) -> StreamingResponse:
    """Establish MCP SSE transport connection."""
    async def sse_generator():
        # Send endpoint event informing client where to send POST messages
        yield f"event: endpoint\ndata: http://127.0.0.1:8787/mcp/messages\n\n".encode("utf-8")

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/mcp/messages")
@router.post("/messages")
@router.post("/mcp/sse")
@router.post("/sse")
async def mcp_messages_endpoint(request: Request) -> JSONResponse:
    """Handle MCP JSON-RPC 2.0 requests."""
    try:
        body: dict = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        )

    msg_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    logger.info("MCP request method=%s id=%s", method, msg_id)

    # 1. Initialize
    if method == "initialize":
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": "CodeBridge MCP Gateway",
                        "version": "1.0.0",
                    },
                },
            }
        )

    # 2. Notifications / initialized
    if method == "notifications/initialized":
        return JSONResponse(content={"status": "ok"})

    # 3. Tools / List
    if method == "tools/list":
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "codebridge_generate_code",
                            "description": "Generate or refactor code using NVIDIA NIM models through CodeBridge",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "prompt": {
                                        "type": "string",
                                        "description": "Task or code generation request",
                                    },
                                    "model": {
                                        "type": "string",
                                        "description": "Optional model ID (defaults to meta/llama-3.3-70b-instruct)",
                                    },
                                },
                                "required": ["prompt"],
                            },
                        }
                    ]
                },
            }
        )

    # 4. Tools / Call
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        prompt = arguments.get("prompt", "")
        model_name = resolve_model(arguments.get("model"))

        provider: NvidiaProvider = get_provider()
        chat_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            resp = await provider.chat_completions(chat_payload)
            chat_json = resp.json()
            reply = (
                chat_json.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": reply,
                            }
                        ]
                    },
                }
            )
        except Exception as exc:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32603, "message": str(exc)},
                }
            )

    # Fallback for unknown methods
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {},
        }
    )
