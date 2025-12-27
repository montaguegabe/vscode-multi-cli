# init

Initialize a new multi workspace.

## Usage

```bash
multi init
```

## Description

The `init` command sets up a new multi workspace in the current directory. It guides you through an interactive process to configure your workspace.

## Interactive Process

When you run `multi init`, you'll be prompted to:

1. **Enter repository URLs** - Paste the Git URLs of repositories you want to include
2. **Add descriptions (optional)** - Provide descriptions for each repository to generate Cursor rules

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

## Generated Files

The init command creates several files in your workspace:

### multi.json

The main configuration file containing repository URLs and settings:

```json
{
  "repos": [
    { "url": "https://github.com/org/api-server" },
    { "url": "https://github.com/org/web-client" },
    { "url": "https://github.com/org/common" }
  ]
}
```

### README.md

A basic README for your workspace (only created if one doesn't exist).

### .cursor/rules/repo-directories.mdc

If you provided repository descriptions, a Cursor rule file is created to help AI assistants understand your project structure.

### .vscode/

Merged VS Code configuration from all sub-repositories.

## Notes

- Run this command in an empty directory or an existing Git repository
- If the directory is not a Git repository, one will be initialized
- The command performs an initial sync after setup
- All changes are committed automatically
