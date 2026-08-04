import json
import shutil

import git
import pytest

from multi.branch import report_branches
from multi.cli import main
from multi.errors import GitError
from multi.git_helpers import check_all_on_same_branch, describe_head
from multi.git_run import run_git_in_all_repos
from multi.paths import Paths


def _make_dirty(repo_path):
    (repo_path / "dirty.txt").write_text("uncommitted change")


def _configure_fixed_branch(root_repo_path, repo_index, branch_name):
    multi_json_path = root_repo_path / "multi.json"
    config = json.loads(multi_json_path.read_text(encoding="utf-8"))
    config["repos"][repo_index]["fixedBranch"] = branch_name
    multi_json_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def test_report_branches_works_with_dirty_trees(setup_git_repos):
    """Branch checking is read-only and must not require clean working trees."""
    root_repo_path, sub_repo_paths = setup_git_repos
    _make_dirty(root_repo_path)
    for sub_repo_path in sub_repo_paths:
        _make_dirty(sub_repo_path)

    assert report_branches(Paths(root_repo_path)) is True


def test_report_branches_flags_mismatch_with_dirty_trees(setup_git_repos):
    """Mismatched branches are reported (not raised) even when trees are dirty."""
    root_repo_path, sub_repo_paths = setup_git_repos
    git.Repo(sub_repo_paths[0]).create_head("other-branch").checkout()
    _make_dirty(root_repo_path)
    _make_dirty(sub_repo_paths[0])

    assert report_branches(Paths(root_repo_path)) is False


def test_report_branches_respects_fixed_branch(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    fixed_repo = git.Repo(sub_repo_paths[0])
    fixed_repo.create_head("stable").checkout()
    _configure_fixed_branch(root_repo_path, repo_index=0, branch_name="stable")

    assert report_branches(Paths(root_repo_path)) is True


def test_report_branches_reports_detached_head(setup_git_repos):
    """A detached HEAD is reported as detached instead of crashing."""
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo = git.Repo(sub_repo_paths[0])
    sub_repo.git.checkout("--detach")

    assert report_branches(Paths(root_repo_path)) is False
    assert describe_head(sub_repo_paths[0]).startswith("(detached at ")


def test_branch_cmd_succeeds_with_dirty_trees(setup_git_repos, monkeypatch):
    root_repo_path, sub_repo_paths = setup_git_repos
    _make_dirty(root_repo_path)
    _make_dirty(sub_repo_paths[0])
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch"])

    assert result.exit_code == 0
    assert "main" in result.output


def test_branch_check_cmd_succeeds_with_dirty_trees(setup_git_repos, monkeypatch):
    root_repo_path, sub_repo_paths = setup_git_repos
    _make_dirty(root_repo_path)
    _make_dirty(sub_repo_paths[0])
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch", "check"])

    assert result.exit_code == 0
    assert "main" in result.output


def test_branch_cmd_fails_on_mismatch(setup_git_repos, monkeypatch):
    root_repo_path, sub_repo_paths = setup_git_repos
    git.Repo(sub_repo_paths[0]).create_head("other-branch").checkout()
    _make_dirty(sub_repo_paths[0])
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch"])

    assert result.exit_code == 1
    assert "other-branch" in result.output
    assert "expected root branch main" in result.output


def test_branch_check_cmd_fails_on_mismatch(setup_git_repos, monkeypatch):
    root_repo_path, sub_repo_paths = setup_git_repos
    git.Repo(sub_repo_paths[0]).create_head("other-branch").checkout()
    _make_dirty(sub_repo_paths[0])
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch", "check"])

    assert result.exit_code == 1
    assert "other-branch" in result.output
    assert "expected root branch main" in result.output


def test_branch_help_lists_check_subcommand():
    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch", "--help"])

    assert result.exit_code == 0
    assert "check" in result.output
    assert "expected branches" in result.output


def test_report_branches_continues_past_missing_repo(setup_git_repos):
    """A configured but never-synced sub-repo is reported, not fatal."""
    root_repo_path, sub_repo_paths = setup_git_repos
    shutil.rmtree(sub_repo_paths[0])

    assert report_branches(Paths(root_repo_path)) is False


def test_report_branches_continues_past_non_git_directory(setup_git_repos):
    """A sub-repo directory without .git is reported as missing, not fatal."""
    root_repo_path, sub_repo_paths = setup_git_repos
    shutil.rmtree(sub_repo_paths[0] / ".git")

    assert report_branches(Paths(root_repo_path)) is False


def test_branch_cmd_lists_all_repos_when_one_is_missing(setup_git_repos, monkeypatch):
    """The full report is printed (once per repo) before the nonzero exit."""
    root_repo_path, sub_repo_paths = setup_git_repos
    missing_repo = sub_repo_paths[0]
    remaining_repo = sub_repo_paths[1]
    shutil.rmtree(missing_repo)
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["branch"])

    assert result.exit_code == 1
    missing_line = f"{missing_repo.name}: (missing — run `multi sync`)"
    assert result.output.count(missing_line) == 1
    # Repos after the missing one are still listed.
    assert f"{remaining_repo.name}: main" in result.output
    # No absolute filesystem paths and no bad `git init` advice.
    assert str(missing_repo) not in result.output
    assert "git init" not in result.output


