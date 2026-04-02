"""Tests for MCP client tools — verifies correct WebSocket messages are sent."""
import asyncio
import json

import pytest

from a2a.mcp_client.tools import ToolHandler


class MockWebSocket:
    """Records sent messages and pre-loads responses into the handler's queue."""

    def __init__(self):
        self.sent: list[dict] = []

    async def send(self, data: str):
        self.sent.append(json.loads(data))


def make_handler(responses: list[dict] | None = None) -> tuple[ToolHandler, MockWebSocket]:
    ws = MockWebSocket()
    handler = ToolHandler(ws=ws)
    for resp in (responses or []):
        handler._response_queue.put_nowait(json.dumps(resp))
    return handler, ws


class TestToolList:
    def test_tool_list(self):
        handler = ToolHandler(ws=None)
        tools = handler.get_tools()
        names = {t.name for t in tools}
        assert names == {"connect", "disconnect", "emit", "watch", "unwatch", "list_agents"}

    def test_tools_have_input_schemas(self):
        handler = ToolHandler(ws=None)
        for tool in handler.get_tools():
            assert tool.inputSchema is not None
            assert tool.inputSchema["type"] == "object"


class TestToolMessages:
    async def test_connect_sends_ws_message(self):
        handler, ws = make_handler([{"response": "connected", "agent_id": "abc123"}])
        await handler.call("connect", {"name": "alice"})
        assert ws.sent == [{"action": "connect", "name": "alice"}]

    async def test_disconnect_sends_ws_message(self):
        handler, ws = make_handler([{"response": "disconnected"}])
        await handler.call("disconnect", {})
        assert ws.sent == [{"action": "disconnect"}]

    async def test_emit_sends_ws_message(self):
        handler, ws = make_handler([{"response": "emitted"}])
        await handler.call("emit", {"content": "hello", "context": {"file": "main.py"}})
        assert ws.sent == [{"action": "emit", "content": "hello", "context": {"file": "main.py"}}]

    async def test_watch_sends_ws_message(self):
        handler, ws = make_handler([{"response": "watching", "target_id": "abc123"}])
        await handler.call("watch", {"agent_id": "abc123"})
        assert ws.sent == [{"action": "watch", "target_id": "abc123"}]

    async def test_unwatch_sends_ws_message(self):
        handler, ws = make_handler([{"response": "unwatched", "target_id": "abc123"}])
        await handler.call("unwatch", {"agent_id": "abc123"})
        assert ws.sent == [{"action": "unwatch", "target_id": "abc123"}]

    async def test_list_agents_sends_ws_message(self):
        handler, ws = make_handler([{"response": "agents", "agents": []}])
        await handler.call("list_agents", {})
        assert ws.sent == [{"action": "list_agents"}]


class TestToolResponses:
    async def test_tool_returns_hub_response(self):
        handler, ws = make_handler([{"response": "connected", "agent_id": "abc123"}])
        result = await handler.call("connect", {"name": "alice"})
        assert "abc123" in result

    async def test_tool_errors_when_not_connected(self):
        handler = ToolHandler(ws=None)
        result = await handler.call("connect", {"name": "alice"})
        assert "error" in result.lower() or "not connected" in result.lower()
