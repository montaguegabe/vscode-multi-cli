# Getting Started

This guide will help you install Multi and set up your first multi-repo workspace.

## Prerequisites

- Python 3.9 or higher
- Git

## Installation

### Desktop App

On Apple Silicon Macs, you can also install
[Multi Desktop](https://multi-desktop-releases-632795836081-us-east-1.s3.amazonaws.com/mac/Multi-Desktop-latest-arm64.dmg)
to inspect and manage Multi workspaces from a native app.

For terminal-only setup, install the Multi CLI with one of the package managers
below.

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

Run the interactive init command:

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
2. Run `multi sync`
3. Clone repositories (standard mode)
4. Set up the initial `.vscode` configuration
5. Create a `README.md` for your workspace if missing
6. Save optional repository descriptions for generated agent instructions

## Automation Path

For scripts/automation, you can initialize directly from the command line:

```bash
multi init \
  --repo https://github.com/org/backend \
  --repo-description "Backend API service" \
  --repo https://github.com/org/frontend \
  --repo-description "React frontend application"
```

If you want `multi init` to create the GitHub repositories first, use `--github-repo`. This shells out to `gh repo create`, requires `gh` to be installed and authenticated, and defaults to private repositories:

```bash
multi init \
  --github-repo org/backend \
  --github-description "Backend API service" \
  --github-repo org/frontend \
  --github-description "React frontend application"
```

You can override the defaults with `--github-visibility public|private|internal` and choose the URL format written to `multi.json` with `--github-clone-protocol https|ssh`.

You can still hand-author `multi.json` and run:

```bash
multi sync
```

`multi init` automatically uses short local repo names when the remote slug starts with the workspace directory name. Example: in a `t-ide/` workspace, `https://github.com/org/t-ide-cli` becomes local folder `cli`. If you hand-author `multi.json`, keep using that same convention.

The same convention applies when you later run `multi add`.

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
- Generates agent instruction files from `AGENTS.parts/*.md` when enabled

## Next Steps

- Learn about all [available commands](commands/index.md)
- Understand the [configuration format](configuration.md)
- Set up [branch synchronization](commands/set-branch.md) for your workflow
