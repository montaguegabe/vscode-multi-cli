from pathlib import Path

from multi import api


def test_sync_workspace_delegates_to_sync(monkeypatch):
    calls = []

    def fake_sync(*, root_dir, ensure_on_same_branch, install_set):
        calls.append(
            {
                "root_dir": root_dir,
                "ensure_on_same_branch": ensure_on_same_branch,
                "install_set": install_set,
            }
        )

    monkeypatch.setattr(api, "sync", fake_sync)

    api.sync_workspace(
        "/tmp/example",
        install_set="default",
        ensure_on_same_branch=False,
    )

    assert calls == [
        {
            "root_dir": Path("/tmp/example"),
            "ensure_on_same_branch": False,
            "install_set": "default",
        }
    ]
