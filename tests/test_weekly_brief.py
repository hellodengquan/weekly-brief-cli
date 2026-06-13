from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from weekly_brief.cli import app
from weekly_brief.store import init_store, add_entry, delete_entry, load_entries, load_groups, save_groups
from weekly_brief.models import Entry, Group


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    init_store(tmp_path)
    return tmp_path


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_delete_entry_cleans_up_orphan_references(tmp_data_dir: Path):
    e1 = add_entry("素材一", ["后端"], "", tmp_data_dir)
    e2 = add_entry("素材二", ["前端"], "", tmp_data_dir)
    e3 = add_entry("素材三", ["文档"], "", tmp_data_dir)

    save_groups([
        Group(name="组A", entries=[e1, e2]),
        Group(name="组B", entries=[e2, e3]),
        Group(name="组C", entries=[e1]),
    ], tmp_data_dir)

    ok = delete_entry(e2.id, tmp_data_dir)
    assert ok is True

    entries = load_entries(tmp_data_dir)
    assert {e.id for e in entries} == {e1.id, e3.id}

    groups = load_groups(tmp_data_dir)
    assert len(groups) == 3, "空分组不应被删除"

    group_a = next(g for g in groups if g.name == "组A")
    assert {e.id for e in group_a.entries} == {e1.id}, "孤儿引用应被清理"

    group_b = next(g for g in groups if g.name == "组B")
    assert {e.id for e in group_b.entries} == {e3.id}, "孤儿引用应被清理"

    group_c = next(g for g in groups if g.name == "组C")
    assert {e.id for e in group_c.entries} == {e1.id}


def test_list_since_filter(runner: CliRunner, tmp_data_dir: Path):
    save_groups([], tmp_data_dir)

    old_entry = Entry(content="上周素材", tags=["杂项"], created_at="2026-06-01 10:00")
    new_entry = Entry(content="本周素材", tags=["杂项"], created_at="2026-06-10 14:30")
    with (tmp_data_dir / "entries.json").open("w", encoding="utf-8") as f:
        import json
        json.dump([old_entry.to_dict(), new_entry.to_dict()], f, ensure_ascii=False)

    result = runner.invoke(app, ["list", "--dir", str(tmp_data_dir), "--since", "2026-06-07"])
    assert result.exit_code == 0, result.output
    assert "本周素材" in result.output
    assert "上周素材" not in result.output


def test_list_since_plus_tag_filter(runner: CliRunner, tmp_data_dir: Path):
    save_groups([], tmp_data_dir)

    import json
    entries = [
        Entry(content="老后端", tags=["后端"], created_at="2026-06-01 09:00").to_dict(),
        Entry(content="新后端", tags=["后端"], created_at="2026-06-10 09:00").to_dict(),
        Entry(content="新前端", tags=["前端"], created_at="2026-06-10 09:00").to_dict(),
    ]
    with (tmp_data_dir / "entries.json").open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)

    result = runner.invoke(
        app,
        ["list", "--dir", str(tmp_data_dir), "--since", "2026-06-07", "--tag", "后端"],
    )
    assert result.exit_code == 0, result.output
    assert "新后端" in result.output
    assert "老后端" not in result.output, "时间筛选应生效"
    assert "新前端" not in result.output, "标签筛选应生效"
