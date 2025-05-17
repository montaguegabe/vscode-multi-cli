import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def write_json_file(path: Path, data: Dict[str, Any]):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def soft_read_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file if it exists, otherwise return an empty dict."""
    if path.exists():
        try:
            with path.open("r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {path}, skipping...")
    return {}
