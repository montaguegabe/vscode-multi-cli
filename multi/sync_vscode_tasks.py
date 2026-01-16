import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import click

from multi.paths import Paths
from multi.repos import Repository
from multi.sync_vscode_helpers import VSCodeFileMerger

logger = logging.getLogger(__name__)


def get_required_tasks_from_json(tasks_json: Dict[str, Any]) -> List[str]:
    """Extract tasks marked as required from the tasks.json structure."""
    required_tasks = []

    for task in tasks_json.get("tasks", []):
        if isinstance(task, dict) and task.get("required", False):
            label = task.get("label")
            if label:
                required_tasks.append(label)

    return list(dict.fromkeys(task for task in required_tasks if task is not None))


class TasksFileMerger(VSCodeFileMerger):
    def __init__(self, paths: Paths):
        self.paths = paths
        # Track required tasks declared in multi.json for each repo
        self._multi_json_required_tasks: List[str] = []

    def _get_destination_json_path(self) -> Path:
        return self.paths.vscode_tasks_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return self.paths.get_vscode_config_dir(repo_path) / "tasks.json"

    def _get_repo_defaults(self, repo: Repository) -> Dict[str, Any]:
        return {
            "tasks": {"apply_to_list_items": {"options": {"cwd": "${workspaceFolder}"}}}
        }

    def _merge_repo_json(
        self,
        merged_json: Dict[str, Any],
        repo_json: Dict[str, Any],
        repo: Repository,
    ) -> Dict[str, Any]:
        # Collect required tasks declared in multi.json for this repo
        repo_required_tasks = getattr(repo, "requiredTasks", None)
        if repo_required_tasks and isinstance(repo_required_tasks, list):
            self._multi_json_required_tasks.extend(repo_required_tasks)
            logger.debug(
                f"Found requiredTasks in multi.json for {repo.name}: {repo_required_tasks}"
            )

        return super()._merge_repo_json(merged_json, repo_json, repo)

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Collect required tasks from tasks.json files (marked with required: true)
        json_required_tasks = get_required_tasks_from_json(merged_json)

        # Combine with required tasks from multi.json
        all_required_tasks = list(
            dict.fromkeys(json_required_tasks + self._multi_json_required_tasks)
        )

        if all_required_tasks:
            master_task_name = (
                f"All Required Tasks - {os.path.basename(self.paths.root_dir).title()}"
            )
            if "tasks" not in merged_json:
                merged_json["tasks"] = []

            # Rename any existing task with the same label instead of removing it
            for task in merged_json.get("tasks", []):
                if task.get("label") == master_task_name:
                    task["label"] = f"{master_task_name} (Original)"
                    logger.info(
                        f"Renamed existing task '{master_task_name}' to '{task['label']}'"
                    )

            # Create a compound task that depends on all required tasks
            master_task = {
                "label": master_task_name,
                "dependsOn": all_required_tasks,
                "dependsOrder": "parallel",  # Run all required tasks in parallel
                "problemMatcher": [],
            }

            merged_json["tasks"].append(master_task)
            logger.info(
                f"Created/updated master task '{master_task_name}' in tasks.json"
            )

        return merged_json


def merge_tasks_json(root_dir: Path) -> None:
    merger = TasksFileMerger(paths=Paths(root_dir))
    merger.merge()


@click.command(name="tasks")
def merge_tasks_cmd():
    """Merge tasks.json files from all repositories into the root .vscode directory.

    This command will:
    1. Merge task definitions from all repos using the new merger class.
    2. Set proper working directories for each task using defaults.
    3. Create a master compound task if required tasks exist.
    4. Preserve existing tasks by renaming conflicts.
    """
    logger.info("Merging tasks.json files from all repositories...")
    merge_tasks_json(root_dir=Path.cwd())
