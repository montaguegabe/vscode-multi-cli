from dataclasses import dataclass
from typing import Optional, List, Dict
import os


@dataclass
class RuleFrontmatter:
    description: Optional[str] = None
    globs: Optional[List[str]] = None
    always_apply: bool = False

    @staticmethod
    def parse(frontmatter_str: str) -> "RuleFrontmatter":
        """Parse frontmatter string into a RuleFrontmatter object."""
        result = RuleFrontmatter()
        for line in frontmatter_str.splitlines():
            line = line.strip()
            if line.startswith("description:"):
                result.description = line[12:].strip()
            elif line.startswith("globs:"):
                globs_str = line[6:].strip()
                result.globs = (
                    [g.strip() for g in globs_str.split(",")] if globs_str else []
                )
            elif line.startswith("alwaysApply:"):
                result.always_apply = "true" in line.lower()
        return result

    def render(self) -> str:
        """Render frontmatter object back to string format."""
        lines = []
        if self.description:
            lines.append(f"description: {self.description}")
        if self.globs is not None:
            lines.append(f"globs: {','.join(self.globs)}")
        lines.append(f"alwaysApply: {str(self.always_apply).lower()}")
        return "\n".join(lines)


@dataclass
class Rule:
    frontmatter: RuleFrontmatter
    body: str

    @staticmethod
    def parse(content: str) -> Optional["Rule"]:
        """Parse a rule file content into a Rule object."""
        parts = content.split("---\n", 2)
        if len(parts) != 3:
            return None

        frontmatter = RuleFrontmatter.parse(parts[1])
        return Rule(frontmatter=frontmatter, body=parts[2])

    def render(self) -> str:
        """Render rule object back to string format."""
        return f"---\n{self.frontmatter.render()}\n---\n{self.body}"

    def __eq__(self, other: object) -> bool:
        """Two rules are equal if they have the same description and body."""
        if not isinstance(other, Rule):
            return NotImplemented
        return (
            self.frontmatter.description == other.frontmatter.description
            and self.body == other.body
            and self.frontmatter.always_apply == other.frontmatter.always_apply
        )


def combine_identical_rules(rules_by_repo: Dict[str, str]) -> Optional[str]:
    """
    Combine identical rules from different repos, merging their globs.

    Args:
        rules_by_repo: Dict mapping repo names to their rule content

    Returns:
        Combined rule content if rules are identical (ignoring globs),
        None if rules are different
    """
    # Parse all rules
    parsed_rules = {
        repo: Rule.parse(content) for repo, content in rules_by_repo.items()
    }

    # Filter out any that failed to parse
    parsed_rules = {
        repo: rule for repo, rule in parsed_rules.items() if rule is not None
    }

    if not parsed_rules:
        return None

    # Get first rule as reference
    first_repo = next(iter(parsed_rules))
    reference_rule = parsed_rules[first_repo]

    # Check all rules are identical (ignoring globs)
    if not all(rule == reference_rule for rule in parsed_rules.values()):
        return None

    # Combine all globs
    all_globs = set()
    for rule in parsed_rules.values():
        if rule.frontmatter.globs:
            all_globs.update(rule.frontmatter.globs)

    # Create combined rule
    combined_rule = Rule(
        frontmatter=RuleFrontmatter(
            description=reference_rule.frontmatter.description,
            globs=sorted(all_globs) if all_globs else None,
            always_apply=reference_rule.frontmatter.always_apply,
        ),
        body=reference_rule.body,
    )

    return combined_rule.render()


def modify_rule_content(content: str, repo_name: str) -> str:
    """Modify a rule file's content to scope its globs to the repo directory."""
    # Parse the rule
    rule = Rule.parse(content)
    if not rule:
        return content  # No valid frontmatter found

    # Check if this is an agent-requested rule (no globs and no alwaysApply: true)
    if not rule.frontmatter.globs and not rule.frontmatter.always_apply:
        return content

    # Transform the frontmatter
    if rule.frontmatter.always_apply:
        # For alwaysApply: true rules, we override with repo-wide glob
        rule.frontmatter.always_apply = False
        rule.frontmatter.globs = [f"{repo_name}/**/*"]
    else:
        # For normal glob rules, scope the globs to the repo
        if rule.frontmatter.globs:
            rule.frontmatter.globs = [
                f"{repo_name}/{g}" for g in rule.frontmatter.globs
            ]

    # Render the modified rule
    return rule.render()


