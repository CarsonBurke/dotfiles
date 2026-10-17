---
name: add-skill
description: Use when creating or editing a personal skill.
---

# Add Skill

- Everything around an agent conditions it: skills, global instructions, documentation, and the examples implicit in existing code and comments. Ideally all of it conditions the agent away from the things agents normally do that hurt them. These are generally overconfidence, not predicting consequences and alternatives, narrativizing, and bad epistemology and ontology overall.
- So a skill is a set of suggestions for a reader as capable as you or more so. A useful starting question is what an agent would get wrong here by default.
- The skill's own writing is one of those examples. A common failure is taking something that is good in some cases and writing it as an absolute, which the agent then applies where it doesn't fit, and which is itself overconfident. Say when and why something is good, and leave absolutes for things that are always true.
- Context and reasons usually work better than dos and don'ts or specific steps.
- Most skills end up short, because the agent already knows or would do most of what you could write. Some need more, such as how to use a tool.
- The description usually only needs to say when to use the skill.
- Sources are in `skills/src/<name>.md` in this dotfiles repository. See `skills/README.md` for building and checks.
- `skill-creator` has the format reference and `quick_validate.py`, but its style advice is more verbose and prescriptive than we want.
- `.system` and `synced/` are upstream snapshots.
