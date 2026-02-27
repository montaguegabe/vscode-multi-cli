import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from multi.sync_github import GENERATED_MARKER, sync_all_github_actions, sync_github_cmd


def _write_multi_json(workspace: Path, mono_repo: bool) -> None:
    multi_json = {
        "monoRepo": mono_repo,
        "repos": [
            {"name": "packages/api"},
            {"name": "packages/web"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))


def _parse_generated_yaml(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    while lines and lines[0].startswith("#"):
        lines = lines[1:]
    while lines and lines[0] == "":
        lines = lines[1:]
    parsed = yaml.safe_load("\n".join(lines))
    assert isinstance(parsed, dict)
    return parsed


def test_sync_github_generates_root_workflow_and_injects_working_directory(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_multi_json(workspace, mono_repo=True)

    source_workflow = workspace / "packages" / "api" / ".github" / "workflows" / "ci.yml"
    source_workflow.parent.mkdir(parents=True, exist_ok=True)
    source_workflow.write_text(
        """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "hello"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    sync_all_github_actions(root_dir=workspace)

    generated_path = workspace / ".github" / "workflows" / "ci.yml"
    assert generated_path.exists()
    assert generated_path.read_text(encoding="utf-8").startswith(GENERATED_MARKER)

    generated_yaml = _parse_generated_yaml(generated_path)
    assert (
        generated_yaml["jobs"]["build"]["defaults"]["run"]["working-directory"]
        == "packages/api"
    )


def test_sync_github_preserves_existing_working_directory_defaults(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_multi_json(workspace, mono_repo=True)

    source_workflow = workspace / "packages" / "api" / ".github" / "workflows" / "ci.yml"
    source_workflow.parent.mkdir(parents=True, exist_ok=True)
    source_workflow.write_text(
        """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: custom/path
    steps:
      - run: echo "hello"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    sync_all_github_actions(root_dir=workspace)

    generated_path = workspace / ".github" / "workflows" / "ci.yml"
    generated_yaml = _parse_generated_yaml(generated_path)
    assert (
        generated_yaml["jobs"]["build"]["defaults"]["run"]["working-directory"]
        == "custom/path"
    )


def test_sync_github_prefixes_workflow_filename_on_collision(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_multi_json(workspace, mono_repo=True)

    api_workflow = workspace / "packages" / "api" / ".github" / "workflows" / "ci.yml"
    web_workflow = workspace / "packages" / "web" / ".github" / "workflows" / "ci.yml"
    api_workflow.parent.mkdir(parents=True, exist_ok=True)
    web_workflow.parent.mkdir(parents=True, exist_ok=True)
    api_workflow.write_text("name: API\njobs: {}\n", encoding="utf-8")
    web_workflow.write_text("name: WEB\njobs: {}\n", encoding="utf-8")

    sync_all_github_actions(root_dir=workspace)

    workflows_dir = workspace / ".github" / "workflows"
    assert (workflows_dir / "ci.yml").exists()
    assert (workflows_dir / "packages-web--ci.yml").exists()


def test_sync_github_removes_stale_generated_and_preserves_manual_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_multi_json(workspace, mono_repo=True)

    source_workflow = workspace / "packages" / "api" / ".github" / "workflows" / "ci.yml"
    source_workflow.parent.mkdir(parents=True, exist_ok=True)
    source_workflow.write_text("name: API\njobs: {}\n", encoding="utf-8")

    sync_all_github_actions(root_dir=workspace)

    workflows_dir = workspace / ".github" / "workflows"
    manual_workflow = workflows_dir / "manual.yml"
    manual_workflow.write_text("name: manual\njobs: {}\n", encoding="utf-8")

    source_workflow.unlink()
    sync_all_github_actions(root_dir=workspace)

    assert not (workflows_dir / "ci.yml").exists()
    assert manual_workflow.exists()


def test_sync_github_command_fails_outside_monorepo_mode():
    runner = CliRunner()
    with runner.isolated_filesystem():
        multi_json = {
            "monoRepo": False,
            "repos": [{"url": "https://github.com/example/repo"}],
        }
        Path("multi.json").write_text(json.dumps(multi_json, indent=2))

        result = runner.invoke(sync_github_cmd)

    assert result.exit_code != 0
    assert "only available in monorepo mode" in result.output
