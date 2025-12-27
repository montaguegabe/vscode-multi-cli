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

- Generates files in your root `.vscode` folder when sub-repo configurations change
- Generates `CLAUDE.md` files when Cursor rules change

## Watched Files

The extension monitors these files in your sub-repositories:

| File | Triggers |
|------|----------|
| `.vscode/launch.json` | `multi sync vscode launch` |
| `.vscode/settings.json` | `multi sync vscode settings` |
| `.vscode/tasks.json` | `multi sync vscode tasks` |
| `.vscode/extensions.json` | `multi sync vscode extensions` |
| `.cursor/rules/*` | `multi sync claude` |

## Usage

The extension activates automatically when VS Code starts. Simply edit any of the watched config files in a sub-repository and the appropriate sync will run in the background.

No manual intervention is required - changes are detected and synced automatically.
