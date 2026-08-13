#!/usr/bin/env python3
"""Durable, fail-closed control record for the solve-ticket workflow."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, TypedDict, cast


SCHEMA_VERSION = 1
GATES = tuple(f"G{number}" for number in range(9))
DECISIONS = {"yes", "no", "unknown"}
EVIDENCE_KINDS = {"inspection", "test", "live", "measurement", "review", "remote", "decision"}
CHECKPOINT_DIMENSIONS = {"candidate", "intent", "head", "base", "config", "build", "environment", "external"}
DEFAULT_EVIDENCE_DEPENDENCIES = {
    "inspection": ["candidate", "intent", "base", "config", "environment"],
    "test": ["candidate", "intent", "base", "config", "build", "environment"],
    "live": ["candidate", "intent", "base", "config", "build", "environment", "external"],
    "measurement": ["candidate", "intent", "base", "config", "build", "environment"],
    "review": ["candidate", "intent", "base", "config"],
    "remote": ["candidate", "intent", "head", "base", "external"],
    "host-audit": ["candidate", "intent", "head", "base", "external"],
    "terminal-audit": ["candidate", "intent", "head", "base", "config", "build", "environment", "external"],
    "blocker": ["candidate", "intent", "base", "config", "environment", "external"],
    "decision": ["candidate", "intent", "base", "config"],
}
EVIDENCE_KINDS = set(DEFAULT_EVIDENCE_DEPENDENCIES)
REVIEW_LENSES = {"outcome", "correctness", "safety", "evidence-operations", "architecture"}
GATE_EVIDENCE_KINDS = {
    "G0": {"inspection", "decision"},
    "G1": {"inspection", "test", "live", "measurement", "decision"},
    "G2": {"inspection", "review", "decision"},
    "G3": {"inspection", "test"},
    "G4": {"test", "live", "measurement"},
    "G5": {"review"},
    "G6": {"remote", "host-audit"},
    "G7": {"host-audit"},
    "G8": {"terminal-audit"},
}
INVALIDATION_EVENTS = {
    "source-change",
    "base-change",
    "remote-head-change",
    "design-change",
    "review-fix",
    "environment-change",
    "external-feedback",
    "authority-change",
}
ACTION_STATES = {
    "prepared",
    "applied-unverified",
    "uncertain",
    "verified-applied",
    "verified-not-applied",
}
ACTION_TRANSITIONS = {
    "prepared": {"applied-unverified", "uncertain", "verified-not-applied"},
    "applied-unverified": {"verified-applied", "verified-not-applied", "uncertain"},
    "uncertain": {"verified-applied", "verified-not-applied", "uncertain"},
    "verified-applied": set(),
    "verified-not-applied": set(),
}
TERMINAL_ACTION_STATES = {"verified-applied", "verified-not-applied"}
POSITIVE_TERMINALS = {"complete", "merge-ready-awaiting-human"}
NO_CHANGE_TERMINAL = "resolved-no-change"
SUCCESS_TERMINALS = POSITIVE_TERMINALS | {NO_CHANGE_TERMINAL}
TERMINALS = SUCCESS_TERMINALS | {"blocked", "partial"}
REQUESTED_ENDPOINTS = {
    "local",
    "static-fact",
    "merge-ready-pr",
    "merge",
    "deploy",
    "release",
    "close-ticket",
}
LEGACY_REQUESTED_ENDPOINTS = {"complete"}
PR_SLOT_DOMAIN = "ticketctl.pr-slot"
REMOTE_REF_DOMAIN = "ticketctl.remote-ref"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_TEXT_PATTERNS = (
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b"),
    re.compile(r"(?:^|\s)(?:/home/|/Users/|[A-Za-z]:\\)"),
    re.compile(r"\b(?:password|passwd|token|secret|cookie|authorization)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b(?:bearer|basic)\s+[A-Za-z0-9+/_.=-]{8,}", re.IGNORECASE),
)
DEFAULT_INVALIDATIONS = {
    "inspection": ["source-change", "base-change", "design-change", "review-fix"],
    "test": ["source-change", "base-change", "review-fix", "environment-change"],
    "live": ["source-change", "base-change", "review-fix", "environment-change"],
    "measurement": ["source-change", "base-change", "review-fix", "environment-change"],
    "review": ["source-change", "base-change", "design-change", "review-fix", "external-feedback"],
    "remote": ["source-change", "base-change", "remote-head-change", "external-feedback"],
    "decision": ["design-change", "authority-change", "external-feedback"],
    "host-audit": ["source-change", "base-change", "remote-head-change", "external-feedback"],
    "terminal-audit": ["source-change", "base-change", "remote-head-change", "environment-change", "external-feedback", "authority-change"],
    "blocker": ["source-change", "base-change", "environment-change", "external-feedback", "authority-change"],
}
ACTION_TRIGGER_REQUIREMENTS = {
    "merge": {"external-writes", "merge"},
    "deploy": {"external-writes", "deploy"},
    "release": {"external-writes", "release"},
    "close-ticket": {"external-writes", "close-ticket"},
    "branch-rewrite": {"external-writes", "branch-rewrite"},
    "contact-user": {"external-writes", "contact-users"},
    "destructive-financial-action": {"external-writes", "destructive-financial"},
}
ACTION_KINDS = {
    "push",
    "create-pr",
    "update-pr",
    "tracker-write",
    "comment",
    "resolve-thread",
    "merge",
    "deploy",
    "release",
    "close-ticket",
    "branch-rewrite",
    "contact-user",
    "destructive-financial-action",
    "auto-merge",
    "rollback",
    "production-read",
    "customer-read",
    "cleanup",
    "paid-action",
    "request-reviewer",
    "change-label",
    "reassign-ticket",
}
ACTION_TARGET_KINDS = {"remote", "pr", "tracker", "environment", "artifact", "external"}
ACTION_KIND_TARGETS = {
    "push": {"remote"},
    "create-pr": {"pr"},
    "update-pr": {"pr"},
    "tracker-write": {"tracker"},
    "comment": {"pr", "tracker"},
    "resolve-thread": {"pr"},
    "merge": {"pr"},
    "deploy": {"environment"},
    "release": {"artifact"},
    "close-ticket": {"tracker"},
    "branch-rewrite": {"remote"},
    "contact-user": {"external"},
    "destructive-financial-action": {"external"},
    "auto-merge": {"pr"},
    "rollback": {"environment"},
    "production-read": {"external"},
    "customer-read": {"external"},
    "cleanup": {"external"},
    "paid-action": {"external"},
    "request-reviewer": {"pr"},
    "change-label": {"pr", "tracker"},
    "reassign-ticket": {"tracker"},
}
ACTION_EFFECTS = {
    "force-update",
    "auto-merge-enable",
    "closing-semantics",
    "reviewer-request",
    "label-change",
    "ticket-close",
    "ticket-reassign",
    "user-notification",
    "production-read",
    "customer-read",
    "destructive",
    "paid",
    "cleanup",
}
CANONICAL_KIND_EFFECTS = {kind: set() for kind in ACTION_KINDS}
CANONICAL_KIND_EFFECTS.update(
    {
        "close-ticket": {"closing-semantics", "ticket-close"},
        "branch-rewrite": {"force-update"},
        "contact-user": {"user-notification"},
        "destructive-financial-action": {"destructive"},
        "auto-merge": {"auto-merge-enable"},
        "production-read": {"production-read"},
        "customer-read": {"customer-read"},
        "cleanup": {"cleanup"},
        "paid-action": {"paid"},
        "request-reviewer": {"reviewer-request"},
        "change-label": {"label-change"},
        "reassign-ticket": {"ticket-reassign"},
    }
)
EFFECT_TRIGGER_REQUIREMENTS = {
    "force-update": {"branch-rewrite"},
    "auto-merge-enable": {"auto-merge"},
    "closing-semantics": {"close-ticket"},
    "ticket-close": {"close-ticket"},
    "user-notification": {"contact-users"},
    "production-read": {"production-read"},
    "customer-read": {"customer-read"},
    "destructive": {"destructive-financial"},
    "paid": {"paid-action"},
    "cleanup": {"cleanup"},
    "reviewer-request": {"external-writes"},
    "label-change": {"external-writes"},
    "ticket-reassign": {"external-writes"},
}
ACTION_TRIGGER_REQUIREMENTS.update(
    {
        "auto-merge": {"external-writes", "auto-merge"},
        "rollback": {"external-writes", "rollback"},
        "production-read": {"production-access", "production-read"},
        "customer-read": {"customer-data", "customer-read"},
        "cleanup": {"external-writes", "cleanup"},
        "paid-action": {"external-writes", "paid-action"},
    }
)
COMPLETION_ACTIONS = {
    "merge": {"merge"},
    "deploy": {"deploy"},
    "release": {"release"},
    "close-ticket": {"close-ticket"},
    "contact-users": {"contact-user"},
    "branch-rewrite": {"branch-rewrite"},
    "destructive-financial": {"destructive-financial-action"},
    "auto-merge": {"auto-merge"},
    "rollback": {"rollback"},
    "production-read": {"production-read"},
    "customer-read": {"customer-read"},
    "cleanup": {"cleanup"},
    "paid-action": {"paid-action"},
}
ENDPOINT_TRIGGER = {
    "merge-ready-pr": "external-writes",
    "merge": "merge",
    "deploy": "deploy",
    "release": "release",
    "close-ticket": "close-ticket",
}


class TicketCtlError(RuntimeError):
    """A safe, user-actionable control-record error."""


class Fingerprint(TypedDict):
    algorithm: Literal["sha256"]
    digest: str
    dirty: bool
    head_digest: str
    intent_digest: str
    index_digest: str
    worktree_digest: str
    untracked_digest: str


class GateResult(TypedDict):
    gate: str
    passed: bool
    reasons: list[str]
    reason_digests: list[str]


class Evaluation(TypedDict):
    current_gate: str | None
    ready_to_finish: bool
    gates: list[GateResult]


class AuthorityEnvelope(TypedDict):
    schema_version: int
    trusted_turn_digest: str
    ticket_digest: str
    repository_digest: str
    parent_digest: str | None
    requested_endpoint: str
    allowed_scopes: list[str]
    allowed_action_kinds: list[str]
    allowed_effects: list[str]
    allowed_target_digests: list[str]
    denials: list[str]
    max_actions: int
    expires_at: str | None
    delegable: bool


class ActionManifest(TypedDict):
    schema_version: int
    kind: str
    work_unit: str | None
    target_kind: str
    target_digest: str
    revision_digest: str
    payload_digest: str
    effects: list[str]
    predecessor_action: str | None


def validate_authority_envelope(
    value: object, *, historical: bool = False
) -> AuthorityEnvelope:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "trusted_turn_digest",
        "ticket_digest",
        "repository_digest",
        "parent_digest",
        "requested_endpoint",
        "allowed_scopes",
        "allowed_action_kinds",
        "allowed_effects",
        "allowed_target_digests",
        "denials",
        "max_actions",
        "expires_at",
        "delegable",
    }:
        raise TicketCtlError("authority envelope must contain exactly the canonical fields")
    valid_endpoints = REQUESTED_ENDPOINTS | (LEGACY_REQUESTED_ENDPOINTS if historical else set())
    if value["schema_version"] != 1 or value["requested_endpoint"] not in valid_endpoints:
        raise TicketCtlError("authority envelope schema or requested endpoint is invalid")
    for field in ("trusted_turn_digest", "ticket_digest", "repository_digest"):
        require_digest(value[field], field.replace("_", " "))
    if value["parent_digest"] is not None:
        require_digest(value["parent_digest"], "parent")
    if not isinstance(value["allowed_scopes"], list) or not all(isinstance(item, str) for item in value["allowed_scopes"]):
        raise TicketCtlError("authority envelope allowed_scopes must be a string list")
    known_scopes = set(load_template()["policy"]["authority_scopes"])
    if set(value["allowed_scopes"]) - known_scopes:
        raise TicketCtlError("authority envelope contains an unknown allowed scope")
    if not isinstance(value["allowed_action_kinds"], list) or not all(
        item in ACTION_KINDS for item in value["allowed_action_kinds"]
    ):
        raise TicketCtlError("authority envelope contains an invalid action kind")
    if not isinstance(value["allowed_effects"], list) or not all(
        item in ACTION_EFFECTS for item in value["allowed_effects"]
    ):
        raise TicketCtlError("authority envelope contains an invalid external effect")
    if not isinstance(value["allowed_target_digests"], list):
        raise TicketCtlError("authority envelope target digests must be a list")
    for digest in value["allowed_target_digests"]:
        require_digest(digest, "authority target")
    if not isinstance(value["denials"], list) or not all(isinstance(item, str) for item in value["denials"]):
        raise TicketCtlError("authority envelope denials must be a string list")
    if set(value["denials"]) - known_scopes or set(value["denials"]) & set(value["allowed_scopes"]):
        raise TicketCtlError("authority envelope denials are unknown or conflict with allowed scopes")
    if not isinstance(value["max_actions"], int) or value["max_actions"] < 0:
        raise TicketCtlError("authority envelope max_actions must be a non-negative integer")
    if (
        not historical
        and value["expires_at"] is not None
        and parse_time(value["expires_at"]) <= datetime.now(timezone.utc)
    ):
        raise TicketCtlError("authority envelope is expired")
    if not isinstance(value["delegable"], bool):
        raise TicketCtlError("authority envelope delegable must be boolean")
    return cast(AuthorityEnvelope, value)


def load_authority_envelope(path: str) -> tuple[AuthorityEnvelope, str]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise TicketCtlError(f"cannot read authority envelope: {error}") from error
    envelope = validate_authority_envelope(value)
    return envelope, sha256_bytes(canonical_json(envelope))


def validate_action_manifest(value: object) -> ActionManifest:
    fields = {
        "schema_version",
        "kind",
        "work_unit",
        "target_kind",
        "target_digest",
        "revision_digest",
        "payload_digest",
        "effects",
        "predecessor_action",
    }
    if not isinstance(value, dict) or set(value) != fields or value.get("schema_version") != 1:
        raise TicketCtlError("action request manifest must contain exactly the canonical schema-v1 fields")
    if value.get("kind") not in ACTION_KINDS:
        raise TicketCtlError("action request manifest has an unknown action kind")
    target_kind = value.get("target_kind")
    if target_kind not in ACTION_KIND_TARGETS[value["kind"]]:
        raise TicketCtlError("action request target kind is incompatible with its action kind")
    if target_kind in {"remote", "pr"}:
        require_id(str(value.get("work_unit", "")), "work unit")
    elif value.get("work_unit") is not None:
        require_id(str(value["work_unit"]), "work unit")
    if value["predecessor_action"] is not None:
        require_id(str(value["predecessor_action"]), "predecessor action")
    for field in ("target_digest", "revision_digest", "payload_digest"):
        require_digest(str(value.get(field, "")), field.replace("_", " "))
    effects = value.get("effects")
    if not isinstance(effects, list) or len(effects) != len(set(effects)) or not all(
        effect in ACTION_EFFECTS for effect in effects
    ):
        raise TicketCtlError("action request manifest effects must be a unique known-effect list")
    if set(effects) != CANONICAL_KIND_EFFECTS[value["kind"]]:
        raise TicketCtlError("action kind requires its exact canonical effect classification")
    normalized = cast(ActionManifest, dict(value))
    normalized["effects"] = sorted(effects)
    return normalized


def load_action_manifest(path: str) -> tuple[ActionManifest, str]:
    try:
        value = json.loads(Path(path).read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise TicketCtlError(f"cannot read action request manifest: {error}") from error
    normalized = validate_action_manifest(value)
    return normalized, sha256_bytes(canonical_json(normalized))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise TicketCtlError("record contains an invalid timestamp") from error


def expiry_time(ttl_seconds: int) -> str:
    if ttl_seconds < 30 or ttl_seconds > 86_400:
        raise TicketCtlError("lease TTL must be between 30 and 86400 seconds")
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def derive_pr_slot_digest(
    *,
    provider: str,
    target_repo: str,
    target_ref: str,
    head_repo: str,
    head_ref: str,
    work_unit: str,
) -> str:
    fields = {
        "domain": PR_SLOT_DOMAIN,
        "schema_version": 1,
        "provider": safe_text(provider, "provider", 100),
        "target_repo": safe_text(target_repo, "target repository", 200),
        "target_ref": safe_text(target_ref, "target ref", 200),
        "head_repo": safe_text(head_repo, "head repository", 200),
        "head_ref": safe_text(head_ref, "head ref", 200),
        "work_unit": require_id(work_unit, "work unit"),
    }
    return sha256_bytes(canonical_json(fields))


def derive_remote_ref_digest(
    *, provider: str, repository: str, ref: str, work_unit: str
) -> str:
    fields = {
        "domain": REMOTE_REF_DOMAIN,
        "schema_version": 1,
        "provider": safe_text(provider, "provider", 100),
        "repository": safe_text(repository, "repository", 200),
        "ref": safe_text(ref, "ref", 200),
        "work_unit": require_id(work_unit, "work unit"),
    }
    return sha256_bytes(canonical_json(fields))


def require_digest(value: str, field: str) -> str:
    normalized = value.lower()
    if not DIGEST_PATTERN.fullmatch(normalized):
        raise TicketCtlError(f"{field} must be a 64-character SHA-256 digest")
    return normalized


def require_id(value: str, field: str = "id") -> str:
    if not ID_PATTERN.fullmatch(value):
        raise TicketCtlError(f"{field} must match {ID_PATTERN.pattern}")
    return value


def safe_text(value: str, field: str, maximum: int = 500) -> str:
    if value != value.strip() or not value or len(value) > maximum:
        raise TicketCtlError(f"{field} must be non-empty, trimmed, and at most {maximum} characters")
    if any(character in value for character in "\r\n\x00"):
        raise TicketCtlError(f"{field} must be one line")
    if any(pattern.search(value) for pattern in UNSAFE_TEXT_PATTERNS):
        raise TicketCtlError(f"{field} appears to contain a URL, identity, path, or credential; store only a sanitized summary")
    return value


def content_digest(*, digest: str | None, file: str | None, field: str) -> str:
    if bool(digest) == bool(file):
        raise TicketCtlError(f"provide exactly one of --{field}-digest or --{field}-file")
    if digest:
        return require_digest(digest, field)
    hasher = hashlib.sha256()
    with Path(cast(str, file)).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_git(repo: Path, *arguments: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", os.fspath(repo), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        message = result.stderr.decode(errors="replace").strip()
        raise TicketCtlError(message or "git command failed")
    return result.stdout


def git_common_dir(repo: Path) -> Path:
    raw = run_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(os.fsdecode(raw).strip()).resolve()


def git_fingerprint(repo: Path) -> Fingerprint:
    hasher = hashlib.sha256()

    def include(label: bytes, value: bytes) -> None:
        hasher.update(label)
        hasher.update(len(value).to_bytes(8, "big"))
        hasher.update(value)

    head_result = subprocess.run(
        ["git", "-C", os.fspath(repo), "rev-parse", "--verify", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if head_result.returncode not in (0, 128):
        raise TicketCtlError(head_result.stderr.decode(errors="replace").strip() or "could not fingerprint HEAD")
    head_digest = sha256_bytes(head_result.stdout.strip() if head_result.returncode == 0 else b"unborn")
    paths = run_git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")
    paths = sorted(set(item for item in paths if item))
    for encoded_name in paths:
        path = repo / os.fsdecode(encoded_name)
        if not path.is_symlink() and not path.is_file():
            continue
        include(b"path", encoded_name)
        if path.is_symlink():
            include(b"symlink", os.fsencode(os.readlink(path)))
        elif path.is_file():
            file_hasher = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    file_hasher.update(chunk)
            include(b"content", file_hasher.digest())
            include(b"executable", b"1" if os.access(path, os.X_OK) else b"0")
    dirty = bool(run_git(repo, "status", "--porcelain=v1", "-z"))
    index_digest = sha256_bytes(run_git(repo, "ls-files", "--stage", "-z"))
    worktree_digest = sha256_bytes(run_git(repo, "diff", "--binary", "--no-ext-diff"))
    untracked_digest = sha256_bytes(run_git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    intent_digest = sha256_bytes(canonical_json([index_digest, worktree_digest, untracked_digest]))
    return {
        "algorithm": "sha256",
        "digest": hasher.hexdigest(),
        "dirty": dirty,
        "head_digest": head_digest,
        "intent_digest": intent_digest,
        "index_digest": index_digest,
        "worktree_digest": worktree_digest,
        "untracked_digest": untracked_digest,
    }


def template_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "control-record-template.json"


def load_template() -> dict[str, Any]:
    try:
        value = json.loads(template_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TicketCtlError(f"cannot load control-record template: {error}") from error
    if value.get("schema_version") != SCHEMA_VERSION:
        raise TicketCtlError("control-record template schema is incompatible")
    return cast(dict[str, Any], value)


def default_record_path(repo: Path, ticket: str) -> Path:
    ticket_digest = sha256_bytes(ticket.encode())
    return git_common_dir(repo) / "ticketctl" / f"v{SCHEMA_VERSION}" / ticket_digest[:24] / "record.json"


def safe_artifact_locator(locator: str) -> bool:
    path = Path(locator)
    return bool(
        "\\" not in locator
        and not path.is_absolute()
        and len(path.parts) >= 2
        and path.parts[0] == "artifacts"
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def artifact_path(record_path: Path, locator: str) -> Path:
    if not safe_artifact_locator(locator):
        raise TicketCtlError("artifact locator must be a safe relative path under artifacts/")
    candidate = record_path.parent / locator
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise TicketCtlError(f"artifact sidecar {locator} cannot be read: {error}") from error
    raw_artifacts_root = record_path.parent / "artifacts"
    if raw_artifacts_root.is_symlink():
        raise TicketCtlError("run artifacts directory cannot be a symbolic link")
    artifacts_root = raw_artifacts_root.resolve()
    if not resolved.is_relative_to(artifacts_root) or not resolved.is_file():
        raise TicketCtlError(f"artifact sidecar {locator} is not a regular file under the run artifacts directory")
    return resolved


def artifact_error(record: dict[str, Any], record_path: Path, artifact_id: str) -> str | None:
    artifact = record["artifacts"].get(artifact_id)
    if artifact is None:
        return f"artifact {artifact_id} is missing"
    try:
        path = artifact_path(record_path, str(artifact.get("locator", "")))
        actual_digest = file_digest(path)
    except (OSError, TicketCtlError) as error:
        return str(error)
    if actual_digest != artifact.get("content_digest"):
        return f"artifact {artifact_id} content digest does not match its registered sidecar"
    return None


def repository_digest(repo: Path) -> str:
    return sha256_bytes(os.fsencode(git_common_dir(repo)))


def resolve_record(args: argparse.Namespace, *, initializing: bool = False) -> Path:
    repo = Path(args.repo).resolve()
    if args.record:
        return Path(args.record).resolve()
    if not args.ticket:
        operation = "init" if initializing else "this command"
        raise TicketCtlError(f"{operation} requires --ticket when --record is omitted")
    return default_record_path(repo, args.ticket)


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(json.dumps(value, indent=2, sort_keys=True).encode())
            destination.write(b"\n")
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def exclusive_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        payload = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
        write_all(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(temporary, path)
        fsync_directory(path.parent)
    except FileExistsError as error:
        raise TicketCtlError(f"refusing to overwrite existing output file: {path}") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def fsync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def event_hash(event: dict[str, Any]) -> str:
    normalized = copy.deepcopy(event)
    normalized.pop("event_hash", None)
    if isinstance(normalized.get("state"), dict):
        normalized["state"]["run"]["journal_head"] = None
    return sha256_bytes(canonical_json(normalized))


def write_all(descriptor: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        try:
            written = os.write(descriptor, data[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise OSError("journal append made no progress")
        offset += written


def validate_record(record: dict[str, Any]) -> None:
    if record.get("schema_version") != SCHEMA_VERSION:
        raise TicketCtlError("unsupported or missing record schema version")
    run = record.get("run")
    if not isinstance(run, dict) or not isinstance(run.get("revision"), int):
        raise TicketCtlError("record run metadata is malformed")
    require_digest(str(run.get("ticket_digest", "")), "ticket digest")
    lease = record.get("lease")
    if not isinstance(lease, dict) or not isinstance(lease.get("epoch"), int) or lease["epoch"] < 0:
        raise TicketCtlError("record lease metadata is malformed")
    for collection in ("contexts", "capabilities", "triggers", "claims", "obligations", "evidence", "artifacts", "findings", "work_units", "actions", "effects", "checkpoints"):
        if not isinstance(record.get(collection), dict):
            raise TicketCtlError(f"record {collection} collection is malformed")
    if not isinstance(record.get("invalidations"), list):
        raise TicketCtlError("record invalidations collection is malformed")
    for trigger in record["triggers"].values():
        if trigger.get("decision") not in DECISIONS:
            raise TicketCtlError("record contains an invalid trigger decision")
        if trigger.get("category") not in {"applicability", "reserved-authority"}:
            raise TicketCtlError("record contains an invalid trigger category")
    authority_contexts = [
        context for context in record["contexts"].values() if context.get("kind") == "trusted-instruction"
    ]
    if not authority_contexts:
        raise TicketCtlError("record has no trusted authority envelope")
    for context in authority_contexts:
        validate_authority_envelope(context.get("envelope"), historical=True)
    for obligation in record["obligations"].values():
        if obligation.get("gate") not in GATES:
            raise TicketCtlError("record contains an invalid obligation gate")
    for action in record["actions"].values():
        if action.get("status") not in ACTION_STATES:
            raise TicketCtlError("record contains an unknown external-action state")
        if (
            action.get("kind") not in ACTION_KINDS
            or action.get("target_kind") not in ACTION_TARGET_KINDS
            or not isinstance(action.get("effects"), list)
        ):
            raise TicketCtlError("record contains a malformed external action")
        for field in (
            "target_digest",
            "request_digest",
            "expected_state_digest",
            "idempotency_digest",
            "revision_digest",
        ):
            require_digest(str(action.get(field, "")), f"action {field}")
    for artifact_id, artifact in record["artifacts"].items():
        require_id(str(artifact_id), "artifact")
        locator = artifact.get("locator")
        dependencies = artifact.get("dependencies")
        if (
            not isinstance(locator, str)
            or not safe_artifact_locator(locator)
            or not isinstance(dependencies, list)
            or set(dependencies) - record["artifacts"].keys()
        ):
            raise TicketCtlError("record contains a malformed artifact registry entry")
        require_digest(str(artifact.get("content_digest", "")), "artifact content")
    allowed_dispositions = {None, "fixed", "refuted", "duplicate", "accepted-residual", "follow-up"}
    for finding in record["findings"].values():
        if finding.get("disposition") not in allowed_dispositions:
            raise TicketCtlError("record contains an unknown finding disposition")
        if finding.get("origin") not in {"introduced", "pre-existing", "unknown"}:
            raise TicketCtlError("record contains an unknown finding origin")
    seen_review_artifacts: set[str] = set()
    for evidence in record["evidence"].values():
        if evidence.get("kind") not in EVIDENCE_KINDS:
            raise TicketCtlError("record contains an unknown evidence kind")
        if evidence.get("result") not in {"pass", "fail", "gap"}:
            raise TicketCtlError("record contains an unknown evidence result")
        if evidence.get("kind") == "blocker":
            reason_digests = evidence.get("reason_digests")
            if not isinstance(reason_digests, list) or not reason_digests:
                raise TicketCtlError("record contains blocker evidence without mapped gate reasons")
            for reason_digest in reason_digests:
                require_digest(str(reason_digest), "blocker reason")
        if evidence.get("kind") == "review":
            review_lenses = evidence.get("review_lenses")
            if review_lenses is None and evidence.get("review_lens") in REVIEW_LENSES:
                review_lenses = [evidence["review_lens"]]
            if (
                not isinstance(review_lenses, list)
                or not review_lenses
                or not set(review_lenses).issubset(REVIEW_LENSES)
                or not DIGEST_PATTERN.fullmatch(str(evidence.get("reviewer_digest", "")))
                or not DIGEST_PATTERN.fullmatch(str(evidence.get("review_input_digest", "")))
            ):
                raise TicketCtlError("record contains review evidence without valid lens coverage and provenance")
            artifact_digest = str(evidence.get("artifact_digest", ""))
            if artifact_digest in seen_review_artifacts:
                raise TicketCtlError("record reuses one review artifact across multiple review evidence rows")
            seen_review_artifacts.add(artifact_digest)


class RecordStore:
    def __init__(
        self,
        path: Path,
        *,
        expected_ticket_digest: str | None = None,
        expected_repository_digest: str | None = None,
    ) -> None:
        self.path = path
        self.journal_path = path.with_name("journal.jsonl")
        self.lock_path = path.with_name("record.lock")
        self.expected_ticket_digest = expected_ticket_digest
        self.expected_repository_digest = expected_repository_digest

    @contextmanager
    def lock(self) -> Iterator[None]:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as lock_file:
            os.chmod(self.lock_path, 0o600)
            if os.name == "nt":
                import msvcrt

                lock_file.seek(0)
                lock_file.write(b"0")
                lock_file.flush()
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _last_journal_event(self) -> dict[str, Any] | None:
        if not self.journal_path.exists():
            return None
        previous_hash: str | None = None
        previous_sequence = 0
        last: dict[str, Any] | None = None
        raw_lines = self.journal_path.read_bytes().splitlines(keepends=True)
        valid_length = 0
        torn_tail = False
        unterminated_valid_tail = False
        with self.journal_path.open("rb") as source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    valid_length += len(line)
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    if line_number == len(raw_lines) and not line.endswith(b"\n") and last is not None:
                        torn_tail = True
                        break
                    raise TicketCtlError(f"journal line {line_number} is corrupt") from error
                if event.get("sequence") != previous_sequence + 1 or event.get("previous_hash") != previous_hash:
                    raise TicketCtlError(f"journal chain breaks at line {line_number}")
                if event.get("event_hash") != event_hash(event):
                    raise TicketCtlError(f"journal hash fails at line {line_number}")
                state = event.get("state")
                if not isinstance(state, dict) or state.get("run", {}).get("revision") != event["sequence"]:
                    raise TicketCtlError(f"journal snapshot is malformed at line {line_number}")
                previous_sequence = event["sequence"]
                previous_hash = event["event_hash"]
                last = cast(dict[str, Any], event)
                valid_length += len(line)
                if line_number == len(raw_lines) and not line.endswith(b"\n"):
                    unterminated_valid_tail = True
        if torn_tail:
            descriptor = os.open(self.journal_path, os.O_WRONLY)
            try:
                os.ftruncate(descriptor, valid_length)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        elif unterminated_valid_tail:
            descriptor = os.open(self.journal_path, os.O_WRONLY | os.O_APPEND)
            try:
                os.write(descriptor, b"\n")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return last

    def load(self) -> dict[str, Any]:
        event = self._last_journal_event()
        record: dict[str, Any] | None = None
        if self.path.exists():
            try:
                record = cast(dict[str, Any], json.loads(self.path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as error:
                if event is None:
                    raise TicketCtlError(f"record cannot be read: {error}") from error
        if event is None and record is None:
            raise TicketCtlError("control record does not exist; run init first")
        if event is None and record is not None:
            raise TicketCtlError("control record has no valid append-only journal; recover or reinitialize it")
        if event is not None:
            journal_record = cast(dict[str, Any], event["state"])
            journal_record["run"]["journal_head"] = event["event_hash"]
            if record is None or canonical_json(record) != canonical_json(journal_record):
                atomic_write_json(self.path, journal_record)
                record = journal_record
        assert record is not None
        validate_record(record)
        for artifact_id in record["artifacts"]:
            if error := artifact_error(record, self.path, artifact_id):
                raise TicketCtlError(error)
        if self.expected_ticket_digest is not None:
            if record["run"].get("ticket_digest") != self.expected_ticket_digest:
                raise TicketCtlError("control record is bound to a different ticket")
            if any(
                context["envelope"].get("ticket_digest") != self.expected_ticket_digest
                for context in record["contexts"].values()
                if context.get("kind") == "trusted-instruction"
            ):
                raise TicketCtlError("authority history is bound to a different ticket")
        if self.expected_repository_digest is not None and any(
            context["envelope"].get("repository_digest") != self.expected_repository_digest
            for context in record["contexts"].values()
            if context.get("kind") == "trusted-instruction"
        ):
            raise TicketCtlError("control record is bound to a different Git common directory")
        return record

    def commit(
        self,
        record: dict[str, Any],
        event_name: str,
        details: dict[str, Any],
        *,
        lease_token: str | None = None,
        lease_epoch: int | None = None,
        bypass_lease: bool = False,
    ) -> None:
        if not bypass_lease:
            require_active_lease(record, lease_token, lease_epoch)
        previous_hash = record["run"].get("journal_head")
        record["run"]["revision"] += 1
        record["run"]["updated_at"] = utc_now()
        snapshot = copy.deepcopy(record)
        event = {
            "sequence": record["run"]["revision"],
            "at": record["run"]["updated_at"],
            "event": event_name,
            "details": details,
            "previous_hash": previous_hash,
            "state": snapshot,
        }
        digest = event_hash(event)
        event["event_hash"] = digest
        event["state"]["run"]["journal_head"] = digest
        record["run"]["journal_head"] = digest
        self.journal_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(self.journal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            write_all(descriptor, canonical_json(event) + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        fsync_directory(self.journal_path.parent)
        atomic_write_json(self.path, record)


def bound_record_store(args: argparse.Namespace) -> RecordStore:
    if not args.ticket:
        raise TicketCtlError("record access requires --ticket, including with --record")
    repo = Path(args.repo).resolve()
    return RecordStore(
        resolve_record(args),
        expected_ticket_digest=sha256_bytes(args.ticket.encode()),
        expected_repository_digest=repository_digest(repo),
    )


def lease_is_active(lease: dict[str, Any]) -> bool:
    return bool(
        lease.get("token_digest")
        and lease.get("released_at") is None
        and lease.get("expires_at")
        and parse_time(lease["expires_at"]) > datetime.now(timezone.utc)
    )


def require_active_lease(record: dict[str, Any], token: str | None, epoch: int | None) -> None:
    lease = record["lease"]
    if not token or epoch is None:
        raise TicketCtlError("mutation requires --lease-token or --lease-token-file and --lease-epoch")
    if not lease_is_active(lease):
        raise TicketCtlError("coordinator lease is absent or expired; acquire or take it over after reconciliation")
    if epoch != lease["epoch"]:
        raise TicketCtlError("coordinator lease epoch is stale")
    supplied = sha256_bytes(token.encode())
    if not secrets.compare_digest(supplied, str(lease["token_digest"])):
        raise TicketCtlError("coordinator lease token is invalid")


def lease_token_from_args(args: argparse.Namespace) -> str | None:
    token = getattr(args, "lease_token", None)
    token_file = getattr(args, "lease_token_file", None)
    if token and token_file:
        raise TicketCtlError("provide only one of --lease-token or --lease-token-file")
    if token_file:
        try:
            token = Path(token_file).read_text(encoding="utf-8").strip()
        except OSError as error:
            raise TicketCtlError(f"cannot read lease token file: {error}") from error
    if token is not None and (not token or len(token) > 1024 or any(character.isspace() for character in token)):
        raise TicketCtlError("lease token must be a non-empty, whitespace-free value")
    return token


def commit_mutation(
    store: RecordStore,
    record: dict[str, Any],
    args: argparse.Namespace,
    event_name: str,
    details: dict[str, Any],
) -> None:
    store.commit(
        record,
        event_name,
        details,
        lease_token=lease_token_from_args(args),
        lease_epoch=args.lease_epoch,
    )


def capability_is_current(record: dict[str, Any], capability: dict[str, Any] | None) -> bool:
    if not capability:
        return False
    authority = current_authority_context(record)
    envelope = authority.get("envelope", {})
    return bool(
        capability.get("available") == "yes"
        and capability.get("authority") == "granted"
        and capability.get("basis") == authority.get("id")
        and capability.get("authority_revision") == record["run"].get("authority_revision")
        and (not capability.get("expires_at") or parse_time(capability["expires_at"]) > datetime.now(timezone.utc))
        and (not envelope.get("expires_at") or parse_time(envelope["expires_at"]) > datetime.now(timezone.utc))
    )


def capability_grants(record: dict[str, Any], capability_id: str, scope: str) -> bool:
    capability = record["capabilities"].get(capability_id)
    return bool(
        capability_is_current(record, capability)
        and scope in capability.get("covers", [])
    )


def control_target_digest(kind: str, item_id: str) -> str:
    return sha256_bytes(canonical_json({"kind": kind, "id": item_id}))


def capability_grants_target(
    record: dict[str, Any], capability_id: str, scope: str, target_digest: str
) -> bool:
    capability = record["capabilities"].get(capability_id)
    return bool(
        capability_grants(record, capability_id, scope)
        and target_digest in capability.get("target_digests", [])
    )


def current_authority_context(record: dict[str, Any]) -> dict[str, Any]:
    return max(
        (
            context
            for context in record["contexts"].values()
            if context.get("kind") == "trusted-instruction"
        ),
        key=lambda context: context.get("authority_revision", 0),
    )


def action_capability_error(
    record: dict[str, Any], action: dict[str, Any], *, allow_prior_lease: bool = False
) -> str | None:
    capability = record["capabilities"].get(action.get("capability"))
    if not capability_is_current(record, capability):
        return "action capability is unavailable, expired, revoked, or from a stale authority revision"
    assert capability is not None
    authority = current_authority_context(record)
    envelope = authority["envelope"]
    if capability.get("basis") != authority.get("id"):
        return "action capability does not cite the current canonical authority envelope"
    if envelope.get("expires_at") and parse_time(envelope["expires_at"]) <= datetime.now(timezone.utc):
        return "current authority envelope is expired"
    if action.get("authority_revision") != record["run"].get("authority_revision"):
        return "action was prepared under a stale authority revision"
    if not allow_prior_lease and action.get("lease_epoch") != record["lease"].get("epoch"):
        return "action was prepared under a stale coordinator lease epoch"
    if action.get("kind") not in capability.get("action_kinds", []):
        return "action kind is no longer allowed by its capability"
    if action.get("target_digest") not in capability.get("target_digests", []):
        return "action target is no longer allowed by its capability"
    if set(action.get("effects", [])) - set(capability.get("effects", [])):
        return "action effects are no longer allowed by its capability"
    if capability.get("uses", 0) > capability.get("max_uses", 0):
        return "action capability cardinality was narrowed below its consumed uses"
    if record["run"].get("authority_action_uses", 0) > envelope.get("max_actions", 0):
        return "authority cardinality was narrowed below its consumed actions"
    if action.get("kind") not in envelope.get("allowed_action_kinds", []):
        return "action kind is no longer allowed by the authority envelope"
    if action.get("target_digest") not in envelope.get("allowed_target_digests", []):
        return "action target is no longer allowed by the authority envelope"
    if set(action.get("effects", [])) - set(envelope.get("allowed_effects", [])):
        return "action effects are no longer allowed by the authority envelope"
    required = required_action_triggers(str(action.get("kind"))) | {
        trigger
        for effect in action.get("effects", [])
        for trigger in EFFECT_TRIGGER_REQUIREMENTS.get(effect, set())
    }
    if any(record["triggers"].get(trigger, {}).get("decision") != "yes" for trigger in required):
        return "an action trigger is no longer affirmatively applicable"
    if not required.issubset(set(capability.get("covers", []))):
        return "action capability no longer covers every required authority trigger"
    return None


def action_coherence_error(record: dict[str, Any], action: dict[str, Any]) -> str | None:
    checkpoint_id = action.get("checkpoint")
    if checkpoint_id != record["run"].get("current_checkpoint"):
        return "checkpoint is no longer current"
    checkpoint = record["checkpoints"].get(checkpoint_id, {})
    dimensions = checkpoint.get("dimensions", {})
    kind = action.get("kind")
    target_kind = action.get("target_kind")
    if kind not in ACTION_KIND_TARGETS or target_kind not in ACTION_KIND_TARGETS[kind]:
        return "target kind does not match its action kind"
    unit_id = action.get("work_unit")
    unit = record["work_units"].get(unit_id) if unit_id is not None else None
    if target_kind in {"remote", "pr"} and unit is None:
        return f"{target_kind} target requires a work unit"
    if unit_id is not None and unit is None:
        return "work unit does not exist"
    expected_revision = (
        unit.get("coordinates", {}).get("head") if unit is not None else dimensions.get("head")
    )
    if action.get("revision_digest") != expected_revision:
        return "revision does not match its independent work-unit or checkpoint provenance"
    expected_target = {
        "remote": unit.get("coordinates", {}).get("remote") if unit is not None else None,
        "pr": unit.get("coordinates", {}).get("pr") if unit is not None else None,
        "tracker": record["run"].get("ticket_digest"),
        "environment": dimensions.get("environment"),
        "artifact": dimensions.get("build"),
        "external": action.get("target_digest"),
    }.get(str(target_kind))
    if action.get("target_digest") != expected_target:
        return f"target does not match its canonical {target_kind} coordinate"
    return None


def action_has_equivalent_effect(
    record: dict[str, Any], action_id: str, action: dict[str, Any]
) -> bool:
    return any(
        effect.get("action") == action_id
        and effect.get("kind") == action.get("kind")
        and effect.get("target_kind") == action.get("target_kind")
        and effect.get("target_digest") == action.get("target_digest")
        and effect.get("work_unit") == action.get("work_unit")
        and effect.get("revision_digest") == action.get("revision_digest")
        and effect.get("checkpoint") == record["run"].get("current_checkpoint")
        for effect in record["effects"].values()
    )


def action_is_current_applied(
    record: dict[str, Any], action_id: str, action: dict[str, Any]
) -> bool:
    return bool(
        action_coherence_error(record, action) is None
        and action_capability_error(record, action, allow_prior_lease=True) is None
        and (
            action.get("status") == "verified-applied"
            or action_has_equivalent_effect(record, action_id, action)
        )
    )


def fresh_evidence_reason(
    record: dict[str, Any], evidence_id: str, current: Fingerprint, record_path: Path | None = None
) -> str | None:
    evidence = record["evidence"].get(evidence_id)
    if evidence is None:
        return f"evidence {evidence_id} is missing"
    if evidence.get("result") != "pass":
        return f"evidence {evidence_id} result is {evidence.get('result')}"
    if evidence.get("invalidated") is not None:
        return f"evidence {evidence_id} was invalidated by {evidence['invalidated']['event']}"
    if (
        evidence.get("kind") == "terminal-audit"
        and (
            evidence.get("authority_revision") != record["run"].get("authority_revision")
            or evidence.get("requested_endpoint") != record["run"].get("requested_endpoint")
        )
    ):
        return f"evidence {evidence_id} is stale for authority revision or requested endpoint"
    if record_path is not None:
        for artifact_id in evidence.get("artifacts", []):
            if error := artifact_error(record, record_path, artifact_id):
                return f"evidence {evidence_id} cites invalid {error}"
    checkpoint = record["checkpoints"].get(evidence.get("checkpoint"))
    if checkpoint is None:
        return f"evidence {evidence_id} has no valid checkpoint"
    active_checkpoint = record["checkpoints"].get(record["run"].get("current_checkpoint"))
    if active_checkpoint is None:
        return f"evidence {evidence_id} cannot be compared without a current checkpoint"
    current_dimensions = dict(active_checkpoint.get("dimensions", {}))
    current_dimensions.update(
        {"candidate": current["digest"], "intent": current["intent_digest"], "head": current["head_digest"]}
    )
    evidence_dimensions = checkpoint.get("dimensions", {})
    for dimension in evidence.get("dependencies", []):
        if evidence_dimensions.get(dimension) != current_dimensions.get(dimension):
            return f"evidence {evidence_id} is stale for checkpoint dimension {dimension}"
    if evidence.get("kind") == "host-audit":
        unit_id = evidence.get("work_unit")
        unit = record["work_units"].get(unit_id, {})
        coordinates = unit.get("coordinates", {})
        if (
            not unit_id
            or evidence.get("revision_digest") != coordinates.get("head")
            or evidence.get("target_digest") not in {coordinates.get("remote"), coordinates.get("pr")}
        ):
            return f"evidence {evidence_id} host audit does not match its work-unit revision and target"
    return None


def any_fresh_evidence(
    record: dict[str, Any],
    evidence_ids: list[str],
    current: Fingerprint,
    gate: str | None = None,
    record_path: Path | None = None,
) -> bool:
    return any(
        fresh_evidence_reason(record, evidence_id, current, record_path) is None
        and (
            gate is None
            or record["evidence"][evidence_id].get("kind") in GATE_EVIDENCE_KINDS[gate]
            or static_oracle_satisfies(record, record["evidence"][evidence_id], gate)
        )
        for evidence_id in evidence_ids
        if evidence_id in record["evidence"]
    )


def static_oracle_satisfies(record: dict[str, Any], evidence: dict[str, Any], gate: str) -> bool:
    digests = [
        evidence.get("artifact_digest"),
        evidence.get("static_oracle_digest"),
        evidence.get("surface_digest"),
        evidence.get("oracle_actor_digest"),
    ]
    return bool(
        record["run"].get("requested_endpoint") == "static-fact"
        and gate in {"G4", "G8"}
        and evidence.get("kind") == "inspection"
        and all(DIGEST_PATTERN.fullmatch(str(digest or "")) for digest in digests)
        and len(set(digests)) == len(digests)
    )


def graph_error(work_units: dict[str, Any]) -> str | None:
    for unit_id, unit in work_units.items():
        missing = sorted(set(unit.get("depends_on", [])) - work_units.keys())
        if missing:
            return f"work unit {unit_id} has missing dependencies: {', '.join(missing)}"
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str) -> bool:
        if unit_id in visiting:
            return True
        if unit_id in visited:
            return False
        visiting.add(unit_id)
        if any(visit(dependency) for dependency in work_units[unit_id].get("depends_on", [])):
            return True
        visiting.remove(unit_id)
        visited.add(unit_id)
        return False

    if any(visit(unit_id) for unit_id in work_units):
        return "work-unit graph contains a cycle"
    return None


def dependency_closure(work_units: dict[str, Any], unit_id: str) -> set[str]:
    result: set[str] = set()
    pending = list(work_units.get(unit_id, {}).get("depends_on", []))
    while pending:
        dependency = pending.pop()
        if dependency in result or dependency not in work_units:
            continue
        result.add(dependency)
        pending.extend(work_units[dependency].get("depends_on", []))
    return result


def required_work_unit_ids(work_units: dict[str, Any]) -> set[str]:
    required = {unit_id for unit_id, unit in work_units.items() if unit.get("required")}
    return required | {
        dependency
        for unit_id in required
        for dependency in dependency_closure(work_units, unit_id)
    }


def eligible_work_units(record: dict[str, Any]) -> list[str]:
    return sorted(
        unit_id
        for unit_id, unit in record["work_units"].items()
        if unit.get("status") in {"planned", "active"}
        and all(
            record["work_units"].get(dependency, {}).get("status") == "done"
            for dependency in unit.get("depends_on", [])
        )
    )


def obligation_reasons(
    record: dict[str, Any],
    gate: str,
    current: Fingerprint,
    record_path: Path | None = None,
) -> list[str]:
    reasons: list[str] = []
    for obligation_id, obligation in record["obligations"].items():
        if obligation.get("gate") != gate or not obligation.get("required", True):
            continue
        condition = obligation.get("condition_trigger")
        if condition and record["triggers"].get(condition, {}).get("decision") != "yes":
            continue
        status = obligation.get("status")
        if status == "waived":
            capability_id = str(obligation.get("waiver_capability") or "")
            valid_waiver = capability_grants_target(
                record,
                capability_id,
                "accept-residual-risk",
                control_target_digest("obligation", obligation_id),
            )
            if (
                not obligation.get("waivable")
                or not obligation.get("rationale")
                or obligation.get("waiver_authority_revision") != record["run"].get("authority_revision")
                or not valid_waiver
            ):
                reasons.append(f"obligation {obligation_id} has an invalid waiver")
        elif status == "satisfied":
            if not any_fresh_evidence(
                record, obligation.get("evidence", []), current, gate, record_path
            ):
                reasons.append(f"obligation {obligation_id} lacks fresh passing evidence")
        else:
            reasons.append(f"obligation {obligation_id} is {status}")
    return reasons


def evaluate(record: dict[str, Any], repo: Path, record_path: Path | None = None) -> Evaluation:
    current = git_fingerprint(repo)
    gates: list[GateResult] = []
    policy = record["policy"]
    required_work_units = required_work_unit_ids(record["work_units"])

    for gate in GATES:
        reasons = obligation_reasons(record, gate, current, record_path)
        if gate == "G0":
            observed_kinds = {item.get("kind") for item in record["contexts"].values()}
            for kind in policy["required_context_kinds"]:
                if kind not in observed_kinds:
                    reasons.append(f"required context kind {kind} is missing")
            for trigger_id, trigger in record["triggers"].items():
                if trigger.get("decision") not in {"yes", "no"} or not trigger.get("rationale"):
                    reasons.append(f"trigger {trigger_id} is unknown or lacks rationale")
                elif trigger["decision"] == "yes":
                    obligation_id = trigger.get("obligation")
                    obligation = record["obligations"].get(obligation_id)
                    if not obligation or obligation.get("condition_trigger") != trigger_id:
                        reasons.append(f"trigger {trigger_id}=yes lacks its required obligation card")
            for capability_id, capability in record["capabilities"].items():
                if capability.get("required") and not capability_is_current(record, capability):
                    reasons.append(f"required capability {capability_id} is unavailable or unauthorized")
            granted_covers = {
                trigger
                for capability in record["capabilities"].values()
                if capability_is_current(record, capability)
                for trigger in capability.get("covers", [])
            }
            for trigger_id in policy["triggers_requiring_authority"]:
                if record["triggers"][trigger_id]["decision"] == "yes" and trigger_id not in granted_covers:
                    reasons.append(f"trigger {trigger_id} has no explicit granted capability")
            endpoint_trigger = ENDPOINT_TRIGGER.get(str(record["run"].get("requested_endpoint")))
            if (
                endpoint_trigger
                and record["triggers"].get(endpoint_trigger, {}).get("decision") != "yes"
            ):
                reasons.append(
                    f"requested endpoint {record['run'].get('requested_endpoint')} requires trigger {endpoint_trigger}=yes"
                )
        elif gate == "G1":
            for kind in ("acceptance", "risk"):
                if not any(
                    claim.get("kind") == kind
                    and claim.get("required")
                    and claim.get("gate") == "G1"
                    for claim in record["claims"].values()
                ):
                    reasons.append(f"at least one {kind} claim is required")
            for claim_id, claim in record["claims"].items():
                if claim.get("required") and claim.get("gate") == "G1":
                    if not any_fresh_evidence(
                        record, claim.get("evidence", []), current, "G1", record_path
                    ):
                        reasons.append(f"claim {claim_id} lacks fresh passing evidence")
        elif gate == "G2":
            if not any(unit.get("required") for unit in record["work_units"].values()):
                reasons.append("at least one required work unit is needed")
            error = graph_error(record["work_units"])
            if error:
                reasons.append(error)
            for unit_id in sorted(required_work_units):
                unit = record["work_units"][unit_id]
                if any(
                    not unit.get("coordinates", {}).get(name) for name in ("branch", "worktree", "base", "head")
                ):
                    reasons.append(f"required work unit {unit_id} lacks hashed branch/worktree/base/head coordinates")
        elif gate == "G3":
            for unit_id in sorted(required_work_units):
                unit = record["work_units"][unit_id]
                if unit.get("status") != "done":
                    reasons.append(f"required work path unit {unit_id} is {unit.get('status')}")
                elif not any_fresh_evidence(
                    record, unit.get("evidence", []), current, "G3", record_path
                ):
                    reasons.append(f"work unit {unit_id} lacks fresh passing evidence")
                epoch = record["checkpoints"].get(unit.get("evidence_epoch"))
                if (
                    epoch is None
                    or unit.get("evidence_epoch") != record["run"].get("current_checkpoint")
                    or epoch.get("dimensions", {}).get("candidate") != current["digest"]
                    or epoch.get("dimensions", {}).get("intent") != current["intent_digest"]
                ):
                    reasons.append(f"work unit {unit_id} lacks a current evidence epoch")
        elif gate == "G4":
            for claim_id, claim in record["claims"].items():
                if claim.get("required") and claim.get("gate") == "G4":
                    if not any_fresh_evidence(
                        record, claim.get("evidence", []), current, "G4", record_path
                    ):
                        reasons.append(f"claim {claim_id} lacks fresh passing evidence")
        elif gate == "G5":
            fresh_reviews = [
                evidence_id
                for evidence_id, evidence in record["evidence"].items()
                if evidence.get("kind") == "review"
                and fresh_evidence_reason(record, evidence_id, current, record_path) is None
            ]
            if not fresh_reviews:
                reasons.append("no fresh passing review evidence exists")
            covered_lenses = {
                lens
                for evidence_id in fresh_reviews
                for lens in (
                    record["evidence"][evidence_id].get("review_lenses")
                    or [record["evidence"][evidence_id].get("review_lens")]
                )
                if lens in REVIEW_LENSES
            }
            missing_lenses = REVIEW_LENSES - covered_lenses
            if missing_lenses:
                reasons.append(f"review lenses are missing: {', '.join(sorted(missing_lenses))}")
            for finding_id, finding in record["findings"].items():
                disposition = finding.get("disposition")
                if disposition is None:
                    reasons.append(f"finding {finding_id} is open")
                    continue
                if finding.get("severity") in {"blocker", "major"} and disposition == "follow-up":
                    reasons.append(f"material finding {finding_id} cannot be deferred")
                if disposition == "accepted-residual" and (
                    finding.get("waiver_authority_revision") != record["run"].get("authority_revision")
                    or not capability_grants_target(
                        record,
                        str(finding.get("waiver_capability") or ""),
                        "accept-residual-risk",
                        control_target_digest("finding", finding_id),
                    )
                ):
                    reasons.append(f"finding {finding_id} residual-risk acceptance is no longer authorized")
                if not finding.get("rationale") or not any_fresh_evidence(
                    record, finding.get("evidence", []), current, record_path=record_path
                ):
                    reasons.append(f"finding {finding_id} disposition lacks rationale or fresh evidence")
        elif gate in {"G6", "G7"}:
            external = record["triggers"]["external-writes"]["decision"]
            if external == "no" and record["actions"]:
                reasons.append("external actions exist although external-writes trigger is no")
            if external == "yes" and not record["actions"]:
                reasons.append("external-writes trigger is yes but no write-ahead action exists")
            for action_id, action in record["actions"].items():
                current_action = action.get("checkpoint") == record["run"].get("current_checkpoint")
                if action.get("status") not in TERMINAL_ACTION_STATES:
                    reasons.append(f"external action {action_id} is {action.get('status')}")
                if current_action or action.get("status") not in TERMINAL_ACTION_STATES:
                    coherence_error = action_coherence_error(record, action)
                    if coherence_error:
                        reasons.append(f"external action {action_id} {coherence_error}")
                if (
                    current_action
                    and action.get("status") == "verified-not-applied"
                    and not action_has_equivalent_effect(record, action_id, action)
                ):
                    reasons.append(
                        f"external action {action_id} was not applied and has no current equivalent observed effect"
                    )
            if gate == "G6" and external == "yes":
                for unit_id in sorted(required_work_units):
                    unit = record["work_units"][unit_id]
                    if any(
                        not unit.get("coordinates", {}).get(name) for name in ("remote", "pr")
                    ):
                        reasons.append(f"delivered work unit {unit_id} lacks hashed remote/PR coordinates")
            if gate == "G7" and external == "yes":
                fresh_host_audits = {
                    evidence.get("work_unit")
                    for evidence_id, evidence in record["evidence"].items()
                    if evidence.get("kind") == "host-audit"
                    and fresh_evidence_reason(record, evidence_id, current, record_path) is None
                }
                missing_audits = sorted(required_work_units - fresh_host_audits)
                if missing_audits:
                    reasons.append(
                        f"external delivery lacks fresh structured host audits for: {', '.join(missing_audits)}"
                    )
                for evidence_id, evidence in record["evidence"].items():
                    if evidence.get("kind") != "host-audit" or fresh_evidence_reason(
                        record, evidence_id, current, record_path
                    ):
                        continue
                    audit = evidence.get("host_audit") or {}
                    expected = {
                        "lanes": "complete",
                        "feedback": "none",
                        "automated_review": "complete",
                        "draft": "no",
                        "mergeable": "yes",
                    }
                    for key, value in expected.items():
                        if audit.get(key) != value:
                            reasons.append(f"host audit {evidence_id} has {key}={audit.get(key)}")
        elif gate == "G8":
            terminal_claims = [
                (claim_id, claim)
                for claim_id, claim in record["claims"].items()
                if claim.get("kind") == "terminal" and claim.get("terminal_outcome") in SUCCESS_TERMINALS
            ]
            if not terminal_claims:
                reasons.append("no positive terminal claim is recorded")
            elif not any(
                claim.get("authority_revision") == record["run"].get("authority_revision")
                and claim.get("requested_endpoint") == record["run"].get("requested_endpoint")
                and any_fresh_evidence(
                    record, claim.get("evidence", []), current, "G8", record_path
                )
                for _, claim in terminal_claims
            ):
                reasons.append("positive terminal claims lack fresh passing evidence")
        gates.append(
            {
                "gate": gate,
                "passed": not reasons,
                "reasons": reasons,
                "reason_digests": [sha256_bytes(reason.encode()) for reason in reasons],
            }
        )

    current_gate = next((result["gate"] for result in gates if not result["passed"]), None)
    return {"current_gate": current_gate, "ready_to_finish": current_gate is None, "gates": gates}


def ensure_open(record: dict[str, Any]) -> None:
    if record.get("terminal") is not None:
        raise TicketCtlError("record is terminal; run reopen before changing it")


def output(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def cmd_init(args: argparse.Namespace) -> None:
    if not args.ticket:
        raise TicketCtlError("init requires --ticket; the raw locator is hashed and never stored")
    envelope, authority_digest = load_authority_envelope(args.authority_envelope)
    expected_ticket_digest = sha256_bytes(args.ticket.encode())
    expected_repository_digest = repository_digest(Path(args.repo).resolve())
    if envelope["ticket_digest"] != expected_ticket_digest:
        raise TicketCtlError("authority envelope is bound to a different ticket")
    if envelope["repository_digest"] != expected_repository_digest:
        raise TicketCtlError("authority envelope is bound to a different repository")
    if envelope["parent_digest"] is not None:
        raise TicketCtlError("root authority envelope parent_digest must be null")
    path = resolve_record(args, initializing=True)
    store = RecordStore(path)
    with store.lock():
        if path.exists() or store.journal_path.exists():
            raise TicketCtlError("control record already exists")
        record = load_template()
        now = utc_now()
        starting = git_fingerprint(Path(args.repo).resolve())
        ticket_digest = sha256_bytes(args.ticket.encode())
        record["run"].update(
            {
                "id": ticket_digest[:24],
                "ticket_digest": ticket_digest,
                "created_at": now,
                "updated_at": now,
                "authority_root_digest": authority_digest,
                "authority_revision": 1,
                "requested_endpoint": envelope["requested_endpoint"],
                "starting_candidate_digest": starting["digest"],
                "starting_intent_digest": starting["intent_digest"],
            }
        )
        record["contexts"]["authority.root"] = {
            "id": "authority.root",
            "kind": "trusted-instruction",
            "source": "root-user",
            "authority_revision": 1,
            "digest": authority_digest,
            "summary": None,
            "envelope": envelope,
            "recorded_at": now,
        }
        store.commit(
            record,
            "init",
            {"schema_version": SCHEMA_VERSION, "authority_digest": authority_digest, "requested_endpoint": envelope["requested_endpoint"]},
            bypass_lease=True,
        )
    output({"record": os.fspath(path), "run_id": record["run"]["id"]})


def cmd_locate(args: argparse.Namespace) -> None:
    path = resolve_record(args)
    output({"record": os.fspath(path), "exists": path.exists()})


def cmd_show(args: argparse.Namespace) -> None:
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        evaluation = evaluate(record, Path(args.repo).resolve(), store.path)
    terminal = record.get("terminal")
    terminal_current = None
    if terminal is not None:
        current = git_fingerprint(Path(args.repo).resolve())
        terminal_current = bool(
            terminal.get("fingerprint") == current["digest"]
            and terminal.get("intent_fingerprint") == current["intent_digest"]
            and terminal.get("head_fingerprint") == current["head_digest"]
        )
        if terminal.get("status") in POSITIVE_TERMINALS:
            terminal_current = terminal_current and not positive_finish_errors(
                record, terminal["status"], Path(args.repo).resolve(), store.path
            )
        elif terminal.get("status") == NO_CHANGE_TERMINAL:
            terminal_current = terminal_current and not resolved_no_change_errors(
                record, Path(args.repo).resolve(), store.path
            )
        else:
            record["_finish_args"] = {
                "unresolved_actions": terminal.get("unresolved_actions", []),
                "open_findings": terminal.get("open_findings", []),
                "reason_digests": terminal.get("reason_digests", []),
            }
            terminal_current = terminal_current and not interruption_finish_errors(
                record,
                terminal["status"],
                terminal.get("blocked_obligations", []),
                Path(args.repo).resolve(),
                store.path,
            )
            record.pop("_finish_args", None)
    output({"record": record, "evaluation": evaluation, "terminal_current": terminal_current})


def new_lease_token() -> str:
    return f"ticketctl_{secrets.token_urlsafe(32)}"


def cmd_lease_acquire(args: argparse.Namespace) -> None:
    owner_digest = require_digest(args.owner_digest, "owner")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        lease = record["lease"]
        if lease_is_active(lease):
            raise TicketCtlError("an active coordinator lease already exists")
        if lease.get("token_digest") and lease.get("released_at") is None:
            raise TicketCtlError("expired unreleased lease requires guarded takeover")
        token = new_lease_token()
        now = utc_now()
        lease.update(
            {
                "epoch": lease["epoch"] + 1,
                "owner_digest": owner_digest,
                "token_digest": sha256_bytes(token.encode()),
                "acquired_at": now,
                "heartbeat_at": now,
                "expires_at": expiry_time(args.ttl),
                "released_at": None,
                "takeover_reconciliation_digest": None,
                "takeover_journal_head": None,
            }
        )
        store.commit(
            record,
            "lease.acquire",
            {"epoch": lease["epoch"], "owner_digest": owner_digest, "expires_at": lease["expires_at"]},
            bypass_lease=True,
        )
    output({"epoch": lease["epoch"], "token": token, "expires_at": lease["expires_at"]})


def cmd_lease_renew(args: argparse.Namespace) -> None:
    token = lease_token_from_args(args)
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        require_active_lease(record, token, args.lease_epoch)
        now = utc_now()
        record["lease"].update({"heartbeat_at": now, "expires_at": expiry_time(args.ttl)})
        store.commit(
            record,
            "lease.renew",
            {"epoch": args.lease_epoch, "expires_at": record["lease"]["expires_at"]},
            lease_token=token,
            lease_epoch=args.lease_epoch,
        )
    output({"epoch": args.lease_epoch, "expires_at": record["lease"]["expires_at"]})


def cmd_lease_release(args: argparse.Namespace) -> None:
    token = lease_token_from_args(args)
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        require_active_lease(record, token, args.lease_epoch)
        record["lease"]["released_at"] = utc_now()
        store.commit(
            record,
            "lease.release",
            {"epoch": args.lease_epoch},
            bypass_lease=True,
        )
    output({"epoch": args.lease_epoch, "released": True})


def cmd_lease_takeover(args: argparse.Namespace) -> None:
    owner_digest = require_digest(args.owner_digest, "owner")
    reconciliation_digest = require_digest(args.reconciliation_digest, "reconciliation")
    expected_head = require_digest(args.expected_journal_head, "expected journal head")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        lease = record["lease"]
        if lease_is_active(lease):
            raise TicketCtlError("active coordinator lease cannot be taken over")
        if lease.get("released_at") is not None:
            raise TicketCtlError("released lease should be acquired, not taken over")
        if lease.get("token_digest") is None:
            raise TicketCtlError("no prior lease exists; acquire the initial lease")
        if args.expected_epoch != lease["epoch"]:
            raise TicketCtlError("takeover expected lease epoch is stale")
        if expected_head != record["run"]["journal_head"]:
            raise TicketCtlError("takeover expected journal head is stale")
        token = new_lease_token()
        now = utc_now()
        lease.update(
            {
                "epoch": lease["epoch"] + 1,
                "owner_digest": owner_digest,
                "token_digest": sha256_bytes(token.encode()),
                "acquired_at": now,
                "heartbeat_at": now,
                "expires_at": expiry_time(args.ttl),
                "released_at": None,
                "takeover_reconciliation_digest": reconciliation_digest,
                "takeover_journal_head": expected_head,
            }
        )
        for action in record["actions"].values():
            if action.get("status") not in TERMINAL_ACTION_STATES:
                action.update(
                    {"armed_at": None, "arm_expires_at": None, "armed_lease_epoch": None, "armed_authority_revision": None}
                )
        for obligation in record["obligations"].values():
            if obligation.get("status") == "waived":
                obligation.update(
                    {
                        "status": "open",
                        "rationale": None,
                        "waiver_capability": None,
                        "waiver_authority_revision": None,
                    }
                )
        for finding in record["findings"].values():
            if finding.get("disposition") == "accepted-residual":
                finding.update(
                    {
                        "disposition": None,
                        "rationale": None,
                        "waiver_capability": None,
                        "waiver_authority_revision": None,
                    }
                )
        store.commit(
            record,
            "lease.takeover",
            {
                "epoch": lease["epoch"],
                "owner_digest": owner_digest,
                "reconciliation_digest": reconciliation_digest,
                "prior_journal_head": expected_head,
                "unsettled_actions": sorted(
                    action_id
                    for action_id, action in record["actions"].items()
                    if action.get("status") not in TERMINAL_ACTION_STATES
                ),
            },
            bypass_lease=True,
        )
    output({"epoch": lease["epoch"], "token": token, "expires_at": lease["expires_at"]})


def cmd_context_add(args: argparse.Namespace) -> None:
    context_id = require_id(args.id)
    digest = content_digest(digest=args.content_digest, file=args.content_file, field="content")
    summary = safe_text(args.summary, "summary") if args.summary else None
    item = {
        "id": context_id,
        "kind": args.kind,
        "digest": digest,
        "summary": summary,
        "recorded_at": utc_now(),
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        existing = record["contexts"].get(context_id)
        if existing:
            comparable = {key: value for key, value in existing.items() if key != "recorded_at"}
            if comparable == {key: value for key, value in item.items() if key != "recorded_at"}:
                output(existing)
                return
            raise TicketCtlError(f"context {context_id} already exists with different content")
        record["contexts"][context_id] = item
        commit_mutation(store, record, args, "context.add", {"id": context_id, "kind": args.kind, "digest": digest})
    output(item)


def cmd_artifact_add(args: argparse.Namespace) -> None:
    artifact_id = require_id(args.id)
    digest = content_digest(digest=args.content_digest, file=args.content_file, field="content")
    locator = safe_text(args.locator, "locator", 200)
    if not safe_artifact_locator(locator):
        raise TicketCtlError("artifact locator must be a safe relative path under artifacts/")
    dependencies = sorted(set(args.depends_on or []))
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        missing = set(dependencies) - record["artifacts"].keys()
        if missing:
            raise TicketCtlError(f"unknown artifact dependencies: {', '.join(sorted(missing))}")
        actual_digest = file_digest(artifact_path(store.path, locator))
        if actual_digest != digest:
            raise TicketCtlError("artifact locator content does not match the supplied content digest")
        item = {
            "id": artifact_id,
            "kind": args.kind,
            "locator": locator,
            "content_digest": digest,
            "dependencies": dependencies,
            "recorded_at": utc_now(),
        }
        existing = record["artifacts"].get(artifact_id)
        if existing:
            if all(existing.get(key) == value for key, value in item.items() if key != "recorded_at"):
                output(existing)
                return
            raise TicketCtlError(f"artifact {artifact_id} already exists with different coordinates")
        record["artifacts"][artifact_id] = item
        commit_mutation(store, record, args, "artifact.add", {"id": artifact_id, "kind": args.kind, "content_digest": digest})
    output(item)


def cmd_authority_amend(args: argparse.Namespace) -> None:
    envelope, digest = load_authority_envelope(args.authority_envelope)
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        require_active_lease(record, lease_token_from_args(args), args.lease_epoch)
        if envelope["ticket_digest"] != record["run"]["ticket_digest"]:
            raise TicketCtlError("authority amendment is bound to a different ticket")
        if envelope["repository_digest"] != repository_digest(Path(args.repo).resolve()):
            raise TicketCtlError("authority amendment is bound to a different repository")
        current_context = max(
            (
                context
                for context in record["contexts"].values()
                if context.get("kind") == "trusted-instruction"
            ),
            key=lambda context: context.get("authority_revision", 0),
        )
        if envelope["parent_digest"] != current_context["digest"]:
            raise TicketCtlError("authority amendment does not chain from the current authority envelope")
        context_id = f"authority.amendment.{record['run']['revision'] + 1}"
        record["contexts"][context_id] = {
            "id": context_id,
            "kind": "trusted-instruction",
            "source": "direct-user-amendment",
            "authority_revision": record["run"]["authority_revision"] + 1,
            "digest": digest,
            "summary": None,
            "envelope": envelope,
            "recorded_at": utc_now(),
        }
        record["run"]["authority_revision"] += 1
        record["run"]["authority_action_uses"] = 0
        record["run"]["requested_endpoint"] = envelope["requested_endpoint"]
        for existing_capability in record["capabilities"].values():
            existing_capability.update(
                {"authority": "unknown", "basis": None, "rationale": "Authority envelope was amended"}
            )
        for action in record["actions"].values():
            if action.get("status") not in TERMINAL_ACTION_STATES:
                action.update(
                    {"armed_at": None, "arm_expires_at": None, "armed_lease_epoch": None, "armed_authority_revision": None}
                )
        at = utc_now()
        invalidated: list[str] = []
        for evidence_id, evidence in record["evidence"].items():
            if evidence.get("invalidated") is None and (
                evidence.get("kind") == "terminal-audit"
                or "authority-change" in evidence.get("invalidated_by", [])
            ):
                evidence["invalidated"] = {
                    "event": "authority-change",
                    "rationale": "Trusted authority was amended",
                    "at": at,
                }
                invalidated.append(evidence_id)
        record["invalidations"].append(
            {
                "event": "authority-change",
                "rationale": "Trusted authority was amended",
                "at": at,
                "evidence": sorted(invalidated),
            }
        )
        commit_mutation(
            store,
            record,
            args,
            "authority.amend",
            {"id": context_id, "digest": digest, "requested_endpoint": envelope["requested_endpoint"]},
        )
    output(record["contexts"][context_id])


def cmd_capability_set(args: argparse.Namespace) -> None:
    capability_id = require_id(args.id)
    rationale = safe_text(args.rationale, "rationale")
    covers = sorted(set(args.covers or []))
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        unknown = set(covers) - set(record["policy"]["authority_scopes"])
        if unknown:
            raise TicketCtlError(f"capability covers unknown triggers: {', '.join(sorted(unknown))}")
        if args.available != "yes" and args.authority == "granted":
            raise TicketCtlError("authority cannot be granted for an unavailable or unknown capability")
        basis = args.basis
        action_kinds = sorted(set(args.action_kind or []))
        effects = sorted(set(args.effect or []))
        target_digests = sorted(set(require_digest(value, "target") for value in (args.target_digest or [])))
        if args.authority == "granted":
            basis_context = record["contexts"].get(basis) if basis else None
            if (
                not basis_context
                or basis_context.get("kind") != "trusted-instruction"
                or basis_context.get("source") not in {"root-user", "direct-user-amendment"}
            ):
                raise TicketCtlError("granted authority requires an append-only root-user or direct-user-amendment basis")
            envelope = basis_context["envelope"]
            current_authority = max(
                (
                    context
                    for context in record["contexts"].values()
                    if context.get("kind") == "trusted-instruction"
                ),
                key=lambda context: context.get("authority_revision", 0),
            )
            if basis_context["digest"] != current_authority["digest"]:
                raise TicketCtlError("capability basis must be the current canonical authority envelope")
            effective_covers = set(covers) | ({"local-change"} if capability_id == "local-change" else set())
            if effective_covers - set(envelope["allowed_scopes"]):
                raise TicketCtlError("capability scopes exceed the authority envelope")
            if set(action_kinds) - set(envelope["allowed_action_kinds"]):
                raise TicketCtlError("capability action kinds exceed the authority envelope")
            if set(effects) - set(envelope["allowed_effects"]):
                raise TicketCtlError("capability external effects exceed the authority envelope")
            if set(target_digests) - set(envelope["allowed_target_digests"]):
                raise TicketCtlError("capability targets exceed the authority envelope")
            if set(covers) & set(envelope["denials"]):
                raise TicketCtlError("capability requests an explicitly denied scope")
            if args.max_uses < 0 or args.max_uses > envelope["max_actions"]:
                raise TicketCtlError("capability cardinality exceeds the authority envelope")
            if args.delegable and not envelope["delegable"]:
                raise TicketCtlError("capability cannot become delegable when its authority envelope is not")
            if args.expires_at:
                expiry = parse_time(args.expires_at)
                if expiry <= datetime.now(timezone.utc):
                    raise TicketCtlError("capability expiry must be in the future")
                if envelope["expires_at"] and expiry > parse_time(envelope["expires_at"]):
                    raise TicketCtlError("capability expiry exceeds the authority envelope")
            elif envelope["expires_at"]:
                args.expires_at = envelope["expires_at"]
        elif basis and basis not in record["contexts"]:
            raise TicketCtlError("capability basis context does not exist")
        existing = record["capabilities"].get(capability_id, {})
        item = {
            "id": capability_id,
            "required": bool(args.required or existing.get("required")),
            "available": args.available,
            "authority": args.authority,
            "basis": basis,
            "covers": covers,
            "action_kinds": action_kinds,
            "effects": effects,
            "target_digests": target_digests,
            "max_uses": args.max_uses,
            "uses": existing.get("uses", 0),
            "expires_at": args.expires_at,
            "delegable": args.delegable,
            "authority_revision": record["run"]["authority_revision"],
            "rationale": rationale,
            "recorded_at": utc_now(),
        }
        record["capabilities"][capability_id] = item
        commit_mutation(
            store, record, args, "capability.set",
            {"id": capability_id, "available": args.available, "authority": args.authority, "covers": covers},
        )
    output(item)


def cmd_trigger_set(args: argparse.Namespace) -> None:
    trigger_id = require_id(args.id)
    rationale = safe_text(args.rationale, "rationale")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if trigger_id not in record["triggers"]:
            raise TicketCtlError(f"unknown trigger {trigger_id}")
        item = record["triggers"][trigger_id]
        item.update({"decision": args.decision, "rationale": rationale, "recorded_at": utc_now()})
        if args.decision == "yes":
            specification = record["policy"]["trigger_obligations"].get(trigger_id)
            if specification is None:
                raise TicketCtlError(f"trigger {trigger_id} has no obligation policy")
            obligation_id = f"trigger.{trigger_id}"
            existing = record["obligations"].get(obligation_id)
            generated = {
                "id": obligation_id,
                "gate": specification["gate"],
                "kind": specification["kind"],
                "summary": specification["summary"],
                "required": True,
                "waivable": False,
                "condition_trigger": trigger_id,
                "status": "open",
                "evidence": [],
                "rationale": None,
            }
            if existing is None:
                record["obligations"][obligation_id] = generated
            elif any(existing.get(key) != value for key, value in generated.items() if key not in {"status", "evidence", "rationale"}):
                raise TicketCtlError(f"trigger obligation {obligation_id} conflicts with policy")
            item["obligation"] = obligation_id
        commit_mutation(store, record, args, "trigger.set", {"id": trigger_id, "decision": args.decision})
    output(item)


def cmd_claim_add(args: argparse.Namespace) -> None:
    claim_id = require_id(args.id)
    summary = safe_text(args.summary, "summary")
    if args.kind == "terminal" and args.gate != "G8":
        raise TicketCtlError("terminal claims must be assigned to G8")
    if args.kind == "terminal" and not args.terminal_outcome:
        raise TicketCtlError("terminal claims require --terminal-outcome")
    if args.kind != "terminal" and args.terminal_outcome:
        raise TicketCtlError("--terminal-outcome is valid only for terminal claims")
    if args.kind != "terminal" and args.gate not in {"G1", "G4"}:
        raise TicketCtlError("acceptance and risk claims must be assigned to G1 or G4")
    item = {
        "id": claim_id,
        "gate": args.gate,
        "kind": args.kind,
        "criticality": args.criticality,
        "summary": summary,
        "required": not args.optional,
        "terminal_outcome": args.terminal_outcome,
        "authority_revision": None,
        "requested_endpoint": None,
        "evidence": [],
        "recorded_at": utc_now(),
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if claim_id in record["claims"]:
            raise TicketCtlError(f"claim {claim_id} already exists")
        if args.kind == "terminal":
            item.update(
                {
                    "authority_revision": record["run"]["authority_revision"],
                    "requested_endpoint": record["run"]["requested_endpoint"],
                }
            )
        record["claims"][claim_id] = item
        commit_mutation(store, record, args, "claim.add", {"id": claim_id, "gate": args.gate, "kind": args.kind})
    output(item)


def cmd_obligation_add(args: argparse.Namespace) -> None:
    obligation_id = require_id(args.id)
    item = {
        "id": obligation_id,
        "gate": args.gate,
        "kind": require_id(args.kind, "kind"),
        "summary": safe_text(args.summary, "summary"),
        "required": not args.optional,
        "waivable": args.waivable,
        "status": "open",
        "evidence": [],
        "rationale": None,
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if obligation_id in record["obligations"]:
            raise TicketCtlError(f"obligation {obligation_id} already exists")
        record["obligations"][obligation_id] = item
        commit_mutation(store, record, args, "obligation.add", {"id": obligation_id, "gate": args.gate})
    output(item)


def cmd_obligation_resolve(args: argparse.Namespace) -> None:
    obligation_id = require_id(args.id)
    evidence_ids = sorted(set(args.evidence or []))
    rationale = safe_text(args.rationale, "rationale") if args.rationale else None
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        obligation = record["obligations"].get(obligation_id)
        if obligation is None:
            raise TicketCtlError(f"obligation {obligation_id} does not exist")
        missing = set(evidence_ids) - record["evidence"].keys()
        if missing:
            raise TicketCtlError(f"unknown evidence: {', '.join(sorted(missing))}")
        if args.status == "satisfied" and not evidence_ids:
            raise TicketCtlError("satisfied obligations require evidence")
        if args.status == "blocked" and not evidence_ids:
            raise TicketCtlError("blocked obligations require evidence of the blocking condition")
        if args.status in {"waived", "blocked"} and not rationale:
            raise TicketCtlError(f"{args.status} obligations require rationale")
        if args.status == "waived" and not obligation.get("waivable"):
            raise TicketCtlError("this obligation is not waivable")
        if args.status == "waived" and not (
            args.waiver_capability
            and capability_grants_target(
                record,
                args.waiver_capability,
                "accept-residual-risk",
                control_target_digest("obligation", obligation_id),
            )
        ):
            raise TicketCtlError(
                "waiving an obligation requires a current residual-risk capability bound to this obligation"
            )
        if args.status == "open":
            evidence_ids = []
            rationale = None
        obligation.update(
            {
                "status": args.status,
                "evidence": evidence_ids,
                "rationale": rationale,
                "waiver_capability": args.waiver_capability if args.status == "waived" else None,
                "waiver_authority_revision": (
                    record["run"]["authority_revision"] if args.status == "waived" else None
                ),
            }
        )
        commit_mutation(store, record, args, "obligation.resolve", {"id": obligation_id, "status": args.status})
    output(obligation)


def cmd_checkpoint_create(args: argparse.Namespace) -> None:
    checkpoint_id = require_id(args.id)
    summary = safe_text(args.summary, "summary") if args.summary else None
    fingerprint = git_fingerprint(Path(args.repo).resolve())
    dimensions = {
        "candidate": fingerprint["digest"],
        "intent": fingerprint["intent_digest"],
        "head": fingerprint["head_digest"],
        "base": require_digest(args.base_digest, "base"),
        "config": require_digest(args.config_digest, "config"),
        "build": require_digest(args.build_digest, "build"),
        "environment": require_digest(args.environment_digest, "environment"),
        "external": require_digest(args.external_digest, "external"),
    }
    item = {
        "id": checkpoint_id,
        "manifest_digest": sha256_bytes(canonical_json(dimensions)),
        "dimensions": dimensions,
        "dirty": fingerprint["dirty"],
        "summary": summary,
        "recorded_at": utc_now(),
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        existing = record["checkpoints"].get(checkpoint_id)
        if existing:
            if existing.get("manifest_digest") == item["manifest_digest"]:
                record["run"]["current_checkpoint"] = checkpoint_id
                commit_mutation(
                    store,
                    record,
                    args,
                    "checkpoint.activate",
                    {"id": checkpoint_id, "manifest_digest": item["manifest_digest"]},
                )
                output(existing)
                return
            raise TicketCtlError(f"checkpoint {checkpoint_id} already names a different fingerprint")
        record["checkpoints"][checkpoint_id] = item
        record["run"]["current_checkpoint"] = checkpoint_id
        commit_mutation(
            store,
            record,
            args,
            "checkpoint.create",
            {"id": checkpoint_id, "manifest_digest": item["manifest_digest"]},
        )
    output(item)


def cmd_fingerprint(args: argparse.Namespace) -> None:
    output(git_fingerprint(Path(args.repo).resolve()))


def cmd_hash(args: argparse.Namespace) -> None:
    hasher = hashlib.sha256()
    if args.file:
        source = Path(args.file).open("rb")
        close_source = True
    else:
        source = sys.stdin.buffer
        close_source = False
    try:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    finally:
        if close_source:
            source.close()
    output({"algorithm": "sha256", "digest": hasher.hexdigest()})


def cmd_target_derive_pr_slot(args: argparse.Namespace) -> None:
    digest = derive_pr_slot_digest(
        provider=args.provider,
        target_repo=args.target_repo,
        target_ref=args.target_ref,
        head_repo=args.head_repo,
        head_ref=args.head_ref,
        work_unit=args.work_unit,
    )
    output(
        {
            "algorithm": "sha256",
            "domain": PR_SLOT_DOMAIN,
            "schema_version": 1,
            "target_kind": "pr",
            "digest": digest,
        }
    )


def cmd_target_derive_remote_ref(args: argparse.Namespace) -> None:
    digest = derive_remote_ref_digest(
        provider=args.provider,
        repository=args.repository,
        ref=args.ref,
        work_unit=args.work_unit,
    )
    output(
        {
            "algorithm": "sha256",
            "domain": REMOTE_REF_DOMAIN,
            "schema_version": 1,
            "target_kind": "remote",
            "digest": digest,
        }
    )


def cmd_authority_scaffold(args: argparse.Namespace) -> None:
    if not args.ticket:
        raise TicketCtlError("authority scaffold requires --ticket")
    try:
        trusted_turn_digest = file_digest(Path(args.trusted_request_file))
    except OSError as error:
        raise TicketCtlError(f"cannot read trusted request file: {error}") from error
    if args.preset == "local":
        if args.remote_target_digest or args.pr_target_digest or args.max_actions is not None:
            raise TicketCtlError("local authority preset does not accept targets or max-actions")
        endpoint = "local"
        scopes = ["local-change"]
        kinds: list[str] = []
        targets: list[str] = []
        max_actions = 0
    else:
        remote_targets = [
            require_digest(value, "remote target")
            for value in (args.remote_target_digest or [])
        ]
        pr_targets = [
            require_digest(value, "PR target") for value in (args.pr_target_digest or [])
        ]
        if not remote_targets or len(remote_targets) != len(pr_targets):
            raise TicketCtlError(
                "merge-ready-pr authority requires equal nonzero remote-target and PR-target counts"
            )
        targets = remote_targets + pr_targets
        if len(set(targets)) != len(targets):
            raise TicketCtlError("every remote-ref and PR-slot target must be globally distinct")
        minimum_actions = 2 * len(remote_targets)
        if args.max_actions is None or args.max_actions < minimum_actions:
            raise TicketCtlError(
                f"merge-ready-pr authority requires explicit --max-actions of at least {minimum_actions}"
            )
        endpoint = "merge-ready-pr"
        scopes = ["local-change", "external-writes"]
        kinds = ["create-pr", "push", "update-pr"]
        targets = sorted(targets)
        max_actions = args.max_actions
    known_scopes = set(load_template()["policy"]["authority_scopes"])
    envelope: AuthorityEnvelope = {
        "schema_version": 1,
        "trusted_turn_digest": trusted_turn_digest,
        "ticket_digest": sha256_bytes(args.ticket.encode()),
        "repository_digest": repository_digest(Path(args.repo).resolve()),
        "parent_digest": None,
        "requested_endpoint": endpoint,
        "allowed_scopes": scopes,
        "allowed_action_kinds": kinds,
        "allowed_effects": [],
        "allowed_target_digests": targets,
        "denials": sorted(known_scopes - set(scopes)),
        "max_actions": max_actions,
        "expires_at": None,
        "delegable": False,
    }
    validate_authority_envelope(envelope)
    destination = Path(args.output).resolve()
    exclusive_write_json(destination, envelope)
    output(
        {
            "authority_digest": sha256_bytes(canonical_json(envelope)),
            "output": os.fspath(destination),
            "preset": args.preset,
        }
    )


def cmd_action_scaffold(args: argparse.Namespace) -> None:
    manifest = validate_action_manifest(
        {
            "schema_version": 1,
            "kind": args.kind,
            "work_unit": args.work_unit,
            "target_kind": args.target_kind,
            "target_digest": args.target_digest,
            "revision_digest": args.revision_digest,
            "payload_digest": args.payload_digest,
            "effects": sorted(CANONICAL_KIND_EFFECTS[args.kind]),
            "predecessor_action": args.predecessor_action,
        }
    )
    destination = Path(args.output).resolve()
    exclusive_write_json(destination, manifest)
    output(
        {
            "request_digest": sha256_bytes(canonical_json(manifest)),
            "output": os.fspath(destination),
        }
    )


def cmd_profile_apply_routine(args: argparse.Namespace) -> None:
    repository_instructions_digest = require_digest(
        args.repository_instructions_digest, "repository instructions"
    )
    starting_state_digest = require_digest(args.starting_state_digest, "starting state")
    classification_digest = require_digest(args.classification_digest, "classification")
    rationale = safe_text(args.rationale, "rationale")
    repo = Path(args.repo).resolve()
    current = git_fingerprint(repo)
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        require_active_lease(record, lease_token_from_args(args), args.lease_epoch)
        if record["run"].get("requested_endpoint") not in {"local", "static-fact"}:
            raise TicketCtlError("routine profile is valid only for local or static-fact endpoints")
        if current["dirty"]:
            raise TicketCtlError("routine profile requires a clean Git worktree and index")
        if (
            current["digest"] != record["run"].get("starting_candidate_digest")
            or current["intent_digest"] != record["run"].get("starting_intent_digest")
        ):
            raise TicketCtlError("routine profile requires the unchanged starting fingerprint")
        started_collections = (
            "claims", "evidence", "artifacts", "findings", "work_units", "actions", "effects", "checkpoints"
        )
        if any(record[collection] for collection in started_collections) or record["invalidations"]:
            raise TicketCtlError("routine profile cannot be applied after control-record work has started")
        if record["obligations"] != load_template()["obligations"]:
            raise TicketCtlError("routine profile requires pristine obligations")
        if set(record["contexts"]) != {"authority.root"}:
            raise TicketCtlError("routine profile requires a pristine post-init context set")
        local_capability = record["capabilities"].get("local-change", {})
        if any(
            capability_id != "local-change"
            or capability.get("available") != "unknown"
            or capability.get("authority") != "unknown"
            for capability_id, capability in record["capabilities"].items()
        ):
            raise TicketCtlError("routine profile requires pristine capabilities")
        if any(trigger.get("decision") != "unknown" for trigger in record["triggers"].values()):
            raise TicketCtlError("routine profile requires unresolved pristine triggers")
        authority = current_authority_context(record)
        if authority.get("id") != "authority.root" or authority.get("source") != "root-user":
            raise TicketCtlError("routine profile can derive authority only from the root envelope")
        envelope = authority["envelope"]
        if (
            "local-change" not in envelope.get("allowed_scopes", [])
            or (envelope.get("expires_at") and parse_time(envelope["expires_at"]) <= datetime.now(timezone.utc))
        ):
            raise TicketCtlError("root authority does not currently allow local-change")
        now = utc_now()
        record["contexts"]["repository-instructions"] = {
            "id": "repository-instructions",
            "kind": "repository-instructions",
            "digest": repository_instructions_digest,
            "summary": None,
            "recorded_at": now,
        }
        record["contexts"]["starting-state"] = {
            "id": "starting-state",
            "kind": "starting-state",
            "digest": starting_state_digest,
            "summary": None,
            "recorded_at": now,
        }
        record["contexts"]["routine-classification"] = {
            "id": "routine-classification",
            "kind": "design",
            "digest": classification_digest,
            "summary": rationale,
            "recorded_at": now,
        }
        local_capability.update(
            {
                "id": "local-change",
                "required": True,
                "available": "yes",
                "authority": "granted",
                "basis": "authority.root",
                "covers": [],
                "action_kinds": [],
                "effects": [],
                "target_digests": [],
                "max_uses": 0,
                "uses": 0,
                "expires_at": envelope.get("expires_at"),
                "delegable": False,
                "authority_revision": record["run"]["authority_revision"],
                "rationale": rationale,
                "recorded_at": now,
            }
        )
        for trigger in record["triggers"].values():
            trigger.update(
                {
                    "decision": "no",
                    "rationale": rationale,
                    "obligation": None,
                    "recorded_at": now,
                }
            )
        commit_mutation(
            store,
            record,
            args,
            "profile.apply-routine",
            {
                "classification_digest": classification_digest,
                "repository_instructions_digest": repository_instructions_digest,
                "starting_state_digest": starting_state_digest,
            },
        )
    output(
        {
            "profile": "routine",
            "classification_digest": classification_digest,
            "current_gate": evaluate(record, repo, store.path)["current_gate"],
        }
    )


def cmd_evidence_add(args: argparse.Namespace) -> None:
    evidence_id = require_id(args.id)
    digest = content_digest(digest=args.artifact_digest, file=args.artifact_file, field="artifact")
    claim_ids = sorted(set(args.claim or []))
    obligation_ids = sorted(set(args.obligation or []))
    artifact_refs = sorted(set(args.artifact_ref or []))
    reason_digests = sorted(set(require_digest(item, "reason") for item in (args.reason_digest or [])))
    invalidated_by = sorted(
        set(DEFAULT_INVALIDATIONS[args.kind]) | set(args.invalidate_on or [])
    )
    dependencies = sorted(set(DEFAULT_EVIDENCE_DEPENDENCIES[args.kind]) | set(args.depends_on or []))
    unknown_events = set(invalidated_by) - INVALIDATION_EVENTS
    if unknown_events:
        raise TicketCtlError(f"unknown invalidation events: {', '.join(sorted(unknown_events))}")
    unknown_dependencies = set(dependencies) - CHECKPOINT_DIMENSIONS
    if unknown_dependencies:
        raise TicketCtlError(f"unknown checkpoint dimensions: {', '.join(sorted(unknown_dependencies))}")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if evidence_id in record["evidence"]:
            raise TicketCtlError(f"evidence {evidence_id} already exists")
        if args.checkpoint not in record["checkpoints"]:
            raise TicketCtlError(f"checkpoint {args.checkpoint} does not exist")
        if args.checkpoint != record["run"].get("current_checkpoint"):
            raise TicketCtlError("new evidence must bind to the current checkpoint")
        missing_claims = set(claim_ids) - record["claims"].keys()
        missing_obligations = set(obligation_ids) - record["obligations"].keys()
        missing_artifacts = set(artifact_refs) - record["artifacts"].keys()
        if missing_claims or missing_obligations or missing_artifacts:
            missing = sorted(missing_claims | missing_obligations | missing_artifacts)
            raise TicketCtlError(f"unknown evidence targets: {', '.join(missing)}")
        item = {
            "id": evidence_id,
            "kind": args.kind,
            "result": args.result,
            "artifact_digest": digest,
            "checkpoint": args.checkpoint,
            "dependencies": dependencies,
            "review_lenses": sorted(set(args.review_lens or [])),
            "reviewer_digest": None,
            "review_input_digest": None,
            "host_audit": None,
            "work_unit": None,
            "revision_digest": None,
            "target_digest": None,
            "static_oracle_digest": None,
            "surface_digest": None,
            "oracle_actor_digest": None,
            "claims": claim_ids,
            "obligations": obligation_ids,
            "artifacts": artifact_refs,
            "reason_digests": reason_digests,
            "invalidated_by": invalidated_by,
            "invalidated": None,
            "authority_revision": None,
            "requested_endpoint": None,
            "recorded_at": utc_now(),
        }
        if args.kind == "terminal-audit":
            item.update(
                {
                    "authority_revision": record["run"]["authority_revision"],
                    "requested_endpoint": record["run"]["requested_endpoint"],
                }
            )
        if args.kind == "review" and not args.review_lens:
            raise TicketCtlError("review evidence requires at least one --review-lens")
        if args.kind == "review":
            if not args.reviewer_digest or not args.review_input_digest:
                raise TicketCtlError("review evidence requires --reviewer-digest and --review-input-digest")
            item["reviewer_digest"] = require_digest(args.reviewer_digest, "reviewer")
            item["review_input_digest"] = require_digest(args.review_input_digest, "review input")
            duplicate_artifact = next(
                (
                    other_id
                    for other_id, other in record["evidence"].items()
                    if other.get("kind") == "review" and other.get("artifact_digest") == digest
                ),
                None,
            )
            if duplicate_artifact:
                raise TicketCtlError(f"review artifact digest is already used by evidence {duplicate_artifact}")
        if args.kind != "review" and args.review_lens:
            raise TicketCtlError("--review-lens is valid only for review evidence")
        if args.kind != "review" and (args.reviewer_digest or args.review_input_digest):
            raise TicketCtlError("review provenance fields are valid only for review evidence")
        if args.kind == "blocker" and not reason_digests:
            raise TicketCtlError("blocker evidence requires at least one --reason-digest")
        if args.kind != "blocker" and reason_digests:
            raise TicketCtlError("--reason-digest is valid only for blocker evidence")
        static_fields = (args.static_oracle_digest, args.surface_digest, args.oracle_actor_digest)
        if any(static_fields):
            if args.kind != "inspection" or record["run"].get("requested_endpoint") != "static-fact":
                raise TicketCtlError("static oracle fields require inspection evidence for a static-fact endpoint")
            if not all(static_fields):
                raise TicketCtlError("static inspection requires oracle, surface, and oracle-actor digests together")
            normalized_static = [
                require_digest(str(value), field)
                for value, field in zip(
                    static_fields,
                    ("static oracle", "complete surface", "oracle actor"),
                    strict=True,
                )
            ]
            if len(set([digest, *normalized_static])) != 4:
                raise TicketCtlError("static oracle provenance digests must be distinct")
            item.update(
                {
                    "static_oracle_digest": normalized_static[0],
                    "surface_digest": normalized_static[1],
                    "oracle_actor_digest": normalized_static[2],
                }
            )
        if args.kind == "host-audit":
            host_fields = (
                args.lanes,
                args.feedback,
                args.automated_review,
                args.human_approval,
                args.draft,
                args.mergeable,
            )
            if any(value is None for value in host_fields):
                raise TicketCtlError("host-audit evidence requires every structured readiness field")
            pending = sorted(set(args.pending or []))
            if args.human_approval == "pending" and "human-approval" not in pending:
                raise TicketCtlError("pending human approval must be named in --pending")
            if args.human_approval == "pending" and not args.pending_human_digest:
                raise TicketCtlError("pending human approval requires --pending-human-digest")
            if args.pending_human_digest:
                require_digest(args.pending_human_digest, "pending human")
            unit_id = require_id(args.work_unit or "", "work unit")
            unit = record["work_units"].get(unit_id)
            if unit is None:
                raise TicketCtlError("host-audit evidence requires an existing --work-unit")
            revision_digest = require_digest(args.revision_digest or "", "revision")
            target_digest = require_digest(args.target_digest or "", "target")
            coordinates = unit.get("coordinates", {})
            if revision_digest != coordinates.get("head"):
                raise TicketCtlError("host-audit revision does not match the work-unit head")
            if target_digest not in {coordinates.get("remote"), coordinates.get("pr")}:
                raise TicketCtlError("host-audit target does not match the work-unit remote or PR")
            item.update(
                {
                    "work_unit": unit_id,
                    "revision_digest": revision_digest,
                    "target_digest": target_digest,
                }
            )
            item["host_audit"] = {
                "lanes": args.lanes,
                "feedback": args.feedback,
                "automated_review": args.automated_review,
                "human_approval": args.human_approval,
                "draft": args.draft,
                "mergeable": args.mergeable,
                "pending": pending,
                "pending_human_digest": args.pending_human_digest,
            }
        elif any(
            value is not None
            for value in (
                args.lanes,
                args.feedback,
                args.automated_review,
                args.human_approval,
                args.draft,
                args.mergeable,
                args.pending_human_digest,
                args.work_unit,
                args.revision_digest,
                args.target_digest,
            )
        ) or args.pending:
            raise TicketCtlError("host readiness fields are valid only for host-audit evidence")
        record["evidence"][evidence_id] = item
        for claim_id in claim_ids:
            record["claims"][claim_id]["evidence"] = sorted(
                set(record["claims"][claim_id].get("evidence", [])) | {evidence_id}
            )
        for obligation_id in obligation_ids:
            record["obligations"][obligation_id]["evidence"] = sorted(
                set(record["obligations"][obligation_id].get("evidence", [])) | {evidence_id}
            )
        commit_mutation(store, record, args, "evidence.add", {"id": evidence_id, "kind": args.kind, "result": args.result})
    output(item)


def cmd_invalidate(args: argparse.Namespace) -> None:
    rationale = safe_text(args.rationale, "rationale")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        invalidated: list[str] = []
        at = utc_now()
        for evidence_id, evidence in record["evidence"].items():
            if evidence.get("invalidated") is None and args.event in evidence.get("invalidated_by", []):
                evidence["invalidated"] = {"event": args.event, "rationale": rationale, "at": at}
                invalidated.append(evidence_id)
        record["invalidations"].append(
            {"event": args.event, "rationale": rationale, "at": at, "evidence": sorted(invalidated)}
        )
        if args.event == "authority-change":
            for capability in record["capabilities"].values():
                capability.update({"authority": "unknown", "basis": None, "rationale": None})
        commit_mutation(store, record, args, "invalidate", {"event": args.event, "evidence": sorted(invalidated)})
    output({"event": args.event, "invalidated": sorted(invalidated)})


def cmd_finding_add(args: argparse.Namespace) -> None:
    finding_id = require_id(args.id)
    item = {
        "id": finding_id,
        "severity": args.severity,
        "origin": args.origin,
        "summary": safe_text(args.summary, "summary"),
        "disposition": None,
        "rationale": None,
        "evidence": [],
        "recorded_at": utc_now(),
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if finding_id in record["findings"]:
            raise TicketCtlError(f"finding {finding_id} already exists")
        record["findings"][finding_id] = item
        commit_mutation(
            store,
            record,
            args,
            "finding.add",
            {"id": finding_id, "severity": args.severity, "origin": args.origin},
        )
    output(item)


def cmd_finding_dispose(args: argparse.Namespace) -> None:
    finding_id = require_id(args.id)
    evidence_ids = sorted(set(args.evidence or []))
    rationale = safe_text(args.rationale, "rationale")
    if not evidence_ids:
        raise TicketCtlError("finding dispositions require evidence")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        finding = record["findings"].get(finding_id)
        if finding is None:
            raise TicketCtlError(f"finding {finding_id} does not exist")
        missing = set(evidence_ids) - record["evidence"].keys()
        if missing:
            raise TicketCtlError(f"unknown evidence: {', '.join(sorted(missing))}")
        if finding["severity"] in {"blocker", "major"} and args.disposition == "follow-up":
            raise TicketCtlError("blocker and major findings cannot be deferred to follow-up")
        canonical_finding = None
        waiver_capability = None
        if args.disposition == "duplicate":
            canonical_finding = require_id(args.canonical_finding or "", "canonical finding")
            canonical = record["findings"].get(canonical_finding)
            if canonical is None or canonical_finding == finding_id:
                raise TicketCtlError("duplicate disposition requires a distinct existing canonical finding")
            if canonical.get("disposition") == "duplicate":
                raise TicketCtlError("canonical finding cannot itself be a duplicate")
        elif args.canonical_finding:
            raise TicketCtlError("--canonical-finding is valid only for duplicate dispositions")
        if args.disposition == "accepted-residual":
            waiver_capability = require_id(args.waiver_capability or "", "waiver capability")
            if not capability_grants_target(
                record,
                waiver_capability,
                "accept-residual-risk",
                control_target_digest("finding", finding_id),
            ):
                raise TicketCtlError(
                    "accepted-residual requires a current residual-risk capability bound to this finding"
                )
        elif args.waiver_capability:
            raise TicketCtlError("--waiver-capability is valid only for accepted-residual dispositions")
        finding.update(
            {
                "disposition": args.disposition,
                "rationale": rationale,
                "evidence": evidence_ids,
                "canonical_finding": canonical_finding,
                "waiver_capability": waiver_capability,
                "waiver_authority_revision": (
                    record["run"]["authority_revision"] if waiver_capability else None
                ),
            }
        )
        commit_mutation(store, record, args, "finding.dispose", {"id": finding_id, "disposition": args.disposition})
    output(finding)


def cmd_work_add(args: argparse.Namespace) -> None:
    unit_id = require_id(args.id)
    dependencies = sorted(set(args.depends_on or []))
    claim_ids = sorted(set(args.claim or []))
    obligation_ids = sorted(set(args.obligation or []))
    item = {
        "id": unit_id,
        "summary": safe_text(args.summary, "summary"),
        "required": not args.optional,
        "depends_on": dependencies,
        "claims": claim_ids,
        "obligations": obligation_ids,
        "status": "planned",
        "evidence": [],
        "evidence_epoch": None,
        "coordinates": {name: None for name in ("branch", "worktree", "base", "head", "remote", "pr")},
        "rationale": None,
        "recorded_at": utc_now(),
    }
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if unit_id in record["work_units"]:
            raise TicketCtlError(f"work unit {unit_id} already exists")
        missing = (set(dependencies) - record["work_units"].keys()) | (
            set(claim_ids) - record["claims"].keys()
        ) | (set(obligation_ids) - record["obligations"].keys())
        if missing:
            raise TicketCtlError(f"unknown work-unit references: {', '.join(sorted(missing))}")
        record["work_units"][unit_id] = item
        error = graph_error(record["work_units"])
        if error:
            raise TicketCtlError(error)
        commit_mutation(store, record, args, "work.add", {"id": unit_id, "depends_on": dependencies})
    output(item)


def cmd_work_set(args: argparse.Namespace) -> None:
    unit_id = require_id(args.id)
    evidence_ids = sorted(set(args.evidence or []))
    rationale = safe_text(args.rationale, "rationale") if args.rationale else None
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        unit = record["work_units"].get(unit_id)
        if unit is None:
            raise TicketCtlError(f"work unit {unit_id} does not exist")
        missing = set(evidence_ids) - record["evidence"].keys()
        if missing:
            raise TicketCtlError(f"unknown evidence: {', '.join(sorted(missing))}")
        if args.status == "done" and not evidence_ids:
            raise TicketCtlError("done work units require evidence")
        if args.evidence_epoch and args.evidence_epoch not in record["checkpoints"]:
            raise TicketCtlError(f"checkpoint {args.evidence_epoch} does not exist")
        if args.status == "done" and not (args.evidence_epoch or unit.get("evidence_epoch")):
            raise TicketCtlError("done work units require --evidence-epoch")
        if args.status in {"skipped", "blocked"} and not rationale:
            raise TicketCtlError(f"{args.status} work units require rationale")
        if args.status == "skipped" and unit.get("required"):
            raise TicketCtlError("required work units cannot be skipped")
        if args.depends_on is not None:
            dependencies = sorted(set(args.depends_on))
            missing_dependencies = set(dependencies) - record["work_units"].keys()
            if missing_dependencies:
                raise TicketCtlError(f"unknown dependencies: {', '.join(sorted(missing_dependencies))}")
            unit["depends_on"] = dependencies
            error = graph_error(record["work_units"])
            if error:
                raise TicketCtlError(error)
        unit.update({"status": args.status, "evidence": evidence_ids, "rationale": rationale})
        if args.evidence_epoch:
            unit["evidence_epoch"] = args.evidence_epoch
        commit_mutation(store, record, args, "work.set", {"id": unit_id, "status": args.status})
    output(unit)


def cmd_work_coordinate(args: argparse.Namespace) -> None:
    unit_id = require_id(args.id)
    updates = {
        name: require_digest(value, name)
        for name in ("branch", "worktree", "base", "head", "remote", "pr")
        if (value := getattr(args, f"{name}_digest")) is not None
    }
    if not updates and not args.evidence_epoch:
        raise TicketCtlError("provide at least one coordinate digest or --evidence-epoch")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        unit = record["work_units"].get(unit_id)
        if unit is None:
            raise TicketCtlError(f"work unit {unit_id} does not exist")
        if args.evidence_epoch and args.evidence_epoch not in record["checkpoints"]:
            raise TicketCtlError(f"checkpoint {args.evidence_epoch} does not exist")
        unit.setdefault("coordinates", {}).update(updates)
        if args.evidence_epoch:
            unit["evidence_epoch"] = args.evidence_epoch
        commit_mutation(
            store, record, args, "work.coordinate",
            {"id": unit_id, "coordinates": sorted(updates), "evidence_epoch": args.evidence_epoch},
        )
    output(unit)


def required_action_triggers(kind: str) -> set[str]:
    return ACTION_TRIGGER_REQUIREMENTS.get(kind, {"external-writes"})


def cmd_action_prepare(args: argparse.Namespace) -> None:
    action_id = require_id(args.id)
    capability_id = require_id(args.capability, "capability")
    manifest, request_digest = load_action_manifest(args.request_manifest)
    target_digest = manifest["target_digest"]
    expected_state_digest = content_digest(
        digest=args.expected_state_digest, file=args.expected_state_file, field="expected-state"
    )
    effects = manifest["effects"]
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        checkpoint_id = record["run"].get("current_checkpoint")
        if checkpoint_id is None:
            raise TicketCtlError("external actions require a current checkpoint manifest")
        coherence_error = action_coherence_error(
            record,
            {
                **manifest,
                "checkpoint": checkpoint_id,
            },
        )
        if coherence_error:
            raise TicketCtlError(f"action request is incoherent: {coherence_error}")
        correlation_digest = sha256_bytes(
            canonical_json(
                [
                    manifest["kind"],
                    manifest["work_unit"],
                    manifest["target_kind"],
                    target_digest,
                    manifest["revision_digest"],
                    manifest["payload_digest"],
                    effects,
                    expected_state_digest,
                ]
            )
        )
        predecessor_id = manifest["predecessor_action"]
        if predecessor_id is not None:
            predecessor = record["actions"].get(predecessor_id)
            if predecessor is None or predecessor.get("status") != "verified-not-applied":
                raise TicketCtlError("action retry requires a verified-not-applied predecessor")
            if predecessor.get("correlation_digest") != correlation_digest:
                raise TicketCtlError("action retry does not match its predecessor's semantic operation")
            if action_has_equivalent_effect(record, predecessor_id, predecessor):
                raise TicketCtlError("action retry is unsafe because the predecessor has an observed effect")
            successor = next(
                (
                    other_id
                    for other_id, other in record["actions"].items()
                    if other_id != action_id and other.get("predecessor_action") == predecessor_id
                ),
                None,
            )
            if successor:
                raise TicketCtlError(f"action predecessor already has successor {successor}")
        idempotency_digest = sha256_bytes(
            canonical_json(
                [
                    correlation_digest,
                    predecessor_id,
                    record["run"]["authority_revision"],
                ]
            )
        )
        immutable = {
            "kind": manifest["kind"],
            "capability": capability_id,
            "target_kind": manifest["target_kind"],
            "target_digest": target_digest,
            "request_digest": request_digest,
            "payload_digest": manifest["payload_digest"],
            "expected_state_digest": expected_state_digest,
            "effects": effects,
            "idempotency_digest": idempotency_digest,
            "correlation_digest": correlation_digest,
            "predecessor_action": predecessor_id,
            "work_unit": manifest["work_unit"],
            "revision_digest": manifest["revision_digest"],
            "authority_revision": record["run"]["authority_revision"],
            "lease_epoch": record["lease"]["epoch"],
            "checkpoint": checkpoint_id,
        }
        existing = record["actions"].get(action_id)
        if existing:
            if all(existing.get(key) == value for key, value in immutable.items()):
                output(existing)
                return
            raise TicketCtlError(f"action {action_id} was already prepared with different content")
        correlated_actions = {
            other_id: other
            for other_id, other in record["actions"].items()
            if other.get("correlation_digest") == correlation_digest
        }
        if predecessor_id is None and correlated_actions:
            collision = next(iter(correlated_actions))
            raise TicketCtlError(f"semantic operation already belongs to action {collision}")
        unsafe_correlation = next(
            (
                other_id
                for other_id, other in correlated_actions.items()
                if other.get("status") != "verified-not-applied"
                or action_has_equivalent_effect(record, other_id, other)
            ),
            None,
        )
        if unsafe_correlation:
            raise TicketCtlError(
                f"semantic operation may already have been applied by action {unsafe_correlation}"
            )
        capability = record["capabilities"].get(capability_id)
        capability_error = action_capability_error(record, immutable)
        if capability_error:
            raise TicketCtlError(capability_error)
        assert capability is not None
        if capability.get("uses", 0) >= capability.get("max_uses", 0):
            raise TicketCtlError("external action capability has exhausted its cardinality")
        basis_context = record["contexts"].get(capability.get("basis"), {})
        envelope = basis_context.get("envelope", {})
        if record["run"].get("authority_action_uses", 0) >= envelope.get("max_actions", 0):
            raise TicketCtlError("authority envelope has exhausted its global action cardinality")
        required_triggers = required_action_triggers(manifest["kind"]) | {
            trigger
            for effect in effects
            for trigger in EFFECT_TRIGGER_REQUIREMENTS.get(effect, set())
        }
        for trigger_id in required_triggers:
            if record["triggers"].get(trigger_id, {}).get("decision") != "yes":
                raise TicketCtlError(f"action requires trigger {trigger_id}=yes")
        if not required_triggers.issubset(set(capability.get("covers", []))):
            missing = required_triggers - set(capability.get("covers", []))
            raise TicketCtlError(f"action capability does not cover triggers: {', '.join(sorted(missing))}")
        collision = next(
            (
                other_id
                for other_id, action in record["actions"].items()
                if action.get("idempotency_digest") == idempotency_digest
            ),
            None,
        )
        if collision:
            raise TicketCtlError(f"idempotency digest already belongs to action {collision}")
        item = {
            "id": action_id,
            **immutable,
            "status": "prepared",
            "receipt_digest": None,
            "armed_at": None,
            "arm_expires_at": None,
            "armed_lease_epoch": None,
            "armed_authority_revision": None,
            "prepared_at": utc_now(),
            "settled_at": None,
        }
        record["actions"][action_id] = item
        capability["uses"] = capability.get("uses", 0) + 1
        record["run"]["authority_action_uses"] = record["run"].get("authority_action_uses", 0) + 1
        commit_mutation(store, record, args, "action.prepare", {"id": action_id, **immutable})
    output(item)


def cmd_action_arm(args: argparse.Namespace) -> None:
    action_id = require_id(args.id)
    observed_state_digest = require_digest(args.observed_state_digest, "observed state")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        require_active_lease(record, lease_token_from_args(args), args.lease_epoch)
        action = record["actions"].get(action_id)
        if action is None or action.get("status") != "prepared":
            raise TicketCtlError("only a prepared action can be armed")
        if observed_state_digest != action.get("expected_state_digest"):
            raise TicketCtlError("observed external state does not match the prepared expected state")
        if action.get("checkpoint") != record["run"].get("current_checkpoint"):
            raise TicketCtlError("action checkpoint is no longer current")
        capability_error = action_capability_error(record, action)
        coherence_error = action_coherence_error(record, action)
        if capability_error or coherence_error:
            raise TicketCtlError(capability_error or coherence_error or "action is stale")
        now = utc_now()
        action.update(
            {
                "armed_at": now,
                "arm_expires_at": expiry_time(args.ttl),
                "armed_lease_epoch": record["lease"]["epoch"],
                "armed_authority_revision": record["run"]["authority_revision"],
            }
        )
        commit_mutation(store, record, args, "action.arm", {"id": action_id, "expires_at": action["arm_expires_at"]})
    output(action)


def cmd_action_settle(args: argparse.Namespace) -> None:
    action_id = require_id(args.id)
    receipt_digest = content_digest(digest=args.receipt_digest, file=args.receipt_file, field="receipt")
    desired = {
        "succeeded": "applied-unverified",
        "uncertain": "uncertain",
        "verified-applied": "verified-applied",
        "verified-not-applied": "verified-not-applied",
    }[args.outcome]
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        action = record["actions"].get(action_id)
        if action is None:
            raise TicketCtlError(f"action {action_id} does not exist; prepare it before the external write")
        if action["status"] == desired and action.get("receipt_digest") == receipt_digest:
            output(action)
            return
        if desired not in ACTION_TRANSITIONS[action["status"]]:
            raise TicketCtlError(f"cannot transition action from {action['status']} to {desired}")
        reconciliation_effect: str | None = None
        if action["status"] == "uncertain" and desired == "verified-applied":
            reconciliation_effect = require_id(args.effect or "", "effect")
            effect = record["effects"].get(reconciliation_effect)
            if (
                effect is None
                or effect.get("action") != action_id
                or effect.get("kind") != action.get("kind")
                or effect.get("target_kind") != action.get("target_kind")
                or effect.get("target_digest") != action.get("target_digest")
                or effect.get("revision_digest") != action.get("revision_digest")
                or effect.get("work_unit") != action.get("work_unit")
                or effect.get("checkpoint") != record["run"].get("current_checkpoint")
                or effect.get("authority_revision") != record["run"].get("authority_revision")
                or effect.get("lease_epoch") != record["lease"].get("epoch")
                or effect.get("receipt_digest") != receipt_digest
            ):
                raise TicketCtlError("uncertain reconciliation requires a fresh current linked effect receipt")
            capability_error = action_capability_error(record, action, allow_prior_lease=True)
            coherence_error = action_coherence_error(record, action)
            if capability_error or coherence_error:
                raise TicketCtlError(capability_error or coherence_error or "action reconciliation is stale")
        elif desired in {"applied-unverified", "verified-applied"}:
            observed_state_digest = require_digest(
                args.observed_state_digest or "", "observed state"
            )
            capability_error = action_capability_error(record, action)
            coherence_error = action_coherence_error(record, action)
            if capability_error or coherence_error:
                raise TicketCtlError(capability_error or coherence_error or "action is stale")
            if (
                action.get("armed_lease_epoch") != record["lease"]["epoch"]
                or action.get("armed_authority_revision") != record["run"]["authority_revision"]
                or not action.get("arm_expires_at")
                or parse_time(action["arm_expires_at"]) <= datetime.now(timezone.utc)
            ):
                raise TicketCtlError("action was not armed under the current live lease and authority revision")
            if observed_state_digest != action.get("expected_state_digest"):
                raise TicketCtlError("action settlement does not confirm the armed expected external state")
        action.update(
            {
                "status": desired,
                "receipt_digest": receipt_digest,
                "reconciliation_effect": reconciliation_effect,
                "settled_at": utc_now(),
            }
        )
        if desired in {"uncertain", "verified-applied", "verified-not-applied"}:
            action.update(
                {
                    "armed_at": None,
                    "arm_expires_at": None,
                    "armed_lease_epoch": None,
                    "armed_authority_revision": None,
                }
            )
        commit_mutation(store, record, args, "action.settle", {"id": action_id, "status": desired, "receipt_digest": receipt_digest})
    output(action)


def cmd_effect_observe(args: argparse.Namespace) -> None:
    effect_id = require_id(args.id)
    receipt_digest = content_digest(digest=args.receipt_digest, file=args.receipt_file, field="receipt")
    actor_digest = require_digest(args.actor_digest, "actor")
    action_id = require_id(args.action, "action")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        ensure_open(record)
        if effect_id in record["effects"]:
            raise TicketCtlError(f"effect {effect_id} already exists")
        action = record["actions"].get(action_id)
        if action is None:
            raise TicketCtlError("observed effect must link to a prepared action")
        checkpoint_id = record["run"].get("current_checkpoint")
        if not checkpoint_id or action.get("checkpoint") != checkpoint_id:
            raise TicketCtlError("observed effect action must bind to the current checkpoint")
        capability_error = action_capability_error(record, action, allow_prior_lease=True)
        coherence_error = action_coherence_error(record, action)
        if capability_error or coherence_error:
            raise TicketCtlError(capability_error or coherence_error or "observed effect is stale")
        item = {
            "id": effect_id,
            "kind": action["kind"],
            "target_kind": action["target_kind"],
            "target_digest": action["target_digest"],
            "revision_digest": action["revision_digest"],
            "work_unit": action["work_unit"],
            "action": action_id,
            "actor": args.actor,
            "actor_digest": actor_digest,
            "receipt_digest": receipt_digest,
            "checkpoint": checkpoint_id,
            "authority_revision": record["run"]["authority_revision"],
            "lease_epoch": record["lease"]["epoch"],
            "correlation_digest": action.get("correlation_digest"),
            "observed_at": utc_now(),
        }
        record["effects"][effect_id] = item
        commit_mutation(
            store,
            record,
            args,
            "effect.observe",
            {
                "id": effect_id,
                "kind": action["kind"],
                "target_digest": action["target_digest"],
                "action": action_id,
                "actor": args.actor,
            },
        )
    output(item)


def cmd_gate(args: argparse.Namespace) -> None:
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        result = evaluate(record, Path(args.repo).resolve(), store.path)
    output(result)


def cmd_next(args: argparse.Namespace) -> None:
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        result = evaluate(record, Path(args.repo).resolve(), store.path)
    if result["current_gate"] is None:
        output(
            {
                "gate": None,
                "next": "Record is eligible for a guarded positive finish",
                "eligible_work_units": eligible_work_units(record),
            }
        )
        return
    gate = next(item for item in result["gates"] if item["gate"] == result["current_gate"])
    output(
        {
            "gate": gate["gate"],
            "next": gate["reasons"],
            "reason_digests": gate["reason_digests"],
            "eligible_work_units": eligible_work_units(record),
        }
    )


def current_terminal_claim(
    record: dict[str, Any],
    status: str,
    current: Fingerprint,
    record_path: Path | None = None,
) -> bool:
    return any(
        claim.get("kind") == "terminal"
        and claim.get("terminal_outcome") == status
        and claim.get("authority_revision") == record["run"].get("authority_revision")
        and claim.get("requested_endpoint") == record["run"].get("requested_endpoint")
        and any_fresh_evidence(
            record, claim.get("evidence", []), current, "G8", record_path
        )
        for claim in record["claims"].values()
    )


def terminal_matches_endpoint(status: str, endpoint: str) -> bool:
    if status in {"blocked", "partial", NO_CHANGE_TERMINAL}:
        return True
    if status == "merge-ready-awaiting-human":
        return endpoint == "merge"
    return status == "complete" and endpoint in REQUESTED_ENDPOINTS | LEGACY_REQUESTED_ENDPOINTS


def positive_finish_errors(
    record: dict[str, Any], status: str, repo: Path, record_path: Path | None = None
) -> list[str]:
    current = git_fingerprint(repo)
    result = evaluate(record, repo, record_path)
    errors: list[str] = []
    if not result["ready_to_finish"]:
        errors.append(f"earliest failing gate is {result['current_gate']}")
    if not current_terminal_claim(record, status, current, record_path):
        errors.append(f"no fresh terminal claim supports {status}")
    fresh_host_audits = [
        evidence
        for evidence_id, evidence in record["evidence"].items()
        if evidence.get("kind") == "host-audit"
        and fresh_evidence_reason(record, evidence_id, current, record_path) is None
    ]
    if record["triggers"]["external-writes"]["decision"] == "yes":
        if not fresh_host_audits:
            errors.append("external delivery lacks a fresh host audit")
        for evidence in fresh_host_audits:
            audit = evidence.get("host_audit") or {}
            if status == "complete" and (
                audit.get("human_approval") == "pending" or audit.get("pending")
            ):
                errors.append("complete cannot leave human approval or merge pending")
            if status == "merge-ready-awaiting-human":
                if set(audit.get("pending", [])) - {"human-approval", "merge"}:
                    errors.append("merge-ready may leave only named human approval and merge pending")
                if not audit.get("pending"):
                    errors.append("merge-ready must name the pending human approval and/or merge action")
    endpoint = record["run"].get("requested_endpoint")
    requires_pr_delivery = status == "merge-ready-awaiting-human" or (
        status == "complete" and endpoint == "merge-ready-pr"
    )
    if requires_pr_delivery:
        if record["triggers"]["external-writes"]["decision"] != "yes":
            errors.append("the requested PR-delivery outcome requires external-writes=yes")
        for gate in ("G6", "G7"):
            gate_result = next(item for item in result["gates"] if item["gate"] == gate)
            if not gate_result["passed"]:
                errors.append(f"the requested PR-delivery outcome requires current {gate}")
        required_units = required_work_unit_ids(record["work_units"])
        delivery_units = {
            unit_id
            for unit_id in required_units
            if all(
                DIGEST_PATTERN.fullmatch(
                    str(record["work_units"][unit_id].get("coordinates", {}).get(coordinate, ""))
                )
                for coordinate in ("head", "remote", "pr")
            )
        }
        if not delivery_units:
            errors.append(
                "the requested PR-delivery outcome requires a required work unit with "
                "current head, remote, and PR-slot coordinates"
            )
        delivery_proofs: list[tuple[bool, bool, bool]] = []
        for unit_id in delivery_units:
            unit = record["work_units"][unit_id]
            coordinates = unit["coordinates"]
            has_push = any(
                action.get("kind") == "push"
                and action.get("work_unit") == unit_id
                and action.get("target_kind") == "remote"
                and action.get("target_digest") == coordinates["remote"]
                and action.get("revision_digest") == coordinates["head"]
                and action_is_current_applied(record, action_id, action)
                for action_id, action in record["actions"].items()
            )
            has_pr = any(
                action.get("kind") in {"create-pr", "update-pr"}
                and action.get("work_unit") == unit_id
                and action.get("target_kind") == "pr"
                and action.get("target_digest") == coordinates["pr"]
                and action.get("revision_digest") == coordinates["head"]
                and action_is_current_applied(record, action_id, action)
                for action_id, action in record["actions"].items()
            )
            has_pr_audit = any(
                evidence.get("work_unit") == unit_id
                and evidence.get("revision_digest") == coordinates["head"]
                and evidence.get("target_digest") == coordinates["pr"]
                and (
                    (
                        status == "merge-ready-awaiting-human"
                        and bool((evidence.get("host_audit") or {}).get("pending"))
                        and not set((evidence.get("host_audit") or {}).get("pending", []))
                        - {"human-approval", "merge"}
                    )
                    or (
                        status == "complete"
                        and not (evidence.get("host_audit") or {}).get("pending")
                    )
                )
                for evidence in fresh_host_audits
            )
            delivery_proofs.append((has_push, has_pr, has_pr_audit))
        if delivery_units and not any(all(proof) for proof in delivery_proofs):
            if not any(proof[0] for proof in delivery_proofs):
                errors.append("PR delivery lacks a current applied push")
            if not any(proof[1] for proof in delivery_proofs):
                errors.append("PR delivery lacks a current applied create/update PR action")
            if not any(proof[2] for proof in delivery_proofs):
                errors.append(
                    "PR delivery lacks a current PR host audit with "
                    f"{'named human-only pending work' if status == 'merge-ready-awaiting-human' else 'no pending work'}"
                )
            if all(any(proof[index] for proof in delivery_proofs) for index in range(3)):
                errors.append("PR delivery proof is split across unrelated work-unit coordinates")
    nonterminal = [
        action_id for action_id, action in record["actions"].items() if action.get("status") not in TERMINAL_ACTION_STATES
    ]
    if nonterminal:
        errors.append(f"external actions have uncertain or unverified outcomes: {', '.join(sorted(nonterminal))}")
    for action_id, action in record["actions"].items():
        if action.get("status") != "verified-not-applied":
            continue
        if action.get("checkpoint") != record["run"].get("current_checkpoint"):
            continue
        equivalent_applied = any(
            other_id != action_id
            and other.get("kind") == action.get("kind")
            and other.get("target_digest") == action.get("target_digest")
            and other.get("status") == "verified-applied"
            for other_id, other in record["actions"].items()
        ) or action_has_equivalent_effect(record, action_id, action)
        if not equivalent_applied:
            errors.append(f"external action {action_id} was not applied and has no current equivalent observed effect")
    if status == "complete":
        for trigger, kinds in COMPLETION_ACTIONS.items():
            if record["triggers"][trigger]["decision"] != "yes":
                continue
            if not any(
                action.get("kind") in kinds
                and action_is_current_applied(record, action_id, action)
                for action_id, action in record["actions"].items()
            ) and not any(
                effect.get("kind") in kinds
                and effect.get("checkpoint") == record["run"].get("current_checkpoint")
                and record["actions"].get(effect.get("action"), {}).get("kind") == effect.get("kind")
                and record["work_units"].get(effect.get("work_unit"), {}).get("coordinates", {}).get("head")
                == effect.get("revision_digest")
                for effect in record["effects"].values()
            ):
                errors.append(f"trigger {trigger}=yes lacks a verified applied completion action")
    return errors


def resolved_no_change_errors(
    record: dict[str, Any], repo: Path, record_path: Path | None = None
) -> list[str]:
    current = git_fingerprint(repo)
    result = evaluate(record, repo, record_path)
    errors: list[str] = []
    for gate in ("G0", "G1"):
        gate_result = next(item for item in result["gates"] if item["gate"] == gate)
        reasons = list(gate_result["reasons"])
        if gate == "G0":
            endpoint = record["run"].get("requested_endpoint")
            endpoint_reason = f"requested endpoint {endpoint} requires trigger {ENDPOINT_TRIGGER.get(str(endpoint))}=yes"
            reasons = [reason for reason in reasons if reason != endpoint_reason]
        if reasons:
            errors.append(f"{gate} is not passed: {'; '.join(reasons)}")
    if record["work_units"]:
        errors.append("resolved-no-change cannot contain implementation work units")
    if current["digest"] != record["run"].get("starting_candidate_digest"):
        errors.append("resolved-no-change has an owned candidate-content delta from the starting state")
    if current["intent_digest"] != record["run"].get("starting_intent_digest"):
        errors.append("resolved-no-change has a tracked/index/intent delta from the starting state")
    invalid_actions = [
        action_id
        for action_id, action in record["actions"].items()
        if action.get("kind") != "tracker-write" or action.get("status") not in TERMINAL_ACTION_STATES
    ]
    if invalid_actions:
        errors.append("resolved-no-change permits only reconciled factual tracker-write actions")
    if any(effect.get("kind") != "tracker-write" for effect in record["effects"].values()):
        errors.append("resolved-no-change permits only factual tracker-write effect receipts")
    if not current_terminal_claim(record, NO_CHANGE_TERMINAL, current, record_path):
        errors.append("no fresh resolved-no-change terminal claim exists")
    terminal_audit = record["obligations"].get("terminal-audit", {})
    if terminal_audit.get("status") != "satisfied" or not any_fresh_evidence(
        record, terminal_audit.get("evidence", []), current, "G8", record_path
    ):
        errors.append("terminal-audit lacks fresh passing evidence")
    for trigger_id, trigger in record["triggers"].items():
        if trigger.get("decision") != "yes":
            continue
        obligation = record["obligations"].get(trigger.get("obligation"), {})
        if obligation.get("status") != "satisfied" or not any_fresh_evidence(
            record,
            obligation.get("evidence", []),
            current,
            obligation.get("gate"),
            record_path,
        ):
            errors.append(f"trigger {trigger_id} lacks fresh no-change disposition evidence")
    for finding_id, finding in record["findings"].items():
        if finding.get("disposition") is None or not any_fresh_evidence(
            record, finding.get("evidence", []), current, record_path=record_path
        ):
            errors.append(f"finding {finding_id} is unresolved or stale")
        elif finding.get("disposition") == "accepted-residual" and not capability_grants_target(
            record,
            str(finding.get("waiver_capability") or ""),
            "accept-residual-risk",
            control_target_digest("finding", finding_id),
        ):
            errors.append(f"finding {finding_id} residual-risk acceptance is no longer authorized")
    return errors


def interruption_finish_errors(
    record: dict[str, Any],
    status: str,
    blocked_obligations: list[str],
    repo: Path,
    record_path: Path | None = None,
) -> list[str]:
    current = git_fingerprint(repo)
    result = evaluate(record, repo, record_path)
    errors: list[str] = []
    unknown_triggers = [
        trigger_id
        for trigger_id, trigger in record["triggers"].items()
        if trigger.get("decision") not in {"yes", "no"} or not trigger.get("rationale")
    ]
    if unknown_triggers:
        errors.append(f"triggers remain unknown: {', '.join(sorted(unknown_triggers))}")
    if result["current_gate"] is None:
        errors.append("no gate is unresolved")
        earliest_reason_digests: list[str] = []
    else:
        earliest = next(item for item in result["gates"] if item["gate"] == result["current_gate"])
        earliest_reason_digests = sorted(earliest["reason_digests"])
    if not blocked_obligations:
        errors.append("no --blocked-obligation was supplied")
    for obligation_id in blocked_obligations:
        obligation = record["obligations"].get(obligation_id)
        if obligation is None:
            errors.append(f"blocked obligation {obligation_id} does not exist")
            continue
        if obligation.get("gate") != result["current_gate"]:
            errors.append(f"blocked obligation {obligation_id} is not at the earliest failing gate")
        if obligation.get("status") != "blocked" or not obligation.get("rationale"):
            errors.append(f"obligation {obligation_id} is not explicitly blocked")
        if not any(
            record["evidence"].get(evidence_id, {}).get("kind") == "blocker"
            and fresh_evidence_reason(record, evidence_id, current, record_path) is None
            for evidence_id in obligation.get("evidence", [])
        ):
            errors.append(f"blocked obligation {obligation_id} lacks fresh evidence")
    unsettled = sorted(
        action_id
        for action_id, action in record["actions"].items()
        if action.get("status") not in TERMINAL_ACTION_STATES
    )
    open_material = sorted(
        finding_id
        for finding_id, finding in record["findings"].items()
        if finding.get("severity") in {"blocker", "major"} and finding.get("disposition") is None
    )
    finish_args = record.get("_finish_args", {})
    listed_actions = sorted(set(finish_args.get("unresolved_actions", [])))
    listed_findings = sorted(set(finish_args.get("open_findings", [])))
    listed_reasons = sorted(set(finish_args.get("reason_digests", [])))
    if listed_reasons != earliest_reason_digests:
        errors.append("finish must enumerate exactly every reason at the earliest failing gate")
    evidenced_reasons = sorted(
        {
            reason_digest
            for obligation_id in blocked_obligations
            for evidence_id in record["obligations"].get(obligation_id, {}).get("evidence", [])
            if record["evidence"].get(evidence_id, {}).get("kind") == "blocker"
            and fresh_evidence_reason(record, evidence_id, current, record_path) is None
            for reason_digest in record["evidence"][evidence_id].get("reason_digests", [])
        }
    )
    if evidenced_reasons != earliest_reason_digests:
        errors.append("blocker evidence must map exactly every reason at the earliest failing gate")
    if unsettled != listed_actions or open_material != listed_findings:
        errors.append(
            f"{status} must enumerate exactly every unresolved action and open material finding"
        )
    if status == "blocked":
        eligible_units = eligible_work_units(record)
        if eligible_units:
            errors.append(
                "blocked cannot finish while eligible work units remain: "
                + ", ".join(eligible_units)
            )
        safe_independent = {
            obligation_id
            for obligation_id, obligation in record["obligations"].items()
            if obligation.get("required", True)
            and obligation.get("gate") == result["current_gate"]
            and obligation.get("status") not in {"satisfied", "waived"}
            and (
                not obligation.get("condition_trigger")
                or record["triggers"].get(obligation["condition_trigger"], {}).get("decision") == "yes"
            )
        }
        if set(blocked_obligations) != safe_independent:
            errors.append("blocked must enumerate every applicable required obligation at the earliest failing gate")
    return errors


def cmd_finish(args: argparse.Namespace) -> None:
    rationale = safe_text(args.rationale, "rationale")
    repo = Path(args.repo).resolve()
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        if not terminal_matches_endpoint(args.status, str(record["run"].get("requested_endpoint"))):
            raise TicketCtlError(
                f"terminal status {args.status} is incompatible with frozen requested endpoint {record['run'].get('requested_endpoint')}"
            )
        existing = record.get("terminal")
        if existing:
            raise TicketCtlError("record is already terminal; use show to revalidate or reopen before a new finish")
        result = evaluate(record, repo, store.path)
        record["_finish_args"] = {
            "unresolved_actions": list(args.unresolved_action or []),
            "open_findings": list(args.open_finding or []),
            "reason_digests": [require_digest(item, "reason") for item in (args.reason_digest or [])],
        }
        blocked_obligations = sorted(set(args.blocked_obligation or []))
        if args.status in POSITIVE_TERMINALS:
            errors = positive_finish_errors(record, args.status, repo, store.path)
            if errors:
                raise TicketCtlError("unsafe terminal claim: " + "; ".join(errors))
        elif args.status == NO_CHANGE_TERMINAL:
            errors = resolved_no_change_errors(record, repo, store.path)
            if errors:
                raise TicketCtlError("unsafe resolved-no-change claim: " + "; ".join(errors))
        else:
            if not args.next_action or not args.needed_evidence:
                raise TicketCtlError(f"{args.status} requires --next-action and --needed-evidence")
            errors = interruption_finish_errors(
                record, args.status, blocked_obligations, repo, store.path
            )
            if errors:
                raise TicketCtlError(f"unsafe {args.status} claim: " + "; ".join(errors))
        record.pop("_finish_args", None)
        fingerprint = git_fingerprint(repo)
        unresolved_actions = sorted(
            action_id
            for action_id, action in record["actions"].items()
            if action.get("status") not in TERMINAL_ACTION_STATES
        )
        terminal = {
            "status": args.status,
            "rationale": rationale,
            "gate": result["current_gate"],
            "fingerprint": fingerprint["digest"],
            "intent_fingerprint": fingerprint["intent_digest"],
            "head_fingerprint": fingerprint["head_digest"],
            "unresolved_actions": unresolved_actions,
            "open_findings": sorted(set(args.open_finding or [])),
            "next_action": safe_text(args.next_action, "next action") if args.next_action else None,
            "needed_evidence": safe_text(args.needed_evidence, "needed evidence") if args.needed_evidence else None,
            "blocked_obligations": blocked_obligations,
            "reason_digests": sorted(set(args.reason_digest or [])),
            "recorded_at": utc_now(),
        }
        record["terminal"] = terminal
        commit_mutation(store, record, args, "finish", {"status": args.status, "gate": result["current_gate"]})
    output(terminal)


def cmd_reopen(args: argparse.Namespace) -> None:
    rationale = safe_text(args.rationale, "rationale")
    store = bound_record_store(args)
    with store.lock():
        record = store.load()
        if record.get("terminal") is None:
            raise TicketCtlError("record is not terminal")
        prior_status = record["terminal"]["status"]
        record["terminal"] = None
        for capability in record["capabilities"].values():
            capability.update(
                {"authority": "unknown", "basis": None, "rationale": "Capability requires reconciliation after reopen"}
            )
        for action in record["actions"].values():
            if action.get("status") not in TERMINAL_ACTION_STATES:
                action.update(
                    {"armed_at": None, "arm_expires_at": None, "armed_lease_epoch": None, "armed_authority_revision": None}
                )
        at = utc_now()
        invalidated: list[str] = []
        for evidence_id, evidence in record["evidence"].items():
            if evidence.get("invalidated") is None:
                evidence["invalidated"] = {"event": "external-feedback", "rationale": rationale, "at": at}
                invalidated.append(evidence_id)
        record["invalidations"].append(
            {"event": "external-feedback", "rationale": rationale, "at": at, "evidence": sorted(invalidated)}
        )
        commit_mutation(store, record, args, "reopen", {"prior_status": prior_status, "rationale": rationale})
    output({"reopened": True, "prior_status": prior_status})


def add_digest_arguments(parser: argparse.ArgumentParser, name: str) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(f"--{name}-digest")
    group.add_argument(f"--{name}-file")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain a sanitized, evidence-gated solve-ticket control record."
    )
    parser.add_argument("--repo", default=".", help="Git worktree used for location and fingerprints")
    parser.add_argument("--ticket", help="Ticket locator; hashed for lookup and never stored")
    parser.add_argument("--record", help="Explicit record.json path instead of the Git-common-dir default")
    parser.add_argument("--lease-token", help="Coordinator lease token (prefer --lease-token-file)")
    parser.add_argument("--lease-token-file", help="File containing the coordinator lease token")
    parser.add_argument("--lease-epoch", type=int, help="Monotonic coordinator lease epoch")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Create a control record")
    init.add_argument("--authority-envelope", required=True)
    init.set_defaults(handler=cmd_init)
    locate = commands.add_parser("locate", help="Print the deterministic record path")
    locate.set_defaults(handler=cmd_locate)
    show = commands.add_parser("show", help="Print the record and derived gate evaluation")
    show.set_defaults(handler=cmd_show)
    fingerprint = commands.add_parser("fingerprint", help="Hash the current Git tree without storing its content")
    fingerprint.set_defaults(handler=cmd_fingerprint)
    hash_command = commands.add_parser("hash", help="SHA-256 hash a file or stdin without recording its content")
    hash_sources = hash_command.add_mutually_exclusive_group(required=True)
    hash_sources.add_argument("--file")
    hash_sources.add_argument("--stdin", action="store_true")
    hash_command.set_defaults(handler=cmd_hash)
    target = commands.add_parser(
        "target", help="Derive stable content-addressed targets before external objects exist"
    )
    target_commands = target.add_subparsers(dest="target_command", required=True)
    pr_slot = target_commands.add_parser(
        "derive-pr-slot",
        help="Derive the immutable PR origin-slot digest before a provider assigns a PR number",
        description=(
            "Hash the canonical v1 provider/repository/ref/work-unit origin tuple. Retain the digest "
            "as work-unit coordinates.pr for the PR lifecycle; verify the assigned PR URL or number "
            "separately in evidence and receipts."
        ),
    )
    pr_slot.add_argument("--provider", required=True, help="Sanitized provider identifier")
    pr_slot.add_argument("--target-repo", required=True, help="Sanitized target repository identifier")
    pr_slot.add_argument("--target-ref", required=True, help="Sanitized target/base ref")
    pr_slot.add_argument("--head-repo", required=True, help="Sanitized head repository identifier")
    pr_slot.add_argument("--head-ref", required=True, help="Sanitized head ref")
    pr_slot.add_argument("--work-unit", required=True, help="Controller work-unit ID")
    pr_slot.set_defaults(handler=cmd_target_derive_pr_slot)
    remote_ref = target_commands.add_parser(
        "derive-remote-ref",
        help="Derive a stable remote-ref target from provider/repository/ref/work-unit coordinates",
    )
    remote_ref.add_argument("--provider", required=True, help="Sanitized provider identifier")
    remote_ref.add_argument("--repository", required=True, help="Sanitized repository identifier")
    remote_ref.add_argument("--ref", required=True, help="Sanitized fully qualified remote ref")
    remote_ref.add_argument("--work-unit", required=True, help="Controller work-unit ID")
    remote_ref.set_defaults(handler=cmd_target_derive_remote_ref)
    gate = commands.add_parser("gate", help="Evaluate G0-G8 and report the earliest failing gate")
    gate.set_defaults(handler=cmd_gate)
    next_command = commands.add_parser("next", help="Print the reasons at the earliest failing gate")
    next_command.set_defaults(handler=cmd_next)

    lease = commands.add_parser("lease", help="Coordinate the single durable writer")
    lease_commands = lease.add_subparsers(dest="lease_command", required=True)
    lease_acquire = lease_commands.add_parser("acquire")
    lease_acquire.add_argument("--owner-digest", required=True)
    lease_acquire.add_argument("--ttl", type=int, default=900)
    lease_acquire.set_defaults(handler=cmd_lease_acquire)
    lease_renew = lease_commands.add_parser("renew")
    lease_renew.add_argument("--ttl", type=int, default=900)
    lease_renew.set_defaults(handler=cmd_lease_renew)
    lease_release = lease_commands.add_parser("release")
    lease_release.set_defaults(handler=cmd_lease_release)
    lease_takeover = lease_commands.add_parser("takeover")
    lease_takeover.add_argument("--owner-digest", required=True)
    lease_takeover.add_argument("--expected-epoch", required=True, type=int)
    lease_takeover.add_argument("--expected-journal-head", required=True)
    lease_takeover.add_argument("--reconciliation-digest", required=True)
    lease_takeover.add_argument("--ttl", type=int, default=900)
    lease_takeover.set_defaults(handler=cmd_lease_takeover)

    authority = commands.add_parser("authority", help="Generate or amend a typed authority envelope")
    authority_commands = authority.add_subparsers(dest="authority_command", required=True)
    authority_scaffold = authority_commands.add_parser(
        "scaffold", help="Exclusively create a mode-0600 root authority envelope"
    )
    authority_scaffold.add_argument("--preset", required=True, choices=("local", "merge-ready-pr"))
    authority_scaffold.add_argument("--trusted-request-file", required=True)
    authority_scaffold.add_argument(
        "--remote-target-digest",
        action="append",
        help="Derived remote-ref digest; repeat once per work unit",
    )
    authority_scaffold.add_argument(
        "--pr-target-digest",
        action="append",
        help="Derived PR-slot digest; repeat in matching work-unit order",
    )
    authority_scaffold.add_argument(
        "--max-actions",
        type=int,
        help="Bounded action forecast; merge-ready-pr requires at least two per target pair",
    )
    authority_scaffold.add_argument("--output", required=True)
    authority_scaffold.set_defaults(handler=cmd_authority_scaffold)
    authority_amend = authority_commands.add_parser("amend")
    authority_amend.add_argument("--authority-envelope", required=True)
    authority_amend.set_defaults(handler=cmd_authority_amend)

    artifact = commands.add_parser("artifact", help="Register a content-addressed recoverable sidecar")
    artifact_commands = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_add = artifact_commands.add_parser("add")
    artifact_add.add_argument("id")
    artifact_add.add_argument(
        "--kind",
        required=True,
        choices=("capability-envelope", "work-graph", "host-registry", "monitor", "raw-evidence", "other"),
    )
    artifact_add.add_argument("--locator", required=True)
    add_digest_arguments(artifact_add, "content")
    artifact_add.add_argument("--depends-on", action="append")
    artifact_add.set_defaults(handler=cmd_artifact_add)

    context = commands.add_parser("context", help="Record hashed source context")
    context_commands = context.add_subparsers(dest="context_command", required=True)
    context_add = context_commands.add_parser("add")
    context_add.add_argument("id")
    context_add.add_argument(
        "--kind",
        required=True,
        choices=(
            "ticket",
            "repository-instructions",
            "starting-state",
            "design",
            "review",
            "delivery",
        ),
    )
    add_digest_arguments(context_add, "content")
    context_add.add_argument("--summary")
    context_add.set_defaults(handler=cmd_context_add)

    capability = commands.add_parser("capability", help="Record availability and explicit authority")
    capability_commands = capability.add_subparsers(dest="capability_command", required=True)
    capability_set = capability_commands.add_parser("set")
    capability_set.add_argument("id")
    capability_set.add_argument("--available", required=True, choices=("yes", "no", "unknown"))
    capability_set.add_argument("--authority", required=True, choices=("granted", "denied", "unknown"))
    capability_set.add_argument("--basis")
    capability_set.add_argument(
        "--covers", action="append", choices=tuple(sorted(load_template()["policy"]["authority_scopes"]))
    )
    capability_set.add_argument("--action-kind", action="append", choices=tuple(sorted(ACTION_KINDS)))
    capability_set.add_argument("--effect", action="append", choices=tuple(sorted(ACTION_EFFECTS)))
    capability_set.add_argument("--target-digest", action="append")
    capability_set.add_argument("--max-uses", type=int, default=0)
    capability_set.add_argument("--expires-at")
    capability_set.add_argument("--delegable", action="store_true")
    capability_set.add_argument("--required", action="store_true")
    capability_set.add_argument("--rationale", required=True)
    capability_set.set_defaults(handler=cmd_capability_set)

    trigger = commands.add_parser("trigger", help="Resolve a known risk trigger")
    trigger_commands = trigger.add_subparsers(dest="trigger_command", required=True)
    trigger_set = trigger_commands.add_parser("set")
    trigger_set.add_argument("id")
    trigger_set.add_argument("--decision", required=True, choices=("yes", "no"))
    trigger_set.add_argument("--rationale", required=True)
    trigger_set.set_defaults(handler=cmd_trigger_set)

    claim = commands.add_parser("claim", help="Record an acceptance, risk, or terminal claim")
    claim_commands = claim.add_subparsers(dest="claim_command", required=True)
    claim_add = claim_commands.add_parser("add")
    claim_add.add_argument("id")
    claim_add.add_argument("--gate", required=True, choices=GATES)
    claim_add.add_argument("--kind", required=True, choices=("acceptance", "risk", "terminal"))
    claim_add.add_argument("--criticality", default="material", choices=("routine", "material", "critical"))
    claim_add.add_argument("--summary", required=True)
    claim_add.add_argument("--optional", action="store_true")
    claim_add.add_argument("--terminal-outcome", choices=tuple(sorted(SUCCESS_TERMINALS)))
    claim_add.set_defaults(handler=cmd_claim_add)

    obligation = commands.add_parser("obligation", help="Add or resolve a gate obligation")
    obligation_commands = obligation.add_subparsers(dest="obligation_command", required=True)
    obligation_add = obligation_commands.add_parser("add")
    obligation_add.add_argument("id")
    obligation_add.add_argument("--gate", required=True, choices=GATES)
    obligation_add.add_argument("--kind", required=True)
    obligation_add.add_argument("--summary", required=True)
    obligation_add.add_argument("--optional", action="store_true")
    obligation_add.add_argument("--waivable", action="store_true")
    obligation_add.set_defaults(handler=cmd_obligation_add)
    obligation_resolve = obligation_commands.add_parser("resolve")
    obligation_resolve.add_argument("id")
    obligation_resolve.add_argument("--status", required=True, choices=("open", "satisfied", "waived", "blocked"))
    obligation_resolve.add_argument("--evidence", action="append")
    obligation_resolve.add_argument("--rationale")
    obligation_resolve.add_argument("--waiver-capability")
    obligation_resolve.set_defaults(handler=cmd_obligation_resolve)

    checkpoint = commands.add_parser("checkpoint", help="Bind evidence to the current Git fingerprint")
    checkpoint_commands = checkpoint.add_subparsers(dest="checkpoint_command", required=True)
    checkpoint_create = checkpoint_commands.add_parser("create")
    checkpoint_create.add_argument("id")
    checkpoint_create.add_argument("--summary")
    for dimension_name in ("base", "config", "build", "environment", "external"):
        checkpoint_create.add_argument(f"--{dimension_name}-digest", required=True)
    checkpoint_create.set_defaults(handler=cmd_checkpoint_create)

    evidence = commands.add_parser("evidence", help="Record hashed proof tied to a checkpoint")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_add = evidence_commands.add_parser("add")
    evidence_add.add_argument("id")
    evidence_add.add_argument("--kind", required=True, choices=tuple(sorted(EVIDENCE_KINDS)))
    evidence_add.add_argument("--result", required=True, choices=("pass", "fail", "gap"))
    evidence_add.add_argument("--checkpoint", required=True)
    add_digest_arguments(evidence_add, "artifact")
    evidence_add.add_argument("--claim", action="append")
    evidence_add.add_argument("--obligation", action="append")
    evidence_add.add_argument("--artifact-ref", action="append")
    evidence_add.add_argument("--reason-digest", action="append")
    evidence_add.add_argument("--invalidate-on", action="append", choices=tuple(sorted(INVALIDATION_EVENTS)))
    evidence_add.add_argument("--depends-on", action="append", choices=tuple(sorted(CHECKPOINT_DIMENSIONS)))
    evidence_add.add_argument("--review-lens", action="append", choices=tuple(sorted(REVIEW_LENSES)))
    evidence_add.add_argument("--reviewer-digest")
    evidence_add.add_argument("--review-input-digest")
    evidence_add.add_argument("--lanes", choices=("complete", "pending", "failed", "missing"))
    evidence_add.add_argument("--feedback", choices=("none", "actionable", "undecided"))
    evidence_add.add_argument("--automated-review", choices=("complete", "pending", "failed", "missing"))
    evidence_add.add_argument("--human-approval", choices=("approved", "pending", "not-required"))
    evidence_add.add_argument("--draft", choices=("yes", "no"))
    evidence_add.add_argument("--mergeable", choices=("yes", "no", "unknown"))
    evidence_add.add_argument("--pending", action="append", choices=("human-approval", "merge"))
    evidence_add.add_argument("--pending-human-digest")
    evidence_add.add_argument("--work-unit")
    evidence_add.add_argument("--revision-digest")
    evidence_add.add_argument("--target-digest")
    evidence_add.add_argument("--static-oracle-digest")
    evidence_add.add_argument("--surface-digest")
    evidence_add.add_argument("--oracle-actor-digest")
    evidence_add.set_defaults(handler=cmd_evidence_add)

    invalidate = commands.add_parser("invalidate", help="Invalidate evidence affected by a recorded event")
    invalidate.add_argument("event", choices=tuple(sorted(INVALIDATION_EVENTS)))
    invalidate.add_argument("--rationale", required=True)
    invalidate.set_defaults(handler=cmd_invalidate)

    finding = commands.add_parser("finding", help="Record and disposition review findings")
    finding_commands = finding.add_subparsers(dest="finding_command", required=True)
    finding_add = finding_commands.add_parser("add")
    finding_add.add_argument("id")
    finding_add.add_argument("--severity", required=True, choices=("blocker", "major", "minor"))
    finding_add.add_argument("--origin", required=True, choices=("introduced", "pre-existing", "unknown"))
    finding_add.add_argument("--summary", required=True)
    finding_add.set_defaults(handler=cmd_finding_add)
    finding_dispose = finding_commands.add_parser("dispose")
    finding_dispose.add_argument("id")
    finding_dispose.add_argument(
        "--disposition", required=True, choices=("fixed", "refuted", "duplicate", "accepted-residual", "follow-up")
    )
    finding_dispose.add_argument("--canonical-finding")
    finding_dispose.add_argument("--waiver-capability")
    finding_dispose.add_argument("--rationale", required=True)
    finding_dispose.add_argument("--evidence", action="append", required=True)
    finding_dispose.set_defaults(handler=cmd_finding_dispose)

    work = commands.add_parser("work", help="Maintain the implementation work-unit DAG")
    work_commands = work.add_subparsers(dest="work_command", required=True)
    work_add = work_commands.add_parser("add")
    work_add.add_argument("id")
    work_add.add_argument("--summary", required=True)
    work_add.add_argument("--optional", action="store_true")
    work_add.add_argument("--depends-on", action="append")
    work_add.add_argument("--claim", action="append")
    work_add.add_argument("--obligation", action="append")
    work_add.set_defaults(handler=cmd_work_add)
    work_set = work_commands.add_parser("set")
    work_set.add_argument("id")
    work_set.add_argument("--status", required=True, choices=("planned", "active", "done", "skipped", "blocked"))
    work_set.add_argument("--evidence", action="append")
    work_set.add_argument("--rationale")
    work_set.add_argument("--depends-on", action="append", default=None)
    work_set.add_argument("--evidence-epoch")
    work_set.set_defaults(handler=cmd_work_set)
    work_coordinate = work_commands.add_parser("coordinate")
    work_coordinate.add_argument("id")
    for coordinate_name in ("branch", "worktree", "base", "head", "remote", "pr"):
        work_coordinate.add_argument(f"--{coordinate_name}-digest")
    work_coordinate.add_argument("--evidence-epoch")
    work_coordinate.set_defaults(handler=cmd_work_coordinate)

    profile = commands.add_parser("profile", help="Apply a bounded setup profile without proving outcomes")
    profile_commands = profile.add_subparsers(dest="profile_command", required=True)
    profile_routine = profile_commands.add_parser(
        "apply-routine",
        help="Atomically record pristine local/static intake context, no-risk triggers, and local authority",
    )
    profile_routine.add_argument("--repository-instructions-digest", required=True)
    profile_routine.add_argument("--starting-state-digest", required=True)
    profile_routine.add_argument("--classification-digest", required=True)
    profile_routine.add_argument("--rationale", required=True)
    profile_routine.set_defaults(handler=cmd_profile_apply_routine)

    action = commands.add_parser("action", help="Prepare and reconcile write-ahead external actions")
    action_commands = action.add_subparsers(dest="action_command", required=True)
    action_scaffold = action_commands.add_parser(
        "scaffold", help="Exclusively create a validated mode-0600 typed action request"
    )
    action_scaffold.add_argument("--kind", required=True, choices=tuple(sorted(ACTION_KINDS)))
    action_scaffold.add_argument(
        "--target-kind", required=True, choices=tuple(sorted(ACTION_TARGET_KINDS))
    )
    action_scaffold.add_argument("--target-digest", required=True)
    action_scaffold.add_argument("--revision-digest", required=True)
    action_scaffold.add_argument("--payload-digest", required=True)
    action_scaffold.add_argument("--work-unit")
    action_scaffold.add_argument("--predecessor-action")
    action_scaffold.add_argument("--output", required=True)
    action_scaffold.set_defaults(handler=cmd_action_scaffold)
    action_prepare = action_commands.add_parser("prepare")
    action_prepare.add_argument("id")
    action_prepare.add_argument("--capability", required=True)
    action_prepare.add_argument("--request-manifest", required=True)
    add_digest_arguments(action_prepare, "expected-state")
    action_prepare.set_defaults(handler=cmd_action_prepare)
    action_arm = action_commands.add_parser("arm")
    action_arm.add_argument("id")
    action_arm.add_argument("--observed-state-digest", required=True)
    action_arm.add_argument("--ttl", type=int, default=120)
    action_arm.set_defaults(handler=cmd_action_arm)
    action_settle = action_commands.add_parser("settle")
    action_settle.add_argument("id")
    action_settle.add_argument(
        "--outcome",
        required=True,
        choices=("succeeded", "uncertain", "verified-applied", "verified-not-applied"),
    )
    add_digest_arguments(action_settle, "receipt")
    action_settle.add_argument("--observed-state-digest")
    action_settle.add_argument("--effect")
    action_settle.set_defaults(handler=cmd_action_settle)

    effect = commands.add_parser("effect", help="Record an immutable externally observed effect")
    effect_commands = effect.add_subparsers(dest="effect_command", required=True)
    effect_observe = effect_commands.add_parser("observe")
    effect_observe.add_argument("id")
    effect_observe.add_argument("--action", required=True)
    effect_observe.add_argument("--actor", required=True, choices=("coordinator", "human", "automation", "external"))
    effect_observe.add_argument("--actor-digest", required=True)
    add_digest_arguments(effect_observe, "receipt")
    effect_observe.set_defaults(handler=cmd_effect_observe)

    finish = commands.add_parser("finish", help="Record a guarded terminal outcome")
    finish.add_argument("--status", required=True, choices=tuple(sorted(TERMINALS)))
    finish.add_argument("--rationale", required=True)
    finish.add_argument("--blocked-obligation", action="append")
    finish.add_argument("--unresolved-action", action="append")
    finish.add_argument("--open-finding", action="append")
    finish.add_argument("--reason-digest", action="append")
    finish.add_argument("--next-action")
    finish.add_argument("--needed-evidence")
    finish.set_defaults(handler=cmd_finish)
    reopen = commands.add_parser("reopen", help="Resume a terminal record after new information")
    reopen.add_argument("--rationale", required=True)
    reopen.set_defaults(handler=cmd_reopen)
    return parser


def main(arguments: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(arguments)
        args.handler(args)
        return 0
    except TicketCtlError as error:
        print(f"ticketctl: {error}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as error:
        print(f"ticketctl: local operation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
