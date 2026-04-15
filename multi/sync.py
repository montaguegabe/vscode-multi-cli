import logging
import os
import shutil
import tempfile
from pathlib import Path

import click
import git
from git.exc import GitCommandError

from multi.bootstrap import ensure_root_git_repo, ensure_workspace_readme
from multi.cli_helpers import common_command_wrapper
from multi.doctor import find_nested_git_repos_in_monorepo
from multi.git_helpers import get_current_branch
from multi.ignore_files import (
    update_gitignore_with_generated_files,
    update_gitignore_with_repos,
    update_ignore_with_repos,
)
from multi.paths import Paths
from multi.registry import lookup_repo, register_repo
from multi.repos import Repository, load_repos
from multi.sync_github import sync_all_github_actions, sync_github_cmd
from multi.sync_rules import sync_all_rules, sync_rules_cmd
from multi.sync_vscode import merge_vscode_configs, vscode_cmd

logger = logging.getLogger(__name__)


def _is_path_inside(child: Path, parent: Path) -> bool:
    """Check if child path is inside parent path."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _try_symlink_repo(
    repo_config: Repository,
    paths: Paths,
    current_branch: str | None,
) -> bool:
    """Attempt to create a symlink for a repository.

    Returns:
        True if symlink was successfully created, False otherwise.
    """
    # Check if symlinks are enabled globally and for this repo
    global_symlinks = paths.settings.get("allowSymlinks", False)
    if not global_symlinks or not repo_config.allow_symlink:
        return False

    # Look up the repo in the registry
    existing_path = lookup_repo(repo_config.url)
    if not existing_path:
        return False

    # Avoid recursive symlinks - don't symlink if existing path is inside current workspace
    if _is_path_inside(existing_path, paths.root_dir):
        logger.debug(
            f"Existing repo at {existing_path} is inside current workspace, will clone instead"
        )
        return False

    # Check for virtual environments - these contain absolute paths that break with symlinks
    venv_path = existing_path / "venv"
    dot_venv_path = existing_path / ".venv"
    if venv_path.exists() or dot_venv_path.exists():
        venv_name = "venv" if venv_path.exists() else ".venv"
        logger.warning(
            f"⚠️  Cannot symlink {repo_config.name}: source repo contains {venv_name}/, will clone instead"
        )
        return False

    # Try to create the symlink
    try:
        os.symlink(existing_path, repo_config.path)
        logger.info(f"🔗 Symlinked {repo_config.name} -> {existing_path}")

        # Checkout the correct branch if needed
        if current_branch:
            try:
                symlinked_repo = git.Repo(repo_config.path)
                symlinked_repo.git.checkout(current_branch)
                logger.debug(f"Checked out branch {current_branch} in symlinked repo")
            except GitCommandError:
                logger.warning(
                    f"Branch {current_branch} not found in {repo_config.name}, staying on current branch."
                )

        return True
    except OSError as e:
        logger.warning(f"Failed to create symlink for {repo_config.name}: {e}")
        return False


def _clone_repo(
    repo_config: Repository,
    current_branch: str | None,
) -> None:
    """Clone a repository and checkout the appropriate branch."""
    logger.debug(f"Cloning {repo_config.name}...")

    with tempfile.TemporaryDirectory(
        prefix=f"multi-{repo_config.name}-clone-",
    ) as temp_dir:
        temp_repo_path = Path(temp_dir) / repo_config.name

        # First clone the default branch outside the workspace, then move the
        # checked-out repo into place. This avoids checkout conflicts when the
        # workspace root gitignore already manages sub-repo paths.
        cloned_repo = git.Repo.clone_from(repo_config.url, temp_repo_path)

        # Then checkout the same branch as parent repo if it exists
        if current_branch:
            try:
                cloned_repo.git.checkout(current_branch)
                logger.info(
                    f"✅ Cloned {repo_config.name} and checked out branch {current_branch}"
                )
            except GitCommandError:
                logger.warning(
                    f"Branch {current_branch} not found in {repo_config.name}, staying on default branch."
                )

        shutil.move(str(temp_repo_path), str(repo_config.path))


def clone_repos(paths: Paths, ensure_on_same_branch: bool = True):
    """Clone all repositories from the repos.json file.

    Supports symlinking to existing repos from the global registry when:
    - Global allowSymlinks setting is True (default: False)
    - Per-repo allowSymlink setting is True (default: False)
    - An existing clone is found in the registry
    """
    repos = load_repos(paths=paths)

    # Get the current branch of the parent repo
    current_branch = (
        get_current_branch(paths.root_dir) if ensure_on_same_branch else None
    )
    if ensure_on_same_branch:
        logger.info(f"Current branch: {current_branch}")

    for repo_config in repos:
        if repo_config.path.exists():
            # Path already exists - register it and skip
            logger.debug(
                f"{repo_config.name} already exists, registering and skipping..."
            )
            register_repo(repo_config.url, repo_config.path)
            continue

        # Try to symlink first
        if _try_symlink_repo(repo_config, paths, current_branch):
            continue

        # Fall back to cloning
        _clone_repo(repo_config, current_branch)

        # Register the newly cloned repo
        register_repo(repo_config.url, repo_config.path)

    update_gitignore_with_repos(paths=paths)
    update_ignore_with_repos(paths=paths)


def sync(root_dir: Path, ensure_on_same_branch: bool = True):
    """Run all sync operations."""
    logger.info("Syncing...")

    paths = Paths(root_dir)
    ensure_root_git_repo(paths.root_dir)
    ensure_workspace_readme(paths=paths)

    nested_git_repos = find_nested_git_repos_in_monorepo(paths=paths)
    if nested_git_repos:
        logger.warning(
            "monoRepo mode expects listed directories to be part of the root git repo "
            f"(no nested .git). Found nested git repos: {', '.join(nested_git_repos)}."
        )

    if not paths.settings.is_monorepo():
        clone_repos(paths=paths, ensure_on_same_branch=ensure_on_same_branch)

    update_gitignore_with_generated_files(paths=paths)
    merge_vscode_configs(root_dir=root_dir)
    sync_all_rules(root_dir=root_dir)
    sync_all_github_actions(root_dir=root_dir)

    logger.info("✅ Sync complete")


@click.group(name="sync", invoke_without_command=True)
@click.pass_context
def sync_cmd(ctx: click.Context):
    """Sync development environment and configurations.

    If no subcommand is given, performs complete sync:
    1. Clones/updates all repositories
    2. Merges VSCode configurations
    """
    if ctx.invoked_subcommand is None:
        sync(root_dir=Path.cwd())


# Add subcommands
sync_cmd.add_command(common_command_wrapper(vscode_cmd))
sync_cmd.add_command(common_command_wrapper(sync_rules_cmd))
sync_cmd.add_command(common_command_wrapper(sync_github_cmd))
