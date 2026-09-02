from __future__ import annotations

import dataclasses
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path
from typing import Any, Literal, TypedDict

from multi.doctor import run_doctor_checks
from multi.errors import NoRepositoriesError
from multi.paths import Paths
from multi.repos import Repository, load_repos

RepoStatus = Literal[
    "clean",
    "dirty",
    "out-of-sync",
    "no_git",
    "missing",
    "unknown",
]

HISTORY_GROUP_WINDOW_MS = 60_000
HISTORY_MAX_COMMITS_PER_REPO = 250
GIT_HISTORY_FORMAT = "%H%x1f%h%x1f%an%x1f%ae%x1f%at%x1f%s%x1f%b%x1e"
PROJECT_SUMMARY_METADATA_CACHE_TTL_SECONDS = 10.0
PROJECT_SUMMARY_WORKERS = 8
PROJECT_SUMMARY_TIMEOUT_SECONDS = 12.0

_project_summary_cache_lock = threading.Lock()
_project_summary_executor = ThreadPoolExecutor(
    max_workers=PROJECT_SUMMARY_WORKERS,
    thread_name_prefix="multi-project-summary",
)
_cached_project_summary_metadata: dict[str, tuple[float, dict[str, Any]]] = {}
_refreshing_project_summary_paths: set[str] = set()


class RepoSyncState(TypedDict):
    ahead: int
    behind: int
    hasUpstream: bool
    isRepo: bool


class SubRepoPayload(TypedDict):
    name: str
    path: str


class RepoBranchPayload(TypedDict):
    name: str
    path: str
    branch: str


def _run_git(
    args: list[str],
    cwd: Path,
    timeout: int = 30,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        input=input_text,
    )


def _normalize_optional_ms(value: int | None) -> int | None:
    if value is None:
        return None
    return value


def _get_git_top_level(repo_path: Path) -> Path | None:
    try:
        result = _run_git(["rev-parse", "--show-toplevel"], cwd=repo_path)
    except (OSError, subprocess.SubprocessError):
        return None

    top_level = result.stdout.strip()
    if not top_level:
        return None
    return Path(top_level).resolve()


def is_git_repo_root(repo_path: Path) -> bool:
    top_level = _get_git_top_level(repo_path)
    if top_level is None:
        return False
    return top_level == repo_path.resolve()


def _load_subrepos(repo_path: Path) -> list[Repository] | None:
    multi_json_path = repo_path / "multi.json"
    if not multi_json_path.exists():
        return None

    try:
        paths = Paths(repo_path)
        if paths.root_dir.resolve() != repo_path.resolve():
            return None
        return sorted(load_repos(paths), key=lambda repo: repo.name)
    except (FileNotFoundError, NoRepositoriesError, ValueError, OSError):
        return None


def _subrepo_payloads(repo_path: Path) -> list[SubRepoPayload] | None:
    subrepos = _load_subrepos(repo_path)
    if not subrepos:
        return None

    return [
        {
            "name": repo.name,
            "path": str(repo.path),
        }
        for repo in subrepos
    ]


def get_project_subrepos(repo_path: str | Path) -> list[SubRepoPayload]:
    """Public multi.json sub-repo listing for library consumers ([] when not a workspace)."""
    return _subrepo_payloads(Path(repo_path)) or []


def list_project_repo_names(repo_path: str | Path) -> list[str]:
    """Names of repos declared in repo_path's own multi.json ([] when absent/invalid).

    Only reads a multi.json directly inside repo_path — never searches parent
    directories — so callers can safely probe arbitrary directories.
    """
    subrepos = _load_subrepos(Path(repo_path))
    return [repo.name for repo in subrepos] if subrepos else []


