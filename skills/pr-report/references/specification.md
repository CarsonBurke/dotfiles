# Report specification

`render_report.py` accepts one UTF-8 JSON object. All displayed values are non-empty strings unless noted. Repository-derived strings are HTML-escaped by the renderer.

## Top-level fields

- `title`, `executive_summary`, `base_sha`, `head_sha`, `worktree_state`, and `risk_summary`
- `repository` and `scope`: either a string or `{ "label": "…", "url": "https://…" }`
- `generated` (optional): `{ "iso": "2026-07-21T22:00:00-07:00", "display": "July 21, 2026 · 22:00 PDT" }`; local time is generated when omitted
- `outcome`: `{ "title": "…", "summary": "…" }`
- `important_note`: `{ "title": "…", "text": "…" }`
- `coverage`: one or more `{ "claim": "…", "evidence": "…", "status": "covered|gap" }`
- `evidence`: one or more evidence objects described below
- `validation`: one or more `{ "status": "pass|warn|gap|fail", "name": "…", "evidence": "…" }`
- `risks`: one or more `{ "title": "…", "detail": "…" }`; when no product risk is known, record the evidence boundary instead of implying exhaustive review
- `provenance`: `{ "text": "…", "links": [{ "label": "…", "url": "https://…" }] }`; `links` may be empty

Links must use HTTP or HTTPS and cannot contain URL credentials. Sanitize private identifiers and sensitive URL paths before adding them.

## Evidence objects

Every evidence object has `type`, `area`, `title`, and `summary`, plus an optional `note`.

### Screenshot

Provide `before`, `after`, or both. Image paths are relative to `--asset-root`, cannot contain query strings or fragments, and are embedded into the output.

```json
{
  "type": "screenshot",
  "area": "Button disabled state",
  "title": "Disabled controls retain readable contrast",
  "summary": "Matched light-theme captures at 390 × 844 CSS pixels.",
  "before": {
    "caption": "Muted label disappears",
    "image": "button-before.png",
    "alt": "Disabled button before the change with a faint label"
  },
  "after": {
    "caption": "Muted label remains legible",
    "image": "button-after.png",
    "alt": "Disabled button after the change with a readable label"
  }
}
```

### Code or textual transcript

Provide `before`, `after`, or both. Use `path_ref` for the file, command, revision, or other provenance. The `code` string can contain source, a schema, a sanitized request/response, CLI output, a query, or a benchmark excerpt.

```json
{
  "type": "code",
  "area": "Retry control flow",
  "title": "Cancellation is terminal",
  "summary": "The signal reaches fetch and aborts are not retried.",
  "after": {
    "caption": "Abort-aware implementation",
    "path_ref": "src/retry.ts · def5678",
    "code": "return fetch(url, { signal });"
  }
}
```

### Comparison table

`columns` is a non-empty string array. Every row must contain exactly the same number of non-empty string cells.

```json
{
  "type": "table",
  "area": "Compatibility",
  "title": "Payload handling by client version",
  "summary": "The new field remains optional for older clients.",
  "columns": ["Client", "Old payload", "New payload"],
  "rows": [
    ["Current", "Accepted", "Accepted"],
    ["Previous", "Accepted", "Unknown field ignored"]
  ]
}
```

Use `assets/spec.example.json` as a complete runnable backend example. Repeat evidence objects as needed; do not add an empty screenshot block to a non-visual report.
