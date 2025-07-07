import json
import logging
from functools import cached_property
from typing import Any, Dict

from vscode_multi.paths import paths
from vscode_multi.utils import apply_defaults_to_structure

logger = logging.getLogger(__name__)

default_settings = {
    "vscode": {"skipSettings": ["workbench.colorCustomizations"]},
    "repos": [],
}


class Settings:
    """A lazy-loading settings class that reads from multi.json only when accessed."""

    @cached_property
    def dict(self) -> Dict[str, Any]:
        """Load settings from multi.json file, applying defaults for missing keys."""
        with paths.multi_json_path.open() as f:
            user_settings = json.load(f)
            assert isinstance(user_settings, dict)
        return apply_defaults_to_structure(user_settings, default_settings)

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access to settings."""
        return self.dict[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting with a default value if it doesn't exist."""
        return self.dict.get(key, default)


# Create a singleton instance
settings = Settings()
