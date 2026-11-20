#!/bin/bash
#SBATCH --job-name=cornetto-bench
#SBATCH -p nodes
#SBATCH -N 1
#SBATCH --exclusive
#SBATCH -t 12:00:00
#SBATCH -o logs/bench_%A_%a.out

# Full-stack benchmark on Spartan: dependency retrieval + diagnosis (prefill
# and expand_context) + reliability gate (net-benefit 1.0, evidence nudge),
# gpt-4o-mini, 20 steps, seed 42. Runs through run_diagnosis_ablation.sh so
# settings match our held-out runs.
#
# --exclusive: Batfish's port 9996 is fixed, so one job per node.
# Array tasks split the scenario list; finished runs are skipped on resubmit.
#
# One-scenario test:
#   sbatch --array=0 --export=ALL,SCENARIOS=231 scripts/hpc/benchmark.sbatch
# All 231 scenarios across 4 nodes:
#   sbatch --array=0-3 scripts/hpc/benchmark.sbatch

set -uo pipefail
cd "${SLURM_SUBMIT_DIR}"

eval "$(/opt/Miniconda3/Miniconda3-py312_24.9.2-0-science/bin/conda shell.bash hook)"
conda activate cornetto

source scripts/hpc/start_batfish.sh

ALL_SCENARIOS="${SCENARIOS:-$(ls dataset/main_dataset | sed 's/^scenario-//' | tr '\n' ' ')}"
TASK_ID="${SLURM_ARRAY_TASK_ID:-0}"
TASK_COUNT="${SLURM_ARRAY_TASK_COUNT:-1}"

# Round-robin split so large and small scenarios spread across tasks.
MY_SCENARIOS=""
i=0
for s in ${ALL_SCENARIOS}; do
  [ $((i % TASK_COUNT)) -eq "${TASK_ID}" ] && MY_SCENARIOS="${MY_SCENARIOS} ${s}"
  i=$((i + 1))
done
echo "Task ${TASK_ID}/${TASK_COUNT} on $(hostname): ${MY_SCENARIOS}"

PYTHON=python \
SCENARIOS="${MY_SCENARIOS}" \
SEEDS="42" \
CONDITIONS="diagon" \
CONTEXT=spec_dependency \
EXPAND=true \
GATE=1.0 \
EVIDENCE=true \
RUN_TAG="${RUN_TAG:-spartan-fullstack-v1}" \
LOG_DIR="matrix_logs/${RUN_TAG:-spartan-fullstack-v1}" \
bash scripts/benchmark/run_diagnosis_ablation.sh
