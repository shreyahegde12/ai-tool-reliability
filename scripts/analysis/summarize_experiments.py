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
    "actions_rejected",
    "automatic_rollbacks",
    "selective_rollbacks",
    "forced_final_verifications",
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

    return {
        "run_directory": str(aggregate_path.parent),
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
        "actions_rejected": result.get(
            "agent_reliability_actions_rejected"
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


def _markdown_value(row: dict[str, Any], field: str) -> str:
    value: Any
    if field == "fix_rate_display":
        rate = row.get("fix_rate")
        value = f"{100 * rate:.1f}%" if isinstance(rate, (int, float)) else ""
    elif field == "latency_display":
        latency = row.get("latency_seconds")
        value = f"{latency:.1f}" if isinstance(latency, (int, float)) else ""
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
