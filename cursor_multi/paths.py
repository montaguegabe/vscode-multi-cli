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
        if (current / "repos.json").exists():
            return current

        if current.parent == current:  # Reached root directory
            raise FileNotFoundError("Could not find repos.json in any parent directory")

        current = current.parent


def get_cursor_rules_dir(repo_dir: Path, create: bool = True) -> Path:
    result = repo_dir / ".cursor" / "rules"
    if create:
        os.makedirs(result, exist_ok=True)
    return result


root_dir = get_root()

root_rules_dir = get_cursor_rules_dir(root_dir, create=True)

imported_rules_path = root_dir / ".importedrules"

gitignore_path = root_dir / ".gitignore"

vscode_ignore_path = root_dir / ".ignore"

multi_toml_path = root_dir / "multi.toml"
