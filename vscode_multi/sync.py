#!/usr/bin/env python3

import logging
from pathlib import Path

import click

from vscode_multi.cli_helpers import common_command_wrapper
from vscode_multi.git_helpers import (
    get_current_branch,
    run_git,
)
from vscode_multi.ignore_files import (
    update_gitignore_with_repos,
    update_ignore_with_repos,
)
from vscode_multi.paths import Paths
from vscode_multi.repos import load_repos
from vscode_multi.sync_claude import convert_all_cursor_rules, convert_claude_cmd
from vscode_multi.sync_ruff import sync_all_ruff_configs, sync_ruff_cmd
from vscode_multi.sync_vscode import merge_vscode_configs, vscode_cmd

logger = logging.getLogger(__name__)


def clone_repos(paths: Paths, ensure_on_same_branch: bool = True):
    """Clone all repositories from the repos.json file."""
    repos = load_repos(paths=paths)

    # Get the current branch of the parent repo
    current_branch = (
        get_current_branch(paths.root_dir) if ensure_on_same_branch else None
    )
    if ensure_on_same_branch:
        logger.info(f"Current branch: {current_branch}")

    for repo in repos:
        if repo.path.exists():
            logger.debug(f"{repo.name} already exists, skipping...")
            continue

        logger.debug(f"Cloning {repo.name}...")

        # First clone the default branch
        run_git(
            ["clone", repo.url, str(repo.path)],
            f"clone {repo.name}",
            paths.root_dir,
        )

        # Then checkout the same branch as parent repo if it exists
        if current_branch:
            try:
                run_git(
                    ["checkout", current_branch],
                    f"checkout branch {current_branch}",
                    repo.path,
                )
                logger.info(
                    f"✅ Cloned {repo.name} and checked out branch {current_branch}"
                )
            except SystemExit:
                logger.warning(
                    f"Branch {current_branch} not found in {repo.name}, staying on default branch."
                )

    update_gitignore_with_repos(paths=paths)
    update_ignore_with_repos(paths=paths)


def sync(root_dir: Path, ensure_on_same_branch: bool = True):
    """Run all sync operations."""
    logger.info("Syncing...")

    paths = Paths(root_dir)
    clone_repos(paths=paths, ensure_on_same_branch=ensure_on_same_branch)
    merge_vscode_configs(root_dir=root_dir)
    convert_all_cursor_rules(root_dir=root_dir)
    sync_all_ruff_configs(root_dir=root_dir)

    logger.info("✅ Sync complete")


@click.group(name="sync", invoke_without_command=True)
@click.pass_context
def sync_cmd(ctx: click.Context):
    """Sync development environment and configurations.

    If no subcommand is given, performs complete sync:
    1. Clones/updates all repositories
    2. Merges VSCode configurations
    """
    if ctx.invoked_subcommand is None:
        sync(root_dir=Path.cwd())


# Add subcommands
sync_cmd.add_command(common_command_wrapper(vscode_cmd))
sync_cmd.add_command(common_command_wrapper(convert_claude_cmd))
sync_cmd.add_command(common_command_wrapper(sync_ruff_cmd))
