# Material-risk proof and review

Use this appendix only when the compact [proof router](proof-and-review.md) selects the material-risk profile. Turn each implementation claim into falsifiable, revision-bound evidence and run review as an attempt to break those claims, not as a checklist or vote. Keep branch, PR, CI-wait, and tracker mechanics in [delivery](delivery-and-lifecycle.md).

## Contents

- [Read-only discovery](#read-only-discovery)
- [Proof record](#proof-record)
- [Production-shaped execution](#production-shaped-execution)
- [Test integrity audit](#test-integrity-audit)
- [Risk obligation cards](#risk-obligation-cards)
- [Independent review](#independent-review)
- [Empirical validation](#empirical-validation)
- [Finding ledger](#finding-ledger)
- [Review-fix semantic-delta audit](#review-fix-semantic-delta-audit)
- [Finding convergence](#finding-convergence)

## Read-only discovery

During [diagnosis](diagnosis-and-design.md), complete these proof-specific records before editing source or tests. Run inspections and baseline experiments without changing ticket-owned code; allow only disposable outputs and record them separately from pre-existing dirt.

1. Resolve the actual base and starting snapshot. Inventory tracked, untracked, staged, and generated state so later evidence cannot absorb unrelated work.
2. Locate the production entrypoint, build/package path, runtime configuration, and every existing or anticipated changed producer, contract, and consumer. Read implementation and call sites, not only the proposed diff.
3. Locate existing tests, fixtures, harnesses, mocks, test selection rules, and prior evidence. Determine which executable path each test bypasses.
4. Reproduce the baseline or the nearest controlled negative case. Preserve the raw observation even when the reproduction contradicts the ticket.
5. Assign stable `A-###` IDs to acceptance claims. Build the boundary-and-hypothesis map below, predeclare material proof claims, and activate risk cards before implementation changes can bias the oracle.

Use one row per changed boundary and materially plausible failure hypothesis. Assign stable `B-###` and `H-###` IDs; repeat a boundary ID when several hypotheses cross it.

| Acceptance ID | Boundary ID | Hypothesis ID | Producer → contract → consumer | Changed assumption | Reachable falsifying input/state | Planned proof/review owner |
| --- | --- | --- | --- | --- | --- | --- |
| A-001 | B-001 | H-001 | concrete runtime path | behavior that may differ | condition that would expose a defect | proof claim and review assignment |

Count coverage by mapped acceptance claims, boundaries, and hypotheses, never by files, tests, reviewers, or review rounds. Add a row when investigation or a finding exposes a new producer, consumer, trust boundary, persisted representation, process, artifact, or lifecycle transition. Append materiality/applicability changes with their evidence; never erase the earlier classification.

Do not edit until the actual base, production-shaped entrypoint or evidence that no executable artifact is affected, highest-risk hypotheses, and a credible falsifier for the primary outcome are known. Record an explicit discovery gap when the environment makes one unknowable.

## Proof record

Separate immutable proof claims from their executions. Seal and fingerprint each claim before its first execution; never revise an oracle after observing a result or overwrite a failed run.

| Claim ID | Claim and acceptance/boundary/hypothesis/obligation IDs | Controlled setup and production-shaped entrypoint | Independent oracle and shared dependencies | Frozen run-valid, pass, fail, and gap predicates | Sensitivity obligation |
| --- | --- | --- | --- | --- | --- |
| P-001 | one observable outcome at `A-###` / `B-###` / `H-###` / `O-###` as applicable | input, state, environment, and exact action | independently derived measurement plus any shared plumbing | mutually exhaustive decision rules declared before execution | required or exempt with reason |

| Execution ID | Claim ID | Subject, harness, source/build, and environment fingerprints | Raw sanitized observation and immutable digest/locator | Verdict | Validity/invalidation reason |
| --- | --- | --- | --- | --- | --- |
| E-001 | P-001 | immutable identities for exactly what ran and observed it | stdout, trace, query, capture, samples, exit status, and artifact locator | pass, fail, or gap | current, or the later change that made it stale |

Enforce the row contract:

- State one falsifiable claim. Split rows whose observations can pass independently.
- Name the highest real boundary crossed. Do not label a unit harness as end-to-end.
- Control the initial state, input, environment, clock/randomness, and relevant configuration. Record uncontrolled variables.
- Use an independent oracle: observe the effect through a different mechanism from the code that produced it. Prefer a persisted-state query, protocol capture, accessibility tree, process/resource observation, or external response over the implementation's own success flag or log message. List shared helpers, schemas, generators, mocks, and algorithms; require a second independently derived oracle or record `gap` when shared changed semantics can make producer and oracle agree incorrectly.
- Freeze valid-run preconditions and mutually exhaustive `pass`, `fail`, and `gap` predicates before execution. State the exact observation, threshold, invariant violation, or missing side effect that produces each verdict; absence of the chosen failure signal is not itself a pass.
- Bound universal or negative claims. Predeclare the input/state partition, sink set, seeds/schedules/repetitions, observation window or quiescence condition, detection floor, and numeric threshold; otherwise narrow the claim to the exercised bound or record `gap`.
- Preserve the raw, sanitized observation and exit status. Link or locate it; do not paraphrase it into “works.” Keep secrets and user data out of evidence artifacts.
- Bind the observation to separately fingerprinted subject and harness plus the immutable source snapshot and exact tested artifact. Use a commit/tree identity for a clean tree or a content-addressed snapshot/diff manifest for dirty state; never use “current working tree” as a fingerprint. Include relevant lockfile/dependency, configuration, platform/runtime, feature-flag, schema, and external-contract identities.
- Keep raw observations at an immutable or content-hashed locator so a later run cannot overwrite the evidence behind an earlier verdict.
- Separate observation from interpretation. Let another reader reach the verdict from the recorded oracle and raw data.

Keep `P-###` stable while its claim, boundary/hypothesis, setup, oracle, or decision rules remain identical. Create a new claim when any changes. Append a new `E-###` for every rerun and retain invalidated executions.

### Demonstrate sensitivity

Prove that a regression check distinguishes the intended semantics:

1. Require sensitivity for every primary regression and changed material-risk invariant. Record inability to demonstrate required sensitivity as `gap`.
2. Freeze the candidate harness, input, fixture, selector, oracle, and decision rule. Swap only the subject artifact between actual base and candidate head; comparing each revision's own tests does not establish sensitivity. Keep any base adapter minimal and prove it cannot affect the input, oracle, or verdict. Record `base FAIL → head PASS`.
3. When the frozen harness cannot exercise base because the intended contract changed, predeclare one minimal production-subject mutation tied to the hypothesis: restore the faulty behavior, invert the fixed predicate, bypass the new effect, or corrupt the relevant mapping. Never mutate the test, fixture, selector, oracle, or build configuration.
4. Run the mutation only in an isolated disposable snapshot. Record its diff/hash, prove setup completed and the targeted branch ran, require the declared oracle failure before unrelated failure, then run the byte-identical harness against unmodified head. Verify the final candidate/artifact excludes the mutation and record `mutation FAIL → head PASS`.
5. Reject compile failures, fixture-load failures, unrelated exceptions, and timeouts as sensitivity. Record `not shown` when no comparison is credible; do not call that claim regression proof.

Use base/head measurement for performance and resource claims. Use mutation only to show test discrimination, not to manufacture a performance baseline or compatibility claim.

## Production-shaped execution

For executable or build-affecting claims, exercise the path that real inputs use: the same exported command/API/UI entrypoint, loader, validation, serialization, process boundary, runtime defaults, and built assets. Use the highest safe real boundary; label narrower substitutes precisely.

Materialize every tracked and intentional untracked build input in an isolated temporary worktree/export; never clean the user's working tree in place. Start with absent verified outputs and empty or explicitly fingerprinted caches, install from the frozen lockfile without mutating it, and build through the repository's production command. Record pre/post source manifests, build command/configuration, a recursive artifact manifest/digest, runtime/platform, and any unavoidable shared cache.

Copy or install the artifact outside the repository and run it with source/dev resolution unavailable whenever workspace fallback could mask a defect. Record executable, module, and resource roots; invalidate the run on workspace fallback or post-build artifact mutation. A dev server, source runner, unit import, mocked transport, or previously built output does not establish a production-wiring claim.

Start the scenario from realistic clean state. Exercise one success path and the consequential reject/recovery path through the entrypoint. Observe both the user/caller result and an independent downstream effect. Re-run after restart when persistence, registration, worker loading, cleanup, or startup wiring matters.

Treat an unavailable production-shaped path as a named evidence gap. Record the attempted setup, blocker, nearest substitute, claims left unproven, and risk consequence; do not dilute the entrypoint until the row passes.

## Test integrity audit

Audit the tests before accepting their results:

1. Diff every added, changed, deleted, skipped, quarantined, focused, or snapshot-updated test and every affected fixture, mock, helper, timeout, retry, and runner configuration.
2. Trace each material assertion to the boundary map. Identify mocks or shared helpers that bypass the changed branch, reproduce the implementation's algorithm, or make producer and oracle fail together.
3. Run the exact selector non-interactively. Record discovered, executed, passed, failed, skipped, retried, and quarantined counts plus the exit status. Treat zero discovered tests, watch-mode output, hidden retries, or unexpected skips as failure.
4. Demonstrate base/head or mutation/head sensitivity for every proof claim marked `required`. Confirm the expected assertion fails, not merely setup.
5. Verify realistic producer/consumer shapes, defaults, ordering, and error objects. Reject fixtures that omit the field, scale, encoding, locale, permission, or lifecycle state that makes the production path risky.
6. Inspect weakened assertions, broadened tolerances, unconditional snapshot acceptance, swallowed errors, fake timers, excessive mocks, and implementation-only hooks. Require a separate oracle when production and test code share the changed helper.
7. Run the narrow check and highest applicable safe integration boundary. If that boundary is unavailable, record a `gap` rather than silently lowering the claim. Use repository-wide gates as corroboration, not as a substitute for claim-specific proof.

Record the audit as proof claims/executions or concise notes attached to them. Preserve a failing raw observation whenever the audit detects a false green.

## Risk obligation cards

Open every card whose trigger is reachable. Assign stable `O-###` IDs to each listed obligation that the changed path can reach and mark each `required`, evidence-backed `not applicable`, or `gap`. Fill its claim, boundary, controlled setup, oracle, falsifier, raw artifact, and proof IDs before calling it closed. Stay within the controller's authority and use local, synthetic, digital-twin, sandbox, or dedicated test state; activating a card never authorizes production access or a real destructive effect.

### Runtime and UI card

- Open for user journeys, stateful runtime behavior, CLI/API behavior, background work, error recovery, or accessibility-visible changes.
- Start from a clean realistic profile/state and enter through the production-shaped UI, command, or API. Exercise primary, deny/invalid, interruption, retry, cancellation, restart, and nearest-regression paths as applicable.
- Observe visible/caller state plus independent network, persistence, process, accessibility-tree, focus/keyboard, console/error, and cleanup effects. Include realistic content, localization, zoom/theme, and responsive states when the changed boundary can affect them.
- Falsify on false success, stale/duplicated state, stranded loading, inaccessible action/status, lost context, unsafe retry, unhandled runtime error, or effect that exists only in the component/harness.

### Public API and schema card

- Open for public APIs, schemas, serialized contracts, generated clients/types, or externally consumed request and response shapes.
- State the compatibility and versioning contract, exact released/public shape, supported old/new producer-consumer combinations, and unknown or malformed data policy. Exercise representative producers and consumers through their real validation and serialization boundaries.
- Regenerate and inspect every derived artifact, prove it corresponds to the frozen source schema, and verify checked-in/generated outputs and downstream compilation or contract tests where applicable.
- Falsify on an undocumented breaking change, released shape drift, stale generated output, an unsupported old/new combination, a representative consumer failure, or unknown external data bypassing validation or being silently misinterpreted.

### Performance and resource card

- Open for a latency, throughput, responsiveness, memory, CPU, I/O, startup, bundle-size, or scaling claim.
- Predeclare the user-visible claim, budget, representative corpus/scale, correctness invariant, host/runtime/build controls, warm/cold policy, repetitions, percentiles/tail/worst statistic, and raw sample format.
- Measure actual base and head under matched conditions, preferably interleaved to expose environmental drift. Capture individual samples and resource ceilings; report variance and outliers rather than only an average.
- Falsify on budget breach, breach of the predeclared statistical/practical threshold, unbounded growth within the declared observation bound, shifted work that harms another resource, or incorrect output under load. Restrict a microbenchmark verdict to its component boundary.

### Concurrency and lifecycle card

- Open for async ownership, queues, workers, IPC, retries, cancellation, shared state, or distributed/process lifecycle behavior.
- State actors, durable and volatile state, identity/epoch/idempotency key, allowed transitions, safety/liveness invariants, retry budget, backpressure, and cleanup/recovery owner. Prove that an ownership identity is unique at the actor's actual isolation scope; a process identifier, thread-local set, lock, timestamp, or liveness probe is not sufficient when runtimes share it or identities can be reused.
- Define overlapping-operation semantics instead of assuming serialization: reject, queue, merge, first-writer-wins, or last-commit-wins. Prove the declared outcome at the atomic commit boundary; a pre-commit check followed by an unguarded write cannot establish first-writer-wins.
- Name the irreversible commit point and define truthful caller-visible outcomes on both sides of it. A post-commit cleanup/release failure must not be reported as though the primary effect did not occur or were safely retryable; return or reconcile committed-with-warning/unknown outcomes explicitly.
- Drive deterministic interleavings or fault injection for same-process workers, multiple processes, duplication, delay, reordering, cancellation, lost wakeup, stale or reused owner identity, bounded-queue pressure, process death, restart, retry exhaustion, and partial success. Avoid sleeps as synchronization proof.
- Falsify on double effect, lost work, post-cancel effect, deadlock/starvation, unbounded resource retention, stale ownership, ambiguous completion, or failure to converge after recovery.

### Migration and persisted-data card

- Open for schema, durable state, serialized format, cache compatibility, or release-order changes.
- Exercise clean creation and upgrade from representative historical fixtures at realistic scale. Cover old/new reader-writer combinations, version skew, constraints, locking, interruption, resume, repeated application, and partial state.
- Use independent integrity queries, checksums, counts, or round trips. Execute the declared rollback or forward-repair path; never imply rollback when only forward recovery is possible.
- Falsify on loss, duplication, silent reinterpretation, partial visibility, non-idempotent retry, incompatible release order, unacceptable lock/resource cost, or unrecoverable interruption.

For filesystem replacement, include destination identity and metadata in the contract: symlink/hardlink behavior, ownership, mode, ACL/xattrs where the platform exposes them, case and path aliases, parent retargeting, same-process/thread/process writers, and the difference between process crash and power loss. Preserve or explicitly reject unsupported metadata/path forms before effects; never infer full metadata preservation from mode bits alone.

### Privacy, security, and destructive-action card

- Open for identity/content data, credentials, authn/authz, permissions, remote sinks, telemetry, logs, URLs, exports, deletion, money, or irreversible third-party effects.
- Trace inputs through every trust boundary and outbound sink. Use synthetic or dedicated safe data. Exercise least privilege, tenant/identity separation, deny paths, malformed input, secret redaction, error serialization, replay, retry, partial effect, and unknown outcome.
- Observe exported payloads and actual side effects independently of application success messages. Prove confirmation, idempotency or explicit reconciliation, auditability, and recovery before repeating a destructive request.
- Falsify on unauthorized reachability, sensitive plaintext leaving its allowed boundary, secret-bearing evidence, confused identity, overbroad permission, false confirmation, duplicate destructive effect, or unsafe retry after an unknown result.

### External-drift card

- Open for third-party APIs/pages, browser selectors, undocumented behavior, webhooks, protocol/version negotiation, or externally controlled schemas.
- Exercise a sanctioned sandbox, digital twin, fixture captured from the current contract, or dedicated test account. Cover representative locale/variant, pagination, malformed/unknown fields, empty/partial response, auth expiry, rate limit, timeout, retry headers, and capability/version mismatch.
- Capture sanitized request/response or DOM/protocol shape and its date/version. Keep the parser permissive only where the contract permits and strict at the product invariant.
- Falsify on selector/schema dependence on presentation text or incidental ordering, silent partial processing, incompatible unknown values, unsafe replay, stale fixture-only success, or external failure reported as product success.

### Packaging and obfuscation card

- Open for bundling, exports, code generation, dynamic imports, workers, native modules, assets, minification/obfuscation, installers, or platform-specific behavior.
- Produce a clean production artifact from the candidate snapshot. Inspect its manifest/contents and launch that exact artifact without source-tree or development fallbacks on every materially distinct runtime/platform path available. Record each unavailable material path as a proof gap rather than silently narrowing the platform matrix.
- Exercise dynamic registration/import, worker/process startup, assets, native dependencies, permissions, install/upgrade/startup, and string/reflection contracts under the shipped obfuscation/minification settings. Compare unobfuscated behavior only as diagnostic evidence.
- Falsify on missing or stale artifact, development-only resolution, tree-shaken registration, changed reflective/string identity, absent native/asset payload, source-map or secret leakage, platform-only startup failure, or packaged behavior that diverges from the clean build claim.

### Rollout and observability card

- Open for feature flags, cohorts, staged release, telemetry, logs, alerts, dashboards, canaries, operational fallbacks, or code whose safe release depends on detecting degradation.
- State default/unknown flag behavior, cohort and version-skew semantics, privacy-safe success/failure signals, expected baseline, alert threshold and window, owner, and rollback or forward-fix trigger. Verify signals describe the real terminal outcome rather than an intermediate attempt or aggregate false success.
- Exercise off/on, missing/stale configuration, partial rollout, rollback/disable, and signal-loss paths in synthetic or authorized environments. Inspect the actual exported telemetry/alert payload and ensure sensitive input cannot cross its allowed boundary.
- Falsify on unsafe default, cohort inconsistency, unverifiable rollout, alert blindness/noise above the declared bound, PII leakage, rollback that cannot restore a safe state, or a success signal emitted before durable settlement.

## Independent review

Review the content-addressed candidate source read-only against its actual base. Run experiments only in isolated disposable state; let only the coordinator mutate the canonical proof record and finding ledger. Count complete changed-boundary/hypothesis coverage, never reviewers.

### Review lenses

Partition Phase 1 by subsystem/source coordinates and the applicable lenses below, not by the author's boundary map or hypotheses:

- outcome, integration, UX, accessibility, and localization;
- correctness, edge/error/recovery state, concurrency, lifecycle, and cleanup;
- privacy, security, permissions, secrets, destructive effects, and data integrity;
- test integrity, runtime evidence, performance/resources, compatibility, migrations, packaging, and operations;
- architecture, repository idioms, simplicity, types, comments/docs accuracy, scope, and bloat.

Combine lenses only when the reviewer can inspect the assigned surface deeply. Partition a broad surface further; a constrained, failed, or timed-out assignment remains uncovered.

### Phase 1: blind discovery

Start reviewers in fresh context after implementation self-review. Provide only trusted outcome/constraints, repository rules, exact immutable base/candidate coordinates, assigned subsystem/source coordinates and lens, and access to the source and tests. Withhold the author's boundary/hypothesis map, rationale, preferred design, proof verdicts, suspected findings, prior reviewer conclusions, and finding dispositions.

Require each reviewer to:

1. Reconstruct the behavior and changed boundary map from source.
2. Trace assigned producers, consumers, callers, failure paths, and tests beyond the diff.
3. Generate concrete candidate findings as reachable input/state → execution path → violated contract → observable impact.
4. State contrary evidence inspected and the fastest falsification experiment for each candidate.
5. Return uncovered boundaries and unavailable checks, even when no candidate survives initial inspection.

Seal the Phase 1 input and output fingerprints before revealing author evidence. Reconcile the reviewer's independently reconstructed map with the author's map, ingest every frozen candidate into the canonical ledger as a stable `F-###`, and add every newly exposed boundary/hypothesis. A reviewer exposed to implementation discussion or prior conclusions provides a second pass, not blind coverage; label it accurately.

### Phase 2: adversarial falsification

Reveal the proof record, raw artifacts, relevant design rationale, and full existing finding ledger only after Phase 1 candidates are ingested. Ask the reviewer to disprove both its candidates and the author's passes:

- Trace reachability and contract ownership; inspect complete callers and producer/consumer shapes.
- Run the smallest decisive experiment where safe. Compare the raw result with the predeclared oracle and falsifier.
- Try the boundary values, failure transition, alternate consumer, stale state, restart, or mutation most likely to turn a pass into a fail.
- Return each candidate as `survives`, `refuted`, or `unresolved`, with evidence. Let the coordinator validate that result, keep unresolved findings at the controller's single open disposition with the exact uncertainty explained in the linked artifact, or apply a terminal `refuted` disposition; do not use confidence, reviewer agreement, or absence of time as a disposition.
- Add newly exposed hypotheses to the boundary map and proof record.

Maintain a coverage map:

| Boundary/hypothesis | Reviewer and phase | Source/call paths inspected | Experiment or refutation | Coverage gap |
| --- | --- | --- | --- | --- |
| `B-###` / `H-###` | fresh reviewer, Phase 1+2 | exact producer and consumers | raw result or decisive source evidence | none or explicit limitation |

After Phase 2, complete this closure matrix:

| Acceptance/hypothesis | Boundary | Risk obligation | Current proof execution | Phase 1/2 coverage | State or gap |
| --- | --- | --- | --- | --- | --- |
| `A-###` / `H-###` | `B-###` | `O-###` or evidenced n/a | `P-###` / `E-###` | review assignment/result | closed or exact gap |

Cover every acceptance claim, changed contract boundary, materially affected failure/lifecycle hypothesis, activated obligation, and unchanged consumer that depends on a changed assumption. Add a closure row rather than inferring coverage from counts.

## Empirical validation

Use a fresh empirical validator for novel or high-impact runtime/UI, performance, concurrency, migration, privacy/security/destructive, external-drift, and packaged-artifact claims. Keep this role separate from the implementation author and code reviewer; if no independent validator is available, record the missing independence as a `gap` for the controller.

1. Freeze the proof claim's setup, oracle, and falsifier before dispatch.
2. Give the validator the exact artifact, environment setup, controlled input, entry action, capture instructions, and safety boundary. Withhold the author's observed result and preferred conclusion. Withhold the expected numeric/result value until the raw observation is sealed unless the action cannot be executed safely without knowing its bound; record that limitation.
3. Require a clean-state execution through the production-shaped entrypoint. Have the validator return raw sanitized artifacts, environment/build fingerprints, deviations, and observations without translating them into the author's narrative.
4. Compare the sealed observation to the predeclared oracle. Investigate disagreement; never average the results.

Label same-context re-execution, static review, or inspection of author-selected screenshots as corroboration, not independent empirical validation.

## Finding ledger

Assign stable `F-###` IDs when the coordinator ingests a Phase 1 candidate and never renumber, delete, or silently rewrite them. Preserve refuted and duplicate findings so later rounds can distinguish recurrence from rediscovery. Record origin (`introduced`, `pre-existing`, or `unknown`) separately from disposition.

The controller has one open finding state: `disposition: null`; that is the only structural fact gates and terminals consume. At ingestion, the sanitized summary may label the uncertainty as `candidate`, `validated`, or `decision-needed`, but those are descriptive annotations, not controller states or required transitions. Keep later validation or decision evidence in content-addressed proof/review artifacts until the finding receives a terminal disposition. Terminal dispositions are `fixed`, `refuted`, `duplicate`, `follow-up`, and `accepted-residual`.

| ID | Found at fingerprint | Boundary/hypothesis | Reachable scenario and violated contract | Severity/impact | Raw evidence | Open reason or terminal disposition | Fix fingerprint | Invalidated proof/review IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | immutable reviewed snapshot | `B-###` / `H-###` | input → path → wrong observation | blocker, major, or minor | locator or decisive source coordinates | `open` (`disposition=null`) or a terminal disposition | immutable snapshot or n/a | `P-###`, `E-###`, coverage rows |

Preserve every material finding observation and disposition in content-addressed artifacts plus the controller journal; never rewrite earlier evidence:

| Transition ID | Finding ID | From → to | Candidate/disposition fingerprint | Evidence and rationale | Actor/time |
| --- | --- | --- | --- | --- | --- |
| D-001 | F-001 | open → fixed | immutable source, build, contract, and evidence identities | decisive fix/proof/review evidence | coordinator identity and timestamp |

Apply dispositions with evidence:

- Keep `disposition: null` while reachability, contract, impact, remediation, or an authoritative decision remains unresolved. The linked artifacts—not a second shadow state machine—explain what is known and the next falsifier or decision.
- Mark `fixed` only with the root cause, fix fingerprint, sensitivity evidence, rerun proof rows, and focused re-review. A code edit alone is not closure.
- Mark `refuted` only with the controlling contract plus decisive call-path or empirical evidence. “Cannot reproduce,” author intent, or reviewer disagreement is insufficient.
- Mark `duplicate` with the canonical finding ID and confirm the scenarios share one root invariant.
- Record `pre-existing` as provenance only after observing the same behavior at actual base. Keep a separate open/fixed/follow-up disposition because pre-existing does not mean irrelevant.
- Route only verified, nonblocking, non-branch-introduced findings to [delivery follow-ups](delivery-and-lifecycle.md#shape-the-work-and-pr-graph); keep anything required for current acceptance or safety open.

Derive severity from reachable impact, blast radius, reversibility, and detectability. Do not inherit a reviewer's label without validation. Keep human-authorized risk acceptance separate; never turn a proof `fail`/`gap` or validated finding into `pass`/`fixed` because it was accepted. When evidence behind `fixed` or `refuted` invalidates, append a transition back to the earliest supported state.

## Review-fix semantic-delta audit

After every review fix, compare the previously reviewed fingerprint with the new candidate; do not inspect only the intended hunk.

1. Enumerate every semantic delta, including source, tests, fixtures, generated output, schemas, configuration, dependencies, and build/package behavior.
2. Map each delta to the finding/root invariant it resolves. Identify unrelated behavior, weakened tests, moved policy, new consumers, changed defaults, and newly activated risk cards.
3. Re-run every proof row whose setup, subject, oracle, artifact, or assumption can observe the delta. Rebuild cleanly when shipped code or build inputs changed.
4. Give every final semantic source, test, fixture, configuration, generated, dependency, or build delta fresh blind incremental review: provide the new delta plus its surrounding invariant to a fresh reviewer using Phase 1 input restrictions, ingest candidates, then run focused Phase 2. Use focused informed re-review alone only for a proven nonsemantic format/metadata change.
5. Run a concise whole-diff self-review at the new fingerprint. Restart full Phase 1 across the affected surface only for a material redesign or evidence of a systemic same-class defect.

Treat any unmapped semantic delta as accidental until justified. Remove it, prove it, or return it to review scope.

## Finding convergence

Model invalidation as a dependency chain:

`source/base/config/external contract → clean build artifact → proof executions → review coverage → finding dispositions`

Record explicit dependency edges from every execution, review coverage row, and finding transition to its source/base, subject, harness, artifact, configuration, environment, and external-contract fingerprints. Invalidate descendants whenever a dependency changes or its equality is uncertain:

| Change | Invalidate and redo |
| --- | --- |
| Source, test, fixture, schema, config, dependency, or generated change | affected build, proof rows, sensitivity, semantic-delta audit, and focused review |
| Actual base move or rebase | base/head comparisons, whole-diff boundary map, affected builds, and review whose reachability changed |
| Rebuild or different runtime/platform/flag | every runtime observation not tied to the new artifact/environment |
| New boundary, risk trigger, or external-contract version | corresponding obligation card, proof rows, and review coverage |
| Semantic review fix | affected executions plus fresh blind incremental Phase 1 and focused Phase 2; restart full Phase 1 for material redesign/systemic failure |
| Time-sensitive external or performance environment drift | stale live measurements and contract captures |

Preserve evidence only when immutable fingerprints and material assumptions remain identical; record that determination rather than assuming it. Seal one final accepted candidate fingerprint and reopen the gate after any effective input changes.

Return exactly `pass`, `pass-with-waiver`, or `gap`. Return `pass` only when:

- every acceptance claim and material-risk hypothesis has a current decisive proof execution with verdict `pass`;
- every proof claim whose sensitivity obligation is `required` demonstrates base/head or valid mutation/head sensitivity;
- the production-shaped entrypoint has been exercised from a clean build when runtime wiring can affect the outcome;
- the test integrity audit is current and every required risk obligation is closed by a current passing proof execution;
- fresh two-phase review covers the mapped boundaries/hypotheses, and required empirical validation is current;
- the closure matrix contains no uncovered row or `gap`;
- every finding has an evidence-backed terminal disposition, with zero findings whose disposition is `null` regardless of descriptive uncertainty or severity;
- the final semantic-delta audit accounts for the entire current candidate and all invalidated evidence has been rerun.

Return `pass-with-waiver` only when `pass` fails solely because a specifically authorized accountable human—not the agent or controller—accepted each remaining finding or proof/review gap with named scope, rationale, residual impact, and expiry. Keep underlying `fail`/`gap` executions unchanged, disposition each accepted finding as `accepted-residual`, and return it as terminal residual risk without rewriting the evidence that made it open. A critical safety/privacy/data-loss gap cannot support a positive terminal unless the trusted user explicitly accepts that exact risk. Otherwise return `gap` with exact IDs and risk consequences to the [controller](../SKILL.md#derived-gate-chain).

Stop review churn at `pass` or authorized `pass-with-waiver`; additional rounds without a new hypothesis, invalidation, or semantic delta add activity rather than evidence.
