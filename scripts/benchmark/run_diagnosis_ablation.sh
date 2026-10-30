#!/usr/bin/env bash
set -uo pipefail

# Diagnosis ablation: deterministic diagnosis ON vs OFF, everything else fixed
# (dependency retrieval, reliability gate off, 20 steps, gpt-4o-mini).
# Default: 4 scenarios x 3 seeds x 2 conditions = 24 runs.

PYTHON="${PYTHON:-.venv312/bin/python}"
SCENARIOS="${SCENARIOS:-003 006 008 009}"
SEEDS="${SEEDS:-42 43 44}"
CONDITIONS="${CONDITIONS:-diagon diagoff}"
RUN_TAG="${RUN_TAG:-diagab-v1}"
LOG_DIR="${LOG_DIR:-matrix_logs/${RUN_TAG}}"
mkdir -p "$LOG_DIR"

run_one() {
  local scenario=$1 seed=$2 condition=$3
  local enabled=false
  [ "$condition" = "diagon" ] && enabled=true
  local run_id="s${scenario}-dependency-${condition}-${RUN_TAG}"
  local log_file="${LOG_DIR}/${run_id}-seed-${seed}.log"

  if ls results_main/zero_shot/*/*/*/*/*/"run-${run_id}-seed-${seed}"/zero_shot_benchmark_results.json \
      >/dev/null 2>&1; then
    echo "  skip (exists)"
    return 0
  fi

  "$PYTHON" -m src.benchmark.zero_shot \
    --config-name agent_config \
    "data.scenario_filter=[\"scenario-${scenario}\"]" \
    "experiment.run_id=${run_id}" \
    "data.seed=${seed}" \
    model.provider=openai \
    model.model_name=gpt-4o-mini \
    model.max_tokens=1200 \
    model.context_sampling=spec_dependency \
    model.max_context_tokens=12000 \
    agentic.max_steps=20 \
    agentic.verification_mode=per_step \
    agentic.context_prefill=false \
    agentic.reliability.enabled=false \
    "agentic.diagnosis.enabled=${enabled}" \
    agentic.diagnosis.prefill=true \
    diagnosis_judge.enabled=false > "$log_file" 2>&1
}

total=0; failed=0
for scenario in $SCENARIOS; do
  for seed in $SEEDS; do
    for condition in $CONDITIONS; do
      total=$((total + 1))
      echo "[$(date '+%H:%M:%S')] s${scenario} seed ${seed} ${condition}"
      if ! run_one "$scenario" "$seed" "$condition"; then
        echo "  failed once; retrying"
        sleep 20
        run_one "$scenario" "$seed" "$condition" || { echo "  FAILED"; failed=$((failed + 1)); }
      fi
    done
  done
done

echo "Done: $((total - failed))/${total} runs ok"
"$PYTHON" scripts/analysis/summarize_experiments.py results_main > /dev/null
