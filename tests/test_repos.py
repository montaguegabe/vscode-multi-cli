import pytest

from multi.paths import Paths
from multi.repos import Repository


def _paths(root):
    paths = Paths.__new__(Paths)
    paths.root_dir = root
    return paths


def test_relative_path_defaults_to_name(tmp_path):
    repo = Repository(paths=_paths(tmp_path), url="https://github.com/org/api")
    assert repo.name == "api"
    assert repo.relative_path == "api"
    assert repo.path == tmp_path / "api"


def test_custom_path_decouples_location_from_name(tmp_path):
    repo = Repository(
        paths=_paths(tmp_path),
        url="https://github.com/org/api",
        path="services/api",
    )
    # Name stays the repo identity; only the on-disk location changes.
    assert repo.name == "api"
    assert repo.relative_path == "services/api"
    assert repo.path == tmp_path / "services" / "api"


def test_custom_path_is_normalized(tmp_path):
    repo = Repository(
        paths=_paths(tmp_path),
        url="https://github.com/org/api",
        path="  services/api/  ",
    )
    assert repo.relative_path == "services/api"
    assert repo.path == tmp_path / "services" / "api"


@pytest.mark.parametrize("bad_path", ["/abs/api", "../escape", "services/../..", ""])
def test_custom_path_rejects_escapes_and_absolute(tmp_path, bad_path):
    with pytest.raises(ValueError):
        Repository(
            paths=_paths(tmp_path),
            url="https://github.com/org/api",
            path=bad_path,
        )


def test_custom_path_must_be_string(tmp_path):
    with pytest.raises(ValueError):
        Repository(
            paths=_paths(tmp_path),
            url="https://github.com/org/api",
            path=123,
        )
