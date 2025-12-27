# sync claude

Convert Cursor rule files to `CLAUDE.md` files.

## Usage

```bash
multi sync claude
```

## Description

The `sync claude` command converts Cursor rule files (`.cursor/rules/*.mdc`) into `CLAUDE.md` files. This allows AI assistants that read `CLAUDE.md` files (like Claude Code) to benefit from the context you've defined in your Cursor rules.

## How It Works

1. Scans the root directory and all sub-repos for `.cursor/rules/*.mdc` files
2. Parses the Cursor rule format (MDC)
3. Generates a `CLAUDE.md` file alongside each `.cursor` directory

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

Running `multi sync claude` generates:

```
my-workspace/
├── .cursor/
│   └── rules/
│       └── project-context.mdc
├── CLAUDE.md                    # Generated from project-context.mdc
├── api-repo/
│   ├── .cursor/
│   │   └── rules/
│   │       └── api-guidelines.mdc
│   └── CLAUDE.md                # Generated from api-guidelines.mdc
└── web-repo/
    ├── .cursor/
    │   └── rules/
    │       └── frontend-rules.mdc
    └── CLAUDE.md                # Generated from frontend-rules.mdc
```

## Why Use This?

- **Cursor users**: Define your AI context once in Cursor rules
- **Claude Code users**: Automatically get the same context in Claude Code
- **Team consistency**: Share AI context across different tools

## Notes

- The VS Code extension automatically runs this when `.cursor/rules/*` files change
- Existing `CLAUDE.md` files are overwritten - don't manually edit generated files
- If you want manual control over `CLAUDE.md`, don't create `.cursor/rules/` files
