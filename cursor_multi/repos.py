import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from cursor_multi.errors import NoRepositoriesError
from cursor_multi.paths import get_root


@dataclass
class Repository:
    """Represents a repository in the workspace.

    Attributes:
        url: The repository URL
        name: Repository name derived from the URL
        path: Local filesystem path where the repository is/will be cloned
    """

    url: str
    options: dict | None = None
    skip: bool = False

    def __post_init__(self):
        """Derive name and path from URL after initialization."""
        self.name = self.url.split("/")[-1]
        self.path = get_root() / self.name
        if self.options is None:
            self.options = {}

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
    """Load repository information from repos.json.

    The repos.json file should contain a list of objects with the following structure:
    [
        {
            "url": "https://github.com/user/repo",
            "options": {
                // Repository-specific settings (optional)
            }
        },
        // More repositories...
    ]
    """
    root = get_root()
    repos_file = Path(root) / "repos.json"

    with open(repos_file) as f:
        repo_configs = json.load(f)

    result = []
    for config in repo_configs:
        if isinstance(config, dict):
            url = config.get("url")
            if not url:
                raise ValueError("Repository config must contain a 'url' field")
            result.append(Repository(url=url, **config.get("options", {})))
        else:
            raise ValueError(
                "Each repository config must be an object with a 'url' field"
            )

    if not result:
        raise NoRepositoriesError("No repositories found in repos.json")

    return result
