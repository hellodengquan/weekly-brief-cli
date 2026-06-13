from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .store import init_store, add_entry, load_entries, delete_entry, DEFAULT_DATA_DIR
from .grouper import auto_group_by_tag, create_manual_group, list_groups, remove_group, merge_auto_and_manual
from .renderer import render_markdown, export_markdown

app = typer.Typer(help="周报素材整理器：收集、分组、输出 Markdown")
console = Console()


def _resolve_dir(data_dir: Optional[str]) -> Path:
    return Path(data_dir) if data_dir else DEFAULT_DATA_DIR


@app.command()
def init(
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = init_store(_resolve_dir(data_dir))
    console.print(f"[green]✓[/green] 存储已初始化：{d}")


@app.command()
def add(
    content: str = typer.Argument(..., help="素材内容"),
    tags: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="标签（可多次指定）"),
    source: str = typer.Option("", "--source", "-s", help="来源"),
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = _resolve_dir(data_dir)
    init_store(d)
    entry = add_entry(content=content, tags=tags or [], source=source, data_dir=d)
    console.print(f"[green]✓[/green] 已添加素材 [{entry.id}]：{entry.content}")


@app.command(name="list")
def list_entries(
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="按标签筛选"),
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = _resolve_dir(data_dir)
    entries = load_entries(d)
    if tag:
        entries = [e for e in entries if tag in e.tags]

    if not entries:
        console.print("[yellow]暂无素材[/yellow]")
        return

    table = Table(title="素材列表")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("内容")
    table.add_column("标签", style="magenta")
    table.add_column("来源", style="dim")
    table.add_column("时间", style="dim")

    for e in entries:
        table.add_row(e.id, e.content, ", ".join(e.tags), e.source, e.created_at)

    console.print(table)


@app.command()
def rm(
    entry_id: str = typer.Argument(..., help="素材 ID"),
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = _resolve_dir(data_dir)
    if delete_entry(entry_id, d):
        console.print(f"[green]✓[/green] 已删除素材 [{entry_id}]")
    else:
        console.print(f"[red]✗[/red] 未找到素材 [{entry_id}]")


@app.command(name="group")
def group_cmd(
    action: str = typer.Argument("auto", help="操作：auto=按标签自动分组 / manual=手动建组 / list=查看分组 / rm=删除分组"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="分组名称（manual 时必填）"),
    entry_ids: Optional[list[str]] = typer.Option(None, "--entry", "-e", help="素材 ID（manual 时指定，可多次）"),
    group_id: Optional[str] = typer.Option(None, "--group-id", "-g", help="分组 ID（rm 时必填）"),
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = _resolve_dir(data_dir)
    init_store(d)

    if action == "auto":
        groups = auto_group_by_tag(d)
        if not groups:
            console.print("[yellow]暂无素材可分组[/yellow]")
            return
        for g in groups:
            console.print(f"[bold]{g.name}[/bold] ({len(g.entries)} 条)")
            for e in g.entries:
                console.print(f"  [{e.id}] {e.content}")

    elif action == "manual":
        if not name:
            console.print("[red]✗[/red] 手动分组需要 --name 参数")
            raise typer.Exit(code=1)
        if not entry_ids:
            console.print("[red]✗[/red] 手动分组需要至少一个 --entry 参数")
            raise typer.Exit(code=1)
        group = create_manual_group(name=name, entry_ids=entry_ids, data_dir=d)
        console.print(f"[green]✓[/green] 已创建分组 [{group.id}]「{group.name}」，包含 {len(group.entries)} 条素材")

    elif action == "list":
        groups = list_groups(d)
        if not groups:
            console.print("[yellow]暂无手动分组[/yellow]")
            return
        for g in groups:
            console.print(f"[bold]{g.name}[/bold] (id={g.id}, {len(g.entries)} 条)")

    elif action == "rm":
        if not group_id:
            console.print("[red]✗[/red] 删除分组需要 --group-id 参数")
            raise typer.Exit(code=1)
        if remove_group(group_id, d):
            console.print(f"[green]✓[/green] 已删除分组 [{group_id}]")
        else:
            console.print(f"[red]✗[/red] 未找到分组 [{group_id}]")

    else:
        console.print(f"[red]✗[/red] 未知操作：{action}（可选：auto / manual / list / rm）")


@app.command()
def export(
    output: Path = typer.Argument("weekly-brief.md", help="输出文件路径"),
    title: Optional[str] = typer.Option(None, "--title", help="周报标题"),
    date_range: Optional[str] = typer.Option(None, "--date-range", help="时间范围描述"),
    mode: str = typer.Option("auto", "--mode", "-m", help="auto=按标签自动分组 / manual=仅手动分组 / all=合并两者"),
    data_dir: Optional[str] = typer.Option(None, "--dir", help="数据存储目录"),
):
    d = _resolve_dir(data_dir)
    init_store(d)

    if mode == "auto":
        groups = auto_group_by_tag(d)
    elif mode == "manual":
        groups = list_groups(d)
    elif mode == "all":
        groups = merge_auto_and_manual(d)
    else:
        console.print(f"[red]✗[/red] 未知模式：{mode}（可选：auto / manual / all）")
        raise typer.Exit(code=1)

    if not groups:
        console.print("[yellow]暂无分组可导出[/yellow]")
        return

    path = export_markdown(groups, output=output, title=title, date_range=date_range)
    console.print(f"[green]✓[/green] 周报已导出：{path}")
