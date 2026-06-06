import json
from pathlib import Path

from click.testing import CliRunner

from multi.cli import main
from multi.sync import sync
from multi.utils import soft_read_json_file


def _write_workspace(workspace: Path) -> None:
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "repos": [
                    {
                        "url": "https://github.com/test/public",
                        "installSets": ["default", "dev"],
                    },
                    {
                        "url": "https://github.com/test/private",
                        "installSets": ["dev"],
                    },
                    {"url": "https://github.com/test/legacy"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_repo_settings(workspace: Path, repo_name: str, key: str) -> None:
    vscode_dir = workspace / repo_name / ".vscode"
    vscode_dir.mkdir(parents=True)
    (vscode_dir / "settings.json").write_text(
        json.dumps({key: repo_name}),
        encoding="utf-8",
    )


def test_sync_without_install_set_includes_all_repos(tmp_path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    _write_repo_settings(workspace, "public", "multi.public")
    _write_repo_settings(workspace, "private", "multi.private")
    _write_repo_settings(workspace, "legacy", "multi.legacy")

    sync(root_dir=workspace, ensure_on_same_branch=False)

    settings = soft_read_json_file(workspace / ".vscode" / "settings.json")
    assert settings["multi.public"] == "public"
    assert settings["multi.private"] == "private"
    assert settings["multi.legacy"] == "legacy"

    gitignore = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert "public/" in gitignore
    assert "private/" in gitignore
    assert "legacy/" in gitignore


def test_sync_with_install_set_excludes_repos_outside_set(tmp_path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    _write_repo_settings(workspace, "public", "multi.public")
    _write_repo_settings(workspace, "private", "multi.private")
    _write_repo_settings(workspace, "legacy", "multi.legacy")

    sync(root_dir=workspace, ensure_on_same_branch=False, install_set="default")

    settings = soft_read_json_file(workspace / ".vscode" / "settings.json")
    assert settings["multi.public"] == "public"
    assert "multi.private" not in settings


def test_repos_without_install_sets_are_included_in_selected_sets(tmp_path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    _write_repo_settings(workspace, "public", "multi.public")
    _write_repo_settings(workspace, "legacy", "multi.legacy")

    sync(root_dir=workspace, ensure_on_same_branch=False, install_set="default")

    settings = soft_read_json_file(workspace / ".vscode" / "settings.json")
    assert settings["multi.legacy"] == "legacy"


def test_install_set_updates_generated_files_for_selected_repos_only(tmp_path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    _write_repo_settings(workspace, "public", "multi.public")
    _write_repo_settings(workspace, "private", "multi.private")
    _write_repo_settings(workspace, "legacy", "multi.legacy")

    sync(root_dir=workspace, ensure_on_same_branch=False, install_set="default")

    gitignore = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert "public/" in gitignore
    assert "legacy/" in gitignore
    assert "private/" not in gitignore

    settings = soft_read_json_file(workspace / ".vscode" / "settings.json")
    assert "multi.private" not in settings


def test_sync_accepts_install_set_flag():
    result = CliRunner().invoke(main, ["sync", "--help"])

    assert result.exit_code == 0
    assert "--install-set" in result.output
    assert "--set" in result.output


def test_install_set_applies_to_partial_sync_commands(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    _write_repo_settings(workspace, "public", "multi.public")
    _write_repo_settings(workspace, "private", "multi.private")
    _write_repo_settings(workspace, "legacy", "multi.legacy")

    monkeypatch.chdir(workspace)
    result = CliRunner().invoke(
        main, ["sync", "--set", "default", "vscode", "settings"]
    )

    assert result.exit_code == 0

    settings = soft_read_json_file(workspace / ".vscode" / "settings.json")
    assert settings["multi.public"] == "public"
    assert settings["multi.legacy"] == "legacy"
    assert "multi.private" not in settings
