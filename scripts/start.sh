#!/bin/bash
# Start CodeBridge Gateway

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

export PATH="$HOME/.local/bin:$PATH"

cd "$PROJECT_DIR"

echo "Starting CodeBridge Gateway..."
echo "Press Ctrl+C to stop."
echo ""

exec uv run codebridge serve
