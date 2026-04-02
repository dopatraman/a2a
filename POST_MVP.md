# Post-MVP TODOs

## Direct Messaging
- Add `send(to_agent_id, content)` MCP tool for point-to-point agent communication
- Envelope already has `to_agent` field — routing logic needed in the router

## Message Queues
- Add per-agent in-memory buffer in the router
- If a listener callback fails or WebSocket is temporarily down, events accumulate and drain on reconnect
- Prevents dropped messages, especially important once direct messaging exists
- Consider max queue depth and eviction policy (drop oldest vs reject new)

## Authentication
- Agents should authenticate when connecting to the hub (token, API key, or session-based)
- Hub should verify agent identity before allowing registration
- Watch permissions: gate who can watch whom (not all agents should be observable by all)
- Hook ingest endpoint (`/api/hook-ingest`) needs auth to prevent unauthorized event injection
- Required before any network/remote deployment

## Backpressure
- Rate limiting on emit: prevent a single agent from flooding the hub and overwhelming watchers
- Per-agent event rate caps (e.g., max N events per second)
- Watcher-side protection: if a watcher's context window is filling up, signal the hub to throttle or batch events
- Dashboard throttling: aggregate/sample events if volume exceeds what the UI can render

## Automatic Error Capture (Hooks)
- PostToolUse hook on Bash that auto-forwards stderr/errors to the hub
- Removes the need for agents to manually `emit` errors
- Hook script exists at `src/a2a/hooks/post_bash.sh`, installer at `src/a2a/hooks/install.py`
- Needs investigation: hook must be installed before Claude session starts (hooks are read at startup)
- `/connect` skill should install the hook and prompt a session restart if needed

## Network Support
- Make hub URL configurable (replace hardcoded `127.0.0.1:7800`)
- Add TLS for remote connections
- Auth becomes mandatory (see above)
