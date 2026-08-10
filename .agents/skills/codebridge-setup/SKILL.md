---
name: codebridge-setup
description: >
  Install, configure, diagnose, and start CodeBridge Gateway.
  Use when the user needs to set up CodeBridge, configure Codex, or troubleshoot
  connection issues. Covers Linux, macOS, and Windows.
---

# CodeBridge Setup Guide

## Requirements

- Python 3.10+
- uv (installed automatically by setup script)
- NVIDIA API key from https://build.nvidia.com

## Quick Install

### Linux / macOS
```bash
cd /path/to/codebridge
bash scripts/setup.sh
```

### Windows (PowerShell)
```powershell
cd C:\path\to\codebridge
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

## Manual Install

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra dev

# Create .env
cp .env.example .env
```

## Configuration

### Required: NVIDIA API Key

**ACTION REQUIRED:** Open `.env` and set:
```env
NVIDIA_API_KEY=your_nvidia_api_key_here
```

Get your key at: https://build.nvidia.com

### Set Default Model

After getting models (`codebridge models`), set:
```env
NVIDIA_DEFAULT_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | (required) | NVIDIA NIM API key |
| `NVIDIA_DEFAULT_MODEL` | (empty) | Model to use by default |
| `CODEBRIDGE_HOST` | `127.0.0.1` | Bind host (keep localhost) |
| `CODEBRIDGE_PORT` | `8787` | Server port |
| `CODEBRIDGE_LOCAL_TOKEN` | (auto-generated) | Auth token for Codex |

## Starting the Gateway

```bash
# Linux/macOS
./scripts/start.sh

# Windows
.\scripts\start.ps1

# Direct
uv run codebridge serve
```

## Connecting Codex

```bash
# Interactive configuration
uv run python scripts/configure_codex.py

# Or via CLI
uv run codebridge configure-codex
```

Add to `~/.codex/config.toml`:
```toml
model_provider = "codebridge"
model = "nvidia/your-chosen-model"

[model_providers.codebridge]
name = "CodeBridge NVIDIA"
base_url = "http://127.0.0.1:8787/v1"
env_key = "CODEBRIDGE_LOCAL_TOKEN"
wire_api = "responses"
```

Set environment:
```bash
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

## Testing the Setup

```bash
# Test NVIDIA connectivity
python scripts/test_nvidia.py

# Test gateway health
curl http://127.0.0.1:8787/health

# Run diagnostics
curl http://127.0.0.1:8787/diagnostics

# Smoke test via CLI
uv run codebridge test
```

## Switching Modes

**Economy Mode (NVIDIA via CodeBridge):**
```toml
model_provider = "codebridge"
model = "nvidia/your-model"
```

**Premium Mode (OpenAI direct):**
```toml
model_provider = "openai"
model = "gpt-5.6-sol"
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| 401 Unauthorized | Verify `CODEBRIDGE_LOCAL_TOKEN` env var matches `.codebridge_token` |
| 503 Service Unavailable | Check `NVIDIA_API_KEY` is set in `.env` |
| Model not found | Run `codebridge models` and update `NVIDIA_DEFAULT_MODEL` |
| Streaming not working | Check `CODEBRIDGE_RESPONSES_FALLBACK=true` in `.env` |
| Gateway not starting | Check port 8787 is not in use: `lsof -i :8787` |

For detailed diagnostics:
```bash
curl http://127.0.0.1:8787/diagnostics?format=text
```
