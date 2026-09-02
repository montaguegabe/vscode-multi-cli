# Multi

**Multi** is the best way to work with VS Code/Cursor on multiple Git repos at once. It is an alternative to [multi-root workspaces](https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces) that offers more flexibility and control.

## Why Multi?

When working on projects that span multiple repositories, VS Code's multi-root workspaces can be limiting. Multi provides:

- **Unified branch management** - Keep repos on their expected branches with a single command
- **Configuration merging** - Automatically combine `.vscode` settings, launch configurations, and tasks from all repos
- **AI assistant support** - Optionally generate `CLAUDE.md` and `AGENTS.md` from tracked Markdown part files
- **Flexible structure** - Sub-repos are simply cloned into your workspace directory, no submodules required
- **Workspace diagnostics** - Detect common misconfigurations with `multi doctor`

## Key Features

### Desktop App

Use the desktop app to inspect configured Multi workspaces, review cross-repo diffs, and keep track of repository status.

- [Download for macOS Apple Silicon](https://multi-desktop-releases-632795836081-us-east-1.s3.amazonaws.com/mac/Multi-Desktop-latest-arm64.dmg)
- [Download for macOS Intel](https://multi-desktop-releases-632795836081-us-east-1.s3.amazonaws.com/mac/Multi-Desktop-latest-x64.dmg)

### Branch Synchronization

Switch repositories to the same workspace branch, except repos configured with `fixedBranch`:

```bash
multi set-branch feature/my-feature
```

Check expected branch alignment — read-only, so it works with dirty working trees and detached HEADs:

```bash
multi branch check
```

Create an isolated worktree (in a sibling `<workspace>-worktrees` directory) for parallel branch work:

```bash
multi worktree add my-feature --branch feature/my-feature
```

### VS Code Configuration Merging

Merge `launch.json`, `tasks.json`, `settings.json`, and `extensions.json` from all sub-repos into your root `.vscode` folder:

```bash
multi sync vscode
```

### Agent Instructions Sync

Generate agent instruction files from `AGENTS.parts/*.md` when enabled:

```bash
multi sync agents
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
