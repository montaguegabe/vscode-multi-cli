# branch

Show the current branch of the root repo and every sub-repo.

## Usage

```bash
multi branch
```

## Description

The `branch` command reports which branch the root repository and each sub-repository are currently on, and flags any repository that is not on its expected branch (the root branch, or the repo's configured `fixedBranch`).

It is **read-only** and intentionally has none of the preconditions of the mutating commands:

- Working trees may be **dirty** (uncommitted changes are fine)
- Repositories may be on **different branches** — mismatches are reported instead of blocking
- **Detached HEAD** states (common in git worktrees) are reported as `(detached at <short-sha>)` instead of failing
- Works in linked worktrees created by `multi worktree add`, where `.git` is a file

## Output

```text
my-workspace (root): feature/login
backend: feature/login
frontend: main (expected root branch feature/login)
docs: stable
```

Repos on their expected branch are listed plainly. Mismatched repos are flagged with the expected branch. Repos with `fixedBranch` are expected to be on that fixed branch instead of the root branch.

## Exit Status

- `0` — every repository is on its expected branch
- `1` — one or more repositories are not on their expected branches (the listing is still printed)

This makes `multi branch` usable as a quick verification step in scripts.

## Fixing Mismatches

To actually switch branches, use [`set-branch`](set-branch.md) — which, unlike `branch`, requires clean working trees:

```bash
multi branch                 # inspect (works dirty)
multi set-branch feature/x   # fix (requires clean trees)
```

## Notes

- In monorepo mode, only the root branch is reported (sub-directories are part of the root repo).
