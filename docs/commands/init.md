# init

Initialize a new multi workspace.

## Usage

```bash
multi init
multi init --repo https://github.com/org/api-server --repo-description "REST API backend"
multi init --github-repo org/api-server --github-description "REST API backend"
```

## Description

The `init` command sets up a new multi workspace in the current directory. By default it guides you through an interactive process, but it can also run non-interactively from flags.

When `--github-repo` is used, `multi init` creates the GitHub repositories first via `gh repo create`, then writes their resulting clone URLs into `multi.json`.

When a repository slug starts with the workspace directory name plus `-`, `multi init` automatically writes a short local `name` into `multi.json`. For example, in a workspace named `t-ide`, `https://github.com/org/t-ide-cli` becomes local folder `cli`.

## Options

- `--repo URL` — add an existing repository URL to the workspace. Repeat for multiple repos.
- `--repo-description TEXT` — description for the corresponding `--repo`. Repeat in the same order.
- `--github-repo OWNER/REPO` — create a GitHub repository with `gh repo create` and add it to the workspace.
- `--github-description TEXT` — description for the corresponding `--github-repo`. Also passed to GitHub when creating the repo.
- `--github-visibility private|public|internal` — visibility used for every `--github-repo`. Defaults to `private`.
- `--github-clone-protocol https|ssh` — URL format written to `multi.json` for created GitHub repos. Defaults to `https`.

## Interactive Process

When you run `multi init` with no repo flags, you'll be prompted to:

1. **Enter repository URLs** - Paste the Git URLs of repositories you want to include
2. **Add descriptions (optional)** - Provide descriptions for each repository (saved to `multi.json`)

### Example Session

```
$ multi init
Enter repository URLs (one per line, empty line to finish):
> https://github.com/org/api-server
Description (optional): REST API backend built with FastAPI
> https://github.com/org/web-client
Description (optional): React frontend application
> https://github.com/org/common
Description (optional): Shared types and utilities
>

Initializing workspace...
✓ Created multi.json
✓ Cloned api-server
✓ Cloned web-client
✓ Cloned common
✓ Created .vscode configuration
✓ Created README.md
✓ Created repo-directories.mdc Cursor rule
Done!
```

## Non-Interactive Examples

Create a workspace from existing repositories:

```bash
multi init \
  --repo https://github.com/org/api-server \
  --repo-description "REST API backend built with FastAPI" \
  --repo https://github.com/org/web-client \
  --repo-description "React frontend application"
```

Create private GitHub repositories first, then initialize the workspace:

```bash
multi init \
  --github-repo org/api-server \
  --github-description "REST API backend built with FastAPI" \
  --github-repo org/web-client \
  --github-description "React frontend application"
```

Write SSH clone URLs to `multi.json` for the created repos:

```bash
multi init \
  --github-repo org/api-server \
  --github-clone-protocol ssh
```

## Generated Files

The init command creates several files in your workspace:

### multi.json

The main configuration file containing repository URLs, descriptions, and settings:

```json
{
  "repos": [
    {
      "url": "https://github.com/org/api-server",
      "description": "REST API backend built with FastAPI"
    },
    {
      "url": "https://github.com/org/web-client",
      "description": "React frontend application"
    },
    {
      "url": "https://github.com/org/common",
      "description": "Shared types and utilities"
    }
  ]
}
```

### README.md

A basic README for your workspace (only created if one doesn't exist).

### .cursor/rules/repo-directories.mdc

If you provided repository descriptions, a Cursor rule file is generated during sync (from the descriptions in `multi.json`) to help AI assistants understand your project structure.

### .vscode/

Merged VS Code configuration from all sub-repositories.

## Notes

- Run this command in an empty directory or an existing Git repository
- Root git repo and README creation are handled during sync
- The command performs an initial sync after setup
- All changes are committed automatically
- `--repo-description` must be repeated once per `--repo`
- `--github-description` must be repeated once per `--github-repo`
- `--github-repo` requires the GitHub CLI (`gh`) to be installed and authenticated
- `--github-repo` must use `OWNER/REPO` format so `multi` can write the created remote URL to `multi.json`
- Product-prefixed repo slugs are automatically shortened to local folder names when they match the workspace name prefix, e.g. `t-ide-cli` -> `cli` inside a `t-ide/` workspace
