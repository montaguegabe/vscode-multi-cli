# Commands Overview

Multi provides commands for managing your multi-repo workspace.

## Available Commands

| Command | Description |
|---------|-------------|
| [`add`](add.md) | Add a repository to an existing workspace |
| [`collaborator`](collaborator.md) | Add or remove a GitHub collaborator across all workspace repos |
| [`init`](init.md) | Initialize a new multi workspace |
| [`sync`](sync.md) | Sync configurations and repositories |
| [`sync github`](sync-github.md) | Sync root GitHub Actions workflows (monorepo mode) |
| [`set-branch`](set-branch.md) | Switch all repos to the same branch |
| [`git`](git.md) | Run git commands across all repos |
| [`doctor`](doctor.md) | Diagnose common workspace configuration issues |

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

# Add another repo to the workspace
multi add https://github.com/org/t-ide-cli

# Add a collaborator to every workspace repo
multi collaborator add octocat --yes

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
