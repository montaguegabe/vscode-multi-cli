import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Generator, List

import pytest

from cursor_multi.sync import sync

# Define a consistent temporary directory path structure
_TEMP_ROOT = Path("/tmp/cursor-multi-test")
_TEMP_PROJECT_ROOT = _TEMP_ROOT / "root"
_TEMP_REMOTES_ROOT = _TEMP_ROOT / "remotes"
_TEMP_PROJECT_ROOT_INITIAL = _TEMP_ROOT / "root_initial"
_TEMP_REMOTES_ROOT_INITIAL = _TEMP_ROOT / "remotes_initial"

# Set the environment variable to our consistent temp project root directory
# This is needed for sync() to correctly determine the project root.
os.environ["CURSOR_MULTI_ROOT_DIR"] = str(_TEMP_PROJECT_ROOT)

# Now we can safely import from cursor_multi
from cursor_multi.git_helpers import run_git  # noqa: E402


@pytest.fixture
def setup_git_repos() -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository, sub-repositories, and their remotes.
    Uses a caching mechanism to speed up setup after the first run.
    Returns a tuple of (root_repo_path, [sub_repo_dirs]).
    """
    # Ensure the main temporary root directory exists for cache dirs
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    sub_repo_names = [f"repo{i}" for i in range(2)]  # Consistent naming

    if _TEMP_PROJECT_ROOT_INITIAL.exists() and _TEMP_REMOTES_ROOT_INITIAL.exists():
        # Cache hit: Copy from initial to working directories
        if _TEMP_PROJECT_ROOT.exists():
            shutil.rmtree(_TEMP_PROJECT_ROOT)
        shutil.copytree(_TEMP_PROJECT_ROOT_INITIAL, _TEMP_PROJECT_ROOT)

        if _TEMP_REMOTES_ROOT.exists():
            shutil.rmtree(_TEMP_REMOTES_ROOT)
        shutil.copytree(_TEMP_REMOTES_ROOT_INITIAL, _TEMP_REMOTES_ROOT)

        # CURSOR_MULTI_ROOT_DIR is already set. The initial state includes post-sync.
        current_sub_repo_dirs = [_TEMP_PROJECT_ROOT / name for name in sub_repo_names]
        yield _TEMP_PROJECT_ROOT, current_sub_repo_dirs
    else:
        # Cache miss: Create everything from scratch, then populate the cache.
        # Clear the entire _TEMP_ROOT to ensure no stale _INITIAL or other files.
        if _TEMP_ROOT.exists():
            shutil.rmtree(_TEMP_ROOT)
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        _TEMP_PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        _TEMP_REMOTES_ROOT.mkdir(parents=True, exist_ok=True)

        # --- Full setup of local repositories ---
        multi_json_content = {
            "repos": [
                {"url": f"https://github.com/test/{name}"} for name in sub_repo_names
            ]
        }
        multi_json_path = _TEMP_PROJECT_ROOT / "multi.json"
        multi_json_path.write_text(json.dumps(multi_json_content, indent=2))

        run_git(["init"], "initialize root repository", _TEMP_PROJECT_ROOT)
        readme_path = _TEMP_PROJECT_ROOT / "README.md"
        readme_path.write_text("# Root Repository")
        run_git(["add", "README.md", "multi.json"], "stage files", _TEMP_PROJECT_ROOT)
        run_git(
            ["commit", "-m", "Initial commit"],
            "create initial commit",
            _TEMP_PROJECT_ROOT,
        )

        created_sub_repo_dirs = []
        for name in sub_repo_names:
            sub_repo_dir = _TEMP_PROJECT_ROOT / name
            sub_repo_dir.mkdir()
            run_git(["init"], f"initialize sub-repo {name}", sub_repo_dir)
            readme_sub_path = sub_repo_dir / "README.md"
            readme_sub_path.write_text(f"# Sub Repository {name}")
            run_git(["add", "README.md"], "stage README", sub_repo_dir)
            run_git(
                ["commit", "-m", "Initial commit"],
                f"create initial commit in {name}",
                sub_repo_dir,
            )
            created_sub_repo_dirs.append(sub_repo_dir)

        # Run sync() - uses CURSOR_MULTI_ROOT_DIR env var set earlier
        sync()
        run_git(["add", "."], "stage post-sync files", _TEMP_PROJECT_ROOT)
        run_git(
            ["commit", "-m", "Post-sync commit"], "post-sync commit", _TEMP_PROJECT_ROOT
        )

        # --- Full setup of remote repositories and linking ---
        # Remote for root repository
        root_remote_git_path_str = str(_TEMP_REMOTES_ROOT / "root.git")
        run_git(
            ["init", "--bare", root_remote_git_path_str],
            "create root bare repo",
            _TEMP_PROJECT_ROOT,
        )
        run_git(
            ["remote", "add", "origin", root_remote_git_path_str],
            "add remote to root repo",
            _TEMP_PROJECT_ROOT,
        )
        run_git(
            ["push", "-u", "origin", "main"],
            "push root repo to its remote",
            _TEMP_PROJECT_ROOT,
        )

        # Remotes for sub-repositories
        for i, sub_repo_path_obj in enumerate(created_sub_repo_dirs):
            sub_repo_actual_name = sub_repo_names[i]
            sub_remote_git_path_str = str(
                _TEMP_REMOTES_ROOT / f"{sub_repo_actual_name}.git"
            )
            run_git(
                ["init", "--bare", sub_remote_git_path_str],
                f"create bare repo for {sub_repo_actual_name}",
                sub_repo_path_obj,
            )
            run_git(
                ["remote", "add", "origin", sub_remote_git_path_str],
                f"add remote to {sub_repo_actual_name}",
                sub_repo_path_obj,
            )
            run_git(
                ["push", "-u", "origin", "main"],
                f"push {sub_repo_actual_name} to its remote",
                sub_repo_path_obj,
            )

        # Populate the cache with the newly created state
        shutil.copytree(_TEMP_PROJECT_ROOT, _TEMP_PROJECT_ROOT_INITIAL)
        shutil.copytree(_TEMP_REMOTES_ROOT, _TEMP_REMOTES_ROOT_INITIAL)

        yield _TEMP_PROJECT_ROOT, created_sub_repo_dirs


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up the temporary directory after all tests are done."""
    # Open temp directories in Finder on Mac if tests failed to aid debugging.
    # This does not delete the _TEMP_ROOT, so the cache (_INITIAL dirs) persists.
    if sys.platform == "darwin" and exitstatus != 0:
        subprocess.run(["open", str(_TEMP_ROOT)])
