import json
import os
import shutil
from pathlib import Path
from typing import Generator, List

import pytest

from vscode_multi.sync import sync

# Define a consistent temporary directory path structure
_TEMP_ROOT = Path("/tmp/vscode-multi-test")
_TEMP_PROJECT_ROOT = _TEMP_ROOT / "root"
_TEMP_REMOTES_ROOT = _TEMP_ROOT / "remotes"
_TEMP_PROJECT_ROOT_INITIAL = _TEMP_ROOT / "root_initial"
_TEMP_REMOTES_ROOT_INITIAL = _TEMP_ROOT / "remotes_initial"

# Set the environment variable to our consistent temp project root directory
# This is needed for sync() to correctly determine the project root.
os.environ["vscode_multi_ROOT_DIR"] = str(_TEMP_PROJECT_ROOT)

# Now we can safely import from vscode_multi
from vscode_multi.git_helpers import run_git  # noqa: E402


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(call):
    raise call.excinfo.value


@pytest.hookimpl(tryfirst=True)
def pytest_internalerror(excinfo):
    raise excinfo.value


@pytest.fixture(scope="session", autouse=True)
def clear_temp_root():
    """Clear the temp root directory at the start of the test session."""
    if _TEMP_ROOT.exists():
        shutil.rmtree(_TEMP_ROOT)
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def setup_git_repos() -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository and sub-repositories.
    On first run (cache miss), also sets up their remotes and caches everything.
    On subsequent runs (cache hit), restores local repos from cache. Remotes are
    created/cached on miss but not restored from cache by this base fixture.
    Yields a tuple of (root_repo_path, [sub_repo_dirs]).
    """
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)  # Ensure base temp dir exists
    sub_repo_names = [f"repo{i}" for i in range(2)]

    if _TEMP_PROJECT_ROOT_INITIAL.exists():
        # Cache hit for local project files
        if _TEMP_PROJECT_ROOT.exists():
            shutil.rmtree(_TEMP_PROJECT_ROOT)
        shutil.copytree(_TEMP_PROJECT_ROOT_INITIAL, _TEMP_PROJECT_ROOT)

        # Ensure remotes directory is clean but don't populate from cache here
        if _TEMP_REMOTES_ROOT.exists():
            shutil.rmtree(_TEMP_REMOTES_ROOT)
        _TEMP_REMOTES_ROOT.mkdir(parents=True, exist_ok=True)

        current_sub_repo_dirs = [_TEMP_PROJECT_ROOT / name for name in sub_repo_names]
        yield _TEMP_PROJECT_ROOT, current_sub_repo_dirs
    else:
        # Cache miss: Create everything from scratch, then populate both caches.
        if _TEMP_ROOT.exists():  # Clear entire temp area for a full rebuild
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

        sync()  # Uses vscode_multi_ROOT_DIR
        run_git(["add", "."], "stage post-sync files", _TEMP_PROJECT_ROOT)
        run_git(
            ["commit", "-m", "Post-sync commit"], "post-sync commit", _TEMP_PROJECT_ROOT
        )

        # --- Full setup of remote repositories and linking ---
        root_remote_git_path_str = str(_TEMP_REMOTES_ROOT / "root.git")
        run_git(
            ["init", "--bare", root_remote_git_path_str],
            "create root bare repo",
            _TEMP_PROJECT_ROOT,
        )  # Bare repo in _TEMP_REMOTES_ROOT
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

        for i, sub_repo_path_obj in enumerate(created_sub_repo_dirs):
            sub_repo_actual_name = sub_repo_names[i]
            sub_remote_git_path_str = str(
                _TEMP_REMOTES_ROOT / f"{sub_repo_actual_name}.git"
            )
            # Bare repo in _TEMP_REMOTES_ROOT, context for run_git is the sub_repo_path_obj for git commands if needed, but init --bare doesn't need it.
            # Let's run it in the sub_repo_path_obj context just for consistency, though for bare it doesn't matter much.
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

        # Populate both caches
        shutil.copytree(_TEMP_PROJECT_ROOT, _TEMP_PROJECT_ROOT_INITIAL)
        shutil.copytree(_TEMP_REMOTES_ROOT, _TEMP_REMOTES_ROOT_INITIAL)

        yield _TEMP_PROJECT_ROOT, created_sub_repo_dirs


@pytest.fixture
def setup_git_repos_with_remotes(
    setup_git_repos: tuple[Path, List[Path]],
) -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Ensures local git repos are set up (via setup_git_repos fixture) and
    that the remote repositories are also restored from cache.
    Yields a tuple of (root_repo_path, [sub_repo_dirs]).
    """
    root_repo_path, sub_repo_dirs = setup_git_repos

    # Ensure _TEMP_REMOTES_ROOT_INITIAL exists (should have been created by setup_git_repos on a cache miss)
    if not _TEMP_REMOTES_ROOT_INITIAL.exists():
        # This case should ideally not be hit if setup_git_repos is working correctly
        # and was called, leading to a cache miss and population of _TEMP_REMOTES_ROOT_INITIAL.
        # For robustness, one might re-trigger the caching part or error, but here we assume it exists.
        # Or, if it's a hard requirement, raise an error.
        # For now, we'll proceed assuming it was created if a full setup ran.
        raise Exception(
            "setup_git_repos_with_remotes: _TEMP_REMOTES_ROOT_INITIAL does not exist"
        )  # If it doesn't exist, the copytree below will fail, which is an indicator of a problem.

    if (
        _TEMP_REMOTES_ROOT_INITIAL.exists()
    ):  # Double check, or rely on setup_git_repos logic
        if _TEMP_REMOTES_ROOT.exists():
            shutil.rmtree(_TEMP_REMOTES_ROOT)
        shutil.copytree(_TEMP_REMOTES_ROOT_INITIAL, _TEMP_REMOTES_ROOT)
    # If _TEMP_REMOTES_ROOT_INITIAL doesn't exist, it means the initial full setup
    # in setup_git_repos didn't complete or wasn't triggered. This fixture relies on that.
    else:
        raise Exception(
            "setup_git_repos_with_remotes: _TEMP_REMOTES_ROOT_INITIAL does not exist"
        )

    yield root_repo_path, sub_repo_dirs
