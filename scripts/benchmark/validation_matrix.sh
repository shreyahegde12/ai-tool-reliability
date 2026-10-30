#!/bin/bash
set -euo pipefail

# Validation matrix: nb1.0 vs strict across scenarios and repeated runs.
# Default: 3 scenarios × 3 seeds × 1 retrieval × 2 gates = 18 runs.
# Set RETRIEVALS="random spec_dependency" for the full 36-run factorial.

PYTHON="${PYTHON:-.venv312/bin/python}"
SCENARIOS="${SCENARIOS:-006 008 009}"
SEEDS="${SEEDS:-42 43 44}"
RETRIEVALS="${RETRIEVALS:-spec_dependency}"
GATES="${GATES:-strict nb1.0}"
RUN_TAG="${RUN_TAG:-scoreguard-v1}"
LOG_DIR="${LOG_DIR:-matrix_logs/${RUN_TAG}}"
mkdir -p "$LOG_DIR"

total_runs=0
for scenario in $SCENARIOS; do
  for seed in $SEEDS; do
    for retrieval in $RETRIEVALS; do
      for gate in $GATES; do
        total_runs=$((total_runs + 1))
      done
    done
  done
done
current_run=0
failed_runs=0

echo "====================================="
echo "Net-Benefit Validation Matrix"
echo "====================================="
echo "Scenarios: $SCENARIOS"
echo "Seeds: $SEEDS"
echo "Retrievals: $RETRIEVALS"
echo "Gates: $GATES"
echo "Total: $total_runs runs"
echo "Run tag: $RUN_TAG"
echo "====================================="
echo ""

run_experiment() {
  local scenario=$1
  local seed=$2
  local retrieval=$3
  local gate=$4

  current_run=$((current_run + 1))

  case "$gate" in
    strict) nb_arg="strict" ;;
    nb1.0) nb_arg="1.0" ;;
  esac

  case "$retrieval" in
    random) ret_short="random" ;;
    spec_dependency) ret_short="dependency" ;;
    *) ret_short="$retrieval" ;;
  esac
  run_id="s${scenario}-${ret_short}-${gate}-${RUN_TAG}"
  log_file="${LOG_DIR}/${run_id}-seed-${seed}.log"

  echo "[$(date '+%H:%M:%S')] [$current_run/$total_runs] $run_id"

  if "$PYTHON" -m src.benchmark.zero_shot \
    --config-name agent_config \
    "data.scenario_filter=[\"scenario-${scenario}\"]" \
    "experiment.run_id=${run_id}" \
    "data.seed=${seed}" \
    model.provider=openai \
    model.model_name=gpt-4o-mini \
    model.max_tokens=1200 \
    "model.context_sampling=${retrieval}" \
    model.max_context_tokens=12000 \
    agentic.max_steps=20 \
    agentic.verification_mode=per_step \
    agentic.context_prefill=false \
    agentic.reliability.enabled=true \
    "agentic.reliability.net_benefit_ratio=${nb_arg}" \
    agentic.reliability.force_final_verification=true \
    agentic.reliability.selective_rollback=true \
    diagnosis_judge.enabled=false > "$log_file" 2>&1
  then
    echo "  ✓ ($log_file)"
  else
    echo "  ✗ FAILED (exit code $?, log: $log_file)"
    failed_runs=$((failed_runs + 1))
  fi
}

# Run matrix
for scenario in $SCENARIOS; do
  for seed in $SEEDS; do
    for retrieval in $RETRIEVALS; do
      for gate in $GATES; do
        run_experiment "$scenario" "$seed" "$retrieval" "$gate"
      done
    done
  done
done

echo ""
echo "====================================="
echo "Matrix Complete"
echo "====================================="
echo "Completed: $((total_runs - failed_runs))/$total_runs"
if [ $failed_runs -gt 0 ]; then
  echo "Failed: $failed_runs"
fi
echo ""
echo "Generating summary..."
"$PYTHON" scripts/analysis/summarize_experiments.py results_main > /dev/null
echo "✓ Results saved to results_main/experiment_summary.md"
echo ""
