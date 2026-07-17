---
name: issue-to-github
description: Validate a described problem and create one evidence-based GitHub issue while avoiding duplicates.
---

# Issue to GitHub

Create an issue only when the requested outcome includes GitHub issue creation. Describing, diagnosing, or finding a bug alone remains read-only.

Resolve the intended GitHub repository against its git remotes and `gh repo view`; stop on fork/upstream, multiple-remote, or ownership ambiguity. Validate the described problem against its code, contract, reachable trigger, and impact. If it is not a demonstrated problem, explain why and do not create an issue.

Search open and closed issues for the same root cause and outcome. Return an open canonical issue or a closed duplicate, declined, or still-applicable issue; create a new issue for a verified regression after a prior fix and reference the old one. Otherwise create one concise, evidence-based issue without secrets or unsupported claims. Include relevant `file:line` locations and a minimal fix direction, use only existing labels unless the user requests a new one, and pass the body through a temporary file rather than shell interpolation. Verify and return the created issue URL; if the mutation result is uncertain, search recent issues before retrying.
