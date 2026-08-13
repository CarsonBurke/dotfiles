# Delivery and lifecycle

Use this reference for the semantic decisions and observable pass conditions of G6–G8. Use [control-record.md](control-record.md) and `ticketctl --help` as the sole authority for record storage, coordinator leases, worker envelopes, action fields/states, invalidation, resumption, and guarded terminal transitions. A filled record is not evidence; verify every claim against repository or canonical remote state.

## Contents

- [Enter delivery](#enter-delivery)
- [Shape the work and PR graph](#shape-the-work-and-pr-graph)
- [Freeze and publish a reviewable candidate](#freeze-and-publish-a-reviewable-candidate)
- [Verify rebases and restack descendants](#verify-rebases-and-restack-descendants)
- [Converge the current remote revision](#converge-the-current-remote-revision)
- [Project tracker state and wait durably](#project-tracker-state-and-wait-durably)
- [Cross the merge race barrier](#cross-the-merge-race-barrier)
- [Deploy and verify post-delivery](#deploy-and-verify-post-delivery)
- [Report terminal truth](#report-terminal-truth)

## Enter delivery

Reconcile the controller and canonical local/remote state before committing, publishing, rewriting, commenting, changing a tracker, merging, or deploying. Perform an external action only when both conditions hold:

1. The trusted requested endpoint makes its action trigger applicable.
2. A current target-specific capability authorizes that action.

Treat availability and authority as independent. A capability does not create a requested action, and a ticket, repository policy, helper, prior run, or observed access cannot grant either. Apply the exact authority boundaries in `SKILL.md`; in particular, keep merge, auto-merge, deploy, release, rollback, production/customer access, closing syntax, manual reviewer requests, published-history rewrite, and destructive cleanup separate.

Use the controller's single-writer and write-ahead action protocol for every authorized external mutation. Re-read the target immediately before applying it, use an expected-head/version guard when supported, and read back the exact effect. Reconcile `uncertain` or `applied-unverified` actions according to the controller; never invent a parallel journal or retry a possibly duplicated effect.

Skip implementation publication and convergence when the trusted endpoint is local-only or evidence supports `resolved-no-change`; mark them inapplicable rather than pretending they occurred. After the no-change result has independent terminal evidence, an authorized factual tracker projection may still be part of the requested endpoint, but it neither becomes an implementation/delivery effect nor proves the no-change result. Do not manufacture a commit, work unit, PR, or tracker mutation to demonstrate activity.

## Shape the work and PR graph

Use the scope classification from [diagnosis-and-design.md](diagnosis-and-design.md). Keep core and necessary enabling work in the outcome. Publish a worthwhile adjacent item only when its inclusion improves the current reviewer story; otherwise create an authorized follow-up only when it is verified, nonduplicate, independently actionable, valuable, and not required for safe acceptance. Never defer a branch-introduced regression or a required privacy, security, integrity, recovery, migration, or acceptance condition.

Use one controller work unit for a single coherent delivery. Build a multi-unit DAG only when a split materially improves reviewability, ownership, reuse, independent landing, or risk isolation and every unit has its own motivation, contract, proof boundary, safe intermediate tree, and merge/rollback story. Keep behavior with its tests, migrations, generated outputs, and required documentation.

For every `depends_on` edge, record which meaning applies:

- **Semantic dependency:** the child consumes a contract introduced by the parent and must remain based on it until that contract lands.
- **Temporary extraction order:** independently coherent work was intermixed, and sequential bases temporarily produce clean review diffs. Record the temporary base and exact retarget/flatten condition; do not present sequencing as architectural dependency.

Represent several units sharing one PR by the same immutable PR origin-slot coordinate, not by a dependency edge. Before creation, derive that slot through the controller from provider, target repository/ref, head repository/ref, and work-unit ID; authorize and retain it through the lifecycle. Record and verify the provider-assigned PR number/URL separately in receipts and host evidence. Assign every ticket-owned delta exactly once. Reject cycles, duplicated commits, hidden cross-PR assumptions, unsafe intermediate trees, and a child whose diff is unintelligible against its recorded base.

Define the graph's completion predicate. Use closing syntax only on a PR whose merge occurs after or atomically contains every required unit; otherwise use non-closing relations and complete the tracker separately. Never let a terminal-looking PR close a ticket while an independent required sibling remains open.

Before final proof/review, give the provisional graph a reviewer-navigability challenge: can a fresh reviewer state each unit's motivation and contract, inspect its diff and tests without mentally reassembling unrelated layers, and understand the safe intermediate and final trees? Split or regroup when the answer is materially no, then freeze the graph. Prove each independently coherent unit and the reassembled terminal tree. If later proof or review reveals the topology is wrong, return to G2/G3, change it, and invalidate affected proof/review; do not split a reviewed monolith afterward merely to make its residual diff look smaller.

## Freeze and publish a reviewable candidate

After G4–G5 pass on the frozen topology, preserve the exact reviewed delta, intended bases, and integrated terminal tree. Prefer additive fix commits after reviewers see a head. Rewrite a reviewed or collaborator-touched head only with the specific authority required by `SKILL.md`; a backup ref preserves code, not approvals, comments, or reviewer context.

Publish each unit in dependency order:

1. Fetch and reconcile the controller, ticket-owned dirt, actual target/merge bases, local head, canonical remote head, and ownership.
2. Confirm the final commits, unit boundaries, and graph match the G4–G5 candidate. Return to the invalidated gate if they do not.
3. Create intentional commits from ticket-owned changes only; verify the unit's semantic delta against its actual base and the reassembled terminal tree.
4. Prepare the controller action against the observed remote head or expected absence. Push with lease protection, then require the canonical remote ref to equal the intended commit.
5. Derive title, body, actual base, scope, stack position, ticket relation, labels, and draft state from that verified remote snapshot—not from a prior local description.
6. Prepare and apply the PR create/update action, then re-read the canonical PR and verify its URL, head, base, metadata, and state.
7. Perform only the separately applicable and authorized follow-up, tracker, comment, resolution, or reviewer-request actions. Deduplicate them through controller intents.
8. Record receipts and enter current-revision convergence.

After publication and after every redesign, extraction, rebase, restack, or material fix, compare the canonical PR against its observed diff. Require its title/body, examples, scope and exclusions, risk/evidence claims, base/head, stack graph and merge order, labels, ticket relation, and draft state to be true. Stale handoff prose is a delivery defect.

## Verify rebases and restack descendants

Resolve the semantic base: the lowest current tree that provides every contract the unit assumes. Before rebasing, preserve recorded and local pre-fetch coordinates, then fetch successfully and record canonical target/base/head coordinates. Block rather than rebase from cached refs when refresh fails.

Route mechanics through the verified-rebase helper, then verify meaning:

- Compare old and new semantic deltas and terminal trees, not only commit counts, patch IDs, or conflict-free application.
- Identify upstreamed, superseded, intentionally changed, and dropped deltas; verify conflict resolutions preserve the outcome contract.
- Exclude unrelated and descendant changes from the unit, and rerun every proof/review invalidated by the new base or build.
- If a lease-protected push fails, discard the stale result, reconcile the new remote head and collaborator delta, and recompute. Never widen the lease or force through the race.

Treat a parent rebase, force-push, retarget, merge, or contract change as invalidating every descendant. Stop concurrent writes to that subgraph, stabilize the parent, then restack one child at a time. For each child, verify its isolated delta and integrated terminal tree, push against its observed head, re-read and correct its PR metadata, and reconverge it before advancing. Never merge or restack a descendant against an old parent head.

## Converge the current remote revision

Define one revision tuple for every readiness claim: controller graph revision, target-base SHA, merge-base SHA, head SHA, and tested candidate/build identity when applicable. Store the complete lane and feedback inventory as a sanitized evidence artifact and cite its digest from the controller. The controller's structural G7 result alone does not prove host convergence.

Build the lane inventory from branch protection/rulesets, workflow definitions, configured bots, requested ownership, supported platforms, and outcome/risk obligations. For each lane record its source, applicability and required-coverage reason, current tuple, canonical run/review identity, terminal state, and observation time.

- Require every applicable required-coverage lane to finish successfully on the current tuple.
- Require every applicable informational lane to reach a current terminal state and inspect its output; its result blocks only when it exposes actionable feedback or contradicts a material claim.
- Treat missing, pending, skipped, neutral, cancelled, stale, and infrastructure-failed required coverage as not passing. Treat superseded runs as stale, never as failures or passes.
- Mark a lane inapplicable only from authoritative repository configuration/policy or an explicit decision by the accountable human owner that accepts the named residual impact. Agent rationale alone cannot waive coverage.

Read every feedback surface at the same tuple: check annotations, review bodies and decisions, unresolved/resolved/outdated threads and their comments, top-level comments, requested reviewers, mergeability, and draft state. Paginate rather than trusting aggregate status. Treat every human or bot comment as a claim: fix it, reject it with evidence, or leave a genuine material decision visibly open. A reply, resolved checkbox, label removal, or earlier approval does not prove disposition on a new head.

Classify a failed lane from evidence as introduced, base/pre-existing, flaky, or infrastructure. Reproduce base failures on the actual base; retry flakes/infrastructure only after identifying a mechanism or known signature; fix introduced failures at the root and validate locally when an executable boundary exists, otherwise record the validation gap. Never suppress a gate or burn retries to manufacture green.

Reconcile existing review requests/runs before invoking another. Allow at most one authorized invocation per lane, head, and reason, with a persisted finite retry budget. Treat reviewer failure or exhaustion as a visible pending decision gate; restarting machinery or removing a label does not clear its findings. Notify a named human once only when social-write authority permits.

After roughly two substantive feedback/fix rounds, cluster the finding morphology before patching again. Repeated same-invariant, cross-surface, test-oracle, or ownership findings trigger a G2/G3 design or topology reset; do not exhaust bots and humans through one-line whack-a-mole.

Declare the graph converged only when the same current tuple has passing required coverage, terminal informational lanes, no actionable or untriaged feedback, current proof/review, truthful non-draft mergeable open PRs, verified merged heads and integrated artifacts for already merged units, stable converged ancestors, and no owned uncommitted/unpushed work. For `merge-ready-awaiting-human` only, permit exactly the named required human approval and/or merge action to remain pending after every agent- and machine-addressable prerequisite passes; record it as pending, never passing or waived. This exception authorizes neither action. After merge, a pending human deployment is a stable external dependency and uses `blocked`, not merge-ready language.

Invalidate readiness whenever the tuple, graph, relevant metadata, evidence input, review requirement, or feedback inventory changes. Cancel an owned pending merge action when authorized; if an existing action cannot be safely cancelled, block and escalate. Re-read canonical state even when the host still displays old green checks or approvals.

## Project tracker state and wait durably

Treat the tracker as a projection of verified delivery truth, never as authority or proof. Under ordinary end-to-end authority, limit projection to the one factual, non-regressive update described by `SKILL.md` and attach owned PR links. Require target-specific authority for other field/state changes. Preserve completed, cancelled, superseded, and intentionally later states; never project completion from a push, opened PR, once-green CI run, or queued merge/deploy.

Put closing syntax only on the graph-completing PR when separately authorized. Link prerequisite/extraction PRs without closing semantics. Create each qualifying follow-up once and link its evidence and parent. When authority is absent, return ready-to-file text instead of mutating the tracker.

Use an inspected shepherd or host-native durable watcher while CI, bots, humans, a base merge, deployment, or an observation window is pending. Treat each event only as a wake-up signal, then re-read canonical state and rebuild the affected inventory. Treat timeout as pending. Use the controller's handoff protocol when monitoring cannot survive the turn; bind any prose status to its revision tuple and observation time.

## Cross the merge race barrier

Attempt a direct merge only when the merge action is part of the trusted requested endpoint and a current target-specific merge capability exists. Immediately before applying it:

1. Hold the controller's active single-writer lease and reconcile incomplete actions; stop concurrent writes to the affected graph.
2. Re-read the head, target and merge bases, candidate merge revision, PR state, mergeability, graph ancestors, every lane and feedback surface, approvals, and tracker relation.
3. Require all direct-merge readiness predicates above to match that exact tuple. Retract readiness and return to convergence if anything moved or any expected review is pending, blocked, exhausted, changes-requested, or unresolved.
4. Prepare the merge action and submit it with an expected-head guard. When the host cannot guard the relevant tuple, re-read at the last possible moment and do not merge across unresolved concurrency.
5. Re-read the result; verify the expected head—not merely the PR number—merged into the intended target and that the resulting history/tree contains the intended semantic delta.

Never overlap a parent merge with a descendant merge/restack. After a parent lands, invalidate and reconverge descendants bottom-up before considering the next merge.

Treat auto-merge as a pending action, not as a completed barrier crossing. Enable it only when auto-merge is separately requested and authorized and the provider binds execution to the exact head plus tested target/candidate tuple or revalidates them in a merge queue. Monitor it, cancel it when readiness becomes stale, and verify the actual merge afterward. Do not enable it when those guarantees are unavailable.

## Deploy and verify post-delivery

Treat merge, deploy, release, production access, rollback, tracker completion, and cleanup as distinct actions. Perform each only when its requested-action trigger is applicable and its target-specific capability is current. Deployment authority never implies merge or production-observation authority; when another actor merged first, verify the canonical merge event instead of attempting another merge.

Before an authorized deploy/release, identify the exact source commit and artifact digest and reject an artifact not traceable to them. Predeclare the target environment, rollout bounds, named health signals and thresholds, observation duration, failure/rollback trigger, and whether rollback is authorized. Apply the deploy/release through the repository mechanism and controller action protocol; verify the provider's actual version/state rather than treating a queued request as delivered.

Run a production smoke check, query production telemetry, or observe production health only with separate production-access capability, even when using synthetic data. Stay within its need-to-know scope, use dedicated/synthetic state, and record only privacy-safe evidence. Without that capability, use authorized provider deployment status and state the production-observation gap.

Execute rollback only when its trigger fires and rollback authority already covers the target; otherwise stop and escalate. If a material blocker arrives after merge, pause authorized downstream delivery, assess containment, and preserve the finding. When authorized, reproduce against the merged baseline and reconverge the smallest coherent correction with regression proof; never erase late feedback to preserve a success claim.

Do not delete recovery refs, branches, worktrees, or artifacts merely because delivery succeeded. Require the applicable destructive cleanup authority.

## Report terminal truth

Use the controller's exact five terminal outcomes and guards in the precedence order defined by `SKILL.md`:

- `resolved-no-change`: current evidence proves the ticket stale, duplicate, already satisfied, false, or harmful as written and no implementation/delivery effect is warranted; a separately authorized factual tracker projection may record that result;
- `complete`: the trusted requested and authorized endpoint occurred and was verified, including a local-only endpoint when that was the whole request;
- `merge-ready-awaiting-human` (render as “merge-ready awaiting human”): the frozen requested endpoint is merge, every agent- and machine-addressable prerequisite passes, and only the named human approval or merge authority/action remains;
- `partial`: a forced but resumable interruption, recoverable tool failure, or explicit handoff leaves known safe work, an exact next action, and no false readiness claim;
- `blocked`: an evidenced stable material blocker at the earliest failing gate leaves no safe independent action that can advance the outcome.

Before finishing, re-read canonical repository, remote, PR, review, CI, tracker, merge/deploy, and controller state. Verify the requested endpoint rather than the ceremony used to reach it. Report the exact terminal outcome, graph and current heads, proof/review and convergence evidence, authorized effects, follow-ups, residual uncertainty, and precise next human action. Never convert a stale record, queued action, timeout, or unobserved effect into completion.
