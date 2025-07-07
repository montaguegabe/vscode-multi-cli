import logging
from pathlib import Path
from typing import List

import click

from vscode_multi.git_helpers import check_all_on_same_branch, run_git
from vscode_multi.paths import paths
from vscode_multi.repos import load_repos

logger = logging.getLogger(__name__)


def run_git_command(repo_path: Path, git_args: List[str]) -> None:
    """Run a git command in the specified repository."""
    command_str = " ".join(git_args)
    logger.info(f"Running 'git {command_str}' in {repo_path}")

    output = run_git(git_args, f"run git {command_str}", repo_path, check=False)
    if output:
        logger.info(f"Output from {repo_path}:\n{output}")


def run_git_in_all_repos(git_args: List[str]) -> None:
    """Run git command across all repositories."""
    # First check if all repos are on the same branch
    check_all_on_same_branch(raise_error=True)

    # Run in root repo first
    run_git_command(paths.root_dir, git_args)

    # Then run in all sub-repos
    for repo in load_repos():
        run_git_command(repo.path, git_args)


@click.command(name="git")
@click.argument("git_args", nargs=-1, required=True)
def git_cmd(git_args: tuple[str, ...]) -> None:
    """Run a git command across all repositories.

    GIT_ARGS: The git command and arguments to run (e.g. 'pull' or 'checkout main')

    Example: multi git pull
             multi git checkout -b feature/new-branch
    """
    run_git_in_all_repos(list(git_args))
