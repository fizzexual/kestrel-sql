# Every failed check —141

20/144 A/A,15/144 guards and4/6 goals fail. Eight failed guards have passing
corresponding controls.107/108 median controls pass; one catalog-sync median,
four whole-p95 and15 setup-p95 controls fail. All full/both-half samples/stalls
remain. P95 uses nearest-rank quantile ratios (max with12/full or6/half samples);
other metrics use within-round medians. No selected retiming/gate change.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | setup_p95_ms | 0.812668 | FAIL / inconclusive |
| A/A | ordered | first_half | setup_p95_ms | 1.373047 | FAIL / inconclusive |
| A/A | ordered | second_half | setup_p95_ms | 0.812668 | FAIL / inconclusive |
| A/A | clustered | full | setup_p95_ms | 1.631682 | FAIL / inconclusive |
| A/A | clustered | second_half | setup_p95_ms | 1.717086 | FAIL / inconclusive |
| A/A | interleaved | full | wall_p95_ms | 3.121856 | FAIL / inconclusive |
| A/A | interleaved | full | setup_p95_ms | 1.145933 | FAIL / inconclusive |
| A/A | interleaved | first_half | setup_p95_ms | 0.686992 | FAIL / inconclusive |
| A/A | interleaved | second_half | wall_p95_ms | 3.121856 | FAIL / inconclusive |
| A/A | interleaved | second_half | setup_p95_ms | 1.156413 | FAIL / inconclusive |
| A/A | duplicates | first_half | setup_p95_ms | 0.857440 | FAIL / inconclusive |
| A/A | duplicates | second_half | setup_p95_ms | 1.652842 | FAIL / inconclusive |
| A/A | late | full | wall_p95_ms | 0.894549 | FAIL / inconclusive |
| A/A | late | full | setup_p95_ms | 0.679033 | FAIL / inconclusive |
| A/A | late | first_half | wall_p95_ms | 0.892923 | FAIL / inconclusive |
| A/A | late | first_half | setup_p95_ms | 0.630563 | FAIL / inconclusive |
| A/A | late | second_half | catalog_sync_ms | 0.868233 | FAIL / inconclusive |
| A/A | extreme | full | setup_p95_ms | 1.146285 | FAIL / inconclusive |
| A/A | extreme | first_half | setup_p95_ms | 0.678247 | FAIL / inconclusive |
| A/A | extreme | second_half | setup_p95_ms | 1.427458 | FAIL / inconclusive |
| guard | ordered | full | wall_p95_ms | 1.220788 | pass |
| guard | ordered | first_half | setup_p95_ms | 1.228970 | FAIL / inconclusive |
| guard | ordered | second_half | wall_p95_ms | 1.233860 | pass |
| guard | clustered | full | setup_p95_ms | 1.310442 | FAIL / inconclusive |
| guard | clustered | first_half | wall_p95_ms | 1.108987 | pass |
| guard | clustered | first_half | setup_p95_ms | 1.310442 | pass |
| guard | clustered | second_half | setup_p95_ms | 1.344005 | FAIL / inconclusive |
| guard | interleaved | full | setup_p95_ms | 1.139357 | FAIL / inconclusive |
| guard | interleaved | first_half | wall_p95_ms | 1.246244 | pass |
| guard | interleaved | second_half | setup_p95_ms | 1.149776 | FAIL / inconclusive |
| guard | duplicates | second_half | segment_write_ms | 1.111357 | pass |
| guard | late | full | wall_p95_ms | 6.133659 | FAIL / inconclusive |
| guard | late | first_half | catalog_sync_ms | 1.127993 | pass |
| guard | late | first_half | wall_p95_ms | 6.133659 | FAIL / inconclusive |
| guard | late | second_half | setup_p95_ms | 1.404614 | pass |
| goal | clustered | full | wall_ms | 0.979958 | pass |
| goal | clustered | first_half | wall_ms | 1.029144 | pass |
| goal | clustered | first_half | prepare_ms | 0.960609 | pass |
| goal | clustered | second_half | wall_ms | 0.978751 | pass |
