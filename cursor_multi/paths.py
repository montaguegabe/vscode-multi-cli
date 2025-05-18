import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Paths:
    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or self.get_root()
        self.multi_json_path = self.root_dir / "multi.json"

        # Cursor
        self.root_rules_dir = self.get_cursor_rules_dir(self.root_dir, create=True)

        # Ignore
        self.imported_rules_path = self.root_dir / ".importedrules"
        self.gitignore_path = self.root_dir / ".gitignore"

        # VSCode
        self.vscode_ignore_path = self.root_dir / ".ignore"
        self.root_vscode_dir = self.get_vscode_config_dir(self.root_dir, create=True)
        self.vscode_launch_path = self.root_vscode_dir / "launch.json"
        self.vscode_tasks_path = self.root_vscode_dir / "tasks.json"
        self.vscode_settings_path = self.root_vscode_dir / "settings.json"
        self.vscode_settings_shared_path = self.root_vscode_dir / "settings.shared.json"

    def get_root(self) -> Path:
        """Get the root directory by finding the first parent directory containing multi.json.

        Returns:
            The absolute path to the root directory containing multi.json.

        Raises:
            FileNotFoundError: If no multi.json is found in any parent directory.
        """
        current = Path.cwd()

        while True:
            if (current / "multi.json").exists():
                return current

            if current.parent == current:  # Reached root directory
                msg = "Could not find multi.json in any parent directory"
                logger.error(msg)
                raise FileNotFoundError(msg)

            current = current.parent

    def get_cursor_rules_dir(self, repo_dir: Path, create: bool = False) -> Path:
        result = repo_dir / ".cursor" / "rules"
        if create:
            os.makedirs(result, exist_ok=True)
        return result

    def get_vscode_config_dir(self, repo_dir: Path, create: bool = False) -> Path:
        result = repo_dir / ".vscode"
        if create:
            os.makedirs(result, exist_ok=True)
        return result


# Global instance that can be mocked in tests
paths = Paths()
