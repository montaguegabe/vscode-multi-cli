import logging
from typing import Any, Dict, List

from cursor_multi.merge_vscode_helpers import deep_merge
from cursor_multi.paths import get_vscode_config_dir, vscode_settings_shared_path
from cursor_multi.utils import soft_read_json_file

logger = logging.getLogger(__name__)


def merge_settings_json(repos: List[Any]) -> Dict[str, Any]:
    merged_settings: Dict[str, Any] = {}

    # Merge configs from each repo
    for repo in repos:
        if repo.skip:
            continue

        repo_settings_path = get_vscode_config_dir(repo.path) / "settings.json"
        repo_settings = soft_read_json_file(repo_settings_path)
        merged_settings = deep_merge(merged_settings, repo_settings, repo.name)

    # Merge in settings.shared.json
    shared_settings = soft_read_json_file(vscode_settings_shared_path)
    logger.info("Merging shared settings from settings.shared.json")
    merged_settings = deep_merge(merged_settings, shared_settings)

    # Add Python paths for autocomplete
    python_paths = [repo.name for repo in repos if repo.is_python]
    if python_paths:
        logger.info("Adding Python paths for autocomplete")
        if "python.autoComplete.extraPaths" not in merged_settings:
            merged_settings["python.autoComplete.extraPaths"] = []
        for path_val in python_paths:
            if path_val not in merged_settings["python.autoComplete.extraPaths"]:
                merged_settings["python.autoComplete.extraPaths"].append(path_val)

    return merged_settings
