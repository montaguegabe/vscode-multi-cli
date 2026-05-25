# Multi

**Multi** is the best way to work with VS Code/Cursor on multiple Git repos at once. It is an alternative to [multi-root workspaces](https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces) that offers more flexibility and control.

## Why Multi?

When working on projects that span multiple repositories, VS Code's multi-root workspaces can be limiting. Multi provides:

- **Unified branch management** - Keep all your repos on the same branch with a single command
- **Configuration merging** - Automatically combine `.vscode` settings, launch configurations, and tasks from all repos
- **AI assistant support** - Generate `repo-directories.mdc`, `CLAUDE.md`, and `AGENTS.md` from `multi.json` descriptions and Cursor rules
- **Flexible structure** - Sub-repos are simply cloned into your workspace directory, no submodules required
- **Workspace diagnostics** - Detect common misconfigurations with `multi doctor`

## Key Features

### Branch Synchronization

Switch all repositories to the same branch simultaneously:

```bash
multi set-branch feature/my-feature
```

Create a sibling worktree for parallel branch work:

```bash
multi worktree add my-feature --branch feature/my-feature
```

### VS Code Configuration Merging

Merge `launch.json`, `tasks.json`, `settings.json`, and `extensions.json` from all sub-repos into your root `.vscode` folder:

```bash
multi sync vscode
```

### Cursor Rules Sync

Generate repo descriptions from `multi.json` and convert Cursor rules to `CLAUDE.md` files:

```bash
multi sync rules
```

### Monorepo GitHub Workflow Sync

In `monoRepo` mode, sync package workflows into root `.github/workflows`:

```bash
multi sync github
```

### Workspace Diagnostics

Catch mode mismatches and setup issues early:

```bash
multi doctor
```

### Cross-Repo Git Commands

Run git commands across all repositories:

```bash
multi git pull
multi git status
```

## Quick Start

Get started in minutes:

1. Install Multi: `pipx install multi-workspace`
2. Create a workspace directory and run: `multi init`
3. Add your repository URLs and optional descriptions when prompted, or pass `--repo` / `--repo-description` for non-interactive setup
4. Install the [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=montaguegabe.multi-workspace) for automatic syncing

See the [Getting Started](getting-started.md) guide for detailed instructions.
