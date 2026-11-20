#!/bin/bash
#SBATCH --job-name=cornetto-smoke
#SBATCH -p nodes
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 00:30:00
#SBATCH -o logs/smoke_%j.out

# Smoke test: Batfish starts, Python imports work. No API calls (free).
# For real runs use benchmark.sbatch.

set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"

eval "$(/opt/Miniconda3/Miniconda3-py312_24.9.2-0-science/bin/conda shell.bash hook)"
conda activate cornetto

source scripts/hpc/start_batfish.sh

python -c "import src.benchmark.zero_shot, pybatfish; print('imports ok')"
python -c "from pybatfish.client.session import Session; Session(host='localhost'); print('batfish session ok')"

echo "Smoke test finished."
