from __future__ import annotations

import hashlib
import io
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


SCRIPT = Path(__file__).with_name("ticketctl.py")
SPEC = importlib.util.spec_from_file_location("ticketctl", SCRIPT)
assert SPEC and SPEC.loader
ticketctl = importlib.util.module_from_spec(SPEC)
sys.modules["ticketctl"] = ticketctl
SPEC.loader.exec_module(ticketctl)
DIGEST = "a" * 64


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class TicketCtlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-qm", "initial")
        self.ticket = "private-ticket-locator"
        self.envelope_path = Path(self.temporary.name) / "authority.json"
        self.write_envelope()
        result = self.cli("init", "--authority-envelope", os.fspath(self.envelope_path))
        self.record_path = Path(json.loads(result.stdout)["record"])
        lease = self.cli("lease", "acquire", "--owner-digest", DIGEST)
        lease_data = json.loads(lease.stdout)
        self.token = lease_data["token"]
        self.epoch = str(lease_data["epoch"])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", os.fspath(self.repo), *arguments],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def repository_digest(self) -> str:
        common = self.git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
        return hashlib.sha256(os.fsencode(str(Path(common).resolve()))).hexdigest()

    def write_envelope(
        self,
        *,
        endpoint: str = "local",
        allowed_scopes: list[str] | None = None,
        action_kinds: list[str] | None = None,
        effects: list[str] | None = None,
        targets: list[str] | None = None,
        max_actions: int = 4,
        parent: str | None = None,
    ) -> dict[str, object]:
        envelope: dict[str, object] = {
            "schema_version": 1,
            "trusted_turn_digest": sha("trusted-turn"),
            "ticket_digest": sha(self.ticket),
            "repository_digest": self.repository_digest(),
            "parent_digest": parent,
            "requested_endpoint": endpoint,
            "allowed_scopes": allowed_scopes or ["local-change"],
            "allowed_action_kinds": action_kinds or [],
            "allowed_effects": effects or [],
            "allowed_target_digests": targets or [],
            "denials": [],
            "max_actions": max_actions,
            "expires_at": None,
            "delegable": False,
        }
        self.envelope_path.write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
        return envelope

    def cli(self, *arguments: str, mutate: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = [
            "--repo",
            os.fspath(self.repo),
            "--ticket",
            self.ticket,
        ]
        if mutate:
            command.extend(("--lease-token", self.token, "--lease-epoch", self.epoch))
        command.extend(arguments)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                returncode = ticketctl.main(command)
            except SystemExit as error:
                returncode = int(error.code or 0)
        result = subprocess.CompletedProcess(command, returncode, stdout.getvalue(), stderr.getvalue())
        if check and result.returncode:
            self.fail(f"command failed: {' '.join(arguments)}\n{result.stderr}")
        return result

    def record(self) -> dict[str, object]:
        return json.loads(self.record_path.read_text(encoding="utf-8"))

    def add_contexts_and_capability(self) -> None:
        self.cli("context", "add", "repo-rules", "--kind", "repository-instructions", "--content-digest", DIGEST, mutate=True)
        self.cli("context", "add", "starting", "--kind", "starting-state", "--content-digest", "b" * 64, mutate=True)
        self.cli(
            "capability",
            "set",
            "local-change",
            "--available",
            "yes",
            "--authority",
            "granted",
            "--basis",
            "authority.root",
            "--required",
            "--rationale",
            "Trusted local implementation request",
            mutate=True,
        )

    def resolve_all_triggers_no(self) -> None:
        for trigger_id in self.record()["triggers"]:
            self.cli(
                "trigger",
                "set",
                trigger_id,
                "--decision",
                "no",
                "--rationale",
                "This boundary is not involved",
                mutate=True,
            )

    def test_default_location_is_sanitized_and_shared_by_worktrees(self) -> None:
        record_text = self.record_path.read_text(encoding="utf-8")
        journal_text = self.record_path.with_name("journal.jsonl").read_text(encoding="utf-8")
        self.assertNotIn(self.ticket, record_text + journal_text)
        self.assertTrue(self.record_path.is_relative_to(self.repo / ".git"))

        worktree = Path(self.temporary.name) / "linked"
        self.git("worktree", "add", "-qb", "linked", os.fspath(worktree))
        located = subprocess.run(
            [sys.executable, os.fspath(SCRIPT), "--repo", os.fspath(worktree), "--ticket", self.ticket, "locate"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        self.assertEqual(Path(json.loads(located.stdout)["record"]), self.record_path)

    def test_journal_recovers_atomic_snapshot_after_interrupted_projection(self) -> None:
        self.cli("context", "add", "repo-rules", "--kind", "repository-instructions", "--content-digest", DIGEST, mutate=True)
        before = self.record_path.read_text(encoding="utf-8")
        self.record_path.write_text("{broken", encoding="utf-8")
        shown = self.cli("show")
        self.assertIn("repo-rules", shown.stdout)
        self.assertEqual(self.record_path.read_text(encoding="utf-8"), before)
        json.loads(self.record_path.read_text(encoding="utf-8"))

    def test_local_only_run_reaches_g1_and_unknown_trigger_fails_g0(self) -> None:
        self.add_contexts_and_capability()
        result = json.loads(self.cli("gate").stdout)
        self.assertEqual(result["current_gate"], "G0")
        self.assertTrue(any("trigger" in reason for reason in result["gates"][0]["reasons"]))
        self.resolve_all_triggers_no()
        checkpoint = self.make_checkpoint("g0")
        self.add_evidence("g0-proof", "inspection", checkpoint, obligation="establish-state")
        self.cli("obligation", "resolve", "establish-state", "--status", "satisfied", "--evidence", "g0-proof", mutate=True)
        result = json.loads(self.cli("gate").stdout)
        self.assertEqual(result["current_gate"], "G1")

    def test_expired_capability_and_optional_claims_cannot_advance_gates(self) -> None:
        self.add_contexts_and_capability()
        self.resolve_all_triggers_no()
        checkpoint = self.make_checkpoint("capability")
        self.add_evidence("g0-proof", "inspection", checkpoint, obligation="establish-state")
        self.cli("obligation", "resolve", "establish-state", "--status", "satisfied", "--evidence", "g0-proof", mutate=True)
        self.cli("claim", "add", "optional-acceptance", "--gate", "G1", "--kind", "acceptance", "--summary", "Optional scenario", "--optional", mutate=True)
        self.cli("claim", "add", "optional-risk", "--gate", "G1", "--kind", "risk", "--summary", "Optional risk", "--optional", mutate=True)
        gate = json.loads(self.cli("gate").stdout)
        self.assertEqual(gate["current_gate"], "G1")
        self.assertTrue(any("at least one acceptance" in reason for reason in gate["gates"][1]["reasons"]))

        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["capabilities"]["local-change"]["expires_at"] = "2000-01-01T00:00:00Z"
            store.commit(record, "test.expire-capability", {}, bypass_lease=True)
        gate = json.loads(self.cli("gate").stdout)
        self.assertEqual(gate["current_gate"], "G0")
        self.assertTrue(any("local-change" in reason for reason in gate["gates"][0]["reasons"]))

    def make_checkpoint(self, checkpoint_id: str, *, external: str = DIGEST) -> str:
        self.cli(
            "checkpoint",
            "create",
            checkpoint_id,
            "--base-digest",
            "1" * 64,
            "--config-digest",
            "2" * 64,
            "--build-digest",
            "3" * 64,
            "--environment-digest",
            "4" * 64,
            "--external-digest",
            external,
            mutate=True,
        )
        return checkpoint_id

    def add_evidence(self, evidence_id: str, kind: str, checkpoint: str, *, obligation: str | None = None) -> None:
        arguments = [
            "evidence",
            "add",
            evidence_id,
            "--kind",
            kind,
            "--result",
            "pass",
            "--checkpoint",
            checkpoint,
            "--artifact-digest",
            sha(evidence_id),
        ]
        if obligation:
            arguments.extend(("--obligation", obligation))
        self.cli(*arguments, mutate=True)

    def test_fingerprint_survives_staging_and_commit_but_changes_with_content(self) -> None:
        (self.repo / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        before = json.loads(self.cli("fingerprint").stdout)["digest"]
        self.git("add", "tracked.txt")
        staged = json.loads(self.cli("fingerprint").stdout)["digest"]
        self.git("commit", "-qm", "candidate")
        committed = json.loads(self.cli("fingerprint").stdout)["digest"]
        self.assertEqual(before, staged)
        self.assertEqual(staged, committed)
        (self.repo / "tracked.txt").write_text("different\n", encoding="utf-8")
        self.assertNotEqual(committed, json.loads(self.cli("fingerprint").stdout)["digest"])

    def test_checkpoint_dependency_and_event_invalidation_fail_closed(self) -> None:
        checkpoint = self.make_checkpoint("one", external="a" * 64)
        self.cli(
            "evidence", "add", "proof", "--kind", "test", "--result", "pass",
            "--checkpoint", checkpoint, "--artifact-digest", sha("proof"),
            "--obligation", "prove-behavior", "--depends-on", "external", mutate=True,
        )
        self.cli("obligation", "resolve", "prove-behavior", "--status", "satisfied", "--evidence", "proof", mutate=True)
        self.make_checkpoint("two", external="b" * 64)
        record = self.record()
        reason = ticketctl.fresh_evidence_reason(record, "proof", ticketctl.git_fingerprint(self.repo))
        self.assertIn("external", reason)
        self.cli("invalidate", "source-change", "--rationale", "Candidate changed", mutate=True)
        self.assertIsNotNone(self.record()["evidence"]["proof"]["invalidated"])

    def test_trigger_yes_materializes_mandatory_obligation(self) -> None:
        self.cli("trigger", "set", "performance-resource", "--decision", "yes", "--rationale", "Latency changes", mutate=True)
        record = self.record()
        obligation_id = record["triggers"]["performance-resource"]["obligation"]
        self.assertEqual(obligation_id, "trigger.performance-resource")
        self.assertFalse(record["obligations"][obligation_id]["waivable"])

    def test_evidence_and_finding_vocabularies_match_control_contract(self) -> None:
        checkpoint = self.make_checkpoint("terms")
        gap = self.cli(
            "evidence", "add", "known-gap", "--kind", "test", "--result", "gap",
            "--checkpoint", checkpoint, "--artifact-digest", sha("gap"), mutate=True,
        )
        self.assertEqual(json.loads(gap.stdout)["result"], "gap")
        partial = self.cli(
            "evidence", "add", "wrong-term", "--kind", "test", "--result", "partial",
            "--checkpoint", checkpoint, "--artifact-digest", sha("partial"), mutate=True, check=False,
        )
        self.assertNotEqual(partial.returncode, 0)
        unknown = self.cli(
            "finding", "add", "unknown-origin", "--severity", "minor", "--origin", "unknown",
            "--summary", "Origin is not yet proven", mutate=True,
        )
        self.assertEqual(json.loads(unknown.stdout)["origin"], "unknown")
        review_origin = self.cli(
            "finding", "add", "bad-origin", "--severity", "minor", "--origin", "review",
            "--summary", "Found during review", mutate=True, check=False,
        )
        self.assertNotEqual(review_origin.returncode, 0)

    def test_review_evidence_requires_provenance_and_unique_output(self) -> None:
        checkpoint = self.make_checkpoint("review")
        missing = self.cli(
            "evidence", "add", "review-missing", "--kind", "review", "--result", "pass",
            "--checkpoint", checkpoint, "--artifact-digest", sha("same-output"),
            "--review-lens", "correctness", mutate=True, check=False,
        )
        self.assertNotEqual(missing.returncode, 0)
        first = self.cli(
            "evidence", "add", "review-one", "--kind", "review", "--result", "pass",
            "--checkpoint", checkpoint, "--artifact-digest", sha("same-output"),
            "--review-lens", "correctness", "--reviewer-digest", "b" * 64,
            "--review-input-digest", "c" * 64, mutate=True,
        )
        self.assertEqual(json.loads(first.stdout)["review_lenses"], ["correctness"])
        reused = self.cli(
            "evidence", "add", "review-two", "--kind", "review", "--result", "pass",
            "--checkpoint", checkpoint, "--artifact-digest", sha("same-output"),
            "--review-lens", "architecture", "--reviewer-digest", "d" * 64,
            "--review-input-digest", "e" * 64, mutate=True, check=False,
        )
        self.assertNotEqual(reused.returncode, 0)
        self.assertIn("already used", reused.stderr)

    def test_lease_rejects_second_writer_and_requires_guarded_takeover(self) -> None:
        second = self.cli("lease", "acquire", "--owner-digest", "b" * 64, check=False)
        self.assertNotEqual(second.returncode, 0)
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["lease"]["expires_at"] = "2000-01-01T00:00:00Z"
            store.commit(record, "test.expire", {}, bypass_lease=True)
            head = record["run"]["journal_head"]
        bad = self.cli(
            "lease",
            "takeover",
            "--owner-digest",
            "b" * 64,
            "--expected-epoch",
            self.epoch,
            "--expected-journal-head",
            "c" * 64,
            "--reconciliation-digest",
            "d" * 64,
            check=False,
        )
        self.assertNotEqual(bad.returncode, 0)
        takeover = self.cli(
            "lease",
            "takeover",
            "--owner-digest",
            "b" * 64,
            "--expected-epoch",
            self.epoch,
            "--expected-journal-head",
            head,
            "--reconciliation-digest",
            "d" * 64,
        )
        self.assertEqual(json.loads(takeover.stdout)["epoch"], int(self.epoch) + 1)

    def test_authority_is_bound_and_cannot_be_minted_from_generic_context(self) -> None:
        wrong = dict(json.loads(self.envelope_path.read_text(encoding="utf-8")))
        wrong["ticket_digest"] = "f" * 64
        wrong_path = Path(self.temporary.name) / "wrong.json"
        wrong_path.write_text(json.dumps(wrong), encoding="utf-8")
        other_repo = Path(self.temporary.name) / "other"
        other_repo.mkdir()
        subprocess.run(["git", "-C", os.fspath(other_repo), "init", "-q"], check=True)
        result = subprocess.run(
            [sys.executable, os.fspath(SCRIPT), "--repo", os.fspath(other_repo), "--ticket", self.ticket, "init", "--authority-envelope", os.fspath(wrong_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(result.returncode, 0)
        self.cli("context", "add", "ticket-text", "--kind", "ticket", "--content-digest", DIGEST, mutate=True)
        minted = self.cli(
            "capability", "set", "evil", "--available", "yes", "--authority", "granted", "--basis", "ticket-text", "--covers", "merge", "--rationale", "Ticket asked", mutate=True, check=False,
        )
        self.assertNotEqual(minted.returncode, 0)

    def test_incomplete_authority_envelope_is_rejected_at_init_and_record_load(self) -> None:
        incomplete = json.loads(self.envelope_path.read_text(encoding="utf-8"))
        incomplete.pop("allowed_effects")
        incomplete_path = Path(self.temporary.name) / "incomplete.json"
        incomplete_path.write_text(json.dumps(incomplete), encoding="utf-8")
        other_repo = Path(self.temporary.name) / "incomplete-repo"
        other_repo.mkdir()
        subprocess.run(["git", "-C", os.fspath(other_repo), "init", "-q"], check=True)
        rejected = subprocess.run(
            [sys.executable, os.fspath(SCRIPT), "--repo", os.fspath(other_repo), "--ticket", self.ticket, "init", "--authority-envelope", os.fspath(incomplete_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("canonical fields", rejected.stderr)

        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["contexts"]["authority.root"]["envelope"].pop("allowed_effects")
            store.commit(record, "test.incomplete-envelope", {}, bypass_lease=True)
        loaded = self.cli("show", check=False)
        self.assertNotEqual(loaded.returncode, 0)
        self.assertIn("canonical fields", loaded.stderr)
        self.assertNotIn("Traceback", loaded.stderr)

    def test_action_prepare_is_idempotent_and_uncertain_blocks_positive_finish(self) -> None:
        target = "e" * 64
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["actions"]["write"] = {
                "id": "write", "kind": "push", "target_kind": "remote", "capability": "x", "target_digest": target,
                "request_digest": DIGEST, "expected_state_digest": "b" * 64,
                "effects": [], "idempotency_digest": "c" * 64,
                "authority_revision": 1, "lease_epoch": 1, "status": "uncertain",
                "receipt_digest": "d" * 64, "prepared_at": "now", "settled_at": "now",
            }
            record["actions"]["absent"] = {
                "id": "absent", "kind": "push", "target_kind": "remote", "capability": "x", "target_digest": "f" * 64,
                "request_digest": DIGEST, "expected_state_digest": "b" * 64,
                "effects": [], "idempotency_digest": "9" * 64,
                "authority_revision": 1, "lease_epoch": 1, "status": "verified-not-applied",
                "receipt_digest": "8" * 64, "prepared_at": "now", "settled_at": "now",
            }
            store.commit(record, "test.action", {}, bypass_lease=True)
        record = self.record()
        errors = ticketctl.positive_finish_errors(record, "complete", self.repo)
        self.assertTrue(any("write" in error for error in errors))
        self.assertTrue(any("absent" in error and "no current equivalent" in error for error in errors))

    def test_interruption_requires_blocker_evidence_kind(self) -> None:
        self.add_contexts_and_capability()
        self.resolve_all_triggers_no()
        checkpoint = self.make_checkpoint("blocked")
        self.add_evidence("inspection-only", "inspection", checkpoint, obligation="establish-state")
        self.cli(
            "obligation", "resolve", "establish-state", "--status", "blocked",
            "--evidence", "inspection-only", "--rationale", "Tool boundary unavailable", mutate=True,
        )
        rejected = self.cli(
            "finish", "--status", "partial", "--rationale", "Forced handoff",
            "--blocked-obligation", "establish-state", "--next-action", "Restore the tool",
            "--needed-evidence", "A fresh blocker observation", mutate=True, check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("lacks fresh evidence", rejected.stderr)
        blocked_gate = json.loads(self.cli("gate").stdout)
        blocker_reason_arguments: list[str] = []
        for reason_digest in blocked_gate["gates"][0]["reason_digests"]:
            blocker_reason_arguments.extend(("--reason-digest", reason_digest))
        self.cli(
            "evidence", "add", "blocker-proof", "--kind", "blocker", "--result", "pass",
            "--checkpoint", checkpoint, "--artifact-digest", sha("blocker"),
            "--obligation", "establish-state", *blocker_reason_arguments, mutate=True,
        )
        self.cli(
            "obligation", "resolve", "establish-state", "--status", "blocked",
            "--evidence", "blocker-proof", "--rationale", "Tool boundary unavailable", mutate=True,
        )
        reason_arguments: list[str] = []
        gate = json.loads(self.cli("gate").stdout)
        for reason_digest in gate["gates"][0]["reason_digests"]:
            reason_arguments.extend(("--reason-digest", reason_digest))
        finished = self.cli(
            "finish", "--status", "partial", "--rationale", "Forced handoff",
            "--blocked-obligation", "establish-state", "--next-action", "Restore the tool",
            "--needed-evidence", "A fresh blocker observation", *reason_arguments, mutate=True,
        )
        self.assertEqual(json.loads(finished.stdout)["status"], "partial")

    def test_finish_guards_unknowns_partial_enumeration_and_endpoint(self) -> None:
        result = self.cli("finish", "--status", "complete", "--rationale", "Done", mutate=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        partial = self.cli(
            "finish", "--status", "partial", "--rationale", "Interrupted", "--next-action", "Resume verification", "--needed-evidence", "Current tests", mutate=True, check=False,
        )
        self.assertNotEqual(partial.returncode, 0)

    def test_atomic_write_preserves_old_file_when_replace_fails(self) -> None:
        path = Path(self.temporary.name) / "atomic.json"
        path.write_text('{"old":true}\n', encoding="utf-8")
        with mock.patch.object(ticketctl.os, "replace", side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                ticketctl.atomic_write_json(path, {"new": True})
        self.assertEqual(path.read_text(encoding="utf-8"), '{"old":true}\n')
        self.assertEqual(list(path.parent.glob(".atomic.json.*")), [])


if __name__ == "__main__":
    unittest.main()
