#!/usr/bin/env bash
set -euo pipefail

# Matched Reliability V2 experiments:
#   3 scenarios x 3 seeds x 2 retrieval modes = 18 runs.
CORNETTO_PYTHON="${CORNETTO_PYTHON:-.venv312/bin/python}"

for scenario in 006 008 009; do
  for context_mode in random spec_dependency; do
    run_number=1
    for seed in 42 43 44; do
      method_name="${context_mode/spec_dependency/dependency}"
      run_id="s${scenario}-${method_name}-gatev2-r${run_number}"

      echo "Starting ${run_id} (seed ${seed})"
      "${CORNETTO_PYTHON}" -m src.benchmark.zero_shot \
        --config-name agent_config \
        "data.scenario_filter=[\"scenario-${scenario}\"]" \
        "experiment.run_id=${run_id}" \
        "data.seed=${seed}" \
        model.provider=openai \
        model.model_name=gpt-4o-mini \
        model.max_tokens=1200 \
        "model.context_sampling=${context_mode}" \
        model.max_context_tokens=12000 \
        agentic.max_steps=12 \
        agentic.verification_mode=per_step \
        agentic.context_prefill=false \
        agentic.reliability.enabled=true \
        agentic.reliability.force_final_verification=true \
        agentic.reliability.selective_rollback=true \
        diagnosis_judge.enabled=false

      run_number=$((run_number + 1))
    done
  done
done
