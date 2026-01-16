import json
import os

from multi.sync_vscode_tasks import merge_tasks_json
from multi.utils import soft_read_json_file


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
    merge_tasks_json(root_repo_path)

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "tasks.json"
    assert merged_file_path.exists()

    merged_data = soft_read_json_file(merged_file_path)

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


def test_required_tasks_from_multi_json(setup_git_repos):
    """Test that requiredTasks in multi.json are included in the master task."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]  # repo0
    repo1_path = sub_repo_dirs[1]  # repo1

    # Update multi.json to include requiredTasks
    multi_json_content = {
        "repos": [
            {"url": "https://github.com/test/repo0", "requiredTasks": ["Repo0 Build"]},
            {"url": "https://github.com/test/repo1", "requiredTasks": ["Repo1 Clean"]},
        ]
    }
    (root_repo_path / "multi.json").write_text(json.dumps(multi_json_content))

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # Create tasks.json files WITHOUT required: true
    repo0_tasks_content = {
        "version": "2.0.0",
        "tasks": [
            {"label": "Repo0 Build", "type": "shell", "command": "./build.sh"},
            {"label": "Repo0 Test", "type": "process", "command": "pytest"},
        ],
    }
    (repo0_path / ".vscode" / "tasks.json").write_text(json.dumps(repo0_tasks_content))

    repo1_tasks_content = {
        "version": "2.0.0",
        "tasks": [{"label": "Repo1 Clean", "type": "npm", "script": "clean"}],
    }
    (repo1_path / ".vscode" / "tasks.json").write_text(json.dumps(repo1_tasks_content))

    # Call the merge function
    merge_tasks_json(root_repo_path)

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "tasks.json"
    merged_data = soft_read_json_file(merged_file_path)

    # Find the master task
    master_task_name = f"All Required Tasks - {os.path.basename(str(root_repo_path)).title()}"
    master_task = next(
        (t for t in merged_data["tasks"] if t.get("label") == master_task_name), None
    )

    assert master_task is not None, f"Master task '{master_task_name}' not found"
    assert "Repo0 Build" in master_task["dependsOn"]
    assert "Repo1 Clean" in master_task["dependsOn"]
    # Repo0 Test should NOT be in the master task (not marked as required)
    assert "Repo0 Test" not in master_task["dependsOn"]


def test_required_tasks_combines_json_and_multi_json(setup_git_repos):
    """Test that required tasks from both tasks.json and multi.json are combined."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]
    repo1_path = sub_repo_dirs[1]

    # Update multi.json to include requiredTasks for repo0 only
    multi_json_content = {
        "repos": [
            {"url": "https://github.com/test/repo0", "requiredTasks": ["Repo0 Build"]},
            {"url": "https://github.com/test/repo1"},
        ]
    }
    (root_repo_path / "multi.json").write_text(json.dumps(multi_json_content))

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # Repo0: task without required:true (will be required via multi.json)
    repo0_tasks_content = {
        "version": "2.0.0",
        "tasks": [{"label": "Repo0 Build", "type": "shell", "command": "./build.sh"}],
    }
    (repo0_path / ".vscode" / "tasks.json").write_text(json.dumps(repo0_tasks_content))

    # Repo1: task with required:true in the JSON
    repo1_tasks_content = {
        "version": "2.0.0",
        "tasks": [
            {"label": "Repo1 Test", "type": "npm", "script": "test", "required": True}
        ],
    }
    (repo1_path / ".vscode" / "tasks.json").write_text(json.dumps(repo1_tasks_content))

    # Call the merge function
    merge_tasks_json(root_repo_path)

    # Find the master task
    merged_data = soft_read_json_file(root_repo_path / ".vscode" / "tasks.json")
    master_task_name = f"All Required Tasks - {os.path.basename(str(root_repo_path)).title()}"
    master_task = next(
        (t for t in merged_data["tasks"] if t.get("label") == master_task_name), None
    )

    assert master_task is not None
    # Both should be in the master task
    assert "Repo0 Build" in master_task["dependsOn"]  # From multi.json
    assert "Repo1 Test" in master_task["dependsOn"]  # From tasks.json required:true
