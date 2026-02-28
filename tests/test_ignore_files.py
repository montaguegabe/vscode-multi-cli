import json

from multi.ignore_files import (
    IgnoreFile,
    remove_gitignore_entries_for_repos,
    remove_ignore_entries_for_repos,
    update_gitignore_with_generated_files,
)
from multi.paths import Paths


def test_add_lines_preserves_existing_content(tmp_path):
    """Test that add_lines_if_missing preserves all existing content."""
    # Create a temporary gitignore with existing content
    ignore_path = tmp_path / ".gitignore"
    existing_content = [
        "# Existing section",
        "*.log",
        "*.tmp",
        "",
        "# Node stuff",
        "node_modules/",
        "package-lock.json",
        "",
        "# Python stuff",
        "__pycache__/",
        "*.pyc",
    ]
    ignore_path.write_text("\n".join(existing_content) + "\n")

    # Initialize IgnoreFile and add new lines
    ignore_file = IgnoreFile(ignore_path)
    new_lines = ["dist/", "build/"]
    ignore_file.add_lines_if_missing(new_lines, "# Build outputs")

    # Read the file and verify all original content is preserved
    updated_content = ignore_file.existing_lines
    for line in existing_content:
        assert line in updated_content

    # Verify new lines were added
    assert "# Build outputs" in updated_content
    assert "dist/" in updated_content
    assert "build/" in updated_content


def test_add_lines_to_existing_section(tmp_path):
    """Test that add_lines_if_missing adds lines under the correct header even with surrounding content."""
    ignore_path = tmp_path / ".gitignore"
    initial_content = [
        "# Top section",
        "*.log",
        "",
        "# Target section",
        "existing_item/",
        "",
        "# Bottom section",
        "*.tmp",
        "temp/",
    ]
    ignore_path.write_text("\n".join(initial_content) + "\n")

    # Add new lines to the middle section
    ignore_file = IgnoreFile(ignore_path)
    new_lines = ["new_item1/", "new_item2/"]
    ignore_file.add_lines_if_missing(new_lines, "# Target section")

    # Verify the structure
    updated_content = ignore_file.existing_lines

    # Check that all sections are preserved
    assert "# Top section" in updated_content
    assert "*.log" in updated_content
    assert "# Target section" in updated_content
    assert "existing_item/" in updated_content
    assert "# Bottom section" in updated_content
    assert "*.tmp" in updated_content
    assert "temp/" in updated_content

    # Check that new items were added in the correct section
    target_section_start = updated_content.index("# Target section")
    bottom_section_start = updated_content.index("# Bottom section")

    # Verify new items are between the target and bottom sections
    section_content = updated_content[target_section_start:bottom_section_start]
    assert "new_item1/" in section_content
    assert "new_item2/" in section_content


def test_update_gitignore_with_generated_files_updates_root_and_subrepos(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "repos": [
                    {"url": "https://github.com/test/repo-a"},
                    {"url": "https://github.com/test/repo-b"},
                ]
            },
            indent=2,
        )
    )

    repo_a = workspace / "repo-a"
    repo_b = workspace / "repo-b"
    (repo_a / ".git").mkdir(parents=True)
    (repo_b / ".git").mkdir(parents=True)

    update_gitignore_with_generated_files(Paths(workspace))

    root_gitignore = (workspace / ".gitignore").read_text()
    assert ".vscode/settings.json" in root_gitignore
    assert ".vscode/tasks.json" in root_gitignore
    assert ".vscode/launch.json" in root_gitignore
    assert ".vscode/extensions.json" in root_gitignore
    assert "CLAUDE.md" in root_gitignore
    assert "AGENTS.md" in root_gitignore

    repo_a_gitignore = (repo_a / ".gitignore").read_text()
    assert "CLAUDE.md" in repo_a_gitignore
    assert "AGENTS.md" in repo_a_gitignore
    assert ".vscode/settings.json" not in repo_a_gitignore

    repo_b_gitignore = (repo_b / ".gitignore").read_text()
    assert "CLAUDE.md" in repo_b_gitignore
    assert "AGENTS.md" in repo_b_gitignore
    assert ".vscode/settings.json" not in repo_b_gitignore


def test_update_gitignore_with_generated_files_skips_non_git_subrepo(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps(
            {
                "repos": [
                    {"url": "https://github.com/test/repo-a"},
                    {"url": "https://github.com/test/repo-b"},
                ]
            },
            indent=2,
        )
    )

    repo_a = workspace / "repo-a"
    repo_b = workspace / "repo-b"
    (repo_a / ".git").mkdir(parents=True)
    repo_b.mkdir(parents=True)

    update_gitignore_with_generated_files(Paths(workspace))

    assert (repo_a / ".gitignore").exists()
    assert not (repo_b / ".gitignore").exists()


def test_remove_lines_removes_exact_matches(tmp_path):
    ignore_path = tmp_path / ".gitignore"
    ignore_path.write_text("repo-a/\nrepo-a\nkeep-me\n", encoding="utf-8")

    ignore_file = IgnoreFile(ignore_path)
    ignore_file.remove_lines(["repo-a/", "repo-a"])

    assert ignore_path.read_text(encoding="utf-8") == "keep-me\n"


def test_remove_repo_entries_from_ignore_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "multi.json").write_text(
        json.dumps({"repos": [{"url": "https://github.com/test/repo-a"}]}, indent=2),
        encoding="utf-8",
    )
    (workspace / ".gitignore").write_text(
        "repo-a/\nrepo-a\nother/\n",
        encoding="utf-8",
    )
    (workspace / ".ignore").write_text(
        "!repo-a/\n!repo-a\n!other/\n",
        encoding="utf-8",
    )

    paths = Paths(workspace)
    remove_gitignore_entries_for_repos(paths, ["repo-a"])
    remove_ignore_entries_for_repos(paths, ["repo-a"])

    assert (workspace / ".gitignore").read_text(encoding="utf-8") == "other/\n"
    assert (workspace / ".ignore").read_text(encoding="utf-8") == "!other/\n"
