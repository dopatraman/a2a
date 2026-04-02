Subscribe to events from another agent.

Usage: /watch <agent_id>

The argument $ARGUMENTS is the agent_id to watch.

## Steps

1. If no agent_id was provided in "$ARGUMENTS", first call `list_agents` to show available agents. Ask the user which agent to watch.

2. Call the `watch` tool with the agent_id.

3. Tell the user they are now watching the target agent and will receive events as `<channel>` notifications.

## How to react to events

You are now watching another agent. Events will arrive as `<channel>` tags in your conversation. When you receive an event:

- **type="stderr"**: The watched agent hit an error. Analyze the error, identify likely causes, and provide debugging advice. Call the `emit` tool with your analysis so the watched agent can see it (if they are watching you back).

- **type="emit"**: The watched agent sent a curated update. Read it and respond if appropriate — they may be asking for help or sharing status.

- **type="status"**: The watched agent connected or disconnected. Acknowledge if relevant.

Be proactive. If you see an error you can diagnose, investigate it immediately — read relevant files, search for the issue, and provide a concrete fix. Don't wait for the user to ask.
