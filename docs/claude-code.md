# Claude Code Skill

Multi provides a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) that helps Claude understand multi-managed workspaces. When Claude detects a `multi.json` file or you ask about multi-repo workflows, it automatically loads context about Multi's commands, configuration, and conventions.

## Installation

Copy the skill files to your Claude Code skills directory:

```bash
mkdir -p ~/.claude/skills/multi/references
```

Then copy the following files from the Multi repository's `claude-code-skill/` directory:

```
~/.claude/skills/multi/
├── SKILL.md                      # Main skill file
└── references/
    ├── configuration.md          # multi.json schema reference
    └── vscode-sync.md            # VS Code merging details
```

Or install with a single command:

```bash
cp -r "$(pip show multi-workspace | grep Location | cut -d' ' -f2)/multi/claude-code-skill/"* ~/.claude/skills/multi/
```

## What It Provides

The skill gives Claude knowledge of:

- **Workspace detection** - Recognizes `multi.json` and understands workspace structure
- **Command usage** - Knows when and how to use `multi sync`, `multi set-branch`, `multi git`, etc.
- **Configuration schema** - Understands all `multi.json` fields and options
- **VS Code merging** - Knows how launch configs, tasks, and settings are prefixed and merged
- **Key constraints** - Knows that `multi init` is interactive, `CLAUDE.md` is auto-generated, and repos must be clean for branch switching

## Trigger Phrases

The skill activates when you mention topics like:

- `multi.json`, multi workspace, multi CLI
- Branch switching across repos
- VS Code config merging, syncing
- Cursor rules sync, `CLAUDE.md` generation
- Working with multiple repositories

## Example Usage

Once installed, you can ask Claude things like:

- "How do I add a new repo to this workspace?"
- "Switch all repos to a feature branch"
- "Why isn't my launch config showing up?"
- "What does `requiredCompounds` do in multi.json?"

Claude will use its knowledge of Multi to give accurate, context-aware answers.