def cleanup_old_imported_rules(git_root: str):
    """Remove any previously imported rules listed in .importedrules."""
    imported_rules_file = os.path.join(git_root, ".importedrules")
    rules_dir = os.path.join(git_root, ".cursor", "rules")

    if not os.path.exists(imported_rules_file):
        return

    with open(imported_rules_file, "r") as f:
        old_rules = [line.strip() for line in f.readlines() if line.strip()]

    for rule in old_rules:
        rule_path = os.path.join(rules_dir, rule)
        if os.path.exists(rule_path):
            os.remove(rule_path)
            print(f"🗑️  Removed old imported rule: {rule}")

    # Clear the imported rules file
    os.remove(imported_rules_file)


def track_imported_rules(git_root: str, imported_rules: list[str]):
    """Write the list of imported rules to .importedrules."""
    imported_rules_file = os.path.join(git_root, ".importedrules")

    with open(imported_rules_file, "w") as f:
        f.write("\n".join(sorted(imported_rules)) + "\n")


def import_cursor_rules(git_root: str, repo_names: list[str]) -> list[str]:
    """Import .cursor/rules files from each repository into root .cursor/rules."""
    root_rules_dir = os.path.join(git_root, ".cursor", "rules")
    imported_rules = []

    # Create root .cursor/rules directory if it doesn't exist
    os.makedirs(root_rules_dir, exist_ok=True)

    # First, build a mapping of rule files to their repos and content
    rule_mapping = {}  # Dict[str, dict] mapping rule name to {repos: [], contents: {}}
    for repo_name in repo_names:
        repo_rules_dir = os.path.join(git_root, repo_name, ".cursor", "rules")
        if not os.path.exists(repo_rules_dir):
            continue

        for rule_file in os.listdir(repo_rules_dir):
            src_path = os.path.join(repo_rules_dir, rule_file)
            if not os.path.isfile(src_path):
                continue

            # Read the original content
            with open(src_path, "r") as f:
                content = f.read()

            # Initialize rule entry if not exists
            if rule_file not in rule_mapping:
                rule_mapping[rule_file] = {"repos": [], "contents": {}}

            # Store the content with the repo as key
            rule_mapping[rule_file]["repos"].append(repo_name)
            rule_mapping[rule_file]["contents"][repo_name] = content

    # Now process and import the rules with conflict awareness
    for rule_file, rule_data in rule_mapping.items():
        source_repos = rule_data["repos"]
        has_conflict = len(source_repos) > 1

        if not has_conflict:
            # Single repo case - process normally
            repo_name = source_repos[0]
            content = rule_data["contents"][repo_name]
            modified_content = modify_rule_content(content, repo_name)
            dst_path = os.path.join(root_rules_dir, rule_file)
            imported_rules.append(rule_file)

            assert not os.path.exists(dst_path)
            with open(dst_path, "w") as f:
                f.write(modified_content)

            print(
                f"✅ Imported rule from {repo_name}/{rule_file} (scoped to {repo_name}/)"
            )
            continue

        # Try to combine identical rules
        combined_content = combine_identical_rules(rule_data["contents"])
        if combined_content:
            # Rules are identical - write combined version
            dst_path = os.path.join(root_rules_dir, rule_file)
            imported_rules.append(rule_file)

            assert not os.path.exists(dst_path)
            with open(dst_path, "w") as f:
                f.write(combined_content)

            repo_list = ", ".join(source_repos)
            print(f"✅ Combined identical rule {rule_file} from repos: {repo_list}")
        else:
            # Rules have different content - use suffixed filenames
            for repo_name in source_repos:
                name, ext = os.path.splitext(rule_file)
                dst_filename = f"{name}-{repo_name}{ext}"
                dst_path = os.path.join(root_rules_dir, dst_filename)
                imported_rules.append(dst_filename)

                content = rule_data["contents"][repo_name]
                modified_content = modify_rule_content(content, repo_name)

                assert not os.path.exists(dst_path)
                with open(dst_path, "w") as f:
                    f.write(modified_content)

                print(
                    f"🔄 Imported rule from {repo_name}/{rule_file} as {dst_filename} (scoped to {repo_name}/)"
                )

    return imported_rules
