"""Event routing — delivers envelopes to watchers and dashboard listeners."""
from collections.abc import Awaitable, Callable
from typing import Union

from a2a.hub.envelope import Envelope
from a2a.hub.registry import Registry

Listener = Callable[[Envelope], Union[None, Awaitable[None]]]


class EventRouter:
    def __init__(self, registry: Registry):
        self._registry = registry
        self._listeners: dict[str, Listener] = {}
        self._dashboard_listeners: list[Listener] = []

    def add_listener(self, agent_id: str, callback: Listener) -> None:
        self._listeners[agent_id] = callback

    def remove_listener(self, agent_id: str) -> None:
        self._listeners.pop(agent_id, None)

    def add_dashboard_listener(self, callback: Listener) -> None:
        self._dashboard_listeners.append(callback)

    def remove_dashboard_listener(self, callback: Listener) -> None:
        try:
            self._dashboard_listeners.remove(callback)
        except ValueError:
            pass

    async def route(self, envelope: Envelope) -> None:
        if envelope.to_agent is not None:
            # Direct message — deliver only to the target agent
            listener = self._listeners.get(envelope.to_agent)
            if listener is not None:
                result = listener(envelope)
                if result is not None:
                    await result
        else:
            # Broadcast — deliver to watchers of the sender
            watchers = self._registry.get_watchers(envelope.from_agent)
            for watcher_id in watchers:
                listener = self._listeners.get(watcher_id)
                if listener is not None:
                    result = listener(envelope)
                    if result is not None:
                        await result

        # Dashboard listeners always receive everything
        for listener in self._dashboard_listeners:
            result = listener(envelope)
            if result is not None:
                await result
