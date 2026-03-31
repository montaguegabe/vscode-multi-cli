# collaborator

Manage GitHub collaborators across all sub-repositories in a workspace.

## Usage

```bash
multi collaborator add USERNAME --yes
multi collaborator remove USERNAME --yes
```

## Description

The `collaborator` command applies GitHub collaborator changes across every sub-repo listed in `multi.json`.

It uses the GitHub CLI via `gh api`, verifies that the GitHub user exists before making changes, and supports a `--yes` flag so scripts can run non-interactively.

Only GitHub-hosted sub-repositories are supported by this command.

## Subcommands

### `multi collaborator add`

Add a collaborator to every sub-repo.

Options:

- `--permission pull|push|admin|maintain|triage` — permission level to grant. Defaults to `push`.
- `--yes` — skip the confirmation prompt.

Example:

```bash
multi collaborator add octocat --permission maintain --yes
```

### `multi collaborator remove`

Remove a collaborator from every sub-repo.

Options:

- `--yes` — skip the confirmation prompt.

Example:

```bash
multi collaborator remove octocat --yes
```

## Notes

- `gh` must be installed and authenticated before using this command
- The command targets sub-repositories from `multi.json`, not the workspace root repository
- Without `--yes`, the command will prompt for confirmation before making changes
