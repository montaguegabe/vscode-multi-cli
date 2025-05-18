import json
import logging
from typing import Any, Dict

from .paths import paths
from .utils import apply_defaults_to_structure

logger = logging.getLogger(__name__)

default_settings = {
    "vscode": {"skip_settings": ["workbench.colorCustomizations"]},
    "repos": [],
}


class Settings:
    """A lazy-loading settings class that reads from multi.json only when accessed."""

    def __init__(self):
        self._settings: Dict[str, Any] | None = None

    def dict(self) -> Dict[str, Any]:
        """Load settings from multi.json file, applying defaults for missing keys."""
        if self._settings is not None:
            return self._settings
        with paths.multi_json_path.open() as f:
            user_settings = json.load(f)
            assert isinstance(user_settings, dict)
        settings = apply_defaults_to_structure(user_settings, default_settings)
        self._settings = settings
        return settings

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access to settings."""
        return self.dict()[key]


# Create a singleton instance
settings = Settings()
