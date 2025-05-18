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

# Set the environment variable to our consistent temp directory
os.environ["CURSOR_MULTI_ROOT_DIR"] = str(_TEMP_ROOT)

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
        shutil.rmtree(_TEMP_ROOT, ignore_errors=True)
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    # Create multi.json in the root
    multi_json = {
        "repos": [
            {"url": "https://github.com/test/repo0"},
            {"url": "https://github.com/test/repo1"},
        ]
    }
    multi_json_path = _TEMP_ROOT / "multi.json"
    multi_json_path.write_text(json.dumps(multi_json, indent=2))

    run_git(["init"], "initialize root repository", _TEMP_ROOT)

    # Create a file and commit it to create an initial branch
    readme = _TEMP_ROOT / "README.md"
    readme.write_text("# Root Repository")
    run_git(["add", "README.md", "multi.json"], "stage files", _TEMP_ROOT)
    run_git(["commit", "-m", "Initial commit"], "create initial commit", _TEMP_ROOT)

    # Create and initialize sub-repos
    sub_repo_dirs = []
    for i in range(2):  # Create 2 sub-repos
        sub_repo_dir = _TEMP_ROOT / f"repo{i}"
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

    run_git(["add", "."], "stage post-sync files", _TEMP_ROOT)
    run_git(["commit", "-m", "Post-sync commit"], "post-sync commit", _TEMP_ROOT)

    yield _TEMP_ROOT, sub_repo_dirs


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up the temporary directory after all tests are done."""
    # Open temp directory in Finder on Mac if tests failed
    if sys.platform == "darwin" and exitstatus != 0:
        subprocess.run(["open", str(_TEMP_ROOT)])
