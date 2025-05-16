"""Shared utilities for scripts."""

import json
import os
import subprocess
import sys
from typing import List, Sequence


def run_git(
    args: Sequence[str],
    description: str,
    repo_path: str | None = None,
) -> subprocess.CompletedProcess:
    """Run a git command with consistent error handling.

    Args:
        args: The git command arguments (e.g. ["checkout", "main"])
        description: Description of the operation for error messages
        repo_path: Optional path to run git command in, uses current directory if None

    Returns:
        CompletedProcess instance if successful

    Exits:
        Prints error and exits with status 1 if command fails
    """
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        repo_name = os.path.basename(repo_path) if repo_path else "current repository"
        print(f"\n❌ Failed to {description} in {repo_name}")
        print(f"Git output:\n{e.stderr}")
        sys.exit(1)


def get_git_root() -> str:
    """Get the root directory of the git repository.

    Returns:
        The absolute path to the git repository root.

    Raises:
        subprocess.CalledProcessError: If git command fails.
    """
    result = run_git(
        ["rev-parse", "--show-toplevel"],
        "get repository root",
    )
    return result.stdout.strip()


def load_repos(names_only: bool = False) -> List[str]:
    """Load repository URLs from repos.json.

    Args:
        names_only: If True, returns only the repository names instead of URLs.

    Returns:
        List of repository URLs or names depending on names_only parameter.
    """
    git_root = get_git_root()
    repos_file = os.path.join(git_root, "repos.json")

    with open(repos_file, "r") as f:
        urls = json.load(f)

    if names_only:
        return [url.split("/")[-1] for url in urls]
    return urls


def get_app_packages(repo_names: List[str]) -> List[str]:
    """Get list of repositories that have web.app_packages entry points.

    Args:
        repo_names: List of repository names to check

    Returns:
        List of repository names that have web.app_packages entry points
    """
    git_root = get_git_root()
    app_packages = []

    for repo in repo_names:
        pyproject_path = os.path.join(git_root, repo, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            continue

        with open(pyproject_path, "r") as f:
            content = f.read()
            if '[project.entry-points."web.app_packages"]' in content:
                app_packages.append(repo)

    return app_packages
