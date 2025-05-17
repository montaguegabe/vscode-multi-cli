from typing import List

import tomli

from .paths import multi_toml_path


def load_settings() -> dict:
    """Load settings from multi.toml file."""
    try:
        with open(multi_toml_path, "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        # Return default settings if file doesn't exist
        return {"vscode": {"skip_keys": ["workbench.colorCustomizations"]}}


# Load settings at module level
_settings = load_settings()

# Export specific settings
SKIP_KEYS: List[str] = _settings["vscode"]["skip_keys"]
