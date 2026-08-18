import json
import os
import asyncio
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.table import Table
from rich.console import Console

from .catalog import Catalog
from .downloader import DownloadManager
from .config import load_config, ensure_config

app = typer.Typer()
console = Console()

DEFAULT_CATALOG = "catalog.json"

@app.command()
def catalog_init(catalog: str = DEFAULT_CATALOG):
    """Create an empty catalog file."""
    c = Catalog(Path(catalog))
    c.init_catalog()
    console.print(f"Catalog initialized at {catalog}")

@app.command()
def catalog_add(catalog: str = DEFAULT_CATALOG, title: str = typer.Option(...), url: str = typer.Option(...), sha256: Optional[str] = None):
    """Add an entry to the catalog."""
    c = Catalog(Path(catalog))
    entry = c.add(title=title, url=url, sha256=sha256)
    console.print(f"Added entry id={entry['id']} title={entry['title']}")

@app.command()
def list_entries(catalog: str = DEFAULT_CATALOG):
    """List catalog entries."""
    c = Catalog(Path(catalog))
    entries = c.list()
    table = Table("ID", "Title", "URL", "SHA256")
    for e in entries:
        table.add_row(str(e["id"]), e["title"], e["url"], e.get("sha256",""))
    console.print(table)

@app.command()
def fetch(catalog: str = DEFAULT_CATALOG, id: Optional[int] = None):
    """Interactive search and download; or download by id."""
    conf = ensure_config()
    c = Catalog(Path(catalog))
    if id:
        entry = c.get(id)
        if not entry:
            console.print(f"[red]No entry with id {id}[/red]")
            raise typer.Exit(code=1)
        entries = [entry]
    else:
        entries = c.list()

        # interactive fuzzy prompt (simple)
        titles = [e["title"] for e in entries]
        completer = WordCompleter(titles, ignore_case=True)
        answer = prompt("Type game title (or leave blank to list): ", completer=completer)
        if not answer:
            console.print("Matching entries:")
            table = Table("ID", "Title", "URL")
            for e in entries:
                table.add_row(str(e["id"]), e["title"], e["url"])
            console.print(table)
            answer = prompt("Type exact title to download: ", completer=completer)
        entries = [e for e in entries if e["title"].lower() == answer.strip().lower()]
        if not entries:
            console.print("[red]No matches[/red]")
            raise typer.Exit(code=0)

    mgr = DownloadManager(conf)
    asyncio.run(mgr.download_entries(entries))
