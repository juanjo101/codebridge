---
name: codebridge-development
description: >
  Architecture guide for developing CodeBridge Gateway. Covers module structure,
  how to add endpoints/providers, testing requirements, and the protocol adapter
  design. Use when modifying CodeBridge internals or adding features.
---

# CodeBridge Development Guide

## Architecture Overview

CodeBridge is a minimal gateway:
```
Codex → POST /v1/responses → CodeBridge → NVIDIA /v1/chat/completions → NVIDIA NIM
```

**Why Chat Completions to NVIDIA?**
NVIDIA's hosted API does not support `/v1/responses` reliably.
The adapter in `src/codebridge/responses/compatibility.py` handles the translation.

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `config.py` | All settings. One `Settings` object. Never hardcode values. |
| `logging.py` | Logging with secret redaction. Always use this, never `print()` for logging. |
| `api/responses.py` | POST /v1/responses — main gateway endpoint |
| `api/models.py` | GET /v1/models — cached model list |
| `api/health.py` | Health endpoints (no auth required) |
| `api/diagnostics.py` | Progressive diagnostic checks |
| `api/usage.py` | Local telemetry snapshot |
| `providers/nvidia.py` | NvidiaProvider — all NVIDIA API calls |
| `responses/compatibility.py` | Protocol adapter Responses ↔ Chat Completions |
| `responses/errors.py` | Normalized error responses |
| `routing/router.py` | Deterministic model selection |
| `models/catalog.py` | Model list with TTL cache |
| `security/auth.py` | Local token validation |
| `telemetry/storage.py` | Thread-safe local metrics |

## Adding a New Endpoint

```python
# 1. Create src/codebridge/api/myendpoint.py
from fastapi import APIRouter, Depends
from codebridge.security.auth import validate_local_token

router = APIRouter()

@router.get("/myendpoint")
async def my_endpoint(_auth=Depends(validate_local_token)):
    return {"status": "ok"}

# 2. Register in api/app.py
from codebridge.api.myendpoint import router as my_router
app.include_router(my_router)

# 3. Write test in tests/integration/test_myendpoint.py
```

## Adding a Future Provider

1. Create `src/codebridge/providers/<name>.py`
2. Implement interface matching `NvidiaProvider`:
   - `async def health() -> dict`
   - `async def list_models() -> list[dict]`
   - `async def chat_completions(payload: dict) -> httpx.Response`
   - `async def chat_completions_stream(payload: dict) -> AsyncIterator[bytes]`
3. Expose `get_<name>_provider()` singleton
4. Wire via `CODEBRIDGE_PROVIDER=<name>` setting

## Protocol Adapter: Responses ↔ Chat Completions

**Location:** `src/codebridge/responses/compatibility.py`

**Request flow:**
```
Responses request (from Codex)
    → responses_to_chat()
    → Chat Completions payload
    → NVIDIA /v1/chat/completions
```

**Response flow:**
```
Chat Completions response (from NVIDIA)
    → chat_to_responses()
    → Responses response
    → Codex
```

**Streaming flow:**
```
NVIDIA SSE chunks (Chat Completions format)
    → stream_chat_to_responses()
    → Responses API SSE events
    → Codex
```

**Principle:** Translate only what is necessary.
Preserve: model, tool calls (call_id, name, arguments), usage, finish reason.
Do NOT: invent fields, fabricate reasoning, modify content.

## Testing Protocol Changes

Every protocol change needs:

```bash
# Unit test (fast, no network)
tests/unit/test_compatibility.py

# Integration test (mocked NVIDIA)
tests/integration/test_api.py
tests/integration/test_streaming.py

# Live test (requires NVIDIA_API_KEY)
python scripts/test_nvidia.py
```

## Security Checklist (for every PR)

- [ ] No secrets in code or logs
- [ ] `validate_local_token` on all protected endpoints
- [ ] NVIDIA API key never forwarded to clients
- [ ] Local token never sent to NVIDIA
- [ ] Error messages don't leak internal details

## Performance Notes

- httpx AsyncClient is reused (singleton in `NvidiaProvider`)
- Model catalog has TTL (default 300s) — don't call `/v1/models` per-request
- Streaming uses `StreamingResponse` — don't buffer entire response
- Avoid JSON re-parsing in the hot path when passthrough is safe

## Debugging

```bash
# Verbose logging
CODEBRIDGE_LOG_LEVEL=DEBUG uv run codebridge serve

# Diagnostics
curl http://127.0.0.1:8787/diagnostics

# Health
curl http://127.0.0.1:8787/health/nvidia

# Usage stats
curl http://127.0.0.1:8787/usage
```
