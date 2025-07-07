import pytest

from vscode_multi.errors import MergeBranchError, RepoNotCleanError
from vscode_multi.git_helpers import run_git
from vscode_multi.git_merge_branch import merge_branches_in_all_repos


def test_successful_merge(setup_git_repos):
    """Test merging a feature branch into main branch successfully."""
    root_repo, sub_repos = setup_git_repos
    source_branch = "feature/test-merge"
    target_branch = "main"

    # Create and set up feature branch with changes in all repos
    all_repos = [root_repo] + sub_repos
    for repo in all_repos:
        # Create and switch to feature branch
        run_git(["checkout", "-b", source_branch], "create branch", repo)

        # Make a change and commit it
        (repo / "merge_test.txt").write_text("test content")
        run_git(["add", "merge_test.txt"], "stage file", repo)
        run_git(["commit", "-m", "test commit"], "commit changes", repo)

        # Switch back to main
        run_git(["checkout", target_branch], "switch to main", repo)

    # Perform the merge
    merge_branches_in_all_repos(source_branch, target_branch)

    # Verify the merge was successful in all repos
    for repo in all_repos:
        # Check we're on target branch
        result = run_git(["branch", "--show-current"], "get current branch", repo)
        assert result == target_branch

        # Verify the merged file exists
        assert (repo / "merge_test.txt").exists()


def test_merge_nonexistent_branch(setup_git_repos):
    """Test that merging a non-existent branch raises appropriate error."""
    root_repo, _ = setup_git_repos
    source_branch = "nonexistent-branch"
    target_branch = "main"

    with pytest.raises(MergeBranchError) as exc_info:
        merge_branches_in_all_repos(source_branch, target_branch)

    assert "does not exist locally or remotely" in str(exc_info.value)


def test_merge_with_uncommitted_changes(setup_git_repos):
    """Test that merging with uncommitted changes fails."""
    root_repo, sub_repos = setup_git_repos
    source_branch = "feature/merge-test"
    target_branch = "main"

    # Create a feature branch
    run_git(["checkout", "-b", source_branch], "create branch", root_repo)
    run_git(["checkout", target_branch], "switch back to main", root_repo)

    # Create uncommitted changes
    (root_repo / "uncommitted.txt").write_text("uncommitted change")
    run_git(["add", "uncommitted.txt"], "stage file", root_repo)

    # Attempt merge should fail
    with pytest.raises(RepoNotCleanError):
        merge_branches_in_all_repos(source_branch, target_branch)


def test_merge_in_multiple_repos(setup_git_repos):
    """Test that merging works across multiple repositories."""
    root_repo, sub_repos = setup_git_repos
    source_branch = "feature/multi-repo-merge"
    target_branch = "main"

    all_repos = [root_repo] + sub_repos

    # Set up branches with different changes in each repo
    for i, repo in enumerate(all_repos):
        # Create and switch to feature branch
        run_git(["checkout", "-b", source_branch], "create branch", repo)

        # Make a unique change in each repo
        (repo / f"merge_test_{i}.txt").write_text(f"content for repo {i}")
        run_git(["add", f"merge_test_{i}.txt"], "stage file", repo)
        run_git(["commit", "-m", f"test commit {i}"], "commit changes", repo)

        run_git(["checkout", target_branch], "switch to main", repo)

    # Perform the merge
    merge_branches_in_all_repos(source_branch, target_branch)

    # Verify changes in each repo
    for i, repo in enumerate(all_repos):
        assert (repo / f"merge_test_{i}.txt").exists()
        assert (repo / f"merge_test_{i}.txt").read_text() == f"content for repo {i}"
