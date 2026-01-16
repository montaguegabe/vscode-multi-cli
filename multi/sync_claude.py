import logging
from pathlib import Path
from typing import List, Tuple

import click

from multi.paths import Paths
from multi.repos import load_repos
from multi.rules import Rule

logger = logging.getLogger(__name__)


def merge_repo_description_rules(root_dir: Path) -> None:
    """Merge all repo-description.mdc files from sub-repos into a root-level repos-description.mdc.

    This creates a combined rule file at .cursor/rules/repos-description.mdc that contains
    descriptions from all repositories, with each repo's description prefixed by its name.
    """
    paths = Paths(root_dir)
    repos = load_repos(paths=paths)

    # Collect all repo description rules
    repo_descriptions: List[Tuple[str, Rule]] = []

    for repo in repos:
        repo_description_path = paths.get_cursor_rules_dir(repo.path) / "repo-description.mdc"
        if repo_description_path.exists():
            try:
                content = repo_description_path.read_text(encoding="utf-8")
                rule = Rule.parse(content)
                repo_descriptions.append((repo.name, rule))
                logger.debug(f"Found repo-description.mdc in {repo.name}")
            except Exception as e:
                logger.warning(f"Failed to parse repo-description.mdc in {repo.name}: {e}")

    if not repo_descriptions:
        logger.debug("No repo-description.mdc files found in any sub-repo")
        return

    # Create the root cursor rules directory if it doesn't exist
    root_rules_dir = paths.get_cursor_rules_dir(root_dir)
    root_rules_dir.mkdir(parents=True, exist_ok=True)

    # Generate combined content with repo names as headers
    content_parts = []
    for repo_name, rule in repo_descriptions:
        content_parts.append(f"## {repo_name}\n\n{rule.body.strip()}")

    combined_body = "\n\n".join(content_parts)

    # Create the merged rule
    merged_rule = Rule(
        description="Combined repository descriptions from all sub-repos",
        globs=None,
        alwaysApply=True,
        body=combined_body,
    )

    # Write to the root repos-description.mdc
    repos_description_path = root_rules_dir / "repos-description.mdc"
    repos_description_path.write_text(merged_rule.render(), encoding="utf-8")

    logger.info(
        f"✅ Merged {len(repo_descriptions)} repo descriptions into {repos_description_path}"
    )


def convert_cursor_rules_to_claude_md(cursor_dir: Path) -> None:
    """Convert cursor rules in a directory to a CLAUDE.md file."""
    rules_dir = cursor_dir / "rules"
    # Place CLAUDE.md at the same level as .cursor directory, not inside it
    claude_md_path = cursor_dir.parent / "CLAUDE.md"

    if not rules_dir.exists():
        logger.debug(f"No rules directory found at {rules_dir}")
        return

    rules = []
    for rule_file in rules_dir.glob("*.mdc"):
        try:
            content = rule_file.read_text(encoding="utf-8")
            rule = Rule.parse(content)
            rules.append(rule)
            logger.debug(f"Found cursor rule: {rule_file.name}")
        except Exception as e:
            logger.warning(f"Failed to parse cursor rule {rule_file}: {e}")

    if not rules:
        logger.debug(f"No valid cursor rules found in {rules_dir}")
        # Remove CLAUDE.md if it exists but no rules found
        if claude_md_path.exists():
            claude_md_path.unlink()
            logger.debug(f"Removed empty CLAUDE.md from {claude_md_path.parent}")
        return

    # Generate content by concatenating rule bodies with line breaks
    content_parts = []
    for i, rule in enumerate(rules):
        if i > 0:
            content_parts.append("\n\n")  # Add line breaks between rules
        content_parts.append(rule.body.strip())

    combined_content = "".join(content_parts)
    claude_md_path.write_text(combined_content, encoding="utf-8")

    logger.info(f"✅ Generated CLAUDE.md with {len(rules)} rules at {claude_md_path}")


def convert_all_cursor_rules(root_dir: Path) -> None:
    """Convert cursor rules to CLAUDE.md files for all repositories.

    This function:
    1. First merges all repo-description.mdc files from sub-repos into a root-level
       repos-description.mdc file
    2. Then converts all cursor rules to CLAUDE.md files
    """
    logger.info("Converting cursor rules to CLAUDE.md files...")

    # Step 1: Merge repo-description.mdc files from sub-repos
    merge_repo_description_rules(root_dir)

    # Step 2: Check root directory for .cursor
    root_cursor_dir = root_dir / ".cursor"
    if root_cursor_dir.exists():
        logger.debug(f"Processing root cursor directory: {root_cursor_dir}")
        convert_cursor_rules_to_claude_md(root_cursor_dir)

    # Step 3: Check each sub-repository for .cursor
    paths = Paths(root_dir)
    repos = load_repos(paths=paths)
    for repo in repos:
        cursor_dir = repo.path / ".cursor"
        if cursor_dir.exists():
            logger.debug(f"Processing cursor directory for {repo.name}: {cursor_dir}")
            convert_cursor_rules_to_claude_md(cursor_dir)
        else:
            logger.debug(f"No cursor directory found for {repo.name}")

    logger.info("✅ Cursor rules conversion complete")


@click.command(name="claude")
def convert_claude_cmd():
    """Convert cursor rules to CLAUDE.md files across all repositories.

    This command will:
    1. Merge all repo-description.mdc files from sub-repos into repos-description.mdc
    2. Scan root and all repositories for .cursor/rules/*.mdc files
    3. Parse each cursor rule using the rules parser
    4. Generate CLAUDE.md files alongside each .cursor directory
    """
    logger.info("Converting cursor rules to CLAUDE.md files...")
    convert_all_cursor_rules(Path.cwd())
