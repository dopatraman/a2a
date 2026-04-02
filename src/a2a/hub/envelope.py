"""Event envelope model."""
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Envelope(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    from_agent: str
    to_agent: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
