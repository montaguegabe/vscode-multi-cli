import json
import subprocess
from pathlib import Path

import pytest

from multi.app_api import (
    get_project_status,
    get_project_subrepos,
    get_repo_diff,
    get_repo_status,
    list_project_repo_names,
)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test"], path)


def _commit_file(path: Path, name: str, content: str = "hello\n") -> None:
    (path / name).write_text(content)
    _git(["add", name], path)
    _git(["commit", "-q", "-m", f"add {name}"], path)


def _add_upstream(repo: Path, remote_dir: Path) -> None:
    _git(["init", "-q", "--bare", str(remote_dir)], repo.parent)
    _git(["remote", "add", "origin", str(remote_dir)], repo)
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _git(["push", "-q", "-u", "origin", branch], repo)


def test_get_repo_status_states(tmp_path: Path) -> None:
    assert get_repo_status(tmp_path / "nope") == "missing"

    plain = tmp_path / "plain"
    plain.mkdir()
    assert get_repo_status(plain) == "no_git"

    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt")
    # No upstream yet: nothing to compare against, so the repo is out-of-sync.
    assert get_repo_status(repo) == "out-of-sync"
    _add_upstream(repo, tmp_path / "repo-remote.git")
    assert get_repo_status(repo) == "clean"

    _commit_file(repo, "c.txt")
    assert get_repo_status(repo) == "out-of-sync"

    (repo / "b.txt").write_text("untracked\n")
    assert get_repo_status(repo) == "dirty"


def test_get_repo_status_survives_broken_git_dir(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: /nonexistent/place\n")
    assert get_repo_status(broken) == "unknown"


def test_get_repo_diff_includes_untracked_and_unborn_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt", "one\n")
    (repo / "a.txt").write_text("two\n")
    (repo / "new.txt").write_text("fresh\n")

    diff = get_repo_diff(repo)
    assert "a.txt" in diff
    assert "new.txt" in diff
    assert "+fresh" in diff

    unborn = tmp_path / "unborn"
    _init_repo(unborn)
    (unborn / "seed.txt").write_text("seed\n")
    _git(["add", "seed.txt"], unborn)
    assert "+seed" in get_repo_diff(unborn)


def test_workspace_helpers_read_only_local_multi_json(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    _init_repo(workspace)
    sub = workspace / "child"
    _init_repo(sub)
    _commit_file(sub, "a.txt")
    (workspace / "multi.json").write_text(
        json.dumps({"repos": [{"name": "child", "url": "https://example.com/child"}]})
    )
    _commit_file(workspace, "multi.json.keep")

    assert list_project_repo_names(workspace) == ["child"]
    payloads = get_project_subrepos(workspace)
    assert payloads == [{"name": "child", "path": str(sub)}]

    # A nested directory must not inherit the parent workspace's multi.json.
    nested = workspace / "child"
    assert list_project_repo_names(nested) == []
    assert get_project_subrepos(nested) == []

    assert list_project_repo_names(tmp_path / "not-a-workspace") == []


def test_get_project_status_folds_worst_subrepo(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    _init_repo(workspace)
    sub = workspace / "child"
    _init_repo(sub)
    _commit_file(sub, "a.txt")
    _add_upstream(sub, tmp_path / "child-remote.git")
    (workspace / "multi.json").write_text(
        json.dumps({"repos": [{"name": "child", "url": "https://example.com/child"}]})
    )
    _git(["add", "multi.json"], workspace)
    _git(["commit", "-q", "-m", "add multi.json"], workspace)
    _add_upstream(workspace, tmp_path / "ws-remote.git")

    assert get_project_status(workspace) == "clean"

    (sub / "wip.txt").write_text("work\n")
    assert get_project_status(workspace) == "dirty"


@pytest.mark.parametrize("payload", ["not json", json.dumps({"repos": "nope"})])
def test_workspace_helpers_tolerate_invalid_multi_json(
    tmp_path: Path, payload: str
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "multi.json").write_text(payload)
    assert list_project_repo_names(workspace) == []
    assert get_project_subrepos(workspace) == []
