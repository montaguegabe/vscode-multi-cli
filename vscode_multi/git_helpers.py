import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

from vscode_multi.errors import GitError, RepoNotCleanError
from vscode_multi.paths import paths

logger = logging.getLogger(__name__)


def is_git_repo_root(repo_path: Path) -> bool:
    # Will fail for submodules and worktrees, but these aren't used by us
    return (repo_path / ".git").is_dir()


def run_git(
    args: List[str],
    action_description: str,
    repo_path: Path,
    check: bool = True,
) -> str:
    """Run a git command and handle errors."""
    cmd = ["git"] + args
    try:
        return subprocess.run(
            cmd,
            cwd=repo_path,
            check=check,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to {action_description}")
        raise GitError(f"Failed to {action_description}") from e


def get_current_branch(repo_path: Path) -> str:
    """Get the current branch name of a git repository."""
    return run_git(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        "determine current branch",
        repo_path,
    )


def check_all_on_same_branch(raise_error: bool = True) -> bool:
    """Validate that all repositories are on the same branch."""
    from vscode_multi.repos import load_repos

    root_branch = get_current_branch(paths.root_dir)
    repo_branches = [(repo, get_current_branch(repo.path)) for repo in load_repos()]
    for repo, branch in repo_branches:
        if branch != root_branch:
            if raise_error:
                raise GitError(
                    f"Repository {repo.name} is not on the same branch as the root repository.  Please fix.  {repo.name}: {branch}, Root: {root_branch}"
                )
            return False
    return True


def check_repo_is_clean(repo_path: Path, raise_error: bool = True) -> bool:
    # Check if this is a git repository
    if not is_git_repo_root(repo_path):
        raise GitError(
            f"{repo_path} is not a git repository or has not been initialized properly (no .git folder)"
        )

    # Make sure we have a clean working directory
    status = run_git(
        ["status", "--porcelain"], "check working directory status", repo_path
    )
    if status:
        if raise_error:
            raise RepoNotCleanError(
                f"Working directory is not clean in {repo_path}. Please commit or stash changes first."
            )
        return False
    return True


def check_all_repos_are_clean(raise_error: bool = True) -> bool:
    """Check if all repositories are clean."""
    from vscode_multi.repos import load_repos

    # Check root repo
    if not check_repo_is_clean(paths.root_dir, raise_error):
        return False

    # Check sub-repos
    return all(check_repo_is_clean(repo.path, raise_error) for repo in load_repos())


def check_branch_existence(repo_path: Path, branch_name: str) -> Tuple[bool, bool]:
    # Check if branch exists locally
    result = run_git(
        ["branch", "--list", branch_name],
        "check if branch exists",
        repo_path,
    )
    exists_locally = bool(result)

    # Check if branch exists remotely
    try:
        result = run_git(
            ["ls-remote", "--heads", "origin", branch_name],
            "check if branch exists remotely",
            repo_path,
        )
        exists_remotely = bool(result)
    except Exception:
        logger.debug(
            f"Could not check remote branches in {repo_path}, assuming branch doesn't exist remotely"
        )
        exists_remotely = False

    return exists_locally, exists_remotely
