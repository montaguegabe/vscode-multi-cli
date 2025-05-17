import os
from pathlib import Path


def get_root() -> Path:
    """Get the root directory by finding the first parent directory containing repos.json.

    Returns:
        The absolute path to the root directory containing repos.json.

    Raises:
        FileNotFoundError: If no repos.json is found in any parent directory.
    """
    current = Path.cwd()

    while True:
        if (current / "multi.toml").exists():
            return current

        if current.parent == current:  # Reached root directory
            raise FileNotFoundError("Could not find multi.toml in any parent directory")

        current = current.parent


def get_cursor_rules_dir(repo_dir: Path, create: bool = False) -> Path:
    result = repo_dir / ".cursor" / "rules"
    if create:
        os.makedirs(result, exist_ok=True)
    return result


def get_vscode_config_dir(repo_dir: Path, create: bool = False) -> Path:
    return repo_dir / ".vscode"


# Root
root_dir = get_root()

multi_toml_path = root_dir / "multi.toml"

# Cursor
root_rules_dir = get_cursor_rules_dir(root_dir, create=True)

# Ignore
imported_rules_path = root_dir / ".importedrules"

gitignore_path = root_dir / ".gitignore"

# VSCode
vscode_ignore_path = root_dir / ".ignore"

vscode_config_path = get_vscode_config_dir(root_dir, create=True)

vscode_launch_path = vscode_config_path / "launch.json"

vscode_tasks_path = vscode_config_path / "tasks.json"

vscode_settings_path = vscode_config_path / "settings.json"

vscode_settings_shared_path = vscode_config_path / "settings.shared.json"
