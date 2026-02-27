# sync github

Sync GitHub Actions workflows from monorepo package directories to the root repository.

## Usage

```bash
multi sync github
```

## Description

The `sync github` command scans each repo directory listed in `multi.json` for workflow files:

- `<repo>/.github/workflows/*.yml`
- `<repo>/.github/workflows/*.yaml`

It generates corresponding files in the root repo at:

- `.github/workflows/`

This is intended for `monoRepo: true` workspaces so workflows are checked into the root repo and can run in GitHub Actions.

## Behavior

- Available only in monorepo mode (`monoRepo: true`)
- Injects `jobs.<job>.defaults.run.working-directory` when missing, pointing to the repo directory
- Preserves existing `working-directory` values
- Adds metadata comments to generated files
- Uses repo-prefixed filenames when source files collide (for example, `packages-web--ci.yml`)
- Cleans up stale generated workflow files while leaving non-generated root workflows untouched

## Examples

```bash
# Sync only root GitHub workflow files
multi sync github

# Full sync (includes github workflow sync)
multi sync
```
