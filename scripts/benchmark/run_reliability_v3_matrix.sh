#!/usr/bin/env bash
set -euo pipefail

# Reliability V3 experiment matrix
#
# 4 conditions (gate_mode):
#   off      — no reliability gate
#   strict   — gate enabled, zero-tolerance rollback (v2 behaviour)
#   nb1.0    — gate enabled, net-benefit ratio 1.0 (fix >= regress)
#   nb2.0    — gate enabled, net-benefit ratio 2.0 (fix >= 2*regress)
#
# 3 scenarios × 3 seeds × 2 retrieval modes × 4 gate modes = 72 runs.
# Estimated cost: ~$3-5 with gpt-4o-mini at 12k context, 20 steps.
#
# Usage:
#   CORNETTO_PYTHON=.venv312/bin/python bash scripts/benchmark/run_reliability_v3_matrix.sh
#
# To run a subset, set SCENARIOS, SEEDS, or GATE_MODES:
#   SCENARIOS="008" GATE_MODES="off nb1.0" bash scripts/benchmark/run_reliability_v3_matrix.sh

CORNETTO_PYTHON="${CORNETTO_PYTHON:-.venv312/bin/python}"
MAX_STEPS="${MAX_STEPS:-20}"

SCENARIOS="${SCENARIOS:-006 008 009}"
SEEDS="${SEEDS:-42 43 44}"
CONTEXT_MODES="${CONTEXT_MODES:-random spec_dependency}"
GATE_MODES="${GATE_MODES:-off strict nb1.0 nb2.0}"

run_count=0

for scenario in ${SCENARIOS}; do
  for context_mode in ${CONTEXT_MODES}; do
    for gate_mode in ${GATE_MODES}; do
      run_number=1
      for seed in ${SEEDS}; do
        method_name="${context_mode/spec_dependency/dependency}"
        run_id="s${scenario}-${method_name}-${gate_mode}-r${run_number}"

        # Gate configuration
        case "${gate_mode}" in
          off)
            gate_args=(
              agentic.reliability.enabled=false
            )
            ;;
          strict)
            gate_args=(
              agentic.reliability.enabled=true
              agentic.reliability.force_final_verification=true
              agentic.reliability.selective_rollback=true
              "agentic.reliability.net_benefit_ratio=strict"
            )
            ;;
          nb*)
            ratio="${gate_mode#nb}"
            gate_args=(
              agentic.reliability.enabled=true
              agentic.reliability.force_final_verification=true
              agentic.reliability.selective_rollback=true
              "agentic.reliability.net_benefit_ratio=${ratio}"
            )
            ;;
          *)
            echo "Unknown gate mode: ${gate_mode}" >&2
            exit 1
            ;;
        esac

        echo "Starting ${run_id} (seed ${seed}, gate=${gate_mode})"
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
          "agentic.max_steps=${MAX_STEPS}" \
          agentic.verification_mode=per_step \
          agentic.context_prefill=false \
          "${gate_args[@]}" \
          diagnosis_judge.enabled=false

        run_number=$((run_number + 1))
        run_count=$((run_count + 1))
      done
    done
  done
done

echo "Completed ${run_count} runs."
echo "Regenerate summaries with:"
echo "  ${CORNETTO_PYTHON} scripts/analysis/summarize_experiments.py results_main"
