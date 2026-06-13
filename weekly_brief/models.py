from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Entry:
    content: str
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Entry:
        return cls(**data)


@dataclass
class Group:
    name: str
    entries: list[Entry] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Group:
        entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        return cls(name=data["name"], entries=entries, id=data.get("id", uuid.uuid4().hex[:8]))
