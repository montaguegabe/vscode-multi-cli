import json
from pathlib import Path

from click.testing import CliRunner

from multi.convert_monorepo import convert_monorepo_cmd
from multi.ignore_files import REPO_DIRECTORIES_BLOCK, SEARCHABLE_REPOS_BLOCK


def _write_multi_json(*, mono_repo: bool) -> None:
    config = {
        "monoRepo": mono_repo,
        "repos": [
            {"url": "https://github.com/example/repo-a"},
            {"url": "https://github.com/example/repo-b"},
        ],
    }
    Path("multi.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def test_convert_monorepo_requires_confirm():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_multi_json(mono_repo=False)
        (Path("repo-a") / ".git").mkdir(parents=True)

        result = runner.invoke(convert_monorepo_cmd)

        assert result.exit_code != 0
        assert "--confirm" in result.output
        assert (Path("repo-a") / ".git").exists()
        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config["monoRepo"] is False


def test_convert_monorepo_converts_workspace_and_cleans_ignore_entries():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_multi_json(mono_repo=False)
        (Path("repo-a") / ".git").mkdir(parents=True)
        Path("repo-b").mkdir(parents=True)
        (Path("repo-b") / ".git").write_text(
            "gitdir: /tmp/repo-b.git\n",
            encoding="utf-8",
        )
        Path(".gitignore").write_text("repo-a/\nrepo-a\nrepo-b/\nrepo-b\nkeep/\n")
        Path(".ignore").write_text("!repo-a/\n!repo-a\n!repo-b/\n!repo-b\n!keep/\n")

        result = runner.invoke(convert_monorepo_cmd, ["--confirm"])

        assert result.exit_code == 0
        config = json.loads(Path("multi.json").read_text(encoding="utf-8"))
        assert config["monoRepo"] is True
        assert not (Path("repo-a") / ".git").exists()
        assert not (Path("repo-b") / ".git").exists()
        gitignore = Path(".gitignore").read_text(encoding="utf-8")
        ignore = Path(".ignore").read_text(encoding="utf-8")
        assert "keep/" in gitignore
        assert "repo-a/" not in gitignore
        assert REPO_DIRECTORIES_BLOCK.begin_marker not in gitignore
        assert "!keep/" in ignore
        assert "!repo-a/" not in ignore
        assert SEARCHABLE_REPOS_BLOCK.begin_marker not in ignore


def test_convert_monorepo_fails_if_already_monorepo():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_multi_json(mono_repo=True)

        result = runner.invoke(convert_monorepo_cmd, ["--confirm"])

        assert result.exit_code != 0
        assert "already in monorepo mode" in result.output.lower()
