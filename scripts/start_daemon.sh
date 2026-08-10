#!/usr/bin/env bash
# Start CodeBridge Gateway persistently in the background

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$DIR/codebridge_server.log"
PID_FILE="$DIR/.codebridge.pid"

# Kill existing process listening on port 8787 if any
PID_ON_PORT=$(lsof -t -i:8787 2>/dev/null)
if [ -n "$PID_ON_PORT" ]; then
    echo "Stopping existing process on port 8787 (PID: $PID_ON_PORT)..."
    kill -9 "$PID_ON_PORT" 2>/dev/null
    sleep 1
fi

echo "Starting CodeBridge Gateway in background..."
nohup uv run codebridge serve > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 2

if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "✓ CodeBridge Gateway started persistently (PID: $NEW_PID)"
    echo "  - Web Chat GUI: http://127.0.0.1:8787/chat"
    echo "  - MCP SSE:      http://127.0.0.1:8787/mcp/sse"
    echo "  - Server log:   $LOG_FILE"
else
    echo "✗ Failed to start CodeBridge. Check $LOG_FILE"
fi
