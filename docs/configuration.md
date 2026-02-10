# Configuration

Multi uses a `multi.json` file in your workspace root to store configuration.

## File Location

```
my-workspace/
├── multi.json          # Configuration file
├── .vscode/            # Merged VS Code config
├── repo-a/             # Sub-repository
├── repo-b/             # Sub-repository
└── ...
```

## Configuration Format

```json
{
  "repos": [
    {
      "url": "https://github.com/org/repo-a",
      "name": "custom-name",
      "skipVSCode": false
    },
    {
      "url": "https://github.com/org/repo-b"
    }
  ],
  "vscode": {
    "skipSettings": ["workbench.colorCustomizations"]
  }
}
```

## Options

### allowSymlinks

| Type | Default | Description |
|------|---------|-------------|
| boolean | `true` | Enable symlinking to existing repository clones instead of re-cloning |

When enabled, Multi maintains a global registry at `~/.multi/repos.json` that tracks where repositories have been cloned. If a repository already exists in another workspace, Multi will create a symlink to it instead of cloning fresh.

This is useful when you work with the same repositories across multiple workspaces, as it:
- Saves disk space by avoiding duplicate clones
- Keeps repository state synchronized across workspaces
- Speeds up `multi sync` by avoiding network operations

#### Example: Disable symlinks globally

```json
{
  "allowSymlinks": false,
  "repos": [...]
}
```

---

### repos

An array of repository configurations. Each repository object supports:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | Git repository URL (HTTPS or SSH) |
| `name` | string | No | Last segment of URL | Custom directory name for the cloned repo |
| `skipVSCode` | boolean | No | `false` | Skip this repo when merging VS Code configurations |
| `allowSymlink` | boolean | No | `true` | Allow symlinking to an existing clone of this repo |

#### Example: Basic repository list

```json
{
  "repos": [
    { "url": "https://github.com/org/backend" },
    { "url": "https://github.com/org/frontend" },
    { "url": "git@github.com:org/private-repo.git" }
  ]
}
```

#### Example: Custom directory names

```json
{
  "repos": [
    {
      "url": "https://github.com/org/my-long-repository-name",
      "name": "api"
    },
    {
      "url": "https://github.com/org/another-long-name",
      "name": "web"
    }
  ]
}
```

#### Example: Skip VS Code config for a repo

```json
{
  "repos": [
    { "url": "https://github.com/org/main-app" },
    {
      "url": "https://github.com/org/legacy-tool",
      "skipVSCode": true
    }
  ]
}
```

#### Example: Disable symlink for a specific repo

Use this when a repository needs its own isolated clone (e.g., for testing different branches independently):

```json
{
  "repos": [
    { "url": "https://github.com/org/shared-lib" },
    {
      "url": "https://github.com/org/needs-own-copy",
      "allowSymlink": false
    }
  ]
}
```

---

### vscode

VS Code-specific configuration options.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skipSettings` | string[] | `["workbench.colorCustomizations"]` | Settings keys to exclude when merging settings.json |

#### Example: Skip additional settings

```json
{
  "repos": [...],
  "vscode": {
    "skipSettings": [
      "workbench.colorCustomizations",
      "editor.fontSize",
      "terminal.integrated.fontSize"
    ]
  }
}
```

This is useful when sub-repos have user-specific settings that shouldn't be merged into the root configuration.

## Shared VS Code Files

Multi supports "shared" VS Code configuration files that are merged into the final output. These files are useful for workspace-level settings that apply across all repos.

### .vscode/settings.shared.json

Settings that should be applied to all repos. Contents are merged into the final `settings.json`.

### .vscode/launch.shared.json

Launch configurations and compounds that span multiple repos. This is the recommended way to create debug compounds that launch services from different sub-repos together:

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

The shared launch file is merged after all sub-repo configurations are collected, so you can reference any configuration by its prefixed name (e.g., `"repo-name: Config Name"`).

## Full Example

```json
{
  "allowSymlinks": true,
  "repos": [
    {
      "url": "https://github.com/myorg/api-server",
      "name": "api"
    },
    {
      "url": "https://github.com/myorg/web-client",
      "name": "web"
    },
    {
      "url": "https://github.com/myorg/mobile-app",
      "name": "mobile",
      "skipVSCode": true
    },
    {
      "url": "git@github.com:myorg/shared-utils.git",
      "name": "shared",
      "allowSymlink": false
    }
  ],
  "vscode": {
    "skipSettings": [
      "workbench.colorCustomizations",
      "editor.fontFamily"
    ]
  }
}
```

## Notes

- The `multi.json` file is created automatically by `multi init`
- You can manually edit this file to add or remove repositories
- After editing, run `multi sync` to apply changes
- Repository URLs can be HTTPS or SSH format
- The global registry is stored at `~/.multi/repos.json` and tracks all known repository locations
