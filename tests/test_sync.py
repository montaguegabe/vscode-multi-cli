import json
import logging

from click.testing import CliRunner

from multi.cli import main
from multi.sync import sync


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
