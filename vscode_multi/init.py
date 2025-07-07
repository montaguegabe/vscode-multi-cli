import json
import logging
from pathlib import Path

import click

from vscode_multi.git_helpers import is_git_repo_root, run_git
from vscode_multi.ignore_files import update_gitignore_with_vscode_files
from vscode_multi.init_readme import init_readme
from vscode_multi.paths import paths
from vscode_multi.sync import sync
from vscode_multi.rules import Rule

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


def create_multi_json(urls: list[str]) -> None:
    """Create the multi.json file with the provided repository URLs."""
    config = {"repos": [{"url": url} for url in urls]}

    multi_json_path = Path.cwd() / "multi.json"
    with multi_json_path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Add newline at end of file


def create_repo_directories_rule(urls: list[str], descriptions: list[str]) -> None:
    """Create a Cursor rule file describing the repositories."""
    if not descriptions:
        return

    # Extract repo names from URLs for use in the rule body
    repo_names = [url.split("/")[-1].replace(".git", "") for url in urls]

    # Create the rule body with repo descriptions
    body = "This workspace contains multiple repositories:\n\n"
    for repo_name, description in zip(repo_names, descriptions, strict=False):
        body += f"- `{repo_name}`: {description}\n"

    # Create the rule
    rule = Rule(
        description="Repository structure documentation",
        globs=None,  # No globs needed as this is documentation
        alwaysApply=False,
        body=body,
    )

    # Ensure .cursor directory exists
    cursor_dir = Path.cwd() / ".cursor"
    cursor_dir.mkdir(exist_ok=True)

    # Write the rule file
    rule_path = cursor_dir / "rules" / "repo-directories.mdc"
    rule_path.write_text(rule.render())


def init_git_repo() -> None:
    """Initialize a git repository if one doesn't exist."""
    if not is_git_repo_root(paths.root_dir):
        logger.info("Initializing git repository...")
        run_git(["init"], "initialize git repository", paths.root_dir)


def commit_changes() -> None:
    """Stage and commit all changes."""
    run_git(["add", "."], "stage changes", paths.root_dir)
    run_git(
        ["commit", "-m", "Multi init: Configure vscode-multi workspace"],
        "commit changes",
        paths.root_dir,
    )


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
    readme_content = init_readme.format(
        __name__=workspace_name, __repo_list__=repo_list
    )
    readme_path.write_text(readme_content)
    logger.info("Created README.md")


@click.command(name="init")
def init_cmd():
    """Initialize a new vscode-multi workspace.

    This command will:
    1. Collect repository URLs interactively (optionally with descriptions)
    2. Create multi.json configuration file
    3. Initialize git repository if needed
    4. Create repository documentation as a Cursor rule (if descriptions provided)
    5. Create README.md if it doesn't exist
    6. Sync all repositories and configurations
    7. Commit the changes
    """
    logger.info("Initializing vscode-multi workspace...")

    # Collect repository URLs and descriptions
    urls, descriptions = collect_repo_urls()

    # Create multi.json
    create_multi_json(urls)
    logger.info("Created multi.json configuration")

    # Create repo directories rule if descriptions were provided
    if descriptions:
        create_repo_directories_rule(urls, descriptions)
        logger.info("Created repository documentation rule")

    # Initialize git repo if needed
    init_git_repo()

    # Create README.md if it doesn't exist
    create_readme(urls)

    # Update gitignore to include vscode files
    update_gitignore_with_vscode_files()

    # Run sync
    sync(ensure_on_same_branch=False)

    # Commit changes
    commit_changes()
    logger.info("✅ Workspace initialized successfully")
