#!/bin/bash
# CodeBridge Setup Script for Linux/macOS
# ==========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"

echo ""
echo "=============================================="
echo " CODEBRIDGE GATEWAY — SETUP"
echo "=============================================="
echo ""

cd "$PROJECT_DIR"

# ── Check Python ───────────────────────────────────────────────────
echo "[1/6] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  ✓ $PYTHON_VERSION"
    PYTHON=python3
else
    echo "  ✗ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# ── Check/Install uv ──────────────────────────────────────────────
echo "[2/6] Checking uv..."
if command -v uv &>/dev/null; then
    UV_VERSION=$(uv --version)
    echo "  ✓ $UV_VERSION"
else
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv &>/dev/null; then
        echo "  ✓ uv installed"
    else
        echo "  ✗ uv installation failed. Install manually: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

export PATH="$HOME/.local/bin:$PATH"

# ── Create virtual environment and install ─────────────────────────
echo "[3/6] Installing dependencies..."
uv sync --extra dev
echo "  ✓ Dependencies installed"

# ── Create .env if not exists ──────────────────────────────────────
echo "[4/6] Creating .env..."
if [ -f "$ENV_FILE" ]; then
    echo "  ✓ .env already exists (not overwriting)"
else
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
    echo "  ✓ Created .env from .env.example"
fi

# ── Generate local token ───────────────────────────────────────────
echo "[5/6] Generating local auth token..."
TOKEN_FILE="$PROJECT_DIR/.codebridge_token"
if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
    echo "  ✓ Existing token loaded"
else
    TOKEN=$(uv run python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "$TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    echo "  ✓ Token generated"
fi

# ── Run unit tests ─────────────────────────────────────────────────
echo "[6/6] Running tests..."
if uv run pytest tests/unit/ tests/integration/ -q --tb=short 2>&1; then
    echo "  ✓ Tests passed"
else
    echo "  ⚠  Some tests failed (check output above)"
fi

echo ""
echo "=============================================="
echo " CODEBRIDGE INSTALLED"
echo "=============================================="
echo ""
echo " Gateway URL:  http://127.0.0.1:8787"
echo ""
echo " ┌──────────────────────────────────────────"
echo " │ ACTION REQUIRED"
echo " │"
echo " │ Open:"
echo " │   $ENV_FILE"
echo " │"
echo " │ Set:"
echo " │   NVIDIA_API_KEY=YOUR_KEY_HERE"
echo " └──────────────────────────────────────────"
echo ""
echo " Then:"
echo ""
echo "   Test NVIDIA connection:"
echo "     python scripts/test_nvidia.py"
echo ""
echo "   Start gateway:"
echo "     ./scripts/start.sh"
echo "     # or: uv run codebridge serve"
echo ""
echo "   Configure Codex:"
echo "     uv run python scripts/configure_codex.py"
echo ""
echo "   Set Codex token:"
echo "     export CODEBRIDGE_LOCAL_TOKEN=$TOKEN"
echo ""
echo "=============================================="
