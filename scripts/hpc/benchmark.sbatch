#!/bin/bash
#SBATCH --job-name=cornetto-bench
#SBATCH -p nodes
#SBATCH -N 1
#SBATCH --exclusive
#SBATCH -t 12:00:00
#SBATCH -o logs/bench_%A_%a.out

# Main benchmark on Spartan: base agent vs full system, gpt-4o-mini, 20 steps,
# seed 42. Runs through run_diagnosis_ablation.sh with exactly the settings of
# the held-out runs.
#
#   MODE=base  random context, no layers (as baseline-v1)
#   MODE=full  dependency retrieval + diagnosis (prefill, expand) + gate
#              (net-benefit 1.0, evidence nudge) (as heldout-full-v2)
#
# By default the dev set (003 006 008 009), the held-out 10 (already run with
# 3 seeds) and scenarios without a 100pct spec file are excluded.
#
# --exclusive: Batfish's port 9996 is fixed, so one job per node.
# Array tasks split the scenario list; finished runs are skipped on resubmit.
#
# One-scenario test:
#   sbatch --array=0 --export=ALL,MODE=base,SCENARIOS=225 scripts/hpc/benchmark.sbatch
# Full set, both conditions, 4 nodes each:
#   sbatch --array=0-3 --export=ALL,MODE=base scripts/hpc/benchmark.sbatch
#   sbatch --array=0-3 --export=ALL,MODE=full scripts/hpc/benchmark.sbatch

set -uo pipefail
cd "${SLURM_SUBMIT_DIR}"

eval "$(/opt/Miniconda3/Miniconda3-py312_24.9.2-0-science/bin/conda shell.bash hook)"
conda activate cornetto

source scripts/hpc/start_batfish.sh

MODE="${MODE:?set MODE=base or MODE=full}"
case "${MODE}" in
  base) MODE_ENV=(CONDITIONS=diagoff CONTEXT=random EXPAND=false GATE=off EVIDENCE=false)
        RUN_TAG="${RUN_TAG:-fullset-base-v1}" ;;
  full) MODE_ENV=(CONDITIONS=diagon CONTEXT=spec_dependency EXPAND=true GATE=1.0 EVIDENCE=true)
        RUN_TAG="${RUN_TAG:-fullset-full-v1}" ;;
  *) echo "MODE must be base or full" >&2; exit 1 ;;
esac

EXCLUDE=" 003 006 008 009 031 035 062 086 133 136 158 170 225 231 "
default_scenarios() {
  for d in dataset/main_dataset/scenario-*; do
    s="${d##*scenario-}"
    [[ "${EXCLUDE}" == *" ${s} "* ]] && continue
    [ -f "${d}/specifications/specifications_100pct.csv" ] || continue
    printf '%s ' "${s}"
  done
}
ALL_SCENARIOS="${SCENARIOS:-$(default_scenarios)}"
TASK_ID="${SLURM_ARRAY_TASK_ID:-0}"
TASK_COUNT="${SLURM_ARRAY_TASK_COUNT:-1}"

# Round-robin split so large and small scenarios spread across tasks.
MY_SCENARIOS=""
i=0
for s in ${ALL_SCENARIOS}; do
  [ $((i % TASK_COUNT)) -eq "${TASK_ID}" ] && MY_SCENARIOS="${MY_SCENARIOS} ${s}"
  i=$((i + 1))
done
echo "Task ${TASK_ID}/${TASK_COUNT} ${MODE} on $(hostname): ${MY_SCENARIOS}"

env "${MODE_ENV[@]}" \
  PYTHON=python \
  SCENARIOS="${MY_SCENARIOS}" \
  SEEDS="${SEEDS:-42}" \
  RUN_TAG="${RUN_TAG}" \
  LOG_DIR="matrix_logs/${RUN_TAG}" \
  bash scripts/benchmark/run_diagnosis_ablation.sh
