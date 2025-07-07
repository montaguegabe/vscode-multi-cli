import pytest

from vscode_multi.errors import RepoNotCleanError
from vscode_multi.git_helpers import run_git
from vscode_multi.git_set_branch import set_branch_in_all_repos


def test_set_branch_creates_new_branch(setup_git_repos):
    """Test creating a new branch in all repositories."""
    root_repo, sub_repos = setup_git_repos
    branch_name = "feature/test-branch"

    # Create and switch to the new branch in all repos
    set_branch_in_all_repos(branch_name)

    # Verify the branch was created and is current in root repo
    result = run_git(["branch", "--show-current"], "get current branch", root_repo)
    assert result == branch_name

    # Verify the branch was created and is current in all sub-repos
    for repo in sub_repos:
        result = run_git(["branch", "--show-current"], "get current branch", repo)
        assert result == branch_name


def test_set_branch_switches_to_existing_branch(setup_git_repos):
    """Test switching to an existing branch in all repositories."""
    root_repo, sub_repos = setup_git_repos
    branch_name = "feature/existing-branch"

    # First create the branch in all repos but switch back to main
    all_repos = [root_repo] + sub_repos
    for repo in all_repos:
        run_git(["checkout", "-b", branch_name], "create branch", repo)
        run_git(["checkout", "main"], "switch back to main", repo)

    # Now use set_branch to switch to the existing branch
    set_branch_in_all_repos(branch_name)

    # Verify we're on the branch in all repos
    for repo in all_repos:
        result = run_git(["branch", "--show-current"], "get current branch", repo)
        assert result == branch_name


def test_set_branch_with_uncommitted_changes(setup_git_repos):
    """Test that setting branch fails when there are uncommitted changes."""
    root_repo, _ = setup_git_repos
    branch_name = "feature/new-branch"

    # Create an uncommitted change in root repo
    (root_repo / "new_file.txt").write_text("uncommitted change")
    run_git(["add", "new_file.txt"], "stage new file", root_repo)

    # Attempt to set branch should fail
    with pytest.raises(RepoNotCleanError):
        set_branch_in_all_repos(branch_name)

    # Verify we're still on the original branch
    result = run_git(["branch", "--show-current"], "get current branch", root_repo)
    assert result == "main"  # or "master" depending on git version


def test_set_branch_with_remote_branch(setup_git_repos_with_remotes):
    """Test switching to a branch that exists only on remote."""
    root_repo, sub_repos = setup_git_repos_with_remotes
    branch_name = "feature/remote-branch"

    # Create and push a branch to remote
    run_git(["checkout", "-b", branch_name], "create branch", root_repo)
    run_git(["push", "-u", "origin", branch_name], "push branch", root_repo)
    run_git(["checkout", "main"], "switch back to main", root_repo)
    run_git(["branch", "-D", branch_name], "delete local branch", root_repo)

    # Now try to set the branch that only exists on remote
    set_branch_in_all_repos(branch_name)

    # Verify we're on the branch
    result = run_git(["branch", "--show-current"], "get current branch", root_repo)
    assert result == branch_name
