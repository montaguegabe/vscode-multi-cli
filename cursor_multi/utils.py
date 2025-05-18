import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def write_json_file(path: Path, data: Dict[str, Any]):
    """Write a JSON file, creating the directory if it doesn't exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
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


def apply_defaults_to_structure(target: Any, defaults_definition: Any) -> Any:
    """
    Recursively applies default values to a target structure.
    Defaults are applied only if the corresponding keys/paths do not exist in the target.
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
