# Getting Started

This guide will help you install Multi and set up your first multi-repo workspace.

## Prerequisites

- Python 3.9 or higher
- Git

## Installation

=== "pipx"

    [pipx](https://github.com/pypa/pipx) installs Python CLI tools in isolated environments:

    ```bash
    pipx install multi-workspace
    ```

=== "uv"

    [uv](https://docs.astral.sh/uv/) is a fast Python package installer:

    ```bash
    uv tool install multi-workspace
    ```

=== "pip"

    ```bash
    pip install multi-workspace
    ```

Verify the installation:

```bash
multi --version
```

## Creating a Workspace

### Step 1: Create a Workspace Directory

Create a new directory that will house all your related repositories:

```bash
mkdir my-workspace
cd my-workspace
```

### Step 2: Initialize the Workspace

Run the init command:

```bash
multi init
```

### Step 3: Add Repository URLs

When prompted, paste the URLs of the repositories you want to include. You can optionally add descriptions for each repository:

```
Enter repository URLs (one per line, empty line to finish):
> https://github.com/org/backend
Description (optional): Backend API service
> https://github.com/org/frontend
Description (optional): React frontend application
> https://github.com/org/shared
Description (optional): Shared utilities and types
>
```

The init command will:

1. Create a `multi.json` configuration file
2. Clone all repositories
3. Set up the initial `.vscode` configuration
4. Create a `README.md` for your workspace
5. Optionally create Cursor rules with repository descriptions

## VS Code Extension

For the best experience, install the [Multi Workspace VS Code Extension](https://marketplace.visualstudio.com/items?itemName=montaguegabe.multi-workspace). The extension automatically runs `multi sync` when relevant files change, keeping your workspace configuration up to date.

## Manual Syncing

If you prefer not to use the extension, you can manually sync your workspace:

```bash
multi sync
```

This command:

- Ensures all repositories are cloned and up to date
- Merges `.vscode` configurations from all sub-repos
- Generates `CLAUDE.md` files from Cursor rules
- Syncs ruff configurations

## Next Steps

- Learn about all [available commands](commands/index.md)
- Understand the [configuration format](configuration.md)
- Set up [branch synchronization](commands/set-branch.md) for your workflow
