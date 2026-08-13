# Proof and review router

Read this during G1–G2, before implementation changes can bias tests or oracles. It is the complete protocol for routine work and routes material-risk work to the deeper appendix. Rigor changes notation and independence, never the meaning of pass.

## Select the profile

Use the **routine profile** only when evidence supports every condition: the change is mechanical and localized; impact is low, reversible, and readily detectable; no public, persisted, cross-surface, packaging, external, or security/privacy contract changes; no user journey or lifecycle ownership changes; topology is narrow; and no material causal or product uncertainty remains.

Use the **material-risk profile** when any of these is true:

- the change affects a user journey or meaningful UI state, cross-surface policy, public API/schema, persisted data/migration, async/concurrency/process lifecycle, privacy/security/auth, destructive/financial effects, an external integration, performance/resources, packaging/platform behavior, or rollout/observability;
- failure is high impact, broad, hard to reverse, or hard to detect;
- the work is stacked/broad, the invariant owner is unclear, or causal/product judgment is materially uncertain.

An internal-tool label, small diff, familiar code, green suite, or easy rollback does not downgrade a material trigger. Upgrade immediately when discovery, implementation, proof, or review exposes hidden complexity. Record the profile and decisive facts in the selected run record; review classification itself so risk cannot be defined away. Material-risk work must now read and execute [material-proof-and-review.md](material-proof-and-review.md); the rest of this file remains its shared minimum.

## Freeze claims before edits

For every ticket:

1. Resolve the actual base and inventory tracked, staged, unstaged, intentional untracked, generated, and excluded starting state.
2. Name the actor, Given/When/Then terminal outcome, consequential negative/recovery outcome when reachable, invariant/non-goal, and independent observable that distinguishes pass, fail, and unknown. Use an evidence-backed `n/a` for a dimension that genuinely cannot apply.
3. Locate the production entrypoint, changed producer → contract → consumer path, existing harnesses/mocks, and the highest credible wrong behavior. Reproduce the baseline or nearest controlled negative case when applicable.
4. Freeze concise content-addressed claim labels, input/setup, oracle, falsifier, and material dependencies before editing tests or source. Material-risk work expands these into the appendix's stable acceptance/boundary/hypothesis/proof records.

Do not use changed implementation logic as its own oracle. Prefer a caller-visible result plus an independently observed state, protocol, accessibility tree, process/resource effect, persisted query, or external response. Name shared helpers and mocked seams. A primary claim cannot be proven only with its central boundary mocked. Preserve raw sanitized observations and exact exit status at an immutable/content-hashed locator; bind them to the complete candidate, harness, relevant build, configuration, runtime, and environment.

## Routine proof

Routine work still requires outcome-specific evidence, not merely a green repository suite:

- For a bug, freeze one regression harness and demonstrate `base FAIL → candidate PASS`. If the same harness cannot run at base, use an isolated minimal production mutation and require `mutation FAIL → candidate PASS` at the intended assertion, not at compile/setup noise. Remove the mutation and prove it is absent.
- For a non-regression behavior change, exercise the real entrypoint and independently observe the promised outcome plus the consequential reject/recovery path. State why the proof would reject a credible wrong implementation.
- Run the exact affected test selector noninteractively and the repository's prescribed formatting, lint, type, build, and relevant integration gates. Record discovery/execution/skips/retries and exit status; zero tests, watch mode, unexpected skips, or hidden retries do not pass.
- Inspect every changed/deleted/skipped/focused/snapshot test, fixture, mock, timeout, retry, and runner option. Reject weakened assertions, implementation-only hooks, fake producer shapes, or a fixture that omits the triggering condition.
- Use the canonical built entrypoint when runtime wiring can affect behavior. A source runner, mock, screenshot, log, or previously built output proves only the boundary it actually exercised. If the highest safe real boundary is unavailable, name the gap and consequence.

## Review and findings

Self-review the complete actual-base-to-candidate delta, including tests, docs, configuration, dependencies, generated output, packaging, intentional untracked files, and accidental noise. Reconsider scope, invariant ownership, compatibility, privacy/outbound data, error/recovery paths, and whether you would still choose this design from scratch.

Routine work gets one fresh blind whole-delta reviewer. Provide only trusted outcomes/constraints, repository rules, immutable base/candidate coordinates, and the source/tests; withhold author rationale, proof verdicts, suspected findings, and prior conclusions. Require concrete reachable state/input → path → violated contract → impact, contrary evidence, fastest falsifier, and uncovered boundaries. This reviewer is read-only and does not violate the single coordinator/writer condition. If a material candidate or disputed conclusion appears, seal it and continue with the material appendix's Phase 2; otherwise preserve a compact changed-boundary/lens coverage record.

Track every candidate finding until it is fixed, decisively refuted, linked as a true duplicate, routed as a qualifying nonblocking follow-up, or remains visibly open because an authoritative decision is missing. `Pre-existing` is provenance, not disposition. A fix closes only after affected proof and final-delta review. For a localized routine fix, the same still-independent reviewer may inspect the final delta; a material/boundary change upgrades the profile and requires fresh blind coverage.

## Pass rule

Return `pass` only when all acceptance claims and activated material risks have current falsifiable evidence; required regression sensitivity holds; the relevant real entrypoint and repository gates pass; test integrity and the complete candidate were self-reviewed; fresh review covers every changed boundary with no open finding; and no unaccepted proof gap remains.

Return `pass-with-waiver` only when `pass` fails solely because a specifically authorized accountable human accepted each exact remaining finding/gap with named scope, residual impact, and expiry. Preserve the underlying failure/gap and report it. Otherwise return `gap` with the exact missing proof, affected outcome, and risk.

Any effective source/base/harness/oracle/build/config/environment/external-contract change invalidates its dependent evidence. A representation-only commit of byte-identical content rebinds provenance; it does not rerun proof. A material semantic fix or newly exposed boundary upgrades/reopens the affected profile, proof, and review. Stop cosmetic churn once the current candidate passes.
