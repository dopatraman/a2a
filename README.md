# A2A — Agent-to-Agent Communication

Let your Claude Code sessions talk to each other.

A2A is a hub that connects Claude Code agents so they can watch each other's work in real-time. The killer use case: one agent runs your code, another watches for errors and debugs them live.

## How it works

```
Claude A --stdio--> MCP Client A --WebSocket--> Hub (:7800) <--WebSocket-- MCP Client B <--stdio-- Claude B
```

**The hub** is a standalone server that keeps track of who's connected and who's watching whom. It routes events between agents.

**Each agent gets an MCP client** that Claude Code spawns automatically. It's a thin bridge — WebSocket to the hub on one side, stdio to Claude on the other. When the hub pushes an event, the MCP client injects it into Claude's session as a `<channel>` notification.

## Quickstart

### Setup

```bash
cd /path/to/a2a
python3 -m venv .venv && source .venv/bin/activate
make install
```

### Run

**Terminal 1** — start the hub:
```bash
make hub
```

**Terminal 2** — agent Alice:
```bash
cd /path/to/a2a
claude --dangerously-load-development-channels server:a2a
```
```
> /connect alice
Connected as alice (id: a1b2c3d4)
```

**Terminal 3** — agent Bob watches Alice:
```bash
cd /path/to/a2a
claude --dangerously-load-development-channels server:a2a
```
```
> /connect bob
> /watch a1b2c3d4
Watching alice.
```

**Back in Terminal 2** — Alice hits a bug:
```
> run python3 buggy_script.py
```

Bob sees the error land in his session and starts debugging. No copy-paste, no Slack, no context switching.

Alice can also send curated updates:
```
> call emit with content "tried 3 fixes, all fail on the same import"
```

## Architecture

| Layer | What it does |
|-------|-------------|
| **Hub** (`src/a2a/hub/`) | Central server. Owns the agent registry, watch subscriptions, and event routing. Runs on `:7800`. |
| **MCP Client** (`src/a2a/mcp_client/`) | Per-agent bridge. Spawned by Claude Code via stdio. Connects to hub via WebSocket. Translates between the two worlds. |
| **Skills** (`.claude/commands/`) | `/connect` and `/watch` — the UX layer so agents don't call raw MCP tools. |

### Event flow

1. Alice runs a command that fails
2. Alice (or a hook) calls `emit` with the error
3. MCP Client A sends it to the hub over WebSocket
4. Hub checks: who's watching Alice? → Bob
5. Hub pushes the event to MCP Client B over WebSocket
6. MCP Client B injects a `<channel>` notification into Bob's Claude session
7. Bob's Claude sees the error and reacts

## Tools

Agents get these MCP tools automatically:

| Tool | What it does |
|------|-------------|
| `connect(name)` | Register with the hub |
| `disconnect()` | Leave the hub |
| `watch(agent_id)` | Subscribe to another agent's events |
| `unwatch(agent_id)` | Unsubscribe |
| `emit(content)` | Broadcast an event to your watchers |
| `list_agents()` | See who's connected |

## Tests

```bash
make test
```

39 tests covering the envelope model, agent registry, event router, and MCP tool message formatting.

## What's next

See [POST_MVP.md](POST_MVP.md) for the roadmap: direct messaging between agents, message queues, authentication, backpressure, and network support.
