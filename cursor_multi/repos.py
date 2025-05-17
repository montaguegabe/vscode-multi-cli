import json
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Union

from cursor_multi.errors import GitError, NoRepositoriesError
from cursor_multi.paths import get_root


@dataclass
class Repository:
    """Represents a repository in the workspace.

    Attributes:
        url: The repository URL
        name: Repository name derived from the URL
        path: Local filesystem path where the repository is/will be cloned
        options: Dictionary of repository-specific settings (defaults to empty dict)
    """

    url: str
    options: dict | None = None

    def __post_init__(self):
        """Derive name and path from URL after initialization."""
        self.name = self.url.split("/")[-1]
        self.path = get_root() / self.name
        if self.options is None:
            self.options = {}


def run_git(
    args: List[str],
    action_description: str,
    repo_path: Union[Path, None] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a git command and handle errors."""
    cmd = ["git"] + args
    try:
        if repo_path:
            return subprocess.run(
                cmd,
                cwd=repo_path,
                check=check,
                capture_output=True,
                text=True,
            )
        return subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to {action_description}")
        print(f"Error: {e.stderr}")
        raise GitError(f"Failed to {action_description}") from e


def validate_repo_is_clean(repo_path: Path) -> bool:
    """Validate that the path is a git repository and has a clean working directory.

    Args:
        repo_path: Path to the repository

    Returns:
        bool: True if repository is valid and clean, False otherwise
    """
    # Check if this is a git repository
    try:
        run_git(["rev-parse", "--git-dir"], "check if git repo", repo_path)
    except Exception:
        print(f"\n❌ {repo_path} is not a git repository or has not been initialized")
        return False

    # Get current branch to ensure we're in a valid state
    try:
        run_git(["rev-parse", "--abbrev-ref", "HEAD"], "get current branch", repo_path)
    except Exception:
        print(f"\n❌ Could not determine current branch in {repo_path}")
        return False

    # Make sure we have a clean working directory
    status = run_git(
        ["status", "--porcelain"], "check working directory status", repo_path
    )
    if status.stdout.strip():
        print(
            f"\n❌ Working directory is not clean in {repo_path}. Please commit or stash changes first."
        )
        return False
    return True


def check_branch_existence(repo_path: Path, branch_name: str) -> Tuple[bool, bool]:
    """Check if a branch exists locally and/or remotely.

    Args:
        repo_path: Path to the repository
        branch_name: Name of the branch to check

    Returns:
        Tuple[bool, bool]: (exists_locally, exists_remotely)
    """
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
        print(
            f"Could not check remote branches in {repo_path}, assuming branch doesn't exist remotely"
        )
        exists_remotely = False

    return exists_locally, exists_remotely


@lru_cache(maxsize=1)
def load_repos() -> List[Repository]:
    """Load repository information from repos.json.

    The repos.json file should contain a list of objects with the following structure:
    [
        {
            "url": "https://github.com/user/repo",
            "options": {
                // Repository-specific settings (optional)
            }
        },
        // More repositories...
    ]
    """
    root = get_root()
    repos_file = Path(root) / "repos.json"

    with open(repos_file) as f:
        repo_configs = json.load(f)

    result = []
    for config in repo_configs:
        if isinstance(config, dict):
            url = config.get("url")
            if not url:
                raise ValueError("Repository config must contain a 'url' field")
            result.append(Repository(url=url, options=config.get("options")))
        else:
            raise ValueError(
                "Each repository config must be an object with a 'url' field"
            )

    if not result:
        raise NoRepositoriesError("No repositories found in repos.json")

    return result
