"""Send channel notifications to Claude Code via stdio."""
from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage, JSONRPCNotification


async def send_channel_event(session, content: str, meta: dict[str, str] | None = None):
    notification = JSONRPCNotification(
        jsonrpc="2.0",
        method="notifications/claude/channel",
        params={"content": content, "meta": meta or {}},
    )
    await session.send_message(SessionMessage(message=JSONRPCMessage(notification)))
