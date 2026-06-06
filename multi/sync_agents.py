import logging
from pathlib import Path

import click

from multi.cli_helpers import get_install_set_from_context
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)


def get_agent_instructions_settings(paths: Paths) -> dict:
    agent_instructions_settings = paths.settings.get("agentInstructions", {})
    return (
        agent_instructions_settings
        if isinstance(agent_instructions_settings, dict)
        else {}
    )


def is_agents_generation_enabled(paths: Paths) -> bool:
    return bool(get_agent_instructions_settings(paths).get("enabled", False))


def get_agents_parts_dir_name(paths: Paths) -> str:
    parts_dir = get_agent_instructions_settings(paths).get("partsDir", "AGENTS.parts")
    if not isinstance(parts_dir, str) or not parts_dir.strip():
        return "AGENTS.parts"
    return parts_dir.strip()


def should_include_repo_descriptions(paths: Paths) -> bool:
    return bool(
        get_agent_instructions_settings(paths).get("includeRepoDescriptions", True)
    )


def get_repo_descriptions_section(paths: Paths) -> str:
    if not should_include_repo_descriptions(paths):
        return ""
    if not paths.settings.get("repos"):
        return ""

    repos_with_descriptions = [
        (repo.name, repo.description)
        for repo in load_repos(paths=paths)
        if getattr(repo, "description", None)
    ]
    if not repos_with_descriptions:
        return ""

    lines = ["This workspace contains multiple repositories:", ""]
    for repo_name, description in repos_with_descriptions:
        lines.append(f"- `{repo_name}`: {description}")
    return "\n".join(lines)


def read_agents_part_files(parts_dir: Path) -> list[str]:
    if not parts_dir.is_dir():
        return []

    parts: list[str] = []
    for part_file in sorted(parts_dir.glob("*.md")):
        if not part_file.is_file():
            continue
        content = part_file.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)
    return parts


def build_agents_content(
    repo_dir: Path, paths: Paths, *, include_root_descriptions: bool
) -> str:
    parts = read_agents_part_files(repo_dir / get_agents_parts_dir_name(paths))
    if include_root_descriptions:
        repo_descriptions = get_repo_descriptions_section(paths)
        if repo_descriptions:
            parts.insert(0, repo_descriptions)

    if not parts:
        return ""

    return "\n\n".join(parts).rstrip() + "\n"


def would_generate_agents_for_repo(
    repo_dir: Path, paths: Paths, *, is_root: bool = False
) -> bool:
    if not is_agents_generation_enabled(paths):
        return False

    content = build_agents_content(
        repo_dir,
        paths,
        include_root_descriptions=is_root,
    )
    return bool(content)


def generate_agents_files(
    repo_dir: Path, paths: Paths, *, is_root: bool = False
) -> None:
    content = build_agents_content(
        repo_dir,
        paths,
        include_root_descriptions=is_root,
    )
    if not content:
        logger.debug(f"No AGENTS parts found at {repo_dir}")
        return

    agents_md_path = repo_dir / "AGENTS.md"
    claude_md_path = repo_dir / "CLAUDE.md"
    agents_md_path.write_text(content, encoding="utf-8")
    claude_md_path.write_text(content, encoding="utf-8")
    logger.info(f"✅ Generated AGENTS.md and CLAUDE.md at {repo_dir}")


def sync_all_agents(root_dir: Path, install_set: str | None = None) -> None:
    paths = Paths(root_dir, install_set=install_set)
    if not is_agents_generation_enabled(paths):
        logger.debug("AGENTS generation is disabled")
        return

    generate_agents_files(paths.root_dir, paths, is_root=True)

    if paths.settings.is_monorepo() or not paths.settings.get("repos"):
        return

    for repo in load_repos(paths=paths):
        if repo.path.exists():
            generate_agents_files(repo.path, paths)


@click.command(name="agents")
def sync_agents_cmd():
    """Generate AGENTS.md and CLAUDE.md from AGENTS.parts/*.md files."""
    logger.info("Syncing AGENTS files...")
    root_dir = Path.cwd()
    install_set = get_install_set_from_context()
    paths = Paths(root_dir, install_set=install_set)
    from multi.ignore_files import update_gitignore_with_generated_files

    update_gitignore_with_generated_files(paths=paths)
    sync_all_agents(root_dir, install_set=install_set)
