# add

Add a repository to an existing multi workspace.

## Usage

```bash
multi add https://github.com/org/t-ide-cli
multi add https://github.com/org/t-ide-cli --name cli
```

## Description

The `add` command appends a repository to `multi.json` and runs `multi sync` so the repo is cloned and all generated workspace files are refreshed.

If the repo slug starts with the workspace directory name plus `-`, `multi add` automatically writes a short local `name` to `multi.json`. For example, in a workspace named `t-ide`, adding `https://github.com/org/t-ide-cli` will use local folder `cli`.

## Options

- `--name TEXT` — override the local directory name written to `multi.json`

## Examples

Add a product-prefixed repo and let `multi` shorten the local folder name:

```bash
multi add https://github.com/org/t-ide-cli
```

This writes:

```json
{
  "url": "https://github.com/org/t-ide-cli",
  "name": "cli"
}
```

Use an explicit local name when you want to override the default:

```bash
multi add https://github.com/org/t-ide-cli --name tools-cli
```
