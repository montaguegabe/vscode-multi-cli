import logging
import os
from typing import Any, Dict, List

from cursor_multi.merge_vscode_helpers import (
    deep_merge,
    prefix_repo_name_to_path,
)
from cursor_multi.paths import paths
from cursor_multi.repos import load_repos
from cursor_multi.utils import (
    apply_defaults_to_structure,
    soft_read_json_file,
    write_json_file,
)

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
            required_configs.append(config.get("name"))

    return list(
        dict.fromkeys(required_configs)
    )  # Remove duplicates while preserving order


def merge_launch_json() -> None:
    # Delete existing file before merging
    paths.vscode_launch_path.unlink(missing_ok=True)

    merged_launch_json: Dict[str, Any] = {}
    repos = load_repos()

    # Merge configs from each repo
    for repo in repos:
        if repo.skip:
            logger.debug(f"Skipping {repo.name} for launch.json")
            continue

        repo_launch_json_path = paths.get_vscode_config_dir(repo.path) / "launch.json"
        repo_launch_json = soft_read_json_file(repo_launch_json_path)

        defaults = {
            "configurations": {
                "*": {"cwd": prefix_repo_name_to_path("${workspaceFolder}", repo.name)}
            }
        }
        effective_repo_launch_json = apply_defaults_to_structure(
            repo_launch_json, defaults
        )
        merged_launch_json = deep_merge(
            merged_launch_json, effective_repo_launch_json, repo.name
        )

    # Create a master compound that includes all configurations marked with required: true
    required_configs = get_required_launch_configurations(merged_launch_json)

    if required_configs:
        master_compound_name = os.path.basename(paths.root_dir).title()
        if "compounds" not in merged_launch_json:
            merged_launch_json["compounds"] = []

        # Rename any existing compound with the same name instead of removing it
        for compound in merged_launch_json["compounds"]:
            if compound.get("name") == master_compound_name:
                compound["name"] = f"{master_compound_name} (Original)"

        master_compound = {
            "name": master_compound_name,
            "configurations": required_configs,
        }

        merged_launch_json["compounds"].append(master_compound)
        logger.info(
            f"Created/updated master compound '{master_compound_name}' in launch.json"
        )

    write_json_file(paths.vscode_launch_path, merged_launch_json)
