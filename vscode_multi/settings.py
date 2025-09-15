import json
import logging
from pathlib import Path
from typing import Any, Dict, Self

from vscode_multi.utils import apply_defaults_to_structure

logger = logging.getLogger(__name__)

default_settings = {
    "vscode": {"skipSettings": ["workbench.colorCustomizations"]},
    "repos": [],
}


class Settings:
    """A lazy-loading settings class that reads from multi.json only when accessed."""

    def __init__(self, dict: Dict[str, Any]):
        self.dict = dict

    @classmethod
    def from_multi_json_file(cls, multi_json_file: Path) -> Self:
        with multi_json_file.open() as f:
            user_settings = json.load(f)
            assert isinstance(user_settings, dict)
        return cls(apply_defaults_to_structure(user_settings, default_settings))

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access to settings."""
        return self.dict[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting with a default value if it doesn't exist."""
        return self.dict.get(key, default)
