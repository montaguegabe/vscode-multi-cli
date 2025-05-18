import logging

from cursor_multi.merge_vscode_launch import merge_launch_json
from cursor_multi.merge_vscode_settings import merge_settings_json
from cursor_multi.merge_vscode_tasks import merge_tasks_json

logger = logging.getLogger(__name__)


def merge_vscode_configs():
    """Merge .vscode configuration files from all repositories."""
    # Merge settings.json
    merge_settings_json()

    # Merge launch.json
    merge_launch_json()

    # Merge tasks.json
    merge_tasks_json()


def main():
    merge_vscode_configs()


if __name__ == "__main__":
    main()
