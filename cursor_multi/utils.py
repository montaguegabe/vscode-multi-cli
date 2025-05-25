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
    """Load a JSON file if it exists, otherwise return an empty dict.
    Handles comments by removing anything after // that's not in a string."""
    if path.exists():
        try:
            with path.open("r") as f:
                lines = []
                for line in f:
                    processed_line = ""
                    in_string = False
                    string_char = None  # Track whether we're in ' or " string
                    i = 0
                    while i < len(line):
                        char = line[i]

                        # Handle string boundaries
                        if char in ['"', "'"] and (i == 0 or line[i - 1] != "\\"):
                            if not in_string:
                                in_string = True
                                string_char = char
                            elif (
                                string_char == char
                            ):  # Make sure we match the same quote type
                                in_string = False
                                string_char = None

                        # Look for comments outside of strings
                        if (
                            not in_string
                            and char == "/"
                            and i + 1 < len(line)
                            and line[i + 1] == "/"
                        ):
                            break

                        processed_line += char
                        i += 1

                    lines.append(processed_line)

                content = "".join(lines)
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Could not parse {path}: {str(e)}, skipping...")
    return {}


def _is_list_default_convention(value: Any) -> bool:
    """Checks if the value represents defaults for items in a list.
    Convention: A list containing a single dictionary.
    e.g., [{"default_prop": "default_value"}]
    """
    return isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict)


def apply_defaults_to_structure(target: Any, defaults_definition: Any) -> Any:
    """Apply defaults from defaults_definition to target structure.

    Args:
        target: The user-provided data structure to fill with defaults
        defaults_definition: The default values to apply

    Returns:
        The target structure with defaults applied for missing keys
    """
    # If defaults_definition is None, return target as-is
    if defaults_definition is None:
        return target

    # Handle the list default convention ([{"key": "value"}])
    if _is_list_default_convention(defaults_definition):
        if isinstance(target, list):
            item_defaults = defaults_definition[0]
            # Only apply defaults to items that are already dicts
            return [
                apply_defaults_to_structure(item, item_defaults)
                if isinstance(item, dict)
                else item
                for item in target
            ]
        elif target is None:
            # Target is None, return empty list
            return []
        else:
            # Target is not a list and not None, return target as-is
            return target

    # Handle the "apply_to_list_items" convention
    if (
        isinstance(defaults_definition, dict)
        and len(defaults_definition) == 1
        and "apply_to_list_items" in defaults_definition
    ):
        if isinstance(target, list):
            item_defaults = defaults_definition["apply_to_list_items"]
            # Only apply defaults to items that are already dicts
            return [
                apply_defaults_to_structure(item, item_defaults)
                if isinstance(item, dict)
                else item
                for item in target
            ]
        elif target is None:
            # Target is None, return empty list
            return []
        else:
            # Target is not a list and not None, return target as-is
            return target

    # If defaults_definition is a dict
    if isinstance(defaults_definition, dict):
        if isinstance(target, dict):
            # Both are dicts, merge them
            result = target.copy()
            for key, default_value in defaults_definition.items():
                if key in result:
                    # Recursively apply defaults to the existing value
                    result[key] = apply_defaults_to_structure(
                        result[key], default_value
                    )
                else:
                    # Key doesn't exist in target, use the default
                    result[key] = apply_defaults_to_structure(None, default_value)
            return result
        elif target is None:
            # Target is None, apply defaults to empty dict
            return apply_defaults_to_structure({}, defaults_definition)
        else:
            # Target is not a dict and not None, return target as-is
            return target

    # For all other cases (defaults_definition is a primitive), return target if not None, else defaults
    if target is None:
        return defaults_definition
    else:
        return target
