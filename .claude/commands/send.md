Send a direct message to another agent.

Usage: /send <agent_name> <message>

The argument $ARGUMENTS contains the target agent name followed by the message.

## Steps

1. Parse `$ARGUMENTS`: the first word is the agent name, the rest is the message. If either is missing, tell the user the correct usage.

2. Call the `send` tool with `to` set to the agent name and `message` set to the message text.

3. If the tool returns an error (agent not found, ambiguous name, not connected), relay it to the user. For ambiguous names, suggest running `list_agents` to see agent IDs.

4. On success, confirm: "Message sent to <agent_name>."
