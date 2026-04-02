Register this agent with the A2A hub.

Usage: /connect <name>

The argument $ARGUMENTS is the agent's display name.

## Steps

1. Check if the hub is running by calling the `list_agents` tool. If it fails with "not connected to hub", tell the user to start the hub first with `make hub` in a separate terminal.

2. Call the `connect` tool with the name "$ARGUMENTS". If no name was provided, use "agent" as the default.

3. The tool returns a JSON response with `agent_id`. Extract it and save it:
   - Create the directory `~/.a2a/` if it doesn't exist
   - Write the agent_id to `~/.a2a/agent_id`

4. Tell the user:
   - Their agent name and ID
   - That errors from Bash commands will be automatically forwarded to watchers (once hooks are set up)
   - That they can use the `emit` tool to send curated updates to anyone watching them
   - That other agents can watch them using `/watch <agent_id>`

## After connecting

You are now connected to the A2A hub. From this point forward:
- When you encounter errors, warnings, or significant events, call the `emit` tool to share them with any agents watching you.
- Use your judgment about what's worth emitting. Errors and blockers are always worth sharing. Routine success output is not.
