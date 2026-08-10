---
name: codebridge-diagnostics
description: >
  Progressive diagnostic procedure for CodeBridge Gateway. Use when Codex cannot
  connect through CodeBridge, when requests fail, or when debugging NVIDIA
  integration issues. Covers full diagnostic checklist from gateway to Codex.
---

# CodeBridge Diagnostics Procedure

## Quick Check

```bash
# Is the gateway running?
curl http://127.0.0.1:8787/health

# Full diagnostics (JSON)
curl http://127.0.0.1:8787/diagnostics

# Full diagnostics (text)
curl "http://127.0.0.1:8787/diagnostics?format=text"
```

## Progressive Diagnostic Checklist

### Step 1: Gateway
```bash
curl http://127.0.0.1:8787/health
```
**Expected:** `{"status": "ok", ...}`
**If fails:** Gateway is not running. Start with: `codebridge serve`

---

### Step 2: Authentication
```bash
TOKEN=$(cat .codebridge_token)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8787/v1/models
```
**Expected:** 200 with model list (may be empty if key not set)
**If 401:** Token mismatch. Check `CODEBRIDGE_LOCAL_TOKEN` env var.

---

### Step 3: NVIDIA API Key
```bash
# Check health endpoint
curl http://127.0.0.1:8787/health | grep nvidia_api_key
```
**Expected:** `"nvidia_api_key": "configured"`
**If not configured:** Set `NVIDIA_API_KEY` in `.env`

---

### Step 4: NVIDIA API Reachability
```bash
curl http://127.0.0.1:8787/health/nvidia
```
**Expected:** `{"status": "ok", "models": N}`
**If auth_failed:** Invalid API key. Check key at https://build.nvidia.com
**If unreachable:** Network issue or NVIDIA service outage.

---

### Step 5: Models Endpoint
```bash
TOKEN=$(cat .codebridge_token)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8787/v1/models
```
**Expected:** JSON with model list
**If empty:** Check API key and connectivity

---

### Step 6: Basic Response
```bash
TOKEN=$(cat .codebridge_token)
curl -X POST http://127.0.0.1:8787/v1/responses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "YOUR_DEFAULT_MODEL",
    "input": "Reply exactly: CODEBRIDGE_OK"
  }'
```
**Expected:** `{"output_text": "CODEBRIDGE_OK", "status": "completed", ...}`

---

### Step 7: Streaming
```bash
TOKEN=$(cat .codebridge_token)
curl -X POST http://127.0.0.1:8787/v1/responses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "YOUR_DEFAULT_MODEL",
    "input": "Count 1 2 3",
    "stream": true
  }'
```
**Expected:** SSE events including `response.created`, `response.output_text.delta`, `response.completed`

---

### Step 8: Tool Calling
```bash
TOKEN=$(cat .codebridge_token)
curl -X POST http://127.0.0.1:8787/v1/responses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "YOUR_DEFAULT_MODEL",
    "input": "What is in /tmp?",
    "tools": [{
      "type": "function",
      "function": {
        "name": "shell",
        "description": "Run shell",
        "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}}
      }
    }]
  }'
```
**Expected:** `function_call` in output with preserved `call_id`

---

### Step 9: Codex Integration

**Verify environment:**
```bash
echo $CODEBRIDGE_LOCAL_TOKEN
cat .codebridge_token
# These must match
```

**Verify Codex config:**
```bash
cat ~/.codex/config.toml | grep -A5 "codebridge"
```

**Start Codex and test:**
- Open Codex
- Ask: "Reply exactly: CODEBRIDGE_OK"
- Expected: "CODEBRIDGE_OK" (served by NVIDIA)

---

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| 401 auth | Token mismatch | `export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)` |
| 503 service | NVIDIA key missing | Set `NVIDIA_API_KEY` in `.env` |
| 404 model | Wrong model ID | Run `codebridge models`, update `NVIDIA_DEFAULT_MODEL` |
| Connection refused | Gateway not running | `codebridge serve` |
| Streaming broken | Missing fallback | Set `CODEBRIDGE_RESPONSES_FALLBACK=true` in `.env` |

## Debug Logging

```bash
CODEBRIDGE_LOG_LEVEL=DEBUG uv run codebridge serve
```

## Running Full Test Suite

```bash
# All mock tests (fast)
uv run pytest tests/ -v

# Live NVIDIA tests (requires API key)
python scripts/test_nvidia.py
```
