# Reliable Agentic Network Repair

An independent research project by Shreya Hegde for improving the reliability of LLM agents that diagnose and repair network configurations.

The project studies two complementary problems:

- **Dependency-aware retrieval** selects router configurations using violated specifications, prefix ownership, topology paths, waypoints, and neighboring routers.
- **Action reliability** checks configuration edits before execution, tracks patch outcomes, requires verification, and rolls back unsafe changes.

Candidate repairs are evaluated against formal network-behavior specifications using Batfish. This is experimental research software and is not intended for direct use on production networks.

## Current research questions

1. Can network-semantic retrieval expose more relevant configurations than random context selection?
2. Can an action-validation layer reduce regressions without preventing useful repairs?
3. How do retrieval and reliability interact across scenarios, seeds, and context budgets?

## Repository highlights

- `src/utils/context_utils/dependency_retrieval.py` — dependency-aware router ranking and selection.
- `src/modules/reliability_controller.py` — pre-action checks and post-verification recovery policy.
- `src/modules/MiniAgent.py` — agent/tool integration, patch checkpoints, verification, and rollback.
- `scripts/benchmark/run_reliability_v2_matrix.sh` — reproducible experiment matrix.
- `scripts/analysis/summarize_experiments.py` — CSV and Markdown result summaries.
- `src/tests/` — unit tests for retrieval and reliability behavior.

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

Start the customized Batfish container:

```bash
bash scripts/batfish_setup/pull_and_run_container.sh
```

## Tests

```bash
.venv312/bin/python -m unittest \
  src.tests.test_dependency_retrieval \
  src.tests.test_reliability_controller -v
```

## Example experiment

```bash
.venv312/bin/python -m src.benchmark.zero_shot \
  --config-name agent_config \
  'data.scenario_filter=["scenario-006"]' \
  experiment.run_id=s006-dependency-reliability-r1 \
  data.seed=42 \
  model.provider=openai \
  model.model_name=gpt-4o-mini \
  model.max_tokens=1200 \
  model.context_sampling=spec_dependency \
  model.max_context_tokens=12000 \
  agentic.max_steps=12 \
  agentic.verification_mode=per_step \
  agentic.context_prefill=false \
  agentic.reliability.enabled=true \
  diagnosis_judge.enabled=false
```

Each run uses a unique output directory derived from its run ID and seed. Generated datasets, API credentials, and experiment outputs are excluded from Git.

Summarize completed experiments with:

```bash
.venv312/bin/python scripts/analysis/summarize_experiments.py results_main
```

## Attribution and licence

This project builds on third-party open-source research software and benchmark data. Required attribution, upstream sources, citations, and licence details are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The software is distributed under the MIT licence in [LICENSE](LICENSE).
