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
- Declared repos have non-empty `description` fields.
- Declared repo remotes can be reached with `git ls-remote`.
- Declared repos and on-disk repos match:
  - warns if a repo is declared in `multi.json` but missing from disk.
  - warns if a git repo exists on disk but is not declared in `multi.json`.
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
- Missing descriptions are warnings because the workspace can still function, but they
  degrade generated context such as repo-directory guidance.
- Remote validation checks reachability, not just syntax. Failed checks can mean a bad URL,
  missing repo, missing credentials, or no network access.
- If you have independent nested git repositories, use standard multi-repo mode (`monoRepo: false`).
