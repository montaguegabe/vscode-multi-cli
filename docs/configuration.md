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

### repos

An array of repository configurations. Each repository object supports:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | Git repository URL (HTTPS or SSH) |
| `name` | string | No | Last segment of URL | Custom directory name for the cloned repo |
| `skipVSCode` | boolean | No | `false` | Skip this repo when merging VS Code configurations |

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

## Full Example

```json
{
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
      "name": "shared"
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
