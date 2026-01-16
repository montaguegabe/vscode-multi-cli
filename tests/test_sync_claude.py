import json

from multi.sync_claude import convert_all_cursor_rules, merge_repo_description_rules


def test_merge_repo_description_rules(setup_git_repos):
    """Test that repo-description.mdc files are merged into a root-level repos-description.mdc."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]  # repo0
    repo1_path = sub_repo_dirs[1]  # repo1

    # Create .cursor/rules directories
    (repo0_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
    (repo1_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
    (root_repo_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)

    # Create repo-description.mdc files in sub-repos
    repo0_description = """---
description: Repo0 description
globs:
alwaysApply: true
---
This is the description for repo0.
It handles user authentication.
"""
    (repo0_path / ".cursor" / "rules" / "repo-description.mdc").write_text(
        repo0_description
    )

    repo1_description = """---
description: Repo1 description
globs:
alwaysApply: true
---
This is the description for repo1.
It handles data storage.
"""
    (repo1_path / ".cursor" / "rules" / "repo-description.mdc").write_text(
        repo1_description
    )

    # Call the merge function
    merge_repo_description_rules(root_repo_path)

    # Check that repos-description.mdc was created in root
    merged_path = root_repo_path / ".cursor" / "rules" / "repos-description.mdc"
    assert merged_path.exists()

    content = merged_path.read_text()

    # Check that both repo descriptions are included with headers
    assert "## repo0" in content
    assert "## repo1" in content
    assert "This is the description for repo0." in content
    assert "It handles user authentication." in content
    assert "This is the description for repo1." in content
    assert "It handles data storage." in content

    # Check that frontmatter is correct
    assert "alwaysApply: true" in content
    assert "Combined repository descriptions" in content


def test_merge_repo_description_rules_single_repo(setup_git_repos):
    """Test merging when only one repo has a repo-description.mdc."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]

    # Create .cursor/rules directory only in repo0
    (repo0_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)

    repo0_description = """---
description:
globs:
alwaysApply: true
---
Single repo description.
"""
    (repo0_path / ".cursor" / "rules" / "repo-description.mdc").write_text(
        repo0_description
    )

    # Call the merge function
    merge_repo_description_rules(root_repo_path)

    # Check that repos-description.mdc was created
    merged_path = root_repo_path / ".cursor" / "rules" / "repos-description.mdc"
    assert merged_path.exists()

    content = merged_path.read_text()
    assert "## repo0" in content
    assert "Single repo description." in content


def test_merge_repo_description_rules_no_files(setup_git_repos):
    """Test that no file is created when there are no repo-description.mdc files."""
    root_repo_path, sub_repo_dirs = setup_git_repos

    # Don't create any repo-description.mdc files
    merge_repo_description_rules(root_repo_path)

    # Check that repos-description.mdc was not created
    merged_path = root_repo_path / ".cursor" / "rules" / "repos-description.mdc"
    assert not merged_path.exists()


def test_convert_all_cursor_rules_merges_descriptions_first(setup_git_repos):
    """Test that convert_all_cursor_rules merges repo descriptions before converting rules."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]

    # Create .cursor/rules directory
    (repo0_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
    (root_repo_path / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)

    # Create repo-description.mdc in sub-repo
    repo0_description = """---
description:
globs:
alwaysApply: true
---
Repo0 handles authentication.
"""
    (repo0_path / ".cursor" / "rules" / "repo-description.mdc").write_text(
        repo0_description
    )

    # Create another rule in root
    root_rule = """---
description: Project conventions
globs:
alwaysApply: true
---
Follow these conventions.
"""
    (root_repo_path / ".cursor" / "rules" / "conventions.mdc").write_text(root_rule)

    # Call convert_all_cursor_rules
    convert_all_cursor_rules(root_repo_path)

    # Check that repos-description.mdc was created (merged from sub-repos)
    merged_descriptions_path = (
        root_repo_path / ".cursor" / "rules" / "repos-description.mdc"
    )
    assert merged_descriptions_path.exists()

    # Check that CLAUDE.md was created in root (includes the merged file)
    claude_md_path = root_repo_path / "CLAUDE.md"
    assert claude_md_path.exists()

    claude_content = claude_md_path.read_text()
    # CLAUDE.md should include content from repos-description.mdc and conventions.mdc
    assert "Repo0 handles authentication." in claude_content
    assert "Follow these conventions." in claude_content
