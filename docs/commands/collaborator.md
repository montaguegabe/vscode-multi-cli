# collaborator

Manage GitHub collaborators across all GitHub repositories in a workspace.

## Usage

```bash
multi collaborator add USERNAME --yes
multi collaborator add --yes
multi collaborator remove USERNAME --yes
multi collaborator recent-users
```

## Description

The `collaborator` command applies GitHub collaborator changes across every sub-repo listed in `multi.json`.

If the workspace root repository also has a GitHub `origin`, the command includes that repository too.

It uses the GitHub CLI via `gh api`, verifies that the GitHub user exists before making changes, and supports a `--yes` flag so scripts can run non-interactively.

Only GitHub-hosted repositories are supported by this command.

If one repository fails, the command continues processing the remaining repositories and reports all failures at the end.

The add and remove commands remember verified GitHub usernames in `~/.multi/recent-github-users.json`. Running `multi collaborator add` without a username opens a recent-user picker, or asks for a username if no recent users have been saved.

## Subcommands

### `multi collaborator add`

Add a collaborator to every workspace repository.

Options:

- `--permission pull|push|admin|maintain|triage` — permission level to grant. Defaults to `push`.
- `--yes` — skip the confirmation prompt.
- `USERNAME` — optional. When omitted, choose from recent GitHub users or enter a username interactively.

Example:

```bash
multi collaborator add octocat --permission maintain --yes
multi collaborator add --yes
```

### `multi collaborator remove`

Remove a collaborator from every workspace repository.

Options:

- `--yes` — skip the confirmation prompt.

Example:

```bash
multi collaborator remove octocat --yes
```

### `multi collaborator recent-users`

List GitHub usernames recently used by the collaborator add and remove commands.

Example:

```bash
multi collaborator recent-users
```

## Notes

- `gh` must be installed and authenticated before using this command
- The command targets GitHub-hosted sub-repositories from `multi.json`
- If the workspace root repository has a GitHub `origin`, it is included automatically
- The command continues after per-repo GitHub API failures, then exits with a summary if any repositories failed
- Without `--yes`, the command will prompt for confirmation before making changes
- Recent GitHub usernames are stored globally for the current OS user under `~/.multi`
