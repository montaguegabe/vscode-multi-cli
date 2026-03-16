import json
from pathlib import Path

import git
from click.testing import CliRunner

from multi.cli import main


def test_multi_init_passes_root_dir_to_sync_and_writes_descriptions(monkeypatch):
    runner = CliRunner()
    calls = {}

    def fake_sync(*, root_dir, ensure_on_same_branch):
        calls["root_dir"] = root_dir
        calls["ensure_on_same_branch"] = ensure_on_same_branch
        git.Repo.init(root_dir, initial_branch="main")

    def fake_commit_changes():
        calls["committed"] = True

    monkeypatch.setattr("multi.init.sync", fake_sync)
    monkeypatch.setattr("multi.init.commit_changes", fake_commit_changes)
    monkeypatch.setattr("multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True)

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["init"],
            input=(
                "https://github.com/openbase-community/openbase\n"
                "Old reference implementation.\n"
                "\n"
            ),
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == Path.cwd()
        assert calls["ensure_on_same_branch"] is False
        assert calls["committed"] is True

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {
                    "url": "https://github.com/openbase-community/openbase",
                    "description": "Old reference implementation.",
                }
            ]
        }


def test_multi_init_skips_descriptions_after_first_blank(monkeypatch):
    runner = CliRunner()
    calls = {}

    def fake_sync(*, root_dir, ensure_on_same_branch):
        calls["root_dir"] = root_dir
        calls["ensure_on_same_branch"] = ensure_on_same_branch
        git.Repo.init(root_dir, initial_branch="main")

    monkeypatch.setattr("multi.init.sync", fake_sync)
    monkeypatch.setattr(
        "multi.init.commit_changes",
        lambda: calls.setdefault("committed", True),
    )
    monkeypatch.setattr("multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True)

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["init"],
            input=(
                "https://github.com/example/repo-a\n"
                "\n"
                "https://github.com/example/repo-b\n"
                "\n"
            ),
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == Path.cwd()
        assert calls["ensure_on_same_branch"] is False
        assert calls["committed"] is True

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {"url": "https://github.com/example/repo-a"},
                {"url": "https://github.com/example/repo-b"},
            ]
        }
