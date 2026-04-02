"""Tests for the event envelope model."""
import json
from datetime import datetime, timezone

from a2a.hub.envelope import Envelope


class TestEnvelope:
    def test_create_with_defaults(self):
        env = Envelope(from_agent="alice", type="emit", payload={"msg": "hello"})
        assert env.id is not None
        assert env.from_agent == "alice"
        assert env.to_agent is None
        assert env.type == "emit"
        assert env.payload == {"msg": "hello"}
        assert env.timestamp is not None

    def test_create_with_all_fields(self):
        env = Envelope(
            id="test-id",
            from_agent="alice",
            to_agent="bob",
            timestamp="2026-04-01T00:00:00Z",
            type="stderr",
            payload={"error": "not found"},
        )
        assert env.id == "test-id"
        assert env.to_agent == "bob"
        assert env.timestamp == "2026-04-01T00:00:00Z"

    def test_unique_ids(self):
        a = Envelope(from_agent="x", type="emit", payload={})
        b = Envelope(from_agent="x", type="emit", payload={})
        assert a.id != b.id

    def test_serialization_roundtrip(self):
        env = Envelope(from_agent="alice", type="emit", payload={"key": "value"})
        data = json.loads(env.model_dump_json())
        restored = Envelope(**data)
        assert restored.id == env.id
        assert restored.from_agent == env.from_agent
        assert restored.payload == env.payload

