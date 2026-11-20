#!/usr/bin/env bash
set -euo pipefail

# One-time setup on the Spartan login node.
#
# Creates the "cornetto" conda env (Python 3.12, CPU-only torch, no vllm)
# and pulls the Batfish image as an Apptainer SIF under scratch.
#
# Usage (from the project root on Spartan):
#   bash scripts/hpc/setup_env.sh

CONDA_BIN=/opt/Miniconda3/Miniconda3-py312_24.9.2-0-science/bin/conda
SCRATCH_DIR="${SCRATCH_DIR:-${HOME}/hpc-scratch}"
SIF="${SCRATCH_DIR}/batfish.sif"

eval "$("${CONDA_BIN}" shell.bash hook)"

if ! conda env list | grep -q '^cornetto '; then
  conda create -y -n cornetto python=3.12
fi
conda activate cornetto

# CPU torch only: the K40 GPUs are too old for current CUDA builds.
pip install --index-url https://download.pytorch.org/whl/cpu torch
grep -v -E '^(torch|vllm)' requirements.txt > /tmp/req-${USER}.txt
pip install -r /tmp/req-${USER}.txt
pip install -e . --no-deps

mkdir -p "${SCRATCH_DIR}"
if [ ! -f "${SIF}" ]; then
  apptainer pull "${SIF}" docker://iprotogeros/batfish-allione:forwarding-analysis-0.1
fi

echo "Done. Env: cornetto  Batfish image: ${SIF}"
