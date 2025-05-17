import tomli

from .paths import multi_toml_path

default_settings = {"vscode": {"skip_keys": ["workbench.colorCustomizations"]}}


def load_settings() -> dict:
    """Load settings from multi.toml file."""
    try:
        with open(multi_toml_path, "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        # Return default settings if file doesn't exist
        return default_settings


# Load settings at module level
settings = load_settings()
