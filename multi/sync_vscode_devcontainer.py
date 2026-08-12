import logging
import shutil
from pathlib import Path

import click

from multi.cli_helpers import get_install_set_from_context
from multi.paths import Paths
from multi.repos import load_repos
from multi.sync_vscode_helpers import prefix_repo_name_to_path_recursive
from multi.utils import soft_read_json_file, write_json_file

logger = logging.getLogger(__name__)


def sync_devcontainer(root_dir: Path, install_set: str | None = None) -> None:
    """Copy .devcontainer folder from a sub-repo to root workspace.

    Assumes only one sub-repo has a .devcontainer folder.
    If found, copies it to the root directory, overwriting any existing one.
    Prefixes workspace folder paths in devcontainer.json with the repo name.
    """
    paths = Paths(root_dir, install_set=install_set)
    repos = load_repos(paths)

    dest_devcontainer = paths.root_dir / ".devcontainer"

    for repo in repos:
        source_devcontainer = repo.path / ".devcontainer"
        if source_devcontainer.exists() and source_devcontainer.is_dir():
            logger.info(f"Found .devcontainer in {repo.name}, copying to root...")

            # Remove existing .devcontainer if present
            if dest_devcontainer.exists():
                shutil.rmtree(dest_devcontainer)

            # Copy the folder
            shutil.copytree(source_devcontainer, dest_devcontainer)

            # Prefix paths in devcontainer.json
            devcontainer_json_path = dest_devcontainer / "devcontainer.json"
            if devcontainer_json_path.exists():
                devcontainer_json = soft_read_json_file(devcontainer_json_path)
                if devcontainer_json:
                    devcontainer_json = prefix_repo_name_to_path_recursive(
                        devcontainer_json,
                        repo.relative_path,
                        resolve_relative_paths=True,
                    )
                    write_json_file(devcontainer_json_path, devcontainer_json)
                    logger.debug(
                        f"Prefixed paths in devcontainer.json with {repo.name}"
                    )

            logger.info(f"Successfully copied .devcontainer from {repo.name}")
            return

    logger.debug("No .devcontainer folder found in any repository")


@click.command(name="devcontainer")
def sync_devcontainer_cmd():
    """Copy .devcontainer folder from a sub-repo to the root workspace.

    This command will:
    1. Search for a .devcontainer folder in sub-repos.
    2. Copy it to the root directory, overwriting any existing one.
    3. Prefix workspace folder paths in devcontainer.json with the repo name.
    """
    logger.info("Syncing .devcontainer folder...")
    sync_devcontainer(root_dir=Path.cwd(), install_set=get_install_set_from_context())
