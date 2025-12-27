# set-branch

Create and switch to a branch in all repositories.

## Usage

```bash
multi set-branch BRANCH_NAME
```

## Description

The `set-branch` command ensures all repositories in your workspace are on the same branch. It creates the branch if it doesn't exist in a repository, or switches to it if it does.

## Arguments

| Argument | Description |
|----------|-------------|
| `BRANCH_NAME` | The name of the branch to switch to |

## Behavior

1. **Validates clean state** - Checks that all repositories have no uncommitted changes
2. **Creates or switches** - For each repository (root and sub-repos):
   - If the branch exists, switches to it
   - If the branch doesn't exist, creates it and switches to it
3. **Maintains consistency** - Ensures all repos end up on the specified branch

## Examples

### Create and switch to a feature branch

```bash
multi set-branch feature/user-authentication
```

### Switch to an existing branch

```bash
multi set-branch main
```

### Switch to a release branch

```bash
multi set-branch release/v2.0
```

## Requirements

- All repositories must have a clean working directory (no uncommitted changes)
- Git must be available in your PATH

## Error Handling

If any repository has uncommitted changes, the command will fail with an error message indicating which repository is not clean. Commit or stash your changes before running `set-branch`.

```bash
# If you have uncommitted changes
git stash  # or commit your changes
multi set-branch feature/new-branch
git stash pop  # if you stashed
```

## Notes

- This command operates on both the root repository (if it exists) and all sub-repositories
- Branch creation is done locally; use `multi git push -u origin BRANCH_NAME` to push to remote
- The command is idempotent - running it when already on the branch is safe
