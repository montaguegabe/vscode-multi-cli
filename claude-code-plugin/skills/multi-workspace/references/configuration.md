# multi.json Configuration Reference

## File Location

`multi.json` lives at the workspace root directory. The CLI auto-discovers it by walking up from the current working directory.

## Default Values

If keys are absent, these defaults apply:

```json
{
  "monoRepo": false,
  "allowSymlinks": false,
  "vscode": {
    "skipSettings": ["workbench.colorCustomizations"]
  },
  "repos": []
}
```

## Top-Level Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repos` | array | `[]` | Array of repository configuration objects |
| `monoRepo` | boolean | `false` | Monorepo mode: skip git cloning/branch ops; `repos` entries are local subdirectories |
| `allowSymlinks` | boolean | `false` | Enable global symlink support (must also be enabled per-repo) |
| `vscode` | object | see defaults | VS Code merge configuration |

## Per-Repo Fields (`repos[]`)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes (except monorepo) | — | Git URL (HTTPS or SSH) |
| `name` | string | No (required in monorepo if no URL) | Last URL path segment | Directory name for the clone |
| `description` | string | No | — | Used to generate `repo-directories.mdc` Cursor rule |
| `skipVSCode` | boolean | No | `false` | Exclude this repo from all VS Code config merging |
| `allowSymlink` | boolean | No | `false` | Allow symlinking to an existing clone for this repo |
| `requiredTasks` | string[] | No | — | Task labels to include in the master compound task |
| `requiredCompounds` | string[] | No | — | Compound names to include in the master launch compound |
| `requiredLaunchConfigurations` | string[] | No | — | Launch config names to include in the master launch compound |
| `vscode.settingsOverrides` | object | No | — | Settings key-values to forcibly override during settings merge |

Any additional keys in a repo config are set as attributes on the internal `Repository` object and accessible programmatically.

## VS Code Configuration (`vscode`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skipSettings` | string[] | `["workbench.colorCustomizations"]` | Settings keys to exclude from `settings.json` merge |

## Example multi.json

```json
{
  "repos": [
    {
      "url": "https://github.com/org/backend",
      "description": "Python FastAPI backend service",
      "requiredTasks": ["Start Backend"],
      "requiredLaunchConfigurations": ["Debug Backend"]
    },
    {
      "url": "https://github.com/org/frontend",
      "name": "web",
      "description": "React frontend application",
      "requiredTasks": ["Start Frontend"],
      "vscode": {
        "settingsOverrides": {
          "editor.defaultFormatter": "esbenp.prettier-vscode"
        }
      }
    },
    {
      "url": "git@github.com:org/shared-lib.git",
      "description": "Shared TypeScript library",
      "skipVSCode": true
    }
  ],
  "allowSymlinks": false,
  "vscode": {
    "skipSettings": ["workbench.colorCustomizations", "editor.fontFamily"]
  }
}
```

## Symlink System

### Global Registry

Location: `~/.multi/repos.json`

Tracks known repo clones:
```json
{
  "version": 1,
  "repos": {
    "https://github.com/org/repo": "/absolute/path/to/clone"
  }
}
```

URL normalization: `.git` suffix is stripped so HTTPS/SSH URLs with/without `.git` map to the same key.

### Clone Logic (per repo during `multi sync`)

1. If repo directory exists: register in global registry, skip.
2. Try symlink: only if `allowSymlinks: true` (global) AND `allowSymlink: true` (per-repo) AND repo found in registry AND registered path is not inside current workspace AND registered path has no `venv/` or `.venv/`.
3. Fall back to `git clone`, then checkout the workspace's current branch if it exists in the sub-repo.
4. Register new clone in global registry.

## Monorepo Mode

When `monoRepo: true`:
- No git cloning or symlinking occurs
- `repos` entries reference existing subdirectories by `name`
- `multi set-branch` and `multi git` are disabled
- VS Code merging still works normally
