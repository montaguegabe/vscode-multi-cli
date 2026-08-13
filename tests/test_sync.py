import json
import logging
from pathlib import Path
from types import SimpleNamespace

import git
from click.testing import CliRunner

from multi.cli import main
from multi.sync import _clone_repo, sync


def test_sync_initializes_root_git_and_creates_readme(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "monoRepo": True,
        "repos": [
            {"name": "packages/api", "description": "Backend API"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    sync(root_dir=workspace)

    assert (workspace / ".git").exists()
    assert (workspace / "README.md").exists()
    readme = (workspace / "README.md").read_text(encoding="utf-8")
    assert "uv tool install multi-workspace" in readme
    assert "pipx install multi-workspace" not in readme


def test_sync_warns_and_continues_for_nested_git_in_monorepo(tmp_path, caplog):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "monoRepo": True,
        "repos": [
            {"name": "packages/api"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))
    (workspace / "packages" / "api" / ".git").mkdir(parents=True)

    with caplog.at_level(logging.WARNING):
        sync(root_dir=workspace)

    assert any("nested .git" in message for message in caplog.messages)


def test_sync_in_monorepo_syncs_github_actions_to_root(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "monoRepo": True,
        "repos": [
            {"name": "packages/api"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    source_workflow = workspace / "packages" / "api" / ".github" / "workflows" / "ci.yml"
    source_workflow.parent.mkdir(parents=True, exist_ok=True)
    source_workflow.write_text(
        """
name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""".strip()
        + "\n"
    )

    sync(root_dir=workspace)

    assert (workspace / ".github" / "workflows" / "ci.yml").exists()


def _commit_all(repo: git.Repo, message: str) -> None:
    repo.git.add(all=True)
    repo.index.commit(message)


def _create_remote_repo(
    base_path: Path,
    name: str,
    *,
    branches: list[str] | None = None,
) -> Path:
    seed_path = base_path / f"{name}-seed"
    seed_path.mkdir()
    repo = git.Repo.init(seed_path, initial_branch="main")
    (seed_path / "branch.txt").write_text("main\n", encoding="utf-8")
    _commit_all(repo, "Initial commit")

    remote_path = base_path / "remotes" / name
    remote_path.parent.mkdir(exist_ok=True)
    git.Repo.init(remote_path, bare=True)
    origin = repo.create_remote("origin", str(remote_path))
    origin.push(refspec="main:main")

    for branch_name in branches or []:
        repo.create_head(branch_name).checkout()
        (seed_path / "branch.txt").write_text(f"{branch_name}\n", encoding="utf-8")
        _commit_all(repo, f"Add {branch_name}")
        origin.push(refspec=f"{branch_name}:{branch_name}")

    repo.heads.main.checkout()
    return remote_path


def _write_clone_workspace(
    workspace: Path,
    repo_configs: list[dict],
    *,
    branch_name: str | None = None,
) -> None:
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps({"repos": repo_configs}, indent=2),
        encoding="utf-8",
    )
    root_repo = git.Repo.init(workspace, initial_branch="main")
    root_repo.git.add(["multi.json"])
    root_repo.index.commit("Configure workspace")
    if branch_name:
        root_repo.create_head(branch_name).checkout()


def test_sync_clones_fixed_branch_to_expected_branch(tmp_path):
    repo0_remote = _create_remote_repo(tmp_path, "repo0", branches=["feature/root"])
    repo1_remote = _create_remote_repo(tmp_path, "repo1", branches=["stable"])
    workspace = tmp_path / "workspace"
    _write_clone_workspace(
        workspace,
        [
            {"url": str(repo0_remote), "name": "repo0"},
            {"url": str(repo1_remote), "name": "repo1", "fixedBranch": "stable"},
        ],
        branch_name="feature/root",
    )

    sync(root_dir=workspace)

    assert git.Repo(workspace / "repo0").active_branch.name == "feature/root"
    assert git.Repo(workspace / "repo1").active_branch.name == "stable"


def test_sync_single_branch_clones_expected_branch_when_remote_default_differs(
    tmp_path,
):
    repo0_remote = _create_remote_repo(tmp_path, "repo0", branches=["develop"])
    git.Repo(repo0_remote).git.symbolic_ref("HEAD", "refs/heads/develop")
    workspace = tmp_path / "workspace"
    _write_clone_workspace(
        workspace,
        [{"url": str(repo0_remote), "name": "repo0"}],
    )

    sync(root_dir=workspace)

    repo = git.Repo(workspace / "repo0")
    assert repo.active_branch.name == "main"
    assert repo.heads.main.commit == repo.remotes.origin.refs.main.commit
    assert "develop" not in [head.name for head in repo.heads]
    assert "origin/develop" not in [ref.name for ref in repo.remotes.origin.refs]


def test_sync_install_set_clones_fixed_branch_to_expected_branch(tmp_path):
    repo0_remote = _create_remote_repo(tmp_path, "repo0", branches=["feature/root"])
    repo1_remote = _create_remote_repo(tmp_path, "repo1", branches=["stable"])
    repo2_remote = _create_remote_repo(tmp_path, "repo2", branches=["stable"])
    workspace = tmp_path / "workspace"
    _write_clone_workspace(
        workspace,
        [
            {
                "url": str(repo0_remote),
                "name": "repo0",
                "installSets": ["default", "dev"],
            },
            {
                "url": str(repo1_remote),
                "name": "repo1",
                "fixedBranch": "stable",
                "installSets": ["default"],
            },
            {
                "url": str(repo2_remote),
                "name": "repo2",
                "fixedBranch": "stable",
                "installSets": ["dev"],
            },
        ],
        branch_name="feature/root",
    )

    sync(root_dir=workspace, install_set="default")

    assert git.Repo(workspace / "repo0").active_branch.name == "feature/root"
    assert git.Repo(workspace / "repo1").active_branch.name == "stable"
    assert not (workspace / "repo2").exists()


def test_sync_with_branch_mirroring_disabled_still_clones_fixed_branch(tmp_path):
    repo0_remote = _create_remote_repo(tmp_path, "repo0")
    repo1_remote = _create_remote_repo(tmp_path, "repo1", branches=["stable"])
    workspace = tmp_path / "workspace"
    _write_clone_workspace(
        workspace,
        [
            {"url": str(repo0_remote), "name": "repo0"},
            {"url": str(repo1_remote), "name": "repo1", "fixedBranch": "stable"},
        ],
        branch_name="feature/not-synced",
    )

    sync(root_dir=workspace, ensure_on_same_branch=False)

    assert git.Repo(workspace / "repo0").active_branch.name == "main"
    assert git.Repo(workspace / "repo1").active_branch.name == "stable"


def test_sync_symlink_checkout_uses_fixed_branch(tmp_path, monkeypatch):
    existing_repo_path = tmp_path / "existing"
    existing_repo_path.mkdir()
    existing_repo = git.Repo.init(existing_repo_path, initial_branch="main")
    (existing_repo_path / "branch.txt").write_text("main\n", encoding="utf-8")
    _commit_all(existing_repo, "Initial commit")
    existing_repo.create_head("stable").checkout()
    (existing_repo_path / "branch.txt").write_text("stable\n", encoding="utf-8")
    _commit_all(existing_repo, "Add stable")
    existing_repo.heads.main.checkout()

    workspace = tmp_path / "workspace"
    _write_clone_workspace(
        workspace,
        [
            {
                "url": "https://github.com/example/repo0",
                "name": "repo0",
                "allowSymlink": True,
                "fixedBranch": "stable",
            },
        ],
    )
    config = json.loads((workspace / "multi.json").read_text(encoding="utf-8"))
    config["allowSymlinks"] = True
    (workspace / "multi.json").write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr("multi.sync.lookup_repo", lambda url: existing_repo_path)

    sync(root_dir=workspace)

    assert (workspace / "repo0").is_symlink()
    assert git.Repo(existing_repo_path).active_branch.name == "stable"


def test_sync_validates_fixed_branch_is_string(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {"repos": [{"url": "https://github.com/example/repo0", "fixedBranch": 1}]}
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(workspace)
    result = CliRunner().invoke(main, ["sync"])

    assert result.exit_code == 1
    assert "fixedBranch for repository repo0 must be a string" in result.output


def test_sync_does_not_generate_agent_instructions_by_default(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "monoRepo": True,
        "repos": [
            {"name": "packages/api", "description": "Backend API"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))
    (workspace / "AGENTS.md").write_text("Manual agents\n", encoding="utf-8")
    (workspace / "CLAUDE.md").write_text("Manual claude\n", encoding="utf-8")
    parts_dir = workspace / "AGENTS.parts"
    parts_dir.mkdir()
    (parts_dir / "base.md").write_text("Generated agents\n", encoding="utf-8")

    sync(root_dir=workspace)

    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "Manual agents\n"
    assert (workspace / "CLAUDE.md").read_text(encoding="utf-8") == "Manual claude\n"


def test_multi_sync_fails_when_repo_url_ends_with_dot_git():
    runner = CliRunner()

    with runner.isolated_filesystem():
        multi_json = {
            "repos": [
                {"url": "https://github.com/example/repo-a.git"},
            ]
        }
        with open("multi.json", "w", encoding="utf-8") as f:
            json.dump(multi_json, f, indent=2)
            f.write("\n")

        result = runner.invoke(main, ["sync"])

    assert result.exit_code == 1
    assert "must not end with '.git'" in result.output
    assert "rerun `multi sync`" in result.output


def test_clone_repo_checks_out_in_temp_dir_before_moving_to_workspace(
    tmp_path,
    monkeypatch,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_path = workspace / "repo-a"
    clone_calls = {}
    move_calls = {}

    class FakeRepo:
        pass

    def fake_clone_from(url, path, **kwargs):
        clone_calls["url"] = url
        clone_calls["path"] = Path(path)
        clone_calls["kwargs"] = kwargs
        return FakeRepo()

    def fake_move(src, dst):
        move_calls["src"] = Path(src)
        move_calls["dst"] = Path(dst)

    monkeypatch.setattr("multi.sync.git.Repo.clone_from", fake_clone_from)
    monkeypatch.setattr("multi.sync.shutil.move", fake_move)

    _clone_repo(
        SimpleNamespace(
            name="repo-a",
            url="https://github.com/example/repo-a",
            path=repo_path,
        ),
        expected_branch=None,
    )

    assert clone_calls["url"] == "https://github.com/example/repo-a"
    assert clone_calls["path"].parent != workspace
    assert clone_calls["kwargs"] == {}
    assert move_calls["src"] == clone_calls["path"]
    assert move_calls["dst"] == repo_path
