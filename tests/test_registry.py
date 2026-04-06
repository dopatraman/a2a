"""Tests for the agent registry."""
import pytest

from a2a.hub.registry import Registry


class TestRegistryConnect:
    def test_connect_returns_agent_id(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        assert isinstance(agent_id, str)
        assert len(agent_id) > 0

    def test_connect_unique_ids(self):
        reg = Registry()
        id1 = reg.connect("alice")
        id2 = reg.connect("bob")
        assert id1 != id2

    def test_connect_same_name_allowed(self):
        reg = Registry()
        id1 = reg.connect("alice")
        id2 = reg.connect("alice")
        assert id1 != id2

    def test_list_agents_after_connect(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        agents = reg.list_agents()
        assert len(agents) == 1
        assert agents[0].agent_id == agent_id
        assert agents[0].name == "alice"
        assert agents[0].status == "connected"


class TestRegistryDisconnect:
    def test_disconnect_removes_agent(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        reg.disconnect(agent_id)
        assert reg.list_agents() == []

    def test_disconnect_unknown_id_is_noop(self):
        reg = Registry()
        reg.disconnect("nonexistent")  # should not raise

    def test_disconnect_cleans_up_watches(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        reg.watch(bob, alice)  # bob watches alice
        reg.disconnect(alice)  # alice disconnects
        assert reg.get_watchers(alice) == set()
        # bob's watch list should be cleaned up too
        assert reg.get_watched_by(bob) == set()


class TestRegistryWatch:
    def test_watch(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        reg.watch(bob, alice)  # bob watches alice
        assert bob in reg.get_watchers(alice)

    def test_get_watchers_empty(self):
        reg = Registry()
        alice = reg.connect("alice")
        assert reg.get_watchers(alice) == set()

    def test_watch_multiple_watchers(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        charlie = reg.connect("charlie")
        reg.watch(bob, alice)
        reg.watch(charlie, alice)
        watchers = reg.get_watchers(alice)
        assert watchers == {bob, charlie}

    def test_unwatch(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        reg.watch(bob, alice)
        reg.unwatch(bob, alice)
        assert reg.get_watchers(alice) == set()

    def test_unwatch_nonexistent_is_noop(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        reg.unwatch(bob, alice)  # never watched, should not raise

    def test_get_watched_by(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        charlie = reg.connect("charlie")
        reg.watch(alice, bob)     # alice watches bob
        reg.watch(alice, charlie)  # alice watches charlie
        assert reg.get_watched_by(alice) == {bob, charlie}

    def test_watch_unknown_target_raises(self):
        reg = Registry()
        bob = reg.connect("bob")
        with pytest.raises(ValueError):
            reg.watch(bob, "nonexistent")

    def test_watch_unknown_watcher_raises(self):
        reg = Registry()
        alice = reg.connect("alice")
        with pytest.raises(ValueError):
            reg.watch("nonexistent", alice)

    def test_duplicate_watch_is_idempotent(self):
        reg = Registry()
        alice = reg.connect("alice")
        bob = reg.connect("bob")
        reg.watch(bob, alice)
        reg.watch(bob, alice)  # duplicate
        assert reg.get_watchers(alice) == {bob}


class TestRegistryGetAgentByName:
    def test_found(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        agent = reg.get_agent_by_name("alice")
        assert agent is not None
        assert agent.agent_id == agent_id

    def test_not_found(self):
        reg = Registry()
        reg.connect("alice")
        assert reg.get_agent_by_name("bob") is None

    def test_empty_registry(self):
        reg = Registry()
        assert reg.get_agent_by_name("alice") is None

    def test_ambiguous_name_raises(self):
        reg = Registry()
        reg.connect("alice")
        reg.connect("alice")
        with pytest.raises(ValueError, match="Multiple agents"):
            reg.get_agent_by_name("alice")

    def test_after_disconnect(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        reg.disconnect(agent_id)
        assert reg.get_agent_by_name("alice") is None


class TestRegistryGetAgent:
    def test_get_agent(self):
        reg = Registry()
        agent_id = reg.connect("alice")
        agent = reg.get_agent(agent_id)
        assert agent is not None
        assert agent.name == "alice"

    def test_get_agent_unknown_returns_none(self):
        reg = Registry()
        assert reg.get_agent("nonexistent") is None
