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

1. Initializes root git repository if missing
2. Creates `README.md` if missing
3. Clones any missing repositories (standard mode only)
4. Merges VS Code configurations (settings, launch, tasks, extensions)
5. Syncs cursor rules (generates repo-directories.mdc from multi.json, converts to CLAUDE.md)
6. Syncs ruff configurations
7. Syncs GitHub Actions workflows to root `.github/workflows` (monorepo mode only)

## Subcommands

| Subcommand | Description |
|------------|-------------|
| [sync vscode](sync-vscode.md) | Merge VS Code configuration files |
| [sync rules](sync-rules.md) | Generate repo descriptions and convert Cursor rules to CLAUDE.md |
| [sync ruff](sync-ruff.md) | Copy ruff configuration to root |
| [sync github](sync-github.md) | Sync root GitHub Actions workflows for monorepo workspaces |

## Examples

```bash
# Full sync (recommended)
multi sync

# Only sync VS Code configurations
multi sync vscode

# Only sync VS Code settings
multi sync vscode settings

# Only sync cursor rules and CLAUDE.md files
multi sync rules

# Only sync root GitHub Actions workflow files (monorepo mode)
multi sync github
```

## Notes

- The VS Code extension can automatically run `multi sync` when relevant files change
- Sync operations are idempotent - running them multiple times is safe
- Use `--verbose` to see detailed output during sync
- `multi sync github` is available only when `monoRepo` is `true`
- Recommended automation path: create/edit `multi.json` and run `multi sync`
