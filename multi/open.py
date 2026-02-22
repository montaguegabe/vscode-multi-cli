from pathlib import Path
from urllib.parse import quote

import click


@click.command("open")
@click.argument("path", type=click.Path(exists=True))
def open_cmd(path: str):
    """Open a project in the Multi desktop app."""
    abs_path = str(Path(path).resolve())
    click.launch(f"multi://open?path={quote(abs_path, safe='')}")
