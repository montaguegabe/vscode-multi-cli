import json

import git

from multi.doctor import run_doctor_checks, run_doctor_fixes


def test_doctor_warns_on_nested_git_repos_in_monorepo(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "monoRepo": True,
        "repos": [
            {"name": "packages/api"},
        ],
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    nested_repo = workspace / "packages" / "api" / ".git"
    nested_repo.mkdir(parents=True)

    report = run_doctor_checks(workspace)

    assert any("nested .git" in warning for warning in report.warnings)
    assert any("packages/api" in warning for warning in report.warnings)
    assert report.should_fail(strict=False) is False
    assert report.should_fail(strict=True) is True


def test_doctor_warns_if_root_git_is_missing(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    report = run_doctor_checks(workspace)
    assert any("Workspace root is not a git repository" in w for w in report.warnings)


def test_doctor_warns_on_undeclared_git_repo_on_disk(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    # Create declared repo on disk
    (workspace / "repo-a" / ".git").mkdir(parents=True)
    # Create undeclared repo on disk
    (workspace / "repo-b" / ".git").mkdir(parents=True)

    report = run_doctor_checks(workspace)
    assert any("not declared in multi.json" in w for w in report.warnings)
    assert any("repo-b" in w for w in report.warnings)


def test_doctor_warns_on_declared_repo_missing_from_disk(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
            {"url": "https://github.com/example/repo-b"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    # Only create repo-a on disk, repo-b is missing
    (workspace / "repo-a" / ".git").mkdir(parents=True)

    report = run_doctor_checks(workspace)
    assert any("not found on disk" in w for w in report.warnings)
    assert any("repo-b" in w for w in report.warnings)


def test_doctor_no_mismatch_warnings_when_in_sync(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    # Create the declared repo on disk
    (workspace / "repo-a" / ".git").mkdir(parents=True)

    report = run_doctor_checks(workspace)
    assert not any("not declared in multi.json" in w for w in report.warnings)
    assert not any("not found on disk" in w for w in report.warnings)


def test_doctor_warns_on_tracked_subrepo(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Initialize workspace as a git repo
    root_repo = git.Repo.init(workspace, initial_branch="main")

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    # Create the sub-repo directory with a file and track it in the root index
    sub_dir = workspace / "repo-a"
    sub_dir.mkdir()
    (sub_dir / ".git").mkdir()
    (sub_dir / "README.md").write_text("hello")
    root_repo.index.add(["repo-a/README.md"])

    report = run_doctor_checks(workspace)
    assert any("tracked in the workspace git index" in w for w in report.warnings)
    assert any("repo-a" in w for w in report.warnings)


def test_doctor_warns_on_subrepo_submodule(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Initialize workspace as a git repo with initial commit
    root_repo = git.Repo.init(workspace, initial_branch="main")
    (workspace / "multi.json").write_text(
        json.dumps({"repos": [{"url": "https://github.com/example/repo-a"}]})
    )
    root_repo.index.add(["multi.json"])
    root_repo.index.commit("init")

    # Create a separate repo to add as submodule
    ext_repo_path = tmp_path / "external-repo"
    ext_repo_path.mkdir()
    ext_repo = git.Repo.init(ext_repo_path, initial_branch="main")
    (ext_repo_path / "file.txt").write_text("content")
    ext_repo.index.add(["file.txt"])
    ext_repo.index.commit("init")

    # Add it as a submodule named repo-a
    root_repo.create_submodule("repo-a", "repo-a", url=str(ext_repo_path))

    report = run_doctor_checks(workspace)
    assert any("submodules" in w for w in report.warnings)
    assert any("repo-a" in w for w in report.warnings)


def test_doctor_fix_removes_tracked_subrepo_from_root_index(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    root_repo = git.Repo.init(workspace, initial_branch="main")
    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))

    sub_dir = workspace / "repo-a"
    sub_dir.mkdir()
    (sub_dir / ".git").mkdir()
    (sub_dir / "README.md").write_text("hello")
    root_repo.index.add(["repo-a/README.md"])

    fixed = run_doctor_fixes(workspace)
    assert fixed == ["repo-a"]
    assert "repo-a/README.md" not in {entry[0] for entry in root_repo.index.entries}

    report = run_doctor_checks(workspace)
    assert not any("tracked in the workspace git index" in w for w in report.warnings)


def test_doctor_fix_is_noop_when_subrepos_are_not_tracked(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    git.Repo.init(workspace, initial_branch="main")
    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))
    (workspace / ".gitignore").write_text("repo-a/\n")
    (workspace / "repo-a" / ".git").mkdir(parents=True)

    fixed = run_doctor_fixes(workspace)
    assert fixed == []


def test_doctor_no_tracking_warning_when_subrepos_ignored(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Initialize workspace as a git repo
    git.Repo.init(workspace, initial_branch="main")

    multi_json = {
        "repos": [
            {"url": "https://github.com/example/repo-a"},
        ]
    }
    (workspace / "multi.json").write_text(json.dumps(multi_json, indent=2))
    (workspace / ".gitignore").write_text("repo-a/\n")

    # Create the sub-repo on disk but don't track it
    (workspace / "repo-a" / ".git").mkdir(parents=True)

    report = run_doctor_checks(workspace)
    assert not any("tracked in the workspace git index" in w for w in report.warnings)
    assert not any("submodules" in w for w in report.warnings)
