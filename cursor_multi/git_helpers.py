import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

from cursor_multi.errors import GitError

logger = logging.getLogger(__name__)


def run_git(
    args: List[str],
    action_description: str,
    repo_path: Path,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a git command and handle errors."""
    cmd = ["git"] + args
    try:
        return subprocess.run(
            cmd,
            cwd=repo_path,
            check=check,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to {action_description}")
        raise GitError(f"Failed to {action_description}") from e


def check_is_git_repo_root(repo_path: Path) -> bool:
    # Will fail for submodules and worktrees, but these aren't used by us
    return (repo_path / ".git").is_dir()


def validate_repo_is_clean(repo_path: Path) -> bool:
    # Check if this is a git repository
    if not check_is_git_repo_root(repo_path):
        logger.error(
            f"{repo_path} is not a git repository or has not been initialized properly (no .git folder)"
        )
        return False

    # Make sure we have a clean working directory
    status = run_git(
        ["status", "--porcelain"], "check working directory status", repo_path
    )
    if status.stdout.strip():
        logger.error(
            f"Working directory is not clean in {repo_path}. Please commit or stash changes first."
        )
        return False
    return True


def check_branch_existence(repo_path: Path, branch_name: str) -> Tuple[bool, bool]:
    # Check if branch exists locally
    result = run_git(
        ["branch", "--list", branch_name],
        "check if branch exists",
        repo_path,
    )
    exists_locally = bool(result.stdout.strip())

    # Check if branch exists remotely
    try:
        result = run_git(
            ["ls-remote", "--heads", "origin", branch_name],
            "check if branch exists remotely",
            repo_path,
        )
        exists_remotely = bool(result.stdout.strip())
    except Exception:
        logger.warning(
            f"Could not check remote branches in {repo_path}, assuming branch doesn't exist remotely"
        )
        exists_remotely = False

    return exists_locally, exists_remotely
