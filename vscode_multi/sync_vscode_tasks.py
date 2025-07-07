import logging
from pathlib import Path
from typing import Any, Dict

import click

from vscode_multi.paths import paths
from vscode_multi.repos import Repository
from vscode_multi.sync_vscode_helpers import VSCodeFileMerger

logger = logging.getLogger(__name__)


class TasksFileMerger(VSCodeFileMerger):
    def _get_destination_json_path(self) -> Path:
        return paths.vscode_tasks_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return paths.get_vscode_config_dir(repo_path) / "tasks.json"

    def _get_repo_defaults(self, repo: Repository) -> Dict[str, Any]:
        return {
            "tasks": {"apply_to_list_items": {"options": {"cwd": "${workspaceFolder}"}}}
        }


def merge_tasks_json() -> None:
    merger = TasksFileMerger()
    merger.merge()


@click.command(name="tasks")
def merge_tasks_cmd():
    """Merge tasks.json files from all repositories into the root .vscode directory.

    This command will:
    1. Merge task definitions from all repos using the new merger class.
    2. Set proper working directories for each task using defaults.
    """
    logger.info("Merging tasks.json files from all repositories...")
    merge_tasks_json()
