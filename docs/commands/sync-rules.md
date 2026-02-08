# sync rules

Sync cursor rules: generate repo descriptions and convert to `CLAUDE.md` files.

## Usage

```bash
multi sync rules
```

## Description

The `sync rules` command:

1. **Generates `repo-directories.mdc`** from repository descriptions in `multi.json`
2. **Converts Cursor rules to `CLAUDE.md`** files for all repositories

This allows AI assistants that read `CLAUDE.md` files (like Claude Code) to benefit from the context you've defined in your Cursor rules.

## How It Works

1. Reads repository descriptions from `multi.json` and generates `.cursor/rules/repo-directories.mdc`
2. Scans the root directory and all sub-repos for `.cursor/rules/*.mdc` files
3. Parses the Cursor rule format (MDC)
4. Generates a `CLAUDE.md` file alongside each `.cursor` directory

## Repository Descriptions

When you run `multi init`, you can optionally provide descriptions for each repository. These are saved to `multi.json`:

```json
{
  "repos": [
    {
      "url": "https://github.com/user/api-repo",
      "description": "Django REST API with authentication and data models"
    },
    {
      "url": "https://github.com/user/web-repo",
      "description": "React frontend application"
    }
  ]
}
```

Running `multi sync rules` generates `.cursor/rules/repo-directories.mdc`:

```
---
description: Repository structure documentation
globs:
alwaysApply: false
---
This workspace contains multiple repositories:

- `api-repo`: Django REST API with authentication and data models
- `web-repo`: React frontend application
```

## Example

Given this structure:

```
my-workspace/
├── .cursor/
│   └── rules/
│       └── project-context.mdc
├── api-repo/
│   └── .cursor/
│       └── rules/
│           └── api-guidelines.mdc
└── web-repo/
    └── .cursor/
        └── rules/
            └── frontend-rules.mdc
```

Running `multi sync rules` generates:

```
my-workspace/
├── .cursor/
│   └── rules/
│       ├── project-context.mdc
│       └── repo-directories.mdc  # Generated from multi.json descriptions
├── CLAUDE.md                     # Generated from all root cursor rules
├── api-repo/
│   ├── .cursor/
│   │   └── rules/
│   │       └── api-guidelines.mdc
│   └── CLAUDE.md                 # Generated from api-guidelines.mdc
└── web-repo/
    ├── .cursor/
    │   └── rules/
    │       └── frontend-rules.mdc
    └── CLAUDE.md                 # Generated from frontend-rules.mdc
```

## Why Use This?

- **Cursor users**: Define your AI context once in Cursor rules
- **Claude Code users**: Automatically get the same context in Claude Code
- **Team consistency**: Share AI context across different tools
- **Repository documentation**: Keep descriptions in `multi.json` and auto-generate cursor rules

## Notes

- The VS Code extension automatically runs this when `.cursor/rules/*` files change
- Existing `CLAUDE.md` files are overwritten - don't manually edit generated files
- The `repo-directories.mdc` file is regenerated from `multi.json` on each sync
- If you want manual control over `CLAUDE.md`, don't create `.cursor/rules/` files
