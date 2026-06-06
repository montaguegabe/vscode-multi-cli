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
5. Generates agent instruction files when `agentInstructions.enabled` is true
6. Syncs GitHub Actions workflows to root `.github/workflows` (monorepo mode only)

## Subcommands

| Subcommand | Description |
|------------|-------------|
| [sync vscode](sync-vscode.md) | Merge VS Code configuration files |
| [sync agents](sync-agents.md) | Generate AGENTS.md and CLAUDE.md from AGENTS.parts/*.md |
| [sync github](sync-github.md) | Sync root GitHub Actions workflows for monorepo workspaces |

## Examples

```bash
# Full sync (recommended)
multi sync

# Only sync VS Code configurations
multi sync vscode

# Only sync VS Code settings
multi sync vscode settings

# Only sync generated agent instruction files
multi sync agents

# Only sync root GitHub Actions workflow files (monorepo mode)
multi sync github
```

## Notes

- The VS Code extension can automatically run `multi sync` when relevant files change
- Sync operations are idempotent - running them multiple times is safe
- Use `--verbose` to see detailed output during sync
- `multi sync github` is available only when `monoRepo` is `true`
- Recommended automation path: create/edit `multi.json` and run `multi sync`
