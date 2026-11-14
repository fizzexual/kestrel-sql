# Every failed check —137

32/144 A/A,13/144 guards and6/6 speed goals fail. Five failed guards have
passing corresponding controls. Failed A/A makes that comparison inconclusive.
P95 uses nearest-rank quantile ratios (max with12/full or6/half samples); other
metrics use median within-round ratios. Every sample stayed; no selected retiming.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | wall_p95_ms | 8.751698 | FAIL / inconclusive |
| A/A | ordered | full | setup_p95_ms | 1.461516 | FAIL / inconclusive |
| A/A | ordered | first_half | setup_p95_ms | 1.461516 | FAIL / inconclusive |
| A/A | ordered | second_half | wall_p95_ms | 8.751698 | FAIL / inconclusive |
| A/A | ordered | second_half | setup_p95_ms | 1.348245 | FAIL / inconclusive |
| A/A | clustered | full | wall_p95_ms | 0.863278 | FAIL / inconclusive |
| A/A | clustered | full | setup_p95_ms | 0.884412 | FAIL / inconclusive |
| A/A | clustered | first_half | catalog_sync_ms | 0.892010 | FAIL / inconclusive |
| A/A | clustered | first_half | setup_p95_ms | 0.769621 | FAIL / inconclusive |
| A/A | clustered | second_half | wall_p95_ms | 0.856468 | FAIL / inconclusive |
| A/A | clustered | second_half | setup_p95_ms | 0.884412 | FAIL / inconclusive |
| A/A | interleaved | full | wall_p95_ms | 1.269219 | FAIL / inconclusive |
| A/A | interleaved | full | setup_p95_ms | 0.810568 | FAIL / inconclusive |
| A/A | interleaved | first_half | wall_p95_ms | 0.218863 | FAIL / inconclusive |
| A/A | interleaved | first_half | setup_p95_ms | 0.701486 | FAIL / inconclusive |
| A/A | interleaved | second_half | catalog_sync_ms | 1.144387 | FAIL / inconclusive |
| A/A | interleaved | second_half | wall_p95_ms | 3.278317 | FAIL / inconclusive |
| A/A | duplicates | full | wall_p95_ms | 1.320227 | FAIL / inconclusive |
| A/A | duplicates | full | setup_p95_ms | 1.274637 | FAIL / inconclusive |
| A/A | duplicates | second_half | wall_p95_ms | 1.320227 | FAIL / inconclusive |
| A/A | duplicates | second_half | setup_p95_ms | 1.274637 | FAIL / inconclusive |
| A/A | late | full | wall_p95_ms | 1.169820 | FAIL / inconclusive |
| A/A | late | first_half | wall_p95_ms | 1.169820 | FAIL / inconclusive |
| A/A | late | second_half | segment_write_ms | 1.124133 | FAIL / inconclusive |
| A/A | extreme | full | wall_p95_ms | 1.877437 | FAIL / inconclusive |
| A/A | extreme | full | setup_p95_ms | 1.747014 | FAIL / inconclusive |
| A/A | extreme | first_half | prepare_ms | 1.105930 | FAIL / inconclusive |
| A/A | extreme | first_half | segment_write_ms | 1.106409 | FAIL / inconclusive |
| A/A | extreme | first_half | wall_p95_ms | 0.877983 | FAIL / inconclusive |
| A/A | extreme | first_half | setup_p95_ms | 2.262230 | FAIL / inconclusive |
| A/A | extreme | second_half | catalog_sync_ms | 1.158947 | FAIL / inconclusive |
| A/A | extreme | second_half | wall_p95_ms | 2.171500 | FAIL / inconclusive |
| guard | ordered | full | setup_p95_ms | 1.354426 | FAIL / inconclusive |
| guard | ordered | first_half | setup_p95_ms | 1.354426 | FAIL / inconclusive |
| guard | clustered | second_half | segment_write_ms | 1.105898 | pass |
| guard | duplicates | first_half | catalog_sync_ms | 1.124759 | pass |
| guard | late | second_half | wall_p95_ms | 1.149104 | pass |
| guard | late | second_half | setup_p95_ms | 1.288084 | pass |
| guard | extreme | full | prepare_ms | 1.131144 | pass |
| guard | extreme | full | wall_p95_ms | 1.261574 | FAIL / inconclusive |
| guard | extreme | full | setup_p95_ms | 1.105027 | FAIL / inconclusive |
| guard | extreme | first_half | prepare_ms | 1.131144 | FAIL / inconclusive |
| guard | extreme | first_half | segment_write_ms | 1.156590 | FAIL / inconclusive |
| guard | extreme | first_half | wall_p95_ms | 1.261574 | FAIL / inconclusive |
| guard | extreme | first_half | setup_p95_ms | 1.430913 | FAIL / inconclusive |
| goal | clustered | full | wall_ms | 0.968549 | pass |
| goal | clustered | full | write_sync_ms | 0.957400 | pass |
| goal | clustered | first_half | wall_ms | 0.956605 | pass |
| goal | clustered | first_half | write_sync_ms | 0.975929 | pass |
| goal | clustered | second_half | wall_ms | 0.988157 | pass |
| goal | clustered | second_half | write_sync_ms | 0.955664 | pass |
