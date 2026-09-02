import json
from pathlib import Path

import git

from multi.git_helpers import is_git_repo_root
from multi.worktree import add_worktree


def _commit_all(repo: git.Repo, message: str) -> None:
    repo.git.add(all=True)
    repo.index.commit(message)


def _create_remote_repo(
    base_path: Path, name: str, branches: list[str] | None = None
) -> Path:
    seed_path = base_path / "seeds" / name
    remote_path = base_path / "remotes" / name
    seed_path.mkdir(parents=True)
    remote_path.parent.mkdir(parents=True, exist_ok=True)

    repo = git.Repo.init(seed_path, initial_branch="main")
    (seed_path / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    (seed_path / ".gitignore").write_text(".secret\n", encoding="utf-8")
    _commit_all(repo, "Initial commit")

    for branch_name in branches or []:
        repo.create_head(branch_name).checkout()
        (seed_path / f"{branch_name}.txt").write_text(branch_name, encoding="utf-8")
        _commit_all(repo, f"Add {branch_name}")
        repo.heads.main.checkout()

    git.Repo.init(remote_path, bare=True)
    origin = repo.create_remote("origin", str(remote_path))
    origin.push(refspec="main:main")
    for branch_name in branches or []:
        origin.push(refspec=f"{branch_name}:{branch_name}")

    return remote_path


def _create_workspace(
    tmp_path: Path,
    *,
    repo_configs: list[dict[str, str]],
    worktree_config: dict[str, list[str]] | None = None,
) -> Path:
    root_path = tmp_path / "workspace"
    root_path.mkdir()

    config: dict[str, object] = {"repos": repo_configs}
    if worktree_config:
        config["worktree"] = worktree_config
    (root_path / "multi.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    gitignore_entries = [".env", ".cache/"]
    gitignore_entries.extend(f"{repo_config['name']}/" for repo_config in repo_configs)
    (root_path / ".gitignore").write_text(
        "\n".join(gitignore_entries) + "\n",
        encoding="utf-8",
    )
    (root_path / "README.md").write_text("# Workspace\n", encoding="utf-8")

    root_repo = git.Repo.init(root_path, initial_branch="main")
    _commit_all(root_repo, "Initial commit")

    for repo_config in repo_configs:
        git.Repo.clone_from(repo_config["url"], root_path / repo_config["name"])

    return root_path


def test_add_worktree_uses_name_as_default_branch(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
    )

    destination = add_worktree(root_path, name="feature-test")

    assert destination == tmp_path / "workspace-worktrees" / "feature-test"
    assert is_git_repo_root(destination) is True
    assert git.Repo(destination).active_branch.name == "feature-test"
    assert git.Repo(destination / "repo0").active_branch.name == "feature-test"


def test_add_worktree_creates_worktrees_sibling_directory(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
    )
    assert not (tmp_path / "workspace-worktrees").exists()

    destination = add_worktree(root_path, name="feature-placed")

    assert destination.parent == tmp_path / "workspace-worktrees"
    assert destination.parent.is_dir()
    assert is_git_repo_root(destination) is True


def test_add_worktree_allows_dirty_root_and_subrepos(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
    )
    (root_path / "README.md").write_text("# Workspace (edited)\n", encoding="utf-8")
    (root_path / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    (root_path / "repo0" / "README.md").write_text(
        "# repo0 (edited)\n", encoding="utf-8"
    )

    destination = add_worktree(root_path, name="feature-dirty")

    assert git.Repo(destination).active_branch.name == "feature-dirty"
    assert git.Repo(destination / "repo0").active_branch.name == "feature-dirty"
    # Source working trees are untouched.
    assert (root_path / "README.md").read_text(encoding="utf-8") == (
        "# Workspace (edited)\n"
    )
    assert (root_path / "repo0" / "README.md").read_text(encoding="utf-8") == (
        "# repo0 (edited)\n"
    )
    # Uncommitted changes do not leak into the new worktree.
    assert (destination / "README.md").read_text(encoding="utf-8") == "# Workspace\n"
    assert not (destination / "untracked.txt").exists()


def test_add_worktree_uses_custom_branch_name(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
    )

    destination = add_worktree(root_path, name="sibling", branch_name="feature/custom")

    assert destination == tmp_path / "workspace-worktrees" / "sibling"
    assert git.Repo(destination).active_branch.name == "feature/custom"
    assert git.Repo(destination / "repo0").active_branch.name == "feature/custom"


def test_add_worktree_respects_fixed_branch(tmp_path):
    repo0_remote = _create_remote_repo(tmp_path, "repo0")
    repo1_remote = _create_remote_repo(tmp_path, "repo1", branches=["stable"])
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[
            {"url": str(repo0_remote), "name": "repo0"},
            {"url": str(repo1_remote), "name": "repo1", "fixedBranch": "stable"},
        ],
    )
    git.Repo(root_path / "repo1").git.checkout("stable")

    destination = add_worktree(root_path, name="feature-fixed")

    assert git.Repo(destination).active_branch.name == "feature-fixed"
    assert git.Repo(destination / "repo0").active_branch.name == "feature-fixed"
    assert git.Repo(destination / "repo1").active_branch.name == "stable"


def test_add_worktree_transfers_gitignored_paths(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
        worktree_config={
            "symlink": [".env"],
            "copy": [".cache/config.json", "repo0/.secret"],
        },
    )
    (root_path / ".env").write_text("TOKEN=local\n", encoding="utf-8")
    (root_path / ".cache").mkdir()
    (root_path / ".cache" / "config.json").write_text(
        '{"local": true}\n', encoding="utf-8"
    )
    (root_path / "repo0" / ".secret").write_text("repo-local\n", encoding="utf-8")

    destination = add_worktree(root_path, name="feature-transfer")

    assert (destination / ".env").is_symlink()
    assert (destination / ".env").resolve() == root_path / ".env"
    assert (destination / ".cache" / "config.json").read_text(encoding="utf-8") == (
        root_path / ".cache" / "config.json"
    ).read_text(encoding="utf-8")
    assert (destination / "repo0" / ".secret").read_text(
        encoding="utf-8"
    ) == "repo-local\n"


def test_add_worktree_respects_install_set(tmp_path):
    repo0_remote = _create_remote_repo(tmp_path, "repo0")
    repo1_remote = _create_remote_repo(tmp_path, "repo1")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[
            {"url": str(repo0_remote), "name": "repo0", "installSets": ["default"]},
            {"url": str(repo1_remote), "name": "repo1", "installSets": ["dev"]},
        ],
    )

    destination = add_worktree(root_path, name="feature-default", install_set="default")

    assert (destination / "repo0").is_dir()
    assert not (destination / "repo1").exists()
    assert git.Repo(destination / "repo0").active_branch.name == "feature-default"


def test_add_worktree_uses_base_ref_for_root_and_subrepos(tmp_path):
    remote = _create_remote_repo(tmp_path, "repo0")
    root_path = _create_workspace(
        tmp_path,
        repo_configs=[{"url": str(remote), "name": "repo0"}],
    )
    root_repo = git.Repo(root_path)
    root_repo.create_head("agent-work/upstream").checkout()
    (root_path / "root-upstream.txt").write_text("root upstream\n", encoding="utf-8")
    _commit_all(root_repo, "Root upstream")
    repo0 = git.Repo(root_path / "repo0")
    repo0.create_head("agent-work/upstream").checkout()
    (root_path / "repo0" / "repo-upstream.txt").write_text(
        "repo upstream\n",
        encoding="utf-8",
    )
    _commit_all(repo0, "Repo upstream")

    destination = add_worktree(
        root_path,
        name="feature-downstream",
        base_ref="agent-work/upstream",
    )

    assert git.Repo(destination).active_branch.name == "feature-downstream"
    assert git.Repo(destination / "repo0").active_branch.name == "feature-downstream"
    assert (destination / "root-upstream.txt").read_text(encoding="utf-8") == (
        "root upstream\n"
    )
    assert (destination / "repo0" / "repo-upstream.txt").read_text(
        encoding="utf-8"
    ) == "repo upstream\n"
