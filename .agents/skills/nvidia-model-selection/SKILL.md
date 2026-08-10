---
name: nvidia-model-selection
description: >
  Help select the best NVIDIA NIM model for a coding task. Covers listing models,
  understanding capabilities, setting defaults, and testing specific models.
  Use when the user needs to choose or change their NVIDIA model.
---

# NVIDIA Model Selection Guide

## List Available Models

```bash
# Via CLI (requires gateway running)
uv run codebridge models

# Or directly from NVIDIA
uv run python -c "
import asyncio, sys
sys.path.insert(0, 'src')
from codebridge.providers.nvidia import NvidiaProvider
async def main():
    p = NvidiaProvider()
    models = await p.list_models()
    for m in models:
        print(m['id'])
    await p.close()
asyncio.run(main())
"
```

## Model Categories (as inferred by CodeBridge)

| Capability | Pattern | Example |
|-----------|---------|---------|
| `coding` | deepseek, coder, starcoder, qwen-coder | nvidia/deepseek-coder-v2 |
| `reasoning` | reason, think, r1, o1 | nvidia/nemotron-think |
| `large` | 70b, 72b, 405b | nvidia/llama-3.1-70b-instruct |
| `fast` | 7b, 8b, 14b | nvidia/llama-3.2-8b |

## NVIDIA Hosted Models (Common Examples)

Check actual availability with `codebridge models` — this list changes.

Common choices for coding:
- `nvidia/llama-3.1-nemotron-70b-instruct` — strong general + coding
- `nvidia/deepseek-coder-v2` — specialized for code
- `meta/llama-3.1-70b-instruct` — strong general purpose
- `meta/llama-3.1-8b-instruct` — fast, less capable

## Setting Your Model

```env
# In .env:
NVIDIA_DEFAULT_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
NVIDIA_FALLBACK_MODEL=meta/llama-3.1-8b-instruct
```

## Testing a Specific Model

```python
# scripts/test_nvidia.py automatically tests the default model
python scripts/test_nvidia.py

# Or test manually:
import asyncio, sys
sys.path.insert(0, 'src')
from codebridge.providers.nvidia import NvidiaProvider

async def test(model):
    p = NvidiaProvider()
    resp = await p.chat_completions({
        "model": model,
        "messages": [{"role": "user", "content": "Reply: CODEBRIDGE_OK"}],
        "max_tokens": 20,
    })
    print(resp.json())
    await p.close()

asyncio.run(test("nvidia/your-model-here"))
```

## Model Selection Strategy

1. **Start with the recommended model for your use case**
   - General coding → Nemotron 70B or Llama 3.1 70B
   - Fast responses → 8B models
   - Complex reasoning → reasoning-specialized models

2. **Test before committing**
   ```bash
   python scripts/test_nvidia.py
   ```

3. **Set as default in .env**
   ```env
   NVIDIA_DEFAULT_MODEL=nvidia/your-chosen-model
   ```

4. **Monitor performance via /usage**
   ```bash
   curl http://127.0.0.1:8787/usage
   ```

## Availability Note

NVIDIA model availability, rate limits, and pricing depend on your NVIDIA account
and the specific API tier you are using. Always verify current availability at
https://build.nvidia.com before relying on a specific model.

## Requesting Specific Model per Request

Codex will use whatever model is configured in `model_provider`/`model` settings.
To temporarily use a different model, adjust `~/.codex/config.toml`:
```toml
model = "nvidia/alternate-model"
```
