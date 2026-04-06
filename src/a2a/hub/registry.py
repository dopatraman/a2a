"""Agent registry and watch subscriptions."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    connected_at: datetime
    status: str = "connected"


class Registry:
    def __init__(self):
        self._agents: dict[str, AgentRecord] = {}
        self._watches: dict[str, set[str]] = {}  # watcher_id -> set of watched_ids
        self._reverse_watches: dict[str, set[str]] = {}  # watched_id -> set of watcher_ids

    def connect(self, name: str) -> str:
        agent_id = str(uuid4())[:8]
        self._agents[agent_id] = AgentRecord(
            agent_id=agent_id,
            name=name,
            connected_at=datetime.now(timezone.utc),
        )
        self._watches[agent_id] = set()
        self._reverse_watches[agent_id] = set()
        return agent_id

    def disconnect(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            return

        # Clean up watches where this agent is the watcher
        for target_id in self._watches.get(agent_id, set()):
            self._reverse_watches.get(target_id, set()).discard(agent_id)

        # Clean up watches where this agent is being watched
        for watcher_id in self._reverse_watches.get(agent_id, set()):
            self._watches.get(watcher_id, set()).discard(agent_id)

        self._watches.pop(agent_id, None)
        self._reverse_watches.pop(agent_id, None)
        del self._agents[agent_id]

    def watch(self, watcher_id: str, target_id: str) -> None:
        if watcher_id not in self._agents:
            raise ValueError(f"Unknown watcher: {watcher_id}")
        if target_id not in self._agents:
            raise ValueError(f"Unknown target: {target_id}")

        self._watches[watcher_id].add(target_id)
        self._reverse_watches[target_id].add(watcher_id)

    def unwatch(self, watcher_id: str, target_id: str) -> None:
        self._watches.get(watcher_id, set()).discard(target_id)
        self._reverse_watches.get(target_id, set()).discard(watcher_id)

    def get_watchers(self, agent_id: str) -> set[str]:
        return set(self._reverse_watches.get(agent_id, set()))

    def get_watched_by(self, agent_id: str) -> set[str]:
        return set(self._watches.get(agent_id, set()))

    def get_agent(self, agent_id: str) -> AgentRecord | None:
        return self._agents.get(agent_id)

    def get_agent_by_name(self, name: str) -> AgentRecord | None:
        matches = [a for a in self._agents.values() if a.name == name]
        if len(matches) > 1:
            raise ValueError(
                f"Multiple agents named '{name}' — use list_agents to disambiguate"
            )
        return matches[0] if matches else None

    def list_agents(self) -> list[AgentRecord]:
        return list(self._agents.values())
