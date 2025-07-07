import json

from vscode_multi.sync_vscode_settings import merge_settings_json


def test_merge_settings_files(setup_git_repos, mocker):
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]  # repo0
    repo1_path = sub_repo_dirs[1]  # repo1

    # --- Make repo0 a Python project by adding pyproject.toml ---
    pyproject_content = """[tool.poetry]
name = "repo0"
version = "0.1.0"
description = ""
authors = ["Test User <test@example.com>"]

[tool.poetry.dependencies]
python = ">=3.8"
"""
    (repo0_path / "pyproject.toml").write_text(pyproject_content)

    # --- Create .vscode dirs ---
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # --- Repo0 settings.json ---
    repo0_settings_content = {
        "python.pythonPath": "${workspaceFolder}/.venv/bin/python",
        "editor.formatOnSave": True,
        "files.exclude": {"**/.git": True, "**/__pycache__": True},
    }
    (repo0_path / ".vscode" / "settings.json").write_text(
        json.dumps(repo0_settings_content)
    )

    # --- Repo1 settings.json ---
    repo1_settings_content = {
        "editor.tabSize": 2,
        "files.exclude": {"**/.DS_Store": True},
        "toBeSkipped": "repo1Value",
        "anotherKey": "repo1Specific",
    }
    (repo1_path / ".vscode" / "settings.json").write_text(
        json.dumps(repo1_settings_content)
    )

    # --- Root .vscode/settings.shared.json ---
    shared_settings_content = {
        "editor.rulers": [80, 120],
        "search.exclude": {"**/node_modules": True, "**/bower_components": True},
    }
    (root_repo_path / ".vscode" / "settings.shared.json").write_text(
        json.dumps(shared_settings_content)
    )

    # Mock the settings module to return our desired skip_keys
    mock_settings = {"vscode": {"skipSettings": ["toBeSkipped"]}}
    # Mock the settings import in sync_vscode_settings.py
    mocker.patch("vscode_multi.sync_vscode_settings.settings", mock_settings)

    # Call the merge function
    merge_settings_json()

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "settings.json"
    assert merged_file_path.exists()

    with open(merged_file_path, "r") as f:
        merged_data = json.load(f)

    assert (
        merged_data.get("python.pythonPath")
        == "${workspaceFolder}/repo0/.venv/bin/python"
    )
    assert merged_data.get("editor.formatOnSave") is True
    assert merged_data.get("editor.tabSize") == 2
    assert merged_data.get("anotherKey") == "repo1Specific"
    assert "toBeSkipped" not in merged_data
    assert merged_data["files.exclude"]["**/.git"] is True
    assert merged_data["files.exclude"]["**/__pycache__"] is True
    assert merged_data["files.exclude"]["**/.DS_Store"] is True
    assert merged_data["editor.rulers"] == [80, 120]
    assert merged_data["search.exclude"]["**/node_modules"] is True
    assert "python.autoComplete.extraPaths" in merged_data
    assert "repo0" in merged_data["python.autoComplete.extraPaths"]
    assert "repo1" not in merged_data["python.autoComplete.extraPaths"]
    assert len(merged_data["python.autoComplete.extraPaths"]) == 1
