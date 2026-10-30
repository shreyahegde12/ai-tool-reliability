# Experiment Summary

| Metadata | Scenario | Method | Gate | Diagnosis | Run | Seed | Routers | Repaired | Evaluated | Repair rate | Regressions | Steps | Verifications | Tokens | Latency (s) | Complete | Termination |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_missing_context_metadata | Task-2 | random | off | off |  |  |  | 0 | 402 | 0.0% | 0 | 12 | 1 | 101401 | 40.3 | False | max_steps_reached |
| legacy_missing_context_metadata | Task-2 | random | off | off |  |  |  |  |  | 0.0% |  | 2 | 0 | 50304 | 18.7 | False | submitted |
| legacy_missing_context_metadata | Task-2 | spec_dependency | off | off |  |  |  | 39 | 402 | 9.7% | 0 | 12 | 4 | 107109 | 138.5 | False | max_steps_reached |
| legacy_missing_context_metadata | Task-2 | spec_dependency | off | off |  |  |  |  |  | 0.0% |  | 2 | 0 | 49524 | 17.6 | False | submitted |
| complete | scenario-003 | spec_dependency | off | off | s003-dependency-diagoff-diagab-v1 | 42 | 5 | 0 | 402 | 0.0% | 0 | 20 | 1 | 158603 | 83.2 | False | max_steps_reached |
| complete | scenario-003 | spec_dependency | off | on (followed) | s003-dependency-diagon-diagab-v1 | 42 | 5 | 402 | 402 | 100.0% | 0 | 8 | 1 | 82398 | 28.5 | True | submitted |
| complete | scenario-003 | spec_dependency | off | off | s003-dependency-diagoff-diagab-v1 | 43 | 5 | 0 | 402 | 0.0% | 0 | 20 | 4 | 204410 | 121.6 | False | max_steps_reached |
| complete | scenario-003 | spec_dependency | off | on (followed) | s003-dependency-diagon-diagab-v1 | 43 | 5 | 402 | 402 | 100.0% | 0 | 10 | 1 | 92556 | 53.7 | True | submitted |
| complete | scenario-003 | spec_dependency | off | off | s003-dependency-diagoff-diagab-v1 | 44 | 5 | 38 | 402 | 9.5% | 0 | 20 | 4 | 176117 | 100.9 | False | max_steps_reached |
| complete | scenario-003 | spec_dependency | off | on (followed) | s003-dependency-diagon-diagab-v1 | 44 | 5 | 402 | 402 | 100.0% | 0 | 10 | 1 | 91685 | 40.9 | True | submitted |
| complete | scenario-006 | random | strict | off | s006-random-gatev2-r1 | 42 | 13 | 0 | 83 | 0.0% | 0 | 12 | 2 | 60840 | 48.2 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-r1 | 42 | 13 |  |  | 0.0% |  | 12 | 0 | 63506 | 18.0 | False | max_steps_reached |
| complete | scenario-006 | random | nb1.0 | off | s006-ran-nb1.0-val | 42 | 13 | 0 | 83 | 0.0% | 0 | 20 | 3 | 123819 | 64.9 | False | max_steps_reached |
| complete | scenario-006 | random | nb1.0 | off | s006-random-nb1.0-scoreguard-v2-seed42 | 42 | 13 | 0 | 83 | 0.0% | 0 | 20 | 3 | 97336 | 65.7 | False | max_steps_reached |
| complete | scenario-006 | random | strict | off | s006-random-gatev2-r2 | 43 | 18 | 0 | 83 | 0.0% | 0 | 12 | 2 | 54868 | 32.1 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-r2 | 43 | 18 | 1 | 83 | 1.2% | 0 | 12 | 2 | 48132 | 65.3 | False | max_steps_reached |
| complete | scenario-006 | random | strict | off | s006-random-gatev2-r3 | 44 | 18 | 1 | 83 | 1.2% | 0 | 12 | 4 | 52203 | 43.4 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-r3 | 44 | 18 | 0 | 83 | 0.0% | 0 | 12 | 2 | 56963 | 65.5 | False | max_steps_reached |
| complete | scenario-006 | random | strict | off | s006-random-gate-r4 | 45 | 17 | 3 | 83 | 3.6% | 0 | 12 | 2 | 53922 | 64.3 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-nogate-r4 | 45 | 17 | 0 | 83 | 0.0% | 0 | 12 | 1 | 49586 | 41.9 | False | max_steps_reached |
| complete | scenario-006 | random | strict | off | s006-random-gate-r5 | 46 | 17 | 0 | 83 | 0.0% | 0 | 12 | 2 | 55498 | 68.7 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-nogate-r5 | 46 | 17 | 2 | 88 | 2.3% | 5 | 12 | 1 | 53773 | 45.7 | False | max_steps_reached |
| complete | scenario-006 | random | strict | off | s006-random-gate-r6 | 47 | 18 | 4 | 83 | 4.8% | 0 | 12 | 0 | 55184 | 17.5 | False | max_steps_reached |
| complete | scenario-006 | random | off | off | s006-random-nogate-r6 | 47 | 18 | 3 | 83 | 3.6% | 0 | 12 | 2 | 48256 | 67.8 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-dependency-gatev2-r1 | 42 | 13 | 0 | 83 | 0.0% | 0 | 12 | 4 | 50713 | 34.2 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-r1 | 42 | 13 | 0 | 83 | 0.0% | 0 | 12 | 1 | 57692 | 46.4 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-diagoff-diagab-v1 | 42 | 13 | 4 | 83 | 4.8% | 0 | 20 | 4 | 98534 | 52.9 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | on (ignored) | s006-dependency-diagon-diagab-v1 | 42 | 13 | 4 | 83 | 4.8% | 0 | 20 | 3 | 94442 | 55.5 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | nb1.0 | off | s006-dependency-nb1.0-scoreguard-v2-seed42 | 42 | 13 | 1 | 83 | 1.2% | 0 | 20 | 5 | 109160 | 54.9 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | nb1.0 | off | s006-nb1.0-final-s42 | 42 | 13 | 3 | 83 | 3.6% | 0 | 20 | 5 | 105453 | 49.1 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | nb1.0 | off | s006-spe-nb1.0-val | 42 | 13 | 0 | 83 | 0.0% | 0 | 20 | 1 | 109331 | 58.4 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-strict-final-s42 | 42 | 13 | 6 | 83 | 7.2% | 0 | 20 | 4 | 98551 | 47.3 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-dependency-gatev2-r2 | 43 | 13 | 0 | 83 | 0.0% | 0 | 12 | 1 | 51045 | 28.8 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-r2 | 43 | 13 | 0 | 83 | 0.0% | 0 | 12 | 1 | 48443 | 42.8 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-diagoff-diagab-v1 | 43 | 13 | 0 | 83 | 0.0% | 0 | 20 | 3 | 109792 | 57.7 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | on (ignored) | s006-dependency-diagon-diagab-v1 | 43 | 13 | 0 | 83 | 0.0% | 0 | 20 | 4 | 97879 | 50.2 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | nb1.0 | off | s006-nb1.0-final-s43 | 43 | 13 | 0 | 83 | 0.0% | 0 | 20 | 3 | 98181 | 39.4 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-strict-final-s43 | 43 | 13 | 43 | 83 | 51.8% | 0 | 20 | 3 | 77041 | 36.0 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-dependency-gatev2-r3 | 44 | 13 | 0 | 83 | 0.0% | 0 | 12 | 3 | 47107 | 43.4 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-r3 | 44 | 13 | 0 | 83 | 0.0% | 0 | 12 | 2 | 63174 | 59.2 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | off | s006-dependency-diagoff-diagab-v1 | 44 | 13 | 2 | 822 | 0.2% | 739 | 20 | 4 | 116312 | 60.7 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | off | on (followed) | s006-dependency-diagon-diagab-v1 | 44 | 13 | 3 | 124 | 2.4% | 41 | 20 | 4 | 96735 | 54.6 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | nb1.0 | off | s006-nb1.0-final-s44 | 44 | 13 | 0 | 83 | 0.0% | 0 | 20 | 5 | 120373 | 43.8 | False | max_steps_reached |
| complete | scenario-006 | spec_dependency | strict | off | s006-strict-final-s44 | 44 | 13 | 3 | 83 | 3.6% | 0 | 20 | 4 | 103509 | 40.3 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gatev2-r1 | 42 | 22 | 0 | 68 | 0.0% | 0 | 12 | 3 | 44529 | 38.6 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-r1 | 42 | 22 | 23 | 152 | 15.1% | 84 | 12 | 1 | 44271 | 44.8 | False | max_steps_reached |
| complete | scenario-008 | random | nb1.0 | off | s008-ran-nb1.0-val | 42 | 22 | 0 | 68 | 0.0% | 0 | 20 | 2 | 80305 | 58.7 | False | max_steps_reached |
| complete | scenario-008 | random | nb1.0 | off | s008-random-nb1.0-r1 | 42 | 22 | 0 | 68 | 0.0% | 0 | 20 | 4 | 82164 | 53.0 | False | max_steps_reached |
| complete | scenario-008 | random | nb1.0 | off | s008-random-nb1.0-scoreguard-v2-seed42 | 42 | 22 | 0 | 68 | 0.0% | 0 | 19 | 3 | 72256 | 42.9 | False | submitted |
| complete | scenario-008 | random | nb2.0 | off | s008-random-nb2.0-r1 | 42 | 22 | 0 | 68 | 0.0% | 0 | 20 | 5 | 80146 | 58.0 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-off-r1 | 42 | 22 | 29 | 752 | 3.9% | 684 | 20 | 2 | 78169 | 54.8 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-strict-r1 | 42 | 22 | 0 | 68 | 0.0% | 0 | 20 | 4 | 82025 | 53.8 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gatev2-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 12 | 3 | 43375 | 35.0 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 12 | 1 | 42455 | 37.6 | False | max_steps_reached |
| complete | scenario-008 | random | nb1.0 | off | s008-random-nb1.0-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 20 | 3 | 82621 | 50.7 | False | max_steps_reached |
| complete | scenario-008 | random | nb2.0 | off | s008-random-nb2.0-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 20 | 6 | 78851 | 59.6 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-off-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 20 | 0 | 70207 | 36.7 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-strict-r2 | 43 | 20 | 0 | 68 | 0.0% | 0 | 20 | 5 | 79683 | 56.0 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gatev2-r3 | 44 | 23 | 0 | 68 | 0.0% | 0 | 12 | 6 | 39069 | 46.1 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-r3 | 44 | 23 | 0 | 68 | 0.0% | 0 | 12 | 1 | 41737 | 39.3 | False | max_steps_reached |
| complete | scenario-008 | random | nb1.0 | off | s008-random-nb1.0-r3 | 44 | 23 | 4 | 69 | 5.8% | 1 | 20 | 7 | 73973 | 59.2 | False | max_steps_reached |
| complete | scenario-008 | random | nb2.0 | off | s008-random-nb2.0-r3 | 44 | 23 | 0 | 68 | 0.0% | 0 | 20 | 2 | 78313 | 45.0 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-off-r3 | 44 | 23 | 0 | 68 | 0.0% | 0 | 20 | 2 | 73324 | 41.5 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-strict-r3 | 44 | 23 | 0 | 68 | 0.0% | 0 | 20 | 8 | 78762 | 69.0 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gate-r4 | 45 | 20 | 0 | 68 | 0.0% | 0 | 12 | 2 | 41549 | 71.6 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-nogate-r4 | 45 | 20 |  |  | 0.0% |  | 12 | 1 | 46475 | 50.3 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gate-r5 | 46 | 23 | 0 | 68 | 0.0% | 0 | 12 | 2 | 43219 | 70.8 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-nogate-r5 | 46 | 23 | 0 | 68 | 0.0% | 0 | 12 | 2 | 44102 | 74.3 | False | max_steps_reached |
| complete | scenario-008 | random | strict | off | s008-random-gate-r6 | 47 | 23 |  |  | 0.0% |  | 12 | 1 | 42303 | 45.3 | False | max_steps_reached |
| complete | scenario-008 | random | off | off | s008-random-nogate-r6 | 47 | 23 | 0 | 68 | 0.0% | 0 | 12 | 1 | 44140 | 49.6 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-gatev2-r1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 12 | 2 | 43773 | 32.9 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-r1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 12 | 2 | 46045 | 65.8 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dep-nb1.0-diag-s42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 1 | 70352 | 39.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dep-off-diag-s42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 4 | 93086 | 52.7 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dep-strict-diag-s42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 5 | 91166 | 54.1 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-diagoff-diagab-v1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 3 | 81172 | 62.0 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | on (followed) | s008-dependency-diagon-diagab-v1 | 42 | 18 | 68 | 68 | 100.0% | 0 | 4 | 1 | 6838 | 8.9 | True | submitted |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dependency-nb1.0-r1 | 42 | 18 | 68 | 68 | 100.0% | 0 | 13 | 1 | 45195 | 27.1 | True | submitted |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dependency-nb1.0-scoreguard-smoke-r1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 6 | 84374 | 81.6 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dependency-nb1.0-scoreguard-v2-seed42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 4 | 92769 | 51.9 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dependency-nb1.0-test | 42 | 18 | 68 | 68 | 100.0% | 0 | 20 | 8 | 89016 | 79.1 | True | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb2.0 | off | s008-dependency-nb2.0-test | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 4 | 80411 | 70.6 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-off-r1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 0 | 78206 | 43.4 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-off-test | 42 | 18 | 65 | 68 | 95.6% | 0 | 20 | 3 | 75478 | 64.8 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-strict-r1 | 42 | 18 | 68 | 68 | 100.0% | 0 | 5 | 1 | 15290 | 11.4 | True | submitted |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-strict-scoreguard-smoke-r1 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 7 | 86613 | 140.7 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-strict-test | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 5 | 83346 | 54.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-nb1.0-final-s42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 6 | 1 | 20470 | 1890.1 | False | timeout |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-spe-nb1.0-val | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 3 | 78028 | 69.4 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-strict-final-s42 | 42 | 18 | 0 | 68 | 0.0% | 0 | 20 | 6 | 87073 | 49.1 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-gatev2-r2 | 43 | 18 | 0 | 68 | 0.0% | 0 | 12 | 2 | 45435 | 31.7 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-r2 | 43 | 18 | 68 | 68 | 100.0% | 0 | 5 | 1 | 15415 | 25.9 | True | submitted |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dep-nb1.0-diag-s43 | 43 | 18 | 0 | 68 | 0.0% | 0 | 20 | 3 | 90520 | 50.5 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dep-off-diag-s43 | 43 | 18 | 63 | 267 | 23.6% | 199 | 20 | 5 | 85905 | 50.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dep-strict-diag-s43 | 43 | 18 | 26 | 68 | 38.2% | 0 | 20 | 4 | 73408 | 49.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-diagoff-diagab-v1 | 43 | 18 | 0 | 68 | 0.0% | 0 | 20 | 2 | 69565 | 48.7 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | on (followed) | s008-dependency-diagon-diagab-v1 | 43 | 18 | 68 | 68 | 100.0% | 0 | 4 | 1 | 6752 | 8.9 | True | submitted |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-off-r2 | 43 | 18 | 0 | 68 | 0.0% | 0 | 20 | 2 | 84382 | 48.4 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-strict-r2 | 43 | 18 | 67 | 68 | 98.5% | 0 | 20 | 3 | 80985 | 54.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-nb1.0-final-s43 | 43 | 18 | 0 | 68 | 0.0% | 0 | 20 | 2 | 79727 | 41.6 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-strict-final-s43 | 43 | 18 | 0 | 68 | 0.0% | 0 | 20 | 1 | 81891 | 49.2 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-gatev2-r3 | 44 | 18 | 24 | 68 | 35.3% | 0 | 12 | 2 | 41031 | 31.0 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-r3 | 44 | 18 | 0 | 68 | 0.0% | 0 | 12 | 3 | 46255 | 91.6 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-dep-nb1.0-diag-s44 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 2 | 82389 | 41.3 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dep-off-diag-s44 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 3 | 82302 | 41.9 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dep-strict-diag-s44 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 3 | 80964 | 46.8 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-diagoff-diagab-v1 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 0 | 87586 | 48.5 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | off | on (followed) | s008-dependency-diagon-diagab-v1 | 44 | 18 | 68 | 68 | 100.0% | 0 | 4 | 1 | 6830 | 9.7 | True | submitted |
| complete | scenario-008 | spec_dependency | off | off | s008-dependency-off-r3 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 2 | 75536 | 45.2 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-dependency-strict-r3 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 8 | 87964 | 69.0 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | nb1.0 | off | s008-nb1.0-final-s44 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 7 | 81889 | 46.5 | False | max_steps_reached |
| complete | scenario-008 | spec_dependency | strict | off | s008-strict-final-s44 | 44 | 18 | 0 | 68 | 0.0% | 0 | 20 | 5 | 86378 | 44.9 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gatev2-r1 | 42 | 21 | 0 | 14 | 0.0% | 0 | 12 | 3 | 33485 | 28.3 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-r1 | 42 | 21 | 5 | 15 | 33.3% | 1 | 12 | 3 | 31936 | 76.4 | False | max_steps_reached |
| complete | scenario-009 | random | nb1.0 | off | s009-ran-nb1.0-val | 42 | 21 | 5 | 15 | 33.3% | 1 | 20 | 8 | 61091 | 63.7 | False | max_steps_reached |
| complete | scenario-009 | random | nb1.0 | off | s009-random-nb1.0-scoreguard-v2-seed42 | 42 | 21 | 5 | 15 | 33.3% | 1 | 20 | 6 | 67314 | 49.5 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gatev2-r2 | 43 | 21 |  |  | 0.0% |  | 12 | 7 | 30317 | 36.7 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-r2 | 43 | 21 | 5 | 15 | 33.3% | 1 | 12 | 3 | 32775 | 79.6 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gatev2-r3 | 44 | 21 |  |  | 0.0% |  | 12 | 6 | 32882 | 36.3 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-r3 | 44 | 21 | 5 | 15 | 33.3% | 1 | 12 | 3 | 29519 | 65.9 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gate-r4 | 45 | 21 | 0 | 14 | 0.0% | 0 | 12 | 1 | 34772 | 37.3 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-nogate-r4 | 45 | 21 | 5 | 15 | 33.3% | 1 | 12 | 0 | 29957 | 19.3 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gate-r5 | 46 | 21 |  |  | 0.0% |  | 12 | 1 | 30338 | 37.7 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-nogate-r5 | 46 | 21 | 12 | 86 | 14.0% | 72 | 12 | 0 | 33238 | 23.0 | False | max_steps_reached |
| complete | scenario-009 | random | strict | off | s009-random-gate-r6 | 47 | 21 | 14 | 51 | 27.5% | 37 | 12 | 0 | 31662 | 17.8 | False | max_steps_reached |
| complete | scenario-009 | random | off | off | s009-random-nogate-r6 | 47 | 21 | 14 | 92 | 15.2% | 78 | 12 | 0 | 30848 | 18.5 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-dependency-gatev2-r1 | 42 | 19 | 0 | 14 | 0.0% | 0 | 12 | 5 | 28464 | 32.7 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-r1 | 42 | 19 | 5 | 14 | 35.7% | 0 | 12 | 0 | 32867 | 19.5 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-diagoff-diagab-v1 | 42 | 19 | 5 | 15 | 33.3% | 1 | 20 | 1 | 58494 | 37.3 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | on (followed) | s009-dependency-diagon-diagab-v1 | 42 | 19 | 9 | 14 | 64.3% | 0 | 20 | 6 | 76197 | 53.4 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | nb1.0 | off | s009-dependency-nb1.0-scoreguard-v2-seed42 | 42 | 19 | 5 | 15 | 33.3% | 1 | 20 | 6 | 61250 | 45.3 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | nb1.0 | off | s009-nb1.0-final-s42 | 42 | 19 | 5 | 15 | 33.3% | 1 | 20 | 9 | 65466 | 47.5 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | nb1.0 | off | s009-spe-nb1.0-val | 42 | 19 | 14 | 18 | 77.8% | 4 | 20 | 8 | 68692 | 69.9 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-strict-final-s42 | 42 | 19 | 5 | 14 | 35.7% | 0 | 20 | 3 | 65021 | 36.4 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-dependency-gatev2-r2 | 43 | 19 | 0 | 14 | 0.0% | 0 | 12 | 7 | 29750 | 35.2 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-r2 | 43 | 19 | 5 | 14 | 35.7% | 0 | 12 | 1 | 28761 | 30.2 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-diagoff-diagab-v1 | 43 | 19 | 12 | 65 | 18.5% | 51 | 20 | 2 | 68325 | 46.2 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | on (followed) | s009-dependency-diagon-diagab-v1 | 43 | 19 | 9 | 14 | 64.3% | 0 | 20 | 6 | 74333 | 49.1 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | nb1.0 | off | s009-nb1.0-final-s43 | 43 | 19 | 5 | 15 | 33.3% | 1 | 20 | 10 | 61364 | 45.9 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-strict-final-s43 | 43 | 19 | 5 | 14 | 35.7% | 0 | 20 | 6 | 64289 | 41.7 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-dependency-gatev2-r3 | 44 | 19 | 0 | 14 | 0.0% | 0 | 12 | 2 | 40146 | 26.9 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-r3 | 44 | 19 | 5 | 14 | 35.7% | 0 | 12 | 0 | 33250 | 18.8 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | off | s009-dependency-diagoff-diagab-v1 | 44 | 19 | 5 | 14 | 35.7% | 0 | 20 | 4 | 61962 | 45.2 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | off | on (followed) | s009-dependency-diagon-diagab-v1 | 44 | 19 | 9 | 14 | 64.3% | 0 | 20 | 6 | 75616 | 49.7 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | nb1.0 | off | s009-nb1.0-final-s44 | 44 | 19 | 5 | 15 | 33.3% | 1 | 20 | 10 | 66793 | 46.4 | False | max_steps_reached |
| complete | scenario-009 | spec_dependency | strict | off | s009-strict-final-s44 | 44 | 19 | 0 | 14 | 0.0% | 0 | 20 | 7 | 58107 | 36.8 | False | max_steps_reached |
| complete | scenario-031 | spec_dependency | off | off | s031-dependency-diagoff-heldout-v1 | 42 | 7 | 0 | 138 | 0.0% | 0 | 20 | 2 | 121150 | 90.9 | False | max_steps_reached |
| complete | scenario-031 | spec_dependency | off | on (followed) | s031-dependency-diagon-heldout-v1 | 42 | 7 | 138 | 138 | 100.0% | 0 | 5 | 1 | 26848 | 33.8 | True | submitted |
| complete | scenario-035 | spec_dependency | off | off | s035-dependency-diagoff-heldout-v1 | 42 | 10 | 0 | 46 | 0.0% | 0 | 20 | 2 | 81605 | 51.1 | False | max_steps_reached |
| complete | scenario-035 | spec_dependency | off | on (no_finding) | s035-dependency-diagon-heldout-v1 | 42 | 10 | 46 | 46 | 100.0% | 0 | 17 | 1 | 75809 | 34.9 | True | submitted |
| complete | scenario-062 | spec_dependency | off | off | s062-dependency-diagoff-heldout-v1 | 42 | 6 | 0 | 1182 | 0.0% | 0 | 20 | 7 | 171754 | 107.6 | False | max_steps_reached |
| complete | scenario-062 | spec_dependency | off | on (ignored) | s062-dependency-diagon-heldout-v1 | 42 | 6 | 0 | 1198 | 0.0% | 16 | 20 | 2 | 191229 | 103.6 | False | max_steps_reached |
| complete | scenario-086 | spec_dependency | off | off | s086-dependency-diagoff-heldout-v1 | 42 | 7 | 8 | 317 | 2.5% | 0 | 20 | 4 | 130478 | 580.8 | False | max_steps_reached |
| complete | scenario-086 | spec_dependency | off | on (ignored) | s086-dependency-diagon-heldout-v1 | 42 | 7 | 0 | 317 | 0.0% | 0 | 20 | 1 | 245829 | 110.7 | False | max_steps_reached |
| complete | scenario-133 | spec_dependency | off | off | s133-dependency-diagoff-heldout-v1 | 42 | 2 | 0 | 1271 | 0.0% | 0 | 20 | 1 | 187389 | 62.3 | False | max_steps_reached |
| complete | scenario-133 | spec_dependency | off | on (followed) | s133-dependency-diagon-heldout-v1 | 42 | 2 | 0 | 1272 | 0.0% | 1 | 20 | 5 | 252356 | 109.0 | False | max_steps_reached |
| complete | scenario-136 | spec_dependency | off | off | s136-dependency-diagoff-heldout-v1 | 42 | 2 | 19 | 297 | 6.4% | 0 | 20 | 5 | 181768 | 76.1 | False | max_steps_reached |
| complete | scenario-136 | spec_dependency | off | on (followed) | s136-dependency-diagon-heldout-v1 | 42 | 2 | 257 | 297 | 86.5% | 0 | 20 | 2 | 234401 | 85.0 | False | max_steps_reached |
| complete | scenario-158 | spec_dependency | off | off | s158-dependency-diagoff-heldout-v1 | 42 | 5 | 0 | 2 | 0.0% | 0 | 20 | 6 | 90455 | 71.9 | False | max_steps_reached |
| complete | scenario-158 | spec_dependency | off | on (no_finding) | s158-dependency-diagon-heldout-v1 | 42 | 5 | 1 | 2 | 50.0% | 0 | 20 | 6 | 82107 | 76.7 | False | max_steps_reached |
| complete | scenario-170 | spec_dependency | off | off | s170-dependency-diagoff-heldout-v1 | 42 | 5 | 0 | 1000 | 0.0% | 0 | 20 | 3 | 207681 | 81.0 | False | max_steps_reached |
| complete | scenario-170 | spec_dependency | off | on (no_finding) | s170-dependency-diagon-heldout-v1 | 42 | 5 | 0 | 1000 | 0.0% | 0 | 19 | 3 | 189177 | 102.6 | False | submitted |
| complete | scenario-225 | spec_dependency | off | off | s225-dependency-diagoff-heldout-v1 | 42 | 4 | 2 | 126 | 1.6% | 0 | 20 | 4 | 123228 | 57.1 | False | max_steps_reached |
| complete | scenario-225 | spec_dependency | off | on (no_finding) | s225-dependency-diagon-heldout-v1 | 42 | 4 | 2 | 126 | 1.6% | 0 | 20 | 5 | 133219 | 67.9 | False | max_steps_reached |
| complete | scenario-231 | spec_dependency | off | off | s231-dependency-diagoff-heldout-v1 | 42 | 6 | 4 | 136 | 2.9% | 0 | 20 | 3 | 152493 | 111.2 | False | max_steps_reached |
| complete | scenario-231 | spec_dependency | off | on (followed) | s231-dependency-diagon-heldout-v1 | 42 | 6 | 136 | 136 | 100.0% | 0 | 20 | 5 | 129125 | 75.0 | True | submitted |
