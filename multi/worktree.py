import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import click

from multi.cli_helpers import common_command_wrapper
from multi.errors import GitError
from multi.git_helpers import (
    check_all_on_same_branch,
    check_all_repos_are_clean,
    check_branch_existence,
)
from multi.git_set_branch import create_and_switch_branch
from multi.paths import Paths
from multi.repos import Repository, load_repos
from multi.sync import sync

logger = logging.getLogger(__name__)


def _run_git(repo_path: Path, args: list[str]) -> None:
    try:
        subprocess.run(
            ["git", *args],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        raise GitError(
            f"Failed to run git {' '.join(args)} in {repo_path}{detail}"
        ) from e


def _create_root_worktree(root_dir: Path, destination: Path, branch_name: str) -> None:
    exists_locally, exists_remotely = check_branch_existence(root_dir, branch_name)

    if exists_locally:
        args = ["worktree", "add", str(destination), branch_name]
    elif exists_remotely:
        args = [
            "worktree",
            "add",
            "-b",
            branch_name,
            str(destination),
            f"origin/{branch_name}",
        ]
    else:
        args = ["worktree", "add", "-b", branch_name, str(destination), "HEAD"]

    _run_git(root_dir, args)
    logger.info(f"Created worktree at {destination}")


def _configured_transfer_paths(paths: Paths, transfer_type: str) -> list[str]:
    worktree_settings = paths.settings.get("worktree", {})
    if not isinstance(worktree_settings, dict):
        raise GitError("multi.json field 'worktree' must be an object.")

    entries = worktree_settings.get(transfer_type, [])
    if entries is None:
        return []
    if not isinstance(entries, list) or not all(
        isinstance(entry, str) for entry in entries
    ):
        raise GitError(
            f"multi.json field 'worktree.{transfer_type}' must be a string array."
        )
    return entries


def _resolve_relative_path(entry: str) -> Path:
    relative_path = Path(entry)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise GitError(
            f"Worktree transfer path must be relative and stay inside the workspace: {entry}"
        )
    return relative_path


def _destination_for_name(root_dir: Path, name: str) -> Path:
    name_path = Path(name)
    if name_path.is_absolute() or len(name_path.parts) != 1 or name in {"", ".", ".."}:
        raise GitError(
            "Worktree NAME must be a single sibling directory name. "
            "Use --branch for branch names that contain path separators."
        )
    return root_dir.parent / name


def _repo_for_path(paths: Paths, relative_path: Path) -> tuple[Path, Path]:
    source_path = paths.root_dir / relative_path
    for repo in load_repos(paths):
        try:
            repo_relative_path = source_path.resolve().relative_to(repo.path.resolve())
        except ValueError:
            continue
        return repo.path, repo_relative_path
    return paths.root_dir, relative_path


def _is_gitignored(repo_path: Path, relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(relative_path)],
        cwd=repo_path,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise GitError(f"Could not check gitignore status for {repo_path / relative_path}")


def _validate_transfer_source(paths: Paths, relative_path: Path) -> Path:
    source_path = paths.root_dir / relative_path
    if not source_path.exists():
        raise GitError(
            f"Configured worktree transfer path does not exist: {relative_path}"
        )

    repo_path, repo_relative_path = _repo_for_path(paths, relative_path)
    if not _is_gitignored(repo_path, repo_relative_path):
        raise GitError(
            f"Configured worktree transfer path is not gitignored: {relative_path}"
        )
    return source_path


def _transfer_path(
    source_path: Path, destination_path: Path, transfer_type: str
) -> None:
    if destination_path.exists() or destination_path.is_symlink():
        logger.info(f"Skipping existing worktree path {destination_path}")
        return

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if transfer_type == "symlink":
        os.symlink(source_path, destination_path)
        logger.info(f"Symlinked {destination_path} -> {source_path}")
    elif source_path.is_dir():
        shutil.copytree(source_path, destination_path)
        logger.info(f"Copied directory {source_path} -> {destination_path}")
    else:
        shutil.copy2(source_path, destination_path)
        logger.info(f"Copied file {source_path} -> {destination_path}")


def _transfer_configured_paths(source_paths: Paths, destination_paths: Paths) -> None:
    for transfer_type in ("symlink", "copy"):
        for entry in _configured_transfer_paths(source_paths, transfer_type):
            relative_path = _resolve_relative_path(entry)
            source_path = _validate_transfer_source(source_paths, relative_path)
            destination_path = destination_paths.root_dir / relative_path
            _transfer_path(source_path, destination_path, transfer_type)


def _checkout_subrepos(
    repos: Iterable[Repository],
    branch_name: str,
    allow_create: bool,
) -> None:
    for repo in repos:
        repo_branch_name = repo.fixed_branch or branch_name
        create_and_switch_branch(
            repo.path,
            repo_branch_name,
            allow_create=allow_create,
        )


def add_worktree(root_dir: Path, name: str, branch_name: str | None = None) -> Path:
    paths = Paths(root_dir)
    if paths.settings.is_monorepo():
        raise click.UsageError(
            "The 'multi worktree add' command is not available in monorepo mode. "
            "Use git directly in the root workspace."
        )

    branch_name = branch_name or name
    destination = _destination_for_name(paths.root_dir, name)
    if destination.exists():
        raise GitError(f"Worktree destination already exists: {destination}")

    check_all_repos_are_clean(paths=paths, raise_error=True)
    all_on_same_branch = check_all_on_same_branch(paths=paths, raise_error=False)
    if not all_on_same_branch:
        logger.warning(
            "Some repos are not on their expected branches. If the target branches "
            "already exist for all repos, this command will fix the situation."
        )

    _create_root_worktree(paths.root_dir, destination, branch_name)
    sync(root_dir=destination)

    destination_paths = Paths(destination)
    _checkout_subrepos(
        load_repos(destination_paths),
        branch_name,
        allow_create=all_on_same_branch,
    )
    _transfer_configured_paths(paths, destination_paths)
    return destination


@click.group(name="worktree")
def worktree_cmd() -> None:
    """Manage sibling git worktrees for a multi workspace."""


@click.command(name="add")
@click.argument("name")
@click.option(
    "--branch",
    "branch_name",
    help="Branch name for the worktree. Defaults to NAME.",
)
def worktree_add_cmd(name: str, branch_name: str | None = None) -> None:
    """Create a sibling worktree.

    NAME: Directory name for the sibling worktree. Used as the branch name when
    --branch is omitted.
    """
    add_worktree(Path.cwd(), name=name, branch_name=branch_name)


worktree_cmd.add_command(common_command_wrapper(worktree_add_cmd))
