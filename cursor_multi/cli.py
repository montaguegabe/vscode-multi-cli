import click

from cursor_multi.cli_helpers import common_command_wrapper
from cursor_multi.git_merge_branch import merge_branch_cmd
from cursor_multi.git_set_branch import set_branch_cmd
from cursor_multi.merge_cursor import merge_rules_cmd
from cursor_multi.merge_vscode import vscode_cmd
from cursor_multi.sync import sync_cmd


@click.group()
def main():
    """Cursor Multi - A tool for managing multiple Git repositories.

    This CLI tool provides commands for performing Git operations across multiple
    repositories simultaneously. It operates on both the root repository and all
    configured sub-repositories.
    """
    pass


main.add_command(common_command_wrapper(merge_branch_cmd))
main.add_command(common_command_wrapper(set_branch_cmd))
main.add_command(common_command_wrapper(merge_rules_cmd))
main.add_command(common_command_wrapper(vscode_cmd))
main.add_command(common_command_wrapper(sync_cmd))

if __name__ == "__main__":
    main()
