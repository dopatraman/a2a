#!/bin/bash
# PostToolUse hook for Bash — forwards errors to the A2A hub.
# Reads tool result JSON from stdin. If the output looks like an error,
# POSTs it to the hub's /api/hook-ingest endpoint.

AGENT_ID_FILE="$HOME/.a2a/agent_id"
HUB_URL="http://127.0.0.1:7800/api/hook-ingest"
DEBUG_LOG="$HOME/.a2a/hook_debug.log"

# No agent_id = not connected, nothing to do
if [ ! -f "$AGENT_ID_FILE" ]; then
    exit 0
fi

AGENT_ID=$(cat "$AGENT_ID_FILE")
INPUT=$(cat)

# Debug: log the raw input
echo "=== $(date) ===" >> "$DEBUG_LOG"
echo "$INPUT" >> "$DEBUG_LOG"
echo "---" >> "$DEBUG_LOG"

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
RESULT=$(echo "$INPUT" | jq -r '.tool_result // ""')

echo "COMMAND: $COMMAND" >> "$DEBUG_LOG"
echo "RESULT: $RESULT" >> "$DEBUG_LOG"

# Heuristic: check if the result contains error indicators
# This catches tracebacks, common error prefixes, and non-zero exit mentions
if echo "$RESULT" | grep -qiE '(error|exception|traceback|fatal|panic|fail|denied|not found|no such file|exit code [1-9])'; then
    echo "MATCH: sending to hub" >> "$DEBUG_LOG"
    curl -s -X POST "$HUB_URL" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg agent_id "$AGENT_ID" \
            --arg stderr "$RESULT" \
            --arg command "$COMMAND" \
            '{agent_id: $agent_id, stderr: $stderr, command: $command}'
        )" >> "$DEBUG_LOG" 2>&1
else
    echo "NO MATCH: not an error" >> "$DEBUG_LOG"
fi

echo "" >> "$DEBUG_LOG"
exit 0
