#!/usr/bin/env python3
"""Instruction ablation on pinned, externally authored BigCodeBench-Hard tasks.

Uses the upstream evaluator unchanged. This module only selects cases, delivers
original prompts to fresh agents, captures scripts, and summarizes official scores.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import pickle
import statistics
import subprocess
import sys
import uuid

from evaluate import ROOT, VARIANTS, audit_namespace, command, execute, parse_events, namespace_command, write_json

EXTERNAL = Path.home() / ".local/share/agent-instruction-eval/external"
UPSTREAM = EXTERNAL / "bigcodebench"
PYTHON = EXTERNAL / "eval-env/bin/python"
REFERENCE = EXTERNAL / "reference"
DATASET_REVISION = "298d2cc7b96612e15e47313c3603ee124cee0c1f"
UPSTREAM_REVISION = "09dd993f46c3fbf3a799465bb96d524edcb0b199"
DATASET_URL = f"https://huggingface.co/datasets/bigcode/bigcodebench-hard/resolve/{DATASET_REVISION}/data/v0.1.4-00000-of-00001.parquet"


def cache_directory():
    return Path(subprocess.check_output([str(PYTHON), "-c", "from bigcodebench.data.utils import CACHE_DIR; print(CACHE_DIR)"], text=True).strip())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source():
    if subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip() != UPSTREAM_REVISION:
        raise ValueError("Upstream revision changed")
    subprocess.run(["git", "-C", str(UPSTREAM), "diff", "--exit-code", "HEAD", "--"], check=True)
    installed = Path(subprocess.check_output([str(PYTHON), "-c", "import bigcodebench; print(next(iter(bigcodebench.__path__)))"], text=True).strip())
    for source in (UPSTREAM / "bigcodebench").rglob("*.py"):
        if source.name == "_version.py":
            continue  # Build-generated SCM metadata, not evaluator logic.
        if sha(source) != sha(installed / source.relative_to(UPSTREAM / "bigcodebench")):
            raise ValueError(f"Installed evaluator differs: {source.name}")


def verify_protocol(protocol):
    verify_source()
    for name, field in (("dataset.jsonl", "jsonl_sha256"), ("prompts.json", "prompts_sha256")):
        if sha(REFERENCE / name) != protocol[field]:
            raise ValueError(f"Benchmark artifact changed: {name}")


def grader_environment():
    # Reference data is supplied ONLY to the grader, never the generation process.
    env = dict(os.environ)
    env.update(BIGCODEBENCH_OVERRIDE_PATH=str(REFERENCE / "dataset.jsonl"),
               CUDA_VISIBLE_DEVICES="", MPLBACKEND="Agg", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", NUMBA_NUM_THREADS="1", TF_NUM_INTRAOP_THREADS="1",
               TF_NUM_INTEROP_THREADS="1")
    scratch = EXTERNAL / "scratch"
    scratch.mkdir(exist_ok=True)
    env["TMPDIR"] = str(scratch)
    return env


def prepare(count, seed, exclude=(), comparison_pair=("telegraphic", "original"), artifact_prefix="external"):
    """Pin full data and choose IDs before reading task content or generating answers."""
    REFERENCE.mkdir(parents=True, exist_ok=True)
    verify_source()
    commit = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if commit != UPSTREAM_REVISION:
        raise ValueError("Upstream revision changed")
    parquet = EXTERNAL / "BigCodeBench-Hard-v0.1.4.parquet"
    program = """import json,sys,pandas as pd
rows=pd.read_parquet(sys.argv[1]).to_dict('records')
with open(sys.argv[2],'w') as f:
 for row in rows: f.write(json.dumps(row)+'\\n')
