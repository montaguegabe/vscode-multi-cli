import argparse
import logging
import sys
from pathlib import Path

from cursor_multi.errors import MergeBranchError
from cursor_multi.git_helpers import check_branch_existence, run_git
from cursor_multi.repos import load_repos

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
        f"Successfully merged '{source_branch}' into '{target_branch}' in {repo_path}"
    )


def merge_branches_in_all_repos(source_branch: str, target_branch: str) -> None:
    """
    Merge source branch into target branch across all repositories.
    Raises MergeBranchError if any operation fails.
    """
    root = get_root()

    # First merge in root repo
    merge_branch(root, source_branch, target_branch)

    # Load repos
    repos = load_repos()

    # Merge sub-repositories
    for repo in repos:
        merge_branch(repo.path, source_branch, target_branch)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge source branch into target branch across all repositories"
    )
    parser.add_argument("source_branch", help="Name of the source branch to merge from")
    parser.add_argument("target_branch", help="Name of the target branch to merge into")
    args = parser.parse_args()

    if not args.source_branch or not args.target_branch:
        logger.error("Both source and target branch names are required")
        sys.exit(1)

    merge_branches_in_all_repos(args.source_branch, args.target_branch)


if __name__ == "__main__":
    main()
