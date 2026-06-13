from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import Entry, Group

DEFAULT_DATA_DIR = Path.home() / ".weekly-brief"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _entries_path(data_dir: Path) -> Path:
    return data_dir / "entries.json"


def _groups_path(data_dir: Path) -> Path:
    return data_dir / "groups.json"


def init_store(data_dir: Path | None = None) -> Path:
    d = data_dir or DEFAULT_DATA_DIR
    _ensure_dir(d)
    ep = _entries_path(d)
    gp = _groups_path(d)
    if not ep.exists():
        ep.write_text("[]", encoding="utf-8")
    if not gp.exists():
        gp.write_text("[]", encoding="utf-8")
    return d


def load_entries(data_dir: Path) -> list[Entry]:
    p = _entries_path(data_dir)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [Entry.from_dict(e) for e in raw]


def save_entries(entries: list[Entry], data_dir: Path) -> None:
    _ensure_dir(data_dir)
    p = _entries_path(data_dir)
    p.write_text(
        json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_entry(content: str, tags: list[str], source: str, data_dir: Path) -> Entry:
    entries = load_entries(data_dir)
    entry = Entry(content=content, tags=tags, source=source)
    entries.append(entry)
    save_entries(entries, data_dir)
    return entry


def delete_entry(entry_id: str, data_dir: Path) -> bool:
    entries = load_entries(data_dir)
    new_entries = [e for e in entries if e.id != entry_id]
    if len(new_entries) == len(entries):
        return False
    save_entries(new_entries, data_dir)

    groups = load_groups(data_dir)
    groups_dirty = False
    for group in groups:
        new_group_entries = [e for e in group.entries if e.id != entry_id]
        if len(new_group_entries) != len(group.entries):
            group.entries = new_group_entries
            groups_dirty = True
    if groups_dirty:
        save_groups(groups, data_dir)

    return True


def load_groups(data_dir: Path) -> list[Group]:
    p = _groups_path(data_dir)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [Group.from_dict(g) for g in raw]


def save_groups(groups: list[Group], data_dir: Path) -> None:
    _ensure_dir(data_dir)
    p = _groups_path(data_dir)
    p.write_text(
        json.dumps([g.to_dict() for g in groups], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
