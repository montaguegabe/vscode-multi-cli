import logging
from importlib.resources import files
from pathlib import Path

import git

from multi.git_helpers import is_git_repo_root
from multi.paths import Paths
from multi.repos import load_repos

logger = logging.getLogger(__name__)

init_readme_template = (files("multi") / "resources" / "init_readme.md").read_text()


def _render_init_readme(workspace_name: str, repo_list: str) -> str:
    # Keep compatibility with the current template placeholder style.
    if "{**name**}" in init_readme_template:
        return init_readme_template.replace("{**name**}", workspace_name).replace(
            "{**repo_list**}",
            repo_list,
        )
    return init_readme_template.format(__name__=workspace_name, __repo_list__=repo_list)


def _to_https_repo_link(url: str) -> str:
    if url.startswith("git@github.com:"):
        slug = url[len("git@github.com:") :].replace(".git", "")
        return f"https://github.com/{slug}"
    if url.startswith("ssh://git@github.com/"):
        slug = url[len("ssh://git@github.com/") :].replace(".git", "")
        return f"https://github.com/{slug}"
    return url.replace(".git", "")


def build_repo_list(paths: Paths) -> str:
    repo_entries: list[str] = []
    for repo in load_repos(paths):
        if repo.url:
            repo_name = repo.name.replace(".git", "")
            repo_entries.append(f"- [{repo_name}]({_to_https_repo_link(repo.url)})")
        else:
            repo_entries.append(f"- `{repo.name}`")
    return "\n".join(repo_entries)


def ensure_root_git_repo(root_dir: Path) -> None:
    if is_git_repo_root(root_dir):
        return
    logger.info("Initializing git repository at workspace root...")
    git.Repo.init(root_dir)


def ensure_workspace_readme(paths: Paths) -> None:
    readme_path = paths.root_dir / "README.md"
    if readme_path.exists():
        return

    repo_list = build_repo_list(paths)
    workspace_name = paths.root_dir.name
    readme_content = _render_init_readme(workspace_name=workspace_name, repo_list=repo_list)
    readme_path.write_text(readme_content)
    logger.info("Created README.md")
