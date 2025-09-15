import logging
import shutil
from pathlib import Path

import click

from vscode_multi.paths import Paths
from vscode_multi.repos import load_repos

logger = logging.getLogger(__name__)


def copy_ruff_config_from_repo(repo_path: Path, paths: Paths) -> bool:
    """Copy ruff.toml from a repository to the root directory.

    Args:
        repo_path: Path to the repository to check for ruff.toml

    Returns:
        True if a ruff.toml file was found and copied, False otherwise
    """
    ruff_config_path = repo_path / "ruff.toml"
    root_ruff_path = paths.root_dir / "ruff.toml"

    if not ruff_config_path.exists():
        logger.debug(f"No ruff.toml found in {repo_path}")
        return False

    try:
        shutil.copy2(ruff_config_path, root_ruff_path)
        logger.info(f"✅ Copied ruff.toml from {repo_path.name} to root")
        return True
    except Exception as e:
        logger.warning(f"Failed to copy ruff.toml from {repo_path}: {e}")
        return False


def sync_all_ruff_configs(root_dir: Path) -> None:
    """Copy ruff.toml files from all repositories to the root directory.

    This will search all sub-repositories for ruff.toml files and copy the first
    one found to the root directory. If multiple repositories have ruff.toml,
    the last one processed will overwrite previous ones.
    """
    logger.info("Syncing ruff configuration files...")

    # Check each sub-repository for ruff.toml
    paths = Paths(root_dir)
    repos = load_repos(paths=paths)
    configs_found = 0

    for repo in repos:
        if repo.path.exists():
            logger.debug(f"Checking {repo.name} for ruff.toml")
            if copy_ruff_config_from_repo(repo.path, paths=paths):
                configs_found += 1
        else:
            logger.debug(f"Repository {repo.name} not found at {repo.path}")

    if configs_found == 0:
        logger.info("No ruff.toml files found in any repository")
        # Remove root ruff.toml if it exists but no configs found
        root_ruff_path = paths.root_dir / "ruff.toml"
        if root_ruff_path.exists():
            root_ruff_path.unlink()
            logger.info(
                "Removed existing ruff.toml from root (no source configs found)"
            )
    else:
        logger.info(
            f"✅ Ruff configuration sync complete ({configs_found} configs found)"
        )


@click.command(name="ruff")
def sync_ruff_cmd():
    """Copy ruff.toml configuration files from repositories to root.

    This command will:
    1. Scan all repositories for ruff.toml files
    2. Copy the configuration to the root directory
    3. If multiple ruff.toml files exist, the last one processed will be used
    """
    logger.info("Syncing ruff configuration files...")
    sync_all_ruff_configs(root_dir=Path.cwd())
