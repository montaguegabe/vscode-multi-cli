from pathlib import Path

from multi.sync import sync


def sync_workspace(
    root_dir: str | Path,
    *,
    install_set: str | None = None,
    ensure_on_same_branch: bool = True,
) -> None:
    """Sync a Multi workspace from Python code."""
    sync(
        root_dir=Path(root_dir),
        ensure_on_same_branch=ensure_on_same_branch,
        install_set=install_set,
    )
