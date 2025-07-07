from functools import lru_cache
from typing import Any, List

from vscode_multi.errors import NoRepositoriesError
from vscode_multi.paths import paths
from vscode_multi.settings import settings


class Repository:
    """Represents a repository in the workspace.

    Attributes:
        url: The repository URL.
        name: Repository name derived from the URL.
        path: Local filesystem path where the repository is/will be cloned.
        skip: Whether to skip this repository for certain operations (default: False).
              Other attributes may be dynamically added from the config.
    """

    def __init__(self, url: str, **kwargs: Any):
        """Initialize Repository, deriving name and path, and setting other attributes from kwargs."""
        self.url = url
        # Derive name and path from URL
        self.name = self.url.split("/")[-1]
        self.path = paths.root_dir / self.name

        # Set 'skip' attribute, defaulting to False if not provided in kwargs
        self.skip_vscode = kwargs.pop("skipVSCode", False)

        # Set any other attributes passed in kwargs (top-level keys from repo config)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __hash__(self) -> int:
        """Make Repository hashable based on its URL."""
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        """Make Repository equatable based on its URL."""
        if not isinstance(other, Repository):
            return NotImplemented
        return self.url == other.url

    @property
    def is_python(self) -> bool:
        python_files = [
            "pyproject.toml",
            "requirements.txt",
            "Pipfile",
            "setup.py",
            "environment.yml",
            "setup.cfg",
        ]
        return any((self.path / file).exists() for file in python_files)


@lru_cache(maxsize=1)
def load_repos() -> List[Repository]:
    """Load repository information from the "repos" key in multi.json settings.

    Each repository config in the list should be an object. Example:
    {
        "repos": [
            {
                "url": "https://github.com/user/repo",
                "skip": false, // Optional, defaults to false
                "custom_setting": "value" // Other top-level settings become attributes
            }
        ]
    }
    """
    repo_configs_list = settings.get("repos", [])

    result = []
    for config_dict in repo_configs_list:
        if not isinstance(config_dict, dict):
            raise ValueError("Each repository config in multi.json must be an object.")

        if "url" not in config_dict:
            raise ValueError(
                "Repository config in multi.json must contain a 'url' field."
            )

        # Directly pass the config_dict; __init__ will handle parsing.
        result.append(Repository(**config_dict))

    if not result:
        raise NoRepositoriesError("No repositories found in multi.json settings.")

    return result
