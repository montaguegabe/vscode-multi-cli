# Multi Agent Skill

Multi now ships as an agent skill repository compatible with [`vercel-labs/skills`](https://github.com/vercel-labs/skills).

The skill teaches agents how to work with Multi-managed workspaces, including `multi.json`, branch orchestration, VS Code sync behavior, and Cursor-rules-to-`CLAUDE.md` generation.

## Installation

Install the Multi skill from the standalone repo:

```bash
# Optional: preview available skills
npx skills add montaguegabe/multi-skills --list

# Install for detected local agents
npx skills add montaguegabe/multi-skills --skill multi-workspace
```

Common options:

```bash
# Install globally instead of project-local
npx skills add montaguegabe/multi-skills --skill multi-workspace -g

# Target specific agents only
npx skills add montaguegabe/multi-skills --skill multi-workspace -a claude-code -a codex
```

## What It Provides

The `multi-workspace` skill gives your agent knowledge of:

- **Workspace detection** - Recognizes `multi.json` and understands workspace structure
- **Command usage** - Knows when and how to use `multi sync`, `multi add`, `multi collaborator`, `multi set-branch`, `multi git`, etc.
- **Configuration schema** - Understands all `multi.json` fields and options
- **VS Code merging** - Knows how launch configs, tasks, and settings are prefixed and merged
- **Key constraints** - Knows that `multi init` supports both interactive and non-interactive setup, can optionally create GitHub repos via `gh`, `multi add` follows the same workspace-prefix shortening rule for local folder names, `multi collaborator` uses `gh api` to manage GitHub access across all subrepos, `CLAUDE.md` is auto-generated, and repos must be clean for branch switching

## Trigger Phrases

The skill activates when you mention topics like:

- `multi.json`, multi workspace, multi CLI
- Branch switching across repos
- VS Code config merging, syncing
- Cursor rules sync, `CLAUDE.md` generation
- Working with multiple repositories

## Example Usage

Once installed, you can ask your agent things like:

- "How do I add a new repo to this workspace?"
- "Switch all repos to a feature branch"
- "Why isn't my launch config showing up?"
- "What does `requiredCompounds` do in multi.json?"
