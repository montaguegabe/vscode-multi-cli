import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import click

from multi.cli_helpers import get_install_set_from_context
from multi.paths import Paths
from multi.repos import Repository
from multi.sync_vscode_helpers import (
    VSCodeFileMerger,
    deep_merge,
    prefix_repo_name_to_path,
)
from multi.utils import soft_read_json_file

logger = logging.getLogger(__name__)


def get_required_launch_configurations(launch_json: Dict[str, Any]) -> List[str]:
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

    def _get_destination_json_path(self) -> Path:
        return self.paths.vscode_launch_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return self.paths.get_vscode_config_dir(repo_path) / "launch.json"

    def _merge_repo_json(
        self,
        merged_json: Dict[str, Any],
        repo_json: Dict[str, Any],
        repo: Repository,
        source_json_path: Path,
    ) -> Dict[str, Any]:
        # Add cwd to configurations unless explicitly provided.
        if "configurations" in repo_json:
            for config in repo_json["configurations"]:
                if isinstance(config, dict):
                    if "cwd" not in config:
                        config["cwd"] = prefix_repo_name_to_path(
                            "${workspaceFolder}", repo.relative_path
                        )

        # Check if repo has requiredCompounds config and mark matching compounds
        required_compounds = getattr(repo, "requiredCompounds", None)
        if required_compounds and isinstance(required_compounds, list):
            for compound in repo_json.get("compounds", []):
                if (
                    isinstance(compound, dict)
                    and compound.get("name") in required_compounds
                ):
                    compound["required"] = True

        # Check if repo has requiredLaunchConfigurations config and mark matching configs
        required_configs = getattr(repo, "requiredLaunchConfigurations", None)
        if required_configs and isinstance(required_configs, list):
            for config in repo_json.get("configurations", []):
                if isinstance(config, dict) and config.get("name") in required_configs:
                    config["required"] = True

        return super()._merge_repo_json(merged_json, repo_json, repo, source_json_path)

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Merge in launch.shared.json (for workspace-level compounds that span repos)
        shared_launch_path = self.paths.vscode_launch_shared_path
        if shared_launch_path.exists():
            shared_launch = soft_read_json_file(shared_launch_path)
            if shared_launch:
                merged_json = deep_merge(merged_json, shared_launch)
                logger.info(
                    f"Merged shared launch config from {shared_launch_path.name}"
                )
            else:
                logger.debug(
                    f"Shared launch file at {shared_launch_path.name} is empty or invalid, skipping."
                )
        else:
            logger.debug(
                f"Shared launch file not found at {shared_launch_path.name}, skipping."
            )

        required_configs = get_required_launch_configurations(merged_json)

        if required_configs:
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
                "configurations": required_configs,
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


def merge_launch_json(root_dir: Path, install_set: str | None = None) -> None:
    merger = LaunchFileMerger(paths=Paths(root_dir, install_set=install_set))
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
    merge_launch_json(root_dir=Path.cwd(), install_set=get_install_set_from_context())
