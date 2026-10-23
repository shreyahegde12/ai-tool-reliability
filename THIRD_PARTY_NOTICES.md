# Third-Party Notices

This repository contains modified software from the Cornetto network-configuration-repair benchmark.

## Cornetto

- Upstream repository: https://github.com/nsg-ethz/cornetto
- Original copyright: Copyright (c) 2025 Rufat Asadli
- Licence: MIT; the original copyright and permission notice are preserved in `LICENSE`.

Substantial additions in this repository include dependency-aware router retrieval, an action-reliability controller, patch checkpoints and rollback behavior, reproducible experiment bookkeeping, result reporting, and associated tests.

Research that uses the benchmark or dataset should cite the relevant upstream publications:

```bibtex
@misc{protogeros2026benchmarking,
  title={Benchmarking LLM-Driven Network Configuration Repair},
  author={Ioannis Protogeros and Rufat Asadli and Benjamin Hoffman and Laurent Vanbever},
  year={2026},
  eprint={2604.22513},
  archivePrefix={arXiv},
  primaryClass={cs.NI},
  url={https://arxiv.org/abs/2604.22513}
}

@misc{asadli2026evaluating,
  title={Evaluating Agentic Configuration Repair for Computer Networks},
  author={Rufat Asadli and Benjamin Hoffman and Ioannis Protogeros and Laurent Vanbever},
  year={2026},
  eprint={2606.06212},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2606.06212}
}
```

The Git history in this repository represents the development of this independent derivative project. It does not replace or alter the upstream project history, which remains available at the upstream repository above.
