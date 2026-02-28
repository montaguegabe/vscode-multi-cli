import json
import logging
import shutil
from pathlib import Path

import click

from multi.ignore_files import (
    remove_gitignore_entries_for_repos,
    remove_ignore_entries_for_repos,
)
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)


def _remove_nested_git_dirs(paths: Paths) -> None:
    repos = load_repos(paths=paths)
    for repo in repos:
        git_path = repo.path / ".git"
        if git_path.is_dir():
            shutil.rmtree(git_path)
            logger.info(f"✅ Removed nested git directory: {repo.name}/.git")
        elif git_path.exists() or git_path.is_symlink():
            git_path.unlink()
            logger.info(f"✅ Removed nested git file: {repo.name}/.git")
        else:
            logger.warning(f"No nested .git found for {repo.name}; skipping")


def _set_monorepo_flag(paths: Paths) -> None:
    with paths.multi_json_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    if not isinstance(config, dict):
        raise ValueError("multi.json must contain a top-level object.")

    config["monoRepo"] = True
    with paths.multi_json_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def convert_to_monorepo(root_dir: Path) -> None:
    paths = Paths(root_dir)
    repos = load_repos(paths=paths)
    repo_names = [repo.name for repo in repos]

    _remove_nested_git_dirs(paths=paths)
    _set_monorepo_flag(paths=paths)
    remove_gitignore_entries_for_repos(paths=paths, repo_names=repo_names)
    remove_ignore_entries_for_repos(paths=paths, repo_names=repo_names)
    logger.info("✅ Converted workspace to monorepo mode")


@click.command(name="convert-monorepo")
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm conversion to monorepo mode (required).",
)
def convert_monorepo_cmd(confirm: bool) -> None:
    """Convert a standard multi workspace to monorepo mode."""
    if not confirm:
        raise click.UsageError(
            "This command is destructive and requires --confirm. "
            "It will delete nested .git directories in configured repos."
        )

    paths = Paths(Path.cwd())
    if paths.settings.is_monorepo():
        raise click.UsageError("Workspace is already in monorepo mode.")

    convert_to_monorepo(root_dir=Path.cwd())
