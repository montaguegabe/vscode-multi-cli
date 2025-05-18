import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

# Create a temporary directory at module level that will exist for all tests
root_repo = Path(tempfile.mkdtemp())
os.environ["CURSOR_MULTI_ROOT_DIR"] = str(root_repo)

# Now we can safely import from cursor_multi
from cursor_multi.git_helpers import run_git  # noqa: E402


@pytest.fixture
def setup_git_repos() -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository and sub-repositories for testing.
    Returns a tuple of (root_repo_path, [sub_repo_paths]).
    """
    # Create multi.json in the root
    multi_json = {
        "repos": [
            {"url": "https://github.com/test/repo0"},
            {"url": "https://github.com/test/repo1"},
        ]
    }
    multi_json_path = root_repo / "multi.json"
    multi_json_path.write_text(json.dumps(multi_json, indent=2))

    run_git(["init"], "initialize root repository", root_repo)

    # Create a file and commit it to create an initial branch
    readme = root_repo / "README.md"
    readme.write_text("# Root Repository")
    run_git(["add", "README.md", "multi.json"], "stage files", root_repo)
    run_git(["commit", "-m", "Initial commit"], "create initial commit", root_repo)

    # Create and initialize sub-repos
    sub_repos = []
    for i in range(2):  # Create 2 sub-repos
        sub_repo = root_repo / f"repo{i}"
        sub_repo.mkdir()
        run_git(["init"], f"initialize sub-repo {i}", sub_repo)

        # Create a file and commit it
        readme = sub_repo / "README.md"
        readme.write_text(f"# Sub Repository {i}")
        run_git(["add", "README.md"], "stage README", sub_repo)
        run_git(["commit", "-m", "Initial commit"], "create initial commit", sub_repo)
        sub_repos.append(sub_repo)

    # Create repos.txt in root repo
    repos_file = root_repo / "repos.txt"
    repos_file.write_text(
        "\n".join(str(repo.relative_to(root_repo)) for repo in sub_repos)
    )
    run_git(["add", "repos.txt"], "stage repos.txt", root_repo)
    run_git(["commit", "-m", "Add repos.txt"], "commit repos.txt", root_repo)

    yield root_repo, sub_repos


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up the temporary directory after all tests are done."""

    # Open temp directory in Finder on Mac
    if sys.platform == "darwin":
        subprocess.run(["open", str(root_repo)])

    # shutil.rmtree(_TEMP_ROOT, ignore_errors=True)
