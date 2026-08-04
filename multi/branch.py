import logging
from pathlib import Path

import click

from multi.cli_helpers import common_command_wrapper
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


def _check_branch_alignment() -> None:
    paths = Paths(Path.cwd())
    if not report_branches(paths):
        raise GitError(
            "Repositories are missing or not on their expected branches. "
            "Run `multi sync` to clone missing repos, or `multi set-branch` "
            "(with clean working trees) to fix branch mismatches."
        )


@click.group(name="branch", invoke_without_command=True)
@click.pass_context
def branch_cmd(ctx: click.Context) -> None:
    """Show branch state and expected-branch alignment.

    Running `multi branch` is kept as the backwards-compatible spelling for
    `multi branch check`.
    """
    if ctx.invoked_subcommand is None:
        _check_branch_alignment()


@click.command(name="check")
def branch_check_cmd() -> None:
    """Check that repos are on their expected branches."""
    _check_branch_alignment()


branch_cmd.add_command(common_command_wrapper(branch_check_cmd))
