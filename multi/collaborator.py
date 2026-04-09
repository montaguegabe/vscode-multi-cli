import logging
import shutil
import subprocess
from pathlib import Path

import click
import git

from multi.cli_helpers import common_command_wrapper
from multi.paths import Paths
from multi.repo_urls import parse_github_repo_slug
from multi.repos import load_repos

logger = logging.getLogger(__name__)


def _ensure_gh_available() -> str:
    gh_path = shutil.which("gh")
    if gh_path is None:
        raise click.ClickException(
            "GitHub CLI `gh` is required for collaborator management."
        )
    return gh_path


def _run_gh_api(
    gh_path: str,
    *,
    method: str,
    endpoint: str,
    fields: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [gh_path, "api", "--method", method, endpoint]
    if fields:
        for key, value in fields.items():
            cmd.extend(["-f", f"{key}={value}"])

    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        message = stderr or stdout or str(exc)
        raise click.ClickException(message) from exc


def _load_workspace_github_repo_slug(paths: Paths) -> str | None:
    try:
        repo = git.Repo(paths.root_dir)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        return None

    origin = next((remote for remote in repo.remotes if remote.name == "origin"), None)
    if origin is None:
        return None

    return parse_github_repo_slug(origin.url)


def _dedupe_repo_targets(
    repo_targets: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    seen_slugs: set[str] = set()
    unique_targets: list[tuple[str, str]] = []

    for label, slug in repo_targets:
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        unique_targets.append((label, slug))

    return unique_targets


def _load_github_repo_targets(paths: Paths) -> list[tuple[str, str]]:
    repo_targets: list[tuple[str, str]] = []
    invalid_repos: list[str] = []

    workspace_slug = _load_workspace_github_repo_slug(paths)
    if workspace_slug:
        repo_targets.append(("workspace", workspace_slug))

    for repo in load_repos(paths):
        if not repo.url:
            invalid_repos.append(repo.name)
            continue

        slug = parse_github_repo_slug(repo.url)
        if slug is None:
            invalid_repos.append(repo.name)
            continue

        repo_targets.append((repo.name, slug))

    if invalid_repos:
        repo_list = ", ".join(sorted(invalid_repos))
        raise click.ClickException(
            "Collaborator management currently supports only GitHub-hosted repos. "
            f"Unsupported repos: {repo_list}"
        )

    unique_targets = _dedupe_repo_targets(repo_targets)
    if not unique_targets:
        raise click.ClickException(
            "No GitHub-hosted repositories were found in this workspace."
        )

    return unique_targets


def _verify_user_exists(gh_path: str, username: str) -> None:
    _run_gh_api(
        gh_path,
        method="GET",
        endpoint=f"users/{username}",
    )


def _confirm_across_repos(
    *,
    action: str,
    username: str,
    repo_targets: list[tuple[str, str]],
    yes: bool,
) -> None:
    if yes:
        return

    repo_list = "\n".join(f"- {label}: {slug}" for label, slug in repo_targets)
    confirmed = click.confirm(
        f"{action.title()} collaborator '{username}' in these repos?\n{repo_list}",
        default=False,
    )
    if not confirmed:
        raise click.ClickException("Operation cancelled.")


def _manage_collaborator(
    *,
    action: str,
    username: str,
    permission: str | None,
    yes: bool,
) -> None:
    paths = Paths(Path.cwd())
    gh_path = _ensure_gh_available()
    repo_targets = _load_github_repo_targets(paths)
    failures: list[tuple[str, str]] = []

    _verify_user_exists(gh_path, username)
    _confirm_across_repos(
        action=action,
        username=username,
        repo_targets=repo_targets,
        yes=yes,
    )

    for _, slug in repo_targets:
        endpoint = f"repos/{slug}/collaborators/{username}"
        try:
            if action == "add":
                logger.info(f"Adding collaborator {username} to {slug}")
                _run_gh_api(
                    gh_path,
                    method="PUT",
                    endpoint=endpoint,
                    fields={"permission": permission or "push"},
                )
            else:
                logger.info(f"Removing collaborator {username} from {slug}")
                _run_gh_api(
                    gh_path,
                    method="DELETE",
                    endpoint=endpoint,
                )
        except click.ClickException as exc:
            message = exc.message or str(exc)
            logger.error(f"Failed {action} collaborator {username} on {slug}: {message}")
            failures.append((slug, message))

    if failures:
        failure_lines = "\n".join(f"- {slug}: {message}" for slug, message in failures)
        raise click.ClickException(
            f"Finished {action} collaborator {username} with failures:\n{failure_lines}"
        )

    logger.info(
        f"✅ Finished {action} collaborator {username} across all workspace repos"
    )


@click.group(name="collaborator")
def collaborator_cmd() -> None:
    """Manage GitHub collaborators across all workspace repositories."""


@click.command(name="add")
@click.argument("username")
@click.option(
    "--permission",
    type=click.Choice(["pull", "push", "admin", "maintain", "triage"]),
    default="push",
    show_default=True,
    help="Repository permission to grant.",
)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip the confirmation prompt.",
)
def collaborator_add_cmd(username: str, permission: str, yes: bool) -> None:
    """Add a GitHub collaborator to every repo in this workspace."""
    _manage_collaborator(
        action="add",
        username=username,
        permission=permission,
        yes=yes,
    )


@click.command(name="remove")
@click.argument("username")
@click.option(
    "--yes",
    is_flag=True,
    help="Skip the confirmation prompt.",
)
def collaborator_remove_cmd(username: str, yes: bool) -> None:
    """Remove a GitHub collaborator from every repo in this workspace."""
    _manage_collaborator(
        action="remove",
        username=username,
        permission=None,
        yes=yes,
    )


collaborator_cmd.add_command(common_command_wrapper(collaborator_add_cmd))
collaborator_cmd.add_command(common_command_wrapper(collaborator_remove_cmd))
