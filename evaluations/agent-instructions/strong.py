#!/usr/bin/env python3
"""Frozen stronger-telegraphy experiment on unseen, externally authored tasks."""
import argparse
import json

import external

external.REFERENCE = external.EXTERNAL / "reference-strong-v1"
external.VARIANTS = ("original", "telegraphic", "telegraphic_strong")
OUTPUT = external.ROOT / "runs/strong-v1"


def prepare():
    if (external.REFERENCE / "protocol.json").exists():
        raise ValueError("Protocol already frozen; do not overwrite")
    previous = json.loads((external.ROOT / "external-protocol.json").read_text())
    protocol = external.prepare(60, 20261013, previous["selected_ids"],
                                ("telegraphic_strong", "telegraphic"), "strong")
    protocol.update(
        secondary=["telegraphic_strong minus original", "output tokens", "latency"],
        reference_diagnostic_tracing=False,
        hypothesis="Denser fragments may condition execution better; matching private reasoning is not established.",
        policy_semantics="Strong restores correction usually; wording/length differ, not a pure syntax intervention.",
        policy_sha256={v: external.sha(external.ROOT / "variants" / (v + ".md")) for v in external.VARIANTS},
        excluded_prior_protocol_sha256=external.sha(external.ROOT / "external-protocol.json"),
    )
    external.write_json(external.REFERENCE / "protocol.json", protocol)
    external.write_json(external.ROOT / "strong-protocol.json", protocol)
    print(f"Frozen {len(protocol['selected_ids'])} tasks, no overlap with previous 40, three policies", flush=True)


def run():
    protocol = json.loads((external.REFERENCE / "protocol.json").read_text())
    for variant, digest in protocol["policy_sha256"].items():
        if external.sha(external.ROOT / "variants" / (variant + ".md")) != digest:
            raise ValueError("Policy changed after protocol freeze")
    external.references()
    external.generate(OUTPUT, "gpt-6.1-sol", "medium", 4, 300)
    external.score(OUTPUT)
    external.report(OUTPUT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    args = parser.parse_args()
    prepare() if args.action == "prepare" else run()
