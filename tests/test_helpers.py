"""Helper functions for tests."""

from typing import Any, Dict


def get_default_multi_json_content() -> Dict[str, Any]:
    """Get the default multi.json content for tests.

    This function is used by conftest.py to set up the test environment.
    Tests can mock this function to customize the multi.json content.
    """
    return {"repos": [{"url": f"https://github.com/test/repo{i}"} for i in range(2)]}
