# Personal skill sources

Author personal skills in `src/<name>.md`. Each source has the usual YAML
frontmatter (`name` matching the filename, plus `description`) and Markdown body.
The generated `skills/<name>/SKILL.md` files remain checked in and are what agents
load through `~/.agents/skills`. They carry no marker, so remember that an edit
made there is overwritten by the next build.

From the repository root:

```sh
python3 -m pip install -r skills/requirements.txt
python3 skills/build.py
python3 skills/build.py --check
python3 -m unittest discover -s skills/tests -v
```

The build resolves paths relative to the script, so it also works from another
directory. Commit source changes together with their regenerated outputs.
`--check` writes nothing and exits nonzero for missing or stale outputs.
Builds validate the whole include graph before writing and leave identical files
untouched. The generator cannot tell a retired output from a skill installed by
something else, so it never deletes or reports either: retiring a skill means
removing both `src/<name>.md` and `skills/<name>/`.

## Composition

Place an include on its own line wherever the shared instructions belong:

```markdown
---
name: merge-steward-pr
description: Steward a PR and merge it once ready.
---

# Merge Steward PR

Complete stewardship, then merge the ready PR.

<!-- include: steward-pr -->

## Merge

Verify the current head, required checks and reviews, then merge and verify it.
```

The generator inserts the included skill's body, recursively, without its
frontmatter. The wrapper keeps its own name and description.
Includes expand in order; repeated includes are repeated deliberately. Directives
inside fenced code blocks remain literal examples. Unknown targets, cycles,
malformed directives, and invalid metadata fail the build.

Reusable instructions that should not be discoverable skills belong in
`src/parts/<name>.md`, without frontmatter. Include them with
`<!-- include: parts/<name> -->`. Share judgment in parts when the skills taking
different actions would otherwise inherit conflicting instructions. For example,
`review-deep` and `review-deep-action` share review standards while only the former
requires remaining read-only. Express direct-invocation limits and the actions a
wrapper adds explicitly: composition inserts text and does not resolve semantic
conflicts or grant permissions by itself.

Keep scripts, references, and assets in the existing `skills/<name>/` directory;
this generator owns only `SKILL.md`. Included resource references must identify
their original skill directory (for example `../other-skill/references/guide.md`),
since composition does not rewrite paths. Include directives resolve only sources
and parts, never arbitrary files. Synced skills, upstream snapshots, and trash are
outside this build.
