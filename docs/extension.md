# VS Code Extension

The Multi VS Code Extension automatically keeps your workspace synced when you edit configuration files. Instead of manually running `multi sync`, the extension detects changes and runs the appropriate sync in the background.

[Install from VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=montaguegabe.multi-workspace){ .md-button }

## Requirements

- **Multi CLI** must be installed and accessible via the `multi` command
- **VS Code** version 1.99.0 or higher

To verify the CLI is available:

```bash
multi --version
```

## Features

The extension automatically syncs when changes are detected:

- Runs the matching `multi sync ...` command when watched source files change
- Regenerates root `.vscode` outputs from repo config files and workspace-level shared files
- Runs optional agent instruction sync when `AGENTS.parts/*.md` files change; the CLI generates `CLAUDE.md` and `AGENTS.md` only when `agentInstructions.enabled` is `true`
- Syncs root `.github/workflows` files from repo workflows in monorepo mode

## Watched Files

The extension monitors these source files across your workspace and sub-repositories:

| File | Triggers |
|------|----------|
| `.vscode/launch.json` | `multi sync vscode launch` |
| `.vscode/launch.shared.json` | `multi sync vscode launch` |
| `.vscode/settings.json` | `multi sync vscode settings` |
| `.vscode/settings.shared.json` | `multi sync vscode settings` |
| `.vscode/settings.local.json` | `multi sync vscode settings` |
| `.vscode/tasks.json` | `multi sync vscode tasks` |
| `.vscode/tasks.shared.json` | `multi sync vscode tasks` |
| `.vscode/extensions.json` | `multi sync vscode extensions` |
| `AGENTS.parts/*.md` | `multi sync agents` |
| `.github/workflows/*.{yml,yaml}` | `multi sync github` |
| `multi.json` | `multi sync` |

## Usage

The extension activates automatically when VS Code starts. Simply edit any of the watched source files in your workspace or a sub-repository and the appropriate sync will run in the background.

Generated outputs like root `.vscode/settings.json`, root `.devcontainer/`, and root `.github/workflows/` are ignored so the extension does not loop on its own writes.

No manual intervention is required - changes are detected and synced automatically.
