# worktree add

Create a sibling Git worktree for a multi workspace.

## Usage

```bash
multi worktree add NAME [--branch BRANCH]
```

## Description

The `worktree add` command creates a Git worktree next to the current workspace root. It then runs `multi sync` in the new worktree, checks sub-repos out to the worktree branch, and transfers configured gitignored local paths from the original workspace.

If `--branch` is omitted, `NAME` is used as the branch name.

## Arguments

| Argument | Description |
|----------|-------------|
| `NAME` | Sibling directory name for the new worktree |

## Options

| Option | Description |
|--------|-------------|
| `--branch BRANCH` | Branch name for the worktree. Defaults to `NAME` |

## Behavior

1. Checks that the root repo and sub-repos are clean.
2. Creates a sibling root worktree on the target branch.
3. Runs `multi sync` in the new worktree to populate sub-repos and generated config.
4. Checks sub-repos out to the target branch, except repos with `fixedBranch`.
5. Symlinks or copies configured gitignored paths from the original workspace.

## Examples

### Use the worktree name as the branch

```bash
multi worktree add feature-user-auth
```

### Use a custom branch name

```bash
multi worktree add user-auth --branch feature/user-auth
```

### Transfer ignored local files

```json
{
  "worktree": {
    "symlink": [".env", ".venv"],
    "copy": [".cursor/local.json"]
  },
  "repos": [
    {
      "url": "https://github.com/org/shared",
      "fixedBranch": "main"
    }
  ]
}
```

## Requirements

- The command is not available in `monoRepo` mode.
- The destination sibling directory must not already exist.
- Transfer paths must be relative, gitignored, and inside the workspace.
- Existing transfer destinations are skipped.
