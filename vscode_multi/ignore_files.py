import logging
from pathlib import Path
from typing import List, Optional

from vscode_multi.paths import paths
from vscode_multi.repos import load_repos

logger = logging.getLogger(__name__)


class IgnoreFile:
    def __init__(self, path: Path):
        self.path = path
        self._existing_lines: Optional[List[str]] = None

    @property
    def existing_lines(self) -> List[str]:
        """Lazily load and cache existing lines from the file."""
        if self._existing_lines is None:
            self._existing_lines = self._read_lines()
        return self._existing_lines

    def _read_lines(self) -> List[str]:
        """Read and return lines from the ignore file."""
        if not self.path.exists():
            return []
        with self.path.open("r") as f:
            return [line.strip() for line in f.readlines()]

    def add_lines_if_missing(self, lines: List[str], header: str) -> None:
        """Add lines under the specified header section, creating it if needed.

        If the header exists, new lines are added under the existing section.
        If the header doesn't exist, it's added to the bottom of the file.
        Only lines that don't already exist in the file are added.
        """
        if not lines:
            return

        # Find lines that don't already exist
        lines_to_add = [line for line in lines if line not in self.existing_lines]
        if not lines_to_add:
            return

        existing_lines = self.existing_lines.copy()

        # Try to find the header in existing content
        try:
            header_index = existing_lines.index(header)
            # Find the end of this section (next header or end of file)
            section_end = header_index + 1
            while section_end < len(existing_lines):
                if existing_lines[section_end].startswith("#"):
                    break
                section_end += 1
            # Insert new lines after the last line in this section
            existing_lines[section_end:section_end] = lines_to_add
        except ValueError:
            # Header not found, add to end of file
            if existing_lines and existing_lines[-1] != "":
                existing_lines.append("")  # Add blank line before new section
            existing_lines.append(header)
            existing_lines.extend(lines_to_add)

        # Write back the updated content
        with self.path.open("w") as f:
            f.write("\n".join(existing_lines) + "\n")

        # Update cached lines
        self._existing_lines = existing_lines


def update_gitignore_with_repos():
    """Ensure all repos are in gitignore entries."""
    repos = load_repos()
    repo_entries = [f"{repo.name}/" for repo in repos]
    gitignore = IgnoreFile(paths.gitignore_path)
    gitignore.add_lines_if_missing(repo_entries, "# Ignore repository directories")
    logger.debug("Updated .gitignore with new repositories")


def update_ignore_with_repos():
    """Update .ignore to allow searching in gitignored directories."""
    repos = load_repos()
    repo_entries = [f"!{repo.name}/" for repo in repos]
    vscode_ignore = IgnoreFile(paths.vscode_ignore_path)
    vscode_ignore.add_lines_if_missing(
        repo_entries,
        "# Allow us to search inside these gitignored directories",
    )
    logger.debug("Updated .ignore with new repositories")


def update_gitignore_with_vscode_files():
    """Add VS Code generated configuration files to gitignore entries."""
    vscode_entries = [
        ".vscode/launch.json",
        ".vscode/settings.json",
        ".vscode/tasks.json",
        ".vscode/extensions.json",
    ]
    gitignore = IgnoreFile(paths.gitignore_path)
    gitignore.add_lines_if_missing(vscode_entries, "# Generated files")
    logger.debug("Updated .gitignore with VS Code configuration files")
