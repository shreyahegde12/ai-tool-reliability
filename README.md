# Reliable Agentic Network Repair

An independent research project by Shreya Hegde for improving the reliability of LLM agents that diagnose and repair network configurations.

The central question is how to let an agent repair broken parts of a network without breaking the parts that already work. The harness wraps a ReAct-style repair agent in three deterministic layers:

1. **Dependency-aware retrieval** selects router configurations using violated specifications, prefix ownership, topology paths, waypoints and neighbouring routers. Routers flagged by the diagnosis can be added to the workspace when retrieval missed them.
2. **Deterministic diagnosis** runs rule-based cross-device consistency checks (BGP peering and ASNs, neighbor shutdown, link addressing, duplicate addresses, interface state, OSPF adjacency, prefix origination) and gives the agent ranked root-cause hypotheses with evidence. It uses only what the agent is allowed to see, never ground truth.
3. **Reliability gate** checks edits before execution, requires verification, accepts a patch only if it repairs more than it breaks (net-benefit rule), rolls back regressing patches selectively, forces a final verification, and pauses once before the agent patches a router the diagnosis did not flag.

Candidate repairs are evaluated against formal network-behaviour specifications using Batfish. This is experimental research software and is not intended for direct use on production networks.

## Design status

The harness design is frozen. Experiments compare:

- **Base agent:** the same agent, prompts, tools, model and budget with all three layers switched off (random context selection).
- **Full system:** all three layers switched on.

Both conditions use gpt-4o-mini, 20 steps, a 12k-token context cap, 1,200 output tokens and per-step verification, unless an experiment states otherwise.

## Repository highlights

- `src/utils/context_utils/dependency_retrieval.py`: dependency-aware router ranking and selection.
- `src/modules/diagnosis_engine.py`: deterministic fault localisation.
- `src/modules/reliability_controller.py`: pre-action checks, net-benefit acceptance, rollback and evidence nudge.
- `src/modules/MiniAgent.py`: agent and tool integration, patch checkpoints, verification and rollback.
- `scripts/benchmark/run_diagnosis_ablation.sh`: experiment runner for base agent, full system and ablations.
- `scripts/analysis/summarize_experiments.py`: CSV and Markdown result summaries.
- `scripts/analysis/diagnosis_benchmark.py`: offline fault-injection benchmark for the diagnosis (no LLM, no Batfish).
- `scripts/analysis/diagnosis_coverage.py`: how often the diagnosis finds something across all scenarios.
- `src/tests/`: unit tests for retrieval, diagnosis and reliability behaviour.

## Setup

Python 3.12 is recommended. Docker Desktop must be running for Batfish verification.

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add the required provider API key to `.env`, then download the public benchmark data:

```bash
python download_dataset.py
```

Start the customised Batfish container:

```bash
bash scripts/batfish_setup/pull_and_run_container.sh
```

## Tests

```bash
.venv312/bin/python -m unittest discover -s src/tests -t . -v
```

## Running experiments

Base agent on one scenario:

```bash
SCENARIOS="031" SEEDS="42" CONDITIONS=diagoff CONTEXT=random RUN_TAG=baseline-v1 \
  bash scripts/benchmark/run_diagnosis_ablation.sh
```

Full system on the same scenario:

```bash
SCENARIOS="031" SEEDS="42" CONDITIONS=diagon EXPAND=true GATE=1.0 EVIDENCE=true \
  RUN_TAG=heldout-full-v2 bash scripts/benchmark/run_diagnosis_ablation.sh
```

`GATE` takes `off`, `strict` or a net-benefit ratio; `PROVIDER`, `MODEL` and `EXTRA` select other models or pass further Hydra overrides. Each run writes to a unique directory derived from its run ID and seed, and existing results are skipped, so an interrupted batch can be restarted. Generated datasets, API credentials and experiment outputs are excluded from Git.

Summarise completed experiments with:

```bash
.venv312/bin/python scripts/analysis/summarize_experiments.py results_main
```

## Attribution and licence

This project builds on third-party open-source research software and benchmark data, including the Cornetto benchmark and its agent. Required attribution, upstream sources, citations and licence details are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The software is distributed under the MIT licence in [LICENSE](LICENSE).