print(json.dumps({'count':len(rows),'ids':[row['task_id'] for row in rows]}))
"""
    result = subprocess.check_output([str(PYTHON), "-c", program, str(parquet), str(REFERENCE / "dataset.jsonl")], text=True)
    metadata = json.loads(result)
    eligible = sorted(set(metadata["ids"]) - set(exclude))
    if metadata["count"] != 148 or not 1 <= count <= len(eligible):
        raise ValueError("Unexpected benchmark size or invalid sample count")
    # Sorting and seeded sampling depend on IDs alone, not content or performance.
    selected = sorted(random.Random(seed).sample(eligible, count))
    protocol = {
        "benchmark": "BigCodeBench-Hard", "split": "instruct", "dataset_version": "v0.1.4",
        "dataset_revision": DATASET_REVISION, "dataset_url": DATASET_URL,
        "parquet_sha256": sha(parquet), "jsonl_sha256": sha(REFERENCE / "dataset.jsonl"),
        "upstream_revision": commit, "requirements_sha256": sha(UPSTREAM / "Requirements/requirements-eval.txt"),
        "seed": seed, "selection": "Uniform seeded sample of sorted task IDs; no content/performance filtering",
        "selected_ids": selected, "available_tasks": metadata["count"],
        "excluded_ids": sorted(exclude), "eligible_tasks": len(eligible),
        "comparison_pair": list(comparison_pair), "artifact_prefix": artifact_prefix,
        "grading": "Unmodified upstream bigcodebench.evaluate local, calibrated=True, pass_k=1; multiprocessing spawn; headless Agg backend",
        "primary_comparison": f"Paired pass/fail difference: {comparison_pair[0]} minus {comparison_pair[1]}",
        "secondary": ["compact minus telegraphic", "none versus instruction variants", "output tokens", "latency"],
        "reference_gate": "Every selected canonical solution must pass before generation; no dropping failed cases",
        "limits": "Public benchmark may occur in training. Tests evaluate coding outputs, not all AGENTS behaviors. Codex agent scaffold differs from the benchmark's standard one-shot generation scaffold.",
    }
    write_json(REFERENCE / "protocol.json", protocol)
    # Only this prompt-only projection is available to the orchestration program.
    data = [json.loads(line) for line in (REFERENCE / "dataset.jsonl").read_text().splitlines()]
    prompts = {row["task_id"]: row["instruct_prompt"] for row in data if row["task_id"] in selected}
    write_json(REFERENCE / "prompts.json", prompts)
    protocol["prompts_sha256"] = sha(REFERENCE / "prompts.json")
    write_json(REFERENCE / "protocol.json", protocol)
    return protocol


def official_arguments(protocol, samples=None, references=False):
    args = [str(PYTHON), "-c", "import multiprocessing; multiprocessing.set_start_method('spawn'); from bigcodebench.evaluate import main; main()", "--execution", "local", "--split", "instruct",
            "--subset", "hard", "--parallel", "4", "--pass_k", "1", "--selective_evaluate",
            ",".join(protocol["selected_ids"])]
    if references:
        args += ["--check_gt_only", "--samples", str(REFERENCE / "reference.jsonl")]
    else:
        args += ["--samples", str(samples)]
    return args


def references():
    protocol = json.loads((REFERENCE / "protocol.json").read_text())
    verify_protocol(protocol)
    with (REFERENCE / "reference.log").open("w") as log:
        result = subprocess.run(official_arguments(protocol, references=True), env=grader_environment(), text=True,
                                stdout=log, stderr=subprocess.STDOUT)
    print((REFERENCE / "reference.log").read_text(), flush=True)
    result.check_returncode()
    cache = cache_directory() / (hashlib.md5((REFERENCE / "dataset.jsonl").read_bytes()).hexdigest() + ".pkl")
    with cache.open("rb") as f:
        timings = pickle.load(f)
    passed = set(timings) == set(protocol["selected_ids"]) and all(value is not None for value in timings.values())
    write_json(REFERENCE / "reference-gate.json", {"all_pass": passed, "selected_ids": protocol["selected_ids"],
               "dataset_sha256": sha(REFERENCE / "dataset.jsonl"), "official_reference_times": timings})
    if not passed:
        raise ValueError("Official references failed; repair environment without dropping tasks")


def hidden_namespace(args, policy):
    wrapped = namespace_command(args, policy)
    separator = wrapped.index("--")
    hidden = []
    for directory in (*EXTERNAL.glob("reference*"), UPSTREAM, cache_directory()):
        if directory.exists():
            hidden += ["--tmpfs", str(directory)]
    parquet = EXTERNAL / "BigCodeBench-Hard-v0.1.4.parquet"
    if parquet.exists():
        hidden += ["--ro-bind", str(policy), str(parquet)]
    return wrapped[:separator] + hidden + wrapped[separator:]


def generate_one(job, output, workspace_root, model, effort, instructions, prompts, timeout):
    task_id, variant = job
    identifier = uuid.uuid4().hex
    artifact = output / "episodes" / identifier
    workspace = workspace_root / identifier
    artifact.mkdir(parents=True)
    workspace.mkdir(parents=True)
    policy = artifact / "policy.md"
    policy.write_text(instructions[variant])
    original_prompt = prompts[task_id]
    (workspace / "task.txt").write_text(original_prompt)
    prompt = original_prompt + f"\n\nDelivery: write the self-contained Python solution to solution.py in the current directory. " \
             f"Python with benchmark dependencies is available at {PYTHON}. Work only in this directory; do not inspect parent or sibling directories."
    final_path = artifact / "final.txt"
    args = hidden_namespace(command(model, effort, workspace, "", final_path), policy)
    write_json(artifact / "invocation.json", {"argv": args, "prompt": prompt})
    rc, stdout, stderr, seconds, expired = execute(args, prompt, workspace, timeout)
    (artifact / "events.jsonl").write_text(stdout)
    (artifact / "stderr.txt").write_text(stderr)
    events = parse_events(stdout)
    complete = any(event.get("type") == "turn.completed" for event in events)
    backend_failure = any("Failed to create unified exec process" in event.get("item", {}).get("aggregated_output", "") for event in events)
    script = workspace / "solution.py"
    solution = script.read_text() if script.is_file() else ""
    # No extracting or rewriting code: deliver exactly the generated script to upstream scoring.
    (artifact / "solution.py").write_text(solution)
    record = {"episode": identifier, "task_id": task_id, "variant": variant,
              "error": rc != 0 or expired or not complete or backend_failure,
              "missing_solution": not bool(solution.strip()), "timeout": expired, "seconds": seconds,
              "usage": next((event.get("usage", {}) for event in reversed(events) if event.get("type") == "turn.completed"), {}),
              "commands": sum(event.get("type") == "item.completed" and event.get("item", {}).get("type") == "command_execution" for event in events),
              "original_prompt_sha256": hashlib.sha256(original_prompt.encode()).hexdigest(),
              "solution_sha256": hashlib.sha256(solution.encode()).hexdigest(), "workspace": str(workspace)}
    write_json(artifact / "result.json", record)
    return record


def generate(output, model, effort, concurrency, timeout):
    # Same headless plotting backend as the execution grader, for every condition.
    os.environ["MPLBACKEND"] = "Agg"
    protocol = json.loads((REFERENCE / "protocol.json").read_text())
    verify_protocol(protocol)
    gate = REFERENCE / "reference-gate.json"
    if not gate.exists():
        raise ValueError("Run official reference check and record its result before generation")
    verified = json.loads(gate.read_text())
    if not verified.get("all_pass") or verified.get("dataset_sha256") != protocol["jsonl_sha256"] or verified.get("selected_ids") != protocol["selected_ids"]:
        raise ValueError("Reference gate is missing, failed, or stale")
    output.mkdir(parents=True, exist_ok=False)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    workspace_root = Path.home() / ".local/share/agent-instruction-eval" / ("external-" + stamp)
    workspace_root.mkdir()
    instructions = {v: (ROOT / "variants" / (v + ".md")).read_text() for v in VARIANTS}
    if "policy_sha256" in protocol and any(hashlib.sha256(value.encode()).hexdigest() != protocol["policy_sha256"].get(variant) for variant, value in instructions.items()):
        raise ValueError("Policy text differs from frozen protocol")
    audit_namespace(output, instructions, workspace_root, model, effort)
    hidden = subprocess.run(hidden_namespace([str(PYTHON), "-c",
        "import pathlib,sys,pty; pty.openpty(); assert all(not any(pathlib.Path(p).iterdir()) for p in sys.argv[1:]); print('reference mounts hidden; runtime and PTY available')",
        str(REFERENCE), str(UPSTREAM)], output / "audit" / (next(iter(instructions)) + ".md")), cwd=workspace_root,
        capture_output=True, text=True, check=True)
    write_json(output / "audit/benchmark-isolation.json", {"passed": True, "output": hidden.stdout,
               "hidden": [str(REFERENCE), str(UPSTREAM), str(EXTERNAL / "BigCodeBench-Hard-v0.1.4.parquet")]})
    prompts = json.loads((REFERENCE / "prompts.json").read_text())
    jobs = [(task_id, variant) for task_id in protocol["selected_ids"] for variant in VARIANTS]
    random.Random(protocol["seed"]).shuffle(jobs)
    manifest = {"protocol": protocol, "model": model, "effort": effort, "concurrency": concurrency,
                "timeout": timeout, "jobs": jobs, "reference_gate": verified,
                "cli": subprocess.check_output(["codex", "--version"], text=True).strip(),
                "variants": {v: {"sha256": hashlib.sha256(text.encode()).hexdigest(), "utf8_bytes": len(text.encode())} for v, text in instructions.items()}}
    write_json(output / "manifest.json", manifest)
    (output / "variants").mkdir()
    for variant, text in instructions.items():
        (output / "variants" / (variant + ".md")).write_text(text)
    print(f"RUN {output} ({len(jobs)} fresh sessions; external problems and tests)", flush=True)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(generate_one, job, output, workspace_root, model, effort, instructions, prompts, timeout) for job in jobs]
        for i, future in enumerate(as_completed(futures), 1):
            record = future.result()
            print(f"{i}/{len(jobs)} {record['task_id']} {record['variant']} error={record['error']} missing={record['missing_solution']} seconds={record['seconds']:.1f}", flush=True)
    audit = json.loads((output / "audit/isolation.json").read_text())
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != value for p, value in audit["host_instruction_hashes"].items()):
        write_json(output / "INVALID.json", {"reason": "Host instruction file changed"})
        raise ValueError("Host instruction file changed")
    audit["host_hashes_unchanged_after_run"] = True
    write_json(output / "audit/isolation.json", audit)
    export_samples(output)


def export_samples(output):
    records = [json.loads(p.read_text()) for p in (output / "episodes").glob("*/result.json")]
    manifest = json.loads((output / "manifest.json").read_text())
    if len(records) != len(manifest["jobs"]) or len({(r["task_id"], r["variant"]) for r in records}) != len(records) or {(r["task_id"], r["variant"]) for r in records} != {tuple(j) for j in manifest["jobs"]}:
        raise ValueError("Incomplete generation")
    for variant in manifest["variants"]:
        rows = []
        for record in sorted((r for r in records if r["variant"] == variant), key=lambda r: r["task_id"]):
            # Infrastructure failures count as unsuccessful episodes, not missing data.
            solution = "" if record["error"] else (output / "episodes" / record["episode"] / "solution.py").read_text()
            rows.append({"task_id": record["task_id"], "solution": solution})
        (output / (variant + ".jsonl")).write_text("".join(json.dumps(row) + "\n" for row in rows))


def score(output):
    manifest = json.loads((output / "manifest.json").read_text())
    variants = list(manifest["variants"])
    verify_protocol(manifest["protocol"])
    cache = cache_directory() / (hashlib.md5((REFERENCE / "dataset.jsonl").read_bytes()).hexdigest() + ".pkl")
    with cache.open("rb") as f:
        timings = pickle.load(f)
    if timings != manifest["reference_gate"]["official_reference_times"]:
        raise ValueError("Official reference timing cache changed since generation")
    if (output / "INVALID.json").exists():
        raise ValueError("Invalid run")
    export_samples(output)
    if any((output / (v + "_eval_results.json")).exists() for v in variants):
        raise ValueError("Existing official results: use a new scoring run to avoid upstream stale caches")
    write_json(output / "score-provenance.json", {"samples_sha256": {v: sha(output / (v + ".jsonl")) for v in variants},
               "upstream_revision": UPSTREAM_REVISION, "dataset_sha256": manifest["protocol"]["jsonl_sha256"],
               "condition_concurrency": min(4, len(variants)), "upstream_parallel_workers_per_condition": 4,
               "multiprocessing_start_method": "spawn", "matplotlib_backend": "Agg"})
    def grade_variant(variant):
        log_path = output / (variant + "-grading.log")
        with log_path.open("w") as log:
            result = subprocess.run(official_arguments(manifest["protocol"], output / (variant + ".jsonl")),
                                    env=grader_environment(), text=True, stdout=log, stderr=subprocess.STDOUT)
        print(variant, log_path.read_text(), flush=True)
        result.check_returncode()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(grade_variant, variant) for variant in variants]
        for future in as_completed(futures):
            future.result()


def paired_comparison(scores, ids, treatment, baseline, seed):
    deltas = [int(scores[treatment][task]) - int(scores[baseline][task]) for task in ids]
    rng = random.Random(seed)
    bootstrap = sorted(sum(rng.choices(deltas, k=len(ids))) / len(ids) for _ in range(10000))
    wins, losses = deltas.count(1), deltas.count(-1)
    discordant = wins + losses
    return {"difference": statistics.mean(deltas), "descriptive_95pct_task_bootstrap": [bootstrap[250], bootstrap[9749]],
            "treatment": treatment, "baseline": baseline, "treatment_only_pass": wins, "baseline_only_pass": losses,
            "exact_paired_two_sided_p": min(1.0, 2 * sum(math.comb(discordant, k) for k in range(min(wins, losses) + 1)) / 2**discordant) if discordant else 1.0}


def report(output):
    manifest = json.loads((output / "manifest.json").read_text())
    variants = list(manifest["variants"])
    verify_protocol(manifest["protocol"])
    if (output / "INVALID.json").exists():
        raise ValueError("Invalid run")
    provenance = json.loads((output / "score-provenance.json").read_text())
    if any(sha(output / (v + ".jsonl")) != provenance["samples_sha256"][v] for v in variants):
        raise ValueError("Samples changed after scoring")
    ids = manifest["protocol"]["selected_ids"]
    scores, metrics = {}, {}
    records = [json.loads(p.read_text()) for p in (output / "episodes").glob("*/result.json")]
    for variant in variants:
        official = json.loads((output / (variant + "_eval_results.json")).read_text())["eval"]
        if set(official) != set(ids) or any(len(rows) != 1 for rows in official.values()):
            raise ValueError("Official score has incomplete or duplicate tasks")
        scores[variant] = {task: official[task][0]["status"] == "pass" for task in ids}
        episodes = [r for r in records if r["variant"] == variant]
        metrics[variant] = {"passed": sum(scores[variant].values()), "tasks": len(ids),
            "infrastructure_errors": sum(r["error"] for r in episodes),
            "missing_solutions": sum(r["missing_solution"] for r in episodes),
            "median_output_tokens": statistics.median(r["usage"].get("output_tokens", 0) for r in episodes),
            "median_seconds": statistics.median(r["seconds"] for r in episodes)}
    treatment, baseline = manifest["protocol"].get("comparison_pair", ["telegraphic", "original"])
    comparison = paired_comparison(scores, ids, treatment, baseline, manifest["protocol"]["seed"])
    secondary = [paired_comparison(scores, ids, *item.split(" minus "), manifest["protocol"]["seed"])
                 for item in manifest["protocol"].get("secondary", []) if " minus " in item]
    result = {"manifest": manifest, "metrics": metrics, "primary_comparison": comparison, "secondary_comparisons": secondary, "official_per_task": scores}
    artifact = manifest["protocol"].get("artifact_prefix", "external")
    if not artifact.replace("-", "").isalnum():
        raise ValueError("Invalid artifact prefix")
    write_json(ROOT / (artifact + "-results.json"), result)
    environment_file = artifact + "-environment.txt"
    lines = ["# External AGENTS instruction evaluation", "", 
        f"BigCodeBench-Hard v0.1.4: {len(ids)} seeded random externally authored tasks; {len(variants)} frozen policies; one fresh {manifest['model']} session per task and policy. Original benchmark prompts and tests; unmodified upstream execution grader. All {len(ids)} canonical solutions passed before generation.", "",
        "| Policy | Passed | Infrastructure errors | Median output tokens | Median seconds |", "|---|---:|---:|---:|---:|"]
    for variant in variants:
        m = metrics[variant]
        lines.append(f"| {variant} | {m['passed']}/{m['tasks']} | {m['infrastructure_errors']} | {m['median_output_tokens']:.0f} | {m['median_seconds']:.1f} |")
    for item in [comparison, *secondary]:
        lo, hi = item["descriptive_95pct_task_bootstrap"]
        lines += ["", f"{item['treatment']} minus {item['baseline']}: {item['difference'] * 100:+.1f} percentage points. Descriptive paired task-bootstrap 95% interval: {lo*100:+.1f} to {hi*100:+.1f} points. Treatment-only passes: {item['treatment_only_pass']}; baseline-only passes: {item['baseline_only_pass']}. Exact paired two-sided test p = {item['exact_paired_two_sided_p']:.3f}."]
    lines += ["", "The bootstrap intervals are descriptive; these results do not establish equivalence or rule out harm.", "",
        "This is an exploratory estimate of coding performance under this Codex scaffold. This sample and one generation per condition do not establish equivalence or a capability change. Public benchmark contamination is unknown. Policies differ in length and some wording strength, so this does not isolate telegraphic syntax. Benchmark tests do not score every AGENTS behavior; no claim about correction generalization, epistemic honesty, or idiomatic quality is made from pass rates alone.", "",
        "The prior self-authored pilot is withdrawn as effectiveness evidence and retained solely as infrastructure calibration. The same-model subagent reviewed infrastructure, not answers or benchmark task selection.", "",
        f"Execution runtime: Python 3.9.25, headless Matplotlib Agg, multiprocessing spawn; {provenance['condition_concurrency']} condition graders concurrently, each with four upstream workers. Reference diagnostic stack tracing: {manifest['protocol'].get('reference_diagnostic_tracing', True)}; candidate grading used no tracing. Installed packages are frozen in [{environment_file}]({environment_file}).", "",
        f"Provenance: dataset revision `{DATASET_REVISION}`; upstream commit `{UPSTREAM_REVISION}`; seed `{manifest['protocol']['seed']}`. Hashes, selected IDs, full per-task scores and protocol are in [{artifact}-results.json]({artifact}-results.json). Raw run: `{output}`.", "",
        "Sources: [BigCodeBench](https://github.com/bigcode-project/bigcodebench), [BigCodeBench-Hard dataset](https://huggingface.co/datasets/bigcode/bigcodebench-hard)."]
    (ROOT / (artifact.upper() + "-RESULTS.md")).write_text("\n".join(lines) + "\n")
    print(json.dumps({"metrics": metrics, "comparison": comparison}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--count", type=int, default=40)
    prep.add_argument("--seed", type=int, default=20261012)
    gen = sub.add_parser("generate")
    gen.add_argument("--output", type=Path, required=True)
    gen.add_argument("--model", default="gpt-6.1-sol")
    gen.add_argument("--effort", default="medium")
    gen.add_argument("--concurrency", type=int, default=4)
    gen.add_argument("--timeout", type=int, default=300)
    refs = sub.add_parser("reference-command")
    sub.add_parser("references")
    scoring = sub.add_parser("score")
    scoring.add_argument("--output", type=Path, required=True)
    reporting = sub.add_parser("report")
    reporting.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(prepare(args.count, args.seed), indent=2))
    elif args.action == "reference-command":
        import shlex
        print(" ".join(shlex.quote(arg) for arg in official_arguments(json.loads((REFERENCE / "protocol.json").read_text()), references=True)))
    elif args.action == "references":
        references()
    elif args.action == "score":
        score(args.output.resolve())
    elif args.action == "report":
        report(args.output.resolve())
    else:
        generate(args.output.resolve(), args.model, args.effort, args.concurrency, args.timeout)


if __name__ == "__main__":
    main()
