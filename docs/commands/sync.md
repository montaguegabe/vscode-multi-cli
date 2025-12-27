# sync

Sync development environment and configurations.

## Usage

```bash
multi sync [SUBCOMMAND]
```

## Description

The `sync` command ensures your workspace is up to date by cloning/updating repositories and merging configurations. Running `sync` without a subcommand performs a full sync.

## Full Sync

```bash
multi sync
```

A full sync performs all of the following:

1. Clones any missing repositories
2. Merges VS Code configurations (settings, launch, tasks, extensions)
3. Converts Cursor rules to `CLAUDE.md` files
4. Syncs ruff configurations

## Subcommands

| Subcommand | Description |
|------------|-------------|
| [sync vscode](sync-vscode.md) | Merge VS Code configuration files |
| [sync claude](sync-claude.md) | Convert Cursor rules to CLAUDE.md |
| [sync ruff](sync-ruff.md) | Copy ruff configuration to root |

## Examples

```bash
# Full sync (recommended)
multi sync

# Only sync VS Code configurations
multi sync vscode

# Only sync VS Code settings
multi sync vscode settings

# Only update CLAUDE.md files
multi sync claude
```

## Notes

- The VS Code extension can automatically run `multi sync` when relevant files change
- Sync operations are idempotent - running them multiple times is safe
- Use `--verbose` to see detailed output during sync
