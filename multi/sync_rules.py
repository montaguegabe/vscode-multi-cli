import logging
from pathlib import Path

import click

from multi.paths import Paths
from multi.repos import load_repos
from multi.rules import Rule

logger = logging.getLogger(__name__)


def generate_repo_descriptions_rule(root_dir: Path) -> None:
    """Generate the repo-directories.mdc cursor rule from multi.json descriptions."""
    paths = Paths(root_dir)
    repos = load_repos(paths=paths)

    # Collect repos that have descriptions
    repos_with_descriptions = [
        (repo.name, repo.description)
        for repo in repos
        if hasattr(repo, "description") and repo.description
    ]

    if not repos_with_descriptions:
        logger.debug("No repository descriptions found in multi.json")
        return

    # Create the rule body with repo descriptions
    body = "This workspace contains multiple repositories:\n\n"
    for repo_name, description in repos_with_descriptions:
        body += f"- `{repo_name}`: {description}\n"

    rule = Rule(
        description="Repository structure documentation",
        globs=None,
        alwaysApply=False,
        body=body,
    )

    # Ensure .cursor/rules directory exists
    rules_dir = root_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Write the rule file
    rule_path = rules_dir / "repo-directories.mdc"
    rule_path.write_text(rule.render())
    logger.info("✅ Generated repo-directories.mdc from multi.json descriptions")


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
    """Convert cursor rules to CLAUDE.md files for all repositories."""
    logger.info("Converting cursor rules to CLAUDE.md files...")

    # Check root directory for .cursor
    root_cursor_dir = root_dir / ".cursor"
    if root_cursor_dir.exists():
        logger.debug(f"Processing root cursor directory: {root_cursor_dir}")
        convert_cursor_rules_to_claude_md(root_cursor_dir)

    # Check each sub-repository for .cursor
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


def sync_all_rules(root_dir: Path) -> None:
    """Generate repo descriptions rule and convert all cursor rules to CLAUDE.md."""
    generate_repo_descriptions_rule(root_dir)
    convert_all_cursor_rules(root_dir)


@click.command(name="rules")
def sync_rules_cmd():
    """Sync cursor rules and generate CLAUDE.md files.

    This command will:
    1. Generate repo-directories.mdc from multi.json descriptions
    2. Scan root and all repositories for .cursor/rules/*.mdc files
    3. Parse each cursor rule using the rules parser
    4. Generate CLAUDE.md files alongside each .cursor directory
    """
    logger.info("Syncing rules...")
    sync_all_rules(Path.cwd())
