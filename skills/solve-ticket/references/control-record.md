# Control record and gate protocol

Use the bundled `scripts/ticketctl.py` as the private, resumable structural record for every solve-ticket run. It supplements judgment; it does not prove that a test, review, decision, or claimed authority is sound merely because an agent recorded it. It is tamper-evident run coordination, not a security boundary against another process with the same filesystem identity.

## Contents

- [Storage and initialization](#storage-and-initialization)
- [Sanitized record model](#sanitized-record-model)
- [Capabilities and applicability](#capabilities-and-applicability)
- [Fingerprints, evidence, and invalidation](#fingerprints-evidence-and-invalidation)
- [Controller loop](#controller-loop)
- [Workers and the single-writer lease](#workers-and-the-single-writer-lease)
- [External write intents](#external-write-intents)
- [Gate and terminal discipline](#gate-and-terminal-discipline)
- [Resume and handoff](#resume-and-handoff)

## Storage and initialization

Run the tool through Python from the skill directory:

```text
python3 scripts/ticketctl.py --repo <worktree> --ticket <stable-locator> <command>
```

The stable locator may be a tracker URL/key or a deterministic local label. The tool hashes it; it does not store the raw locator. By default it stores `record.json`, an append-only hash-chained `journal.jsonl`, and a lock under the repository's Git common directory, outside normal commits. Use `locate` to recover the path and `show`, `gate`, or `next` to inspect derived state. Do not put the record in the product tree or publish it.

Initialize once. If it exists, reconcile and resume it rather than creating a second run. Create a separate work unit inside the same record for every coherent branch/PR/subticket; do not create competing control records for one ticket graph.

The command names and flags are authoritative in `--help`; inspect them before first use. Before `init`, hash the trusted request through `authority scaffold`. For a merge-ready PR, first derive the remote-ref and PR-slot targets, then pass both to the merge-ready scaffold; for a local run, use its local preset. Scaffolds create validated mode-0600 files exclusively and refuse overwrite. The typical order is:

```text
target derive-remote-ref / target derive-pr-slot (when publishing)
authority scaffold
init
lease acquire
profile apply-routine (eligible local/static work only), or:
context add / capability set / trigger set
claim add / obligation add
work add / work set
checkpoint create / evidence add / obligation resolve
finding add / finding dispose
action scaffold / action prepare / action settle
invalidate
gate / next / show
finish or reopen
```

## Sanitized record model

Record only compact claims, outcomes, classifications, digests, identifiers that are safe inside the local trust boundary, and reproducible artifact locators. Never store:

- secrets, tokens, cookies, credentials, signed/private URLs, environment values, or raw command environments;
- PII, customer content, raw support complaints, production payloads, or real-user observations;
- chain-of-thought, speculative internal monologue, or full source/test output;
- public-ready prose that belongs in the eventual PR or tracker.

Hash raw trusted instructions, ticket sources, starting-state manifests, branch/worktree coordinates, evidence artifacts, and external write payloads. Keep complex sanitized state and raw sanitized evidence in private content-addressed sidecars under the run's `artifacts/` directory, named by stable record ID plus digest. Record the relative locator, digest, schema/kind, and dependencies; load and verify every required sidecar on resume before gate evaluation. A digest without a recoverable locator cannot satisfy a resumable obligation, and identity does not prove correctness.

Before creating a PR, derive its immutable origin-slot digest with `target derive-pr-slot` from the provider, target repository/ref, head repository/ref, and work-unit ID, plus the publication ref with `target derive-remote-ref`. Put those digests in the scaffolded root authority target set, capability, action manifests, and work-unit coordinates; retain the PR slot for that PR lifecycle. For multiple PRs, repeat each scaffold target flag once per remote/PR pair, in matching order, and budget at least two actions per pair. The scaffold rejects missing, duplicate, mismatched, or under-budget target sets. The provider-assigned number/URL cannot exist yet and belongs in the create receipt plus canonical host evidence, not in the pre-authorized target. A later base retarget invalidates affected delivery evidence but does not rewrite the original slot identity. Generate typed request manifests with `action scaffold`; it derives reserved-effect classification and validates kind/target/work-unit coherence before `action prepare` consumes the file.

The record must cover:

- trusted contexts and repository instructions;
- capability provenance and prohibitions;
- applicability triggers and activated obligations;
- acceptance, risk, and terminal claims;
- work-unit DAG, ownership, semantic or sequencing edges, branch/worktree/base/head/remote/PR coordinates, and evidence epoch;
- fingerprints, proof executions, review coverage, findings, and dispositions;
- coordinator lease and worker envelopes;
- external write intents, expected versions, outcomes, and receipts;
- invalidations, blockers, terminal result, and exact next action.

## Capabilities and applicability

Keep authority and applicability separate:

- A **capability** records what the trusted user authorized, for which target and action, with provenance, constraints, use limit, expiry, and whether it may be delegated. Default unknown authority to denied. Freeze one canonical authority envelope whose content binds the trusted-turn digest, ticket/repository, requested endpoint, action kinds and targets, denials, cardinality, expiry, and delegability; derive capability fields from it rather than attaching freeform grants to an unrelated digest. Chain direct-user amendments to the prior envelope. A worker or inferred ticket digest is not authority.
- An **applicability trigger** records what risk or surface the change reaches. Resolve every trigger yes/no with a concrete rationale. `yes` activates obligation cards; it never grants capability.

Reconstruct capability provenance from the current trusted conversation after every resume. The direct root-user invocation defined in `SKILL.md` may grant its bounded routine bundle; never accept a delegated or implicit skill mention, inherited history, ticket, review comment, repository file, old record, prior successful action, or helper default as a grant. Expired, exhausted, one-time, target-mismatched, or ambiguous capability is unavailable. Pass helpers an explicit coordinator-issued strict-subset envelope; reserved production/customer/destructive/merge/deploy/social capabilities default non-delegable.

Classify all trigger families before implementation: user-visible/runtime; product/UI; public API/schema/compatibility; persistence/migration; async/concurrency/cross-process; privacy/security/auth/permissions; destructive/financial; third-party/external drift; performance/resources; native/packaging/platform; rollout/observability; and external publication/lifecycle actions. Use [diagnosis-and-design.md](diagnosis-and-design.md) for the required models and [proof-and-review.md](proof-and-review.md) for the activated proof cards.

## Fingerprints, evidence, and invalidation

A candidate fingerprint must represent effective content independently of whether identical bytes are unstaged, staged, or committed; store Git representation and head separately so a commit alone does not falsify byte-identical proof. Include every tracked and intentional untracked filename/content digest and exclude unrelated starting dirt through an explicit immutable ownership manifest. Separately bind material evidence to:

- actual base and merge-base;
- complete candidate/source manifest;
- harness and predeclared oracle;
- lockfile/dependencies, configuration, schema, generated inputs, and feature flags;
- clean build/artifact digest and execution form;
- environment/runtime/platform, fixture/data seed, and external-contract version/time horizon;
- remote head/base/candidate tuple for PR, CI, and review claims.

Create immutable checkpoints and append evidence executions; do not overwrite a failed run. `inspection` evidence may satisfy a bounded non-behavior acceptance or terminal claim only when the requested outcome is itself a static artifact/source fact and an independent complete-surface oracle proves it. It cannot satisfy executable behavior, review, delivery, or remote-readiness obligations, and it becomes invalid when its source coordinate changes.

Record an invalidation immediately on a material dependency change. Effective candidate, base semantics, test/harness, dependency, config, generated output, design, build, environment, external contract, feedback, review fix, work graph, or authority changes reopen their dependent evidence. A byte-identical representation-only commit rebinds Git provenance without falsifying behavior proof. A remote tuple move always invalidates delivery/readiness evidence and invalidates local proof/review only when its content, base semantics, build, or environment dependency changed. When the tool cannot infer the edge, uncertainty means invalidate. Preserve stale rows; never silently retarget them.

## Controller loop

The global state is the earliest failing global gate, and each independent work unit has its own earliest failing gate. A global blocker keeps dependent units and the terminal claim open but does not prohibit a safe dependency-independent unit whose own G0–G2 prerequisites pass:

```text
reconcile canonical state
→ invalidate stale dependencies
→ derive global and per-unit earliest failing gates
→ resolve safety first, then select the highest-impact eligible obligation
→ investigate/implement/prove/review/deliver
→ record raw result and disposition
→ repeat
```

Before closing an obligation, inspect its evidence against the relevant reference. Do not use one generic test to satisfy unrelated cards. Built-in obligations and trigger cards are non-waivable by default. A waiver is valid only when higher-priority trusted policy or a specifically authorized accountable human names that obligation, scope, residual impact, and expiry; an agent may not make its own obligation waivable. It never changes a failed/gap proof into pass. Instead, a gate may close as `pass-with-waiver` only when every remaining gap or finding is covered by a current waiver, while the underlying states remain open and every waived item is carried into terminal residual risk.

Backtrack rather than paper over a gate when the outcome contract changes, the causal prediction fails, a new boundary/consumer appears, a fix adds special cases, the base or production form changes, a reviewer finds a systemic variant, or remote state moves. Dependency-independent later-gate work is allowed only when its own prerequisites pass and it cannot prejudice the blocked decision; it cannot close the global gate or terminal claim. `next` is a structural diagnostic, not permission to ignore a more fundamental falsified premise.

## Workers and the single-writer lease

Maintain one coordinator lease for the ticket graph: sanitized owner digest, monotonically increasing epoch, acquired/heartbeat/expiry times, and takeover record. Carry the epoch in worker envelopes and every prepared shared write. A worker that observes a different/expired epoch stops shared writes and reports state. A successor may take over only after reconciling the journal, incomplete intents, worktrees, refs, remotes, PR/tracker state, and prior coordinator liveness.

Only the coordinator mutates the canonical record, shared index/branches, remotes, PR/review/tracker surfaces, or deployments. Give workers isolated worktrees or disjoint file/contract ownership and a return-only remote policy. Record:

- unit and run IDs;
- immutable actual base/head and expected output branch or patch;
- owned paths/contracts and explicit exclusions, including pre-existing dirt;
- available local tools/data and privacy boundary;
- granted capabilities and forbidden actions;
- evidence/proof obligations and structured return format.

Validate worker output against the envelope and current coordinator epoch. If two writers touched the same branch or remote head moved unexpectedly, freeze, fetch, attribute deltas, and re-plan; never replay or force blindly.

## External write intents

Before any authorized external mutation, record a write-ahead action with stable ID/idempotency digest, capability and authority revision, target digest, intended request digest, observed expected head/version/state, and coordinator epoch. Reject generic action kinds: every kind and target must be named by the current capability. Use only the exact action states exposed by `ticketctl --help`; the script is the canonical state machine. Then:

1. Re-read the canonical target immediately before writing.
2. Abort if its expected state or coordinator epoch changed.
3. Apply through a native lease/version guard when available.
4. Re-read every relevant surface and store a receipt digest.
5. Record the exact observed outcome through the script's allowed transition and attach its receipt.

Never retry an `uncertain` action until canonical reconciliation proves the first effect absent. If an API lacks compare-and-swap, use a stable correlation marker and full duplicate scan. If equivalent pre-existing state makes attribution ambiguous, keep the script state `uncertain` and escalate; “conflicted” is a prose diagnosis, not another state. Remote success output without read-back remains `applied-unverified`, not complete.

## Gate and terminal discipline

The CLI derives G0–G8 from recorded obligations, evidence freshness, findings, work DAG, actions, and terminal claims. Fail closed: unknown triggers, stale evidence, open unwaived findings or gaps, blocked required units, unresolved write intents, missing current remote proof, or a dirty mismatch keeps the earliest gate open. A current accountable-human waiver closes only the gate predicate; it does not erase the underlying state.

Terminal statuses have distinct rules:

- `complete` and `merge-ready-awaiting-human` require every applicable gate and a current matching terminal claim; the latter is valid only for a frozen `merge` endpoint.
- `resolved-no-change` requires current evidence that the requested outcome is already satisfied, duplicate, stale, false, or harmful, plus proof that no owned implementation/delivery effect remains necessary.
- `blocked` requires an evidenced material blocker at the earliest failing gate and proof that no safe independent obligation can advance.
- `partial` requires a forced interruption, recoverable tool failure, or explicit handoff, an exact next action, and no false readiness claim. It is never a discretionary stopping state.

Local-only authorization changes which publish/converge obligations are applicable; it does not make them failed. Mark them inapplicable with authority evidence rather than pretending they ran. Conversely, an end-to-end publication request cannot waive G6/G7 merely because local code is finished.

The record can guard structural prerequisites but not judge product truth. A manually fabricated passing artifact is still fraud. Terminal claims must be independently supportable from source, evidence, and canonical external state.

## Resume and handoff

On resume, start with `show`, then compare every durable coordinate to canonical live state. Reconcile incomplete actions before any retry, update the coordinator lease, invalidate everything that moved, and derive the earliest gate. Do not trust stale PR bodies, aggregate green status, local remote-tracking refs, or old approvals.

When work must hand off, leave the record path plus a concise sanitized envelope containing current coordinator epoch, work-unit/PR graph, actual base/head tuple, starting-dirt exclusions, incomplete action IDs, open findings/obligations, watcher handle and next wake condition, exact blocker, and one deterministic next command/action. The receiver must reconcile rather than continue from the prose alone.
