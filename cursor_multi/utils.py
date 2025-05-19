import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def write_json_file(path: Path, data: Dict[str, Any]):
    """Write a JSON file, creating the directory if it doesn't exist."""

    # We make sure the parent exists because in the tests we are destroying the root directory every time, so create=True is not enough.
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


def _is_list_default_convention(value: Any) -> bool:
    """Checks if the value represents defaults for items in a list.
    Convention: A list containing a single dictionary.
    e.g., [{"default_prop": "default_value"}]
    """
    return isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict)


def apply_defaults_to_structure(target: Any, defaults_definition: Any) -> Any:
    """
    Recursively applies default values to a target structure.
    If defaults_definition for a list is a list containing a single dictionary, e.g. `[{"a":1}]`,
    this dictionary is applied as a default to each item in the target list.
    """
    if not defaults_definition:
        # If no defaults, return a copy of the target or the target itself if immutable.
        # Since target can be mutable (list/dict), a deepcopy is safer if modifications happened before this point
        # or if caller expects a new object. Given the function's copy-on-write internal, this might be redundant
        # for the initial call but ensures consistency.
        return copy.deepcopy(target)

    # Work on a deep copy of the target for modifications if target is None or to ensure no side-effects.
    # If target is not None, subsequent operations will use its copy.
    # This initial processed_target is crucial for the None case.
    processed_target = copy.deepcopy(target)

    # Case 1: Target is a list, AND defaults_definition implies list item defaults.
    if isinstance(target, list) and _is_list_default_convention(defaults_definition):
        item_defaults_spec = defaults_definition[0]
        result_list = []
        for item in target:
            # If item_defaults_spec is a dictionary (standard case for list item defaults),
            # but the item itself is not a dictionary, preserve the item.
            # Otherwise, apply defaults recursively.
            if isinstance(item_defaults_spec, dict) and not isinstance(item, dict):
                result_list.append(copy.deepcopy(item))
            else:
                result_list.append(
                    apply_defaults_to_structure(item, item_defaults_spec)
                )
        return result_list

    # Case 2: Target is a dictionary, and defaults_definition is a dictionary.
    elif isinstance(target, dict) and isinstance(defaults_definition, dict):
        # Start with a copy of the target dict to modify.
        # processed_target is already a deepcopy of the dict if target was a dict.
        # If target was None, processed_target is None, so we need to initialize to {} here for dict logic.
        current_dict_content = copy.deepcopy(target) if isinstance(target, dict) else {}

        for def_key, def_value_spec in defaults_definition.items():
            # Path A: The default for this key implies list item defaults.
            if _is_list_default_convention(def_value_spec):
                val_at_key_in_dict = current_dict_content.get(def_key)
                if not isinstance(val_at_key_in_dict, list):
                    val_at_key_in_dict = []  # Ensure it's a list, overwriting if not a list.
                current_dict_content[def_key] = apply_defaults_to_structure(
                    val_at_key_in_dict, def_value_spec
                )
            # Path B: Key is not in the current target dictionary.
            elif def_key not in current_dict_content:
                # Initialize current_dict_content[def_key] based on def_value_spec's nature.
                # The base for recursion is an "empty" version of what def_value_spec implies.
                base_for_new_key: Any
                if isinstance(def_value_spec, dict):
                    base_for_new_key = {}
                elif isinstance(def_value_spec, list):
                    # Note: _is_list_default_convention was false for def_value_spec here.
                    # So, this is a direct list default, not an item default spec.
                    base_for_new_key = []
                else:  # Primitive
                    current_dict_content[def_key] = copy.deepcopy(def_value_spec)
                    continue  # Skip recursion for primitives once assigned.

                current_dict_content[def_key] = apply_defaults_to_structure(
                    base_for_new_key, def_value_spec
                )
            # Path C: Key is in current_dict_content, and default is not list item convention.
            else:  # def_key in current_dict_content
                current_dict_content[def_key] = apply_defaults_to_structure(
                    current_dict_content[def_key],
                    def_value_spec,
                )
        return current_dict_content

    # Case 3: Target is None, and defaults_definition is provided.
    # Create structure based purely on defaults_definition.
    elif target is None and defaults_definition is not None:
        if _is_list_default_convention(defaults_definition):
            # Default implies a list structure with item defaults; start with an empty list.
            return apply_defaults_to_structure([], defaults_definition)
        elif isinstance(defaults_definition, dict):
            return apply_defaults_to_structure({}, defaults_definition)
        # If defaults_definition is a list (but not the item default convention) or a primitive:
        return copy.deepcopy(defaults_definition)

    # Fallback: Target is not a list or dict that matches defaults, or target is a primitive,
    # or defaults_definition didn't apply.
    return processed_target  # This was deepcopy(target) initially.
