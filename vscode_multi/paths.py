import logging
import os
from pathlib import Path

from vscode_multi.settings import Settings

logger = logging.getLogger(__name__)


class Paths:
    def __init__(self, target_dir: Path | str | None = None):
        self.target_dir = Path(target_dir) or Path.cwd()
        self.root_dir = self._get_root(self.target_dir)

    @property
    def multi_json_path(self) -> Path:
        return self.root_dir / "multi.json"

    @property
    def gitignore_path(self) -> Path:
        return self.root_dir / ".gitignore"

    @property
    def vscode_ignore_path(self) -> Path:
        return self.root_dir / ".ignore"

    @property
    def root_vscode_dir(self) -> Path:
        return self.get_vscode_config_dir(self.root_dir, create=True)

    @property
    def vscode_launch_path(self) -> Path:
        return self.root_vscode_dir / "launch.json"

    @property
    def vscode_tasks_path(self) -> Path:
        return self.root_vscode_dir / "tasks.json"

    @property
    def vscode_settings_path(self) -> Path:
        return self.root_vscode_dir / "settings.json"

    @property
    def vscode_settings_shared_path(self) -> Path:
        return self.root_vscode_dir / "settings.shared.json"

    @property
    def vscode_extensions_path(self) -> Path:
        return self.root_vscode_dir / "extensions.json"

    def _get_root(self, start_dir: Path) -> Path:
        """Get the root directory by finding the first parent directory containing multi.json.

        Returns:
            The absolute path to the root directory containing multi.json.

        Raises:
            FileNotFoundError: If no multi.json is found in any parent directory.
        """
        current = start_dir

        while True:
            if (current / "multi.json").exists():
                return current

            if current.parent == current:  # Reached root directory
                msg = "Could not find multi.json in any parent directory"
                logger.error(msg)
                raise FileNotFoundError(msg)

            current = current.parent

    def get_vscode_config_dir(self, repo_dir: Path, create: bool = False) -> Path:
        result = repo_dir / ".vscode"
        if create:
            os.makedirs(result, exist_ok=True)
        return result

    def get_cursor_rules_dir(self, repo_dir: Path) -> Path:
        """Get the cursor rules directory for a given repository."""
        return repo_dir / ".cursor" / "rules"

    @property
    def settings(self) -> Settings:
        return Settings.from_multi_json_file(self.multi_json_path)