def _describe_git_head(repo_path: Path) -> str | None:
    if not repo_path.exists():
        return None

    if not (repo_path / ".git").exists():
        return None

    if not is_git_repo_root(repo_path):
        return None

    try:
        branch = _run_git(
            ["symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=repo_path,
            timeout=10,
        ).stdout.strip()
        if branch:
            return branch
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        short_sha = _run_git(
            ["rev-parse", "--short", "HEAD"],
            cwd=repo_path,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

    return f"(detached at {short_sha})" if short_sha else None


def get_project_branches(repo_path: str | Path) -> list[RepoBranchPayload]:
    project_path = Path(repo_path)
    root_name = project_path.name or str(project_path)
    subrepos = _load_subrepos(project_path) or []
    repo_entries = [
        {
            "name": root_name,
            "path": project_path,
        },
        *[
            {
                "name": repo.name,
                "path": Path(repo.path),
            }
            for repo in subrepos
        ],
    ]

    branch_entries: list[RepoBranchPayload] = []
    seen_paths: set[Path] = set()
    for entry in repo_entries:
        entry_path = entry["path"]
        resolved_path = entry_path.resolve()
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)

        branch = _describe_git_head(entry_path)
        if branch is None:
            continue

        branch_entries.append(
            {
                "name": str(entry["name"]),
                "path": str(entry_path),
                "branch": branch,
            }
        )

    return branch_entries


def _get_git_status_internal(repo_path: Path, ignore_untracked: bool) -> RepoStatus:
    if not repo_path.exists():
        return "missing"

    if not (repo_path / ".git").exists():
        return "no_git"

    status_args = ["status", "--porcelain"]
    if ignore_untracked:
        status_args.append("--untracked-files=no")

    try:
        porcelain = _run_git(status_args, cwd=repo_path, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        # A directory with a .git entry that git itself rejects (corrupt or
        # locked repo) is neither clean nor dirty; report it as unknown
        # instead of surfacing an exception to status callers.
        return "unknown"
    if porcelain.strip():
        return "dirty"

    try:
        rev_list = _run_git(
            ["rev-list", "--left-right", "--count", "HEAD...@{u}"],
            cwd=repo_path,
            timeout=10,
        ).stdout
        ahead, behind = [int(part) for part in rev_list.strip().split()]
        if ahead > 0 or behind > 0:
            return "out-of-sync"
    except (OSError, ValueError, subprocess.SubprocessError):
        return "out-of-sync"

    return "clean"


def get_repo_status(repo_path: str | Path) -> RepoStatus:
    return _get_git_status_internal(Path(repo_path), ignore_untracked=False)


def get_repo_sync_state(repo_path: str | Path) -> RepoSyncState:
    repo = Path(repo_path)
    if not repo.exists():
        return {
            "ahead": 0,
            "behind": 0,
            "hasUpstream": False,
            "isRepo": False,
        }

    if not (repo / ".git").exists():
        return {
            "ahead": 0,
            "behind": 0,
            "hasUpstream": False,
            "isRepo": False,
        }

    try:
        rev_list = _run_git(
            ["rev-list", "--left-right", "--count", "HEAD...@{u}"],
            cwd=repo,
            timeout=10,
        ).stdout
        ahead, behind = [int(part) for part in rev_list.strip().split()]
        return {
            "ahead": ahead if isinstance(ahead, int) else 0,
            "behind": behind if isinstance(behind, int) else 0,
            "hasUpstream": True,
            "isRepo": True,
        }
    except (OSError, ValueError, subprocess.SubprocessError):
        return {
            "ahead": 0,
            "behind": 0,
            "hasUpstream": False,
            "isRepo": True,
        }


def _get_latest_commit_ms_for_repo(repo_path: Path) -> int | None:
    if not repo_path.exists():
        return None

    if not (repo_path / ".git").exists():
        return None

    if not is_git_repo_root(repo_path):
        return None

    try:
        stdout = _run_git(
            ["log", "-1", "--format=%at"], cwd=repo_path, timeout=10
        ).stdout
        authored_at_seconds = int(stdout.strip())
        return authored_at_seconds * 1000
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _worst_status(a: RepoStatus, b: RepoStatus) -> RepoStatus:
    severity = {
        "clean": 0,
        "unknown": 1,
        "no_git": 2,
        "out-of-sync": 3,
        "dirty": 4,
        "missing": 5,
    }
    return a if severity[a] >= severity[b] else b


def get_project_status(repo_path: str | Path) -> RepoStatus:
    project_path = Path(repo_path)
    subrepos = _load_subrepos(project_path)
    if subrepos:
        statuses: list[RepoStatus] = [
            _get_git_status_internal(project_path, ignore_untracked=True),
            *[
                _get_git_status_internal(Path(repo.path), ignore_untracked=False)
                for repo in subrepos
            ],
        ]
        worst = statuses[0]
        if worst in {"missing", "no_git"}:
            worst = "clean"
        for status in statuses[1:]:
            if status in {"missing", "no_git"}:
                continue
            worst = _worst_status(worst, status)
        return worst

    return get_repo_status(project_path)


def get_project_last_commit_ms(repo_path: str | Path) -> int | None:
    project_path = Path(repo_path)
    subrepos = _load_subrepos(project_path) or []
    repo_paths = [project_path, *[Path(repo.path) for repo in subrepos]]
    commit_times = [
        commit_time
        for commit_time in (
            _get_latest_commit_ms_for_repo(candidate_path)
            for candidate_path in repo_paths
        )
        if commit_time is not None
    ]
    if not commit_times:
        return None
    return max(commit_times)


def get_repo_diff(repo_path: str | Path) -> str:
    repo = Path(repo_path)
    if not is_git_repo_root(repo):
        return ""

    tracked_diff = ""
    try:
        tracked_diff = _run_git(["diff", "HEAD"], cwd=repo).stdout
    except subprocess.CalledProcessError:
        unstaged = _run_git(["diff"], cwd=repo).stdout
        staged = _run_git(["diff", "--cached"], cwd=repo).stdout
        tracked_diff = unstaged + staged

    untracked_list = _run_git(
        ["ls-files", "--others", "--exclude-standard"],
        cwd=repo,
    ).stdout
    untracked_files = [line for line in untracked_list.strip().splitlines() if line]

    untracked_diffs: list[str] = []
    for file_path in untracked_files:
        try:
            _run_git(["diff", "--no-index", "--", "/dev/null", file_path], cwd=repo)
        except subprocess.CalledProcessError as exc:
            untracked_diffs.append(exc.stdout or "")

    return tracked_diff + "".join(untracked_diffs)


def _history_commit_from_record(
    record: str,
    repo_path: Path,
    repo_name: str,
) -> dict[str, Any] | None:
    (
        hash_value,
        short_hash,
        author_name,
        author_email,
        authored_at_unix,
        subject,
        *description_parts,
    ) = record.split("\x1f")

    description = next(
        (
            line.strip()
            for line in "\x1f".join(description_parts).splitlines()
            if line.strip()
        ),
        "",
    )

    try:
        authored_at_ms = int(authored_at_unix) * 1000
    except ValueError:
        return None

    if not hash_value or not short_hash or not subject:
        return None

    return {
        "hash": hash_value,
        "shortHash": short_hash,
        "subject": subject,
        "description": description,
        "authorName": author_name or "",
        "authorEmail": author_email or "",
        "authoredAtMs": authored_at_ms,
        "authoredAtIso": __import__("datetime")
        .datetime.fromtimestamp(
            authored_at_ms / 1000,
            tz=__import__("datetime").timezone.utc,
        )
        .isoformat()
        .replace("+00:00", "Z"),
        "repoPath": str(repo_path),
        "repoName": repo_name,
    }


def get_history_for_repo(repo_path: str | Path, repo_name: str) -> list[dict[str, Any]]:
    repo = Path(repo_path)
    if not repo.exists() or not is_git_repo_root(repo):
        return []

    try:
        stdout = _run_git(
            [
                "log",
                "--date-order",
                f"--max-count={HISTORY_MAX_COMMITS_PER_REPO}",
                f"--pretty=format:{GIT_HISTORY_FORMAT}",
            ],
            cwd=repo,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []

    if not stdout.strip():
        return []

    entries: list[dict[str, Any]] = []
    for record in stdout.split("\x1e"):
        stripped = record.strip()
        if not stripped:
            continue
        parsed = _history_commit_from_record(stripped, repo, repo_name)
        if parsed is not None:
            entries.append(parsed)
    return entries


def group_history_commits(commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not commits:
        return []

    sorted_commits = sorted(
        commits,
        key=lambda commit: (-commit["authoredAtMs"], commit["hash"]),
    )

    groups: list[dict[str, Any]] = []
    for commit in sorted_commits:
        current_group = groups[-1] if groups else None
        previous_commit = (
            current_group["commits"][-1]
            if current_group and current_group["commits"]
            else None
        )
        should_merge = (
            previous_commit is not None
            and abs(previous_commit["authoredAtMs"] - commit["authoredAtMs"])
            <= HISTORY_GROUP_WINDOW_MS
        )

        if current_group is not None and should_merge:
            current_group["commits"].append(commit)
            current_group["oldestAuthoredAtMs"] = commit["authoredAtMs"]
            if commit["repoName"] not in current_group["repoNames"]:
                current_group["repoNames"].append(commit["repoName"])
            continue

        groups.append(
            {
                "id": f"{commit['authoredAtMs']}-{commit['hash']}",
                "newestAuthoredAtMs": commit["authoredAtMs"],
                "oldestAuthoredAtMs": commit["authoredAtMs"],
                "authoredAtIso": commit["authoredAtIso"],
                "repoNames": [commit["repoName"]],
                "commits": [commit],
            }
        )

    return groups


def get_combined_history(repo_path: str | Path) -> list[dict[str, Any]]:
    project_path = Path(repo_path)
    subrepos = _load_subrepos(project_path) or []
    repos = [
        {
            "name": project_path.name or str(project_path),
            "path": project_path,
        },
        *[
            {
                "name": repo.name,
                "path": Path(repo.path),
            }
            for repo in subrepos
        ],
    ]

    unique_repos: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for repo in repos:
        resolved_path = repo["path"].resolve()
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)
        unique_repos.append(repo)

    histories: list[dict[str, Any]] = []
    for repo in unique_repos:
        histories.extend(get_history_for_repo(repo["path"], repo["name"]))

    return group_history_commits(histories)


def get_history_group_diff(commits: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not commits:
        return []

    by_repo: dict[tuple[str, str], dict[str, Any]] = {}
    for commit in commits:
        repo_path = str(Path(commit["repoPath"]).resolve())
        repo_name = commit["repoName"]
        key = (repo_path, repo_name)
        if key not in by_repo:
            by_repo[key] = {
                "repoPath": commit["repoPath"],
                "repoName": repo_name,
                "hashes": [],
            }
        by_repo[key]["hashes"].append(commit["hash"])

    repo_diffs: list[dict[str, str]] = []
    for repo in by_repo.values():
        diffs: list[str] = []
        for hash_value in repo["hashes"]:
            try:
                stdout = _run_git(
                    ["show", "--format=", "--no-color", hash_value],
                    cwd=Path(repo["repoPath"]),
                ).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                stdout = ""
            if stdout:
                diffs.append(stdout)

        if not diffs:
            continue

        repo_diffs.append(
            {
                "repoPath": repo["repoPath"],
                "repoName": repo["repoName"],
                "diff": "\n".join(diffs),
            }
        )

    return repo_diffs


def _doctor_result(repo_path: Path) -> dict[str, Any] | None:
    if not (repo_path / "multi.json").exists():
        return None

    report = run_doctor_checks(repo_path)
    return {
        "errors": report.errors,
        "warnings": report.warnings,
    }


def _project_summary_static_payload(repo_path: str | Path) -> dict[str, Any]:
    project_path = Path(repo_path)
    name = project_path.name or str(project_path)
    try:
        last_modified_ms = int(project_path.stat().st_mtime * 1000)
    except OSError:
        last_modified_ms = None

    return {
        "path": str(project_path),
        "name": name,
        "lastModifiedMs": _normalize_optional_ms(last_modified_ms),
    }


def _project_summary_metadata(repo_path: str | Path) -> dict[str, Any]:
    project_path = Path(repo_path)
    return {
        "lastCommitMs": _normalize_optional_ms(
            get_project_last_commit_ms(project_path)
        ),
        "status": get_project_status(project_path),
        "doctorResult": _doctor_result(project_path),
        "subRepos": _subrepo_payloads(project_path),
        "branches": get_project_branches(project_path),
    }


def _project_summary_fallback_metadata() -> dict[str, Any]:
    return {
        "lastCommitMs": None,
        "status": "unknown",
        "doctorResult": None,
        "subRepos": None,
        "branches": [],
    }


def _cached_project_metadata(repo_path: str) -> tuple[dict[str, Any] | None, bool]:
    now = time.monotonic()
    with _project_summary_cache_lock:
        cached = _cached_project_summary_metadata.get(repo_path)
        if cached is None:
            return None, False
        cached_at, metadata = cached
        return dict(
            metadata
        ), now - cached_at < PROJECT_SUMMARY_METADATA_CACHE_TTL_SECONDS


def _refresh_project_summary_metadata_task(repo_path: str) -> None:
    try:
        metadata = _project_summary_metadata(repo_path)
        with _project_summary_cache_lock:
            _cached_project_summary_metadata[repo_path] = (time.monotonic(), metadata)
    finally:
        with _project_summary_cache_lock:
            _refreshing_project_summary_paths.discard(repo_path)


def _schedule_project_summary_metadata_refresh(repo_paths: list[str]) -> None:
    now = time.monotonic()
    scheduled: list[str] = []
    with _project_summary_cache_lock:
        for repo_path in dict.fromkeys(path for path in repo_paths if path):
            cached = _cached_project_summary_metadata.get(repo_path)
            if (
                cached is not None
                and now - cached[0] < PROJECT_SUMMARY_METADATA_CACHE_TTL_SECONDS
            ):
                continue
            if repo_path in _refreshing_project_summary_paths:
                continue
            _refreshing_project_summary_paths.add(repo_path)
            scheduled.append(repo_path)

    for repo_path in scheduled:
        _project_summary_executor.submit(
            _refresh_project_summary_metadata_task, repo_path
        )


def _project_summary_payload(repo_path: str | Path) -> dict[str, Any]:
    path_key = str(repo_path)
    metadata, is_fresh = _cached_project_metadata(path_key)
    if not is_fresh:
        _schedule_project_summary_metadata_refresh([path_key])
    return {
        **_project_summary_static_payload(repo_path),
        **(metadata or _project_summary_fallback_metadata()),
    }


def get_project_summary(repo_path: str | Path) -> dict[str, Any]:
    return {
        **_project_summary_static_payload(repo_path),
        **_project_summary_metadata(repo_path),
    }


def get_projects_summary(repo_paths: list[str]) -> list[dict[str, Any]]:
    return [_project_summary_payload(repo_path) for repo_path in repo_paths]


def refresh_projects_summary(repo_paths: list[str]) -> list[dict[str, Any]]:
    unique_paths = list(dict.fromkeys(path for path in repo_paths if path))
    futures = {
        _project_summary_executor.submit(
            _project_summary_metadata, repo_path
        ): repo_path
        for repo_path in unique_paths
    }
    refreshed: dict[str, dict[str, Any]] = {}
    deadline = time.monotonic() + PROJECT_SUMMARY_TIMEOUT_SECONDS

    try:
        for future in as_completed(futures, timeout=PROJECT_SUMMARY_TIMEOUT_SECONDS):
            repo_path = futures[future]
            remaining = max(0.0, deadline - time.monotonic())
            try:
                metadata = future.result(timeout=remaining)
            except Exception:
                metadata = _project_summary_fallback_metadata()
            refreshed[repo_path] = metadata
            with _project_summary_cache_lock:
                _cached_project_summary_metadata[repo_path] = (
                    time.monotonic(),
                    metadata,
                )
    except TimeoutError:
        pass

    return [
        {
            **_project_summary_static_payload(repo_path),
            **refreshed.get(repo_path, _project_summary_fallback_metadata()),
        }
        for repo_path in unique_paths
    ]


def get_project_detail(repo_path: str | Path) -> dict[str, Any]:
    project_path = Path(repo_path)
    root_name = project_path.name or str(project_path)
    subrepos = _subrepo_payloads(project_path)

    repo_entries = [
        {
            "name": root_name,
            "path": str(project_path),
        },
        *(subrepos or []),
    ]

    unique_entries: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    for entry in repo_entries:
        resolved = Path(entry["path"]).resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        unique_entries.append(entry)

    repositories: list[dict[str, str]] = []
    sync_states_by_repo_path: dict[str, RepoSyncState] = {}
    for entry in unique_entries:
        repo_entry_path = entry["path"]
        try:
            diff = get_repo_diff(repo_entry_path)
        except (OSError, subprocess.SubprocessError):
            diff = ""

        repositories.append(
            {
                "path": repo_entry_path,
                "name": entry["name"],
                "diff": diff,
            }
        )
        sync_states_by_repo_path[repo_entry_path] = get_repo_sync_state(repo_entry_path)

    return {
        "repoPath": str(project_path),
        "repositories": repositories,
        "historyGroups": get_combined_history(project_path),
        "syncStatesByRepoPath": sync_states_by_repo_path,
        "subRepos": subrepos,
        "branches": get_project_branches(project_path),
    }


def serialize_dataclass(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return value
