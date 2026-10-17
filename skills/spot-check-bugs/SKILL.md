---
name: spot-check-bugs
description: Run a reproducible sampled bug audit and, when authorized, create GitHub issues for confirmed, nonduplicate findings.
---

# Spot Check Bugs

Run the sampled campaign below, passing along any scope, sample size, or seed the user gave.

# Find Bugs

Creating GitHub issues is part of this workflow only when the request authorizes changes on GitHub. A request to find, review, or diagnose bugs is read-only: return the validated findings in your response. Either way, don't write a local findings report.

## Investigate

- For one path or domain, apply [find-domain-bugs](../find-domain-bugs/SKILL.md) directly or delegate it.
- For a campaign, infer coherent domains from the repository unless the user gives a scope, and delegate disjoint ones to read-only workers using `find-domain-bugs`, as many at once as concurrency allows.
- For a spot check, sample relevant source files reproducibly and report the files and seed.
- Validate every candidate yourself against the code and its contract, merge findings that share a root cause, and normalize severity by impact. Keep only confident, reachable bugs.

## Create issues

- Resolve the GitHub repository from the git remotes and `gh repo view`, and stop if forks, multiple remotes, or ownership make it ambiguous.
- Before creating each issue, search open and closed issues for the same root cause. An open issue, or a closed one that was a duplicate, was declined, or still applies, answers the finding instead of a new issue. A regression after a fixed issue usually gets a new issue that references the old one.
- Create issues one at a time so each result is known before the next.
- The body is for whoever fixes it: the contract, the reachable trigger, `file:line` locations, the impact, and a minimal fix direction, with a concise title, evidence kept apart from inference, and no secrets or unsupported claims. Use only existing labels unless asked to create one, and pass the body through a temporary file rather than the shell command line.
- Verify each issue URL after creating it. If a result is uncertain, search recent issues before retrying, and on a persistent error stop rather than risk duplicates.

Report the scope, the created and existing issue links, rejected or uncertain leads, and the seed if you sampled.
