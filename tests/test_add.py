import json
from pathlib import Path

import git
from click.testing import CliRunner

from multi.cli import main


def test_multi_add_uses_short_local_name_for_workspace_prefixed_repo(monkeypatch):
    runner = CliRunner()
    calls = {}

    def fake_sync(*, root_dir, ensure_on_same_branch=True):
        calls["root_dir"] = root_dir
        calls["ensure_on_same_branch"] = ensure_on_same_branch
        git.Repo.init(root_dir, initial_branch="main")

    monkeypatch.setattr("multi.add.sync", fake_sync)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem(temp_dir="/tmp"):
        workspace = Path.cwd() / "t-ide-workspace"
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        Path("multi.json").write_text('{"repos": []}\n', encoding="utf-8")

        result = runner.invoke(
            main,
            ["add", "https://github.com/example/t-ide-cli"],
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == workspace

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {
                    "url": "https://github.com/example/t-ide-cli",
                    "name": "cli",
                }
            ]
        }


def test_multi_add_falls_back_to_full_slug_when_short_name_conflicts(monkeypatch):
    runner = CliRunner()
    calls = {}

    def fake_sync(*, root_dir, ensure_on_same_branch=True):
        calls["root_dir"] = root_dir
        calls["ensure_on_same_branch"] = ensure_on_same_branch
        git.Repo.init(root_dir, initial_branch="main")

    monkeypatch.setattr("multi.add.sync", fake_sync)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem(temp_dir="/tmp"):
        workspace = Path.cwd() / "openbase-coder-workspace"
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        Path("multi.json").write_text(
            '{"repos": [{"url": "https://github.com/example/agent"}]}\n',
            encoding="utf-8",
        )

        result = runner.invoke(
            main,
            ["add", "https://github.com/example/openbase-coder-agent"],
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == workspace

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {"url": "https://github.com/example/agent"},
                {"url": "https://github.com/example/openbase-coder-agent"},
            ]
        }
