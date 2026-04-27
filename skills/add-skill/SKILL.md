---
name: add-skill
description: Use when the user wants to add a new command/skill pair.
---

# Add Skill

- Create a skill at `~/Documents/repositories/dotfiles/skills` with frontmatter (name, description) and an instruction body.
- Be consistent with existing commands/skills in those directories.
- Write the skill body for the agent, not a human.
- Think about the role, judgment, and task the skill is for, then write instructions that help the agent make good decisions in varied real contexts.
- Prefer intent, principles, boundaries, and expected output over rigid procedures.
- Include exact step-by-step workflow only when order or command shape is essential for correctness, safety, or interoperability.
- Give the agent room to adapt scope, tools, delegation, and level of detail to the user's request.
- Describe what high-quality execution looks like, including tradeoffs and when to avoid overdoing the skill.
