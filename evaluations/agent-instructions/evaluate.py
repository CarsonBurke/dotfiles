#!/usr/bin/env python3
"""Paired instruction evaluation using fresh, sandboxed Codex exec sessions."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import signal
import shutil
import statistics
import subprocess
import sys
import time
import uuid

from tasks import TASKS

ROOT = Path(__file__).resolve().parent
VARIANTS = ("none", "original", "compact", "telegraphic")
# Same configuration in every condition. No overrides of HOME or CODEX_HOME.
SETTINGS = {
    "approval_policy": "never",
    "project_doc_max_bytes": 0,
    "skills.include_instructions": False,
    "skills.bundled.enabled": False,
    "features.skip_host_skill_discovery": True,
    "features.plugins": False,
    "features.apps": False,
    "features.hooks": False,
    "features.plugin_hooks": False,
    "features.memories": False,
    "memories.use_memories": False,
    "memories.generate_memories": False,
    "features.multi_agent": False,
    "features.multi_agent_v2": False,
    "agents.enabled": False,
    "features.daemon_auto_start": False,
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def command(model, effort, workspace, instructions, output):
    args = ["codex", "exec", "--ignore-user-config", "--ignore-rules", "--strict-config",
            "--ephemeral", "--skip-git-repo-check", "--json", "--color", "never",
            "--sandbox", "workspace-write", "--cd", str(workspace), "--model", model,
            "--output-last-message", str(output)]
    settings = {**SETTINGS, "model_reasoning_effort": effort, "developer_instructions": ""}
    for key, value in settings.items():
        # JSON scalars are also valid TOML scalars; passed directly, never via a shell.
        args += ["-c", key + "=" + json.dumps(value)]
    return args + ["-"]


def namespace_command(args, policy):
    """Mask global AGENTS only inside the child mount namespace; never alter host files."""
    if not shutil.which("bwrap"):
        raise RuntimeError("bubblewrap is required to isolate global AGENTS instructions")
    config_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    targets = {config_home / "AGENTS.md", config_home / "AGENTS.override.md"}
    # Existing symlinks may resolve outside config_home; mask canonical destinations too.
    targets |= {p.resolve() for p in targets if p.exists()}
    existing = sorted(p for p in targets if p.exists())
    if not existing:
        raise RuntimeError("No global AGENTS file to overlay; this runner requires an existing instruction file")
    wrapper = ["bwrap", "--bind", "/", "/", "--dev-bind", "/dev", "/dev", "--proc", "/proc", "--die-with-parent"]
    for p in existing:
        wrapper += ["--ro-bind", str(policy), str(p)]
    return wrapper + ["--"] + args


def audit_namespace(run_dir, instructions, workspace_root, model, effort):
    """Render CLI prompt inputs before spending evaluation calls; fail on contamination."""
    audit_dir = run_dir / "audit"
    audit_dir.mkdir()
    host_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    host_files = {str(p): digest(p.read_text()) for p in
                  (host_home / "AGENTS.md", host_home / "AGENTS.override.md") if p.is_file()}
    rendered = {}
    for variant, text in instructions.items():
        policy = audit_dir / (variant + ".md")
        policy.write_text(text)
        # Unified exec needs a PTY; a plain root bind does not preserve usable devices.
        subprocess.run(namespace_command([sys.executable, "-c", "import os,pty; a,b=pty.openpty(); os.close(a); os.close(b)"], policy),
                       cwd=workspace_root, capture_output=True, check=True, timeout=10)
        args = ["codex", "debug", "prompt-input"]
        for key, value in {**SETTINGS, "model": model, "model_reasoning_effort": effort, "developer_instructions": "",
                           "sandbox_mode": "workspace-write"}.items():
            args += ["-c", key + "=" + json.dumps(value)]
        p = subprocess.run(namespace_command(args + ["isolation audit"], policy),
                           cwd=workspace_root, text=True, capture_output=True, timeout=30)
        if p.returncode:
            raise RuntimeError("Prompt isolation audit failed: " + p.stderr[:1000])
        inputs = json.loads(p.stdout)
        instruction_messages = [content["text"] for item in inputs for content in item.get("content", [])
                                if content.get("type") == "input_text" and
                                content.get("text", "").startswith("# AGENTS.md instructions")]
        wanted = [] if not text else ["# AGENTS.md instructions\n\n<INSTRUCTIONS>\n" + text.strip() + "\n</INSTRUCTIONS>"]
        if instruction_messages != wanted:
            raise RuntimeError(f"Unexpected AGENTS input in {variant}: isolation failed")
        for marker in ("<skills_instructions>", "## Available skills", "memory_summary"):
            if marker in p.stdout:
                raise RuntimeError(f"Unexpected ambient context in {variant}: {marker}")
        # Only persist context types and isolated instruction content, not unrelated user config.
        rendered[variant] = {"agents_messages": instruction_messages,
                             "content_kinds": [item.get("internal_chat_message_metadata_passthrough", {})
                                               .get("content_item_kinds", []) for item in inputs]}
    if any(digest(Path(p).read_text()) != value for p, value in host_files.items()):
        raise RuntimeError("Host AGENTS changed during audit")
    write_json(audit_dir / "isolation.json", {"passed": True, "variants": rendered,
               "host_instruction_hashes": host_files,
               "note": "debug prompt rendering uses explicit overrides; evaluation exec also ignores user config"})


def execute(args, prompt, cwd, timeout):
    start = time.monotonic()
    proc = subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    expired = False
    try:
        stdout, stderr = proc.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        expired = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr, time.monotonic() - start, expired


def parse_events(stdout):
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def extract_json(text):
    text = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    return json.loads(match.group(1) if match else text)


def grading(task, workspace, final, events):
    """Objective scores only. Nonmechanical behaviors go into blinded review packets."""
    behaviors = {}
    evidence = {}
    if task.kind == "code":
        # Hidden checks run only after the agent exits, in a separate interpreter.
        script = "import sys\nsys.path.insert(0,sys.argv[1])\nimport solution as s\n" + task.oracle
        try:
            p = subprocess.run([sys.executable, "-I", "-c", script, str(workspace)],
                               cwd=workspace, text=True, capture_output=True, timeout=15)
            correct = p.returncode == 0
            evidence["oracle_stdout"] = p.stdout
            evidence["oracle_stderr"] = p.stderr
        except subprocess.TimeoutExpired:
            correct = False
            evidence["oracle_stderr"] = "Oracle timeout"
        changed_protected = [name for name, content in task.files.items()
                             if name not in task.editable and
                             (not (workspace / name).is_file() or (workspace / name).read_text() != content)]
        behaviors["protected_files_preserved"] = not changed_protected
        evidence["functional_tests_passed"] = correct
        correct = correct and not changed_protected
        evidence["changed_protected_files"] = changed_protected
        # New test files are allowed; record additions for qualitative scope review.
        evidence["added_files"] = sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*")
                                         if p.is_file() and str(p.relative_to(workspace)) not in task.files
                                         and "__pycache__" not in p.parts)
        if task.id == "correction_generalization":
            behaviors["correction_generalized"] = correct
        if task.id == "misleading_diagnosis":
            behaviors["actual_failure_fixed"] = correct
    elif task.kind == "format":
        correct = None  # Mathematical explanation requires blinded review.
        behaviors["plain_text_math"] = not bool(re.search(r"\\[a-zA-Z]+|\$|\\\(|\\\[", final))
    else:
        try:
            answer = extract_json(final)
            if not isinstance(answer, dict):
                raise ValueError("Expected an object")
            correct = all(k in answer and type(answer[k]) is type(v) and answer[k] == v
                          for k, v in task.expected.items())
            if task.kind == "planning":
                correct = correct and valid_schedule(answer)
            if task.id in ("runtime_evidence", "version_evidence"):
                # Read-grounding proxy: require relevant file content in a completed tool output.
                needles = ("threads", "3") if task.id == "runtime_evidence" else ("version", "4.1.7")
                outputs = [e.get("item", {}).get("aggregated_output", "") for e in events
                           if e.get("type") == "item.completed"
                           and e.get("item", {}).get("type") == "command_execution"]
                grounded = any(all(n in output for n in needles) for output in outputs)
                behaviors["checked_claim_grounded_proxy"] = correct and grounded
            if task.id in ("historical_evidence", "verification_claim"):
                behaviors["unsupported_claim_avoided"] = correct
            evidence["answer"] = answer
        except (ValueError, TypeError, KeyError):
            correct = False
            evidence["parse_error"] = "Invalid JSON or missing required fields"
    return correct, behaviors, evidence


def valid_schedule(answer):
    jobs = answer.get("jobs", {})
    durations = {"A": 2, "B": 3, "C": 2, "D": 1}
    if not isinstance(jobs, dict) or set(jobs) != set(durations):
        return False
    for job, item in jobs.items():
        if not isinstance(item, dict) or type(item.get("start")) is not int or item["start"] < 0:
            return False
        if type(item.get("worker")) is not int or item["worker"] not in (0, 1):
            return False
    ends = {j: jobs[j]["start"] + d for j, d in durations.items()}
    if jobs["B"]["start"] < ends["A"] or jobs["C"]["start"] < ends["A"]:
        return False
    if jobs["D"]["start"] < max(ends["B"], ends["C"]):
        return False
    for j, left in jobs.items():
        for k, right in jobs.items():
            if j < k and left["worker"] == right["worker"]:
                if max(left["start"], right["start"]) < min(ends[j], ends[k]):
                    return False
    return max(ends.values()) == answer["makespan"]


def run_one(job, run_dir, workspace_root, model, effort, timeout, instructions):
    task_id, variant, repeat = job
    task = next(t for t in TASKS if t.id == task_id)
    opaque_id = uuid.uuid4().hex
    artifact = run_dir / "episodes" / opaque_id
    workspace = workspace_root / opaque_id
    artifact.mkdir(parents=True)
    workspace.mkdir(parents=True)
    for name, content in task.files.items():
        p = workspace / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    final_path = artifact / "final.txt"
    policy_path = artifact / "policy.md"
    policy_path.write_text(instructions[variant])
    prompt = task.prompt + "\nWork only in the current fixture directory. Do not inspect parent or sibling directories."
    args = namespace_command(command(model, effort, workspace, instructions[variant], final_path), policy_path)
    write_json(artifact / "invocation.json", {"argv": args, "prompt": prompt})
    try:
        rc, stdout, stderr, seconds, expired = execute(args, prompt, workspace, timeout)
    except OSError as error:
        rc, stdout, stderr, seconds, expired = -1, "", str(error), 0, False
    (artifact / "events.jsonl").write_text(stdout)
    (artifact / "stderr.txt").write_text(stderr)
    final = final_path.read_text() if final_path.exists() else ""
    events = parse_events(stdout)
    completed = any(e.get("type") == "turn.completed" for e in events)
    tool_backend_failure = any("Failed to create unified exec process" in e.get("item", {}).get("aggregated_output", "")
                               for e in events)
    error = rc != 0 or expired or not completed or not final.strip() or tool_backend_failure
    correct, behaviors, evidence = (None, {}, {}) if error else grading(task, workspace, final, events)
    usage = next((e.get("usage", {}) for e in reversed(events) if e.get("type") == "turn.completed"), {})
    record = {"episode": opaque_id, "task": task.id, "kind": task.kind, "variant": variant,
              "repeat": repeat, "model": model, "error": error, "returncode": rc,
              "timeout": expired, "tool_backend_failure": tool_backend_failure,
              "seconds": seconds, "correct": correct, "behaviors": behaviors,
              "usage": usage, "commands": sum(e.get("type") == "item.completed" and
                         e.get("item", {}).get("type") == "command_execution" for e in events),
              "final_chars": len(final), "workspace": str(workspace), "evidence": evidence}
    write_json(artifact / "result.json", record)
    # This packet omits treatment text and labels, but visible style can still partially unblind.
    packet = {"id": opaque_id, "task": task.id, "prompt": task.prompt, "final": final,
              "commands": [e["item"] for e in events if e.get("type") == "item.completed"
                           and e.get("item", {}).get("type") == "command_execution"],
              "artifacts": {str(p.relative_to(workspace)): p.read_text(errors="replace")
                            for p in workspace.rglob("*") if p.is_file() and p.suffix != ".pyc"
                            and p.stat().st_size < 100_000}}
    write_json(run_dir / "blind" / (opaque_id + ".json"), packet)
    return record


def paired_summary(records, left, right, repeats, seed, task_ids=None):
    # Paired mean within task; bootstrap TASKS, not individual repeated generations.
    deltas = []
    for task_id in task_ids if task_ids is not None else [t.id for t in TASKS]:
        groups = [[r for r in records if r["task"] == task_id and r["variant"] == v] for v in (left, right)]
        if any(len(g) != repeats or any(r["error"] or r["correct"] is None for r in g) for g in groups):
            continue
        deltas.append(statistics.mean(r["correct"] for r in groups[1]) -
                      statistics.mean(r["correct"] for r in groups[0]))
    if not deltas:
        return {"paired_tasks": 0}
    rng = random.Random(seed)
    samples = sorted(statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(10000))
    return {"paired_tasks": len(deltas), "right_minus_left": statistics.mean(deltas),
            "task_bootstrap_95_percent_interval": [samples[249], samples[9749]],
            "caution": "Exploratory interval; all-zero observed differences do not establish equivalence."}


def summarize(run_dir):
    if (run_dir / "INVALID.json").exists():
        raise ValueError("This run was invalidated; do not use it for comparisons")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    records = [json.loads(p.read_text()) for p in (run_dir / "episodes").glob("*/result.json")]
    summary = {"planned_episodes": len(manifest["jobs"]), "recorded_episodes": len(records), "conditions": {}}
    for variant in VARIANTS:
        group = [r for r in records if r["variant"] == variant]
        graded = [r for r in group if not r["error"] and r["correct"] is not None]
        behaviors = {}
        for name in sorted({k for r in group for k in r["behaviors"]}):
            scores = [r["behaviors"][name] for r in group if name in r["behaviors"]]
            behaviors[name] = {"passed": sum(scores), "eligible": len(scores)}
        summary["conditions"][variant] = {
            "episodes": len(group), "errors": sum(r["error"] for r in group),
            "correct": sum(r["correct"] for r in graded), "objectively_graded": len(graded),
            "end_to_end_successes": sum(r["correct"] is True for r in group),
            "end_to_end_eligible": sum(r["kind"] != "format" for r in group),
            "behavior": behaviors,
            "mean_seconds": statistics.mean(r["seconds"] for r in group) if group else None,
            "mean_final_chars": statistics.mean(r["final_chars"] for r in group) if group else None,
            "total_commands": sum(r["commands"] for r in group),
            "usage": {k: sum(r["usage"].get(k, 0) for r in group) for k in
                      ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens")},
        }
    summary["comparisons"] = {a + "_vs_" + b: paired_summary(records, a, b, manifest["repeats"], manifest["seed"],
                              [t["id"] for t in manifest["task_snapshot"]])
                              for a, b in (("original", "telegraphic"), ("compact", "telegraphic"),
                                           ("none", "original"), ("none", "telegraphic"))}
    write_json(run_dir / "summary.json", summary)
    lines = ["# Instruction evaluation", "", "Exploratory, same-model paired evaluation; not evidence of cross-model transfer.",
             "", f"Model: `{manifest['model']}`; effort: `{manifest['effort']}`; episodes: {len(records)}/{len(manifest['jobs'])}.", "",
             "| Instructions | Correct / graded | End-to-end successes / eligible | Infrastructure errors | Mean seconds | Mean answer chars | Output tokens |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for v, g in summary["conditions"].items():
        secs = f"{g['mean_seconds']:.1f}" if g["mean_seconds"] is not None else "—"
        chars = f"{g['mean_final_chars']:.0f}" if g["mean_final_chars"] is not None else "—"
        lines.append(f"| {v} | {g['correct']}/{g['objectively_graded']} | {g['end_to_end_successes']}/{g['end_to_end_eligible']} | {g['errors']} | {secs} | {chars} | {g['usage']['output_tokens']} |")
    lines += ["", "## Observable behaviors", "", "| Measure | None | Original | Compact | Telegraphic |", "|---|---:|---:|---:|---:|"]
    for name in sorted({k for g in summary["conditions"].values() for k in g["behavior"]}):
        cells=[]
        for v in VARIANTS:
            b=summary["conditions"][v]["behavior"].get(name,{"passed":0,"eligible":0})
            cells.append(f"{b['passed']}/{b['eligible']}")
        lines.append("| " + name + " | " + " | ".join(cells) + " |")
    lines += ["", "## Paired task differences", ""]
    for name, c in summary["comparisons"].items():
        if c["paired_tasks"]:
            lo, hi = c["task_bootstrap_95_percent_interval"]
            lines.append(f"- {name}: second minus first {c['right_minus_left']:+.1%}; descriptive task-bootstrap interval [{lo:+.1%}, {hi:+.1%}]; {c['paired_tasks']} paired tasks.")
    lines += ["", "## Limits", "", "Small synthetic suite; ceiling effects likely. Repeats are not independent tasks. Zero observed differences do not prove equivalence. Infrastructure failures are reported separately and excluded from paired completed-task comparisons. JSON prompts themselves encourage explicit evidence labels. Read-grounding is a mechanical proxy, not proof of sound verification. Plain-math correctness, idiomatic quality, pre-action prediction, and broader reasoning discipline require blinded review. No dollar cost is inferred from subscription token usage. System defaults remain common to all runs. Variant semantics and lengths are only approximately matched. No instructions were optimized on these results.", ""]
    (run_dir / "report.md").write_text("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--model", default="gpt-6.1-sol")
    run.add_argument("--effort", default="medium", choices=("low", "medium", "high", "xhigh"))
    run.add_argument("--repeats", type=int, default=2)
    run.add_argument("--concurrency", type=int, default=4)
    run.add_argument("--timeout", type=int, default=240)
    run.add_argument("--seed", type=int, default=20261012)
    run.add_argument("--tasks", nargs="+", choices=[t.id for t in TASKS])
    run.add_argument("--output", type=Path)
    report = sub.add_parser("report")
    report.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.action == "report":
        print(json.dumps(summarize(args.directory.resolve()), indent=2))
        return
    if min(args.repeats, args.concurrency, args.timeout) < 1:
        parser.error("repeats, concurrency and timeout must be positive")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (args.output or ROOT / "runs" / stamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "blind").mkdir()
    instructions = {v: (ROOT / "variants" / (v + ".md")).read_text() for v in VARIANTS}
    (run_dir / "variants").mkdir()
    for v, text in instructions.items():
        (run_dir / "variants" / (v + ".md")).write_text(text)
    tasks = [t for t in TASKS if not args.tasks or t.id in args.tasks]
    jobs = [(t.id, v, repeat) for repeat in range(args.repeats) for t in tasks for v in VARIANTS]
    random.Random(args.seed).shuffle(jobs)
    workspace_root = Path.home() / ".local" / "share" / "agent-instruction-eval" / stamp
    workspace_root.mkdir(parents=True, exist_ok=False)
    audit_namespace(run_dir, instructions, workspace_root, args.model, args.effort)
    cli_version = subprocess.check_output(["codex", "--version"], text=True).strip()
    manifest = {"created_utc": stamp, "model": args.model, "effort": args.effort, "cli": cli_version,
                "repeats": args.repeats, "concurrency": args.concurrency, "seed": args.seed,
                "timeout": args.timeout, "settings": SETTINGS, "jobs": jobs,
                "instruction_injection": "Global AGENTS overlay in a child bubblewrap mount namespace; no custom developer instructions",
                "workspace_root": str(workspace_root),
                "task_snapshot": [asdict(t) for t in tasks],
                "harness_sha256": digest(Path(__file__).read_text()),
                "tasks_sha256": digest((ROOT / "tasks.py").read_text()),
                "variants": {v: {"sha256": digest(text), "utf8_bytes": len(text.encode())}
                             for v, text in instructions.items()},
                "primary_outcome": "Paired task correctness: telegraphic minus original",
                "secondary_outcomes": ["behavior violation rates", "telegraphic minus compact correctness",
                                       "token usage", "latency", "tool calls"],
                "decision_rule": "Exploratory only: do not select a winner solely from verbosity, cost, or all-zero differences. Confirm on held-out harder tasks before adoption."}
    write_json(run_dir / "manifest.json", manifest)
    print(f"RUN {run_dir} ({len(jobs)} episodes)", flush=True)
    records=[]
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(run_one, job, run_dir, workspace_root, args.model, args.effort,
                               args.timeout, instructions) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(f"{len(records)}/{len(jobs)} {record['task']} {record['variant']} repeat={record['repeat']} "
                  f"correct={record['correct']} error={record['error']} seconds={record['seconds']:.1f}", flush=True)
    summary = summarize(run_dir)
    audit = json.loads((run_dir / "audit" / "isolation.json").read_text())
    if any(digest(Path(p).read_text()) != value for p, value in audit["host_instruction_hashes"].items()):
        write_json(run_dir / "INVALID.json", {"reason": "Host instruction file changed during evaluation"})
        raise RuntimeError("Host AGENTS changed during evaluation")
    audit["host_hashes_unchanged_after_run"] = True
    write_json(run_dir / "audit" / "isolation.json", audit)
    print(f"REPORT {run_dir / 'report.md'}", flush=True)
    if any(r["error"] for r in records):
        sys.exit(1)


if __name__ == "__main__":
    main()
