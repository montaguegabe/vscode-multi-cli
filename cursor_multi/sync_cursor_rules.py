import logging
import os

import click

from cursor_multi.ignore_files import update_gitignore_with_imported_rules
from cursor_multi.paths import paths
from cursor_multi.repos import load_repos
from cursor_multi.rules import (
    Rule,
    RuleParseError,
    RulesNotCombinableError,
    combine_rules,
)

logger = logging.getLogger(__name__)


def cleanup_existing_imported_rules():
    """Remove any previously imported rules listed in .importedrules."""

    # The imported rules path contains a list of rules that were loaded from the subrepos.

    if not paths.imported_rules_path.exists():
        logger.debug("No imported rules to cleanup")
        return

    with paths.imported_rules_path.open("r") as f:
        imported_rules = [line.strip() for line in f.readlines() if line.strip()]

    for rule in imported_rules:
        rule_path = paths.root_rules_dir / rule
        if rule_path.exists():
            rule_path.unlink()
            logger.debug(f"🗑️  Removed old imported rule: {rule}")

    # Clear the imported rules file
    paths.imported_rules_path.unlink()


def track_imported_rules(imported_rules: list[str]):
    """Write the list of imported rules to .importedrules."""
    with paths.imported_rules_path.open("w") as f:
        f.write("\n".join(sorted(imported_rules)) + "\n")


def suffixed_rule_name(rule_name_with_ext: str, repo_name: str) -> str:
    """Suffix the rule name with the repo name."""
    name_part, ext_part = os.path.splitext(rule_name_with_ext)
    return f"{name_part}-{repo_name}{ext_part}"


def sync_cursor_rules():
    """Import .cursor/rules files from each repository into root .cursor/rules."""

    logger.info("Importing Cursor rules...")

    # Clean up any previously imported rules
    logger.debug("Cleaning up old imported rules")
    cleanup_existing_imported_rules()

    # First, build a mapping of rule names to their repos to the parsed rule
    rule_name_mapping = {}  # Dict[rule.name, Dict[Repository, Rule]]
    for repo in load_repos():
        repo_rules_dir = paths.get_cursor_rules_dir(repo.path)
        if not repo_rules_dir.exists():
            continue

        for rule_file in repo_rules_dir.iterdir():
            if not rule_file.is_file():
                continue

            # Read the original content
            with rule_file.open("r") as f:
                content = f.read()

            try:
                rule = Rule.parse(content)
            except RuleParseError:
                logger.error(f"Error parsing rule {rule_file}.  Skipping...")
                continue

            # Initialize rule entry if not exists
            rule_name = rule_file.name
            if rule_name not in rule_name_mapping:
                rule_name_mapping[rule_name] = {}

            scoped_rule = rule.scoped_to_repo(repo.name)
            rule_name_mapping[rule_name][repo] = scoped_rule

    # Resolve conflicts between rules with the same name
    rules_for_import = {}  # Maps rule name to Rule
    for rule_name, repo_to_rule in rule_name_mapping.items():
        try:
            # Note: the below will be a no-op if there is only one rule
            combined_rule = combine_rules(list(repo_to_rule.values()))
            rules_for_import[rule_name] = combined_rule
        except RulesNotCombinableError:
            # Rules have different content - use suffixed filenames
            for repo, rule in repo_to_rule.items():
                rules_for_import[suffixed_rule_name(rule_name, repo.name)] = rule

    # Export the rules
    paths.root_rules_dir.mkdir(parents=True, exist_ok=True)
    for rule_name, rule in rules_for_import.items():
        dst_path = paths.root_rules_dir / rule_name
        assert not dst_path.exists(), "Rules should be cleared properly before import"
        with dst_path.open("w") as f:
            f.write(rule.render())
        logger.debug(f"Imported rule {rule_name}")

    imported_rules = list(rules_for_import.keys())
    track_imported_rules(imported_rules)
    update_gitignore_with_imported_rules(imported_rules)

    logger.info("Cursor rules imported successfully!")


@click.command(name="rules")
def sync_cursor_rules_cmd():
    """Merge Cursor rules from all repositories into the root .cursor/rules directory.

    This command will:
    1. Clean up previously imported rules
    2. Import rules from all repositories
    3. Combine rules with the same name when possible
    4. Update .gitignore to exclude imported rules
    """
    sync_cursor_rules()
