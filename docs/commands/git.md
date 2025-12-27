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

- All repositories must be on the same branch before running git commands
- This validation ensures consistency across your workspace

## Error Handling

If repositories are on different branches, the command will fail with an error. Use `multi set-branch` to synchronize branches first:

```bash
multi set-branch main
multi git pull
```

## Notes

- Any valid git command works with `multi git`
- The command passes arguments directly to git, so all git options are supported
- Interactive git commands (like `git rebase -i`) are not supported
