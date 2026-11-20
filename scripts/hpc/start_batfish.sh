#!/usr/bin/env bash
set -euo pipefail

# Start Batfish from the Apptainer image on the current node and wait until
# port 9996 answers. Batfish.setup() then reuses it instead of calling Docker.
#
# Sourced by the sbatch scripts; sets BATFISH_PID for cleanup.

SCRATCH_DIR="${SCRATCH_DIR:-${HOME}/hpc-scratch}"
SIF="${SCRATCH_DIR}/batfish.sif"
BF_DATA="${SCRATCH_DIR}/batfish-data/${SLURM_JOB_ID:-local}"
mkdir -p "${BF_DATA}"

if (exec 3<>/dev/tcp/127.0.0.1/9996) 2>/dev/null; then
  echo "Port 9996 already in use on $(hostname); another Batfish is running here." >&2
  exit 1
fi

apptainer run --pwd / --writable-tmpfs --bind "${BF_DATA}:/data" "${SIF}" \
  > "${BF_DATA}/batfish.log" 2>&1 &
BATFISH_PID=$!
trap 'kill ${BATFISH_PID} 2>/dev/null || true' EXIT

for _ in $(seq 1 120); do
  if (exec 3<>/dev/tcp/127.0.0.1/9996) 2>/dev/null; then
    echo "Batfish ready on $(hostname) after startup (log: ${BF_DATA}/batfish.log)"
    return 0 2>/dev/null || exit 0
  fi
  sleep 2
done

echo "Batfish did not start within 4 minutes; see ${BF_DATA}/batfish.log" >&2
exit 1
