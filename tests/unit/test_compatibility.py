"""Unit tests for protocol adapter (Responses ↔ Chat Completions)."""


from codebridge.responses.compatibility import (
    chat_to_responses,
    responses_to_chat,
)

# ── Request conversion tests ───────────────────────────────────────────────


def test_string_input_becomes_user_message():
    req = {"model": "test-model", "input": "Hello world"}
    chat = responses_to_chat(req)
    assert chat["messages"][-1]["role"] == "user"
    assert chat["messages"][-1]["content"] == "Hello world"


def test_instructions_become_system_message():
    req = {
        "model": "test-model",
        "instructions": "You are a coding assistant.",
        "input": "Write a hello world",
    }
    chat = responses_to_chat(req)
    assert chat["messages"][0]["role"] == "system"
    assert "coding assistant" in chat["messages"][0]["content"]


def test_max_output_tokens_converted():
    req = {"model": "test", "input": "hi", "max_output_tokens": 512}
    chat = responses_to_chat(req)
    assert chat["max_tokens"] == 512


def test_temperature_preserved():
    req = {"model": "test", "input": "hi", "temperature": 0.7}
    chat = responses_to_chat(req)
    assert chat["temperature"] == 0.7


def test_streaming_preserved():
    req = {"model": "test", "input": "hi", "stream": True}
    chat = responses_to_chat(req)
    assert chat["stream"] is True
    # Should add stream_options for token usage
    assert "stream_options" in chat


def test_tools_preserved():
    req = {
        "model": "test",
        "input": "hi",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    }
    chat = responses_to_chat(req)
    assert "tools" in chat
    assert len(chat["tools"]) == 1
    assert chat["tools"][0]["type"] == "function"


def test_array_input_messages():
    req = {
        "model": "test",
        "input": [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
        ],
    }
    chat = responses_to_chat(req)
    assert len(chat["messages"]) == 3
    assert chat["messages"][0]["content"] == "First message"
    assert chat["messages"][2]["content"] == "Second message"


# ── Response conversion tests ──────────────────────────────────────────────


def test_chat_to_responses_basic():
    chat_resp = {
        "id": "chatcmpl-123",
        "model": "test-model",
        "created": 1700000000,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "Hello!"},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    resp = chat_to_responses(chat_resp, "test-model")
    assert resp["object"] == "response"
    assert resp["status"] == "completed"
    assert resp["output_text"] == "Hello!"
    assert resp["model"] == "test-model"
    assert resp["usage"]["input_tokens"] == 10
    assert resp["usage"]["output_tokens"] == 5


def test_chat_to_responses_tool_call():
    """Tool calls must be preserved with their call_id."""
    chat_resp = {
        "id": "chatcmpl-456",
        "model": "test-model",
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
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"path": "/etc/hosts"}',
                            },
                        }
                    ],
                },
            }
        ],
    }
    resp = chat_to_responses(chat_resp, "test-model")
    # Must have function_call output
    fc_items = [o for o in resp["output"] if o["type"] == "function_call"]
    assert len(fc_items) == 1
    fc = fc_items[0]
    assert fc["call_id"] == "call_abc123"
    assert fc["name"] == "read_file"
    assert '"path"' in fc["arguments"]


def test_finish_reason_mapping():
    for finish, expected_status in [
        ("stop", "completed"),
        ("length", "incomplete"),
        ("tool_calls", "completed"),
    ]:
        chat_resp = {
            "model": "m",
            "created": 0,
            "choices": [
                {"finish_reason": finish, "message": {"content": "x"}}
            ],
        }
        resp = chat_to_responses(chat_resp)
        assert resp["status"] == expected_status
