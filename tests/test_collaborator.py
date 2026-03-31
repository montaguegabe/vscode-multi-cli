import json
import subprocess
from pathlib import Path

from click.testing import CliRunner

from multi.cli import main


def _write_workspace_config() -> None:
    Path("multi.json").write_text(
        json.dumps(
            {
                "repos": [
                    {
                        "url": "https://github.com/example/t-ide-cli",
                        "name": "cli",
                    },
                    {
                        "url": "git@github.com:example/t-ide-extension",
                        "name": "extension",
                    },
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_collaborator_add_uses_gh_api_for_all_subrepos(monkeypatch):
    runner = CliRunner()
    calls: list[list[str]] = []

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()

        result = runner.invoke(
            main,
            [
                "collaborator",
                "add",
                "octocat",
                "--permission",
                "maintain",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            ["gh", "api", "--method", "GET", "users/octocat"],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-cli/collaborators/octocat",
                "-f",
                "permission=maintain",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-extension/collaborators/octocat",
                "-f",
                "permission=maintain",
            ],
        ]


def test_collaborator_remove_uses_gh_api_for_all_subrepos(monkeypatch):
    runner = CliRunner()
    calls: list[list[str]] = []

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()

        result = runner.invoke(
            main,
            [
                "collaborator",
                "remove",
                "octocat",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            ["gh", "api", "--method", "GET", "users/octocat"],
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                "repos/example/t-ide-cli/collaborators/octocat",
            ],
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                "repos/example/t-ide-extension/collaborators/octocat",
            ],
        ]
