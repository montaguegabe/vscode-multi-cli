import json
import os

from multi.sync_vscode_launch import merge_launch_json
from multi.utils import soft_read_json_file


def test_merge_launch_files(setup_git_repos):
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]  # Should be named "repo0" by the fixture
    repo1_path = sub_repo_dirs[1]  # Should be named "repo1" by the fixture

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # --- Repo0 launch.json ---
    repo0_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo0 PyLaunch",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/main.py",
                "console": "integratedTerminal",
                "required": True,
            },
            {
                "name": "Repo0 Another",
                "type": "node",
                "request": "attach",
                "port": 9229,
            },
        ],
        "compounds": [
            {
                "name": "Repo0 Compound",
                "configurations": ["Repo0 PyLaunch", "Repo0 Another"],
            }
        ],
    }
    (repo0_path / ".vscode" / "launch.json").write_text(
        json.dumps(repo0_launch_content)
    )

    # --- Repo1 launch.json ---
    repo1_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo1 NodeLaunch",
                "type": "node",
                "request": "launch",
                "program": "${workspaceFolder}/app.js",
                "required": True,
            },
            {
                "name": "Repo1 JavaDebug",
                "type": "java",
                "request": "attach",
                "hostName": "localhost",
                "port": 8000,
                "required": False,  # Explicitly false
            },
        ],
    }
    (repo1_path / ".vscode" / "launch.json").write_text(
        json.dumps(repo1_launch_content)
    )

    # Call the merge function
    merge_launch_json(root_dir=root_repo_path)

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "launch.json"
    assert merged_file_path.exists()

    merged_data = soft_read_json_file(merged_file_path)

    assert "configurations" in merged_data
    assert "compounds" in merged_data

    # Check configurations
    expected_config_names = [
        "Repo0 PyLaunch",
        "Repo0 Another",
        "Repo1 NodeLaunch",
        "Repo1 JavaDebug",
    ]
    actual_config_names = [c["name"] for c in merged_data["configurations"]]
    for name in expected_config_names:
        assert name in actual_config_names

    # Check cwd for configurations (defaults application)
    for config in merged_data["configurations"]:
        if config["name"] == "Repo0 PyLaunch":
            assert config["cwd"] == "${workspaceFolder}/repo0"
            assert config["program"] == "${workspaceFolder}/repo0/main.py"
        elif config["name"] == "Repo0 Another":  # No program to prefix
            assert config["cwd"] == "${workspaceFolder}/repo0"
        elif config["name"] == "Repo1 NodeLaunch":
            assert config["cwd"] == "${workspaceFolder}/repo1"
            assert config["program"] == "${workspaceFolder}/repo1/app.js"
        elif config["name"] == "Repo1 JavaDebug":  # No program to prefix
            assert config["cwd"] == "${workspaceFolder}/repo1"

    # Check master compound
    # Master compound name is based on the root project directory name
    # The fixture uses /tmp/multi-test/root -> master_compound_name = "Root"
    master_compound_name = os.path.basename(str(root_repo_path)).title()

    master_compound = next(
        (c for c in merged_data["compounds"] if c["name"] == master_compound_name), None
    )
    assert master_compound is not None
    assert "Repo0 PyLaunch" in master_compound["configurations"]
    assert "Repo1 NodeLaunch" in master_compound["configurations"]
    assert "Repo0 Another" not in master_compound["configurations"]  # Not required
    assert "Repo1 JavaDebug" not in master_compound["configurations"]  # Not required

    # Check Repo0 Compound (original compound from repo0)
    repo0_compound = next(
        (c for c in merged_data["compounds"] if c["name"] == "Repo0 Compound"), None
    )
    assert repo0_compound is not None
    assert "Repo0 PyLaunch" in repo0_compound["configurations"]
    assert "Repo0 Another" in repo0_compound["configurations"]

    # Ensure no other unexpected compounds unless they were renamed
    assert len(merged_data["compounds"]) == 2  # Master + Repo0 Compound


