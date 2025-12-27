# sync ruff

Copy ruff configuration from sub-repos to the root.

## Usage

```bash
multi sync ruff
```

## Description

The `sync ruff` command searches all sub-repositories for `ruff.toml` files and copies them to the root directory. This is useful for maintaining consistent Python linting configuration across your workspace.

## How It Works

1. Scans all sub-repositories for `ruff.toml` files
2. Copies found configurations to the root workspace directory

## Why Use This?

[Ruff](https://docs.astral.sh/ruff/) is a fast Python linter and formatter. When working with multiple Python repositories, you often want consistent linting rules across all of them.

By syncing ruff configuration to the root:

- VS Code's Ruff extension can find the configuration
- Running `ruff check` from the root uses consistent settings
- All sub-repos share the same linting standards

## Example

Given this structure:

```
my-workspace/
├── api-repo/
│   ├── ruff.toml
│   └── src/
└── shared-lib/
    ├── ruff.toml
    └── src/
```

Running `multi sync ruff` copies the configuration:

```
my-workspace/
├── ruff.toml          # Copied from a sub-repo
├── api-repo/
│   ├── ruff.toml
│   └── src/
└── shared-lib/
    ├── ruff.toml
    └── src/
```

## Notes

- If multiple sub-repos have `ruff.toml`, one will be chosen (order not guaranteed)
- For consistent results, ensure your sub-repos use the same ruff configuration
- This command only syncs `ruff.toml`, not `pyproject.toml` ruff sections
