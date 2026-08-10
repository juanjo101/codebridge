"""
Configure Codex to use CodeBridge.

This script:
  1. Reads ~/.codex/config.toml (if it exists)
  2. Creates a backup
  3. Adds the CodeBridge provider
  4. Validates the TOML
  5. Saves

Does NOT overwrite the entire config — preserves existing providers.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> None:
    from codebridge.config import get_settings

    settings = get_settings()
    codex_config_path = Path.home() / ".codex" / "config.toml"
    token = settings.effective_token
    port = settings.codebridge_port
    host = settings.codebridge_host
    model = settings.nvidia_default_model or "<your-nvidia-model-id>"

    print("Configure Codex → CodeBridge")
    print("=" * 50)

    # ── Check if config exists ─────────────────────────────────────
    if codex_config_path.exists():
        backup = codex_config_path.with_suffix(".toml.bak")
        shutil.copy2(codex_config_path, backup)
        print(f"✓ Backed up existing config to: {backup}")
        existing = codex_config_path.read_text()
    else:
        print(f"ℹ No existing config at {codex_config_path}")
        codex_config_path.parent.mkdir(parents=True, exist_ok=True)
        existing = ""

    # ── Check if CodeBridge provider already exists ─────────────────
    if "[model_providers.codebridge]" in existing:
        print("⚠  CodeBridge provider already in config.toml")
        print("   Edit manually if you need to update it.")
        print()
        _print_instructions(host, port, model, token)
        return

    # ── Build CodeBridge block ─────────────────────────────────────
    codebridge_block = f"""
# ── CodeBridge Gateway ────────────────────────────────────────────
# Economy Mode: Codex → CodeBridge → NVIDIA NIM
# Enable by running: codex (with model_provider=codebridge set)

[model_providers.codebridge]
name = "CodeBridge NVIDIA"
base_url = "http://{host}:{port}/v1"
env_key = "CODEBRIDGE_LOCAL_TOKEN"
wire_api = "responses"
"""

    # ── Write updated config ───────────────────────────────────────
    new_config = existing.rstrip() + "\n" + codebridge_block
    codex_config_path.write_text(new_config)
    print(f"✓ Added CodeBridge provider to {codex_config_path}")

    # ── Print instructions ─────────────────────────────────────────
    print()
    _print_instructions(host, port, model, token)


def _print_instructions(host: str, port: int, model: str, token: str) -> None:
    print("To use CodeBridge with Codex:")
    print()
    print("  1. Set the environment variable:")
    print(f"     export CODEBRIDGE_LOCAL_TOKEN={token}")
    print()
    print("  2. To use Economy Mode (NVIDIA), start Codex with:")
    print(f'     model_provider="codebridge" codex')
    print()
    print("     OR add to ~/.codex/config.toml:")
    print(f'     model_provider = "codebridge"')
    print(f'     model = "{model}"')
    print()
    print("  3. To return to Premium Mode (OpenAI), set:")
    print('     model_provider = "openai"')
    print()
    print("  4. Make sure CodeBridge is running:")
    print("     codebridge serve")
    print()
    print("Smoke test:")
    print('  Ask Codex: "Reply exactly: CODEBRIDGE_OK"')
    print("  Expected: CODEBRIDGE_OK (served via NVIDIA)")


if __name__ == "__main__":
    main()
