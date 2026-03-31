import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import click

from multi.repo_urls import (
    derive_explicit_local_name,
    derive_repo_slug_from_url,
)
from multi.sync import sync

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InitRepoConfig:
    url: str
    description: str | None = None
    name: str | None = None


def collect_repo_configs() -> list[InitRepoConfig]:
    """Interactively collect repository URLs and descriptions from the user."""
    repo_configs: list[InitRepoConfig] = []
    collect_descriptions = True

    while True:
        url = click.prompt(
            "Enter a repository URL (or press Enter to finish)",
            default="",
            show_default=False,
        )
        if not url:
            if not repo_configs:
                if not click.confirm(
                    "No repositories added. Do you want to finish anyway?"
                ):
                    continue
            break

        if collect_descriptions:
            description = click.prompt(
                "Enter a description for this repo (or press Enter to skip descriptions)",
                default="",
                show_default=False,
            )
            if description:
                repo_configs.append(InitRepoConfig(url=url, description=description))
            else:
                collect_descriptions = False
                repo_configs = [
                    InitRepoConfig(url=config.url) for config in repo_configs
                ]
                repo_configs.append(InitRepoConfig(url=url))
        else:
            repo_configs.append(InitRepoConfig(url=url))

    return repo_configs


def create_multi_json(repo_configs: list[InitRepoConfig]) -> None:
    """Create the multi.json file with the provided repository config."""
    repos = []
    for config in repo_configs:
        repo_config = {"url": config.url}
        if config.name:
            repo_config["name"] = config.name
        if config.description:
            repo_config["description"] = config.description
        repos.append(repo_config)

    config = {"repos": repos}

    multi_json_path = Path.cwd() / "multi.json"
    with multi_json_path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Add newline at end of file


def commit_changes() -> None:
    """Stage and commit all changes."""
    import git

    repo = git.Repo(Path.cwd())
    repo.git.add(all=True)
    repo.index.commit("Multi init: Configure multi workspace")


def _validate_description_count(
    descriptions: tuple[str, ...],
    repo_count: int,
    *,
    option_name: str,
    target_option_name: str,
) -> None:
    if descriptions and len(descriptions) != repo_count:
        raise click.UsageError(
            f"{option_name} must be provided exactly once per {target_option_name}."
        )


def _github_repo_slug_to_url(slug: str, clone_protocol: str) -> str:
    if clone_protocol == "ssh":
        return f"git@github.com:{slug}.git"
    return f"https://github.com/{slug}"


def _apply_default_local_names(
    repo_configs: list[InitRepoConfig], workspace_name: str
) -> list[InitRepoConfig]:
    if not workspace_name:
        return repo_configs

    slugs = [derive_repo_slug_from_url(config.url) for config in repo_configs]
    candidates = [
        derive_explicit_local_name(config.url, workspace_name)
        for config in repo_configs
    ]

    untouched_slugs = {
        slug
        for slug, candidate in zip(slugs, candidates, strict=False)
        if not candidate
    }
    candidate_counts: dict[str, int] = {}
    for candidate in candidates:
        if candidate:
            candidate_counts[candidate] = candidate_counts.get(candidate, 0) + 1

    assigned_names: set[str] = set()
    result: list[InitRepoConfig] = []
    for config, candidate in zip(repo_configs, candidates, strict=False):
        if (
            candidate
            and candidate_counts[candidate] == 1
            and candidate not in untouched_slugs
            and candidate not in assigned_names
        ):
            assigned_names.add(candidate)
            result.append(
                InitRepoConfig(
                    url=config.url,
                    description=config.description,
                    name=candidate,
                )
            )
        else:
            result.append(config)

    return result


def _create_github_repo(
    slug: str,
    *,
    visibility: str,
    description: str | None,
) -> None:
    gh_path = shutil.which("gh")
    if gh_path is None:
        raise click.ClickException(
            "GitHub CLI `gh` is required when using --github-repo."
        )

    cmd = [gh_path, "repo", "create", slug, f"--{visibility}"]
    if description:
        cmd.extend(["--description", description])

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        message = stderr or stdout or str(exc)
        raise click.ClickException(
            f"Failed to create GitHub repo '{slug}': {message}"
        ) from exc


