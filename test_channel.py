#!/usr/bin/env python3
"""
Phase 1: Validate that Python MCP SDK can send Claude Channel notifications.

This minimal server declares claude/channel capability and sends a channel
notification when the 'ping' tool is called. If Claude receives a <channel> tag,
the Python SDK works for channels.
"""
import asyncio

from mcp.server.lowlevel.server import Server, NotificationOptions, request_ctx
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
from mcp.types import (
    JSONRPCMessage,
    JSONRPCNotification,
    TextContent,
    Tool,
)

server = Server(name="test-channel", version="0.0.1")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="ping",
            description="Send a test channel notification to verify channels work",
            inputSchema={"type": "object", "properties": {}},
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "ping":
        ctx = request_ctx.get()
        session = ctx.session

        notification = JSONRPCNotification(
            jsonrpc="2.0",
            method="notifications/claude/channel",
            params={
                "content": "Hello from the channel! Phase 1 works.",
                "meta": {"test": "true"},
            },
        )
        await session.send_message(
            SessionMessage(message=JSONRPCMessage(notification))
        )
        return [TextContent(type="text", text="Channel notification sent")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read, write):
        init_options = server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={"claude/channel": {}},
        )
        await server.run(read, write, init_options)


if __name__ == "__main__":
    asyncio.run(main())
