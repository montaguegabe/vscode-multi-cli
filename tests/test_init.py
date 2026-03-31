import json
import subprocess
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
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

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
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

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


def test_multi_init_supports_non_interactive_repo_flags(monkeypatch):
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
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            [
                "init",
                "--repo",
                "https://github.com/example/repo-a",
                "--repo-description",
                "Backend API",
                "--repo",
                "https://github.com/example/repo-b",
                "--repo-description",
                "Frontend app",
            ],
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == Path.cwd()
        assert calls["ensure_on_same_branch"] is False
        assert calls["committed"] is True

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {
                    "url": "https://github.com/example/repo-a",
                    "description": "Backend API",
                },
                {
                    "url": "https://github.com/example/repo-b",
                    "description": "Frontend app",
                },
            ]
        }


def test_multi_init_uses_short_local_names_for_workspace_prefixed_repos(monkeypatch):
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
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem(temp_dir="/tmp"):
        workspace = Path.cwd() / "t-ide"
        workspace.mkdir()
        previous_cwd = Path.cwd()
        try:
            import os

            os.chdir(workspace)
            result = runner.invoke(
                main,
                [
                    "init",
                    "--repo",
                    "https://github.com/example/t-ide-extension",
                    "--repo-description",
                    "VS Code extension scaffold for tIDE",
                    "--repo",
                    "https://github.com/example/t-ide-cli",
                    "--repo-description",
                    "Python CLI scaffold for tIDE",
                    "--repo",
                    "https://github.com/example/t-ide-skills",
                    "--repo-description",
                    "skills.sh-compatible skill package for tIDE",
                ],
            )
        finally:
            os.chdir(previous_cwd)

        assert result.exit_code == 0

        config = json.loads((workspace / "multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {
                    "url": "https://github.com/example/t-ide-extension",
                    "name": "extension",
                    "description": "VS Code extension scaffold for tIDE",
                },
                {
                    "url": "https://github.com/example/t-ide-cli",
                    "name": "cli",
                    "description": "Python CLI scaffold for tIDE",
                },
                {
                    "url": "https://github.com/example/t-ide-skills",
                    "name": "skills",
                    "description": "skills.sh-compatible skill package for tIDE",
                },
            ]
        }


def test_multi_init_can_create_github_repos(monkeypatch):
    runner = CliRunner()
    calls = {}

    def fake_sync(*, root_dir, ensure_on_same_branch):
        calls["root_dir"] = root_dir
        calls["ensure_on_same_branch"] = ensure_on_same_branch
        git.Repo.init(root_dir, initial_branch="main")

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls["gh_cmd"] = cmd
        calls["gh_check"] = check
        calls["gh_capture_output"] = capture_output
        calls["gh_text"] = text
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.init.sync", fake_sync)
    monkeypatch.setattr(
        "multi.init.commit_changes",
        lambda: calls.setdefault("committed", True),
    )
    monkeypatch.setattr("multi.init.shutil.which", lambda name: "/opt/homebrew/bin/gh")
    monkeypatch.setattr("multi.init.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            [
                "init",
                "--github-repo",
                "acme/api",
                "--github-description",
                "Private API repo",
                "--github-visibility",
                "private",
                "--github-clone-protocol",
                "ssh",
            ],
        )

        assert result.exit_code == 0
        assert calls["root_dir"] == Path.cwd()
        assert calls["ensure_on_same_branch"] is False
        assert calls["committed"] is True
        assert calls["gh_cmd"] == [
            "/opt/homebrew/bin/gh",
            "repo",
            "create",
            "acme/api",
            "--private",
            "--description",
            "Private API repo",
        ]

        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config == {
            "repos": [
                {
                    "url": "git@github.com:acme/api.git",
                    "description": "Private API repo",
                }
            ]
        }


def test_multi_init_requires_matching_repo_description_counts(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            [
                "init",
                "--repo",
                "https://github.com/example/repo-a",
                "--repo",
                "https://github.com/example/repo-b",
                "--repo-description",
                "Only one description",
            ],
        )

        assert result.exit_code == 1
        assert (
            "--repo-description must be provided exactly once per --repo."
            in result.output
        )
