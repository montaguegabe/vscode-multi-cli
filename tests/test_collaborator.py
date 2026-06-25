import json
import subprocess
from pathlib import Path

import git
import pytest
from click.testing import CliRunner

from multi import collaborator
from multi.cli import main


@pytest.fixture(autouse=True)
def recent_github_users_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "multi.collaborator.RECENT_GITHUB_USERS_FILE",
        tmp_path / "recent-github-users.json",
    )


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


def _init_workspace_root_repo() -> None:
    repo = git.Repo.init(Path.cwd(), initial_branch="main")
    repo.create_remote("origin", "https://github.com/example/t-ide-workspace")


def test_collaborator_add_uses_gh_api_for_workspace_and_all_subrepos(monkeypatch):
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
        _init_workspace_root_repo()

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
                "repos/example/t-ide-workspace/collaborators/octocat",
                "-f",
                "permission=maintain",
            ],
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


def test_collaborator_remove_uses_gh_api_for_workspace_and_all_subrepos(monkeypatch):
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
        _init_workspace_root_repo()

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
                "repos/example/t-ide-workspace/collaborators/octocat",
            ],
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


def test_collaborator_skips_workspace_root_without_github_origin(monkeypatch):
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
        git.Repo.init(Path.cwd(), initial_branch="main")

        result = runner.invoke(
            main,
            [
                "collaborator",
                "add",
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
                "PUT",
                "repos/example/t-ide-cli/collaborators/octocat",
                "-f",
                "permission=push",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-extension/collaborators/octocat",
                "-f",
                "permission=push",
            ],
        ]


def test_collaborator_accept_uses_gh_api_for_matching_workspace_invitations(
    monkeypatch,
):
    runner = CliRunner()
    calls: list[list[str]] = []

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls.append(cmd)
        if cmd[:4] == [
            "gh",
            "api",
            "--method",
            "GET",
        ]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(
                    [
                        [
                            {
                                "id": 101,
                                "repository": {
                                    "full_name": "example/t-ide-workspace",
                                },
                            },
                            {
                                "id": 102,
                                "repository": {
                                    "full_name": "example/t-ide-cli",
                                },
                            },
                        ],
                        [
                            {
                                "id": 103,
                                "repository": {
                                    "full_name": "elsewhere/unrelated",
                                },
                            },
                        ],
                    ]
                ),
                stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()
        _init_workspace_root_repo()

        result = runner.invoke(
            main,
            [
                "collaborator",
                "accept",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            [
                "gh",
                "api",
                "--method",
                "GET",
                "user/repository_invitations?per_page=100",
                "--paginate",
                "--slurp",
            ],
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                "user/repository_invitations/101",
            ],
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                "user/repository_invitations/102",
            ],
        ]


def test_collaborator_accept_reports_no_matching_pending_invitations(monkeypatch):
    runner = CliRunner()
    calls: list[list[str]] = []

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls.append(cmd)
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps(
                [
                    {
                        "id": 101,
                        "repository": {
                            "full_name": "elsewhere/unrelated",
                        },
                    }
                ]
            ),
            stderr="",
        )

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()
        _init_workspace_root_repo()

        result = runner.invoke(
            main,
            [
                "collaborator",
                "accept",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert result.output == (
            "No pending repository invitations found for this workspace.\n"
        )
        assert calls == [
            [
                "gh",
                "api",
                "--method",
                "GET",
                "user/repository_invitations?per_page=100",
                "--paginate",
                "--slurp",
            ],
        ]


def test_collaborator_continues_after_repo_failure(monkeypatch):
    runner = CliRunner()
    calls: list[list[str]] = []

    def fake_subprocess_run(cmd, check, capture_output, text):
        calls.append(cmd)
        if "repos/example/t-ide-cli/collaborators/octocat" in cmd:
            raise subprocess.CalledProcessError(
                1,
                cmd,
                output="",
                stderr="gh: Not Found (HTTP 404)",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()
        _init_workspace_root_repo()

        result = runner.invoke(
            main,
            [
                "collaborator",
                "add",
                "octocat",
                "--yes",
            ],
        )

        assert result.exit_code == 1
        assert "Finished add collaborator octocat with failures:" in result.output
        assert "- example/t-ide-cli: gh: Not Found (HTTP 404)" in result.output
        assert calls == [
            ["gh", "api", "--method", "GET", "users/octocat"],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-workspace/collaborators/octocat",
                "-f",
                "permission=push",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-cli/collaborators/octocat",
                "-f",
                "permission=push",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-extension/collaborators/octocat",
                "-f",
                "permission=push",
            ],
        ]


def test_collaborator_add_records_recent_github_username(monkeypatch):
    runner = CliRunner()

    def fake_subprocess_run(cmd, check, capture_output, text):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()
        _init_workspace_root_repo()
        collaborator._save_recent_github_usernames(["hubot"])

        result = runner.invoke(
            main,
            [
                "collaborator",
                "add",
                "octocat",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert collaborator._load_recent_github_usernames() == ["octocat", "hubot"]


def test_collaborator_remove_records_recent_github_username(monkeypatch):
    runner = CliRunner()

    def fake_subprocess_run(cmd, check, capture_output, text):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("multi.collaborator.shutil.which", lambda name: "gh")
    monkeypatch.setattr("multi.collaborator.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", lambda **kwargs: True
    )

    with runner.isolated_filesystem():
        _write_workspace_config()
        _init_workspace_root_repo()

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
        assert collaborator._load_recent_github_usernames() == ["octocat"]


def test_collaborator_add_without_username_prompts_for_recent_user(monkeypatch):
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
        _init_workspace_root_repo()
        collaborator._save_recent_github_usernames(["octocat", "hubot"])

        result = runner.invoke(
            main,
            [
                "collaborator",
                "add",
                "--yes",
            ],
            input="2\n",
        )

        assert result.exit_code == 0
        assert "Recent GitHub users:" in result.output
        assert "1. octocat" in result.output
        assert "2. hubot" in result.output
        assert calls == [
            ["gh", "api", "--method", "GET", "users/hubot"],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-workspace/collaborators/hubot",
                "-f",
                "permission=push",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-cli/collaborators/hubot",
                "-f",
                "permission=push",
            ],
            [
                "gh",
                "api",
                "--method",
                "PUT",
                "repos/example/t-ide-extension/collaborators/hubot",
                "-f",
                "permission=push",
            ],
        ]
        assert collaborator._load_recent_github_usernames() == ["hubot", "octocat"]


def test_collaborator_recent_users_lists_recent_usernames():
    runner = CliRunner()
    collaborator._save_recent_github_usernames(["octocat", "hubot"])

    result = runner.invoke(main, ["collaborator", "recent-users"])

    assert result.exit_code == 0
    assert result.output == "octocat\nhubot\n"
