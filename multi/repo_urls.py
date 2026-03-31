from urllib.parse import urlparse


def normalize_repo_url(url: str) -> str:
    """Normalize a repo URL by stripping trailing / and .git for comparison."""
    normalized = url.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized


def derive_repo_slug_from_url(url: str) -> str:
    """Derive the repo slug (final path component) from a repository URL."""
    return normalize_repo_url(url).split("/")[-1]


def derive_short_local_name(slug: str, workspace_name: str) -> str | None:
    """Return a shortened local name for workspace-prefixed repo slugs."""
    if not workspace_name:
        return None

    candidate_prefixes = [workspace_name]
    workspace_suffix = "-workspace"
    if workspace_name.endswith(workspace_suffix):
        trimmed = workspace_name[: -len(workspace_suffix)]
        if trimmed:
            candidate_prefixes.append(trimmed)

    for candidate_prefix in candidate_prefixes:
        prefix = f"{candidate_prefix}-"
        if not slug.startswith(prefix):
            continue

        short_name = slug[len(prefix) :]
        if short_name:
            return short_name

    return None


def derive_explicit_local_name(url: str, workspace_name: str) -> str | None:
    """Return the explicit local name to write to multi.json, if any."""
    return derive_short_local_name(derive_repo_slug_from_url(url), workspace_name)


def parse_github_repo_slug(url: str) -> str | None:
    """Parse OWNER/REPO from supported GitHub remote URL formats."""
    normalized = normalize_repo_url(url)

    if normalized.startswith("git@github.com:"):
        path = normalized[len("git@github.com:") :]
    elif normalized.startswith("ssh://git@github.com/"):
        path = normalized[len("ssh://git@github.com/") :]
    else:
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != "github.com":
            return None
        path = parsed.path.lstrip("/")

    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        return None
    return f"{parts[0]}/{parts[1]}"
