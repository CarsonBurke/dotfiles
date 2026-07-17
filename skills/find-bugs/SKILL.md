---
name: find-bugs
description: Audit code for concrete bugs and, when authorized, create GitHub issues for confirmed, nonduplicate findings.
---

# Find Bugs

Issue creation is part of this workflow when the requested outcome authorizes GitHub mutation. A request to find, review, or diagnose bugs alone is read-only: return validated findings in the response without mutating GitHub or writing a local report.

## Investigate

- For one path or domain, apply [find-domain-bugs](../find-domain-bugs/SKILL.md) directly or delegate that bounded scope.
- For a campaign, infer coherent domains from the repository unless the user supplies scope. For a requested spot check, sample relevant source files reproducibly and report the selected files and seed.
- Delegate disjoint scopes to read-only workers using `find-domain-bugs`, bounded by available concurrency. Workers may inspect related code needed to prove behavior but must not edit files or create issues.
- Have the parent validate every candidate against the code and its contract, deduplicate common root causes, and normalize severity by impact. Keep only confident, reachable bugs—not style, TODOs, speculative hardening, or missing tests without faulty behavior.

## Create issues

Resolve the intended GitHub repository against its git remotes and `gh repo view`; stop on fork/upstream, multiple-remote, or ownership ambiguity.

Before each creation, search open and closed issues for the same root cause and outcome. Return an open canonical issue or a closed duplicate, declined, or still-applicable issue instead of creating another. A verified regression after a previously fixed issue normally warrants a new issue that references the prior one. Create issues serially so each result is known before continuing.

Write a concise title and an evidence-based body covering the contract, reachable trigger, relevant `file:line` locations, observed impact, and minimal fix direction. Distinguish repository evidence from inference; omit secrets and unsupported claims. Use only existing repository labels unless the user asks to create one. Pass generated bodies through a temporary file rather than interpolating them into a shell command.

After each mutation, verify the issue URL. If a result is uncertain, search recent issues before retrying; on a persistent mutation error, stop rather than risk duplicates. Report the audit scope, created and existing issue links, rejected or uncertain leads, and the sample seed when used. Do not create a local findings report.
