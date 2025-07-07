import logging
import os
from functools import cached_property
from pathlib import Path

logger = logging.getLogger(__name__)


class Paths:
    @cached_property
    def root_dir(self) -> Path:
        return self._get_root()

    @cached_property
    def multi_json_path(self) -> Path:
        return self.root_dir / "multi.json"

    @cached_property
    def gitignore_path(self) -> Path:
        return self.root_dir / ".gitignore"

    @cached_property
    def vscode_ignore_path(self) -> Path:
        return self.root_dir / ".ignore"

    @cached_property
    def root_vscode_dir(self) -> Path:
        return self.get_vscode_config_dir(self.root_dir, create=True)

    @cached_property
    def vscode_launch_path(self) -> Path:
        return self.root_vscode_dir / "launch.json"

    @cached_property
    def vscode_tasks_path(self) -> Path:
        return self.root_vscode_dir / "tasks.json"

    @cached_property
    def vscode_settings_path(self) -> Path:
        return self.root_vscode_dir / "settings.json"

    @cached_property
    def vscode_settings_shared_path(self) -> Path:
        return self.root_vscode_dir / "settings.shared.json"

    @cached_property
    def vscode_extensions_path(self) -> Path:
        return self.root_vscode_dir / "extensions.json"

    def _get_root(self) -> Path:
        """Get the root directory by finding the first parent directory containing multi.json.

        Returns:
            The absolute path to the root directory containing multi.json.

        Raises:
            FileNotFoundError: If no multi.json is found in any parent directory.
        """
        override_root_dir = os.getenv("vscode_multi_ROOT_DIR")
        if override_root_dir:
            return Path(override_root_dir)

        current = Path.cwd()

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


# Global instance that can be mocked in tests
paths = Paths()
