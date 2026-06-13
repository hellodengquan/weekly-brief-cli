from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Group


def render_markdown(
    groups: list[Group],
    title: str | None = None,
    date_range: str | None = None,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if title is None:
        title = f"周报 {today}"
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    if date_range:
        lines.append(f"> 时间范围：{date_range}")
        lines.append("")

    for group in groups:
        lines.append(f"## {group.name}")
        lines.append("")
        if not group.entries:
            lines.append("（暂无内容）")
            lines.append("")
            continue
        for entry in group.entries:
            source_tag = f" `[{entry.source}]`" if entry.source else ""
            lines.append(f"- {entry.content}{source_tag}")
        lines.append("")

    return "\n".join(lines)


def export_markdown(
    groups: list[Group],
    output: Path,
    title: str | None = None,
    date_range: str | None = None,
) -> Path:
    md = render_markdown(groups, title=title, date_range=date_range)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(md, encoding="utf-8")
    return output
