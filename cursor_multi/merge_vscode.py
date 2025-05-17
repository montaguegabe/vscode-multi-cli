import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from .utils import get_app_packages, get_root, load_repos

logger = logging.getLogger(__name__)

# Keys to skip when merging VSCode configurations
SKIP_KEYS = [
    "workbench.colorCustomizations",
]


def soft_load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file if it exists, otherwise return an empty dict."""
    if path.exists():
        try:
            with path.open("r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {path}, skipping...")
    return {}


def prefix_repo_name_to_path(value: str, repo_name: str) -> str:
    if f"${{workspaceFolder}}/{repo_name}" in value:
        return value
    return value.replace("${workspaceFolder}", f"${{workspaceFolder}}/{repo_name}")


def prefix_repo_name_to_path_recursive(value: Any, repo_name: str) -> Any:
    """
    Recursively adjust workspace folder paths in values.

    Args:
        value: The value to process
        repo_name: Name of the repository to add to workspace folder paths
    """
    if isinstance(value, str) and "${workspaceFolder}" in value:
        return prefix_repo_name_to_path(value, repo_name)
    elif isinstance(value, dict):
        return {
            k: prefix_repo_name_to_path_recursive(v, repo_name)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [prefix_repo_name_to_path_recursive(item, repo_name) for item in value]
    return value


def collect_compound_configurations(
    compounds: List[Dict[str, Any]], merged_config: Dict[str, Any]
) -> List[str]:
    configs = []

    # Collect from required compounds
    for compound in compounds:
        if compound.get("required", False) and "configurations" in compound:
            configs.extend(compound["configurations"])

    # Collect standalone required configurations
    if "configurations" in merged_config:
        for config in merged_config["configurations"]:
            if isinstance(config, dict) and config.get("required", False):
                configs.append(config.get("name"))

    return list(dict.fromkeys(configs))  # Remove duplicates while preserving order


def deep_merge(
    base: Dict[str, Any], override: Dict[str, Any], repo_name: str | None = None
) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries, with override taking precedence.
    Lists are concatenated rather than overridden.

    Args:
        base: Base dictionary to merge into
        override: Dictionary to merge from
        repo_name: Name of the repository being merged from, used to adjust workspace paths
    """
    merged = base.copy()

    for key, value in override.items():
        # Skip keys that we don't want to merge
        if key in SKIP_KEYS:
            continue

        # Special handling for launch.json configurations
        if key == "configurations" and isinstance(value, list) and repo_name:
            # Process each launch configuration
            for config in value:
                if isinstance(config, dict) and "cwd" not in config:
                    # Add cwd to the configuration only if it doesn't exist
                    config["cwd"] = prefix_repo_name_to_path(
                        "${workspaceFolder}", repo_name
                    )

        # Special handling for tasks.json tasks
        if key == "tasks" and isinstance(value, list) and repo_name:
            # Process each task configuration
            for task in value:
                if isinstance(task, dict):
                    if "options" not in task:
                        task["options"] = {}
                    if "cwd" not in task["options"]:
                        task["options"]["cwd"] = prefix_repo_name_to_path(
                            "${workspaceFolder}", repo_name
                        )

        # Adjust workspace folder paths in the value if repo_name is provided
        if repo_name:
            value = prefix_repo_name_to_path_recursive(value, repo_name)

        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value, repo_name)
        elif (
            key in merged and isinstance(merged[key], list) and isinstance(value, list)
        ):
            # For lists, concatenate and remove duplicates while preserving order
            merged[key] = merged[key] + [x for x in value if x not in merged[key]]
        else:
            merged[key] = value

    return merged


def merge_vscode_configs():
    """Merge .vscode configuration files from all repositories."""
    git_root = get_root()

    # Delete existing launch.json and tasks.json
    for file_to_delete in ["launch.json", "tasks.json"]:
        file_path = os.path.join(git_root, ".vscode", file_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  Deleted existing {file_to_delete}")

    repos = load_repos()
    repo_names = [repo_url.split("/")[-1] for repo_url in repos]
    root_folder_name = os.path.basename(git_root).title()

    # Get list of app packages to skip
    app_packages = get_app_packages(repo_names)

    # VSCode config files to merge
    config_files = ["settings.json", "launch.json", "tasks.json"]

    for config_file in config_files:
        print(f"\n🔄 Merging {config_file} from all repositories...")

        # Start with the root config if it exists
        root_config_path = os.path.join(git_root, ".vscode", config_file)
        merged_config = load_json_file(root_config_path)

        # For settings.json, add Python paths
        if config_file == "settings.json":
            # Add app packages and web to python.autoComplete.extraPaths
            python_paths = app_packages + ["web"]
            if "python.autoComplete.extraPaths" not in merged_config:
                merged_config["python.autoComplete.extraPaths"] = []
            merged_config["python.autoComplete.extraPaths"].extend(
                [
                    path
                    for path in python_paths
                    if path not in merged_config["python.autoComplete.extraPaths"]
                ]
            )

        # Merge configs from each repo
        for repo_name in repo_names:
            # Skip app packages
            if repo_name in app_packages:
                print(f"⏭️  Skipping {repo_name} (app package)")
                continue

            repo_config_path = os.path.join(git_root, repo_name, ".vscode", config_file)
            repo_config = soft_load_json_file(repo_config_path)

            if repo_config:
                print(f"📦 Merging config from {repo_name}")
                merged_config = deep_merge(merged_config, repo_config, repo_name)

        # For settings.json, merge in @settings.shared.json at the end
        if config_file == "settings.json":
            shared_settings_path = os.path.join(
                git_root, ".vscode", "@settings.shared.json"
            )
            shared_settings = soft_load_json_file(shared_settings_path)
            if shared_settings:
                print("📦 Merging shared settings from @settings.shared.json")
                merged_config = deep_merge(merged_config, shared_settings)

        # For launch.json, create a master compound that includes all configurations
        if config_file == "launch.json" and merged_config:
            all_configs = []

            # Collect configurations from required compounds and standalone required configurations
            if "compounds" in merged_config or "configurations" in merged_config:
                all_configs = collect_compound_configurations(
                    merged_config.get("compounds", []), merged_config
                )

            # Add the master compound if we have configurations
            if all_configs:
                if "compounds" not in merged_config:
                    merged_config["compounds"] = []

                # Create the master compound with the root folder name
                master_compound = {
                    "name": root_folder_name,
                    "configurations": all_configs,
                }

                # Remove any existing compound with the same name
                merged_config["compounds"] = [
                    compound
                    for compound in merged_config["compounds"]
                    if compound.get("name") != root_folder_name
                ]

                merged_config["compounds"].append(master_compound)

        # Write the merged config back to the root .vscode directory
        if merged_config:
            os.makedirs(os.path.join(git_root, ".vscode"), exist_ok=True)
            with open(root_config_path, "w") as f:
                json.dump(merged_config, f, indent=4)
            print(f"✅ Successfully merged {config_file}")
        else:
            print(f"ℹ️  No {config_file} files found to merge")


def main():
    print("🚀 Running post-setup tasks...")
    merge_vscode_configs()
    print("\n✨ Post-setup tasks completed successfully!")


if __name__ == "__main__":
    main()