def test_check_all_on_same_branch_allows_dirty_trees(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    _make_dirty(root_repo_path)
    for sub_repo_path in sub_repo_paths:
        _make_dirty(sub_repo_path)

    assert check_all_on_same_branch(Paths(root_repo_path)) is True


def test_check_all_on_same_branch_describes_detached_head(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    git.Repo(sub_repo_paths[0]).git.checkout("--detach")

    with pytest.raises(GitError) as exc_info:
        check_all_on_same_branch(Paths(root_repo_path))
    assert "(detached at " in str(exc_info.value)


def test_run_git_in_all_repos_allows_dirty_trees(setup_git_repos):
    """Read-only `multi git` queries must not require clean working trees."""
    root_repo_path, sub_repo_paths = setup_git_repos
    _make_dirty(root_repo_path)
    _make_dirty(sub_repo_paths[0])

    # Should not raise despite the dirty trees.
    run_git_in_all_repos(Paths(root_repo_path), ["branch", "--show-current"])


def test_run_git_in_all_repos_allows_fixed_branch_expected_state(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    fixed_repo = git.Repo(sub_repo_paths[0])
    fixed_repo.create_head("stable").checkout()
    _configure_fixed_branch(root_repo_path, repo_index=0, branch_name="stable")

    run_git_in_all_repos(Paths(root_repo_path), ["branch", "--show-current"])


def test_git_cmd_passes_through_git_options(setup_git_repos, monkeypatch):
    """Unknown options like --show-current are forwarded to git, not parsed."""
    root_repo_path, _ = setup_git_repos
    monkeypatch.chdir(root_repo_path)

    from click.testing import CliRunner

    result = CliRunner().invoke(main, ["git", "branch", "--show-current"])

    assert result.exit_code == 0


def test_report_branches_in_worktree_with_detached_subrepo(setup_git_repos, tmp_path):
    """Branch checking works in linked worktrees where .git is a file."""
    root_repo_path, sub_repo_paths = setup_git_repos

    worktree_path = tmp_path / "workspace-worktree"
    git.Repo(root_repo_path).git.worktree("add", "-b", "wt-branch", str(worktree_path))
    # Sub-repos are gitignored, so add them as linked worktrees too.
    for sub_repo_path in sub_repo_paths:
        git.Repo(sub_repo_path).git.worktree(
            "add", "--detach", str(worktree_path / sub_repo_path.name)
        )
    _make_dirty(worktree_path)

    assert (worktree_path / ".git").is_file()
    assert report_branches(Paths(worktree_path)) is False

    # Attach the sub-repo worktrees to the matching branch and re-check.
    for sub_repo_path in sub_repo_paths:
        git.Repo(worktree_path / sub_repo_path.name).git.checkout("-b", "wt-branch")
    assert report_branches(Paths(worktree_path)) is True
