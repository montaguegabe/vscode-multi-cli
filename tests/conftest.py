import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Generator, List

import pytest

from cursor_multi.sync import sync

# Define a consistent temporary directory path
_TEMP_ROOT = Path("/tmp/cursor-multi-test")
_TEMP_PROJECT_ROOT = _TEMP_ROOT / "root"
_TEMP_REMOTES_ROOT = _TEMP_ROOT / "remotes"

# Set the environment variable to our consistent temp directory
os.environ["CURSOR_MULTI_ROOT_DIR"] = str(_TEMP_PROJECT_ROOT)

# Now we can safely import from cursor_multi
from cursor_multi.git_helpers import run_git  # noqa: E402


@pytest.fixture
def setup_git_repos() -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository and sub-repositories for testing.
    Returns a tuple of (root_repo_path, [sub_repo_dirs]).
    """
    # Clean up and recreate the temporary directory at the start of each test
    if _TEMP_ROOT.exists():
        shutil.rmtree(_TEMP_ROOT, ignore_errors=False)
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    _TEMP_PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

    # Create multi.json in the root
    multi_json = {
        "repos": [
            {"url": "https://github.com/test/repo0"},
            {"url": "https://github.com/test/repo1"},
        ]
    }
    multi_json_path = _TEMP_PROJECT_ROOT / "multi.json"
    multi_json_path.write_text(json.dumps(multi_json, indent=2))

    run_git(["init"], "initialize root repository", _TEMP_PROJECT_ROOT)

    # Create a file and commit it to create an initial branch
    readme = _TEMP_PROJECT_ROOT / "README.md"
    readme.write_text("# Root Repository")
    run_git(["add", "README.md", "multi.json"], "stage files", _TEMP_PROJECT_ROOT)
    run_git(
        ["commit", "-m", "Initial commit"], "create initial commit", _TEMP_PROJECT_ROOT
    )

    # Create and initialize sub-repos
    sub_repo_dirs = []
    for i in range(2):  # Create 2 sub-repos
        sub_repo_dir = _TEMP_PROJECT_ROOT / f"repo{i}"
        sub_repo_dir.mkdir()
        run_git(["init"], f"initialize sub-repo {i}", sub_repo_dir)

        # Create a file and commit it
        readme = sub_repo_dir / "README.md"
        readme.write_text(f"# Sub Repository {i}")
        run_git(["add", "README.md"], "stage README", sub_repo_dir)
        run_git(
            ["commit", "-m", "Initial commit"], "create initial commit", sub_repo_dir
        )
        sub_repo_dirs.append(sub_repo_dir)

    # Run sync to create .gitignore and .ignore files. This will not try to pull from the dummy URLs because the directories already exist.
    sync()

    run_git(["add", "."], "stage post-sync files", _TEMP_PROJECT_ROOT)
    run_git(
        ["commit", "-m", "Post-sync commit"], "post-sync commit", _TEMP_PROJECT_ROOT
    )

    yield _TEMP_PROJECT_ROOT, sub_repo_dirs


@pytest.fixture
def setup_git_repos_with_remotes(
    setup_git_repos,
) -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository and sub-repositories for testing, each with their own remote.
    The remotes are bare repositories stored in a separate directory.
    Returns a tuple of (root_repo_path, [sub_repo_dirs]).
    """
    # Get the repos from the parent fixture
    root_repo, sub_repos = setup_git_repos

    # Clean up and recreate the remotes directory
    if _TEMP_REMOTES_ROOT.exists():
        shutil.rmtree(_TEMP_REMOTES_ROOT, ignore_errors=False)
    _TEMP_REMOTES_ROOT.mkdir(parents=True, exist_ok=True)

    # Create and configure remote for root repo
    root_remote_dir = _TEMP_REMOTES_ROOT / "root.git"
    run_git(
        ["init", "--bare", str(root_remote_dir)], "create root bare repo", root_repo
    )
    run_git(
        ["remote", "add", "origin", str(root_remote_dir)],
        "add remote to root repo",
        root_repo,
    )
    run_git(["push", "-u", "origin", "main"], "push root repo", root_repo)

    # Create and configure remotes for sub-repos
    for i, sub_repo in enumerate(sub_repos):
        sub_remote_dir = _TEMP_REMOTES_ROOT / f"repo{i}.git"
        run_git(
            ["init", "--bare", str(sub_remote_dir)],
            f"create sub-repo {i} bare repo",
            sub_repo,
        )
        run_git(
            ["remote", "add", "origin", str(sub_remote_dir)],
            f"add remote to sub-repo {i}",
            sub_repo,
        )
        run_git(["push", "-u", "origin", "main"], f"push sub-repo {i}", sub_repo)

    yield root_repo, sub_repos


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up the temporary directory after all tests are done."""
    # Open temp directories in Finder on Mac if tests failed
    if sys.platform == "darwin" and exitstatus != 0:
        subprocess.run(["open", str(_TEMP_ROOT)])
