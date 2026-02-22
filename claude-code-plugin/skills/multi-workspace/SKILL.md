---
name: Multi Workspace
description: >-
  This skill should be used when the user asks about "multi.json",
  "multi workspace", "multi sync", "multi set-branch", "multi git",
  "multi init", branch switching across repos, VS Code config merging,
  Cursor rules sync, "CLAUDE.md" generation, "AGENTS.md" generation,
  working with multiple repositories in a single workspace, or when a
  multi.json file is detected in the project. Provides knowledge of
  Multi CLI commands, configuration, and workspace conventions.
version: 0.1.0
---

# Multi Workspace

Multi (`multi-workspace` on PyPI) is a CLI tool that enables VS Code/Cursor to work across multiple Git repos in a single workspace. Sub-repos are cloned as directories inside the workspace root and `.gitignored` — no submodules are used. The CLI keeps all repos on the same branch and merges their VS Code configurations.

## Key Constraints

- `multi init` is **interactive** and cannot be scripted non-interactively.
- `CLAUDE.md` and `AGENTS.md` are **auto-generated** from `.cursor/rules/*.mdc` files. Never edit them directly.
- All repos must have **clean working directories** before running `multi set-branch`.
- `multi set-branch` and `multi git` are **disabled in monorepo mode**.
- VS Code config files (`settings.json`, `launch.json`, `tasks.json`, `extensions.json`) at the workspace root are **generated** — do not edit directly. Use the repo-level files or `*.shared.json` files instead.

## Commands

### `multi sync`

Run all sync operations: clone/symlink repos, update `.gitignore`, merge VS Code configs, sync Cursor rules, sync ruff config.

Subcommands for partial sync:
- `multi sync vscode` — merge all VS Code configs (or specify: `settings`, `launch`, `tasks`, `extensions`, `devcontainer`)
- `multi sync rules` — generate `CLAUDE.md`/`AGENTS.md` from Cursor rules and create `repo-directories.mdc` from repo descriptions
- `multi sync ruff` — copy ruff config from a sub-repo to workspace root

### `multi set-branch BRANCH_NAME`

Switch all repos to a branch. If the branch exists locally or on the remote, check it out. If it doesn't exist anywhere, create it from the current HEAD. All repos must be clean first.

### `multi git GIT_ARGS...`

Run any git command across all repos (root first, then sub-repos in order). All repos must be on the same branch. Example: `multi git pull`, `multi git push -u origin feature/foo`.

### `multi init`

Interactive setup: prompts for repo URLs and descriptions, writes `multi.json`, clones repos, runs full sync, commits.

### `multi open PATH`

Open a project path in the Multi desktop app.

## Configuration Overview

The workspace is configured via `multi.json` at the root. Key fields:

- `repos[]` — array of repo configs, each with `url`, optional `name`, `description`, `skipVSCode`, `allowSymlink`, `requiredTasks`, `requiredCompounds`, `requiredLaunchConfigurations`
- `monoRepo` — treat repos as local subdirectories instead of cloning
- `allowSymlinks` — enable symlinking to existing clones from `~/.multi/repos.json`
- `vscode.skipSettings` — settings keys to exclude from merge

For the full schema, consult `references/configuration.md`.

## VS Code Merging Overview

Multi merges `.vscode/` config files from all sub-repos into the workspace root:

- **`${workspaceFolder}` rewriting** — paths are automatically prefixed with the repo name
- **`*.shared.json` files** — `settings.shared.json`, `launch.shared.json`, `tasks.shared.json` at workspace root are merged last (for cross-repo config)
- **Master compound** — auto-created launch compound and task containing all "required" entries
- **Settings overrides** — per-repo `vscode.settingsOverrides` in `multi.json`

For detailed merging behavior, consult `references/vscode-sync.md`.

## CLAUDE.md / AGENTS.md Generation

Running `multi sync rules`:
1. Generates `.cursor/rules/repo-directories.mdc` from repo `description` fields in `multi.json`.
2. For each directory containing `.cursor/rules/*.mdc`, concatenates all rule bodies into `CLAUDE.md` and `AGENTS.md` placed alongside the `.cursor` directory.
3. If no rules exist, removes existing `CLAUDE.md`/`AGENTS.md`.

## Common Tasks

**Add a new repo to the workspace**: Add a `url` entry (and optional `name`/`description`) to the `repos` array in `multi.json`, then run `multi sync`.

**Switch all repos to a feature branch**: Run `multi set-branch feature/my-branch`. Ensure all repos are clean first.

**Fix a missing launch config**: Check the source repo's `.vscode/launch.json`. Ensure `skipVSCode` is not `true` for that repo. Run `multi sync vscode launch`. For cross-repo compounds, use `.vscode/launch.shared.json` at workspace root.

**Add cross-repo settings**: Create or edit `.vscode/settings.shared.json` at the workspace root, then run `multi sync vscode settings`.

## Additional Resources

### Reference Files

For detailed information, consult:
- **`references/configuration.md`** — full `multi.json` schema with all fields and defaults
- **`references/vscode-sync.md`** — detailed VS Code merging behavior, `*.shared.json` usage, master compound creation
- **`references/commands.md`** — complete command reference with all options and edge cases
