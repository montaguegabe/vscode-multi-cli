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
- Merges `.vscode/launch.shared.json` from the workspace root for workspace-level compounds that span repos
- Creates a master compound that includes all required configurations/compounds

**Marking launch configurations as required:**

You can mark launch configurations or compounds as required in two ways:

1. **Per-repo configuration in multi.json** (recommended):
   ```json
   {
     "repos": [
       {
         "url": "https://github.com/org/backend",
         "requiredCompounds": ["Django"],
         "requiredLaunchConfigurations": ["Debug Server"]
       }
     ]
   }
   ```

2. **In the launch definition**: Add `"required": true` to the configuration or compound in the sub-repo's `launch.json` (note: this may cause VS Code schema validation warnings)

**Using launch.shared.json for workspace-level compounds:**

Create a `.vscode/launch.shared.json` file in your workspace root to define compounds that span multiple sub-repos. This is the recommended way to create debug configurations that launch services from different repos together:

```json
{
  "compounds": [
    {
      "name": "Full Stack",
      "configurations": [
        "api: Django Server",
        "web: Next.js Dev"
      ]
    }
  ]
}
```

The contents of `launch.shared.json` are merged into the final `launch.json` after all sub-repo configurations are collected, so you can reference any configuration from any repo by its prefixed name.

---

### sync vscode tasks

```bash
multi sync vscode tasks
```

Merges `tasks.json` from all repositories into the root `.vscode/tasks.json`.

**Behavior:**

- Tasks are prefixed with the repository name
- Creates a master compound task that runs all tasks marked as required in parallel
- Useful for running build tasks across all repos simultaneously

**Marking tasks as required:**

You can mark tasks as required in two ways:

1. **Per-repo configuration in multi.json** (recommended): Add a `requiredTasks` array to the repo config listing task labels that should be required:
   ```json
   {
     "repos": [
       {
         "url": "https://github.com/org/frontend",
         "requiredTasks": ["React: Dev"]
       }
     ]
   }
   ```

2. **In the task definition**: Add `"required": true` to the task in the sub-repo's `tasks.json` (note: this may cause VS Code schema validation warnings)

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
      "skipVSCode": true,
      "requiredTasks": ["Dev Server", "Watch"],
      "requiredCompounds": ["Django"]
    }
  ]
}
```

- `skipSettings` - Array of settings keys to exclude from merging
- `skipVSCode` - Per-repo option to exclude a repo from VS Code config merging
- `requiredTasks` - Per-repo array of task labels to include in the master compound task
- `requiredCompounds` - Per-repo array of compound names to include in the master launch compound
- `requiredLaunchConfigurations` - Per-repo array of launch configuration names to include in the master launch compound
