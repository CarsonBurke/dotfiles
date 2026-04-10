---
name: add-skill
description: Use when the user wants to add a new command/skill pair.
---

# Add Skill

- Create a Claude Code command at `~/.claude/commands/<name>.md` — a brief one-liner prompt.
- Create a matching Codex skill at `~/.codex/skills/<name>/SKILL.md` with frontmatter (name, description) and a short instruction body.
- Keep both consistent with existing commands/skills in those directories.
- Ask the user for the skill name and description if not provided.
