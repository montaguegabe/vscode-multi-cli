from typing import Any, Dict, List


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
