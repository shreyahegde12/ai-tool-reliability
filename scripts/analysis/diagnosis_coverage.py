#!/usr/bin/env python3
"""Measure how often the deterministic diagnosis finds anything.

Runs the diagnosis engine alone (no LLM, no Batfish) on the faulty snapshot
of every scenario and reports how many scenarios get at least one finding,
which checks fire, and how often the top suspect is one of the routers named
by the violated specifications. Free and deterministic.

Usage:
    .venv312/bin/python scripts/analysis/diagnosis_coverage.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modules.diagnosis_engine import diagnose  # noqa: E402

DEV_SET = {"scenario-003", "scenario-006", "scenario-008", "scenario-009"}


def _violated_specs(scenario: Path) -> list[str]:
    path = scenario / "specifications" / "specifications_100pct.csv"
    with path.open(encoding="utf-8") as handle:
        return [line.strip() for line in handle if "broken" in line.lower()]


def _spec_routers(specs: list[str]) -> set[str]:
    routers = set()
    for row in csv.reader(specs):
        if len(row) > 3:
            routers.add(row[1].lower())
            if row[3]:
                routers.add(row[3].lower())
    return routers


def analyse(scenario: Path) -> dict:
    configs = {
        cfg.name: cfg.read_text(encoding="utf-8", errors="replace")
        for cfg in sorted((scenario / "final_configs" / "configs").glob("*.cfg"))
    }
    topology_path = scenario / "data_and_metrics" / "topology.json"
    topology = json.loads(topology_path.read_text()) if topology_path.exists() else None
    specs = _violated_specs(scenario)
    report = diagnose(configs, topology, specs)
    top = report.hypotheses[0] if report.hypotheses else None
    return {
        "scenario": scenario.name,
        "dev": scenario.name in DEV_SET,
        "routers": len(configs),
        "violated_specs": len(specs),
        "finding": top is not None,
        "top_router": top.router if top else None,
        "top_check": top.primary_check if top else None,
        "checks": sorted({f.check for h in report.hypotheses for f in h.findings}),
        "top_in_specs": bool(top)
        and top.router.removesuffix(".cfg").lower() in _spec_routers(specs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("dataset/main_dataset"))
    parser.add_argument("--out", type=Path, default=Path("results_main/diagnosis_coverage.json"))
    args = parser.parse_args()

    rows = []
    for scenario in sorted(args.dataset.glob("scenario-*")):
        try:
            rows.append(analyse(scenario))
        except Exception as exc:  # keep going; report failures
            rows.append({"scenario": scenario.name, "error": str(exc)})

    ok = [r for r in rows if "error" not in r]
    held = [r for r in ok if not r["dev"]]
    found = [r for r in held if r["finding"]]
    print(f"Scenarios analysed: {len(ok)} ({len(rows) - len(ok)} errors)")
    print(f"Non-dev scenarios with a finding: {len(found)}/{len(held)} "
          f"({100 * len(found) / max(len(held), 1):.1f}%)")
    print(f"Top suspect named in violated specs: "
          f"{sum(r['top_in_specs'] for r in found)}/{len(found)}")
    print("Top check (non-dev):")
    for check, n in Counter(r["top_check"] for r in found).most_common():
        print(f"  {check:32s} {n}")
    print("Any check firing (non-dev scenarios):")
    for check, n in Counter(c for r in held for c in r["checks"]).most_common():
        print(f"  {check:32s} {n}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=2))
    print(f"Per-scenario results: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
