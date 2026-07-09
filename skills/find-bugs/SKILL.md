---
name: find-bugs
description: Run a broad, multi-domain, or sampled bug campaign with read-only delegated review. Return findings directly unless the user asks to maintain FOUND_ISSUES.md; use find-domain-bugs for one focused path or domain.
---

# Find Bugs

## Route and investigate

- Route a focused audit of one path or domain to [find-domain-bugs](../find-domain-bugs/SKILL.md) unless the user explicitly requests a report-producing campaign.
- For a campaign, infer coherent domains from the repository unless the user supplies scope. For a requested spot check, sample relevant source files reproducibly and report the selected files and seed.
- Delegate disjoint scopes to read-only workers using `find-domain-bugs`, bounded by available concurrency. Workers may inspect related code needed to prove behavior but must not edit files or create issues.
- Have the parent validate every candidate against the code and its contract, deduplicate common root causes, and normalize severity by impact. Keep only confident, reachable bugs—not style, TODOs, speculative hardening, or missing tests without faulty behavior.

## Optional FOUND_ISSUES.md

Only write a report when the user asks for one. Use `./FOUND_ISSUES.md` unless they specify another path, with this compatible six-field form:

```markdown
### Issue {n}: {summary}

- **Domain:** {domain}
- **Severity:** {critical | high | medium | low}
- **File(s):** `{file}:{line}`
- **Details:** {evidence and observable failure}
- **Suggested fix:** {minimal fix direction}
- **Status:** Pending

---
```

Keep the fields in that order and `Status` last. A new report uses the existing `# Found Issues`, generated date, severity summary, and `## Issues` structure.

When a report exists, parse it before writing. Preserve existing issue numbers, text, fields, and statuses; never reset created, rejected, duplicate, or manually edited entries. Append only newly validated, nonduplicate bugs, continue numbering, and refresh the summary. If parsing is ambiguous, leave the file unchanged and report the problem. If there are no new bugs, leave an existing report unchanged.

Report the campaign scope, accepted findings by severity, and rejected or uncertain leads. Include sampled files and seed for a spot check, and the report path when one was written.
