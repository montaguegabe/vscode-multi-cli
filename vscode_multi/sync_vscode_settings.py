import logging
from pathlib import Path
from typing import Any, Dict, List

import click

from vscode_multi.paths import Paths
from vscode_multi.repos import Repository, load_repos
from vscode_multi.sync_vscode_helpers import VSCodeFileMerger, deep_merge
from vscode_multi.utils import soft_read_json_file

logger = logging.getLogger(__name__)


class SettingsFileMerger(VSCodeFileMerger):
    def _get_destination_json_path(self) -> Path:
        return self.paths.vscode_settings_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return self.paths.get_vscode_config_dir(repo_path) / "settings.json"

    def _get_skip_keys(self, repo: Repository) -> List[str] | None:
        """Return the list of settings keys to skip during merge."""
        return self.paths.settings["vscode"].get("skipSettings", [])

    def _merge_repo_json(
        self,
        merged_json: Dict[str, Any],
        repo_json: Dict[str, Any],
        repo: Repository,
    ) -> Dict[str, Any]:
        """
        Merge the repo's settings.shared.json (if present) into repo_json before merging into merged_json.
        If a merge occurs, write the updated repo_json back to the repo's settings.json file.
        """
        shared_settings_path = (
            self.paths.get_vscode_config_dir(repo.path) / "settings.shared.json"
        )
        repo_settings_path = (
            self.paths.get_vscode_config_dir(repo.path) / "settings.json"
        )
        merged_with_shared = False
        if shared_settings_path.exists():
            shared_settings = soft_read_json_file(shared_settings_path)
            if shared_settings:
                repo_json = deep_merge(shared_settings, repo_json, repo.name)
                merged_with_shared = True
            else:
                logger.debug(
                    f"settings.shared.json for {repo.name} exists but is empty or invalid, skipping merge."
                )
        if merged_with_shared:
            from vscode_multi.utils import write_json_file

            write_json_file(repo_settings_path, repo_json)
        return super()._merge_repo_json(merged_json, repo_json, repo)

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Merge in settings.shared.json
        shared_settings_path = self.paths.vscode_settings_shared_path
        if shared_settings_path.exists():
            shared_settings = soft_read_json_file(shared_settings_path)
            merged_json = deep_merge(merged_json, shared_settings)
        else:
            logger.debug(
                f"Shared settings file not found at {shared_settings_path.name}, skipping."
            )

        # Add Python paths for autocomplete
        repos = load_repos(self.paths)
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


def merge_settings_json(root_dir: Path) -> None:
    paths = Paths(root_dir)
    merger = SettingsFileMerger(paths=paths)
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
    merge_settings_json(root_dir=Path.cwd())
