import copy
from typing import Any, Dict, List

from cursor_multi.settings import settings


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


def apply_defaults_to_structure(target: Any, defaults_definition: Any) -> Any:
    """
    Recursively applies default values to a target structure.
    Defaults are applied only if the corresponding keys/paths do not exist in the target.
    Path variables in default values (like "${workspaceFolder}") are processed.
    """
    if not defaults_definition:
        return target

    # Work on a deep copy of the target to avoid unintended side effects elsewhere
    # and to allow modification.
    processed_target = copy.deepcopy(target)

    if isinstance(processed_target, dict) and isinstance(defaults_definition, dict):
        for def_key, def_value_spec in defaults_definition.items():
            if def_key == "*":  # Should not be a key in defaults for a dict target
                continue

            if def_key not in processed_target:
                # Key from defaults is missing in target, so add it.
                # The def_value_spec is the default value or a deeper spec.
                # Process paths in the default value before adding.
                default_val_to_add = copy.deepcopy(def_value_spec)
                processed_target[def_key] = default_val_to_add
            else:
                # Key exists in target; recurse to apply defaults within this existing value.
                processed_target[def_key] = apply_defaults_to_structure(
                    processed_target[def_key],  # The existing value in the target
                    def_value_spec,
                )
        return processed_target
    elif (
        isinstance(processed_target, list)
        and isinstance(defaults_definition, dict)
        and "*" in defaults_definition
    ):
        # defaults_definition has a "*" key, indicating defaults for list items.
        item_defaults_spec = defaults_definition["*"]
        return [
            apply_defaults_to_structure(item, item_defaults_spec)
            for item in processed_target  # Iterate over items from the (copied) target list
        ]
    else:
        # Target is not a dict or list matching the defaults_definition structure,
        # or no defaults apply at this level. Return the (copied) target as is.
        return processed_target


def _deep_merge_recursive(
    base: Dict[str, Any],
    override: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    merged = base.copy()

    skip_keys: List[str] = kwargs.get("skip_keys", settings["vscode"]["skip_keys"])

    for key, value in override.items():
        # Skip keys that we don't want to merge
        if key in skip_keys:
            continue

        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_recursive(merged[key], value, **kwargs)
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
    **kwargs,
) -> Dict[str, Any]:
    effective_override = override
    # Adjust workspace folder paths in the override value if repo_name is provided
    if repo_name:
        effective_override = prefix_repo_name_to_path_recursive(override, repo_name)

    # Perform the primary merge of base and (processed) override
    return _deep_merge_recursive(base, effective_override, **kwargs)
