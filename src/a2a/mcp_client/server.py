"""MCP client — bridges Claude (stdio) and the hub (WebSocket)."""
import asyncio
import json

import websockets

from mcp.server.lowlevel.server import Server, NotificationOptions, request_ctx
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from a2a.mcp_client.channel import send_channel_event
from a2a.mcp_client.tools import ToolHandler

HUB_URL = "ws://127.0.0.1:7800/ws/agent"

server = Server(name="a2a", version="0.1.0")
tool_handler = ToolHandler(ws=None)

# Store session ref for the WebSocket listener to push channel notifications
_session = None


@server.list_tools()
async def list_tools():
    return tool_handler.get_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    global _session
    if _session is None:
        ctx = request_ctx.get()
        _session = ctx.session

    result = await tool_handler.call(name, arguments)
    return [TextContent(type="text", text=result)]


async def ws_demux(ws):
    """Single reader for the WebSocket. Sorts messages into:
    - Tool responses (have 'response' or 'error' key) → response queue
    - Hub events (have 'from_agent' key) → channel notifications to Claude
    """
    try:
        async for raw in ws:
            msg = json.loads(raw)
            if "from_agent" in msg:
                # Hub-pushed event — forward to Claude as channel notification
                from_name = msg.get("from_agent", "unknown")
                event_type = msg.get("type", "event")
                payload = msg.get("payload", {})
                content = json.dumps(payload) if isinstance(payload, dict) else str(payload)
                meta = {"from": from_name, "type": event_type}
                if msg.get("to_agent"):
                    meta["direct"] = "true"
                if _session:
                    await send_channel_event(_session, content, meta)
            else:
                # Tool call response — put in queue for ToolHandler.call()
                await tool_handler._response_queue.put(raw)
    except websockets.ConnectionClosed:
        pass


async def main():
    global _session

    async with stdio_server() as (read, write):
        init_options = server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={"claude/channel": {}},
        )

        # Connect to hub
        try:
            ws = await websockets.connect(HUB_URL)
            tool_handler._ws = ws

            # Run MCP server and WebSocket demuxer concurrently
            async with asyncio.TaskGroup() as tg:
                tg.create_task(server.run(read, write, init_options))
                tg.create_task(ws_demux(ws))
        except (ConnectionRefusedError, OSError):
            # Hub not running — still start the MCP server so tools can report the error
            await server.run(read, write, init_options)


if __name__ == "__main__":
    asyncio.run(main())
