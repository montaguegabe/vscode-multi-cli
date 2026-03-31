import json
import logging
import shutil
from pathlib import Path

import click
import git

from multi.paths import Paths
from multi.repo_urls import (
    derive_explicit_local_name,
    derive_repo_slug_from_url,
    normalize_repo_url,
)
from multi.sync import sync

logger = logging.getLogger(__name__)


@click.command(name="add")
@click.argument("repo_url")
@click.option("--name", default=None, help="Override directory name derived from URL")
def add_cmd(repo_url: str, name: str | None):
    """Add a repository to the workspace.

    Appends the repo to multi.json and runs sync to clone it
    and merge all configurations. In monorepo mode, the repo's
    .git directory is removed after cloning so it becomes part
    of the root repository.
    """
    paths = Paths(Path.cwd())
    is_monorepo = paths.settings.is_monorepo()

    # Read multi.json as raw JSON
    with paths.multi_json_path.open("r") as f:
        config = json.load(f)

    repos_list = config.get("repos", [])

    # Check for duplicate URL
    normalized_new = normalize_repo_url(repo_url)
    for entry in repos_list:
        existing_url = entry.get("url", "")
        if normalize_repo_url(existing_url) == normalized_new:
            raise click.ClickException(
                f"A repo with URL '{existing_url}' already exists in multi.json."
            )

    # Derive or validate name
    auto_name = derive_explicit_local_name(
        repo_url,
        paths.root_dir.name,
    )
    slug_name = derive_repo_slug_from_url(repo_url)

    existing_names = {
        entry.get("name") or derive_repo_slug_from_url(entry.get("url", ""))
        for entry in repos_list
    }

    if (
        not name
        and auto_name
        and (
            auto_name in existing_names
            or (paths.root_dir / auto_name).exists()
        )
    ):
        auto_name = None

    repo_name = name if name else (auto_name or slug_name)

    # Check for duplicate name
    if repo_name in existing_names:
        raise click.ClickException(
            f"A repo with name '{repo_name}' already exists in multi.json."
        )

    # Check target directory doesn't already exist
    target_dir = paths.root_dir / repo_name
    if target_dir.exists():
        raise click.ClickException(f"Directory '{repo_name}' already exists on disk.")

    # In monorepo mode, clone and remove .git before writing multi.json,
    # since sync() skips clone_repos() in monorepo mode.
    if is_monorepo:
        logger.info(f"Cloning {repo_name}...")
        git.Repo.clone_from(repo_url, target_dir)
        git_dir = target_dir / ".git"
        if git_dir.is_dir():
            shutil.rmtree(git_dir)
        elif git_dir.exists() or git_dir.is_symlink():
            git_dir.unlink()
        logger.info(f"Cloned {repo_name} and removed .git for monorepo mode")

    # Build new entry
    new_entry: dict = {"url": repo_url}
    if name:
        new_entry["name"] = name
    elif auto_name:
        new_entry["name"] = auto_name

    repos_list.append(new_entry)
    config["repos"] = repos_list

    # Write multi.json
    with paths.multi_json_path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    logger.info(f"Added '{repo_name}' to multi.json")

    # Run full sync to clone (non-monorepo) and merge configs
    sync(root_dir=paths.root_dir)

    logger.info(f"✅ Successfully added {repo_name}")
