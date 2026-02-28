# doctor

Diagnose common workspace configuration issues.

## Usage

```bash
multi doctor [--strict] [--fix]
```

## Description

`multi doctor` checks for common setup problems and prints actionable guidance.

Use `--fix` to automatically remove tracked sub-repo directories from the root git
index in standard mode (`monoRepo: false`) using `git rm -r --cached` (files remain
on disk).

## Checks

- `multi.json` can be discovered from the current directory.
- `multi.json` is valid JSON and can be parsed.
- Root workspace git repo exists.
- Standard mode (`monoRepo: false`) consistency:
  - warns if sub-repos are tracked in the root git index.
  - warns if sub-repos are configured as git submodules.
- `monoRepo` mode consistency:
  - warns if configured repo directories contain nested `.git` folders.

## Strict Mode

By default, warnings do not fail the command. Use strict mode to fail on warnings:

```bash
multi doctor --strict
```

## Fix Mode

Apply safe fixes for tracked sub-repos:

```bash
multi doctor --fix
```

## Notes

- In `monoRepo` mode, listed directories should be part of the root git repo.
- If you have independent nested git repositories, use standard multi-repo mode (`monoRepo: false`).
