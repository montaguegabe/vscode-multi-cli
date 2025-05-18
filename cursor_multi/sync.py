#!/usr/bin/env python3

import logging

import click

from cursor_multi.git_helpers import (
    check_all_on_same_branch,
    get_current_branch,
    run_git,
)
from cursor_multi.ignore_files import (
    update_gitignore_with_repos,
    update_ignore_with_repos,
)
from cursor_multi.merge_cursor import import_cursor_rules, merge_rules_cmd
from cursor_multi.merge_vscode import merge_vscode_configs, vscode_cmd
from cursor_multi.paths import paths
from cursor_multi.repos import load_repos

logger = logging.getLogger(__name__)


def clone_repos():
    """Clone all repositories from the repos.json file."""
    repos = load_repos()

    # Get the current branch of the parent repo
    current_branch = get_current_branch(paths.root_dir)
    logger.info(f"📌 Current branch: {current_branch}")

    for repo in repos:
        if repo.path.exists():
            logger.info(f"📁 {repo.name} already exists, skipping...")
            continue

        logger.info(f"\n🔄 Cloning {repo.name}...")

        # First clone the default branch
        run_git(
            ["clone", repo.url, str(repo.path)],
            f"clone {repo.name}",
            paths.root_dir,
        )

        # Then checkout the same branch as parent repo if it exists
        try:
            run_git(
                ["checkout", current_branch],
                f"checkout branch {current_branch}",
                repo.path,
            )
            logger.info(
                f"✅ Successfully cloned {repo.name} and checked out branch {current_branch}"
            )
        except SystemExit:
            logger.warning(
                f"Branch {current_branch} not found in {repo.name}, staying on default branch"
            )

    update_gitignore_with_repos()
    update_ignore_with_repos()

    if not check_all_on_same_branch():
        logger.warning("Repos are not on the same branch! Please fix.")


def sync_all():
    """Run all sync operations."""
    logger.info("🚀 Syncing development environment...")

    clone_repos()
    import_cursor_rules()
    merge_vscode_configs()

    logger.info("\n✨ Sync complete!")


@click.group(name="sync", invoke_without_command=True)
@click.pass_context
def sync_cmd(ctx: click.Context):
    """Sync development environment and configurations.

    If no subcommand is given, performs complete sync:
    1. Clones/updates all repositories
    2. Imports Cursor rules
    3. Merges VSCode configurations
    """
    if ctx.invoked_subcommand is None:
        sync_all()


# Add subcommands
sync_cmd.add_command(vscode_cmd)
sync_cmd.add_command(merge_rules_cmd, name="rules")
