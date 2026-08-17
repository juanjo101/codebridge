"""
Responses API ↔ Chat Completions adapter.

Architecture:
  CodeBridge receives OpenAI Responses API format from Codex.
  NVIDIA NIM hosted service does NOT support /v1/responses (experimental/404).
  This adapter translates:
    Responses request → Chat Completions request  (to NVIDIA)
    Chat Completions response → Responses response (back to Codex)

Principle: translate ONLY what is necessary. Preserve all tool calls, IDs, etc.

SSE streaming:
  NVIDIA emits: data: {..., choices:[{delta:{content:"..."}}]} \n\n
  Codex expects: data: {type:"response.output_text.delta", delta:"..."} \n\n

This translation is the minimal compatibility shim.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger(__name__)


# ── Request: Responses → Chat Completions ──────────────────────────────────


def responses_to_chat(responses_req: dict) -> dict:
    """
    Convert a Responses API request body to a Chat Completions request body.

    Preserves: tools, tool_choice, temperature, max_output_tokens,
               reasoning parameters where possible.
    """
    chat: dict[str, Any] = {}

    # Model
    if "model" in responses_req:
        chat["model"] = responses_req["model"]

    # Input → messages
    chat["messages"] = _convert_input_to_messages(responses_req)

    # Stream
    if "stream" in responses_req:
        chat["stream"] = responses_req["stream"]

    # Max tokens
    if "max_output_tokens" in responses_req:
        chat["max_tokens"] = responses_req["max_output_tokens"]
    elif "max_tokens" in responses_req:
        chat["max_tokens"] = responses_req["max_tokens"]

    # Temperature
    if "temperature" in responses_req:
        chat["temperature"] = responses_req["temperature"]

    # Top-p
    if "top_p" in responses_req:
        chat["top_p"] = responses_req["top_p"]

    # Tools
    if "tools" in responses_req and responses_req["tools"]:
        converted_tools = _convert_tools(responses_req["tools"])
        if converted_tools:
            chat["tools"] = converted_tools

    # Tool choice
    if "tool_choice" in responses_req:
        chat["tool_choice"] = responses_req["tool_choice"]

    # Stop sequences
    if "stop" in responses_req:
        chat["stop"] = responses_req["stop"]

    # Stream options (for token usage in streaming)
    if chat.get("stream"):
        chat["stream_options"] = {"include_usage": True}

    # Reasoning: Nemotron and similar support "thinking" via chat
    # We do not fabricate reasoning; if model supports it via a param, pass it
    if "reasoning" in responses_req:
        reasoning = responses_req["reasoning"]
        if isinstance(reasoning, dict):
            effort = reasoning.get("effort", "")
            # Some NVIDIA models accept thinking budget as max_tokens hint
            # Log the decision; do not invent unsupported parameters
            logger.debug(
                "reasoning_requested effort=%s (may not be supported by NVIDIA)", effort
            )

    # User metadata (ignored by NVIDIA but harmless to omit)
    # Do not forward 'store', 'conversation_id', 'previous_response_id' — NVIDIA doesn't support

    return chat


def _convert_input_to_messages(req: dict) -> list[dict]:
    """Convert Responses API 'input' field to Chat Completions 'messages' list."""
    messages: list[dict] = []

    # System / instructions
    instructions = req.get("instructions") or req.get("system")
    if instructions:
        messages.append({"role": "system", "content": instructions})

    raw_input = req.get("input", "")

    if isinstance(raw_input, str):
        # Simple string input
        if raw_input:
            messages.append({"role": "user", "content": raw_input})
    elif isinstance(raw_input, list):
        # Array of message objects
        for item in raw_input:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "user")
            content = item.get("content", "")

            if isinstance(content, str):
                messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Content parts (text, image_url, etc.)
                text_parts = []
                other_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "input_text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "tool_result":
                            # Tool results come as function messages
                            pass
                        else:
                            other_parts.append(part)

                if text_parts and not other_parts:
                    messages.append({"role": role, "content": "\n".join(text_parts)})
                elif text_parts or other_parts:
                    # Mixed content — pass as-is for NVIDIA
                    messages.append({"role": role, "content": content})

            # Tool calls from assistant
            if "tool_calls" in item:
                msg: dict[str, Any] = {"role": role}
                if content:
                    msg["content"] = content if isinstance(content, str) else None
                msg["tool_calls"] = item["tool_calls"]
                messages.append(msg)
                continue

            # Tool results (function outputs)
            if role == "tool" and "tool_call_id" in item:
                result_content = item.get("output", item.get("content", ""))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": item["tool_call_id"],
                        "content": str(result_content) if result_content is not None else "",
                    }
                )

    else:
        logger.warning("Unexpected input type: %s", type(raw_input))

    # Ensure there's at least one user message
    if not any(m.get("role") == "user" for m in messages):
        if messages and messages[-1]["role"] == "assistant":
            pass  # OK for continuation
        elif not messages:
            messages.append({"role": "user", "content": ""})

    return messages


def _convert_tools(tools: list) -> list[dict]:
    """Convert Responses API tools to Chat Completions format."""
    result = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tool_type = tool.get("type", "")
        if tool_type == "function":
            result.append(tool)  # Already in chat completions format
        elif "name" in tool and "parameters" in tool:
            # Responses API function tool format
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool["parameters"],
                    },
                }
            )
    return result


# ── Response: Chat Completions → Responses ─────────────────────────────────


def chat_to_responses(chat_resp: dict, original_model: str = "") -> dict:
    """
    Convert a Chat Completions response to Responses API format.

    Preserves tool calls, usage, finish reason.
    """
    response_id = f"resp_{uuid.uuid4().hex[:24]}"
    model = chat_resp.get("model", original_model)
    created = chat_resp.get("created", int(time.time()))

    choices = chat_resp.get("choices", [])
    output = []
    finish_reason = "stop"

    for choice in choices:
        finish_reason = choice.get("finish_reason", "stop") or "stop"
        message = choice.get("message", {})
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []

        if content:
            output.append(
                {
                    "type": "message",
                    "id": f"msg_{uuid.uuid4().hex[:20]}",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": content}],
                    "status": "completed",
                }
            )

        for tc in tool_calls:
            func = tc.get("function", {})
            output.append(
                {
                    "type": "function_call",
                    "id": f"fc_{uuid.uuid4().hex[:20]}",
                    "call_id": tc.get("id", f"call_{uuid.uuid4().hex[:20]}"),
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", "{}"),
                    "status": "completed",
                }
            )

    usage_raw = chat_resp.get("usage", {})
    usage = None
    if usage_raw:
        usage = {
            "input_tokens": usage_raw.get("prompt_tokens"),
            "output_tokens": usage_raw.get("completion_tokens"),
            "total_tokens": usage_raw.get("total_tokens"),
        }

    responses_resp: dict[str, Any] = {
        "id": response_id,
        "object": "response",
        "created_at": created,
        "model": model,
        "output": output,
        "output_text": _extract_text(output),
        "status": _map_finish_reason(finish_reason),
    }
    if usage:
        responses_resp["usage"] = usage

    return responses_resp


def _extract_text(output: list) -> str:
    parts = []
    for item in output:
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
    return "".join(parts)


def _map_finish_reason(finish_reason: str) -> str:
    mapping = {
        "stop": "completed",
        "length": "incomplete",
        "tool_calls": "completed",
        "function_call": "completed",
        "content_filter": "incomplete",
    }
    return mapping.get(finish_reason, "completed")


# ── SSE Streaming Adapter ──────────────────────────────────────────────────


async def stream_chat_to_responses(
    nvidia_stream: AsyncIterator[bytes],
    model: str,
    response_id: str | None = None,
) -> AsyncIterator[bytes]:
    """
    Translate NVIDIA Chat Completions SSE stream → Responses API SSE stream.

    NVIDIA SSE format:
      data: {"choices":[{"delta":{"content":"..."},"finish_reason":null}]}

    Responses SSE format (what Codex expects):
      event: response.created
      data: {"type":"response.created","response":{...}}

      event: response.output_text.delta
      data: {"type":"response.output_text.delta","delta":"..."}

      event: response.completed
      data: {"type":"response.completed","response":{...}}
    """
    rid = response_id or f"resp_{uuid.uuid4().hex[:24]}"
    created_at = int(time.time())
    item_id = f"msg_{rid[5:]}"
    accumulated_text = []
    accumulated_tool_calls: dict[int, dict] = {}
    total_usage: dict = {}
    text_item_added = False

    # Send response.created event
    created_event = {
        "type": "response.created",
        "response": {
            "id": rid,
            "object": "response",
            "created_at": created_at,
            "model": model,
            "status": "in_progress",
            "output": [],
        },
    }
    yield _sse_bytes("response.created", created_event)

    async def _emit_text_delta(text: str):
        nonlocal text_item_added
        if not text_item_added:
            text_item_added = True
            item_added_event = {
                "type": "response.output_item.added",
                "output_index": 0,
                "item": {
                    "id": item_id,
                    "object": "realtime.item",
                    "type": "message",
                    "status": "in_progress",
                    "role": "assistant",
                    "content": [],
                },
            }
            yield _sse_bytes("response.output_item.added", item_added_event)

            part_added_event = {
                "type": "response.content_part.added",
                "output_index": 0,
                "item_id": item_id,
                "part_index": 0,
                "part": {"type": "output_text", "text": ""},
            }
            yield _sse_bytes("response.content_part.added", part_added_event)

        accumulated_text.append(text)
        delta_event = {
            "type": "response.output_text.delta",
            "item_id": item_id,
            "output_index": 0,
            "content_index": 0,
            "delta": text,
        }
        yield _sse_bytes("response.output_text.delta", delta_event)

    buffer = b""
    async for chunk in nvidia_stream:
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip()
            if not line or line == b"data: [DONE]":
                if line == b"data: [DONE]":
                    continue
                continue
            if not line.startswith(b"data: "):
                continue
            raw = line[6:]
            if raw == b"[DONE]":
                continue
            try:
                delta_obj = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if delta_obj.get("usage"):
                total_usage = delta_obj["usage"]

            choices = delta_obj.get("choices", [])
            for choice in choices:
                delta = choice.get("delta", {})
                text = delta.get("content")
                if text:
                    async for event in _emit_text_delta(text):
                        yield event

                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    if idx not in accumulated_tool_calls:
                        tc_id = tc.get("id") or f"call_{uuid.uuid4().hex[:20]}"
                        fc_id = f"fc_{uuid.uuid4().hex[:20]}"
                        accumulated_tool_calls[idx] = {
                            "id": fc_id,
                            "call_id": tc_id,
                            "name": "",
                            "arguments": "",
                        }
                        item_added_event = {
                            "type": "response.output_item.added",
                            "output_index": idx + (1 if text_item_added else 0),
                            "item": {
                                "id": fc_id,
                                "call_id": tc_id,
                                "type": "function_call",
                                "name": "",
                                "arguments": "",
                                "status": "in_progress",
                            },
                        }
                        yield _sse_bytes("response.output_item.added", item_added_event)

                    existing = accumulated_tool_calls[idx]
                    fn = tc.get("function", {})
                    if fn.get("name"):
                        existing["name"] += fn["name"]
                    if fn.get("arguments"):
                        arg_delta = fn["arguments"]
                        existing["arguments"] += arg_delta
                        arg_delta_event = {
                            "type": "response.function_call_arguments.delta",
                            "item_id": existing["id"],
                            "call_id": existing["call_id"],
                            "delta": arg_delta,
                        }
                        yield _sse_bytes("response.function_call_arguments.delta", arg_delta_event)

    if buffer.strip() and buffer.strip().startswith(b"data: ") and buffer.strip() != b"data: [DONE]":
        raw = buffer.strip()[6:]
        if raw != b"[DONE]":
            try:
                delta_obj = json.loads(raw)
                if delta_obj.get("usage"):
                    total_usage = delta_obj["usage"]
                choices = delta_obj.get("choices", [])
                for choice in choices:
                    delta = choice.get("delta", {})
                    text = delta.get("content")
                    if text:
                        async for event in _emit_text_delta(text):
                            yield event
            except json.JSONDecodeError:
                pass

    final_output = []
    if text_item_added:
        full_text = "".join(accumulated_text)
        text_done_event = {
            "type": "response.output_text.done",
            "output_index": 0,
            "item_id": item_id,
            "content_index": 0,
            "text": full_text,
        }
        yield _sse_bytes("response.output_text.done", text_done_event)

        part_done_event = {
            "type": "response.content_part.done",
            "output_index": 0,
            "item_id": item_id,
            "part_index": 0,
            "part": {"type": "output_text", "text": full_text},
        }
        yield _sse_bytes("response.content_part.done", part_done_event)

        item_msg = {
            "id": item_id,
            "object": "realtime.item",
            "type": "message",
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": full_text}],
        }
        item_done_event = {
            "type": "response.output_item.done",
            "output_index": 0,
            "item": item_msg,
        }
        yield _sse_bytes("response.output_item.done", item_done_event)

        final_output.append(
            {
                "type": "message",
                "id": item_id,
                "role": "assistant",
                "content": [{"type": "output_text", "text": full_text}],
                "status": "completed",
            }
        )

    for idx, tc in accumulated_tool_calls.items():
        args_done_event = {
            "type": "response.function_call_arguments.done",
            "item_id": tc["id"],
            "call_id": tc["call_id"],
            "arguments": tc["arguments"],
        }
        yield _sse_bytes("response.function_call_arguments.done", args_done_event)

        fc_item = {
            "id": tc["id"],
            "call_id": tc["call_id"],
            "type": "function_call",
            "name": tc["name"],
            "arguments": tc["arguments"],
            "status": "completed",
        }
        tc_item_done_event = {
            "type": "response.output_item.done",
            "output_index": idx + (1 if text_item_added else 0),
            "item": fc_item,
        }
        yield _sse_bytes("response.output_item.done", tc_item_done_event)

        final_output.append(
            {
                "type": "function_call",
                "id": tc["id"],
                "call_id": tc["call_id"],
                "name": tc["name"],
                "arguments": tc["arguments"],
                "status": "completed",
            }
        )

    usage_out = None
    if total_usage:
        usage_out = {
            "input_tokens": total_usage.get("prompt_tokens"),
            "output_tokens": total_usage.get("completion_tokens"),
            "total_tokens": total_usage.get("total_tokens"),
        }

    completed_response: dict[str, Any] = {
        "id": rid,
        "object": "response",
        "created_at": created_at,
        "model": model,
        "status": "completed",
        "output": final_output,
        "output_text": "".join(accumulated_text),
    }
    if usage_out:
        completed_response["usage"] = usage_out

    completed_event = {
        "type": "response.completed",
        "response": completed_response,
    }
    yield _sse_bytes("response.completed", completed_event)
    yield b"data: [DONE]\n\n"


def _sse_bytes(event_type: str, data: dict) -> bytes:
    """Format a Server-Sent Event as bytes."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()
