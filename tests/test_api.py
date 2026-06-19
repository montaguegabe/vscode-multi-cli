from pathlib import Path

from multi import api, app_api


def _clear_project_summary_cache():
    with app_api._project_summary_cache_lock:
        app_api._cached_project_summary_metadata.clear()
        app_api._refreshing_project_summary_paths.clear()


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


def test_get_projects_summary_returns_placeholder_and_schedules_refresh(monkeypatch):
    _clear_project_summary_cache()
    submitted = []

    class FakeExecutor:
        def submit(self, fn, *args):
            submitted.append((fn, args))
            return object()

    monkeypatch.setattr(app_api, "_project_summary_executor", FakeExecutor())
    monkeypatch.setattr(
        app_api.Path, "stat", lambda self: (_ for _ in ()).throw(OSError())
    )

    projects = app_api.get_projects_summary(["/tmp/example"])

    assert projects == [
        {
            "path": "/tmp/example",
            "name": "example",
            "lastModifiedMs": None,
            "lastCommitMs": None,
            "status": "unknown",
            "doctorResult": None,
            "subRepos": None,
        }
    ]
    assert len(submitted) == 1
    assert submitted[0][1] == ("/tmp/example",)


def test_get_projects_summary_reuses_cached_metadata_without_refresh(monkeypatch):
    _clear_project_summary_cache()
    submitted = []

    class FakeExecutor:
        def submit(self, fn, *args):
            submitted.append((fn, args))
            return object()

    monkeypatch.setattr(app_api, "_project_summary_executor", FakeExecutor())
    monkeypatch.setattr(
        app_api.Path, "stat", lambda self: (_ for _ in ()).throw(OSError())
    )
    with app_api._project_summary_cache_lock:
        app_api._cached_project_summary_metadata["/tmp/example"] = (
            app_api.time.monotonic(),
            {
                "lastCommitMs": 123,
                "status": "dirty",
                "doctorResult": {"errors": [], "warnings": ["check"]},
                "subRepos": [{"name": "api", "path": "/tmp/example/api"}],
            },
        )

    projects = app_api.get_projects_summary(["/tmp/example"])

    assert projects[0]["lastCommitMs"] == 123
    assert projects[0]["status"] == "dirty"
    assert projects[0]["doctorResult"] == {"errors": [], "warnings": ["check"]}
    assert projects[0]["subRepos"] == [{"name": "api", "path": "/tmp/example/api"}]
    assert submitted == []
