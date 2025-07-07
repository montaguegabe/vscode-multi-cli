import json

from vscode_multi.sync_vscode_tasks import merge_tasks_json


def test_merge_tasks_files(setup_git_repos):
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]  # repo0
    repo1_path = sub_repo_dirs[1]  # repo1

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # --- Repo0 tasks.json ---
    repo0_tasks_content = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Repo0 Build",
                "type": "shell",
                "command": "./build.sh",
                "problemMatcher": [],
            },
            {"label": "Repo0 Test", "type": "process", "command": "pytest"},
        ],
    }
    (repo0_path / ".vscode" / "tasks.json").write_text(json.dumps(repo0_tasks_content))

    # --- Repo1 tasks.json ---
    repo1_tasks_content = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Repo1 Clean",
                "type": "npm",
                "script": "clean",
                "options": {"cwd": "${workspaceFolder}/specific_subfolder"},
            }
        ],
    }
    (repo1_path / ".vscode" / "tasks.json").write_text(json.dumps(repo1_tasks_content))

    # Call the merge function
    merge_tasks_json()

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "tasks.json"
    assert merged_file_path.exists()

    with open(merged_file_path, "r") as f:
        merged_data = json.load(f)

    assert "version" in merged_data
    assert merged_data["version"] == "2.0.0"  # Should pick up from one of the files
    assert "tasks" in merged_data
    assert len(merged_data["tasks"]) == 3  # 2 from repo0, 1 from repo1

    # Check tasks and their cwds
    task_labels_to_cwds = {
        t["label"]: t.get("options", {}).get("cwd") for t in merged_data["tasks"]
    }

    assert task_labels_to_cwds.get("Repo0 Build") == "${workspaceFolder}/repo0"
    assert task_labels_to_cwds.get("Repo0 Test") == "${workspaceFolder}/repo0"

    assert (
        task_labels_to_cwds.get("Repo1 Clean")
        == "${workspaceFolder}/repo1/specific_subfolder"
    )
