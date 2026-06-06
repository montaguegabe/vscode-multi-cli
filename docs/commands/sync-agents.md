# sync agents

Generate `AGENTS.md` and `CLAUDE.md` from optional Markdown part files.

## Usage

```bash
multi sync agents
```

## Description

The `sync agents` command is disabled unless `agentInstructions.enabled` is set to `true` in `multi.json`.

When enabled, it concatenates tracked Markdown files from `AGENTS.parts/*.md` and writes matching `AGENTS.md` and `CLAUDE.md` files. Generated files are added to Multi-managed `.gitignore` blocks when generation applies.

## How It Works

1. Reads `agentInstructions` settings from `multi.json`.
2. Reads `AGENTS.parts/*.md` files in lexicographic order from the workspace root and each sub-repo.
3. Prepends root repository descriptions when `includeRepoDescriptions` is enabled.
4. Writes generated `AGENTS.md` and `CLAUDE.md` beside the source parts directory.

## Configuration

Agent generation is opt-in:

```json
{
  "agentInstructions": {
    "enabled": true,
    "partsDir": "AGENTS.parts",
    "includeRepoDescriptions": true
  },
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

Descriptions remain stored in `multi.json` and can be included in the root generated files.

## Example

Given this structure:

```
my-workspace/
├── AGENTS.parts/
│   ├── 10-project-context.md
│   └── 20-workflow.md
├── api-repo/
│   └── AGENTS.parts/
│       └── api-guidelines.md
└── web-repo/
    └── AGENTS.parts/
        └── frontend.md
```

Running `multi sync agents` generates:

```
my-workspace/
├── CLAUDE.md                     # Generated from root AGENTS.parts
├── AGENTS.md                     # Generated from root AGENTS.parts
├── api-repo/
│   ├── CLAUDE.md                 # Generated from api-repo/AGENTS.parts
│   └── AGENTS.md                 # Generated from api-repo/AGENTS.parts
└── web-repo/
    ├── CLAUDE.md                 # Generated from web-repo/AGENTS.parts
    └── AGENTS.md                 # Generated from web-repo/AGENTS.parts
```

## Why Use This?

- **Composable instructions**: Split large agent guidance into ordered, focused files
- **Tool compatibility**: Generate both `AGENTS.md` and `CLAUDE.md`
- **Team consistency**: Share AI context across different tools
- **Repository documentation**: Reuse repo descriptions from `multi.json`

## Notes

- The VS Code extension automatically runs this when `AGENTS.parts/*.md` files change
- Existing `CLAUDE.md` and `AGENTS.md` files are overwritten only when generation is enabled and source content exists
- If `agentInstructions.enabled` is false, Multi leaves manual `CLAUDE.md` and `AGENTS.md` files alone
