"""Tests for event routing."""
import asyncio

import pytest

from a2a.hub.envelope import Envelope
from a2a.hub.router import EventRouter
from a2a.hub.registry import Registry


class TestEventRouter:
    def setup_method(self):
        self.registry = Registry()
        self.router = EventRouter(self.registry)

    async def test_route_to_watcher(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        self.registry.watch(bob, alice)  # bob watches alice

        received = []
        self.router.add_listener(bob, received.append)

        envelope = Envelope(from_agent=alice, type="emit", payload={"msg": "hello"})
        await self.router.route(envelope)

        assert len(received) == 1
        assert received[0].from_agent == alice
        assert received[0].payload == {"msg": "hello"}

    async def test_route_no_watchers(self):
        alice = self.registry.connect("alice")

        envelope = Envelope(from_agent=alice, type="emit", payload={})
        await self.router.route(envelope)  # should not raise

    async def test_route_multiple_watchers(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        charlie = self.registry.connect("charlie")
        self.registry.watch(bob, alice)
        self.registry.watch(charlie, alice)

        bob_received = []
        charlie_received = []
        self.router.add_listener(bob, bob_received.append)
        self.router.add_listener(charlie, charlie_received.append)

        envelope = Envelope(from_agent=alice, type="stderr", payload={"err": "fail"})
        await self.router.route(envelope)

        assert len(bob_received) == 1
        assert len(charlie_received) == 1

    async def test_route_does_not_send_to_non_watchers(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        charlie = self.registry.connect("charlie")
        self.registry.watch(bob, alice)  # only bob watches alice

        charlie_received = []
        self.router.add_listener(charlie, charlie_received.append)

        envelope = Envelope(from_agent=alice, type="emit", payload={})
        await self.router.route(envelope)

        assert len(charlie_received) == 0

    async def test_remove_listener(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        self.registry.watch(bob, alice)

        received = []
        self.router.add_listener(bob, received.append)
        self.router.remove_listener(bob)

        envelope = Envelope(from_agent=alice, type="emit", payload={})
        await self.router.route(envelope)

        assert len(received) == 0

    async def test_route_also_sends_to_dashboard_listeners(self):
        alice = self.registry.connect("alice")

        dashboard_received = []
        self.router.add_dashboard_listener(dashboard_received.append)

        envelope = Envelope(from_agent=alice, type="emit", payload={"x": 1})
        await self.router.route(envelope)

        assert len(dashboard_received) == 1
        assert dashboard_received[0].from_agent == alice

    async def test_direct_message_delivered_to_target(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")

        bob_received = []
        self.router.add_listener(bob, bob_received.append)

        envelope = Envelope(from_agent=alice, to_agent=bob, type="direct", payload={"msg": "hi"})
        await self.router.route(envelope)

        assert len(bob_received) == 1
        assert bob_received[0].payload == {"msg": "hi"}

    async def test_direct_message_not_sent_to_watchers(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        charlie = self.registry.connect("charlie")
        self.registry.watch(charlie, alice)  # charlie watches alice

        charlie_received = []
        bob_received = []
        self.router.add_listener(charlie, charlie_received.append)
        self.router.add_listener(bob, bob_received.append)

        # Direct message from alice to bob — charlie should NOT get it
        envelope = Envelope(from_agent=alice, to_agent=bob, type="direct", payload={})
        await self.router.route(envelope)

        assert len(bob_received) == 1
        assert len(charlie_received) == 0

    async def test_direct_message_goes_to_dashboard(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")

        dashboard_received = []
        self.router.add_dashboard_listener(dashboard_received.append)

        envelope = Envelope(from_agent=alice, to_agent=bob, type="direct", payload={})
        await self.router.route(envelope)

        assert len(dashboard_received) == 1

    async def test_direct_message_missing_listener_no_error(self):
        alice = self.registry.connect("alice")
        bob = self.registry.connect("bob")
        # No listener registered for bob
        envelope = Envelope(from_agent=alice, to_agent=bob, type="direct", payload={})
        await self.router.route(envelope)  # should not raise

    async def test_remove_dashboard_listener(self):
        alice = self.registry.connect("alice")

        received = []
        cb = received.append
        self.router.add_dashboard_listener(cb)
        self.router.remove_dashboard_listener(cb)

        envelope = Envelope(from_agent=alice, type="emit", payload={})
        await self.router.route(envelope)

        assert len(received) == 0
