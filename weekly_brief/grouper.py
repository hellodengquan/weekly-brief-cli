from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Optional

from .models import Entry, Group
from .store import load_entries, load_groups, save_groups


def auto_group_by_tag(data_dir: Path) -> list[Group]:
    entries = load_entries(data_dir)
    tag_map: dict[str, list[Entry]] = defaultdict(list)
    untagged: list[Entry] = []

    for e in entries:
        if e.tags:
            for tag in e.tags:
                tag_map[tag].append(e)
        else:
            untagged.append(e)

    groups: list[Group] = []
    for tag, items in tag_map.items():
        groups.append(Group(name=tag, entries=items))

    if untagged:
        groups.append(Group(name="未分类", entries=untagged))

    return groups


def create_manual_group(name: str, entry_ids: list[str], data_dir: Path) -> Group:
    entries = load_entries(data_dir)
    id_set = set(entry_ids)
    matched = [e for e in entries if e.id in id_set]
    group = Group(name=name, entries=matched)

    groups = load_groups(data_dir)
    groups.append(group)
    save_groups(groups, data_dir)
    return group


def remove_group(group_id: str, data_dir: Path) -> bool:
    groups = load_groups(data_dir)
    new_groups = [g for g in groups if g.id != group_id]
    if len(new_groups) == len(groups):
        return False
    save_groups(new_groups, data_dir)
    return True


def list_groups(data_dir: Path) -> list[Group]:
    return load_groups(data_dir)


def merge_auto_and_manual(data_dir: Path) -> list[Group]:
    auto = auto_group_by_tag(data_dir)
    manual = load_groups(data_dir)
    return auto + manual
