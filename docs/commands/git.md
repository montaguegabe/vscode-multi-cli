# git

Run a git command across all repositories.

## Usage

```bash
multi git [GIT_ARGS...]
```

## Description

The `git` command executes any git subcommand in the root repository first, then in all sub-repositories. This is useful for performing git operations consistently across your entire workspace.

## Arguments

| Argument | Description |
|----------|-------------|
| `GIT_ARGS` | Any valid git command and arguments |

## Examples

### Pull latest changes

```bash
multi git pull
```

### Check status of all repos

```bash
multi git status
```

### Fetch from remote

```bash
multi git fetch --all
```

### Push changes

```bash
multi git push
```

### Push a new branch to origin

```bash
multi git push -u origin feature/my-feature
```

### Create and checkout a branch

```bash
multi git checkout -b hotfix/urgent-fix
```

### View recent commits

```bash
multi git log --oneline -5
```

### Stash changes

```bash
multi git stash
```

### Apply stashed changes

```bash
multi git stash pop
```

## Execution Order

1. The git command runs in the **root repository** first
2. Then it runs in each **sub-repository** in order

Output from each repository is displayed with the repository name as a header.

## Requirements

- All repositories must be on their expected branch before running git commands:
  - Unlocked repositories must match the root workspace branch
  - Repositories with `fixedBranch` in `multi.json` must be on that fixed branch
- This validation uses Multi's shared expected-branch invariant from `multi.git_helpers.expected_branch_for_repo`
- Working trees do **not** need to be clean — read-only queries like `multi git branch --show-current` or `multi git status` work with uncommitted changes

## Error Handling

If repositories are not on their expected branches, the command will fail with an error (even for read-only git commands). Use `multi branch` to inspect which branch every repo is on — it works with dirty trees and mismatched branches — then use `multi set-branch` to synchronize:

```bash
multi branch
multi set-branch main
multi git pull
```

## Fixed Branch Warning

`multi git` still runs the exact same git arguments in fixed-branch repositories. Commands that are branch-specific or branch-mutating, such as `checkout`, `branch`, or `push -u origin FEATURE`, can still affect fixed repos. Multi only validates the starting expected-branch state; it does not currently skip fixed repos or rewrite git arguments for them.

## Notes

- Any valid git command works with `multi git`
- The command passes arguments directly to git, so all git options are supported (for example `multi git branch --show-current`)
- Interactive git commands (like `git rebase -i`) are not supported
