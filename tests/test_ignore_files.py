from vscode_multi.ignore_files import IgnoreFile


def test_add_lines_preserves_existing_content(tmp_path):
    """Test that add_lines_if_missing preserves all existing content."""
    # Create a temporary gitignore with existing content
    ignore_path = tmp_path / ".gitignore"
    existing_content = [
        "# Existing section",
        "*.log",
        "*.tmp",
        "",
        "# Node stuff",
        "node_modules/",
        "package-lock.json",
        "",
        "# Python stuff",
        "__pycache__/",
        "*.pyc",
    ]
    ignore_path.write_text("\n".join(existing_content) + "\n")

    # Initialize IgnoreFile and add new lines
    ignore_file = IgnoreFile(ignore_path)
    new_lines = ["dist/", "build/"]
    ignore_file.add_lines_if_missing(new_lines, "# Build outputs")

    # Read the file and verify all original content is preserved
    updated_content = ignore_file.existing_lines
    for line in existing_content:
        assert line in updated_content

    # Verify new lines were added
    assert "# Build outputs" in updated_content
    assert "dist/" in updated_content
    assert "build/" in updated_content


def test_add_lines_to_existing_section(tmp_path):
    """Test that add_lines_if_missing adds lines under the correct header even with surrounding content."""
    ignore_path = tmp_path / ".gitignore"
    initial_content = [
        "# Top section",
        "*.log",
        "",
        "# Target section",
        "existing_item/",
        "",
        "# Bottom section",
        "*.tmp",
        "temp/",
    ]
    ignore_path.write_text("\n".join(initial_content) + "\n")

    # Add new lines to the middle section
    ignore_file = IgnoreFile(ignore_path)
    new_lines = ["new_item1/", "new_item2/"]
    ignore_file.add_lines_if_missing(new_lines, "# Target section")

    # Verify the structure
    updated_content = ignore_file.existing_lines

    # Check that all sections are preserved
    assert "# Top section" in updated_content
    assert "*.log" in updated_content
    assert "# Target section" in updated_content
    assert "existing_item/" in updated_content
    assert "# Bottom section" in updated_content
    assert "*.tmp" in updated_content
    assert "temp/" in updated_content

    # Check that new items were added in the correct section
    target_section_start = updated_content.index("# Target section")
    bottom_section_start = updated_content.index("# Bottom section")

    # Verify new items are between the target and bottom sections
    section_content = updated_content[target_section_start:bottom_section_start]
    assert "new_item1/" in section_content
    assert "new_item2/" in section_content
