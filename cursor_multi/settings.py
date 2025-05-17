import json
import logging

from .paths import multi_json_path
from .utils import apply_defaults_to_structure

logger = logging.getLogger(__name__)

default_settings = {
    "vscode": {"skip_settings": ["workbench.colorCustomizations"]},
    "repos": [],
}


def load_settings() -> dict:
    """Load settings from multi.json file, applying defaults for missing keys."""
    with open(multi_json_path) as f:
        user_settings = json.load(f)
        assert isinstance(user_settings, dict)
    return apply_defaults_to_structure(user_settings, default_settings)


# Load settings at module level
settings = load_settings()
