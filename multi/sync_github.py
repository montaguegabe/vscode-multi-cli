import logging
import re
from pathlib import Path

import click
import yaml

from multi.cli_helpers import get_install_set_from_context
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)

GENERATED_MARKER = "# multi-generated: github-workflow"
WORKFLOW_EXTENSIONS = ("*.yml", "*.yaml")


def _is_generated_workflow(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8") as file:
        first_line = file.readline().strip()
    return first_line == GENERATED_MARKER


def _repo_slug(repo_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", repo_name.strip("/"))
    slug = slug.strip("-")
    return slug or "repo"


def _load_workflow(source_path: Path) -> dict:
    content = source_path.read_text(encoding="utf-8")
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse workflow YAML: {source_path}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError(
            f"Workflow file must contain a top-level object: {source_path}"
        )
    return parsed


def _inject_job_working_directory(workflow: dict, repo_name: str) -> None:
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return

    for _, job in jobs.items():
        if not isinstance(job, dict):
            continue

        defaults = job.get("defaults")
        if defaults is None:
            defaults = {}
            job["defaults"] = defaults
        if not isinstance(defaults, dict):
            continue

        run_defaults = defaults.get("run")
        if run_defaults is None:
            run_defaults = {}
            defaults["run"] = run_defaults

        if isinstance(run_defaults, dict) and "working-directory" not in run_defaults:
            run_defaults["working-directory"] = repo_name


def _is_filename_available(
    destination_dir: Path,
    filename: str,
    reserved_names: set[str],
) -> bool:
    if filename in reserved_names:
        return False

    destination_path = destination_dir / filename
    if not destination_path.exists():
        return True

    return _is_generated_workflow(destination_path)


def _choose_destination_filename(
    destination_dir: Path,
    source_filename: str,
    repo_name: str,
    reserved_names: set[str],
) -> str:
    if _is_filename_available(destination_dir, source_filename, reserved_names):
        return source_filename

    repo_slug = _repo_slug(repo_name)
    prefixed = f"{repo_slug}--{source_filename}"
    if _is_filename_available(destination_dir, prefixed, reserved_names):
        return prefixed

    counter = 2
    while True:
        candidate = f"{repo_slug}-{counter}--{source_filename}"
        if _is_filename_available(destination_dir, candidate, reserved_names):
            return candidate
        counter += 1


def _render_generated_workflow(
    workflow: dict,
    source_display_path: str,
    repo_name: str,
) -> str:
    serialized = yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True)
    headers = [
        GENERATED_MARKER,
        f"# source: {source_display_path}",
        f"# repo: {repo_name}",
        "",
    ]
    return "\n".join(headers) + serialized


def sync_all_github_actions(root_dir: Path, install_set: str | None = None) -> None:
    """Sync GitHub Actions workflow files from monorepo directories to root."""
    paths = Paths(root_dir, install_set=install_set)
    if not paths.settings.is_monorepo():
        logger.debug("Skipping GitHub Actions sync outside monorepo mode")
        return

    logger.info("Syncing GitHub Actions workflows...")
    repos = load_repos(paths=paths)
    destination_dir = paths.root_dir / ".github" / "workflows"
    destination_dir.mkdir(parents=True, exist_ok=True)

    previously_generated_names = {
        path.name
        for pattern in WORKFLOW_EXTENSIONS
        for path in destination_dir.glob(pattern)
        if _is_generated_workflow(path)
    }

    reserved_names: set[str] = set()
    written_names: set[str] = set()

    for repo in repos:
        source_dir = repo.path / ".github" / "workflows"
        if not source_dir.exists():
            logger.debug(f"No workflows directory found for {repo.name}")
            continue

        source_files = sorted(
            [
                workflow_path
                for pattern in WORKFLOW_EXTENSIONS
                for workflow_path in source_dir.glob(pattern)
            ],
            key=lambda path: path.name,
        )

        for source_path in source_files:
            destination_filename = _choose_destination_filename(
                destination_dir=destination_dir,
                source_filename=source_path.name,
                repo_name=repo.name,
                reserved_names=reserved_names,
            )
            reserved_names.add(destination_filename)
            written_names.add(destination_filename)

            workflow = _load_workflow(source_path=source_path)
            _inject_job_working_directory(workflow=workflow, repo_name=repo.name)

            try:
                source_display = str(source_path.relative_to(paths.root_dir))
            except ValueError:
                source_display = str(source_path)

            content = _render_generated_workflow(
                workflow=workflow,
                source_display_path=source_display,
                repo_name=repo.name,
            )
            destination_path = destination_dir / destination_filename
            destination_path.write_text(content, encoding="utf-8")
            logger.info(f"✅ Synced workflow: {destination_filename}")

    stale_generated_files = previously_generated_names - written_names
    for stale_name in stale_generated_files:
        stale_path = destination_dir / stale_name
        if stale_path.exists() and _is_generated_workflow(stale_path):
            stale_path.unlink()
            logger.info(f"🗑️ Removed stale generated workflow: {stale_name}")

    logger.info("✅ GitHub Actions workflow sync complete")


@click.command(name="github")
def sync_github_cmd() -> None:
    """Sync GitHub Actions workflow files into root .github/workflows.

    This command is only available in monorepo mode.
    """
    install_set = get_install_set_from_context()
    paths = Paths(Path.cwd(), install_set=install_set)
    if not paths.settings.is_monorepo():
        raise click.UsageError(
            "The 'multi sync github' command is only available in monorepo mode."
        )
    sync_all_github_actions(root_dir=Path.cwd(), install_set=install_set)
