#!/usr/bin/env python3
"""Export an auditable pilot summary after every planned episode finishes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import statistics

from evaluate import summarize

VARIANTS = ("none", "original", "compact", "telegraphic")


def paired_cost(records, metric, seed):
    differences = []
    for task in sorted({r["task"] for r in records}):
        groups = [[r for r in records if r["task"] == task and r["variant"] == v]
                  for v in ("original", "telegraphic")]
        if any(not group or any(r["error"] for r in group) for group in groups):
            continue
        def value(record):
            return record["usage"].get(metric, 0) if metric.endswith("tokens") else record[metric]
        differences.append(statistics.mean(map(value, groups[1])) - statistics.mean(map(value, groups[0])))
    if not differences:
        return None
    rng = random.Random(seed)
    samples = sorted(statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(10000))
    return {"telegraphic_minus_original_mean": statistics.mean(differences),
            "task_bootstrap_interval": [samples[249], samples[9749]], "tasks": len(differences)}


def export(run_dir, output):
    if (run_dir / "INVALID.json").exists():
        raise ValueError("Invalidated run")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    audit = json.loads((run_dir / "audit" / "isolation.json").read_text())
    records = [json.loads(p.read_text()) for p in (run_dir / "episodes").glob("*/result.json")]
    actual = {(r["task"], r["variant"], r["repeat"]) for r in records}
    planned = {tuple(job) for job in manifest["jobs"]}
    if actual != planned or len(records) != len(planned):
        raise ValueError("Run is incomplete or contains duplicate episodes")
    if not audit.get("host_hashes_unchanged_after_run"):
        raise ValueError("Missing final host-file check")
    # Regenerate only after verifying completeness; do not trust a stale mid-run summary.
    summary = summarize(run_dir)
    by_kind = {}
    for variant in VARIANTS:
        by_kind[variant] = {}
        for kind in ("code", "math", "planning", "evidence"):
            group = [r for r in records if r["variant"] == variant and r["kind"] == kind]
            by_kind[variant][kind] = {"correct": sum(r["correct"] is True for r in group), "episodes": len(group)}
    costs = {metric: paired_cost(records, metric, manifest["seed"]) for metric in
             ("output_tokens", "final_chars", "commands", "seconds")}
    output.mkdir(parents=True, exist_ok=True)
    artifact = {"exported_utc": datetime.now(timezone.utc).isoformat(),
                "model": manifest["model"], "effort": manifest["effort"],
                "repeats": manifest["repeats"], "tasks": len(manifest["task_snapshot"]),
                "episodes": len(records), "source_run": str(run_dir),
                "hashes": {"harness":manifest["harness_sha256"],"tasks":manifest["tasks_sha256"],
                           "variants":manifest["variants"]},
                "summary": summary, "by_kind": by_kind, "paired_costs": costs,
                "isolation_audit_passed": audit["passed"],
                "host_instruction_hashes_unchanged": audit["host_hashes_unchanged_after_run"]}
    (output / "pilot-results.json").write_text(json.dumps(artifact, indent=2) + "\n")
    lines = ["# AGENTS instruction pilot", "", f"{manifest['model']}, {manifest['effort']} reasoning effort. "
             f"{len(manifest['task_snapshot'])} tasks × four conditions × {manifest['repeats']} repeats = {len(records)} fresh sessions.",
             "", "This tests observed behavior and performance on this suite. It does not establish optimal conditioning, underlying capability gains, or transfer to Astra.",
             "", "## Task outcomes", "",
             "| Condition | Coding | Math | Scheduling | Evidence schema checks | Plain-text math | Instruction bytes |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for v in VARIANTS:
        cells = [f"{by_kind[v][k]['correct']}/{by_kind[v][k]['episodes']}" for k in ("code", "math", "planning", "evidence")]
        b = summary["conditions"][v]["behavior"].get("plain_text_math", {"passed":0,"eligible":0})
        cells += [f"{b['passed']}/{b['eligible']}",str(manifest["variants"][v]["utf8_bytes"])]
        lines.append("| " + v + " | " + " | ".join(cells) + " |")
    lines += ["", "A repeat is another sample from the same model on the same task, not independent model or task evidence. Behavior denominators cover only relevant opportunities. Code outcomes combine functional tests and preservation of existing protected files; subjective idiomatic quality is not included.",
              "", "## Output and resource use", "",
              "| Condition | Mean final-answer chars | Total output tokens | Total input tokens | Cached input tokens | Mean seconds | Tool commands |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for v in VARIANTS:
        g = summary["conditions"][v]
        lines.append(f"| {v} | {g['mean_final_chars']:.0f} | {g['usage']['output_tokens']} | {g['usage']['input_tokens']} | {g['usage']['cached_input_tokens']} | {g['mean_seconds']:.1f} | {g['total_commands']} |")
    lines += ["", "Token totals include model interaction across tool calls; input totals include repeated context and cache hits. They are not the token count of AGENTS alone. Instruction sizes above are UTF-8 bytes. No dollar cost is inferred from subscription use. Timing includes provider/network variation and the concurrent workload.",
              "", "## Telegraphic minus original", ""]
    c = summary["comparisons"]["original_vs_telegraphic"]
    if c["paired_tasks"]:
        lo, hi = c["task_bootstrap_95_percent_interval"]
        lines.append(f"- Objective task success: {c['right_minus_left']:+.1%}; descriptive task-bootstrap interval [{lo:+.1%}, {hi:+.1%}] across {c['paired_tasks']} task pairs.")
    for metric, item in costs.items():
        if item:
            lo, hi = item["task_bootstrap_interval"]
            lines.append(f"- {metric}: mean paired difference {item['telegraphic_minus_original_mean']:+.1f}; descriptive interval [{lo:+.1f}, {hi:+.1f}].")
    lines += ["", "These are exploratory descriptive intervals, not adjusted hypothesis tests. Task-level bootstrap resampling avoids treating repeated generations as independent tasks. Zero differences throughout a small easy suite produce a degenerate interval; that cannot demonstrate equivalence.",
              "", "## Integrity and limits", "",
              f"- Infrastructure errors: {sum(r['error'] for r in records)}. Both completed-only and end-to-end success counts are retained in `pilot-results.json`.",
              "- Every episode starts a fresh CLI session. Bubblewrap overlays only its assigned global AGENTS text; no conversation is inherited. Prompt rendering checks passed for all four conditions; real host instruction hashes were unchanged after the run.",
              "- Prompt auditing uses `codex debug prompt-input` under explicit overrides; evaluation uses `codex exec` and additionally ignores user config. The audit is not a captured API request.",
              "- No task or instruction variant was tuned against the valid pilot results. Infrastructure calibrations and invalidated runs are excluded.",
              "- Small synthetic suite; likely ceiling effects. JSON evidence prompts explicitly request epistemic labels, limiting claims about spontaneous behavior. Read-grounding is a proxy. Memory, delegation, worktree placement, attribution, RAM conservation, and genuinely interactive revision are not established by this suite.",
              "- Compact prose and telegraphic text are approximate semantic/length controls. The rewrite removes the original's 'usually' qualifier on generalizing corrections; this is a semantic change, not just compression. A subsequent style-only experiment should restore it in both controls.",
              "- Before adoption or further prompt optimization, use harder held-out repository tasks and real multi-turn corrections. Do not choose a winner merely because its answers are shorter.",
              "", "The runnable experiment is documented in [README.md](README.md). Full manifests, raw traces, blinded review packets and per-episode results remain in the ignored run directory identified in `pilot-results.json`.", ""]
    adjudication_path = output / "adjudication.json"
    if adjudication_path.exists():
        adjudication = json.loads(adjudication_path.read_text())
        if adjudication.get("run") == "runs/" + run_dir.name:
            artifact["post_hoc_adjudication"] = adjudication
            (output / "pilot-results.json").write_text(json.dumps(artifact, indent=2) + "\n")
            lines += ["## Grading ambiguity", "",
                      "The baseline's single evidence-schema mismatch is not demonstrated epistemic failure. It set `tests_passed` to null and explicitly said pass/failure was unknown, but filled `failure_cause` with the observed incomplete-validation status instead of null. That field's intended meaning was underspecified. The raw score is retained; post-hoc manual review is documented in [adjudication.json](adjudication.json). No compliance or capability gain should be inferred from this one mismatch. This review was aware of condition and is not independent model evidence.", ""]
    (output / "RESULTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    export(args.run_directory.resolve(), args.output.resolve())
