import logging
from typing import Any, Dict

from cursor_multi.merge_vscode_helpers import deep_merge
from cursor_multi.paths import paths
from cursor_multi.repos import load_repos
from cursor_multi.utils import (
    apply_defaults_to_structure,
    soft_read_json_file,
    write_json_file,
)

logger = logging.getLogger(__name__)


def merge_tasks_json() -> None:
    # Delete existing file before merging
    paths.vscode_tasks_path.unlink(missing_ok=True)

    merged_tasks_json: Dict[str, Any] = {}
    repos = load_repos()

    # Merge configs from each repo
    for repo in repos:
        if repo.skip:
            logger.debug(f"Skipping {repo.name} for tasks.json")
            continue

        repo_tasks_json_path = paths.get_vscode_config_dir(repo.path) / "tasks.json"
        repo_tasks_json = soft_read_json_file(repo_tasks_json_path)
        defaults = {"tasks": {"*": {"options": {"cwd": "${workspaceFolder}"}}}}
        effective_repo_tasks_json = apply_defaults_to_structure(
            repo_tasks_json, defaults
        )
        merged_tasks_json = deep_merge(
            merged_tasks_json, effective_repo_tasks_json, repo.name
        )

    write_json_file(paths.vscode_tasks_path, merged_tasks_json)
