#!/usr/bin/env python3

import logging
from pathlib import Path

import click

from vscode_multi.errors import GitError
from vscode_multi.git_helpers import (
    check_all_on_same_branch,
    check_all_repos_are_clean,
    check_branch_existence,
    run_git,
)
from vscode_multi.paths import paths
from vscode_multi.repos import load_repos

logger = logging.getLogger(__name__)


def create_and_switch_branch(
    repo_path: Path, branch_name: str, allow_create: bool = True
) -> None:
    """Create a branch if it doesn't exist and switch to it."""

    # Check if branch exists locally or remotely
    exists_locally, exists_remotely = check_branch_existence(repo_path, branch_name)

    if exists_locally or exists_remotely:
        logger.info(f"Branch '{branch_name}' already exists in {repo_path}")
        run_git(["checkout", branch_name], "checkout existing branch", repo_path)
    else:
        if not allow_create:
            raise GitError(
                f"Branch '{branch_name}' does not exist in {repo_path}.  Normally we would create a new branch, but you started with different repos checked out to different branches, so there is no base branch to create from."
            )
        # Create a new branch from current HEAD
        run_git(
            ["checkout", "-b", branch_name],
            "create and checkout new branch",
            repo_path,
        )
    logger.info(f"✅ Switched to branch '{branch_name}' in {repo_path}")


def set_branch_in_all_repos(branch_name: str) -> None:
    check_all_repos_are_clean(raise_error=True)
    all_on_same_branch = check_all_on_same_branch(raise_error=False)
    if not all_on_same_branch:
        logger.warning(
            "Some repos are not on the same branch as the root repo.  If the branch already exists for all repos, this command will fix the situation."
        )

    create_and_switch_branch(
        paths.root_dir, branch_name, allow_create=all_on_same_branch
    )
    for repo in load_repos():
        create_and_switch_branch(
            repo.path, branch_name, allow_create=all_on_same_branch
        )


@click.command(name="set-branch")
@click.argument("branch_name")
def set_branch_cmd(branch_name: str) -> None:
    """Create and switch to a branch in all repositories.

    BRANCH_NAME: Name of the branch to create and switch to
    """
    set_branch_in_all_repos(branch_name)
