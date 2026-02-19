import json
import logging
from importlib.resources import files
from pathlib import Path

import click

from multi.git_helpers import is_git_repo_root
from multi.sync import sync

init_readme_template = (files("multi") / "resources" / "init_readme.md").read_text()

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


def init_git_repo() -> None:
    """Initialize a git repository if one doesn't exist."""
    import git

    if not is_git_repo_root(paths.root_dir):
        logger.info("Initializing git repository...")
        git.Repo.init(paths.root_dir)


def commit_changes() -> None:
    """Stage and commit all changes."""
    import git

    repo = git.Repo(paths.root_dir)
    repo.git.add(all=True)
    repo.index.commit("Multi init: Configure multi workspace")


def create_readme(urls: list[str]) -> None:
    """Create a README.md file if it doesn't exist."""
    readme_path = paths.root_dir / "README.md"
    if readme_path.exists():
        return

    # Extract repo name and create the hyperlink
    repo_entries = []
    for url in urls:
        # Extract repo name and create the hyperlink
        repo_name = url.split("/")[-1].replace(".git", "")
        # Handle both HTTPS and SSH URLs to create proper hyperlinks
        if url.startswith("git@"):
            # Convert SSH URL to HTTPS URL for hyperlink
            # From: git@github.com:username/repo.git
            # To: https://github.com/username/repo
            parts = url.split(":")
            if len(parts) == 2:
                https_url = f"https://github.com/{parts[1].replace('.git', '')}"
                repo_entries.append(f"- [{repo_name}]({https_url})")
        else:
            # Handle HTTPS URL
            # Remove .git suffix if present
            https_url = url.replace(".git", "")
            repo_entries.append(f"- [{repo_name}]({https_url})")

    repo_list = "\n".join(repo_entries)

    # Get the workspace directory name
    workspace_name = paths.root_dir.name

    # Format and write the README
    readme_content = init_readme_template.format(
        __name__=workspace_name, __repo_list__=repo_list
    )
    readme_path.write_text(readme_content)
    logger.info("Created README.md")


@click.command(name="init")
def init_cmd():
    """Initialize a new multi workspace.

    This command will:
    1. Collect repository URLs interactively (optionally with descriptions)
    2. Create multi.json configuration file (with descriptions if provided)
    3. Initialize git repository if needed
    4. Create README.md if it doesn't exist
    5. Sync all repositories and configurations (generates cursor rules from descriptions)
    6. Commit the changes
    """
    logger.info("Initializing multi workspace...")

    # Collect repository URLs and descriptions
    urls, descriptions = collect_repo_urls()

    # Create multi.json (includes descriptions if provided)
    create_multi_json(urls, descriptions)
    logger.info("Created multi.json configuration")

    # Initialize git repo if needed
    init_git_repo()

    # Create README.md if it doesn't exist
    create_readme(urls)

    # Run sync (this will generate repo-directories.mdc from descriptions in multi.json)
    sync(ensure_on_same_branch=False)

    # Commit changes
    commit_changes()
    logger.info("✅ Workspace initialized successfully")
