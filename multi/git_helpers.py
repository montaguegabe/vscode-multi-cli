import logging
from pathlib import Path
from typing import Tuple

import git
from git.exc import InvalidGitRepositoryError

from multi.errors import GitError, RepoNotCleanError
from multi.paths import Paths

logger = logging.getLogger(__name__)


def is_git_repo_root(repo_path: Path) -> bool:
    # Will fail for submodules and worktrees, but these aren't used by us
    return (repo_path / ".git").is_dir()


def get_current_branch(repo_path: Path) -> str:
    """Get the current branch name of a git repository."""
    try:
        repo = git.Repo(repo_path)
        return repo.active_branch.name
    except InvalidGitRepositoryError as e:
        logger.error("Failed to determine current branch")
        raise GitError("Failed to determine current branch") from e
    except TypeError:
        # Detached HEAD state - active_branch raises TypeError
        return "HEAD"


def check_all_on_same_branch(paths: Paths, raise_error: bool = True) -> bool:
    """Validate that all repositories are on the same branch."""
    from multi.repos import load_repos

    root_branch = get_current_branch(paths.root_dir)
    repo_branches = [
        (repo, get_current_branch(repo.path)) for repo in load_repos(paths)
    ]
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
    try:
        repo = git.Repo(repo_path)
        # is_dirty checks for modified/staged files, untracked_files checks for new files
        is_clean = not repo.is_dirty(untracked_files=True)
    except InvalidGitRepositoryError as e:
        logger.error("Failed to check working directory status")
        raise GitError("Failed to check working directory status") from e

    if not is_clean:
        if raise_error:
            raise RepoNotCleanError(
                f"Working directory is not clean in {repo_path}. Please commit or stash changes first."
            )
        return False
    return True


def check_all_repos_are_clean(paths: Paths, raise_error: bool = True) -> bool:
    """Check if all repositories are clean."""
    from multi.repos import load_repos

    # Check root repo
    if not check_repo_is_clean(paths.root_dir, raise_error):
        return False

    # Check sub-repos
    return all(
        check_repo_is_clean(repo.path, raise_error) for repo in load_repos(paths)
    )


def check_branch_existence(repo_path: Path, branch_name: str) -> Tuple[bool, bool]:
    try:
        repo = git.Repo(repo_path)
    except InvalidGitRepositoryError as e:
        logger.error("Failed to check if branch exists")
        raise GitError("Failed to check if branch exists") from e

    # Check if branch exists locally
    exists_locally = branch_name in [head.name for head in repo.heads]

    # Check if branch exists remotely
    try:
        remote_refs = [ref.name for ref in repo.remotes.origin.refs]
        exists_remotely = f"origin/{branch_name}" in remote_refs
    except Exception:
        logger.debug(
            f"Could not check remote branches in {repo_path}, assuming branch doesn't exist remotely"
        )
        exists_remotely = False

    return exists_locally, exists_remotely
