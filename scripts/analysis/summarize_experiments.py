#!/usr/bin/env python3
"""Build CSV and Markdown summaries from Cornetto experiment results."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


RESULT_FILENAME = "zero_shot_benchmark_results.json"

CSV_FIELDS = [
    "run_directory",
    "run_id",
    "metadata_status",
    "scenario_name",
    "sample_id",
    "experiment_seed",
    "model_provider",
    "model_name",
    "context_sampling",
    "max_context_tokens",
    "node_count",
    "node_count_retrieved",
    "selected_routers",
    "selected_config_tokens",
    "requirements_fixed",
    "requirements_evaluated",
    "fix_rate",
    "regressions",
    "complete_repair",
    "agent_steps",
    "verification_calls",
    "patches_attempted",
    "rollbacks",
    "reliability_enabled",
    "net_benefit_ratio",
    "actions_rejected",
    "net_benefit_accepted",
    "automatic_rollbacks",
    "selective_rollbacks",
    "forced_final_verifications",
    "evidence_alignment",
    "evidence_nudges",
    "diagnosis_enabled",
    "diagnosis_calls",
    "diagnosis_top_router",
    "diagnosis_top_check",
    "diagnosis_followed",
    "routers_changed",
    "max_steps",
    "submitted",
    "termination_reason",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "latency_seconds",
    "failure_mode",
]

MARKDOWN_FIELDS = [
    ("Metadata", "metadata_status"),
    ("Scenario", "scenario_name"),
    ("Method", "context_sampling"),
    ("Gate", "gate_label"),
    ("Diagnosis", "diagnosis_label"),
    ("Run", "run_id"),
    ("Seed", "experiment_seed"),
    ("Routers", "node_count_retrieved"),
    ("Repaired", "requirements_fixed"),
    ("Evaluated", "requirements_evaluated"),
    ("Repair rate", "fix_rate_display"),
    ("Regressions", "regressions"),
    ("Steps", "agent_steps"),
    ("Verifications", "verification_calls"),
    ("Tokens", "total_tokens"),
    ("Latency (s)", "latency_display"),
    ("Complete", "complete_repair"),
    ("Termination", "termination_reason"),
]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def _path_value(path: Path, pattern: str) -> str | None:
    match = re.search(pattern, path.as_posix())
    return match.group(1) if match else None


def _task_evaluation(
    aggregate_path: Path,
    sample_id: Any,
) -> dict[str, Any]:
    if sample_id is None:
        return {}
    path = aggregate_path.parent / f"Task_{sample_id}" / "evaluation_results.json"
    return _load_json(path) if path.exists() else {}


def _changed_routers(aggregate_path: Path, sample_id: Any) -> list[str]:
    """Routers whose final config differs from the faulty one."""
    task_dir = aggregate_path.parent / f"Task_{sample_id}"
    changed = []
    for fixed in sorted((task_dir / "fix").glob("*.cfg")):
        faulty = task_dir / "fault" / fixed.name
        if faulty.exists() and fixed.read_text() != faulty.read_text():
            changed.append(fixed.name)
    return changed


def _diagnosis_fields(
    result: dict[str, Any],
    changed: list[str],
) -> dict[str, Any]:
    history = result.get("agent_diagnosis_history") or []
    hypotheses = history[0].get("hypotheses", []) if history else []
    top = hypotheses[0] if hypotheses else {}
    enabled = bool(result.get("agent_diagnosis_enabled"))
    top_router = top.get("router")
    if not enabled:
        followed = None
    elif not top_router:
        followed = "no_finding"
    else:
        followed = "followed" if top_router in changed else "ignored"
    return {
        "diagnosis_enabled": enabled,
        "diagnosis_calls": result.get("agent_diagnosis_calls"),
        "diagnosis_top_router": top_router,
        "diagnosis_top_check": top.get("check"),
        "diagnosis_followed": followed,
    }


def _normalise_row(
    aggregate_path: Path,
    result: dict[str, Any],
    run_info: dict[str, Any],
) -> dict[str, Any]:
    sample_id = result.get("sample_id")
    evaluation = _task_evaluation(aggregate_path, sample_id)
    summary = evaluation.get("fix_evaluation", {}).get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    selected = result.get("selected_routers") or []
    if isinstance(selected, list):
        selected = ";".join(str(router) for router in selected)
    else:
        selected = str(selected)

    fix_rate = summary.get("fix_rate", result.get("best_score"))
    complete = result.get("success")
    if complete is None and isinstance(fix_rate, (int, float)):
        complete = fix_rate >= 1.0

    context_sampling = (
        result.get("context_sampling")
        or result.get("agent_context_mode")
        or _path_value(aggregate_path, r"context-mode-([^/]+)")
    )
    seed = result.get("experiment_seed")
    if seed is None:
        seed = _path_value(aggregate_path, r"seed-([^/]+)")

    has_context_metadata = (
        "scenario_name" in result
        and "selected_routers" in result
        and "selected_config_tokens" in result
    )

    changed = _changed_routers(aggregate_path, sample_id)
    max_steps = _path_value(aggregate_path, r"steps-(\d+)-")

    return {
        "run_directory": str(aggregate_path.parent),
        "run_id": _path_value(aggregate_path, r"/run-([^/]+)-seed-[^/]+/"),
        **_diagnosis_fields(result, changed),
        "routers_changed": ";".join(changed),
        "max_steps": int(max_steps) if max_steps else None,
        "metadata_status": (
            "complete" if has_context_metadata
            else "legacy_missing_context_metadata"
        ),
        "scenario_name": result.get("scenario_name") or f"Task-{sample_id}",
        "sample_id": sample_id,
        "experiment_seed": seed,
        "model_provider": result.get("model_provider") or run_info.get("model_provider"),
        "model_name": result.get("model_name") or run_info.get("model_name"),
        "context_sampling": context_sampling,
        "max_context_tokens": result.get("max_context_tokens"),
        "node_count": result.get("node_count"),
        "node_count_retrieved": (
            result.get("node_count_retrieved")
            if has_context_metadata else None
        ),
        "selected_routers": selected,
        "selected_config_tokens": result.get("selected_config_tokens"),
        "requirements_fixed": summary.get("fixed"),
        "requirements_evaluated": summary.get("evaluated_predicates"),
        "fix_rate": fix_rate,
        "regressions": summary.get("side_effects"),
        "complete_repair": complete,
        "agent_steps": result.get("agent_total_steps"),
        "verification_calls": result.get("agent_verifications"),
        "patches_attempted": result.get("agent_patches_attempted"),
        "rollbacks": result.get("agent_rollbacks"),
        "reliability_enabled": result.get("agent_reliability_enabled"),
        "net_benefit_ratio": (
            result.get("agent_reliability_net_benefit_ratio")
            if result.get("agent_reliability_enabled")
            else None
        ),
        "actions_rejected": result.get(
            "agent_reliability_actions_rejected"
        ),
        "net_benefit_accepted": result.get(
            "agent_reliability_net_benefit_accepted"
        ),
        "automatic_rollbacks": result.get(
            "agent_reliability_auto_rollbacks"
        ),
        "selective_rollbacks": result.get(
            "agent_reliability_selective_rollbacks"
        ),
        "forced_final_verifications": result.get(
            "agent_reliability_forced_final_verifications"
        ),
        "evidence_alignment": result.get(
            "agent_reliability_evidence_alignment"
        ),
        "evidence_nudges": result.get("agent_reliability_evidence_nudges"),
        "submitted": result.get("agent_submitted"),
        "termination_reason": result.get("agent_terminated_reason"),
        "input_tokens": result.get("task_input_tokens"),
        "output_tokens": result.get("task_output_tokens"),
        "total_tokens": result.get("task_token_count"),
        "latency_seconds": result.get("task_inference_time"),
        "failure_mode": result.get("failure_mode"),
    }


def collect_rows(results_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for aggregate_path in sorted(results_root.rglob(RESULT_FILENAME)):
        aggregate = _load_json(aggregate_path)
        run_info = aggregate.get("run_info") or {}
        for result in aggregate.get("results") or []:
            if isinstance(result, dict):
                rows.append(_normalise_row(aggregate_path, result, run_info))
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("scenario_name") or ""),
            str(row.get("context_sampling") or ""),
            str(row.get("experiment_seed") or ""),
            str(row.get("run_directory") or ""),
        ),
    )


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _gate_label(row: dict[str, Any]) -> str:
    enabled = row.get("reliability_enabled")
    if not enabled:
        return "off"
    nbr = row.get("net_benefit_ratio")
    if nbr is None or (isinstance(nbr, str) and nbr.lower() == "strict"):
        return "strict"
    try:
        label = f"nb{float(nbr):.1f}"
    except (TypeError, ValueError):
        label = "on"
    if str(row.get("evidence_alignment")).lower() == "true":
        label += "+evidence"
    return label


def _markdown_value(row: dict[str, Any], field: str) -> str:
    value: Any
    if field == "fix_rate_display":
        rate = row.get("fix_rate")
        value = f"{100 * rate:.1f}%" if isinstance(rate, (int, float)) else ""
    elif field == "latency_display":
        latency = row.get("latency_seconds")
        value = f"{latency:.1f}" if isinstance(latency, (int, float)) else ""
    elif field == "gate_label":
        value = _gate_label(row)
    elif field == "diagnosis_label":
        value = (
            f"on ({row.get('diagnosis_followed')})"
            if row.get("diagnosis_enabled") else "off"
        )
    else:
        value = row.get(field)
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [header for header, _ in MARKDOWN_FIELDS]
    lines = [
        "# Experiment Summary",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [_markdown_value(row, field) for _, field in MARKDOWN_FIELDS]
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results_root",
        nargs="?",
        type=Path,
        default=Path("results_main"),
        help="Directory to search recursively (default: results_main)",
    )
    parser.add_argument("--csv", dest="csv_path", type=Path)
    parser.add_argument("--markdown", dest="markdown_path", type=Path)
    args = parser.parse_args()

    rows = collect_rows(args.results_root)
    if not rows:
        parser.error(f"No {RESULT_FILENAME} files found under {args.results_root}")

    csv_path = args.csv_path or args.results_root / "experiment_summary.csv"
    markdown_path = (
        args.markdown_path
        or args.results_root / "experiment_summary.md"
    )
    write_csv(rows, csv_path)
    write_markdown(rows, markdown_path)
    print(f"Summarized {len(rows)} task results")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
