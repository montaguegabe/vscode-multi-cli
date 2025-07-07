import copy

from vscode_multi.utils import apply_defaults_to_structure


def test_apply_defaults_to_list_of_dicts():
    """Test basic application of defaults to a list of dictionaries."""
    target = [{"name": "item1"}, {"name": "item2", "value": 20}]
    defaults = [{"default_prop": "default_value", "value": 10}]
    expected = [
        {"name": "item1", "default_prop": "default_value", "value": 10},
        {"name": "item2", "default_prop": "default_value", "value": 20},
    ]
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_apply_defaults_to_list_of_dicts_existing_simple_keys_preserved():
    """Test that existing simple keys in list items are preserved."""
    target = [{"a": 1, "b": "original_b"}, {"a": 2}]
    defaults = [{"b": "default_b", "c": "default_c"}]
    expected = [
        {"a": 1, "b": "original_b", "c": "default_c"},
        {"a": 2, "b": "default_b", "c": "default_c"},
    ]
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_apply_defaults_to_list_of_dicts_nested_structures():
    """Test applying defaults to nested structures within list items."""
    target = [
        {"id": 1, "config": {"setting1": "val1"}},
        {"id": 2, "config": {"setting2": "val2"}},
        {"id": 3},  # Item without 'config'
    ]
    defaults = [
        {
            "config": {"default_setting": True, "setting1": "default_val1"},
            "status": "default_status",
        }
    ]
    expected = [
        {
            "id": 1,
            "config": {"setting1": "val1", "default_setting": True},
            "status": "default_status",
        },
        {
            "id": 2,
            "config": {
                "setting2": "val2",
                "default_setting": True,
                "setting1": "default_val1",
            },
            "status": "default_status",
        },
        {
            "id": 3,
            "config": {"default_setting": True, "setting1": "default_val1"},
            "status": "default_status",
        },
    ]
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_apply_defaults_to_empty_list():
    """Test applying defaults to an empty list."""
    target = []
    defaults = [{"default_key": "default_value"}]
    expected = []
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_apply_defaults_to_list_of_non_dicts():
    """Test applying defaults to a list of non-dictionary items."""
    target = {"outer": ["item1", 100, None]}
    defaults = {"outer": [{"default_key": "default_value"}]}
    # Since items are not dicts, the dict default shouldn't apply to them
    expected = {"outer": ["item1", 100, None]}
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_input_target_immutability_for_list():
    """Test that the original input target list is not mutated."""
    original_target = [{"a": 1, "nested": {"x": 10}}, {"b": 2}]
    target_to_pass = copy.deepcopy(original_target)
    defaults = [{"default_key": "default_value", "nested": {"y": 20}}]

    apply_defaults_to_structure(target_to_pass, defaults)

    # Check that the original_target remains unchanged
    assert original_target == [{"a": 1, "nested": {"x": 10}}, {"b": 2}], (
        "Original target list was mutated."
    )


def test_dict_with_list_value_defaults():
    """Test dictionary with a value that should be a list with item defaults."""
    target = {
        "configurations": [{"name": "config1", "value": 10}, {"name": "config2"}],
        "simple_key": "simple_value",
    }
    defaults = {
        "configurations": {"apply_to_list_items": {"value": 0, "type": "default_type"}},
        "simple_key": "default_simple",
        "new_key": "new_value",
    }
    expected = {
        "configurations": [
            {"name": "config1", "value": 10, "type": "default_type"},
            {"name": "config2", "value": 0, "type": "default_type"},
        ],
        "simple_key": "simple_value",
        "new_key": "new_value",
    }
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_dict_with_missing_list_value():
    """Test dictionary where a key's value should be a list (based on defaults) but is missing."""
    target = {"other_key": "value"}
    defaults = {
        "configurations": {"apply_to_list_items": {"name": "default_name", "value": 0}},
        "other_key": "default_value",
    }
    expected = {
        "configurations": [],  # Empty list since no items to apply defaults to
        "other_key": "value",
    }
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_deeply_nested_defaults_in_list_items():
    """Test defaults for deeply nested structures within list items."""
    target = [
        {"item_id": "A", "data": {"level1": {"level2a": {"x": 1}}}},
        {"item_id": "B", "data": {"level1": {"level2b": {"y": 2}}}},
        {"item_id": "C"},
    ]
    defaults = [
        {
            "data": {
                "level1": {
                    "level2a": {"default_x": 100, "z": 3},
                    "level2b": {"default_y": 200, "z": 3},
                    "new_level2": {"k": 30},
                },
                "default_data_prop": "data_default",
            },
            "status": "pending",
        }
    ]
    expected = [
        {
            "item_id": "A",
            "data": {
                "level1": {
                    "level2a": {"x": 1, "default_x": 100, "z": 3},
                    "level2b": {"default_y": 200, "z": 3},
                    "new_level2": {"k": 30},
                },
                "default_data_prop": "data_default",
            },
            "status": "pending",
        },
        {
            "item_id": "B",
            "data": {
                "level1": {
                    "level2a": {"default_x": 100, "z": 3},
                    "level2b": {"y": 2, "default_y": 200, "z": 3},
                    "new_level2": {"k": 30},
                },
                "default_data_prop": "data_default",
            },
            "status": "pending",
        },
        {
            "item_id": "C",
            "data": {
                "level1": {
                    "level2a": {"default_x": 100, "z": 3},
                    "level2b": {"default_y": 200, "z": 3},
                    "new_level2": {"k": 30},
                },
                "default_data_prop": "data_default",
            },
            "status": "pending",
        },
    ]
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_none_target_with_list_defaults():
    """Test handling of None target with list item defaults."""
    target = None
    defaults = [{"name": "default_name", "value": 0}]
    expected = []  # None with list defaults becomes empty list
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_none_target_with_dict_defaults():
    """Test handling of None target with dictionary defaults."""
    target = None
    defaults = {"key": "value", "nested": {"sub": 10}}
    expected = {"key": "value", "nested": {"sub": 10}}
    result = apply_defaults_to_structure(target, defaults)
    assert result == expected


def test_primitive_defaults():
    """Test handling of primitive (non-dict, non-list) defaults."""
    assert apply_defaults_to_structure(None, "default") == "default"
    assert apply_defaults_to_structure(None, 42) == 42
    assert apply_defaults_to_structure("existing", "default") == "existing"
    assert apply_defaults_to_structure(10, "default") == 10
