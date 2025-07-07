import logging
import sys
from pathlib import Path

import click

from vscode_multi.errors import MergeBranchError
from vscode_multi.git_helpers import (
    check_all_on_same_branch,
    check_all_repos_are_clean,
    check_branch_existence,
    run_git,
)
from vscode_multi.paths import paths
from vscode_multi.repos import load_repos

logger = logging.getLogger(__name__)


def merge_branch(repo_path: Path, source_branch: str, target_branch: str) -> None:
    """Merge source_branch into target_branch in the specified repository."""
    # Check if both branches exist
    for branch in [source_branch, target_branch]:
        exists_locally, exists_remotely = check_branch_existence(repo_path, branch)
        if not exists_locally and not exists_remotely:
            raise MergeBranchError(
                f"Branch '{branch}' does not exist locally or remotely in {repo_path}"
            )

    # Switch to target branch
    run_git(["checkout", target_branch], "checkout target branch", repo_path)

    # Perform the merge
    run_git(["merge", source_branch], "merge branches", repo_path)
    logger.info(
        f"✅ Successfully merged '{source_branch}' into '{target_branch}' in {repo_path}"
    )


def merge_branches_in_all_repos(source_branch: str, target_branch: str) -> None:
    """
    Merge source branch into target branch across all repositories.
    Raises MergeBranchError if any operation fails.
    """
    check_all_repos_are_clean(raise_error=True)
    check_all_on_same_branch(raise_error=True)

    merge_branch(paths.root_dir, source_branch, target_branch)
    for repo in load_repos():
        merge_branch(repo.path, source_branch, target_branch)


@click.command(name="merge-branch")
@click.argument("source_branch")
@click.argument("target_branch")
def merge_branch_cmd(source_branch: str, target_branch: str) -> None:
    """Merge source branch into target branch across all repositories.

    SOURCE_BRANCH: Name of the source branch to merge from
    TARGET_BRANCH: Name of the target branch to merge into
    """
    if not source_branch or not target_branch:
        logger.error("Both source and target branch names are required")
        sys.exit(1)

    merge_branches_in_all_repos(source_branch, target_branch)
