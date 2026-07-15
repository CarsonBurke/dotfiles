---
name: github-issues
description: Create GitHub issues from described problems or a FOUND_ISSUES.md report.
---

# GitHub Issues

Creating issues requires explicit user intent. Nearby findings or failures do not authorize remote mutation.

## Modes and validation

- **Single:** turn the requested problem and relevant repository evidence into one candidate.
- **Report:** read `FOUND_ISSUES.md` or the specified report and process pending, validated, or retryable error entries. Preserve the six fields and skip terminal statuses.

Confirm the target repository. Delegate validation when useful, but keep workers read-only and bounded by available concurrency. The parent verifies each contract, trigger, location, and impact and records rejected report entries as `Not a bug — <reason>`.

Before every creation, check both open and closed issues for the same root cause and outcome. Return the existing issue in single mode or record `Duplicate — <URL>` in report mode. Use only existing repository labels unless the user explicitly asks to create labels.

## Create and resume

Create a concise, evidence-based title and body without secrets or unsupported claims. Pass the body through a temporary file rather than shell interpolation. Create issues serially.

After each success, immediately record `Created — <URL>` in that report entry. If a result is uncertain, check recent open and closed issues before retrying. On a persistent mutation error, record `Error — <reason>`, stop, and leave untouched entries resumable. A rerun repeats validation and duplicate checks before creating anything.

Do not alter issue numbers, the other five fields, terminal statuses, or unrelated report content. If the report is ambiguous, do not mutate it or GitHub. Finish with created/existing links and counts for created, duplicate, rejected, error, and skipped entries.
