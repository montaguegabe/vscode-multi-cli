import click

from cursor_multi.cli_helpers import common_command_wrapper
from cursor_multi.git_merge_branch import merge_branch_cmd
from cursor_multi.git_run import git_cmd
from cursor_multi.git_set_branch import set_branch_cmd
from cursor_multi.init import init_cmd
from cursor_multi.sync import sync_cmd


@click.group()
def main():
    """Cursor Multi - Manage multiple Git repositories in Cursor IDE.

    This CLI tool enables seamless work across multiple Git repositories within Cursor IDE.
    Key features:
    - Synchronize Git operations across root and sub-repositories
    - Auto-sync Cursor rule (.mcd) files from sub-repositories
    - Merge .vscode configurations (launch.json, tasks.json, settings.json)
    - Manage consistent branch states across all repositories
    """
    pass


main.add_command(common_command_wrapper(merge_branch_cmd))
main.add_command(common_command_wrapper(set_branch_cmd))
main.add_command(common_command_wrapper(sync_cmd))
main.add_command(common_command_wrapper(git_cmd))
main.add_command(common_command_wrapper(init_cmd))

if __name__ == "__main__":
    main()
