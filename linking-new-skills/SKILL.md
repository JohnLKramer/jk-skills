---
name: linking-new-skills
description: Use when a new skill has just been created or moved, to make it discoverable across all agent runtimes.
---

# Linking New Skills

## Overview

Skills only get discovered from the directories a given runtime searches (`~/.claude/skills/` for Claude Code, etc.). `~/.agents/skills/` is the cross-runtime alias that Claude Code, Codex, Copilot CLI, and Gemini CLI all recognize. A skill authored in a project repo (e.g. `jk-skills`, `classpass/agents`) is invisible to other runtimes until it has an entry there.

## When to Use

After creating a new skill directory anywhere (personal repo, project repo, `~/.claude/skills/`), before considering the work done.

## What to Do

Create a symlink in `~/.agents/skills/` named after the skill, pointing at the skill's real directory — wherever that directory was created:

```bash
ln -s /absolute/path/to/repo/skill-name ~/.agents/skills/skill-name
```

Match the existing convention in `~/.agents/skills/`: the link name equals the skill's directory name, and it points directly at the skill folder (not a parent directory).

## Quick Reference

| Skill created in | Symlink target |
|---|---|
| `~/source/personal/jk-skills/foo/` | `~/.agents/skills/foo -> ~/source/personal/jk-skills/foo` |
| `~/source/classpass/agents/skills/bar/` | `~/.agents/skills/bar -> ~/source/classpass/agents/skills/bar` |

## Common Mistakes

- Forgetting this step entirely — the skill works when invoked by path but never surfaces via discovery in other runtimes.
- Linking to a parent directory instead of the skill directory itself.
- Using a relative path in the symlink instead of an absolute one.
