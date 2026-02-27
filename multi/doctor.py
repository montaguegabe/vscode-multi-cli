import logging
from dataclasses import dataclass, field
from json import JSONDecodeError
from pathlib import Path

import click
import git as gitmodule

from multi.errors import NoRepositoriesError
from multi.git_helpers import is_git_repo_root
from multi.paths import Paths
from multi.repos import Repository, load_repos

logger = logging.getLogger(__name__)


@dataclass
class DoctorReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    def should_fail(self, strict: bool) -> bool:
        return bool(self.errors or (strict and self.warnings))


def find_nested_git_repos_in_monorepo(paths: Paths) -> list[str]:
    if not paths.settings.is_monorepo():
        return []

    try:
        repos = load_repos(paths)
    except (NoRepositoriesError, ValueError):
        return []

    return sorted(repo.name for repo in repos if (repo.path / ".git").exists())


def find_git_repos_on_disk(root_dir: Path) -> set[str]:
    """Find immediate subdirectories of root_dir that are git repositories."""
    result = set()
    try:
        for child in root_dir.iterdir():
            if (
                child.is_dir()
                and not child.name.startswith(".")
                and (child / ".git").is_dir()
            ):
                result.add(child.name)
    except OSError:
        pass
    return result


def find_tracked_subrepos(root_dir: Path, repos: list[Repository]) -> list[str]:
    """Find sub-repos that have files tracked in the workspace git index."""
    try:
        root_repo = gitmodule.Repo(root_dir)
    except (gitmodule.InvalidGitRepositoryError, gitmodule.NoSuchPathError):
        return []

    tracked_prefixes = set()
    for entry in root_repo.index.entries:
        # entry key is (path, stage); check if path starts with a repo name
        path = entry[0]
        for repo in repos:
            # Submodule entries (mode 160000) are handled separately
            if path == repo.name or path.startswith(repo.name + "/"):
                blob = root_repo.index.entries[entry]
                if blob.mode != 0o160000:  # not a submodule
                    tracked_prefixes.add(repo.name)
                break

    return sorted(tracked_prefixes)


def find_subrepo_submodules(root_dir: Path, repos: list[Repository]) -> list[str]:
    """Find sub-repos registered as git submodules in the workspace."""
    try:
        root_repo = gitmodule.Repo(root_dir)
    except (gitmodule.InvalidGitRepositoryError, gitmodule.NoSuchPathError):
        return []

    submodule_paths = {sm.path for sm in root_repo.submodules}
    return sorted(repo.name for repo in repos if repo.name in submodule_paths)


def run_doctor_checks(target_dir: Path) -> DoctorReport:
    report = DoctorReport()

    try:
        paths = Paths(target_dir)
    except FileNotFoundError:
        report.errors.append(
            "Could not find multi.json in this directory or parent directories."
        )
        return report

    report.infos.append(f"Found multi.json at {paths.multi_json_path}")

    try:
        # Access once to validate parseability.
        settings = paths.settings
    except (AssertionError, JSONDecodeError, OSError) as exc:
        report.errors.append(f"Could not parse multi.json: {exc}")
        return report

    if not is_git_repo_root(paths.root_dir):
        report.warnings.append(
            f"Workspace root is not a git repository at {paths.root_dir}. "
            "Run `multi sync` (or `git init -b main`) to initialize it."
        )

    try:
        repos = load_repos(paths)
    except (NoRepositoriesError, ValueError) as exc:
        report.errors.append(str(exc))
        return report

    if settings.is_monorepo():
        nested_git_repos = find_nested_git_repos_in_monorepo(paths)
        if nested_git_repos:
            report.warnings.append(
                "monoRepo mode expects listed directories to be part of the root git repo "
                f"(no nested .git). Found nested git repos: {', '.join(nested_git_repos)}. "
                "Use standard multi-repo mode (monoRepo: false) for independent repos."
            )
    else:
        missing_url_names = [repo.name for repo in repos if not repo.url]
        if missing_url_names:
            report.errors.append(
                "These repos are missing `url` and cannot be managed in standard mode: "
                f"{', '.join(missing_url_names)}."
            )

    # Check if sub-repos are accidentally tracked in the workspace git index
    if is_git_repo_root(paths.root_dir):
        tracked = find_tracked_subrepos(paths.root_dir, repos)
        if tracked:
            report.warnings.append(
                "Sub-repos are tracked in the workspace git index "
                "(they should be .gitignored): "
                f"{', '.join(tracked)}. "
                "Add them to .gitignore and remove from the index with "
                "`git rm -r --cached <repo>`."
            )
        as_submodules = find_subrepo_submodules(paths.root_dir, repos)
        if as_submodules:
            report.warnings.append(
                "Sub-repos are registered as git submodules "
                "(multi does not use submodules): "
                f"{', '.join(as_submodules)}. "
                "Remove them with `git rm --cached <repo>` and delete "
                "the entry from .gitmodules."
            )

    # Check for mismatches between repos on disk and multi.json
    declared_names = {repo.name for repo in repos}
    on_disk = find_git_repos_on_disk(paths.root_dir)

    undeclared = sorted(on_disk - declared_names)
    if undeclared:
        report.warnings.append(
            "Git repos found on disk but not declared in multi.json: "
            f"{', '.join(undeclared)}. Add them to multi.json or remove them."
        )

    missing_on_disk = sorted(declared_names - on_disk)
    if missing_on_disk:
        report.warnings.append(
            "Repos declared in multi.json but not found on disk: "
            f"{', '.join(missing_on_disk)}. Run `multi sync` to clone them."
        )

    return report


def _print_report(report: DoctorReport) -> None:
    logger.info("Running diagnostics...")
    for info in report.infos:
        logger.info(f"ℹ️  {info}")
    for warning in report.warnings:
        logger.warning(f"⚠️  {warning}")
    for error in report.errors:
        logger.error(f"❌ {error}")

    if not (report.errors or report.warnings):
        logger.info("✅ No issues found.")


@click.command(name="doctor")
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Fail on warnings in addition to errors.",
)
def doctor_cmd(strict: bool) -> None:
    """Diagnose common workspace configuration issues."""
    report = run_doctor_checks(Path.cwd())
    _print_report(report)
    if report.should_fail(strict=strict):
        raise click.ClickException("Doctor checks failed.")
