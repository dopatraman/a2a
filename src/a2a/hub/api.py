"""HTTP + WebSocket API routes for the hub."""
import json

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from a2a.hub.envelope import Envelope
from a2a.hub.registry import Registry
from a2a.hub.router import EventRouter

registry = Registry()
router = EventRouter(registry)


async def list_agents(request: Request) -> JSONResponse:
    agents = registry.list_agents()
    return JSONResponse([
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "connected_at": a.connected_at.isoformat(),
            "status": a.status,
        }
        for a in agents
    ])


async def hook_ingest(request: Request) -> JSONResponse:
    body = await request.json()
    agent_id = body.get("agent_id")
    if not agent_id or not registry.get_agent(agent_id):
        return JSONResponse({"error": "unknown agent"}, status_code=400)

    envelope = Envelope(
        from_agent=agent_id,
        type="stderr",
        payload={
            "stderr": body.get("stderr", ""),
            "exit_code": body.get("exit_code", ""),
            "command": body.get("command", ""),
        },
    )
    await router.route(envelope)
    return JSONResponse({"status": "ok"})


async def agent_ws(websocket: WebSocket):
    await websocket.accept()
    agent_id = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "connect":
                name = msg.get("name", "unnamed")
                agent_id = registry.connect(name)

                # Register listener: when events are routed to this agent,
                # send them over this WebSocket
                async def send_envelope(env: Envelope, ws=websocket):
                    await ws.send_text(env.model_dump_json())

                router.add_listener(agent_id, send_envelope)

                # Notify dashboard of new connection
                await router.route(Envelope(
                    from_agent=agent_id,
                    type="status",
                    payload={"event": "connected", "name": name},
                ))

                await websocket.send_text(json.dumps({
                    "response": "connected",
                    "agent_id": agent_id,
                }))

            elif action == "disconnect":
                if agent_id:
                    router.remove_listener(agent_id)
                    await router.route(Envelope(
                        from_agent=agent_id,
                        type="status",
                        payload={"event": "disconnected"},
                    ))
                    registry.disconnect(agent_id)
                    agent_id = None
                await websocket.send_text(json.dumps({"response": "disconnected"}))

            elif action == "emit":
                if not agent_id:
                    await websocket.send_text(json.dumps({"error": "not connected"}))
                    continue
                envelope = Envelope(
                    from_agent=agent_id,
                    type="emit",
                    payload={
                        "content": msg.get("content", ""),
                        "context": msg.get("context", {}),
                    },
                )
                await router.route(envelope)
                await websocket.send_text(json.dumps({"response": "emitted"}))

            elif action == "watch":
                if not agent_id:
                    await websocket.send_text(json.dumps({"error": "not connected"}))
                    continue
                target_id = msg.get("target_id")
                try:
                    registry.watch(agent_id, target_id)
                    await websocket.send_text(json.dumps({
                        "response": "watching",
                        "target_id": target_id,
                    }))
                except ValueError as e:
                    await websocket.send_text(json.dumps({"error": str(e)}))

            elif action == "unwatch":
                if not agent_id:
                    await websocket.send_text(json.dumps({"error": "not connected"}))
                    continue
                target_id = msg.get("target_id")
                registry.unwatch(agent_id, target_id)
                await websocket.send_text(json.dumps({
                    "response": "unwatched",
                    "target_id": target_id,
                }))

            elif action == "list_agents":
                agents = registry.list_agents()
                await websocket.send_text(json.dumps({
                    "response": "agents",
                    "agents": [
                        {"agent_id": a.agent_id, "name": a.name, "status": a.status}
                        for a in agents
                    ],
                }))

            else:
                await websocket.send_text(json.dumps({"error": f"unknown action: {action}"}))

    except WebSocketDisconnect:
        pass
    finally:
        if agent_id:
            router.remove_listener(agent_id)
            await router.route(Envelope(
                from_agent=agent_id,
                type="status",
                payload={"event": "disconnected"},
            ))
            registry.disconnect(agent_id)


async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()

    async def send_to_dashboard(env: Envelope, ws=websocket):
        await ws.send_text(env.model_dump_json())

    router.add_dashboard_listener(send_to_dashboard)

    try:
        # Keep connection alive — dashboard only receives, doesn't send commands
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        router.remove_dashboard_listener(send_to_dashboard)


def create_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/api/agents", list_agents, methods=["GET"]),
            Route("/api/hook-ingest", hook_ingest, methods=["POST"]),
            WebSocketRoute("/ws/agent", agent_ws),
            WebSocketRoute("/ws/dashboard", dashboard_ws),
        ],
    )
