#!/usr/bin/env python3
"""Offline fault-injection benchmark for the deterministic diagnosis engine.

Starts from a scenario's correct configurations, injects one known fault into
a random router, runs the diagnosis engine on the mutated network and checks
whether the injected router and fault family are identified. No LLM or
Batfish calls are made, so the benchmark is free and reproducible.

Usage:
    .venv312/bin/python scripts/analysis/diagnosis_benchmark.py \
        --scenario dataset/main_dataset/scenario-003 --trials 30
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modules.diagnosis_engine import diagnose  # noqa: E402

# Fault family -> diagnosis check that should explain it.
EXPECTED_CHECK = {
    "wrong_local_asn": "bgp_local_asn_mismatch",
    "wrong_remote_as": "bgp_remote_as_mismatch",
    "neighbor_ip_typo": "bgp_neighbor_unknown_ip",
    "missing_bgp_network": "bgp_prefix_not_advertised",
    "interface_ip_wrong": "link_subnet_mismatch",
    "interface_shutdown": "interface_shutdown",
    "ospf_disabled": "ospf_link_not_enabled",
}


def _interface_blocks(config: str) -> list[tuple[int, int, str]]:
    """Return (start, end, name) line spans of GigabitEthernet blocks."""
    lines = config.split("\n")
    spans = []
    for i, line in enumerate(lines):
        if line.startswith("interface GigabitEthernet"):
            j = i + 1
            while j < len(lines) and lines[j].strip() != "!":
                j += 1
            spans.append((i, j, line.split()[1]))
    return spans


def wrong_local_asn(config, rng):
    match = re.search(r"^router bgp (\d+)$", config, re.M)
    if not match:
        return None
    old = int(match.group(1))
    new = old + 1
    config = config.replace(f"router bgp {old}", f"router bgp {new}", 1)
    return config.replace(
        f"neighbor IBGP remote-as {old}", f"neighbor IBGP remote-as {new}"
    )


def wrong_remote_as(config, rng):
    lines = re.findall(r"^ neighbor (\d+\.\d+\.\d+\.\d+) remote-as (\d+)$", config, re.M)
    if not lines:
        return None
    ip, asn = rng.choice(lines)
    return config.replace(
        f" neighbor {ip} remote-as {asn}", f" neighbor {ip} remote-as {int(asn) + 7}"
    )


def neighbor_ip_typo(config, rng):
    ips = re.findall(r"^ neighbor (\d+\.\d+\.\d+\.\d+) peer-group", config, re.M)
    if not ips:
        return None
    ip = rng.choice(ips)
    octets = ip.split(".")
    octets[-1] = str((int(octets[-1]) + 97) % 250 + 3)
    return re.sub(rf"neighbor {re.escape(ip)}\b", f"neighbor {'.'.join(octets)}", config)


def missing_bgp_network(config, rng):
    nets = re.findall(r"^\s+network \d+\.\d+\.\d+\.\d+ mask \S+$", config, re.M)
    if not nets:
        return None
    return config.replace(rng.choice(nets) + "\n", "", 1)


def interface_ip_wrong(config, rng):
    spans = _interface_blocks(config)
    lines = config.split("\n")
    candidates = [
        (k, line) for s, e, _ in spans for k in range(s, e)
        if (line := lines[k]).strip().startswith("ip address")
    ]
    if not candidates:
        return None
    k, line = rng.choice(candidates)
    parts = line.split()
    octets = parts[2].split(".")
    octets[2] = str((int(octets[2]) + 100) % 250)
    lines[k] = line.replace(parts[2], ".".join(octets))
    return "\n".join(lines)


def interface_shutdown(config, rng):
    spans = _interface_blocks(config)
    if not spans:
        return None
    start, _, _ = rng.choice(spans)
    lines = config.split("\n")
    lines.insert(start + 1, " shutdown")
    return "\n".join(lines)


def ospf_disabled(config, rng):
    spans = _interface_blocks(config)
    lines = config.split("\n")
    targets = [
        (s, e) for s, e, _ in spans
        if any("ip ospf" in lines[k] and "area" in lines[k] for k in range(s, e))
    ]
    if not targets:
        return None
    start, end = rng.choice(targets)
    address = None
    for k in range(start, end):
        if lines[k].strip().startswith("ip address"):
            address = lines[k].split()[2]
        if "ip ospf" in lines[k] and "area" in lines[k]:
            lines[k] = ""
    # Also drop OSPF network statements that would still cover the address.
    if address:
        prefix = ".".join(address.split(".")[:3])
        lines = [
            l for l in lines
            if not (l.strip().startswith("network " + prefix) and "area" in l)
        ]
    return "\n".join(lines)


MUTATORS = {
    "wrong_local_asn": wrong_local_asn,
    "wrong_remote_as": wrong_remote_as,
    "neighbor_ip_typo": neighbor_ip_typo,
    "missing_bgp_network": missing_bgp_network,
    "interface_ip_wrong": interface_ip_wrong,
    "interface_shutdown": interface_shutdown,
    "ospf_disabled": ospf_disabled,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="dataset/main_dataset/scenario-003")
    parser.add_argument("--trials", type=int, default=30, help="trials per fault family")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", type=Path, help="optional path for per-trial results")
    args = parser.parse_args()

    scenario = Path(args.scenario)
    clean = {
        os.path.basename(p): open(p).read()
        for p in glob.glob(str(scenario / "initial_configs/configs/*.cfg"))
    }
    if not clean:
        parser.error(f"{scenario} has no initial_configs (ground truth required)")
    topology = json.loads((scenario / "data_and_metrics/topology.json").read_text())
    rng = random.Random(args.seed)
    routers = sorted(clean)

    baseline = diagnose(clean, topology)
    false_positives = sum(len(h.findings) for h in baseline.hypotheses)

    stats = defaultdict(lambda: defaultdict(int))
    trials = []
    for family, mutate in MUTATORS.items():
        done = attempts = 0
        while done < args.trials and attempts < args.trials * 20:
            attempts += 1
            target = rng.choice(routers)
            mutated_text = mutate(clean[target], rng)
            if mutated_text is None or mutated_text == clean[target]:
                continue
            configs = dict(clean, **{target: mutated_text})
            report = diagnose(configs, topology)
            ranked = report.ranked_routers()
            rank = ranked.index(target) + 1 if target in ranked else None
            top_check = report.hypotheses[0].primary_check if report.hypotheses else None
            s = stats[family]
            s["n"] += 1
            s["top1"] += rank == 1
            s["top3"] += rank is not None and rank <= 3
            s["detected"] += rank is not None
            s["type_ok"] += rank == 1 and top_check == EXPECTED_CHECK[family]
            trials.append({
                "family": family, "target": target, "rank": rank,
                "top_check": top_check, "num_hypotheses": len(ranked),
            })
            done += 1

    n_routers = len(routers)
    print(f"Scenario: {scenario.name}  routers: {n_routers}  "
          f"findings on clean network: {false_positives}")
    print(f"Random-guess baseline: top-1 {1 / n_routers:.1%}, top-3 {3 / n_routers:.1%}\n")
    header = f"{'Fault family':22} {'n':>3} {'Top-1':>7} {'Top-3':>7} {'Detected':>9} {'Type ok':>8}"
    print(header)
    print("-" * len(header))
    totals = defaultdict(int)
    for family in MUTATORS:
        s = stats[family]
        for key in ("n", "top1", "top3", "detected", "type_ok"):
            totals[key] += s[key]
        n = s["n"] or 1
        print(f"{family:22} {s['n']:>3} {s['top1']/n:>7.0%} {s['top3']/n:>7.0%} "
              f"{s['detected']/n:>9.0%} {s['type_ok']/n:>8.0%}")
    n = totals["n"] or 1
    print("-" * len(header))
    print(f"{'ALL':22} {totals['n']:>3} {totals['top1']/n:>7.0%} {totals['top3']/n:>7.0%} "
          f"{totals['detected']/n:>9.0%} {totals['type_ok']/n:>8.0%}")

    if args.json:
        args.json.write_text(json.dumps(trials, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
