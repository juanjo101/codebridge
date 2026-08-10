"""
Live NVIDIA API test.

Requires NVIDIA_API_KEY to be set.
Run with: python scripts/test_nvidia.py
Or: pytest -m live

This test is NOT run automatically. It requires a live NVIDIA API key.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def run_tests() -> None:
    from codebridge.config import get_settings
    from codebridge.providers.nvidia import NvidiaProvider, NvidiaProviderError
    from codebridge.responses.compatibility import responses_to_chat, chat_to_responses

    settings = get_settings()

    print()
    print("NVIDIA CONNECTION TEST")
    print("=" * 50)

    if not settings.nvidia_api_key_configured:
        print("FAIL: NVIDIA_API_KEY not configured")
        print()
        print("Open .env and set:")
        print("  NVIDIA_API_KEY=YOUR_KEY_HERE")
        print()
        sys.exit(1)

    provider = NvidiaProvider(settings)
    results = {}

    # ── Test 1: API health ─────────────────────────────────────────
    print("\n[1/6] Checking NVIDIA API...", end=" ")
    health = await provider.health()
    if health.get("status") == "ok":
        model_count = health.get("models", 0)
        print(f"PASS ({model_count} models available)")
        results["api"] = "PASS"
    elif health.get("status") == "auth_failed":
        print("FAIL (Invalid API key)")
        results["api"] = "FAIL"
        await provider.close()
        sys.exit(1)
    else:
        print(f"FAIL ({health})")
        results["api"] = "FAIL"
        await provider.close()
        sys.exit(1)

    # ── Test 2: Models ─────────────────────────────────────────────
    print("\n[2/6] Fetching models...", end=" ")
    try:
        models = await provider.list_models()
        print(f"PASS ({len(models)} models)")
        results["models"] = "PASS"

        print("\n  Available models:")
        for m in models[:10]:
            print(f"    - {m.get('id', 'unknown')}")
        if len(models) > 10:
            print(f"    ... and {len(models) - 10} more")
    except NvidiaProviderError as exc:
        print(f"FAIL ({exc.message})")
        results["models"] = "FAIL"

    # ── Determine model to test ────────────────────────────────────
    model = settings.nvidia_default_model
    if not model:
        # Pick first available
        model = models[0].get("id", "") if models else ""
    if not model:
        print("\nNo model available for testing.")
        await provider.close()
        return

    print(f"\n  Testing with model: {model}")

    # ── Test 3: Basic response ─────────────────────────────────────
    print("\n[3/6] Testing basic response...", end=" ")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Reply exactly: CODEBRIDGE_OK"}],
            "max_tokens": 20,
        }
        resp = await provider.chat_completions(payload)
        resp_json = resp.json()
        content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        if "CODEBRIDGE_OK" in content or content.strip():
            print(f"PASS (response: {content.strip()[:50]})")
            results["basic_response"] = "PASS"
        else:
            print(f"WARN (unexpected response: {content!r})")
            results["basic_response"] = "WARN"
    except NvidiaProviderError as exc:
        print(f"FAIL ({exc.message})")
        results["basic_response"] = "FAIL"

    # ── Test 4: Streaming ──────────────────────────────────────────
    print("\n[4/6] Testing streaming...", end=" ")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Count to 3"}],
            "max_tokens": 30,
            "stream": True,
        }
        chunks_received = 0
        content_parts = []
        async for chunk in provider.chat_completions_stream(payload):
            raw = chunk.decode()
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            content_parts.append(delta)
                            chunks_received += 1
                    except json.JSONDecodeError:
                        pass

        if chunks_received > 0:
            print(f"PASS ({chunks_received} chunks, content: {''.join(content_parts)[:30]!r})")
            results["streaming"] = "PASS"
        else:
            print("WARN (no delta chunks received)")
            results["streaming"] = "WARN"
    except NvidiaProviderError as exc:
        print(f"FAIL ({exc.message})")
        results["streaming"] = "FAIL"

    # ── Test 5: Tool calling ───────────────────────────────────────
    print("\n[5/6] Testing tool calling...", end=" ")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "What files are in /tmp? Use the shell tool."}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "shell",
                        "description": "Execute a shell command",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string", "description": "Command to run"}
                            },
                            "required": ["command"],
                        },
                    },
                }
            ],
            "tool_choice": "auto",
            "max_tokens": 100,
        }
        resp = await provider.chat_completions(payload)
        resp_json = resp.json()
        choice = resp_json.get("choices", [{}])[0]
        finish = choice.get("finish_reason", "")
        tool_calls = choice.get("message", {}).get("tool_calls", [])
        if tool_calls:
            tc = tool_calls[0]
            print(f"PASS (tool: {tc['function']['name']}, id: {tc['id']})")
            results["tool_calling"] = "PASS"
        elif finish == "stop":
            print("WARN (model responded without tool call — may not support tools)")
            results["tool_calling"] = "WARN"
        else:
            print(f"UNKNOWN (finish_reason={finish})")
            results["tool_calling"] = "UNKNOWN"
    except NvidiaProviderError as exc:
        print(f"FAIL ({exc.message})")
        results["tool_calling"] = "FAIL"

    # ── Test 6: Reasoning ──────────────────────────────────────────
    print("\n[6/6] Testing reasoning...", end=" ")
    try:
        # Simple test to see if the model emits any reasoning tokens
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "What is 2+2? Think step by step."}
            ],
            "max_tokens": 200,
        }
        resp = await provider.chat_completions(payload)
        resp_json = resp.json()
        content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Check for reasoning-style response
        has_thinking = any(kw in content.lower() for kw in ("think", "step", "because", "therefore"))
        if has_thinking:
            print("PASS (model shows reasoning-style response)")
        else:
            print("UNKNOWN (cannot determine from standard API)")
        results["reasoning"] = "UNKNOWN"
    except NvidiaProviderError as exc:
        print(f"FAIL ({exc.message})")
        results["reasoning"] = "FAIL"

    # ── Summary ────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test, result in results.items():
        icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "UNKNOWN": "?"}.get(result, "?")
        print(f"  {icon} {test.replace('_', ' ').title()}: {result}")

    overall_ok = all(r in ("PASS", "WARN", "UNKNOWN") for r in results.values())
    print()
    if overall_ok:
        print("✓ NVIDIA integration is working!")
        print()
        print("Next steps:")
        if not settings.nvidia_default_model:
            print(f"  1. Set NVIDIA_DEFAULT_MODEL={model} in .env")
        print("  2. Start gateway: codebridge serve")
        print("  3. Configure Codex: codebridge configure-codex")
    else:
        failed = [k for k, v in results.items() if v == "FAIL"]
        print(f"✗ Some tests failed: {', '.join(failed)}")

    await provider.close()


def main():
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