def _build_non_interactive_repo_configs(
    *,
    workspace_name: str,
    repo_urls: tuple[str, ...],
    repo_descriptions: tuple[str, ...],
    github_repos: tuple[str, ...],
    github_descriptions: tuple[str, ...],
    github_visibility: str,
    github_clone_protocol: str,
) -> list[InitRepoConfig]:
    _validate_description_count(
        repo_descriptions,
        len(repo_urls),
        option_name="--repo-description",
        target_option_name="--repo",
    )
    _validate_description_count(
        github_descriptions,
        len(github_repos),
        option_name="--github-description",
        target_option_name="--github-repo",
    )

    repo_configs = [
        InitRepoConfig(url=url, description=repo_descriptions[index] or None)
        for index, url in enumerate(repo_urls)
    ]

    for index, slug in enumerate(github_repos):
        if slug.count("/") != 1:
            raise click.UsageError(
                "--github-repo must be in OWNER/REPO format so multi can write the "
                "created remote URL to multi.json."
            )

        description = github_descriptions[index] or None
        _create_github_repo(
            slug,
            visibility=github_visibility,
            description=description,
        )
        repo_configs.append(
            InitRepoConfig(
                url=_github_repo_slug_to_url(slug, github_clone_protocol),
                description=description,
            )
        )

    return _apply_default_local_names(repo_configs, workspace_name)


@click.command(name="init")
@click.option(
    "--repo",
    "repo_urls",
    multiple=True,
    help="Repository URL to include. Repeat to initialize non-interactively.",
)
@click.option(
    "--repo-description",
    "repo_descriptions",
    multiple=True,
    help="Description for the corresponding --repo. Repeat in the same order.",
)
@click.option(
    "--github-repo",
    "github_repos",
    multiple=True,
    help="GitHub repository to create via gh in OWNER/REPO format.",
)
@click.option(
    "--github-description",
    "github_descriptions",
    multiple=True,
    help=(
        "Description for the corresponding --github-repo. Also passed to "
        "gh repo create."
    ),
)
@click.option(
    "--github-visibility",
    type=click.Choice(["private", "public", "internal"], case_sensitive=False),
    default="private",
    show_default=True,
    help="Visibility to use for each --github-repo.",
)
@click.option(
    "--github-clone-protocol",
    type=click.Choice(["https", "ssh"], case_sensitive=False),
    default="https",
    show_default=True,
    help="Clone URL format written to multi.json for created GitHub repos.",
)
def init_cmd(
    repo_urls: tuple[str, ...],
    repo_descriptions: tuple[str, ...],
    github_repos: tuple[str, ...],
    github_descriptions: tuple[str, ...],
    github_visibility: str,
    github_clone_protocol: str,
):
    """Initialize a new multi workspace.

    This command will:
    1. Collect repository URLs interactively or from CLI options
    2. Create multi.json configuration file (with descriptions if provided)
    3. Run sync (which initializes git and README if needed)
    4. Commit the changes
    """
    logger.info("Initializing multi workspace...")

    has_non_interactive_inputs = bool(repo_urls or github_repos)
    workspace_name = Path.cwd().name

    if has_non_interactive_inputs:
        repo_configs = _build_non_interactive_repo_configs(
            workspace_name=workspace_name,
            repo_urls=repo_urls,
            repo_descriptions=repo_descriptions,
            github_repos=github_repos,
            github_descriptions=github_descriptions,
            github_visibility=github_visibility.lower(),
            github_clone_protocol=github_clone_protocol.lower(),
        )
    else:
        repo_configs = _apply_default_local_names(
            collect_repo_configs(),
            workspace_name,
        )

    # Create multi.json (includes descriptions if provided)
    create_multi_json(repo_configs)
    logger.info("Created multi.json configuration")

    # Run sync (this will generate repo-directories.mdc from descriptions in multi.json)
    sync(root_dir=Path.cwd(), ensure_on_same_branch=False)

    # Commit changes
    commit_changes()
    logger.info("✅ Workspace initialized successfully")
