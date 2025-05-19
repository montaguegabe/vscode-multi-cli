import json
import logging
import os

import click

from cursor_multi.git_helpers import is_git_repo_root, run_git
from cursor_multi.paths import paths
from cursor_multi.sync import sync

logger = logging.getLogger(__name__)


def collect_repo_urls() -> list[str]:
    """Interactively collect repository URLs from the user."""
    urls = []
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
    return urls


def create_multi_json(urls: list[str]) -> None:
    """Create the multi.json file with the provided repository URLs."""
    config = {"repos": [{"url": url} for url in urls]}

    with open(os.path.join(os.getcwd(), "multi.json"), "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Add newline at end of file


def init_git_repo() -> None:
    """Initialize a git repository if one doesn't exist."""
    if not is_git_repo_root(paths.root_dir):
        logger.info("Initializing git repository...")
        run_git(["init"], "initialize git repository", paths.root_dir)


def commit_changes() -> None:
    """Stage and commit all changes."""
    run_git(["add", "."], "stage changes", paths.root_dir)
    run_git(
        ["commit", "-m", "Multi init: Configure cursor-multi workspace"],
        "commit changes",
        paths.root_dir,
    )


@click.command(name="init")
def init_cmd():
    """Initialize a new cursor-multi workspace.

    This command will:
    1. Collect repository URLs interactively
    2. Create multi.json configuration file
    3. Initialize git repository if needed
    4. Sync all repositories and configurations
    5. Commit the changes
    """
    logger.info("Initializing cursor-multi workspace...")

    # Collect repository URLs
    urls = collect_repo_urls()

    # Create multi.json
    create_multi_json(urls)
    logger.info("Created multi.json configuration")

    # Initialize git repo if needed
    init_git_repo()

    # Run sync
    sync(ensure_on_same_branch=False)

    # Commit changes
    commit_changes()
    logger.info("✅ Workspace initialized successfully")
