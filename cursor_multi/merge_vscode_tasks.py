import logging
from typing import Any, Dict, List

from cursor_multi.merge_vscode_helpers import apply_defaults_to_structure, deep_merge
from cursor_multi.paths import get_vscode_config_dir
from cursor_multi.utils import soft_read_json_file

logger = logging.getLogger(__name__)


def merge_tasks_json(repos: List[Any]) -> Dict[str, Any]:
    merged_tasks_json: Dict[str, Any] = {}

    # Merge configs from each repo
    for repo in repos:
        if repo.skip:
            logger.debug(f"Skipping {repo.name} for tasks.json")
            continue

        repo_tasks_json_path = get_vscode_config_dir(repo.path) / "tasks.json"
        repo_tasks_json = soft_read_json_file(repo_tasks_json_path)
        defaults = {"tasks": {"*": {"options": {"cwd": "${workspaceFolder}"}}}}
        effective_repo_tasks_json = apply_defaults_to_structure(
            repo_tasks_json, defaults
        )
        merged_tasks_json = deep_merge(
            merged_tasks_json, effective_repo_tasks_json, repo.name
        )

    return merged_tasks_json
