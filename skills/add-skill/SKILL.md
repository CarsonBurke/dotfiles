---
name: add-skill
description: Create or update a personal Codex skill in this dotfiles repository. Use when the user wants to add a repository-owned skill rather than install or modify an upstream system skill.
---

# Add Skill

- Follow `skill-creator` and place the skill under this repository's `skills/` directory.
- Do not edit `.system`; it is an upstream snapshot.
- Match the folder and frontmatter name. Make the description clear about what triggers the skill.
- Write for a capable agent with no session memory. Keep only durable context, useful judgment, and non-obvious constraints; avoid narrating ordinary reasoning or engineering practice.
- Inspect related skills for overlap, validate with `.system/skill-creator/scripts/quick_validate.py`, and test any bundled scripts.
