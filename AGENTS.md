# CodeBridge Development Policy

## Mission

CodeBridge is a lightweight local gateway connecting Codex-compatible Responses API
clients to NVIDIA NIM.

The primary design goals are, in order:

1. **Protocol correctness** — Responses API in, Responses API out (adapted via Chat Completions to NVIDIA)
2. **Streaming correctness** — streaming must work without buffering, event order must be preserved
3. **Tool-call correctness** — call IDs, function names, and arguments must survive intact
4. **Security** — secrets never logged, never forwarded, localhost-only by default
5. **Minimal latency** — no unnecessary parsing or buffering
6. **Minimal complexity** — every layer must earn its place
7. **Token efficiency** — the reason we exist: route appropriate workloads to NVIDIA

## Architecture

```
Codex / Antigravity
    ↓
OpenAI Responses API (POST /v1/responses)
    ↓
CodeBridge Gateway
    ↓
Protocol Adapter (Responses → Chat Completions)
    ↓
NVIDIA NIM /v1/chat/completions
    ↓
SSE stream or JSON response
    ↓
Protocol Adapter (Chat Completions → Responses)
    ↓
Codex
```

**Why Chat Completions?**
NVIDIA's hosted service (`integrate.api.nvidia.com`) does not support `/v1/responses`
reliably (404 or experimental). The adapter translates the minimum necessary fields.
If NVIDIA adds native `/v1/responses` support, the passthrough path can be activated.

## Module Structure

```
src/codebridge/
    config.py       — Settings (pydantic-settings), token management
    logging.py      — Logging + secret redaction
    cli.py          — CLI entry point
    main.py         — Uvicorn server entry point
    api/
        app.py      — FastAPI app factory, lifespan, middleware
        responses.py — POST /v1/responses
        models.py   — GET /v1/models
        health.py   — GET /health, /health/nvidia
        diagnostics.py — GET /diagnostics
        usage.py    — GET /usage
    providers/
        nvidia.py   — NvidiaProvider: health, list_models, chat_completions, streaming
    responses/
        compatibility.py — Protocol adapter: Responses ↔ Chat Completions
        errors.py        — Normalized error responses
    routing/
        router.py   — Deterministic model resolution
    models/
        catalog.py  — ModelCatalog with TTL cache
    security/
        auth.py     — Local token validation
    telemetry/
        storage.py  — Local-only metrics
```

## Key Design Decisions

### Responses → Chat Completions (not passthrough)
NVIDIA hosted service does not support `/v1/responses`. We translate to Chat Completions.
This is transparent to Codex (it receives Responses API format back).

### Token architecture
```
Codex → Authorization: Bearer <CODEBRIDGE_LOCAL_TOKEN>
             ↓
        CodeBridge validates local token, strips it
             ↓
NVIDIA ← Authorization: Bearer <NVIDIA_API_KEY>
```
The two secrets never cross their boundaries.

### Singleton pattern
`get_settings()`, `get_provider()`, `get_catalog()`, `get_telemetry()` all return
singletons. Reset functions exist for testing.

### Streaming
NVIDIA sends Chat Completions SSE. We translate to Responses API SSE.
Events: `response.created` → N× `response.output_text.delta` → `response.completed`.

## Adding Endpoints

1. Create `src/codebridge/api/<name>.py`
2. Define `router = APIRouter()`
3. Add endpoint with `Depends(validate_local_token)` for protected routes
4. Register in `api/app.py`: `app.include_router(...)`
5. Write tests in `tests/integration/test_<name>.py`

## Adding Providers

1. Define protocol in `providers/base.py` (optional)
2. Implement `YourProvider` in `providers/<name>.py`
3. Expose singleton `get_<name>_provider()`
4. Implement: `health()`, `list_models()`, `chat_completions()`, `chat_completions_stream()`
5. Wire in `api/responses.py`

## Sources for External API Behavior

Always consult official documentation:
- **Codex config**: https://github.com/openai/codex (config.toml format)
- **NVIDIA NIM**: https://docs.api.nvidia.com/nim/reference/
- **OpenAI Responses API**: https://platform.openai.com/docs/api-reference/responses
- **OpenAI Chat Completions**: https://platform.openai.com/docs/api-reference/chat

Do not rely on assumptions. Document any deviation from official behavior.

## Security Rules

**NEVER commit or print:**
- `NVIDIA_API_KEY`
- `CODEBRIDGE_LOCAL_TOKEN`
- `Authorization` header values
- Any credential or secret

**Default binding:** `CODEBRIDGE_HOST=127.0.0.1` (localhost only)

**Secret redaction:** `src/codebridge/logging.py` redacts known secret patterns.
All new log statements must pass through the redacting logger.

**Constant-time comparison:** Token validation uses `hmac.compare_digest()`.

## Testing Requirements

Every new protocol behavior must have:
- Unit test for the transformation logic
- Integration test with mocked NVIDIA (respx)
- Streaming test if the endpoint supports streaming
- Security test if credentials are involved

Run tests:
```bash
uv run pytest              # unit + integration (no live NVIDIA)
uv run pytest -m live      # live NVIDIA (requires NVIDIA_API_KEY)
```

## Scope (V1)

**In scope:**
- Codex → Responses API → NVIDIA NIM
- Streaming
- Tool calling
- Local telemetry
- Auth token management
- Model catalog with TTL cache
- Health / diagnostics / usage endpoints

**Out of scope for V1:**
- GUI
- MCP (V2 roadmap)
- Additional providers (Ollama, OpenRouter, etc.)
- Voice, messaging, mobile
- Remote/cloud deployment
- Automatic premium fallback (requires Codex API support)

## Roadmap

| Version | Feature |
|---------|---------|
| V1 | Codex → CodeBridge → NVIDIA (current) |
| V1.1 | Capability detection, model profiles |
| V1.2 | Routing rules, model selection by task type |
| V2 | CodeBridge MCP server |
| V3 | Additional providers (Ollama, OpenRouter) |

## Clean Implementation Principle

Do not copy third-party proxy implementations.
External projects may be studied for concepts.
CodeBridge maintains its own architecture and implementation.
