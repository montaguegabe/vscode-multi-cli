import json
import logging
import shutil
from pathlib import Path

import click

from multi.git_helpers import check_repo_is_clean
from multi.ignore_files import (
    clear_subrepo_generated_file_block,
    remove_gitignore_entries_for_repos,
    remove_ignore_entries_for_repos,
)
from multi.paths import Paths
from multi.sync_vscode import merge_vscode_configs

logger = logging.getLogger(__name__)


def _derive_name_from_url(url: str) -> str:
    """Derive a directory name from a repo URL (last path component)."""
    return url.split("/")[-1]


@click.command(name="remove")
@click.argument("repo_name")
@click.option("--delete", is_flag=True, help="Also delete local directory/symlink")
@click.option("--force", is_flag=True, help="Skip uncommitted changes check")
def remove_cmd(repo_name: str, delete: bool, force: bool):
    """Remove a repository from the workspace.

    Removes the repo entry from multi.json and cleans up ignore files.
    Use --delete to also remove the local directory or symlink.
    """
    paths = Paths(Path.cwd())
    is_monorepo = paths.settings.is_monorepo()

    # Read multi.json as raw JSON
    with paths.multi_json_path.open("r") as f:
        config = json.load(f)

    repos_list = config.get("repos", [])

    # Find the matching entry by name
    matched_index = None
    for i, entry in enumerate(repos_list):
        entry_name = entry.get("name") or _derive_name_from_url(entry.get("url", ""))
        if entry_name == repo_name:
            matched_index = i
            break

    if matched_index is None:
        raise click.ClickException(f"No repo named '{repo_name}' found in multi.json.")

    # Handle --delete
    repo_path = paths.root_dir / repo_name
    if delete and repo_path.exists():
        if not force and not is_monorepo:
            # In monorepo mode there's no .git to check; in normal mode, check cleanliness
            if repo_path.is_symlink():
                logger.debug(f"{repo_name} is a symlink, skipping clean check")
            else:
                check_repo_is_clean(repo_path)

        if repo_path.is_symlink():
            repo_path.unlink()
            logger.info(f"Removed symlink '{repo_name}'")
        else:
            shutil.rmtree(repo_path)
            logger.info(f"Deleted directory '{repo_name}'")

    # Remove entry from multi.json
    repos_list.pop(matched_index)
    config["repos"] = repos_list

    with paths.multi_json_path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    logger.info(f"Removed '{repo_name}' from multi.json")

    # Clean up ignore files (not used in monorepo mode)
    if not is_monorepo:
        remove_gitignore_entries_for_repos(paths, [repo_name])
        remove_ignore_entries_for_repos(paths, [repo_name])
        if repo_path.exists():
            clear_subrepo_generated_file_block(repo_path)

    # Re-merge VS Code configs
    merge_vscode_configs(root_dir=paths.root_dir)

    logger.info(f"✅ Successfully removed {repo_name}")
