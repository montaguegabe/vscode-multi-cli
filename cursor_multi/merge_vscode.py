import logging

from cursor_multi.merge_vscode_launch import merge_launch_json
from cursor_multi.merge_vscode_settings import merge_settings_json
from cursor_multi.merge_vscode_tasks import merge_tasks_json
from cursor_multi.paths import (
    vscode_launch_path,
    vscode_settings_path,
    vscode_tasks_path,
)
from cursor_multi.repos import load_repos
from cursor_multi.utils import write_json_file

logger = logging.getLogger(__name__)


def clear_vscode_config_files():
    """Delete existing VSCode config files before merging."""
    for file_to_delete in [vscode_launch_path, vscode_tasks_path, vscode_settings_path]:
        file_to_delete.unlink(missing_ok=True)


def merge_vscode_configs():
    """Merge .vscode configuration files from all repositories."""
    clear_vscode_config_files()
    repos = load_repos()

    # Merge settings.json
    merged_settings = merge_settings_json(repos)
    write_json_file(vscode_settings_path, merged_settings)

    # Merge launch.json
    merged_launch = merge_launch_json(repos)
    write_json_file(vscode_launch_path, merged_launch)

    # Merge tasks.json
    merged_tasks = merge_tasks_json(repos)
    write_json_file(vscode_tasks_path, merged_tasks)


def main():
    merge_vscode_configs()


if __name__ == "__main__":
    main()
