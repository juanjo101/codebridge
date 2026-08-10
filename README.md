# CodeBridge Gateway

**Local gateway connecting Codex to NVIDIA NIM.**

```
Codex → OpenAI Responses API → CodeBridge → NVIDIA NIM
```

## What It Does

CodeBridge is a lightweight local gateway that lets you use NVIDIA NIM models
with Codex as an alternative backend — routing everyday coding tasks to NVIDIA
and reserving your premium OpenAI credits for work that truly needs them.

## Why It Exists

Codex uses the OpenAI Responses API. NVIDIA NIM is OpenAI-compatible, but only
reliably at the Chat Completions level on their hosted service. CodeBridge:

1. Accepts Responses API requests from Codex
2. Translates to NVIDIA's supported `/v1/chat/completions` endpoint
3. Returns Responses API format back to Codex

Completely transparent to Codex.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Codex                                                    │
│  (sends Responses API requests)                           │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /v1/responses
                       ▼
┌──────────────────────────────────────────────────────────┐
│  CodeBridge Gateway  (http://127.0.0.1:8787)             │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Authentication     Telemetry    Model Router   │     │
│  │  (local token)      (local only) (deterministic)│     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────┐     │
│  │  Protocol Adapter                               │     │
│  │  Responses API ↔ Chat Completions               │     │
│  └──────────────────────┬──────────────────────────┘     │
└─────────────────────────┼────────────────────────────────┘
                          │ POST /v1/chat/completions
                          ▼
┌──────────────────────────────────────────────────────────┐
│  NVIDIA NIM  (integrate.api.nvidia.com)                  │
└──────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- NVIDIA API key ([get one here](https://build.nvidia.com))
- Codex CLI

## Quick Start

### Linux / macOS

```bash
git clone <repo> codebridge
cd codebridge
bash scripts/setup.sh
```

### Windows

```powershell
git clone <repo> codebridge
cd codebridge
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

## NVIDIA API Key

> **ACTION REQUIRED:** Open `.env` and set your key.

```env
# .env
NVIDIA_API_KEY=your_nvidia_api_key_here
```

Get your key at: https://build.nvidia.com → Sign in → API Keys

**Security:**
- Key is stored only in `.env` (never committed)
- Key is never logged
- Key is never forwarded to Codex
- Gateway binds to `127.0.0.1` by default (local only)

## Starting CodeBridge

```bash
# Linux/macOS
./scripts/start.sh

# Windows
.\scripts\start.ps1

# Direct
uv run codebridge serve
```

Gateway starts at: `http://127.0.0.1:8787`

## Testing NVIDIA Connection

```bash
python scripts/test_nvidia.py
```

Expected output:
```
NVIDIA CONNECTION TEST
==================================================
[1/6] Checking NVIDIA API... PASS (152 models)
[2/6] Fetching models... PASS (152 models)
[3/6] Testing basic response... PASS
[4/6] Testing streaming... PASS (N chunks)
[5/6] Testing tool calling... PASS / WARN
[6/6] Testing reasoning... UNKNOWN
```

## Available Models

```bash
uv run codebridge models
```

## Selecting a Model

After listing models, set your preferred model in `.env`:

```env
NVIDIA_DEFAULT_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```

Recommendations (verify availability with `codebridge models`):
- **Strong general/coding:** `nvidia/llama-3.1-nemotron-70b-instruct`
- **Code-specialized:** `nvidia/deepseek-coder-v2`
- **Fast/lightweight:** `meta/llama-3.2-8b-instruct`

> **Note:** Model availability, capabilities, and costs depend on your NVIDIA
> account and API tier. Always verify with `codebridge models`.

## Connecting Codex

```bash
# Automated configuration
uv run python scripts/configure_codex.py
```

Or manually add to `~/.codex/config.toml`:

```toml
model_provider = "codebridge"
model = "nvidia/your-chosen-model"

[model_providers.codebridge]
name = "CodeBridge NVIDIA"
base_url = "http://127.0.0.1:8787/v1"
env_key = "CODEBRIDGE_LOCAL_TOKEN"
wire_api = "responses"
```

Set the auth token:
```bash
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

## Economy Mode vs Premium Mode

### Economy Mode (NVIDIA via CodeBridge)

Set `model_provider = "codebridge"` in Codex config.

Good for:
- Everyday coding, CRUD, APIs, frontend
- SQL, tests, documentation, refactoring
- Normal debugging and code explanation

### Premium Mode (OpenAI direct)

Set `model_provider = "openai"` in Codex config.

Good for:
- Complex architecture decisions
- Hard multi-system debugging
- Security review
- Situations where Economy Mode isn't sufficient

> **Note:** We cannot promise specific savings. Your actual token usage and
> costs depend on task volume, NVIDIA plan, and how often you use each mode.

## Health

```bash
curl http://127.0.0.1:8787/health
```

## Diagnostics

```bash
# JSON
curl http://127.0.0.1:8787/diagnostics

# Human-readable
curl "http://127.0.0.1:8787/diagnostics?format=text"
```

## Usage Statistics

```bash
curl http://127.0.0.1:8787/usage
# or
uv run codebridge usage
```

## Security

- **Localhost only:** Gateway binds to `127.0.0.1` by default
- **Token isolation:** Codex token ≠ NVIDIA API key (two separate secrets)
- **No secret logging:** NVIDIA keys, tokens, and Authorization headers are redacted from all logs
- **Constant-time auth:** Token comparison uses `hmac.compare_digest()`
- **CORS restricted:** Only localhost origins permitted

## Responses API

CodeBridge receives standard Responses API requests from Codex and returns
Responses API format responses. Supported fields:

| Field | Supported |
|-------|-----------|
| `input` | ✓ (string or array) |
| `instructions` | ✓ (→ system message) |
| `model` | ✓ |
| `stream` | ✓ |
| `tools` | ✓ |
| `tool_choice` | ✓ |
| `temperature` | ✓ |
| `max_output_tokens` | ✓ |
| `reasoning` | Logged, not forwarded (NVIDIA doesn't support) |
| `store` | Not forwarded (not supported) |

## Streaming

Streaming is fully supported. NVIDIA's Chat Completions SSE stream is translated
to Responses API SSE format:

```
event: response.created
event: response.output_text.delta  (× N)
event: response.completed
```

## Tool Calling

Tool calls are preserved intact through the gateway:
- `call_id` preserved
- `function.name` preserved
- `function.arguments` preserved
- Event types mapped correctly

## Reasoning

Reasoning-style responses depend entirely on the NVIDIA model. CodeBridge does
not fabricate reasoning or convert regular text into reasoning tokens.
Models with reasoning capability (e.g., nemotron-think) return reasoning naturally.

## Fallback

NVIDIA's hosted service does not support `/v1/responses`. CodeBridge automatically
uses `/v1/chat/completions` with protocol translation (configurable via
`CODEBRIDGE_RESPONSES_FALLBACK=true`).

## Troubleshooting

| Symptom | Solution |
|---------|---------|
| 401 Unauthorized | `export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)` |
| Gateway not starting | Check port 8787: `lsof -i :8787` |
| No models listed | Set `NVIDIA_API_KEY` in `.env` |
| Model not found | Run `codebridge models`, update `NVIDIA_DEFAULT_MODEL` |
| Streaming broken | Check `CODEBRIDGE_RESPONSES_FALLBACK=true` |

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Live NVIDIA tests (requires API key)
python scripts/test_nvidia.py
```

## Roadmap

| Version | Feature |
|---------|---------|
| **V1** | **Codex → CodeBridge → NVIDIA** (current) |
| V1.1 | Capability detection, model profiles |
| V1.2 | Routing rules, model selection by task type |
| V2 | CodeBridge MCP server |
| V3 | Additional providers (Ollama, OpenRouter) |

## CLI Reference

```
codebridge serve           Start the gateway
codebridge health          Check gateway health
codebridge models          List NVIDIA models
codebridge test            Run NVIDIA connectivity test
codebridge usage           Show usage statistics
codebridge token           Show local auth token
codebridge configure-codex Configure Codex to use CodeBridge
```

## License

MIT — see [LICENSE](LICENSE)
