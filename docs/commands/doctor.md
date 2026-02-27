# doctor

Diagnose common workspace configuration issues.

## Usage

```bash
multi doctor [--strict]
```

## Description

`multi doctor` checks for common setup problems and prints actionable guidance.

## Checks

- `multi.json` can be discovered from the current directory.
- `multi.json` is valid JSON and can be parsed.
- Root workspace git repo exists.
- `monoRepo` mode consistency:
  - warns if configured repo directories contain nested `.git` folders.

## Strict Mode

By default, warnings do not fail the command. Use strict mode to fail on warnings:

```bash
multi doctor --strict
```

## Notes

- In `monoRepo` mode, listed directories should be part of the root git repo.
- If you have independent nested git repositories, use standard multi-repo mode (`monoRepo: false`).
