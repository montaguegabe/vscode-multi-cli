import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

from cursor_multi.git_helpers import run_git


@pytest.fixture
def temp_git_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for Git repositories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def setup_git_repos(
    temp_git_dir: Path,
) -> Generator[tuple[Path, List[Path]], None, None]:
    """
    Sets up a root Git repository and sub-repositories for testing.
    Returns a tuple of (root_repo_path, [sub_repo_paths]).
    """
    # Create and initialize root repo
    root_repo = temp_git_dir / "root"
    root_repo.mkdir()
    run_git(["init"], "initialize root repository", root_repo)

    # Create a file and commit it to create an initial branch
    readme = root_repo / "README.md"
    readme.write_text("# Root Repository")
    run_git(["add", "README.md"], "stage README", root_repo)
    run_git(
        ["commit", "-m", "Initial commit"],
        "create initial commit",
        root_repo,
    )

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
        run_git(
            ["commit", "-m", "Initial commit"],
            "create initial commit",
            sub_repo,
        )
        sub_repos.append(sub_repo)

    # Create repos.txt in root repo
    repos_file = root_repo / "repos.txt"
    repos_file.write_text(
        "\n".join(str(repo.relative_to(root_repo)) for repo in sub_repos)
    )
    run_git(["add", "repos.txt"], "stage repos.txt", root_repo)
    run_git(
        ["commit", "-m", "Add repos.txt"],
        "commit repos.txt",
        root_repo,
    )

    # Monkeypatch the paths.root_dir to point to our temporary root repo
    import cursor_multi.paths

    original_root = cursor_multi.paths.paths.root_dir
    cursor_multi.paths.paths.root_dir = root_repo

    yield root_repo, sub_repos

    # Restore the original paths.root_dir
    cursor_multi.paths.paths.root_dir = original_root
