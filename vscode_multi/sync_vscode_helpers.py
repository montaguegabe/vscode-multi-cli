import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from vscode_multi.repos import Repository, load_repos
from vscode_multi.utils import (
    apply_defaults_to_structure,
    soft_read_json_file,
    write_json_file,
)

logger = logging.getLogger(__name__)


def prefix_repo_name_to_path(path: str, repo_name: str) -> str:
    if f"${{workspaceFolder}}/{repo_name}" in path:
        return path
    return path.replace("${workspaceFolder}", f"${{workspaceFolder}}/{repo_name}")


def prefix_repo_name_to_path_recursive(value: Any, repo_name: str) -> Any:
    """
    Recursively adjust workspace folder paths in values.

    Args:
        value: The value to process
        repo_name: Name of the repository to add to workspace folder paths
    """
    if isinstance(value, str) and "${workspaceFolder}" in value:
        return prefix_repo_name_to_path(value, repo_name)
    elif isinstance(value, dict):
        return {
            k: prefix_repo_name_to_path_recursive(v, repo_name)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [prefix_repo_name_to_path_recursive(item, repo_name) for item in value]
    return value


def _deep_merge_recursive(
    base: Dict[str, Any],
    override: Dict[str, Any],
    skip_keys: List[str] | None = None,
) -> Dict[str, Any]:
    merged = base.copy()

    for key, value in override.items():
        # Skip keys that we don't want to merge
        if skip_keys is not None and key in skip_keys:
            continue

        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_recursive(merged[key], value, skip_keys)
        elif (
            key in merged and isinstance(merged[key], list) and isinstance(value, list)
        ):
            # For lists, concatenate and remove duplicates while preserving order
            merged[key] = merged[key] + [x for x in value if x not in merged[key]]
        else:
            merged[key] = value

    return merged


def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    repo_name: str | None = None,
    skip_keys: List[str] | None = None,
) -> Dict[str, Any]:
    effective_override = override
    # Adjust workspace folder paths in the override value if repo_name is provided
    if repo_name:
        effective_override = prefix_repo_name_to_path_recursive(override, repo_name)

    # Perform the primary merge of base and (processed) override
    return _deep_merge_recursive(base, effective_override, skip_keys)


class VSCodeFileMerger(ABC):
    @abstractmethod
    def _get_destination_json_path(self) -> Path:
        """Get the destination path for the merged JSON file."""
        pass

    @abstractmethod
    def _get_source_json_path(self, repo_path: Path) -> Path:
        """Get the source JSON file path for a given repository."""
        pass

    def _get_repo_defaults(self, repo: Repository) -> Dict[str, Any] | None:
        """
        Get default values to apply to the repo's JSON.
        Subclasses can override this to provide specific defaults.
        """
        return None

    def _get_skip_keys(self, repo: Repository) -> List[str] | None:
        """
        Get a list of keys to skip during the deep merge for this repo.
        Subclasses can override this to provide specific keys to skip.
        Defaults to None, meaning no keys are skipped by default.
        """
        return None

    def _merge_repo_json(
        self,
        merged_json: Dict[str, Any],
        repo_json: Dict[str, Any],
        repo: Repository,
    ) -> Dict[str, Any]:
        """
        Merge the repo's JSON into the merged_json.
        Subclasses can override this to customize the merge behavior,
        for example, by applying defaults.
        """
        defaults = self._get_repo_defaults(repo)
        skip_keys = self._get_skip_keys(repo)
        effective_repo_json = repo_json
        if defaults:
            effective_repo_json = apply_defaults_to_structure(repo_json, defaults)

        return deep_merge(merged_json, effective_repo_json, repo.name, skip_keys)

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform any post-processing on the merged JSON before saving.
        Subclasses can override this to add or modify configurations.
        """
        return merged_json

    def merge(self) -> None:
        """
        Merges JSON files from all repositories into a single destination file.
        """
        destination_path = self._get_destination_json_path()
        destination_path.unlink(missing_ok=True)

        merged_json: Dict[str, Any] = {}
        repos_list = load_repos()

        for repo_item in repos_list:
            if repo_item.skip_vscode:
                logger.debug(f"Skipping {repo_item.name} for {destination_path.name}")
                continue

            repo_json_path = self._get_source_json_path(repo_item.path)
            repo_json_content = soft_read_json_file(repo_json_path)

            merged_json = self._merge_repo_json(
                merged_json, repo_json_content, repo_item
            )

        merged_json = self._post_process_json(merged_json)
        write_json_file(destination_path, merged_json)
        logger.info(f"Successfully merged files into {destination_path.name}")
