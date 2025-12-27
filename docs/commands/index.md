# Commands Overview

Multi provides four commands for managing your multi-repo workspace.

## Available Commands

| Command | Description |
|---------|-------------|
| [`init`](init.md) | Initialize a new multi workspace |
| [`sync`](sync.md) | Sync configurations and repositories |
| [`set-branch`](set-branch.md) | Switch all repos to the same branch |
| [`git`](git.md) | Run git commands across all repos |

## Global Options

All commands support:

- `--version` - Show version and exit
- `--verbose` - Enable detailed logging output

## Command Structure

```bash
multi [OPTIONS] COMMAND [ARGS]
```

### Examples

```bash
# Initialize a new workspace
multi init

# Sync all configurations
multi sync

# Switch to a feature branch
multi set-branch feature/new-feature

# Pull latest changes in all repos
multi git pull

# Check status across all repos
multi git status
```

## Getting Help

Get help for any command:

```bash
multi --help
multi sync --help
multi sync vscode --help
```
