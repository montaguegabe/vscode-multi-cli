import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import click

from multi.paths import Paths
from multi.repos import Repository
from multi.sync_vscode_helpers import (
    VSCodeFileMerger,
    prefix_repo_name_to_path,
)

logger = logging.getLogger(__name__)


def get_required_launch_configs_from_json(launch_json: Dict[str, Any]) -> List[str]:
    """Extract required launch configurations from launch.json structure."""
    required_configs = []

    # Collect required configurations from required compounds
    for compound in launch_json.get("compounds", []):
        if compound.get("required", False) and "configurations" in compound:
            required_configs.extend(compound["configurations"])

    # Collect standalone required configurations
    for config in launch_json.get("configurations", []):
        if isinstance(config, dict) and config.get("required", False):
            name = config.get("name")
            if name:
                required_configs.append(name)

    return list(
        dict.fromkeys(config for config in required_configs if config is not None)
    )


class LaunchFileMerger(VSCodeFileMerger):
    def __init__(self, paths: Paths):
        self.paths = paths
        # Track required launch configs declared in multi.json for each repo
        self._multi_json_required_configs: List[str] = []

    def _get_destination_json_path(self) -> Path:
        return self.paths.vscode_launch_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return self.paths.get_vscode_config_dir(repo_path) / "launch.json"

    def _get_repo_defaults(self, repo: Repository) -> Dict[str, Any]:
        return {
            "configurations": {
                "apply_to_list_items": {
                    "cwd": prefix_repo_name_to_path("${workspaceFolder}", repo.name)
                }
            }
        }

    def _merge_repo_json(
        self,
        merged_json: Dict[str, Any],
        repo_json: Dict[str, Any],
        repo: Repository,
    ) -> Dict[str, Any]:
        # Collect required launch configs declared in multi.json for this repo
        repo_required_configs = getattr(repo, "requiredLaunchConfigs", None)
        if repo_required_configs and isinstance(repo_required_configs, list):
            self._multi_json_required_configs.extend(repo_required_configs)
            logger.debug(
                f"Found requiredLaunchConfigs in multi.json for {repo.name}: {repo_required_configs}"
            )

        return super()._merge_repo_json(merged_json, repo_json, repo)

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Collect required configs from launch.json files (marked with required: true)
        json_required_configs = get_required_launch_configs_from_json(merged_json)

        # Combine with required configs from multi.json
        all_required_configs = list(
            dict.fromkeys(json_required_configs + self._multi_json_required_configs)
        )

        if all_required_configs:
            master_compound_name = os.path.basename(self.paths.root_dir).title()
            if "compounds" not in merged_json:
                merged_json["compounds"] = []

            # Rename any existing compound with the same name instead of removing it
            for compound in merged_json.get("compounds", []):
                if compound.get("name") == master_compound_name:
                    compound["name"] = f"{master_compound_name} (Original)"
                    logger.info(
                        f"Renamed existing compound '{master_compound_name}' to '{compound['name']}'"
                    )

            master_compound = {
                "name": master_compound_name,
                "configurations": all_required_configs,
            }

            # Add preLaunchTask to run the master task if it exists
            master_task_name = f"All Required Tasks - {master_compound_name}"
            master_compound["preLaunchTask"] = master_task_name
            logger.debug(f"Added preLaunchTask '{master_task_name}' to master compound")

            merged_json["compounds"].append(master_compound)
            logger.info(
                f"Created/updated master compound '{master_compound_name}' in launch.json"
            )
        return merged_json


def merge_launch_json(root_dir: Path) -> None:
    merger = LaunchFileMerger(paths=Paths(root_dir))
    merger.merge()


@click.command(name="launch")
def merge_launch_cmd():
    """Merge launch.json files from all repositories into the root .vscode directory.

    This command will:
    1. Merge debug/launch configurations from all repos using the new merger class.
    2. Create a master compound configuration if required configs exist.
    3. Preserve existing compounds by renaming conflicts.
    """
    logger.info("Merging launch.json files from all repositories...")
    merge_launch_json(root_dir=Path.cwd())
