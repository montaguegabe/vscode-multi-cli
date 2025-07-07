import logging
from pathlib import Path
from typing import Any, Dict, List

import click

from vscode_multi.paths import paths
from vscode_multi.repos import Repository, load_repos
from vscode_multi.settings import settings
from vscode_multi.sync_vscode_helpers import VSCodeFileMerger, deep_merge
from vscode_multi.utils import soft_read_json_file

logger = logging.getLogger(__name__)


class SettingsFileMerger(VSCodeFileMerger):
    def _get_destination_json_path(self) -> Path:
        return paths.vscode_settings_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return paths.get_vscode_config_dir(repo_path) / "settings.json"

    def _get_skip_keys(self, repo: Repository) -> List[str] | None:
        """Return the list of settings keys to skip during merge."""
        return settings["vscode"].get("skipSettings", [])

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Merge in settings.shared.json
        shared_settings_path = paths.vscode_settings_shared_path
        if shared_settings_path.exists():
            shared_settings = soft_read_json_file(shared_settings_path)
            merged_json = deep_merge(merged_json, shared_settings)
        else:
            logger.debug(
                f"Shared settings file not found at {shared_settings_path.name}, skipping."
            )

        # Add Python paths for autocomplete
        repos = load_repos()
        python_paths_to_add = [repo.name for repo in repos if repo.is_python]
        if python_paths_to_add:
            logger.info("Adding Python paths for autocomplete")
            current_extra_paths = merged_json.setdefault(
                "python.autoComplete.extraPaths", []
            )

            for path_val in python_paths_to_add:
                if path_val not in current_extra_paths:
                    current_extra_paths.append(path_val)
        return merged_json


def merge_settings_json() -> None:
    merger = SettingsFileMerger()
    merger.merge()


@click.command(name="settings")
def merge_settings_cmd():
    """Merge settings.json files from all repositories into the root .vscode directory.

    This command will:
    1. Merge VSCode settings from all repos using the new merger class.
    2. Apply shared settings from settings.shared.json.
    3. Configure Python autocomplete paths.
    """
    logger.info("Merging settings.json files from all repositories...")
    merge_settings_json()
