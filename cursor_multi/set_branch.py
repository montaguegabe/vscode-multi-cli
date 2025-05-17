#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path

from cursor_multi.errors import RepoNotCleanError
from cursor_multi.git_helpers import (
    check_branch_existence,
    run_git,
    validate_repo_is_clean,
)
from cursor_multi.paths import root_dir
from cursor_multi.repos import load_repos

logger = logging.getLogger(__name__)


def create_and_switch_branch(repo_path: Path, branch_name: str) -> bool:
    """Create a branch if it doesn't exist and switch to it."""
    if not validate_repo_is_clean(repo_path):
        raise RepoNotCleanError()

    # Check if branch exists locally or remotely
    exists_locally, exists_remotely = check_branch_existence(repo_path, branch_name)

    if exists_locally or exists_remotely:
        logger.info(f"Branch '{branch_name}' already exists in {repo_path}")
        run_git(["checkout", branch_name], "checkout existing branch", repo_path)
    else:
        # Create a new branch from current HEAD
        run_git(
            ["checkout", "-b", branch_name],
            "create and checkout new branch",
            repo_path,
        )
    logger.info(f"✅ Switched to branch '{branch_name}' in {repo_path}")


def set_branch_in_all_repos(branch_name: str) -> None:
    # First create/switch branch in root repo
    logger.info("\n🔄 Processing root repository...")
    create_and_switch_branch(root_dir, branch_name)

    # Load repo names
    repos = load_repos()

    logger.info("\n🔄 Processing sub-repositories...")
    for repo in repos:
        create_and_switch_branch(repo.path, branch_name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create and switch to a branch in all repositories"
    )
    parser.add_argument(
        "branch_name", help="Name of the branch to create and switch to"
    )
    args = parser.parse_args()

    set_branch_in_all_repos(args.branch_name)


if __name__ == "__main__":
    main()
