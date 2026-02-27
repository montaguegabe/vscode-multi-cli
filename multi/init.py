import json
import logging
from pathlib import Path

import click

from multi.sync import sync

logger = logging.getLogger(__name__)


def collect_repo_urls() -> tuple[list[str], list[str]]:
    """Interactively collect repository URLs and descriptions from the user."""
    urls = []
    descriptions = []
    collect_descriptions = True

    while True:
        url = click.prompt(
            "Enter a repository URL (or press Enter to finish)",
            default="",
            show_default=False,
        )
        if not url:
            if not urls:
                if not click.confirm(
                    "No repositories added. Do you want to finish anyway?"
                ):
                    continue
            break

        urls.append(url)

        if collect_descriptions:
            description = click.prompt(
                "Enter a description for this repo (or press Enter to skip descriptions)",
                default="",
                show_default=False,
            )
            if description:
                descriptions.append(description)
            else:
                collect_descriptions = False
                descriptions = []  # Clear any previously collected descriptions

    return urls, descriptions


def create_multi_json(urls: list[str], descriptions: list[str]) -> None:
    """Create the multi.json file with the provided repository URLs and descriptions."""
    repos = []
    for i, url in enumerate(urls):
        repo_config = {"url": url}
        if i < len(descriptions) and descriptions[i]:
            repo_config["description"] = descriptions[i]
        repos.append(repo_config)

    config = {"repos": repos}

    multi_json_path = Path.cwd() / "multi.json"
    with multi_json_path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Add newline at end of file


def commit_changes() -> None:
    """Stage and commit all changes."""
    import git

    repo = git.Repo(Path.cwd())
    repo.git.add(all=True)
    repo.index.commit("Multi init: Configure multi workspace")


@click.command(name="init")
def init_cmd():
    """Initialize a new multi workspace.

    This command will:
    1. Collect repository URLs interactively (optionally with descriptions)
    2. Create multi.json configuration file (with descriptions if provided)
    3. Run sync (which initializes git and README if needed)
    4. Commit the changes
    """
    logger.info("Initializing multi workspace...")

    # Collect repository URLs and descriptions
    urls, descriptions = collect_repo_urls()

    # Create multi.json (includes descriptions if provided)
    create_multi_json(urls, descriptions)
    logger.info("Created multi.json configuration")

    # Run sync (this will generate repo-directories.mdc from descriptions in multi.json)
    sync(ensure_on_same_branch=False)

    # Commit changes
    commit_changes()
    logger.info("✅ Workspace initialized successfully")
