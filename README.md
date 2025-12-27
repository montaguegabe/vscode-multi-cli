# multi

`multi` is the best way to work with VS Code/Cursor on multiple Git repos at once. It is an alternative to [multi-root workspaces](https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces) that offers more flexibility and control. With `multi`, you can gain control over how tasks, debug runnables, and various IDE and linter settings are combined from multiple project repos ("sub-repos") located in the same folder.

Features:

- Generates files in your root `.vscode` folder from sub-repo `launch.json`, `tasks.json`, and `settings.json` files.
- Generates `CLAUDE.md` files from Cursor rules.

## Installation

### Using `pipx`:

- Install [pipx](https://github.com/pypa/pipx)
- Run `pipx install multi-workspace`

### Using `uv`

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv tool install multi-workspace`

## Getting started

To get started, create a new workspace directory that will house all your related repos and run:

```
multi init
```

When prompted, paste in the URLs of all the repositories you want to have in your workspace. You can optionally specify descriptions of what they do, which will be used to create a new repo-directories.mdc Cursor/Claude rule.

It is recommended you also install the [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=montaguegabe.multi-sync) that automatically keeps your project synced when edits are made to synced files. To manually sync, you can run `multi sync`.
