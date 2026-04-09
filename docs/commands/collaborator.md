# collaborator

Manage GitHub collaborators across all GitHub repositories in a workspace.

## Usage

```bash
multi collaborator add USERNAME --yes
multi collaborator remove USERNAME --yes
```

## Description

The `collaborator` command applies GitHub collaborator changes across every sub-repo listed in `multi.json`.

If the workspace root repository also has a GitHub `origin`, the command includes that repository too.

It uses the GitHub CLI via `gh api`, verifies that the GitHub user exists before making changes, and supports a `--yes` flag so scripts can run non-interactively.

Only GitHub-hosted repositories are supported by this command.

If one repository fails, the command continues processing the remaining repositories and reports all failures at the end.

## Subcommands

### `multi collaborator add`

Add a collaborator to every workspace repository.

Options:

- `--permission pull|push|admin|maintain|triage` — permission level to grant. Defaults to `push`.
- `--yes` — skip the confirmation prompt.

Example:

```bash
multi collaborator add octocat --permission maintain --yes
```

### `multi collaborator remove`

Remove a collaborator from every workspace repository.

Options:

- `--yes` — skip the confirmation prompt.

Example:

```bash
multi collaborator remove octocat --yes
```

## Notes

- `gh` must be installed and authenticated before using this command
- The command targets GitHub-hosted sub-repositories from `multi.json`
- If the workspace root repository has a GitHub `origin`, it is included automatically
- The command continues after per-repo GitHub API failures, then exits with a summary if any repositories failed
- Without `--yes`, the command will prompt for confirmation before making changes
