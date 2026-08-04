# branch

Check expected branch alignment for the root repo and every sub-repo.

## Usage

```bash
multi branch
multi branch check
```

## Description

The `branch` command reports which branch the root repository and each sub-repository are currently on, and flags any repository that is not on its expected branch (the root branch, or the repo's configured `fixedBranch`).

`multi branch check` is the clearer explicit spelling for branch alignment checks. `multi branch` remains a backwards-compatible alias for the same check.

It is **read-only** and intentionally has none of the preconditions of the mutating commands:

- Working trees may be **dirty** (uncommitted changes are fine)
- Repositories may be on **different branches** — mismatches are reported instead of blocking
- **Detached HEAD** states (common in git worktrees) are reported as `(detached at <short-sha>)` instead of failing
- Works in linked worktrees created by `multi worktree add`, where `.git` is a file
- Sub-repos listed in `multi.json` that have **not been synced yet** (directory missing or not a git repository) are reported as ``(missing — run `multi sync`)`` and the report continues through the remaining repos

## Output

```text
my-workspace (root): feature/login
backend: feature/login
frontend: main (expected root branch feature/login)
docs: stable
extras: (missing — run `multi sync`)
```

Repos on their expected branch are listed plainly. Mismatched repos are flagged with the expected branch. Repos with `fixedBranch` are expected to be on that fixed branch instead of the root branch. Repos that have not been synced yet are flagged as missing.

## Exit Status

- `0` — every repository is present and on its expected branch
- `1` — one or more repositories are missing or not on their expected branches (the full listing is still printed)

This makes `multi branch check` and the backwards-compatible `multi branch` form usable as quick verification steps in scripts.

## Fixing Mismatches

To actually switch branches, use [`set-branch`](set-branch.md) — which, unlike `branch`, requires clean working trees:

```bash
multi branch check           # inspect (works dirty)
multi set-branch feature/x   # fix (requires clean trees)
```

## Notes

- `multi branch` and `multi branch check` run the same check.
- In monorepo mode, only the root branch is reported (sub-directories are part of the root repo).
