import json

from click.testing import CliRunner

from multi.cli import main
from multi.sync_agents import sync_all_agents


def test_agents_generation_disabled_leaves_manual_files_untouched(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps({"repos": [{"url": "https://github.com/test/repo-a"}]}),
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text("Manual agents\n", encoding="utf-8")
    (workspace / "CLAUDE.md").write_text("Manual claude\n", encoding="utf-8")
    (workspace / "AGENTS.parts").mkdir()
    (workspace / "AGENTS.parts" / "base.md").write_text(
        "Generated agents\n",
        encoding="utf-8",
    )

    sync_all_agents(workspace)

    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "Manual agents\n"
    assert (workspace / "CLAUDE.md").read_text(encoding="utf-8") == "Manual claude\n"


def test_agents_generation_concatenates_parts_in_sorted_order(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "agentInstructions": {
                    "enabled": True,
                    "includeRepoDescriptions": False,
                },
                "repos": [{"url": "https://github.com/test/repo-a"}],
            }
        ),
        encoding="utf-8",
    )
    parts_dir = workspace / "AGENTS.parts"
    parts_dir.mkdir()
    (parts_dir / "20-second.md").write_text("Second\n", encoding="utf-8")
    (parts_dir / "10-first.md").write_text("First\n", encoding="utf-8")

    sync_all_agents(workspace)

    expected = "First\n\nSecond\n"
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == expected
    assert (workspace / "CLAUDE.md").read_text(encoding="utf-8") == expected


def test_agents_generation_prepends_root_repo_descriptions(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "agentInstructions": {"enabled": True},
                "repos": [
                    {
                        "url": "https://github.com/test/repo-a",
                        "description": "Backend API",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    sync_all_agents(workspace)

    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == (
        "This workspace contains multiple repositories:\n\n- `repo-a`: Backend API\n"
    )


def test_agents_generation_skips_empty_parts_without_deleting_manual_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "agentInstructions": {
                    "enabled": True,
                    "includeRepoDescriptions": False,
                },
                "repos": [{"url": "https://github.com/test/repo-a"}],
            }
        ),
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text("Manual agents\n", encoding="utf-8")
    (workspace / "CLAUDE.md").write_text("Manual claude\n", encoding="utf-8")

    sync_all_agents(workspace)

    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "Manual agents\n"
    assert (workspace / "CLAUDE.md").read_text(encoding="utf-8") == "Manual claude\n"


def test_agents_generation_writes_subrepo_outputs(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "agentInstructions": {"enabled": True},
                "repos": [{"url": "https://github.com/test/repo-a"}],
            }
        ),
        encoding="utf-8",
    )
    repo_a = workspace / "repo-a"
    parts_dir = repo_a / "AGENTS.parts"
    parts_dir.mkdir(parents=True)
    (parts_dir / "base.md").write_text("Repo instructions\n", encoding="utf-8")

    sync_all_agents(workspace)

    assert (repo_a / "AGENTS.md").read_text(encoding="utf-8") == ("Repo instructions\n")
    assert (repo_a / "CLAUDE.md").read_text(encoding="utf-8") == ("Repo instructions\n")


def test_sync_agents_command_updates_gitignore_for_generated_outputs(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "agentInstructions": {
                    "enabled": True,
                    "includeRepoDescriptions": False,
                },
                "repos": [{"url": "https://github.com/test/repo-a"}],
            }
        ),
        encoding="utf-8",
    )
    parts_dir = workspace / "AGENTS.parts"
    parts_dir.mkdir()
    (parts_dir / "base.md").write_text("Root instructions\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = CliRunner().invoke(
        main,
        ["sync", "agents"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == (
        "Root instructions\n"
    )
    gitignore = (workspace / ".gitignore").read_text(encoding="utf-8")
    assert "AGENTS.md" in gitignore
    assert "CLAUDE.md" in gitignore
