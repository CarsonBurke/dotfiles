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
SPEC = importlib.util.spec_from_file_location("ticketctl_adversarial", SCRIPT)
assert SPEC and SPEC.loader
ticketctl = importlib.util.module_from_spec(SPEC)
sys.modules["ticketctl_adversarial"] = ticketctl
SPEC.loader.exec_module(ticketctl)
DIGEST = "a" * 64


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class TicketCtlAdversarialTest(unittest.TestCase):
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
        self.ticket = "adversarial-ticket"
        self.envelope_path = Path(self.temporary.name) / "authority.json"
        self.write_envelope(self.envelope_path)
        initialized = self.cli("init", "--authority-envelope", os.fspath(self.envelope_path))
        self.record_path = Path(json.loads(initialized.stdout)["record"])
        lease = json.loads(self.cli("lease", "acquire", "--owner-digest", DIGEST).stdout)
        self.token = lease["token"]
        self.epoch = str(lease["epoch"])

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

    def repository_digest(self, repo: Path | None = None) -> str:
        target = repo or self.repo
        common = subprocess.run(
            ["git", "-C", os.fspath(target), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        return hashlib.sha256(os.fsencode(str(Path(common).resolve()))).hexdigest()

    def write_envelope(
        self,
        path: Path,
        *,
        endpoint: str = "local",
        parent: str | None = None,
        scopes: list[str] | None = None,
        kinds: list[str] | None = None,
        effects: list[str] | None = None,
        targets: list[str] | None = None,
        max_actions: int = 0,
        expires_at: str | None = None,
    ) -> dict[str, object]:
        envelope: dict[str, object] = {
            "schema_version": 1,
            "trusted_turn_digest": sha(f"trusted:{parent}"),
            "ticket_digest": sha(self.ticket),
            "repository_digest": self.repository_digest(),
            "parent_digest": parent,
            "requested_endpoint": endpoint,
            "allowed_scopes": ["local-change"] if scopes is None else scopes,
            "allowed_action_kinds": [] if kinds is None else kinds,
            "allowed_effects": [] if effects is None else effects,
            "allowed_target_digests": [] if targets is None else targets,
            "denials": [],
            "max_actions": max_actions,
            "expires_at": expires_at,
            "delegable": False,
        }
        path.write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
        return envelope

    def cli(
        self,
        *arguments: str,
        mutate: bool = False,
        check: bool = True,
        repo: Path | None = None,
        ticket: str | None = None,
        record: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "--repo",
            os.fspath(repo or self.repo),
            "--ticket",
            ticket or self.ticket,
        ]
        if record:
            command.extend(("--record", os.fspath(record)))
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

    def checkpoint(self, checkpoint_id: str = "checkpoint") -> None:
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
            "5" * 64,
            mutate=True,
        )

    def current_authority(self) -> dict[str, object]:
        contexts = self.record()["contexts"]
        return max(
            (context for context in contexts.values() if context["kind"] == "trusted-instruction"),
            key=lambda context: context["authority_revision"],
        )

    def amend(
        self,
        *,
        endpoint: str = "local",
        scopes: list[str] | None = None,
        kinds: list[str] | None = None,
        effects: list[str] | None = None,
        targets: list[str] | None = None,
        max_actions: int = 0,
    ) -> str:
        current = self.current_authority()
        path = Path(self.temporary.name) / f"amend-{self.record()['run']['revision']}.json"
        self.write_envelope(
            path,
            endpoint=endpoint,
            parent=current["digest"],
            scopes=scopes,
            kinds=kinds,
            effects=effects,
            targets=targets,
            max_actions=max_actions,
        )
        amended = json.loads(
            self.cli("authority", "amend", "--authority-envelope", os.fspath(path), mutate=True).stdout
        )
        return amended["id"]

    def establish_g0(self) -> None:
        self.cli(
            "context",
            "add",
            "repo-rules",
            "--kind",
            "repository-instructions",
            "--content-digest",
            DIGEST,
            mutate=True,
        )
        self.cli(
            "context",
            "add",
            "start",
            "--kind",
            "starting-state",
            "--content-digest",
            "b" * 64,
            mutate=True,
        )
        self.cli(
            "capability",
            "set",
            "local-change",
            "--available",
            "yes",
            "--authority",
            "granted",
            "--basis",
            self.current_authority()["id"],
            "--required",
            "--rationale",
            "Direct local implementation authority",
            mutate=True,
        )
        for trigger_id in self.record()["triggers"]:
            self.cli(
                "trigger",
                "set",
                trigger_id,
                "--decision",
                "no",
                "--rationale",
                "Not involved",
                mutate=True,
            )
        self.checkpoint("g0")
        self.cli(
            "evidence",
            "add",
            "g0-proof",
            "--kind",
            "inspection",
            "--result",
            "pass",
            "--checkpoint",
            "g0",
            "--artifact-digest",
            sha("g0"),
            "--obligation",
            "establish-state",
            mutate=True,
        )
        self.cli(
            "obligation",
            "resolve",
            "establish-state",
            "--status",
            "satisfied",
            "--evidence",
            "g0-proof",
            mutate=True,
        )

    def satisfy_implementation_gates(
        self,
        *,
        checkpoint: str = "g0",
        terminal_outcome: str = "complete",
        remote: str | None = "c" * 64,
        pr: str | None = "d" * 64,
    ) -> str:
        head = self.record()["checkpoints"][checkpoint]["dimensions"]["head"]
        self.cli(
            "claim", "add", "acceptance", "--gate", "G1", "--kind", "acceptance",
            "--summary", "The requested observable outcome is present", mutate=True,
        )
        self.cli(
            "claim", "add", "risk", "--gate", "G1", "--kind", "risk",
            "--summary", "The relevant failure mode remains absent", mutate=True,
        )
        self.cli(
            "claim", "add", "terminal", "--gate", "G8", "--kind", "terminal",
            "--summary", "The exact requested endpoint is complete",
            "--terminal-outcome", terminal_outcome, mutate=True,
        )
        self.cli("work", "add", "delivery", "--summary", "Implement and deliver the change", mutate=True)
        coordinate_arguments = [
            "work", "coordinate", "delivery", "--branch-digest", "1" * 64,
            "--worktree-digest", "2" * 64, "--base-digest", "3" * 64,
            "--head-digest", head, "--evidence-epoch", checkpoint,
        ]
        if remote is not None:
            coordinate_arguments.extend(("--remote-digest", remote))
        if pr is not None:
            coordinate_arguments.extend(("--pr-digest", pr))
        self.cli(*coordinate_arguments, mutate=True)

        def evidence(
            evidence_id: str,
            kind: str,
            *targets: str,
            extra: list[str] | None = None,
        ) -> None:
            arguments = [
                "evidence", "add", evidence_id, "--kind", kind, "--result", "pass",
                "--checkpoint", checkpoint, "--artifact-digest", sha(evidence_id),
            ]
            for target_type, target_id in zip(targets[::2], targets[1::2], strict=True):
                arguments.extend((f"--{target_type}", target_id))
            arguments.extend(extra or [])
            self.cli(*arguments, mutate=True)

        evidence(
            "outcome-proof", "inspection", "claim", "acceptance", "claim", "risk",
            "obligation", "define-outcome",
        )
        evidence("design-proof", "inspection", "obligation", "validate-design")
        evidence("implementation-proof", "test", "obligation", "implement-work")
        evidence("behavior-proof", "test", "obligation", "prove-behavior")
        review_extra = ["--reviewer-digest", "4" * 64, "--review-input-digest", "5" * 64]
        for lens in sorted(ticketctl.REVIEW_LENSES):
            review_extra.extend(("--review-lens", lens))
        evidence("review-proof", "review", "obligation", "converge-review", extra=review_extra)
        evidence(
            "terminal-proof", "terminal-audit", "claim", "terminal",
            "obligation", "terminal-audit",
        )
        for obligation_id, evidence_id in (
            ("define-outcome", "outcome-proof"),
            ("validate-design", "design-proof"),
            ("implement-work", "implementation-proof"),
            ("prove-behavior", "behavior-proof"),
            ("converge-review", "review-proof"),
            ("terminal-audit", "terminal-proof"),
        ):
            self.cli(
                "obligation", "resolve", obligation_id, "--status", "satisfied",
                "--evidence", evidence_id, mutate=True,
            )
        self.cli(
            "work", "set", "delivery", "--status", "done",
            "--evidence", "implementation-proof", "--evidence-epoch", checkpoint, mutate=True,
        )
        return head

    def test_journal_is_canonical_and_recovers_only_a_torn_tail(self) -> None:
        projection = self.record()
        projection["contexts"]["forged"] = {"kind": "ticket"}
        projection["run"]["revision"] += 100
        self.record_path.write_text(json.dumps(projection), encoding="utf-8")
        shown = json.loads(self.cli("show").stdout)
        self.assertNotIn("forged", shown["record"]["contexts"])

        journal = self.record_path.with_name("journal.jsonl")
        journal.write_bytes(journal.read_bytes()[:-1])
        self.cli("show")
        self.assertTrue(journal.read_bytes().endswith(b"\n"))
        with journal.open("ab") as destination:
            destination.write(b'{"torn":')
        self.cli("show")
        self.assertTrue(journal.read_bytes().endswith(b"\n"))

        journal.unlink()
        rejected = self.cli("show", check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("no valid append-only journal", rejected.stderr)

    def test_journal_append_retries_short_writes_and_interruption(self) -> None:
        real_write = ticketctl.os.write
        calls = 0

        def interrupted_then_short_write(descriptor: int, data: bytes) -> int:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise InterruptedError()
            if calls == 2:
                short_length = max(1, len(data) // 3)
                return real_write(descriptor, data[:short_length])
            return real_write(descriptor, data)

        with mock.patch.object(ticketctl.os, "write", side_effect=interrupted_then_short_write):
            self.cli(
                "context", "add", "durable", "--kind", "ticket",
                "--content-digest", "b" * 64, mutate=True,
            )
        self.assertGreaterEqual(calls, 3)
        self.assertIn("durable", json.loads(self.cli("show").stdout)["record"]["contexts"])

        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            before_revision = record["run"]["revision"]
            record["contexts"]["not-acknowledged"] = {"id": "not-acknowledged", "kind": "ticket"}
            with mock.patch.object(ticketctl.os, "write", return_value=0):
                with self.assertRaises(OSError):
                    store.commit(record, "test.zero-write", {}, bypass_lease=True)
        shown = json.loads(self.cli("show").stdout)["record"]
        self.assertEqual(shown["run"]["revision"], before_revision)
        self.assertNotIn("not-acknowledged", shown["contexts"])

    def test_identical_checkpoint_reactivation_is_journaled(self) -> None:
        self.checkpoint("first")
        self.checkpoint("second")
        self.checkpoint("first")
        record = self.record()
        self.assertEqual(record["run"]["current_checkpoint"], "first")
        self.assertEqual(json.loads(self.cli("show").stdout)["record"]["run"]["current_checkpoint"], "first")
        last_event = json.loads(self.record_path.with_name("journal.jsonl").read_text().splitlines()[-1])
        self.assertEqual(last_event["event"], "checkpoint.activate")

    def test_registered_artifact_sidecars_are_contained_and_digest_verified(self) -> None:
        artifacts = self.record_path.parent / "artifacts"
        artifacts.mkdir()
        missing = self.cli(
            "artifact", "add", "missing", "--kind", "raw-evidence",
            "--locator", "artifacts/missing.json", "--content-digest", sha("missing"),
            mutate=True, check=False,
        )
        self.assertNotEqual(missing.returncode, 0)
        traversal = self.cli(
            "artifact", "add", "traversal", "--kind", "raw-evidence",
            "--locator", "artifacts/../outside.json", "--content-digest", sha("outside"),
            mutate=True, check=False,
        )
        self.assertNotEqual(traversal.returncode, 0)
        outside = self.record_path.parent / "outside.json"
        outside.write_text("outside", encoding="utf-8")
        (artifacts / "escape.json").symlink_to(outside)
        escaped = self.cli(
            "artifact", "add", "escaped", "--kind", "raw-evidence",
            "--locator", "artifacts/escape.json", "--content-digest", sha("outside"),
            mutate=True, check=False,
        )
        self.assertNotEqual(escaped.returncode, 0)

        sidecar = artifacts / "proof.json"
        sidecar.write_text("durable proof", encoding="utf-8")
        digest = sha("durable proof")
        registered = json.loads(
            self.cli(
                "artifact", "add", "proof", "--kind", "raw-evidence",
                "--locator", "artifacts/proof.json", "--content-digest", digest, mutate=True,
            ).stdout
        )
        self.assertEqual(registered["content_digest"], digest)
        self.checkpoint("artifact")
        self.cli(
            "evidence", "add", "sidecar-proof", "--kind", "inspection", "--result", "pass",
            "--checkpoint", "artifact", "--artifact-digest", digest,
            "--artifact-ref", "proof", mutate=True,
        )
        sidecar.write_text("tampered", encoding="utf-8")
        tampered = self.cli("show", check=False)
        self.assertNotEqual(tampered.returncode, 0)
        self.assertIn("content digest", tampered.stderr)
        sidecar.write_text("durable proof", encoding="utf-8")
        self.assertEqual(json.loads(self.cli("show").stdout)["record"]["artifacts"]["proof"]["locator"], "artifacts/proof.json")

    def test_explicit_record_remains_bound_to_ticket_and_git_common_dir(self) -> None:
        wrong_ticket = self.cli("show", ticket="different-ticket", record=self.record_path, check=False)
        self.assertNotEqual(wrong_ticket.returncode, 0)
        self.assertIn("different ticket", wrong_ticket.stderr)

        other = Path(self.temporary.name) / "other"
        other.mkdir()
        subprocess.run(["git", "-C", os.fspath(other), "init", "-q"], check=True)
        wrong_repo = self.cli("show", repo=other, record=self.record_path, check=False)
        self.assertNotEqual(wrong_repo.returncode, 0)
        self.assertIn("different Git common directory", wrong_repo.stderr)

    def test_lease_release_is_guarded_and_allows_a_new_epoch(self) -> None:
        released = json.loads(self.cli("lease", "release", mutate=True).stdout)
        self.assertTrue(released["released"])
        acquired = json.loads(self.cli("lease", "acquire", "--owner-digest", "b" * 64).stdout)
        self.assertEqual(acquired["epoch"], int(self.epoch) + 1)

    def test_expired_authority_is_loadable_history_but_cannot_grant(self) -> None:
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["contexts"]["authority.root"]["envelope"]["expires_at"] = "2000-01-01T00:00:00Z"
            record["capabilities"]["expired"] = {
                "id": "expired",
                "required": True,
                "available": "yes",
                "authority": "granted",
                "basis": "authority.root",
                "covers": ["local-change"],
                "action_kinds": [],
                "effects": [],
                "target_digests": [],
                "max_uses": 0,
                "uses": 0,
                "expires_at": None,
                "delegable": False,
                "authority_revision": 1,
                "rationale": "historical",
            }
            store.commit(record, "test.expire-authority", {}, bypass_lease=True)
        shown = json.loads(self.cli("show").stdout)
        self.assertIn("authority.root", shown["record"]["contexts"])
        self.assertFalse(ticketctl.capability_is_current(shown["record"], shown["record"]["capabilities"]["expired"]))

    def test_direct_authority_amendment_revokes_old_basis_without_circular_grant(self) -> None:
        self.establish_g0()
        old_context = self.current_authority()["id"]
        new_context = self.amend(scopes=[])
        self.assertNotEqual(old_context, new_context)
        self.assertEqual(self.record()["capabilities"]["local-change"]["authority"], "unknown")
        resurrected = self.cli(
            "capability",
            "set",
            "resurrected",
            "--available",
            "yes",
            "--authority",
            "granted",
            "--basis",
            old_context,
            "--rationale",
            "Try old authority",
            mutate=True,
            check=False,
        )
        self.assertNotEqual(resurrected.returncode, 0)
        self.assertIn("current canonical", resurrected.stderr)

    def test_terminal_claims_and_audits_are_bound_to_authority_and_endpoint(self) -> None:
        self.checkpoint("terminal-authority")
        self.cli(
            "claim", "add", "old-terminal", "--gate", "G8", "--kind", "terminal",
            "--summary", "Complete under the current authority", "--terminal-outcome", "complete",
            mutate=True,
        )
        audit = json.loads(
            self.cli(
                "evidence", "add", "old-audit", "--kind", "terminal-audit", "--result", "pass",
                "--checkpoint", "terminal-authority", "--artifact-digest", sha("old-audit"),
                "--claim", "old-terminal", "--invalidate-on", "design-change", mutate=True,
            ).stdout
        )
        self.assertIn("authority-change", audit["invalidated_by"])
        before = self.record()
        self.assertTrue(
            ticketctl.current_terminal_claim(
                before, "complete", ticketctl.git_fingerprint(self.repo), self.record_path
            )
        )
        self.amend(endpoint="local", scopes=["local-change"])
        same_endpoint = self.record()
        self.assertEqual(same_endpoint["evidence"]["old-audit"]["invalidated"]["event"], "authority-change")
        self.assertFalse(
            ticketctl.current_terminal_claim(
                same_endpoint, "complete", ticketctl.git_fingerprint(self.repo), self.record_path
            )
        )
        self.assertNotEqual(
            same_endpoint["claims"]["old-terminal"]["authority_revision"],
            same_endpoint["run"]["authority_revision"],
        )

        self.cli(
            "claim", "add", "new-terminal", "--gate", "G8", "--kind", "terminal",
            "--summary", "Complete under the amended endpoint", "--terminal-outcome", "complete",
            mutate=True,
        )
        self.cli(
            "evidence", "add", "new-audit", "--kind", "terminal-audit", "--result", "pass",
            "--checkpoint", "terminal-authority", "--artifact-digest", sha("new-audit"),
            "--claim", "new-terminal", mutate=True,
        )
        self.amend(endpoint="merge", scopes=["local-change"])
        changed_endpoint = self.record()
        self.assertNotEqual(
            changed_endpoint["claims"]["new-terminal"]["requested_endpoint"],
            changed_endpoint["run"]["requested_endpoint"],
        )
        self.assertFalse(
            ticketctl.current_terminal_claim(
                changed_endpoint, "complete", ticketctl.git_fingerprint(self.repo), self.record_path
            )
        )

    def test_terminal_endpoint_compatibility_is_explicit(self) -> None:
        endpoints = ticketctl.REQUESTED_ENDPOINTS | ticketctl.LEGACY_REQUESTED_ENDPOINTS
        for endpoint in endpoints:
            with self.subTest(status="complete", endpoint=endpoint):
                self.assertTrue(ticketctl.terminal_matches_endpoint("complete", endpoint))
            with self.subTest(status="merge-ready-awaiting-human", endpoint=endpoint):
                self.assertEqual(
                    ticketctl.terminal_matches_endpoint("merge-ready-awaiting-human", endpoint),
                    endpoint == "merge",
                )
            for status in ("resolved-no-change", "partial", "blocked"):
                with self.subTest(status=status, endpoint=endpoint):
                    self.assertTrue(ticketctl.terminal_matches_endpoint(status, endpoint))
        self.assertFalse(ticketctl.terminal_matches_endpoint("complete", "unknown"))
        self.assertFalse(ticketctl.terminal_matches_endpoint("merge-ready-awaiting-human", "unknown"))

    def test_pr_slot_target_is_canonical_domain_separated_and_input_sensitive(self) -> None:
        fields = {
            "provider": "github",
            "target_repo": "acme/widgets",
            "target_ref": "refs/heads/main",
            "head_repo": "contributor/widgets",
            "head_ref": "refs/heads/ticket-123",
            "work_unit": "delivery",
        }

        def derive(overrides: dict[str, str] | None = None) -> dict[str, object]:
            values = fields | (overrides or {})
            arguments = ["target", "derive-pr-slot"]
            for name in (
                "provider",
                "target_repo",
                "target_ref",
                "head_repo",
                "head_ref",
                "work_unit",
            ):
                arguments.extend((f"--{name.replace('_', '-')}", values[name]))
            return json.loads(self.cli(*arguments).stdout)

        first = derive()
        second = derive()
        canonical_fields = {
            "domain": ticketctl.PR_SLOT_DOMAIN,
            "schema_version": 1,
            **fields,
        }
        expected = hashlib.sha256(ticketctl.canonical_json(canonical_fields)).hexdigest()
        self.assertEqual(first, second)
        self.assertEqual(first["digest"], expected)
        self.assertEqual(first["target_kind"], "pr")
        self.assertEqual(
            set(first), {"algorithm", "domain", "schema_version", "target_kind", "digest"}
        )
        other_domain = hashlib.sha256(
            ticketctl.canonical_json(canonical_fields | {"domain": "ticketctl.other-slot"})
        ).hexdigest()
        self.assertNotEqual(first["digest"], other_domain)

        variations = {
            "provider": "gitlab",
            "target_repo": "acme/other-widgets",
            "target_ref": "refs/heads/release",
            "head_repo": "other-contributor/widgets",
            "head_ref": "refs/heads/ticket-456",
            "work_unit": "delivery-two",
        }
        for field, value in variations.items():
            with self.subTest(field=field):
                self.assertNotEqual(derive({field: value})["digest"], first["digest"])

        invalid = (
            {"provider": ""},
            {"target_repo": "https://example.invalid/private"},
            {"head_ref": " refs/heads/untrimmed"},
            {"work_unit": "invalid/work-unit"},
        )
        for override in invalid:
            values = fields | override
            arguments = ["target", "derive-pr-slot"]
            for name in (
                "provider",
                "target_repo",
                "target_ref",
                "head_repo",
                "head_ref",
                "work_unit",
            ):
                arguments.extend((f"--{name.replace('_', '-')}", values[name]))
            with self.subTest(invalid=override):
                self.assertNotEqual(self.cli(*arguments, check=False).returncode, 0)

    def test_remote_ref_target_is_deterministic_domain_separated_and_input_sensitive(self) -> None:
        fields = {
            "provider": "github",
            "repository": "acme/widgets",
            "ref": "refs/heads/ticket-123",
            "work_unit": "delivery",
        }

        def derive(overrides: dict[str, str] | None = None) -> dict[str, object]:
            values = fields | (overrides or {})
            return json.loads(
                self.cli(
                    "target", "derive-remote-ref", "--provider", values["provider"],
                    "--repository", values["repository"], "--ref", values["ref"],
                    "--work-unit", values["work_unit"],
                ).stdout
            )

        first = derive()
        self.assertEqual(first, derive())
        self.assertEqual(first["domain"], ticketctl.REMOTE_REF_DOMAIN)
        self.assertEqual(first["target_kind"], "remote")
        self.assertNotEqual(
            first["digest"],
            hashlib.sha256(
                ticketctl.canonical_json(
                    {"domain": ticketctl.PR_SLOT_DOMAIN, "schema_version": 1, **fields}
                )
            ).hexdigest(),
        )
        for field, value in {
            "provider": "gitlab",
            "repository": "acme/other",
            "ref": "refs/heads/other",
            "work_unit": "delivery-two",
        }.items():
            with self.subTest(field=field):
                self.assertNotEqual(first["digest"], derive({field: value})["digest"])

    def test_authority_and_action_scaffolds_are_bounded_valid_and_exclusive(self) -> None:
        request_path = Path(self.temporary.name) / "trusted-request.txt"
        request_path.write_text("Bounded implementation request\n", encoding="utf-8")
        local_path = Path(self.temporary.name) / "local-authority.json"
        local_result = json.loads(
            self.cli(
                "authority", "scaffold", "--preset", "local",
                "--trusted-request-file", os.fspath(request_path),
                "--output", os.fspath(local_path),
            ).stdout
        )
        local = ticketctl.validate_authority_envelope(
            json.loads(local_path.read_text(encoding="utf-8"))
        )
        self.assertEqual(local_result["preset"], "local")
        self.assertEqual(local["trusted_turn_digest"], ticketctl.file_digest(request_path))
        self.assertEqual(local["allowed_scopes"], ["local-change"])
        self.assertEqual(local["allowed_action_kinds"], [])
        self.assertEqual(local["allowed_effects"], [])
        self.assertEqual(local["max_actions"], 0)
        self.assertEqual(local_path.stat().st_mode & 0o777, 0o600)
        original = local_path.read_bytes()
        overwrite = self.cli(
            "authority", "scaffold", "--preset", "local",
            "--trusted-request-file", os.fspath(request_path),
            "--output", os.fspath(local_path), check=False,
        )
        self.assertNotEqual(overwrite.returncode, 0)
        self.assertEqual(local_path.read_bytes(), original)
        invalid_local = self.cli(
            "authority", "scaffold", "--preset", "local",
            "--trusted-request-file", os.fspath(request_path),
            "--max-actions", "1", "--output", os.fspath(Path(self.temporary.name) / "bad.json"),
            check=False,
        )
        self.assertNotEqual(invalid_local.returncode, 0)

        remote = ticketctl.derive_remote_ref_digest(
            provider="github", repository="acme/widgets",
            ref="refs/heads/ticket-123", work_unit="delivery",
        )
        pr = ticketctl.derive_pr_slot_digest(
            provider="github", target_repo="acme/widgets", target_ref="refs/heads/main",
            head_repo="acme/widgets", head_ref="refs/heads/ticket-123", work_unit="delivery",
        )
        merge_ready_path = Path(self.temporary.name) / "merge-ready-authority.json"
        self.cli(
            "authority", "scaffold", "--preset", "merge-ready-pr",
            "--trusted-request-file", os.fspath(request_path),
            "--remote-target-digest", remote, "--pr-target-digest", pr,
            "--max-actions", "5", "--output", os.fspath(merge_ready_path),
        )
        merge_ready = ticketctl.validate_authority_envelope(
            json.loads(merge_ready_path.read_text(encoding="utf-8"))
        )
        self.assertEqual(merge_ready["allowed_scopes"], ["local-change", "external-writes"])
        self.assertEqual(
            merge_ready["allowed_action_kinds"], ["create-pr", "push", "update-pr"]
        )
        self.assertEqual(merge_ready["allowed_effects"], [])
        self.assertEqual(merge_ready["allowed_target_digests"], sorted([remote, pr]))
        self.assertEqual(merge_ready["max_actions"], 5)
        self.assertNotIn("merge", merge_ready["allowed_scopes"])
        self.assertNotIn("merge", merge_ready["allowed_action_kinds"])
        self.assertIn("merge", merge_ready["denials"])
        for max_actions in ("0", "1", "not-an-integer"):
            with self.subTest(max_actions=max_actions):
                rejected = self.cli(
                    "authority", "scaffold", "--preset", "merge-ready-pr",
                    "--trusted-request-file", os.fspath(request_path),
                    "--remote-target-digest", remote, "--pr-target-digest", pr,
                    "--max-actions", max_actions,
                    "--output", os.fspath(Path(self.temporary.name) / f"bad-{max_actions}.json"),
                    check=False,
                )
                self.assertNotEqual(rejected.returncode, 0)

        action_path = Path(self.temporary.name) / "push-action.json"
        action_result = json.loads(
            self.cli(
                "action", "scaffold", "--kind", "push", "--target-kind", "remote",
                "--target-digest", remote, "--revision-digest", "a" * 64,
                "--payload-digest", "b" * 64, "--work-unit", "delivery",
                "--output", os.fspath(action_path),
            ).stdout
        )
        manifest, digest = ticketctl.load_action_manifest(os.fspath(action_path))
        self.assertEqual(action_result["request_digest"], digest)
        self.assertEqual(manifest["effects"], [])
        self.assertEqual(action_path.stat().st_mode & 0o777, 0o600)
        action_overwrite = self.cli(
            "action", "scaffold", "--kind", "push", "--target-kind", "remote",
            "--target-digest", remote, "--revision-digest", "a" * 64,
            "--payload-digest", "b" * 64, "--work-unit", "delivery",
            "--output", os.fspath(action_path), check=False,
        )
        self.assertNotEqual(action_overwrite.returncode, 0)
        wrong_target = self.cli(
            "action", "scaffold", "--kind", "push", "--target-kind", "pr",
            "--target-digest", pr, "--revision-digest", "a" * 64,
            "--payload-digest", "b" * 64, "--work-unit", "delivery",
            "--output", os.fspath(Path(self.temporary.name) / "wrong-action.json"), check=False,
        )
        self.assertNotEqual(wrong_target.returncode, 0)

    def test_multi_pr_authority_scaffold_bootstraps_two_work_units(self) -> None:
        request_path = Path(self.temporary.name) / "multi-pr-request.txt"
        request_path.write_text("Deliver the two-unit PR DAG\n", encoding="utf-8")
        units = ("delivery-one", "delivery-two")
        remote_targets = [
            ticketctl.derive_remote_ref_digest(
                provider="github",
                repository="acme/widgets",
                ref=f"refs/heads/{unit}",
                work_unit=unit,
            )
            for unit in units
        ]
        pr_targets = [
            ticketctl.derive_pr_slot_digest(
                provider="github",
                target_repo="acme/widgets",
                target_ref="refs/heads/main",
                head_repo="acme/widgets",
                head_ref=f"refs/heads/{unit}",
                work_unit=unit,
            )
            for unit in units
        ]
        authority_path = Path(self.temporary.name) / "multi-pr-authority.json"
        arguments = [
            "authority", "scaffold", "--preset", "merge-ready-pr",
            "--trusted-request-file", os.fspath(request_path),
        ]
        for remote, pr in zip(remote_targets, pr_targets, strict=True):
            arguments.extend(("--remote-target-digest", remote, "--pr-target-digest", pr))
        arguments.extend(("--max-actions", "6", "--output", os.fspath(authority_path)))
        other_ticket = "multi-pr-ticket"
        self.cli(*arguments, ticket=other_ticket)
        envelope = ticketctl.validate_authority_envelope(
            json.loads(authority_path.read_text(encoding="utf-8"))
        )
        self.assertEqual(
            envelope["allowed_target_digests"], sorted(remote_targets + pr_targets)
        )
        self.assertEqual(envelope["max_actions"], 6)

        record_path = Path(self.temporary.name) / "multi-pr-run" / "record.json"
        self.cli(
            "init", "--authority-envelope", os.fspath(authority_path),
            ticket=other_ticket, record=record_path,
        )
        bootstrapped = json.loads(record_path.read_text(encoding="utf-8"))
        root_envelope = bootstrapped["contexts"]["authority.root"]["envelope"]
        self.assertEqual(root_envelope["allowed_target_digests"], sorted(remote_targets + pr_targets))
        self.assertEqual(bootstrapped["run"]["requested_endpoint"], "merge-ready-pr")

        invalid_cases = (
            (
                ["--remote-target-digest", remote_targets[0]],
                "equal nonzero",
            ),
            (
                [
                    "--remote-target-digest", remote_targets[0],
                    "--pr-target-digest", remote_targets[0],
                ],
                "globally distinct",
            ),
            (
                [
                    "--remote-target-digest", remote_targets[0],
                    "--pr-target-digest", pr_targets[0],
                    "--remote-target-digest", remote_targets[1],
                    "--pr-target-digest", pr_targets[1],
                ],
                "at least 4",
            ),
        )
        for index, (targets, message) in enumerate(invalid_cases):
            with self.subTest(case=index):
                rejected = self.cli(
                    "authority", "scaffold", "--preset", "merge-ready-pr",
                    "--trusted-request-file", os.fspath(request_path), *targets,
                    "--max-actions", "3",
                    "--output", os.fspath(Path(self.temporary.name) / f"invalid-multi-{index}.json"),
                    ticket=f"invalid-multi-{index}", check=False,
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(message, rejected.stderr)

    def test_routine_profile_is_atomic_sparse_and_does_not_prove_outcomes(self) -> None:
        result = json.loads(
            self.cli(
                "profile", "apply-routine",
                "--repository-instructions-digest", "1" * 64,
                "--starting-state-digest", "2" * 64,
                "--classification-digest", "3" * 64,
                "--rationale", "Bounded local inspection found no routed risk",
                mutate=True,
            ).stdout
        )
        record = self.record()
        self.assertEqual(result["current_gate"], "G0")
        self.assertEqual(record["contexts"]["repository-instructions"]["digest"], "1" * 64)
        self.assertEqual(record["contexts"]["starting-state"]["digest"], "2" * 64)
        self.assertEqual(record["contexts"]["routine-classification"]["digest"], "3" * 64)
        self.assertTrue(all(trigger["decision"] == "no" for trigger in record["triggers"].values()))
        capability = record["capabilities"]["local-change"]
        self.assertTrue(ticketctl.capability_is_current(record, capability))
        self.assertEqual(capability["basis"], "authority.root")
        for collection in ("claims", "evidence", "findings", "work_units", "actions", "effects"):
            self.assertFalse(record[collection], collection)
        evaluation = json.loads(self.cli("gate").stdout)
        g1 = next(gate for gate in evaluation["gates"] if gate["gate"] == "G1")
        self.assertFalse(g1["passed"])
        repeated = self.cli(
            "profile", "apply-routine", "--repository-instructions-digest", "1" * 64,
            "--starting-state-digest", "2" * 64, "--classification-digest", "3" * 64,
            "--rationale", "Bounded local inspection found no routed risk",
            mutate=True, check=False,
        )
        self.assertNotEqual(repeated.returncode, 0)

    def test_routine_profile_refuses_dirty_nonlocal_or_started_work(self) -> None:
        arguments = (
            "profile", "apply-routine", "--repository-instructions-digest", "1" * 64,
            "--starting-state-digest", "2" * 64, "--classification-digest", "3" * 64,
            "--rationale", "Bounded local inspection found no routed risk",
        )
        (self.repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
        dirty = self.cli(*arguments, mutate=True, check=False)
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("clean Git worktree", dirty.stderr)
        (self.repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.cli("work", "add", "started", "--summary", "Already started", mutate=True)
        started = self.cli(*arguments, mutate=True, check=False)
        self.assertNotEqual(started.returncode, 0)
        self.assertIn("control-record work has started", started.stderr)
        self.amend(endpoint="merge-ready-pr", scopes=["local-change"])
        nonlocal_result = self.cli(*arguments, mutate=True, check=False)
        self.assertNotEqual(nonlocal_result.returncode, 0)
        self.assertIn("only for local or static-fact", nonlocal_result.stderr)

    def test_action_transition_matrix_and_parser_vocabulary_are_fail_closed(self) -> None:
        expected_transitions = {
            "prepared": {"applied-unverified", "uncertain", "verified-not-applied"},
            "applied-unverified": {"verified-applied", "verified-not-applied", "uncertain"},
            "uncertain": {"verified-applied", "verified-not-applied", "uncertain"},
            "verified-applied": set(),
            "verified-not-applied": set(),
        }
        for source in ticketctl.ACTION_STATES:
            for target in ticketctl.ACTION_STATES:
                with self.subTest(source=source, target=target):
                    self.assertEqual(
                        target in ticketctl.ACTION_TRANSITIONS[source],
                        target in expected_transitions[source],
                    )
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                ticketctl.build_parser().parse_args(["action", "settle", "write", "--outcome", "applied"])
            with self.assertRaises(SystemExit):
                ticketctl.build_parser().parse_args(["finding", "add", "f", "--origin", "review"])

    def test_action_targets_and_revision_provenance_are_kind_specific(self) -> None:
        self.checkpoint("target-types")
        checkpoint = self.record()["checkpoints"]["target-types"]
        head = checkpoint["dimensions"]["head"]
        self.cli("work", "add", "unit", "--summary", "Targeted delivery", mutate=True)
        self.cli(
            "work", "coordinate", "unit", "--branch-digest", "1" * 64,
            "--worktree-digest", "2" * 64, "--base-digest", "3" * 64,
            "--head-digest", head, "--remote-digest", "4" * 64, "--pr-digest", "5" * 64,
            "--evidence-epoch", "target-types", mutate=True,
        )
        record = self.record()

        def coherence(
            kind: str,
            target_kind: str,
            target_digest: str,
            revision_digest: str = head,
            work_unit: str | None = None,
        ) -> str | None:
            return ticketctl.action_coherence_error(
                record,
                {
                    "kind": kind,
                    "target_kind": target_kind,
                    "target_digest": target_digest,
                    "revision_digest": revision_digest,
                    "work_unit": work_unit,
                    "checkpoint": "target-types",
                },
            )

        self.assertIsNone(coherence("push", "remote", "4" * 64, work_unit="unit"))
        self.assertIsNone(coherence("create-pr", "pr", "5" * 64, work_unit="unit"))
        self.assertIsNone(coherence("tracker-write", "tracker", record["run"]["ticket_digest"]))
        self.assertIsNone(coherence("deploy", "environment", checkpoint["dimensions"]["environment"]))
        self.assertIsNone(coherence("release", "artifact", checkpoint["dimensions"]["build"]))
        self.assertIn("canonical remote", coherence("push", "remote", "5" * 64, work_unit="unit") or "")
        self.assertIn("target kind", coherence("push", "pr", "5" * 64, work_unit="unit") or "")
        self.assertIn("canonical tracker", coherence("tracker-write", "tracker", "6" * 64) or "")
        self.assertIn("canonical environment", coherence("deploy", "environment", head) or "")
        self.assertIn("canonical artifact", coherence("release", "artifact", checkpoint["dimensions"]["environment"]) or "")
        self.assertIn("revision", coherence("deploy", "environment", checkpoint["dimensions"]["environment"], "7" * 64) or "")

    def test_index_intent_and_no_change_detect_rm_cached_with_same_bytes(self) -> None:
        before = ticketctl.git_fingerprint(self.repo)
        self.git("rm", "--cached", "tracked.txt")
        after = ticketctl.git_fingerprint(self.repo)
        self.assertEqual(before["digest"], after["digest"])
        self.assertNotEqual(before["intent_digest"], after["intent_digest"])
        errors = ticketctl.resolved_no_change_errors(self.record(), self.repo)
        self.assertTrue(any("tracked/index/intent delta" in error for error in errors))

    def test_blocked_g1_still_reports_dependency_ready_work(self) -> None:
        self.establish_g0()
        self.cli(
            "claim", "add", "acceptance", "--gate", "G1", "--kind", "acceptance",
            "--summary", "The intended outcome is known", mutate=True,
        )
        self.cli(
            "claim", "add", "risk", "--gate", "G1", "--kind", "risk",
            "--summary", "The material risk is known", mutate=True,
        )
        self.cli(
            "evidence", "add", "g1-proof", "--kind", "inspection", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("g1-proof"),
            "--claim", "acceptance", "--claim", "risk", "--obligation", "define-outcome",
            mutate=True,
        )
        self.cli(
            "obligation", "resolve", "define-outcome", "--status", "blocked",
            "--evidence", "g1-proof", "--rationale", "A decision is unavailable", mutate=True,
        )
        self.cli("work", "add", "independent", "--summary", "Safe independent work", mutate=True)
        result = json.loads(self.cli("next").stdout)
        self.assertEqual(result["gate"], "G1")
        self.assertIn("independent", result["eligible_work_units"])
        reason_arguments: list[str] = []
        for reason_digest in result["reason_digests"]:
            reason_arguments.extend(("--reason-digest", reason_digest))
        self.cli(
            "evidence", "add", "blocked-proof", "--kind", "blocker", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("blocked-proof"),
            "--obligation", "define-outcome", *reason_arguments, mutate=True,
        )
        self.cli(
            "obligation", "resolve", "define-outcome", "--status", "blocked",
            "--evidence", "blocked-proof", "--rationale", "A decision is unavailable", mutate=True,
        )
        blocked = self.cli(
            "finish", "--status", "blocked", "--rationale", "Waiting for a decision",
            "--blocked-obligation", "define-outcome", "--next-action", "Obtain the decision",
            "--needed-evidence", "A trusted decision", *reason_arguments, mutate=True, check=False,
        )
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("eligible work units remain: independent", blocked.stderr)
        partial = json.loads(
            self.cli(
                "finish", "--status", "partial", "--rationale", "Forced handoff",
                "--blocked-obligation", "define-outcome", "--next-action", "Complete independent work",
                "--needed-evidence", "Implementation evidence", *reason_arguments, mutate=True,
            ).stdout
        )
        self.assertEqual(partial["status"], "partial")

    def test_graph_cycles_and_optional_prerequisites_fail_required_path(self) -> None:
        self.cli("work", "add", "optional-parent", "--summary", "Optional parent", "--optional", mutate=True)
        self.cli(
            "work",
            "add",
            "required-child",
            "--summary",
            "Required child",
            "--depends-on",
            "optional-parent",
            mutate=True,
        )
        cycle = self.cli(
            "work",
            "set",
            "optional-parent",
            "--status",
            "active",
            "--depends-on",
            "required-child",
            mutate=True,
            check=False,
        )
        self.assertNotEqual(cycle.returncode, 0)
        self.assertIn("cycle", cycle.stderr)
        gate = json.loads(self.cli("gate").stdout)
        g3 = next(item for item in gate["gates"] if item["gate"] == "G3")
        self.assertTrue(any("optional-parent" in reason and "required work path" in reason for reason in g3["reasons"]))

    def test_transitive_required_closure_is_shared_by_work_and_delivery_gates(self) -> None:
        self.cli("work", "add", "foundation", "--summary", "Required foundation", "--optional", mutate=True)
        self.cli(
            "work", "add", "enabler", "--summary", "Required enabler", "--optional",
            "--depends-on", "foundation", mutate=True,
        )
        self.cli(
            "work", "add", "delivery", "--summary", "Required delivery",
            "--depends-on", "enabler", mutate=True,
        )
        self.cli("work", "add", "unrelated", "--summary", "Unrelated optional work", "--optional", mutate=True)
        self.cli(
            "trigger", "set", "external-writes", "--decision", "yes",
            "--rationale", "The required path is externally delivered", mutate=True,
        )
        self.assertEqual(
            ticketctl.required_work_unit_ids(self.record()["work_units"]),
            {"foundation", "enabler", "delivery"},
        )
        gates = {item["gate"]: item for item in json.loads(self.cli("gate").stdout)["gates"]}
        for gate in ("G2", "G3", "G6", "G7"):
            joined = "\n".join(gates[gate]["reasons"])
            self.assertIn("foundation", joined, gate)
            self.assertNotIn("unrelated", joined, gate)

    def test_static_oracle_is_narrowly_compatible_with_g4_and_g8_only(self) -> None:
        self.amend(endpoint="static-fact", scopes=["local-change"])
        self.checkpoint("static")
        self.cli(
            "evidence",
            "add",
            "static-proof",
            "--kind",
            "inspection",
            "--result",
            "pass",
            "--checkpoint",
            "static",
            "--artifact-digest",
            "6" * 64,
            "--static-oracle-digest",
            "7" * 64,
            "--surface-digest",
            "8" * 64,
            "--oracle-actor-digest",
            "9" * 64,
            mutate=True,
        )
        record = self.record()
        current = ticketctl.git_fingerprint(self.repo)
        self.assertTrue(ticketctl.any_fresh_evidence(record, ["static-proof"], current, "G4"))
        self.assertTrue(ticketctl.any_fresh_evidence(record, ["static-proof"], current, "G8"))
        self.assertFalse(ticketctl.any_fresh_evidence(record, ["static-proof"], current, "G5"))

    def test_one_whole_delta_review_can_declare_multiple_lenses(self) -> None:
        self.checkpoint("review")
        partial = json.loads(
            self.cli(
                "evidence", "add", "partial-review", "--kind", "review", "--result", "pass",
                "--checkpoint", "review", "--artifact-digest", sha("partial-review"),
                "--review-lens", "correctness", "--reviewer-digest", "6" * 64,
                "--review-input-digest", "7" * 64, mutate=True,
            ).stdout
        )
        self.assertEqual(partial["review_lenses"], ["correctness"])
        partial_g5 = next(
            item for item in json.loads(self.cli("gate").stdout)["gates"] if item["gate"] == "G5"
        )
        self.assertTrue(any("review lenses are missing" in reason for reason in partial_g5["reasons"]))

        arguments = [
            "evidence", "add", "whole-delta-review", "--kind", "review", "--result", "pass",
            "--checkpoint", "review", "--artifact-digest", sha("whole-delta-review"),
            "--reviewer-digest", "8" * 64, "--review-input-digest", "9" * 64,
        ]
        for lens in sorted(ticketctl.REVIEW_LENSES):
            arguments.extend(("--review-lens", lens))
        complete = json.loads(self.cli(*arguments, mutate=True).stdout)
        self.assertEqual(set(complete["review_lenses"]), ticketctl.REVIEW_LENSES)
        complete_g5 = next(
            item for item in json.loads(self.cli("gate").stdout)["gates"] if item["gate"] == "G5"
        )
        self.assertFalse(any("review lenses are missing" in reason for reason in complete_g5["reasons"]))

    def test_resolved_no_change_is_an_honest_success_for_a_later_endpoint(self) -> None:
        self.amend(endpoint="deploy", scopes=["local-change"])
        self.establish_g0()
        self.cli(
            "claim", "add", "acceptance", "--gate", "G1", "--kind", "acceptance",
            "--summary", "The requested change is already present", mutate=True,
        )
        self.cli(
            "claim", "add", "risk", "--gate", "G1", "--kind", "risk",
            "--summary", "A false implementation claim would be harmful", mutate=True,
        )
        self.cli(
            "claim", "add", "no-change", "--gate", "G8", "--kind", "terminal",
            "--summary", "The repository already satisfies the request",
            "--terminal-outcome", "resolved-no-change", mutate=True,
        )
        self.cli(
            "evidence", "add", "outcome-proof", "--kind", "inspection", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("outcome-proof"),
            "--claim", "acceptance", "--claim", "risk", "--obligation", "define-outcome", mutate=True,
        )
        self.cli(
            "obligation", "resolve", "define-outcome", "--status", "satisfied",
            "--evidence", "outcome-proof", mutate=True,
        )
        self.cli(
            "evidence", "add", "terminal-proof", "--kind", "terminal-audit", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("terminal-proof"),
            "--claim", "no-change", "--obligation", "terminal-audit", mutate=True,
        )
        self.cli(
            "obligation", "resolve", "terminal-audit", "--status", "satisfied",
            "--evidence", "terminal-proof", mutate=True,
        )
        terminal = json.loads(
            self.cli(
                "finish", "--status", "resolved-no-change",
                "--rationale", "The exact requested behavior already exists", mutate=True,
            ).stdout
        )
        self.assertEqual(terminal["status"], "resolved-no-change")
        self.assertTrue(json.loads(self.cli("show").stdout)["terminal_current"])

    def test_no_change_claims_never_weaken_a_complete_merge_finish(self) -> None:
        self.amend(endpoint="merge", scopes=["local-change"])
        self.establish_g0()
        self.satisfy_implementation_gates()

        def assert_complete_rejected() -> None:
            gate = json.loads(self.cli("gate").stdout)
            self.assertEqual(gate["current_gate"], "G0")
            self.assertTrue(any("requires trigger merge=yes" in reason for reason in gate["gates"][0]["reasons"]))
            rejected = self.cli(
                "finish", "--status", "complete", "--rationale", "Do not bypass merge",
                mutate=True, check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("earliest failing gate is G0", rejected.stderr)

        self.cli(
            "claim", "add", "optional-no-change", "--gate", "G8", "--kind", "terminal",
            "--summary", "Optional no-change hypothesis", "--terminal-outcome", "resolved-no-change",
            "--optional", mutate=True,
        )
        assert_complete_rejected()
        self.cli(
            "claim", "add", "required-no-change", "--gate", "G8", "--kind", "terminal",
            "--summary", "Required no-change hypothesis", "--terminal-outcome", "resolved-no-change",
            mutate=True,
        )
        self.cli(
            "evidence", "add", "no-change-proof", "--kind", "terminal-audit", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("no-change-proof"),
            "--claim", "required-no-change", mutate=True,
        )
        assert_complete_rejected()

        self.cli(
            "checkpoint", "create", "new-external", "--base-digest", "1" * 64,
            "--config-digest", "2" * 64, "--build-digest", "3" * 64,
            "--environment-digest", "4" * 64, "--external-digest", "e" * 64, mutate=True,
        )
        self.cli("work", "coordinate", "delivery", "--evidence-epoch", "new-external", mutate=True)
        self.cli(
            "evidence", "add", "current-terminal-proof", "--kind", "terminal-audit", "--result", "pass",
            "--checkpoint", "new-external", "--artifact-digest", sha("current-terminal-proof"),
            "--claim", "terminal", "--obligation", "terminal-audit", mutate=True,
        )
        self.cli(
            "obligation", "resolve", "terminal-audit", "--status", "satisfied",
            "--evidence", "current-terminal-proof", mutate=True,
        )
        stale_reason = ticketctl.fresh_evidence_reason(
            self.record(), "no-change-proof", ticketctl.git_fingerprint(self.repo), self.record_path
        )
        self.assertIn("external", stale_reason or "")
        assert_complete_rejected()

    def test_action_manifest_is_bound_idempotent_reconciled_and_not_narrowable(self) -> None:
        target = "e" * 64
        head = "f" * 64
        authority_context = self.amend(
            scopes=["local-change", "external-writes"],
            kinds=["push"],
            targets=[target],
            max_actions=3,
        )
        self.cli(
            "trigger",
            "set",
            "external-writes",
            "--decision",
            "yes",
            "--rationale",
            "A push is requested",
            mutate=True,
        )
        self.cli(
            "capability",
            "set",
            "push-capability",
            "--available",
            "yes",
            "--authority",
            "granted",
            "--basis",
            authority_context,
            "--covers",
            "external-writes",
            "--action-kind",
            "push",
            "--target-digest",
            target,
            "--max-uses",
            "3",
            "--rationale",
            "Exact push authority",
            mutate=True,
        )
        self.checkpoint("action")
        self.cli("work", "add", "unit", "--summary", "Publish exact revision", mutate=True)
        coordinate_arguments = [
            "work", "coordinate", "unit", "--branch-digest", "1" * 64,
            "--worktree-digest", "2" * 64, "--base-digest", "3" * 64,
            "--head-digest", head, "--remote-digest", target, "--pr-digest", "4" * 64,
            "--evidence-epoch", "action",
        ]
        self.cli(*coordinate_arguments, mutate=True)
        manifest_path = Path(self.temporary.name) / "action.json"
        manifest = {
            "schema_version": 1,
            "kind": "push",
            "work_unit": "unit",
            "target_kind": "remote",
            "target_digest": target,
            "revision_digest": head,
            "payload_digest": "5" * 64,
            "effects": [],
            "predecessor_action": None,
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        prepare_arguments = [
            "action", "prepare", "push-one", "--capability", "push-capability",
            "--request-manifest", os.fspath(manifest_path), "--expected-state-digest", "6" * 64,
        ]
        first = json.loads(self.cli(*prepare_arguments, mutate=True).stdout)
        repeated = json.loads(self.cli(*prepare_arguments, mutate=True).stdout)
        self.assertEqual(first["idempotency_digest"], repeated["idempotency_digest"])
        duplicate = self.cli(*["action", "prepare", "push-two", *prepare_arguments[4:]], mutate=True, check=False)
        self.assertNotEqual(duplicate.returncode, 0)
        override = self.cli(*prepare_arguments, "--idempotency-digest", "7" * 64, mutate=True, check=False)
        self.assertNotEqual(override.returncode, 0)

        self.cli(
            "capability", "set", "push-capability", "--available", "yes", "--authority", "granted",
            "--basis", authority_context, "--covers", "external-writes", "--action-kind", "push",
            "--max-uses", "3", "--rationale", "Narrow target away", mutate=True,
        )
        narrowed = self.cli(
            "action", "arm", "push-one", "--observed-state-digest", "6" * 64,
            mutate=True, check=False,
        )
        self.assertNotEqual(narrowed.returncode, 0)
        self.assertIn("target", narrowed.stderr)

        self.cli(
            "capability", "set", "push-capability", "--available", "yes", "--authority", "granted",
            "--basis", authority_context, "--covers", "external-writes", "--action-kind", "push",
            "--target-digest", target, "--max-uses", "3", "--rationale", "Restore exact target", mutate=True,
        )
        self.cli("action", "arm", "push-one", "--observed-state-digest", "6" * 64, mutate=True)
        self.cli(
            "action", "settle", "push-one", "--outcome", "succeeded", "--receipt-digest", "7" * 64,
            "--observed-state-digest", "6" * 64, mutate=True,
        )
        self.cli(
            "action", "settle", "push-one", "--outcome", "verified-applied", "--receipt-digest", "8" * 64,
            "--observed-state-digest", "6" * 64, mutate=True,
        )
        observed = json.loads(
            self.cli(
                "effect", "observe", "push-receipt", "--action", "push-one", "--actor", "coordinator",
                "--actor-digest", "9" * 64, "--receipt-digest", "a" * 64, mutate=True,
            ).stdout
        )
        self.assertEqual(observed["work_unit"], "unit")

    def finish_external_delivery(
        self,
        *,
        endpoint: str,
        terminal_outcome: str,
        pending_merge: bool,
        historical_publish: bool = False,
    ) -> dict[str, object]:
        remote = "e" * 64
        pr = ticketctl.derive_pr_slot_digest(
            provider="github",
            target_repo="acme/widgets",
            target_ref="refs/heads/main",
            head_repo="acme/widgets",
            head_ref="refs/heads/ticket-delivery",
            work_unit="delivery",
        )
        authority_context = self.amend(
            endpoint=endpoint,
            scopes=["local-change", "external-writes", *(["merge"] if endpoint == "merge" else [])],
            kinds=["push", "create-pr", *(["update-pr"] if historical_publish else [])],
            targets=[remote, pr],
            max_actions=3 if historical_publish else 2,
        )
        self.establish_g0()
        self.cli(
            "trigger", "set", "external-writes", "--decision", "yes",
            "--rationale", "The trusted endpoint requests a remote branch and PR", mutate=True,
        )
        if endpoint == "merge":
            self.cli(
                "trigger", "set", "merge", "--decision", "yes",
                "--rationale", "The trusted endpoint requests a human merge", mutate=True,
            )
        covers = ["--covers", "external-writes"]
        if endpoint == "merge":
            covers.extend(("--covers", "merge"))
        capability_arguments = [
            "capability", "set", "delivery-capability", "--available", "yes",
            "--authority", "granted", "--basis", authority_context,
            *covers, "--action-kind", "push",
            "--action-kind", "create-pr", "--target-digest", remote,
            "--target-digest", pr, "--max-uses", "3" if historical_publish else "2",
            "--rationale", "Exact branch and PR delivery authority",
        ]
        if historical_publish:
            capability_arguments.extend(("--action-kind", "update-pr"))
        self.cli(*capability_arguments, mutate=True)
        head = self.satisfy_implementation_gates(
            remote=remote, pr=pr, terminal_outcome=terminal_outcome
        )

        manifest_path = Path(self.temporary.name) / "delivery-action.json"

        def apply_action(
            action_id: str,
            kind: str,
            target_kind: str,
            target: str,
            payload_digit: int,
        ) -> None:
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": kind,
                        "work_unit": "delivery",
                        "target_kind": target_kind,
                        "target_digest": target,
                        "revision_digest": head,
                        "payload_digest": str(payload_digit) * 64,
                        "effects": [],
                        "predecessor_action": None,
                    }
                ),
                encoding="utf-8",
            )
            self.cli(
                "action", "prepare", action_id, "--capability", "delivery-capability",
                "--request-manifest", os.fspath(manifest_path),
                "--expected-state-digest", "6" * 64, mutate=True,
            )
            self.cli(
                "action", "arm", action_id, "--observed-state-digest", "6" * 64,
                mutate=True,
            )
            self.cli(
                "action", "settle", action_id, "--outcome", "succeeded",
                "--receipt-digest", str(payload_digit + 2) * 64,
                "--observed-state-digest", "6" * 64, mutate=True,
            )
            self.cli(
                "action", "settle", action_id, "--outcome", "verified-applied",
                "--receipt-digest", str(payload_digit + 4) * 64,
                "--observed-state-digest", "6" * 64, mutate=True,
            )

        if historical_publish:
            self.checkpoint("prior-publication")
            apply_action("historical-pr-update", "update-pr", "pr", pr, 3)
            self.checkpoint("g0")
        apply_action("push-delivery", "push", "remote", remote, 1)
        apply_action("create-delivery-pr", "create-pr", "pr", pr, 2)

        pending_arguments = ["--pending", "merge"] if pending_merge else []
        self.cli(
            "evidence", "add", "host-proof", "--kind", "host-audit", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("host-proof"),
            "--obligation", "publish-authorized-work", "--obligation", "trigger.external-writes",
            "--obligation", "converge-remote", "--lanes", "complete", "--feedback", "none",
            "--automated-review", "complete", "--human-approval", "not-required",
            "--draft", "no", "--mergeable", "yes", "--work-unit", "delivery",
            "--revision-digest", head, "--target-digest", pr, *pending_arguments, mutate=True,
        )
        obligation_ids = [
            "publish-authorized-work",
            "trigger.external-writes",
            "converge-remote",
        ]
        if endpoint == "merge":
            obligation_ids.append("trigger.merge")
        for obligation_id in obligation_ids:
            self.cli(
                "obligation", "resolve", obligation_id, "--status", "satisfied",
                "--evidence", "host-proof", mutate=True,
            )

        gate = json.loads(self.cli("gate").stdout)
        self.assertIsNone(gate["current_gate"], gate)
        return json.loads(
            self.cli(
                "finish", "--status", terminal_outcome,
                "--rationale", "The remote branch and PR are current and converged", mutate=True,
            ).stdout
        )

    def test_merge_ready_external_delivery_reaches_guarded_complete(self) -> None:
        finished = self.finish_external_delivery(
            endpoint="merge-ready-pr",
            terminal_outcome="complete",
            pending_merge=False,
            historical_publish=True,
        )
        self.assertEqual(finished["status"], "complete")
        self.assertTrue(json.loads(self.cli("show").stdout)["terminal_current"])

    def test_merge_endpoint_can_finish_awaiting_only_the_human_merge(self) -> None:
        finished = self.finish_external_delivery(
            endpoint="merge", terminal_outcome="merge-ready-awaiting-human", pending_merge=True
        )
        self.assertEqual(finished["status"], "merge-ready-awaiting-human")
        self.assertTrue(json.loads(self.cli("show").stdout)["terminal_current"])

    def test_merge_ready_rejects_local_only_work_without_external_delivery(self) -> None:
        authority_context = self.amend(endpoint="merge", scopes=["local-change", "merge"])
        self.establish_g0()
        self.cli(
            "trigger", "set", "merge", "--decision", "yes",
            "--rationale", "A human merge is the requested endpoint", mutate=True,
        )
        self.cli(
            "capability", "set", "merge-capability", "--available", "yes",
            "--authority", "granted", "--basis", authority_context, "--covers", "merge",
            "--rationale", "The trusted request permits the named merge endpoint", mutate=True,
        )
        self.satisfy_implementation_gates(
            terminal_outcome="merge-ready-awaiting-human", remote=None, pr=None
        )
        self.cli(
            "evidence", "add", "merge-proof", "--kind", "remote", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("merge-proof"),
            "--obligation", "trigger.merge", mutate=True,
        )
        self.cli(
            "obligation", "resolve", "trigger.merge", "--status", "satisfied",
            "--evidence", "merge-proof", mutate=True,
        )
        self.assertIsNone(json.loads(self.cli("gate").stdout)["current_gate"])
        rejected = self.cli(
            "finish", "--status", "merge-ready-awaiting-human",
            "--rationale", "Awaiting a human merge", mutate=True, check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("requires external-writes=yes", rejected.stderr)

    def test_merge_ready_pr_complete_rejects_tracker_only_external_delivery(self) -> None:
        ticket_target = sha(self.ticket)
        remote = "e" * 64
        pr = ticketctl.derive_pr_slot_digest(
            provider="github",
            target_repo="acme/widgets",
            target_ref="refs/heads/main",
            head_repo="acme/widgets",
            head_ref="refs/heads/ticket-delivery",
            work_unit="delivery",
        )
        authority_context = self.amend(
            endpoint="merge-ready-pr",
            scopes=["local-change", "external-writes"],
            kinds=["tracker-write"],
            targets=[ticket_target],
            max_actions=1,
        )
        self.establish_g0()
        self.cli(
            "trigger", "set", "external-writes", "--decision", "yes",
            "--rationale", "Only a tracker projection was requested", mutate=True,
        )
        self.cli(
            "capability", "set", "tracker-capability", "--available", "yes",
            "--authority", "granted", "--basis", authority_context,
            "--covers", "external-writes", "--action-kind", "tracker-write",
            "--target-digest", ticket_target, "--max-uses", "1",
            "--rationale", "Exact tracker projection authority", mutate=True,
        )
        head = self.satisfy_implementation_gates(remote=remote, pr=pr)
        manifest_path = Path(self.temporary.name) / "tracker-action.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "tracker-write",
                    "work_unit": None,
                    "target_kind": "tracker",
                    "target_digest": ticket_target,
                    "revision_digest": head,
                    "payload_digest": "1" * 64,
                    "effects": [],
                    "predecessor_action": None,
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "action", "prepare", "tracker-only", "--capability", "tracker-capability",
            "--request-manifest", os.fspath(manifest_path),
            "--expected-state-digest", "6" * 64, mutate=True,
        )
        self.cli(
            "action", "arm", "tracker-only", "--observed-state-digest", "6" * 64,
            mutate=True,
        )
        self.cli(
            "action", "settle", "tracker-only", "--outcome", "succeeded",
            "--receipt-digest", "3" * 64, "--observed-state-digest", "6" * 64,
            mutate=True,
        )
        self.cli(
            "action", "settle", "tracker-only", "--outcome", "verified-applied",
            "--receipt-digest", "4" * 64, "--observed-state-digest", "6" * 64,
            mutate=True,
        )
        self.cli(
            "evidence", "add", "host-proof", "--kind", "host-audit", "--result", "pass",
            "--checkpoint", "g0", "--artifact-digest", sha("host-proof"),
            "--obligation", "publish-authorized-work", "--obligation", "trigger.external-writes",
            "--obligation", "converge-remote", "--lanes", "complete", "--feedback", "none",
            "--automated-review", "complete", "--human-approval", "not-required",
            "--draft", "no", "--mergeable", "yes", "--work-unit", "delivery",
            "--revision-digest", head, "--target-digest", pr, mutate=True,
        )
        for obligation_id in (
            "publish-authorized-work", "trigger.external-writes", "converge-remote"
        ):
            self.cli(
                "obligation", "resolve", obligation_id, "--status", "satisfied",
                "--evidence", "host-proof", mutate=True,
            )
        self.assertIsNone(json.loads(self.cli("gate").stdout)["current_gate"])
        rejected = self.cli(
            "finish", "--status", "complete", "--rationale", "Tracker is current",
            mutate=True, check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("PR delivery lacks a current applied push", rejected.stderr)
        self.assertIn("PR delivery lacks a current applied create/update PR action", rejected.stderr)

    def test_uncertain_action_cannot_self_claim_applied_without_a_linked_effect(self) -> None:
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["actions"]["uncertain"] = {
                "id": "uncertain",
                "kind": "push",
                "target_kind": "remote",
                "capability": "missing",
                "target_digest": "1" * 64,
                "request_digest": "2" * 64,
                "payload_digest": "3" * 64,
                "expected_state_digest": "4" * 64,
                "effects": [],
                "idempotency_digest": "5" * 64,
                "work_unit": "missing",
                "revision_digest": "6" * 64,
                "authority_revision": 1,
                "lease_epoch": 1,
                "checkpoint": None,
                "status": "uncertain",
                "receipt_digest": "7" * 64,
                "prepared_at": "now",
                "settled_at": "now",
            }
            store.commit(record, "test.uncertain", {}, bypass_lease=True)
        rejected = self.cli(
            "action", "settle", "uncertain", "--outcome", "verified-applied",
            "--receipt-digest", "8" * 64, "--observed-state-digest", "4" * 64,
            mutate=True, check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("effect", rejected.stderr)

    def test_takeover_reconciles_uncertain_action_and_allows_proven_absent_retry(self) -> None:
        target = "e" * 64
        head = "f" * 64
        authority_context = self.amend(
            scopes=["local-change", "external-writes"],
            kinds=["push"],
            targets=[target],
            max_actions=6,
        )
        self.cli(
            "trigger", "set", "external-writes", "--decision", "yes",
            "--rationale", "The requested push changes remote state", mutate=True,
        )
        self.cli(
            "capability", "set", "push-capability", "--available", "yes", "--authority", "granted",
            "--basis", authority_context, "--covers", "external-writes", "--action-kind", "push",
            "--target-digest", target, "--max-uses", "6", "--rationale", "Exact push authority",
            mutate=True,
        )
        self.checkpoint("action-recovery")
        self.cli("work", "add", "unit", "--summary", "Publish exact revision", mutate=True)
        self.cli(
            "work", "coordinate", "unit", "--branch-digest", "1" * 64,
            "--worktree-digest", "2" * 64, "--base-digest", "3" * 64,
            "--head-digest", head, "--remote-digest", target, "--pr-digest", "4" * 64,
            "--evidence-epoch", "action-recovery", mutate=True,
        )

        manifest_path = Path(self.temporary.name) / "recovery-action.json"

        def write_manifest(payload_digest: str, predecessor: str | None = None) -> None:
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "push",
                        "work_unit": "unit",
                        "target_kind": "remote",
                        "target_digest": target,
                        "revision_digest": head,
                        "payload_digest": payload_digest,
                        "effects": [],
                        "predecessor_action": predecessor,
                    }
                ),
                encoding="utf-8",
            )

        def prepare(action_id: str) -> dict[str, object]:
            return json.loads(
                self.cli(
                    "action", "prepare", action_id, "--capability", "push-capability",
                    "--request-manifest", os.fspath(manifest_path),
                    "--expected-state-digest", "6" * 64, mutate=True,
                ).stdout
            )

        write_manifest("7" * 64)
        uncertain = prepare("uncertain-write")
        self.cli(
            "action", "arm", "uncertain-write", "--observed-state-digest", "6" * 64,
            mutate=True,
        )
        self.cli(
            "action", "settle", "uncertain-write", "--outcome", "uncertain",
            "--receipt-digest", "8" * 64, mutate=True,
        )

        write_manifest("9" * 64)
        prepare("stale-prepared")
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["lease"]["expires_at"] = "2000-01-01T00:00:00Z"
            store.commit(record, "test.expire-lease", {}, bypass_lease=True)
        expired = self.record()
        takeover = json.loads(
            self.cli(
                "lease", "takeover", "--owner-digest", "b" * 64,
                "--expected-epoch", str(expired["lease"]["epoch"]),
                "--expected-journal-head", expired["run"]["journal_head"],
                "--reconciliation-digest", "c" * 64,
            ).stdout
        )
        self.token = takeover["token"]
        self.epoch = str(takeover["epoch"])

        stale_arm = self.cli(
            "action", "arm", "stale-prepared", "--observed-state-digest", "6" * 64,
            mutate=True, check=False,
        )
        self.assertNotEqual(stale_arm.returncode, 0)
        self.assertIn("stale coordinator lease epoch", stale_arm.stderr)

        self.cli(
            "effect", "observe", "uncertain-readback", "--action", "uncertain-write",
            "--actor", "coordinator", "--actor-digest", "d" * 64,
            "--receipt-digest", "a" * 64, mutate=True,
        )
        reconciled = json.loads(
            self.cli(
                "action", "settle", "uncertain-write", "--outcome", "verified-applied",
                "--receipt-digest", "a" * 64, "--effect", "uncertain-readback", mutate=True,
            ).stdout
        )
        self.assertEqual(reconciled["status"], "verified-applied")
        self.assertEqual(reconciled["reconciliation_effect"], "uncertain-readback")

        write_manifest("b" * 64)
        absent = prepare("absent-write")
        self.cli(
            "action", "settle", "absent-write", "--outcome", "verified-not-applied",
            "--receipt-digest", "c" * 64, mutate=True,
        )
        write_manifest("b" * 64, "absent-write")
        retry = prepare("retry-write")
        self.assertEqual(retry["correlation_digest"], absent["correlation_digest"])
        self.assertNotEqual(retry["idempotency_digest"], absent["idempotency_digest"])
        duplicate_retry = self.cli(
            "action", "prepare", "retry-write-two", "--capability", "push-capability",
            "--request-manifest", os.fspath(manifest_path),
            "--expected-state-digest", "6" * 64, mutate=True, check=False,
        )
        self.assertNotEqual(duplicate_retry.returncode, 0)
        self.assertIn("already has successor", duplicate_retry.stderr)
        self.cli(
            "action", "arm", "retry-write", "--observed-state-digest", "6" * 64,
            mutate=True,
        )

    def test_waiver_and_residual_acceptance_expire_with_targeted_capability(self) -> None:
        obligation_target = ticketctl.control_target_digest("obligation", "waivable")
        finding_target = ticketctl.control_target_digest("finding", "residual")
        authority_context = self.amend(
            scopes=["local-change", "accept-residual-risk"],
            targets=[obligation_target, finding_target],
        )
        self.cli(
            "capability", "set", "waiver", "--available", "yes", "--authority", "granted",
            "--basis", authority_context, "--covers", "accept-residual-risk",
            "--target-digest", obligation_target, "--target-digest", finding_target,
            "--rationale", "Explicit targeted residual acceptance", mutate=True,
        )
        self.checkpoint("waiver")
        self.cli(
            "evidence", "add", "waiver-proof", "--kind", "inspection", "--result", "pass",
            "--checkpoint", "waiver", "--artifact-digest", sha("waiver-proof"), mutate=True,
        )
        self.cli(
            "obligation", "add", "waivable", "--gate", "G2", "--kind", "decision",
            "--summary", "Explicitly waivable decision", "--waivable", mutate=True,
        )
        self.cli(
            "obligation", "resolve", "waivable", "--status", "waived",
            "--waiver-capability", "waiver", "--rationale", "Accepted by accountable user", mutate=True,
        )
        self.cli(
            "finding", "add", "residual", "--severity", "minor", "--origin", "introduced",
            "--summary", "Known bounded residual", mutate=True,
        )
        self.cli(
            "finding", "dispose", "residual", "--disposition", "accepted-residual",
            "--waiver-capability", "waiver", "--rationale", "Accepted by accountable user",
            "--evidence", "waiver-proof", mutate=True,
        )
        store = ticketctl.RecordStore(self.record_path)
        with store.lock():
            record = store.load()
            record["capabilities"]["waiver"]["expires_at"] = "2000-01-01T00:00:00Z"
            store.commit(record, "test.expire-waiver", {}, bypass_lease=True)
        record = self.record()
        current = ticketctl.git_fingerprint(self.repo)
        self.assertTrue(any("invalid waiver" in reason for reason in ticketctl.obligation_reasons(record, "G2", current)))
        g5 = next(item for item in ticketctl.evaluate(record, self.repo)["gates"] if item["gate"] == "G5")
        self.assertTrue(any("no longer authorized" in reason for reason in g5["reasons"]))


if __name__ == "__main__":
    unittest.main()