def test_required_launch_configs_from_multi_json(setup_git_repos):
    """Test that requiredLaunchConfigs in multi.json are included in the master compound."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]
    repo1_path = sub_repo_dirs[1]

    # Update multi.json to include requiredLaunchConfigs
    multi_json_content = {
        "repos": [
            {
                "url": "https://github.com/test/repo0",
                "requiredLaunchConfigs": ["Repo0 Debug"],
            },
            {
                "url": "https://github.com/test/repo1",
                "requiredLaunchConfigs": ["Repo1 Debug"],
            },
        ]
    }
    import json

    (root_repo_path / "multi.json").write_text(json.dumps(multi_json_content))

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # Create launch.json files WITHOUT required: true
    repo0_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo0 Debug",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/main.py",
            },
            {
                "name": "Repo0 Other",
                "type": "node",
                "request": "attach",
                "port": 9229,
            },
        ],
    }
    (repo0_path / ".vscode" / "launch.json").write_text(json.dumps(repo0_launch_content))

    repo1_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo1 Debug",
                "type": "node",
                "request": "launch",
                "program": "${workspaceFolder}/app.js",
            },
        ],
    }
    (repo1_path / ".vscode" / "launch.json").write_text(json.dumps(repo1_launch_content))

    # Call the merge function
    merge_launch_json(root_dir=root_repo_path)

    # Assertions
    merged_file_path = root_repo_path / ".vscode" / "launch.json"
    merged_data = soft_read_json_file(merged_file_path)

    # Find the master compound
    master_compound_name = os.path.basename(str(root_repo_path)).title()
    master_compound = next(
        (c for c in merged_data["compounds"] if c["name"] == master_compound_name), None
    )

    assert master_compound is not None, f"Master compound '{master_compound_name}' not found"
    assert "Repo0 Debug" in master_compound["configurations"]
    assert "Repo1 Debug" in master_compound["configurations"]
    # Repo0 Other should NOT be in the master compound
    assert "Repo0 Other" not in master_compound["configurations"]


def test_required_launch_configs_combines_json_and_multi_json(setup_git_repos):
    """Test that required configs from both launch.json and multi.json are combined."""
    root_repo_path, sub_repo_dirs = setup_git_repos
    repo0_path = sub_repo_dirs[0]
    repo1_path = sub_repo_dirs[1]

    # Update multi.json to include requiredLaunchConfigs for repo0 only
    multi_json_content = {
        "repos": [
            {
                "url": "https://github.com/test/repo0",
                "requiredLaunchConfigs": ["Repo0 Debug"],
            },
            {"url": "https://github.com/test/repo1"},
        ]
    }
    import json

    (root_repo_path / "multi.json").write_text(json.dumps(multi_json_content))

    # Create .vscode dirs
    (root_repo_path / ".vscode").mkdir(exist_ok=True)
    (repo0_path / ".vscode").mkdir(exist_ok=True)
    (repo1_path / ".vscode").mkdir(exist_ok=True)

    # Repo0: config without required:true (will be required via multi.json)
    repo0_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo0 Debug",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/main.py",
            },
        ],
    }
    (repo0_path / ".vscode" / "launch.json").write_text(json.dumps(repo0_launch_content))

    # Repo1: config with required:true in the JSON
    repo1_launch_content = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Repo1 Test",
                "type": "node",
                "request": "launch",
                "program": "${workspaceFolder}/test.js",
                "required": True,
            },
        ],
    }
    (repo1_path / ".vscode" / "launch.json").write_text(json.dumps(repo1_launch_content))

    # Call the merge function
    merge_launch_json(root_dir=root_repo_path)

    # Find the master compound
    merged_data = soft_read_json_file(root_repo_path / ".vscode" / "launch.json")
    master_compound_name = os.path.basename(str(root_repo_path)).title()
    master_compound = next(
        (c for c in merged_data["compounds"] if c["name"] == master_compound_name), None
    )

    assert master_compound is not None
    # Both should be in the master compound
    assert "Repo0 Debug" in master_compound["configurations"]  # From multi.json
    assert "Repo1 Test" in master_compound["configurations"]  # From launch.json required:true
