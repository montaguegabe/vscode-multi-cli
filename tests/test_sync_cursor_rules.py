import os
from pathlib import Path

from cursor_multi.paths import paths
from cursor_multi.repos import Repository
from cursor_multi.rules import Rule
from cursor_multi.sync_cursor_rules import sync_cursor_rules


# Helper function to create a rule file in a sub-repo
def create_rule_file(
    repo_path: Path, rule_name: str, content: str, repo_name: str = ""
):
    if not repo_name:
        repo_name = repo_path.name
    cursor_dir = repo_path / ".cursor"
    rules_dir = cursor_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / rule_name).write_text(content)
    return Repository(name=repo_name, path=repo_path, url="")


# Helper function to create rule content string
def create_rule_content(
    description: str,
    globs: list[str] | None = None,
    always_apply: bool = False,
    body: str = "Rule body.",
) -> str:
    rule = Rule(
        description=description, globs=globs, alwaysApply=always_apply, body=body
    )
    return rule.render()


def test_basic_rule_import(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo_path = sub_repo_paths[0]
    sub_repo_name = sub_repo_path.name

    rule_name = "test_rule.mdc"
    rule_description = "A basic test rule"
    original_globs = ["src/*.py", "tests/*.py"]
    rule_body = "This is the body of the basic test rule."
    rule_content = create_rule_content(
        description=rule_description, globs=original_globs, body=rule_body
    )
    create_rule_file(sub_repo_path, rule_name, rule_content, repo_name=sub_repo_name)

    sync_cursor_rules()

    # 1. Check if the rule file was copied to the root rules directory
    imported_rule_path = paths.root_rules_dir / rule_name
    assert imported_rule_path.exists()

    # 2. Check the content of the imported rule
    imported_rule = Rule.parse(imported_rule_path.read_text())
    assert imported_rule is not None
    assert imported_rule.description == rule_description
    assert imported_rule.body.strip() == rule_body.strip()

    expected_globs = [f"{sub_repo_name}/{g}" for g in original_globs]
    assert imported_rule.globs is not None
    assert sorted(imported_rule.globs) == sorted(expected_globs)
    assert not imported_rule.alwaysApply

    # 3. Check .importedrules file
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = [line.strip() for line in f.readlines() if line.strip()]
    assert rule_name in imported_rules_list

    # 4. Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    assert f"/{paths.root_rules_dir.name}/{rule_name}" in gitignore_content


def test_always_apply_rule_import(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo_path = sub_repo_paths[0]
    sub_repo_name = sub_repo_path.name

    rule_name = "always_apply_rule.mdc"
    rule_description = "An always apply test rule"
    rule_body = "This rule should apply to the whole repo."
    rule_content = create_rule_content(
        description=rule_description, always_apply=True, body=rule_body
    )
    create_rule_file(sub_repo_path, rule_name, rule_content, repo_name=sub_repo_name)

    sync_cursor_rules()

    imported_rule_path = paths.root_rules_dir / rule_name
    assert imported_rule_path.exists()

    imported_rule = Rule.parse(imported_rule_path.read_text())
    assert imported_rule is not None
    assert imported_rule.description == rule_description
    assert imported_rule.body.strip() == rule_body.strip()

    assert not imported_rule.alwaysApply  # Should be false after import
    expected_globs = [f"{sub_repo_name}/**/*"]
    assert imported_rule.globs is not None
    assert sorted(imported_rule.globs) == sorted(expected_globs)

    # Check .importedrules file
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = [line.strip() for line in f.readlines() if line.strip()]
    assert rule_name in imported_rules_list

    # Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    assert f"/{paths.root_rules_dir.name}/{rule_name}" in gitignore_content


def test_agent_requested_rule_import(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo_path = sub_repo_paths[0]
    sub_repo_name = sub_repo_path.name

    rule_name = "agent_rule.mdc"
    rule_description = "An agent requested rule"
    rule_body = "This is an agent rule, content should be preserved."
    # Create rule content with no globs and no always_apply
    original_content = create_rule_content(
        description=rule_description, body=rule_body, globs=None, always_apply=False
    )
    create_rule_file(
        sub_repo_path, rule_name, original_content, repo_name=sub_repo_name
    )

    sync_cursor_rules()

    imported_rule_path = paths.root_rules_dir / rule_name
    assert imported_rule_path.exists()

    imported_rule_content = imported_rule_path.read_text()
    # For agent rules, the content should be exactly the same
    assert imported_rule_content.strip() == original_content.strip()

    # Parse to double check specific fields if necessary, though direct string comparison is strong
    imported_rule = Rule.parse(imported_rule_content)
    assert imported_rule is not None
    assert imported_rule.description == rule_description
    assert imported_rule.body.strip() == rule_body.strip()
    assert imported_rule.globs is None
    assert not imported_rule.alwaysApply

    # Check .importedrules file
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = [line.strip() for line in f.readlines() if line.strip()]
    assert rule_name in imported_rules_list

    # Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    assert f"/{paths.root_rules_dir.name}/{rule_name}" in gitignore_content


def test_conflict_identical_content_merge_globs(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo_path1, sub_repo_path2 = sub_repo_paths[0], sub_repo_paths[1]
    sub_repo_name1, sub_repo_name2 = sub_repo_path1.name, sub_repo_path2.name

    rule_name = "common_rule.mdc"
    rule_description = "A common rule with identical content"
    rule_body = "This body is the same in both repos."
    globs1 = ["src/app1/*.py"]
    globs2 = ["src/app2/*.js"]

    content1 = create_rule_content(
        description=rule_description, globs=globs1, body=rule_body
    )
    content2 = create_rule_content(
        description=rule_description, globs=globs2, body=rule_body
    )

    create_rule_file(sub_repo_path1, rule_name, content1, repo_name=sub_repo_name1)
    create_rule_file(sub_repo_path2, rule_name, content2, repo_name=sub_repo_name2)

    sync_cursor_rules()

    # 1. Check that only one rule file was created (original name)
    imported_rule_path = paths.root_rules_dir / rule_name
    assert imported_rule_path.exists()

    # Check that suffixed files were NOT created
    name_part, ext_part = os.path.splitext(rule_name)
    suffixed_rule_path1 = (
        paths.root_rules_dir / f"{name_part}-{sub_repo_name1}{ext_part}"
    )
    suffixed_rule_path2 = (
        paths.root_rules_dir / f"{name_part}-{sub_repo_name2}{ext_part}"
    )
    assert not suffixed_rule_path1.exists()
    assert not suffixed_rule_path2.exists()

    # 2. Check the content of the merged rule
    merged_rule = Rule.parse(imported_rule_path.read_text())
    assert merged_rule is not None
    assert merged_rule.description == rule_description
    assert merged_rule.body.strip() == rule_body.strip()

    expected_globs = sorted(
        [f"{sub_repo_name1}/{g}" for g in globs1]
        + [f"{sub_repo_name2}/{g}" for g in globs2]
    )
    assert merged_rule.globs is not None
    assert sorted(merged_rule.globs) == expected_globs
    assert not merged_rule.alwaysApply

    # 3. Check .importedrules file - should list the single merged rule name
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = [line.strip() for line in f.readlines() if line.strip()]
    assert rule_name in imported_rules_list
    assert len(imported_rules_list) == 1  # Ensure only one entry for the merged rule

    # 4. Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    assert f"/{paths.root_rules_dir.name}/{rule_name}" in gitignore_content


def test_conflict_different_content_suffix_filenames(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    sub_repo_path1, sub_repo_path2 = sub_repo_paths[0], sub_repo_paths[1]
    sub_repo_name1, sub_repo_name2 = sub_repo_path1.name, sub_repo_path2.name

    rule_name = "conflicting_rule.mdc"
    description1 = "Rule from repo1"
    globs1 = ["*.py"]
    body1 = "This is content from repo1."
    content1 = create_rule_content(description=description1, globs=globs1, body=body1)

    description2 = "Rule from repo2"
    globs2 = ["*.js"]
    body2 = "This is different content from repo2."
    content2 = create_rule_content(description=description2, globs=globs2, body=body2)

    create_rule_file(sub_repo_path1, rule_name, content1, repo_name=sub_repo_name1)
    create_rule_file(sub_repo_path2, rule_name, content2, repo_name=sub_repo_name2)

    sync_cursor_rules()

    original_rule_path = paths.root_rules_dir / rule_name
    assert not original_rule_path.exists()  # Original name should not exist

    name_part, ext_part = os.path.splitext(rule_name)
    suffixed_rule_name1 = f"{name_part}-{sub_repo_name1}{ext_part}"
    suffixed_rule_name2 = f"{name_part}-{sub_repo_name2}{ext_part}"

    imported_rule_path1 = paths.root_rules_dir / suffixed_rule_name1
    imported_rule_path2 = paths.root_rules_dir / suffixed_rule_name2

    assert imported_rule_path1.exists()
    assert imported_rule_path2.exists()

    # Check content of first suffixed rule
    rule1_imported = Rule.parse(imported_rule_path1.read_text())
    assert rule1_imported is not None
    assert rule1_imported.description == description1
    assert rule1_imported.body.strip() == body1.strip()
    expected_globs1 = [f"{sub_repo_name1}/{g}" for g in globs1]
    assert rule1_imported.globs is not None
    assert sorted(rule1_imported.globs) == sorted(expected_globs1)

    # Check content of second suffixed rule
    rule2_imported = Rule.parse(imported_rule_path2.read_text())
    assert rule2_imported is not None
    assert rule2_imported.description == description2
    assert rule2_imported.body.strip() == body2.strip()
    expected_globs2 = [f"{sub_repo_name2}/{g}" for g in globs2]
    assert rule2_imported.globs is not None
    assert sorted(rule2_imported.globs) == sorted(expected_globs2)

    # Check .importedrules file
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = sorted(
            [line.strip() for line in f.readlines() if line.strip()]
        )
    expected_imported_rules = sorted([suffixed_rule_name1, suffixed_rule_name2])
    assert imported_rules_list == expected_imported_rules

    # Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    assert f"/{paths.root_rules_dir.name}/{suffixed_rule_name1}" in gitignore_content
    assert f"/{paths.root_rules_dir.name}/{suffixed_rule_name2}" in gitignore_content


def test_cleanup_old_imported_rules(setup_git_repos):
    root_repo_path, _ = setup_git_repos  # We don't need sub_repo_paths for this test

    # Ensure root rules dir exists (it should due to autouse fixture, but being explicit)
    paths.root_rules_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create dummy old imported rule files
    old_rule_name1 = "old_rule_to_delete.mdc"
    old_rule_name2 = "another_old_one.mdc"
    dummy_content = "---\ndescription: Old rule\n---\nBody"

    (paths.root_rules_dir / old_rule_name1).write_text(dummy_content)
    (paths.root_rules_dir / old_rule_name2).write_text(dummy_content)

    # 2. Create a .importedrules file listing these dummy rules
    with paths.imported_rules_path.open("w") as f:
        f.write(f"{old_rule_name1}\n")
        f.write(f"{old_rule_name2}\n")

    assert (paths.root_rules_dir / old_rule_name1).exists()
    assert (paths.root_rules_dir / old_rule_name2).exists()
    assert paths.imported_rules_path.exists()

    # 3. Call the main function (which includes cleanup)
    # No sub-repos will contribute new rules, so we just test cleanup
    sync_cursor_rules()

    # 4. Assert dummy rule files are deleted
    assert not (paths.root_rules_dir / old_rule_name1).exists()
    assert not (paths.root_rules_dir / old_rule_name2).exists()

    # 5. Assert .importedrules file is deleted (or empty if it's recreated empty)
    # The current implementation deletes and then recreates it, possibly empty.
    # If no new rules are imported, it should be recreated empty or just deleted.
    # The `track_imported_rules` function will create it if imported_rules list is not empty.
    # If it's empty, it will create an empty file. So we check for existence and empty content.
    assert paths.imported_rules_path.exists()  # It gets recreated
    with paths.imported_rules_path.open("r") as f:
        content = f.read().strip()
        assert content == ""  # Should be empty as no new rules were tracked

    # .gitignore should also be updated (or created if it wasn't there)
    # and should not contain the old rules. Since no new rules, it might just be empty or have header.
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
        assert old_rule_name1 not in gitignore_content
        assert old_rule_name2 not in gitignore_content


def test_mixed_scenario_e2e(setup_git_repos):
    root_repo_path, sub_repo_paths = setup_git_repos
    # We need at least 2 sub-repos for conflict scenarios from conftest.py
    # If conftest provides more, that's fine. We'll use the first two primarily.
    repo1_path, repo2_path = sub_repo_paths[0], sub_repo_paths[1]
    repo1_name, repo2_name = repo1_path.name, repo2_path.name

    # Rule 1: Basic rule in repo1
    basic_rule_name = "basic.mdc"
    basic_desc = "Basic rule from repo1"
    basic_globs = ["*.txt"]
    basic_body = "Basic body"
    create_rule_file(
        repo1_path,
        basic_rule_name,
        create_rule_content(description=basic_desc, globs=basic_globs, body=basic_body),
        repo_name=repo1_name,
    )

    # Rule 2: alwaysApply rule in repo2
    always_apply_name = "always.mdc"
    always_apply_desc = "Always apply from repo2"
    always_apply_body = "Always body"
    create_rule_file(
        repo2_path,
        always_apply_name,
        create_rule_content(
            description=always_apply_desc, always_apply=True, body=always_apply_body
        ),
        repo_name=repo2_name,
    )

    # Rule 3: Conflict - Identical Content (rule_ident.mdc)
    ident_conflict_name = "ident_conflict.mdc"
    ident_desc = "Identical conflict rule"
    ident_body = "Identical body for merging"
    ident_globs1 = ["app1/*"]
    ident_globs2 = ["app2/*"]
    create_rule_file(
        repo1_path,
        ident_conflict_name,
        create_rule_content(
            description=ident_desc, globs=ident_globs1, body=ident_body
        ),
        repo_name=repo1_name,
    )
    create_rule_file(
        repo2_path,
        ident_conflict_name,
        create_rule_content(
            description=ident_desc, globs=ident_globs2, body=ident_body
        ),
        repo_name=repo2_name,
    )

    # Rule 4: Conflict - Different Content (rule_diff.mdc)
    diff_conflict_name = "diff_conflict.mdc"
    diff_desc1 = "Diff conflict from repo1"
    diff_body1 = "Diff body from repo1"
    diff_globs1 = ["styles1/*.css"]
    diff_desc2 = "Diff conflict from repo2"
    diff_body2 = "Diff body from repo2 - different!"
    diff_globs2 = ["styles2/*.css"]
    create_rule_file(
        repo1_path,
        diff_conflict_name,
        create_rule_content(description=diff_desc1, globs=diff_globs1, body=diff_body1),
        repo_name=repo1_name,
    )
    create_rule_file(
        repo2_path,
        diff_conflict_name,
        create_rule_content(description=diff_desc2, globs=diff_globs2, body=diff_body2),
        repo_name=repo2_name,
    )

    # Rule 5: Agent rule in repo1
    agent_rule_name = "agent_specific.mdc"
    agent_desc = "Agent rule from repo1"
    agent_body = "Agent body, no globs no always."
    create_rule_file(
        repo1_path,
        agent_rule_name,
        create_rule_content(
            description=agent_desc, body=agent_body, globs=None, always_apply=False
        ),
        repo_name=repo1_name,
    )

    # --- Execute ---
    sync_cursor_rules()

    # --- Assertions ---
    # 1. Basic rule
    imported_basic_path = paths.root_rules_dir / basic_rule_name
    assert imported_basic_path.exists()
    basic_imported = Rule.parse(imported_basic_path.read_text())
    assert basic_imported is not None
    assert basic_imported.description == basic_desc
    assert basic_imported.globs is not None
    assert sorted(basic_imported.globs) == sorted(
        [f"{repo1_name}/{g}" for g in basic_globs]
    )

    # 2. Always apply rule
    imported_always_path = paths.root_rules_dir / always_apply_name
    assert imported_always_path.exists()
    always_imported = Rule.parse(imported_always_path.read_text())
    assert always_imported is not None
    assert always_imported.description == always_apply_desc
    assert not always_imported.alwaysApply
    assert always_imported.globs is not None
    assert sorted(always_imported.globs) == sorted([f"{repo2_name}/**/*"])

    # 3. Identical conflict rule (merged)
    imported_ident_path = paths.root_rules_dir / ident_conflict_name
    assert imported_ident_path.exists()
    ident_imported = Rule.parse(imported_ident_path.read_text())
    assert ident_imported is not None
    assert ident_imported.description == ident_desc
    expected_ident_globs = sorted(
        [f"{repo1_name}/{g}" for g in ident_globs1]
        + [f"{repo2_name}/{g}" for g in ident_globs2]
    )
    assert ident_imported.globs is not None
    assert sorted(ident_imported.globs) == expected_ident_globs

    # 4. Different conflict rules (suffixed)
    name_part_diff, ext_part_diff = os.path.splitext(diff_conflict_name)
    suffixed_diff_name1 = f"{name_part_diff}-{repo1_name}{ext_part_diff}"
    suffixed_diff_name2 = f"{name_part_diff}-{repo2_name}{ext_part_diff}"
    imported_diff_path1 = paths.root_rules_dir / suffixed_diff_name1
    imported_diff_path2 = paths.root_rules_dir / suffixed_diff_name2
    assert imported_diff_path1.exists()
    assert imported_diff_path2.exists()

    diff1_imported = Rule.parse(imported_diff_path1.read_text())
    assert diff1_imported is not None
    assert diff1_imported.description == diff_desc1
    assert diff1_imported.globs is not None
    assert sorted(diff1_imported.globs) == sorted(
        [f"{repo1_name}/{g}" for g in diff_globs1]
    )

    diff2_imported = Rule.parse(imported_diff_path2.read_text())
    assert diff2_imported is not None
    assert diff2_imported.description == diff_desc2
    assert diff2_imported.globs is not None
    assert sorted(diff2_imported.globs) == sorted(
        [f"{repo2_name}/{g}" for g in diff_globs2]
    )

    # 5. Agent rule
    imported_agent_path = paths.root_rules_dir / agent_rule_name
    assert imported_agent_path.exists()
    agent_imported = Rule.parse(imported_agent_path.read_text())
    assert agent_imported is not None
    assert agent_imported.description == agent_desc
    assert agent_imported.globs is None
    assert not agent_imported.alwaysApply
    assert agent_imported.body.strip() == agent_body.strip()

    # Check .importedrules file
    assert paths.imported_rules_path.exists()
    with paths.imported_rules_path.open("r") as f:
        imported_rules_list = sorted(
            [line.strip() for line in f.readlines() if line.strip()]
        )

    expected_tracked_rules = sorted(
        [
            basic_rule_name,
            always_apply_name,
            ident_conflict_name,
            suffixed_diff_name1,
            suffixed_diff_name2,
            agent_rule_name,
        ]
    )
    assert imported_rules_list == expected_tracked_rules

    # Check .gitignore file
    gitignore_path = root_repo_path / ".gitignore"
    assert gitignore_path.exists()
    with gitignore_path.open("r") as f:
        gitignore_content = f.read()
    for rule_file in expected_tracked_rules:
        assert f"/{paths.root_rules_dir.name}/{rule_file}" in gitignore_content
