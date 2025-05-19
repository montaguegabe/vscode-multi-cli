import logging

import click

from cursor_multi.cli_helpers import common_command_wrapper
from cursor_multi.sync_vscode_launch import merge_launch_cmd, merge_launch_json
from cursor_multi.sync_vscode_settings import merge_settings_cmd, merge_settings_json
from cursor_multi.sync_vscode_tasks import merge_tasks_cmd, merge_tasks_json

logger = logging.getLogger(__name__)


def merge_vscode_configs():
    logger.info("Merging .vscode configuration files from all repositories...")
    # Merge settings.json
    merge_settings_json()

    # Merge launch.json
    merge_launch_json()

    # Merge tasks.json
    merge_tasks_json()

    logger.info("Done merging .vscode configuration files!")


@click.group(name="vscode", invoke_without_command=True)
@click.pass_context
def vscode_cmd(ctx: click.Context):
    """Manage VSCode configuration files across repositories.

    If no subcommand is given, merges all (settings, launch, tasks).
    """
    if ctx.invoked_subcommand is None:
        merge_vscode_configs()


# Add subcommands
vscode_cmd.add_command(common_command_wrapper(merge_launch_cmd))
vscode_cmd.add_command(common_command_wrapper(merge_settings_cmd))
vscode_cmd.add_command(common_command_wrapper(merge_tasks_cmd))
