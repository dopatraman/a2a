"""MCP tool definitions. Each tool sends a message over WebSocket to the hub."""
import asyncio
import json

from mcp.types import Tool


class ToolHandler:
    def __init__(self, ws):
        self._ws = ws
        self._response_queue: asyncio.Queue[str] = asyncio.Queue()

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="connect",
                description="Register this agent with the A2A hub",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Agent display name"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="disconnect",
                description="Deregister this agent from the A2A hub",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="emit",
                description="Publish an event to all agents watching this agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Event content"},
                        "context": {"type": "object", "description": "Optional context metadata"},
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="watch",
                description="Subscribe to events from another agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "ID of the agent to watch"},
                    },
                    "required": ["agent_id"],
                },
            ),
            Tool(
                name="unwatch",
                description="Unsubscribe from another agent's events",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "ID of the agent to stop watching"},
                    },
                    "required": ["agent_id"],
                },
            ),
            Tool(
                name="send",
                description="Send a direct message to a specific agent by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Name of the target agent"},
                        "message": {"type": "string", "description": "Message content"},
                        "context": {"type": "object", "description": "Optional context metadata"},
                    },
                    "required": ["to", "message"],
                },
            ),
            Tool(
                name="list_agents",
                description="List all agents connected to the A2A hub",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    async def call(self, name: str, arguments: dict) -> str:
        if self._ws is None:
            return "Error: not connected to hub"

        if name == "connect":
            msg = {"action": "connect", "name": arguments.get("name", "unnamed")}
        elif name == "disconnect":
            msg = {"action": "disconnect"}
        elif name == "emit":
            msg = {
                "action": "emit",
                "content": arguments.get("content", ""),
                "context": arguments.get("context", {}),
            }
        elif name == "watch":
            msg = {"action": "watch", "target_id": arguments["agent_id"]}
        elif name == "unwatch":
            msg = {"action": "unwatch", "target_id": arguments["agent_id"]}
        elif name == "send":
            msg = {
                "action": "send",
                "to": arguments["to"],
                "content": arguments["message"],
            }
            if arguments.get("context"):
                msg["context"] = arguments["context"]
        elif name == "list_agents":
            msg = {"action": "list_agents"}
        else:
            return f"Error: unknown tool {name}"

        await self._ws.send(json.dumps(msg))
        response = await self._response_queue.get()
        return response
