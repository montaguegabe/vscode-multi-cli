"""Global repository registry for symlink support.

Manages ~/.multi/repos.json which tracks known repository locations
to enable symlinking instead of re-cloning.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import git

logger = logging.getLogger(__name__)

REGISTRY_DIR = Path.home() / ".multi"
REGISTRY_FILE = REGISTRY_DIR / "repos.json"
REGISTRY_VERSION = 1


def _normalize_url(url: str) -> str:
    """Normalize a git URL for consistent lookups.

    Strips .git suffix so that:
    - https://github.com/org/repo.git
    - https://github.com/org/repo
    Both map to the same key.
    """
    if url.endswith(".git"):
        return url[:-4]
    return url


def load_registry() -> Dict[str, str]:
    """Load the repository registry from disk.

    Returns:
        Dict mapping normalized URLs to absolute paths.
    """
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with REGISTRY_FILE.open() as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning("Invalid registry format, resetting")
            return {}

        # Handle versioned format
        if "version" in data and "repos" in data:
            return data.get("repos", {})

        # Legacy format (just a dict of url -> path)
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load registry: {e}")
        return {}


def save_registry(repos: Dict[str, str]) -> None:
    """Save the repository registry to disk.

    Args:
        repos: Dict mapping normalized URLs to absolute paths.
    """
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    data = {"version": REGISTRY_VERSION, "repos": repos}

    try:
        with REGISTRY_FILE.open("w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.warning(f"Failed to save registry: {e}")


def register_repo(url: str, path: Path) -> None:
    """Register a repository in the global registry.

    Args:
        url: The git URL of the repository.
        path: The absolute path where the repository exists.
    """
    repos = load_registry()
    normalized_url = _normalize_url(url)
    repos[normalized_url] = str(path.resolve())
    save_registry(repos)
    logger.debug(f"Registered repo {normalized_url} at {path}")


def lookup_repo(url: str) -> Optional[Path]:
    """Look up a repository in the registry.

    Args:
        url: The git URL to look up.

    Returns:
        Path to the repository if found and valid, None otherwise.
        A valid path must exist and be a git repository.
    """
    repos = load_registry()
    normalized_url = _normalize_url(url)

    path_str = repos.get(normalized_url)
    if not path_str:
        return None

    path = Path(path_str)

    # Validate the path still exists
    if not path.exists():
        logger.debug(f"Registry entry for {normalized_url} points to non-existent path")
        return None

    # Validate it's a git repository
    try:
        git.Repo(path)
    except git.InvalidGitRepositoryError:
        logger.debug(f"Registry entry for {normalized_url} is not a git repository")
        return None

    return path
