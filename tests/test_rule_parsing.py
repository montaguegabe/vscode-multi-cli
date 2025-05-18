from pathlib import Path

import pytest

from cursor_multi.rules import Rule

RULE_EXAMPLES_DIR = Path(__file__).parent / "rule_examples"

EXAMPLE_FILES = [
    "manual-rule.txt",
    "auto-attached-rule.txt",
    "always-rule.txt",
    "agent-requested-rule.txt",
]


def read_rule_content(rule_file: str) -> str:
    """Read the content of a rule file from the examples directory."""
    file_path = RULE_EXAMPLES_DIR / rule_file
    return file_path.read_text()


@pytest.mark.parametrize(
    "rule_file",
    EXAMPLE_FILES,
)
def test_rule_round_trip(rule_file: str):
    """Test that parsing and rendering a rule produces the exact same string."""
    # Read the original content
    expected_content = read_rule_content(rule_file)

    # Parse the rule
    rule = Rule.parse(expected_content)
    # Render it back to string
    rendered = rule.render()

    # Compare with original
    assert rendered == expected_content, (
        f"Round-trip parsing/rendering of {rule_file} produced different output.\n"
        f"Expected:\n{expected_content}\n"
        f"Got:\n{rendered}"
    )
