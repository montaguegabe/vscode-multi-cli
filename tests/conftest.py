import json
import shutil
from pathlib import Path
from typing import Generator, List

import git
import pytest

from multi.sync import sync

# Define a consistent temporary directory path structure
_TEMP_ROOT = Path("/tmp/vscode-multi-test")
_TEMP_PROJECT_ROOT = _TEMP_ROOT / "root"
_TEMP_REMOTES_ROOT = _TEMP_ROOT / "remotes"
_TEMP_PROJECT_ROOT_INITIAL = _TEMP_ROOT / "root_initial"
_TEMP_REMOTES_ROOT_INITIAL = _TEMP_ROOT / "remotes_initial"


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

        root_repo = git.Repo.init(_TEMP_PROJECT_ROOT)
        readme_path = _TEMP_PROJECT_ROOT / "README.md"
        readme_path.write_text("# Root Repository")
        root_repo.git.add(["README.md", "multi.json"])
        root_repo.index.commit("Initial commit")

        created_sub_repo_dirs = []
        for name in sub_repo_names:
            sub_repo_dir = _TEMP_PROJECT_ROOT / name
            sub_repo_dir.mkdir()
            sub_repo = git.Repo.init(sub_repo_dir)
            readme_sub_path = sub_repo_dir / "README.md"
            readme_sub_path.write_text(f"# Sub Repository {name}")
            sub_repo.git.add(["README.md"])
            sub_repo.index.commit("Initial commit")
            created_sub_repo_dirs.append(sub_repo_dir)

        sync(root_dir=_TEMP_PROJECT_ROOT)
        root_repo.git.add(all=True)
        root_repo.index.commit("Post-sync commit")

        # --- Full setup of remote repositories and linking ---
        root_remote_git_path = _TEMP_REMOTES_ROOT / "root.git"
        git.Repo.init(root_remote_git_path, bare=True)
        root_repo.create_remote("origin", str(root_remote_git_path))
        root_repo.remotes.origin.push(refspec="main:main", set_upstream=True)

        for i, sub_repo_path_obj in enumerate(created_sub_repo_dirs):
            sub_repo_actual_name = sub_repo_names[i]
            sub_remote_git_path = _TEMP_REMOTES_ROOT / f"{sub_repo_actual_name}.git"
            git.Repo.init(sub_remote_git_path, bare=True)
            sub_repo = git.Repo(sub_repo_path_obj)
            sub_repo.create_remote("origin", str(sub_remote_git_path))
            sub_repo.remotes.origin.push(refspec="main:main", set_upstream=True)

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
