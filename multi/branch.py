import logging
from pathlib import Path

import click

from multi.errors import GitError
from multi.git_helpers import (
    describe_head,
    expected_branch_description,
    expected_branch_for_repo,
)
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)


def report_branches(paths: Paths) -> bool:
    """Log the current branch of the root repo and each sub-repo.

    Read-only: works with dirty working trees, mismatched branches, detached
    HEADs (for example in worktrees created by `multi worktree add`), and
    sub-repos that have not been synced yet (reported as missing).
    Returns True when every repo is present and on its expected branch.
    """
    root_branch = describe_head(paths.root_dir)
    logger.info(f"{paths.root_dir.name} (root): {root_branch}")

    if paths.settings.is_monorepo():
        # Sub-repos are part of the root repo in monorepo mode.
        return True

    all_match = True
    for repo in load_repos(paths):
        try:
            branch = describe_head(repo.path)
        except GitError:
            # Missing or uninitialized sub-repo: report it and keep going so
            # the rest of the workspace is still listed.
            all_match = False
            logger.warning(f"{repo.name}: (missing — run `multi sync`)")
            continue
        expected_branch = expected_branch_for_repo(repo, root_branch)
        if branch == expected_branch:
            logger.info(f"{repo.name}: {branch}")
        else:
            all_match = False
            expectation = expected_branch_description(repo, root_branch)
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
            "Repositories are missing or not on their expected branches. "
            "Run `multi sync` to clone missing repos, or `multi set-branch` "
            "(with clean working trees) to fix branch mismatches."
        )
