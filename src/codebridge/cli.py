"""
CodeBridge CLI — simple command-line interface.

Commands:
  codebridge serve             Start the gateway
  codebridge health            Check gateway health
  codebridge models            List NVIDIA models
  codebridge test              Run NVIDIA connectivity test
  codebridge usage             Show usage statistics
  codebridge token             Show local auth token
  codebridge configure-codex   Configure Codex to use CodeBridge
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the CodeBridge gateway."""
    from codebridge.main import run

    run()


def cmd_health(args: argparse.Namespace) -> None:
    """Check gateway health (connects to running gateway)."""
    import urllib.error
    import urllib.request

    from codebridge.config import get_settings

    settings = get_settings()
    url = f"http://{settings.codebridge_host}:{settings.codebridge_port}/health"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            print("CodeBridge Gateway")
            print("=" * 40)
            for k, v in data.items():
                print(f"  {k}: {v}")
    except urllib.error.URLError:
        print(f"ERROR: Gateway not reachable at {url}")
        print("Start with: codebridge serve")
        sys.exit(1)


def cmd_models(args: argparse.Namespace) -> None:
    """List available NVIDIA models."""

    async def _run():
        from codebridge.config import get_settings
        from codebridge.providers.nvidia import NvidiaProvider, NvidiaProviderError

        settings = get_settings()
        provider = NvidiaProvider(settings)

        print("Fetching NVIDIA models...")
        try:
            models = await provider.list_models()
            print(f"\n{'ID':<60} {'Object'}")
            print("-" * 70)
            for m in models:
                print(f"  {m.get('id', ''):<58} {m.get('object', 'model')}")
            print(f"\nTotal: {len(models)} models")
            print(
                "\nSet your preferred model:\n"
                "  Edit .env → NVIDIA_DEFAULT_MODEL=<model-id>"
            )
        except NvidiaProviderError as exc:
            print(f"ERROR: {exc.code}: {exc.message}")
            sys.exit(1)
        finally:
            await provider.close()

    asyncio.run(_run())


def cmd_test(args: argparse.Namespace) -> None:
    """Run NVIDIA connectivity test."""
    import subprocess

    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    test_script = scripts_dir / "test_nvidia.py"

    if test_script.exists():
        subprocess.run([sys.executable, str(test_script)], check=False)
    else:
        asyncio.run(_run_basic_test())


async def _run_basic_test() -> None:
    from codebridge.config import get_settings
    from codebridge.providers.nvidia import NvidiaProvider

    settings = get_settings()
    provider = NvidiaProvider(settings)

    print("NVIDIA CONNECTION TEST")
    print("=" * 40)

    if not settings.nvidia_api_key_configured:
        print("FAIL: NVIDIA_API_KEY not configured")
        print("Set it in .env: NVIDIA_API_KEY=YOUR_KEY")
        return

    print("Checking NVIDIA API...", end=" ")
    health = await provider.health()
    status = health.get("status", "unknown")
    if status == "ok":
        print(f"PASS ({health.get('models', 0)} models)")
    else:
        print(f"FAIL ({status})")
    await provider.close()


def cmd_usage(args: argparse.Namespace) -> None:
    """Show usage statistics (connects to running gateway)."""
    import urllib.error
    import urllib.request

    from codebridge.config import get_settings

    settings = get_settings()
    url = f"http://{settings.codebridge_host}:{settings.codebridge_port}/usage"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            print(json.dumps(data, indent=2))
    except urllib.error.URLError:
        print(f"ERROR: Gateway not reachable at {url}")
        sys.exit(1)


def cmd_token(args: argparse.Namespace) -> None:
    """Show local authentication token."""
    from codebridge.config import get_settings

    settings = get_settings()
    token = settings.effective_token
    print("CodeBridge Local Token")
    print("=" * 40)
    print(f"Token: {token}")
    print()
    print("Use in Codex configuration:")
    print("  env_key = CODEBRIDGE_LOCAL_TOKEN")
    print(f"  export CODEBRIDGE_LOCAL_TOKEN={token}")


def cmd_configure_codex(args: argparse.Namespace) -> None:
    """Configure Codex to use CodeBridge."""
    import subprocess

    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    config_script = scripts_dir / "configure_codex.py"

    if config_script.exists():
        subprocess.run([sys.executable, str(config_script)], check=False)
    else:
        _configure_codex_inline()


def _configure_codex_inline() -> None:
    from codebridge.config import get_settings

    settings = get_settings()
    token = settings.effective_token

    print("Configure Codex to use CodeBridge")
    print("=" * 40)
    print()
    print("Add this to ~/.codex/config.toml:")
    print()
    print("```toml")
    print("model_provider = \"codebridge\"")
    if settings.nvidia_default_model:
        print(f'model = "{settings.nvidia_default_model}"')
    else:
        print('model = "<your-nvidia-model-id>"')
    print()
    print("[model_providers.codebridge]")
    print('name = "CodeBridge NVIDIA"')
    print(f'base_url = "http://{settings.codebridge_host}:{settings.codebridge_port}/v1"')
    print('env_key = "CODEBRIDGE_LOCAL_TOKEN"')
    print('wire_api = "responses"')
    print("```")
    print()
    print("Set the environment variable:")
    print(f"  export CODEBRIDGE_LOCAL_TOKEN={token}")
    print()
    print("Or run the configure script:")
    print("  python scripts/configure_codex.py")


def cmd_convert(args: argparse.Namespace) -> None:
    """Convert a document (PDF, Office, HTML) to Markdown."""
    from codebridge.services.document import get_document_service

    if not args.path:
        print("ERROR: Please specify a file path to convert.")
        print("Usage: codebridge convert <file_path>")
        sys.exit(1)

    try:
        service = get_document_service()
        result = service.convert_file(args.path)
        print(result)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codebridge",
        description="CodeBridge Gateway — Connect Codex to NVIDIA NIM",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("serve", help="Start the CodeBridge gateway")
    subparsers.add_parser("health", help="Check gateway health")
    subparsers.add_parser("models", help="List available NVIDIA models")
    subparsers.add_parser("test", help="Run NVIDIA connectivity test")
    subparsers.add_parser("usage", help="Show usage statistics")
    subparsers.add_parser("token", help="Show local authentication token")
    subparsers.add_parser("configure-codex", help="Configure Codex to use CodeBridge")
    
    parser_convert = subparsers.add_parser(
        "convert", help="Convert a document (PDF, Office, HTML) to Markdown"
    )
    parser_convert.add_argument("path", help="Path to the document file to convert")

    args = parser.parse_args()

    commands = {
        "serve": cmd_serve,
        "health": cmd_health,
        "models": cmd_models,
        "test": cmd_test,
        "usage": cmd_usage,
        "token": cmd_token,
        "configure-codex": cmd_configure_codex,
        "convert": cmd_convert,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
