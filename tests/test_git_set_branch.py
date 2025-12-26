import git
import pytest

from multi.errors import RepoNotCleanError
from multi.git_set_branch import set_branch_in_all_repos


def test_set_branch_creates_new_branch(setup_git_repos):
    """Test creating a new branch in all repositories."""
    root_repo_path, sub_repo_paths = setup_git_repos
    branch_name = "feature/test-branch"

    # Create and switch to the new branch in all repos
    set_branch_in_all_repos(root_dir=root_repo_path, branch_name=branch_name)

    # Verify the branch was created and is current in root repo
    root_repo = git.Repo(root_repo_path)
    assert root_repo.active_branch.name == branch_name

    # Verify the branch was created and is current in all sub-repos
    for repo_path in sub_repo_paths:
        repo = git.Repo(repo_path)
        assert repo.active_branch.name == branch_name


def test_set_branch_switches_to_existing_branch(setup_git_repos):
    """Test switching to an existing branch in all repositories."""
    root_repo_path, sub_repo_paths = setup_git_repos
    branch_name = "feature/existing-branch"

    # First create the branch in all repos but switch back to main
    all_repo_paths = [root_repo_path] + sub_repo_paths
    for repo_path in all_repo_paths:
        repo = git.Repo(repo_path)
        repo.create_head(branch_name).checkout()
        repo.heads.main.checkout()

    # Now use set_branch to switch to the existing branch
    set_branch_in_all_repos(root_dir=root_repo_path, branch_name=branch_name)

    # Verify we're on the branch in all repos
    for repo_path in all_repo_paths:
        repo = git.Repo(repo_path)
        assert repo.active_branch.name == branch_name


def test_set_branch_with_uncommitted_changes(setup_git_repos):
    """Test that setting branch fails when there are uncommitted changes."""
    root_repo_path, _ = setup_git_repos
    branch_name = "feature/new-branch"

    # Create an uncommitted change in root repo
    (root_repo_path / "new_file.txt").write_text("uncommitted change")
    root_repo = git.Repo(root_repo_path)
    root_repo.index.add(["new_file.txt"])

    # Attempt to set branch should fail
    with pytest.raises(RepoNotCleanError):
        set_branch_in_all_repos(root_dir=root_repo_path, branch_name=branch_name)

    # Verify we're still on the original branch
    assert (
        root_repo.active_branch.name == "main"
    )  # or "master" depending on git version


def test_set_branch_with_remote_branch(setup_git_repos_with_remotes):
    """Test switching to a branch that exists only on remote."""
    root_repo_path, sub_repo_paths = setup_git_repos_with_remotes
    branch_name = "feature/remote-branch"

    # Create and push a branch to remote
    root_repo = git.Repo(root_repo_path)
    root_repo.create_head(branch_name).checkout()
    root_repo.remotes.origin.push(
        refspec=f"{branch_name}:{branch_name}", set_upstream=True
    )
    root_repo.heads.main.checkout()
    root_repo.delete_head(branch_name, force=True)

    # Now try to set the branch that only exists on remote
    set_branch_in_all_repos(root_dir=root_repo_path, branch_name=branch_name)

    # Verify we're on the branch
    assert root_repo.active_branch.name == branch_name
