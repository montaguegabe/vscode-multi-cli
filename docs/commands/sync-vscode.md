# sync vscode

Merge VS Code configuration files from all sub-repos into the root `.vscode` folder.

## Usage

```bash
multi sync vscode [SUBCOMMAND]
```

## Description

The `sync vscode` command merges VS Code configuration files from all sub-repositories into your workspace's root `.vscode` folder. This allows you to have unified debug configurations, tasks, settings, and extension recommendations across all your repos.

Running `sync vscode` without a subcommand merges all configuration files.

## Subcommands

### sync vscode settings

```bash
multi sync vscode settings
```

Merges `settings.json` from all repositories into the root `.vscode/settings.json`.

**Behavior:**

- Settings from sub-repos are combined with root settings
- Later repos override earlier ones for conflicting keys
- Use the `skipSettings` configuration option to exclude specific settings keys from being merged

**Example:** If `repo-a` has `"editor.tabSize": 2` and `repo-b` has `"editor.tabSize": 4`, the merged result will use `4` (from the later repo).

---

### sync vscode launch

```bash
multi sync vscode launch
```

Merges `launch.json` from all repositories into the root `.vscode/launch.json`.

**Behavior:**

- Launch configurations are prefixed with the repository name to avoid conflicts
- A configuration named "Debug Server" in `api-repo` becomes "api-repo: Debug Server"
- All configurations from all repos are available in the unified launch menu

---

### sync vscode tasks

```bash
multi sync vscode tasks
```

Merges `tasks.json` from all repositories into the root `.vscode/tasks.json`.

**Behavior:**

- Tasks are prefixed with the repository name
- Creates a master compound task that runs all tasks marked as "required" in parallel
- Useful for running build tasks across all repos simultaneously

---

### sync vscode extensions

```bash
multi sync vscode extensions
```

Merges `extensions.json` recommendations from all repositories into the root `.vscode/extensions.json`.

**Behavior:**

- Combines all extension recommendations from all repos
- Duplicates are removed while preserving order
- Ensures your workspace recommends all extensions needed by any sub-repo

## Examples

```bash
# Merge all VS Code configurations
multi sync vscode

# Only merge settings
multi sync vscode settings

# Only merge launch configurations
multi sync vscode launch

# Only merge tasks
multi sync vscode tasks

# Only merge extension recommendations
multi sync vscode extensions
```

## Configuration

You can configure VS Code syncing behavior in `multi.json`:

```json
{
  "vscode": {
    "skipSettings": ["workbench.colorCustomizations", "editor.fontSize"]
  },
  "repos": [
    {
      "url": "https://github.com/org/repo",
      "skipVSCode": true
    }
  ]
}
```

- `skipSettings` - Array of settings keys to exclude from merging
- `skipVSCode` - Per-repo option to exclude a repo from VS Code config merging
