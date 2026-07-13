import logging
from pathlib import Path

import click

from multi.errors import GitError
from multi.git_helpers import describe_head
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)


def report_branches(paths: Paths) -> bool:
    """Log the current branch of the root repo and each sub-repo.

    Read-only: works with dirty working trees, mismatched branches, and
    detached HEADs (for example in worktrees created by `multi worktree add`).
    Returns True when every repo is on its expected branch.
    """
    root_branch = describe_head(paths.root_dir)
    logger.info(f"{paths.root_dir.name} (root): {root_branch}")

    if paths.settings.is_monorepo():
        # Sub-repos are part of the root repo in monorepo mode.
        return True

    all_match = True
    for repo in load_repos(paths):
        branch = describe_head(repo.path)
        expected_branch = repo.fixed_branch or root_branch
        if branch == expected_branch:
            logger.info(f"{repo.name}: {branch}")
        else:
            all_match = False
            if repo.fixed_branch:
                expectation = f"fixed branch {expected_branch}"
            else:
                expectation = f"root branch {root_branch}"
            logger.warning(f"{repo.name}: {branch} (expected {expectation})")
    return all_match


@click.command(name="branch")
def branch_cmd() -> None:
    """Show the current branch of the root repo and every sub-repo.

    Read-only: unlike `multi set-branch` and `multi git`, this works with
    dirty working trees, mismatched branches, and detached HEADs.
    Exits with an error status when repos are not on their expected branches.
    """
    paths = Paths(Path.cwd())
    if not report_branches(paths):
        raise GitError(
            "Repositories are not all on their expected branches. "
            "Use `multi set-branch` (with clean working trees) to fix."
        )
