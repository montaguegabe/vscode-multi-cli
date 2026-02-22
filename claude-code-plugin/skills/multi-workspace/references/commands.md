# Multi CLI Commands Reference

## Global Options

- `--version` — print version and exit
- `--verbose` — enable verbose output (available on all commands)

## multi init

Interactive workspace initialization.

**Steps performed:**
1. Prompts for repo URLs one at a time (with optional descriptions for each).
2. Writes `multi.json` with collected URLs and descriptions.
3. Initializes a git repo if none exists.
4. Creates `README.md` from template with repo links (if it doesn't exist).
5. Runs a full `multi sync`.
6. Commits everything with message `"Multi init: Configure multi workspace"`.

**Important**: This command is interactive — it prompts for input and cannot be scripted.

## multi sync

Run all sync operations in order:
1. Clone/symlink missing sub-repos (skipped in monorepo mode).
2. Update `.gitignore` and `.ignore`.
3. Merge VS Code configs.
4. Sync Cursor rules / generate `CLAUDE.md` + `AGENTS.md`.
5. Sync ruff config.

### Subcommands

#### multi sync vscode

Merge all VS Code config files. Sub-subcommands for individual files:

- `multi sync vscode settings` — merge `settings.json`
- `multi sync vscode launch` — merge `launch.json`
- `multi sync vscode tasks` — merge `tasks.json`
- `multi sync vscode extensions` — merge `extensions.json`
- `multi sync vscode devcontainer` — sync `.devcontainer` folder

#### multi sync rules

1. Generate `.cursor/rules/repo-directories.mdc` from `description` fields in `multi.json`.
2. For each directory with `.cursor/rules/*.mdc`: concatenate rule bodies into `CLAUDE.md` and `AGENTS.md`.
3. Remove `CLAUDE.md`/`AGENTS.md` if no rules exist.

#### multi sync ruff

Copy `ruff.toml` from a sub-repo to workspace root. If multiple repos have `ruff.toml`, the last one wins. If none found and a root `ruff.toml` exists, it is deleted.

## multi set-branch BRANCH_NAME

Switch all repos to a branch.

**Preconditions:**
- All repos (root + sub-repos) must have clean working directories (no uncommitted or untracked changes).

**Behavior:**
- Operates on root repo first, then sub-repos.
- If branch exists locally or on remote: checks it out.
- If branch doesn't exist anywhere: creates it from current HEAD.
- If repos are on different branches: branch creation is disallowed (can only switch to existing branches).

**Disabled in monorepo mode.**

## multi git GIT_ARGS...

Run any git command across all repos.

**Preconditions:**
- All repos must be on the same branch.

**Behavior:**
- Runs the command in root repo first, then each sub-repo in order.
- Passes all arguments directly to git.

**Examples:**
```bash
multi git pull
multi git status
multi git push -u origin feature/foo
multi git fetch --all
```

**Disabled in monorepo mode. Interactive git commands (e.g., `git rebase -i`) are not supported.**

## multi open PATH

Open a project path in the Multi desktop app by launching a `multi://open?path=...` URL.

Does not require `multi.json`.

## .gitignore and .ignore Management

After cloning, Multi automatically updates:

**`.gitignore`** — adds under `# Ignore repository directories`:
- `repo-name/` and `repo-name` (without slash, for symlink support)
- Generated files: `.vscode/settings.json`, `.vscode/tasks.json`, `.vscode/launch.json`, `.vscode/extensions.json`, `CLAUDE.md`, `AGENTS.md`

**`.ignore`** — adds under `# Allow us to search inside these gitignored directories`:
- `!repo-name/` and `!repo-name` (so VS Code search works inside gitignored sub-repos)
