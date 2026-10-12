# Every failed check —139

27/144 A/A,22/144 guards and4/6 goals fail. Ten failed guards have passing
corresponding controls. All108 median controls pass; the27 identity failures
are13 whole p95 and14 setup p95 checks. P95 uses nearest-rank quantile ratios
(max with12/full or6/half samples); other metrics use within-round medians.
Every sample/stall remains; no selected retiming or gate change.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | wall_p95_ms | 0.076295 | FAIL / inconclusive |
| A/A | ordered | full | setup_p95_ms | 1.331868 | FAIL / inconclusive |
| A/A | ordered | first_half | setup_p95_ms | 1.417853 | FAIL / inconclusive |
| A/A | ordered | second_half | wall_p95_ms | 0.076295 | FAIL / inconclusive |
| A/A | clustered | full | wall_p95_ms | 0.235841 | FAIL / inconclusive |
| A/A | clustered | full | setup_p95_ms | 0.751718 | FAIL / inconclusive |
| A/A | clustered | first_half | wall_p95_ms | 2.007548 | FAIL / inconclusive |
| A/A | clustered | first_half | setup_p95_ms | 0.686200 | FAIL / inconclusive |
| A/A | clustered | second_half | wall_p95_ms | 0.115599 | FAIL / inconclusive |
| A/A | clustered | second_half | setup_p95_ms | 0.751718 | FAIL / inconclusive |
| A/A | interleaved | full | setup_p95_ms | 1.564169 | FAIL / inconclusive |
| A/A | interleaved | first_half | wall_p95_ms | 0.875463 | FAIL / inconclusive |
| A/A | interleaved | first_half | setup_p95_ms | 1.692003 | FAIL / inconclusive |
| A/A | interleaved | second_half | setup_p95_ms | 1.114810 | FAIL / inconclusive |
| A/A | duplicates | full | wall_p95_ms | 1.112095 | FAIL / inconclusive |
| A/A | duplicates | full | setup_p95_ms | 1.321774 | FAIL / inconclusive |
| A/A | duplicates | first_half | setup_p95_ms | 1.407441 | FAIL / inconclusive |
| A/A | duplicates | second_half | wall_p95_ms | 1.171386 | FAIL / inconclusive |
| A/A | late | full | wall_p95_ms | 0.176447 | FAIL / inconclusive |
| A/A | late | full | setup_p95_ms | 1.359127 | FAIL / inconclusive |
| A/A | late | first_half | wall_p95_ms | 0.156110 | FAIL / inconclusive |
| A/A | late | second_half | wall_p95_ms | 1.195571 | FAIL / inconclusive |
| A/A | late | second_half | setup_p95_ms | 1.359127 | FAIL / inconclusive |
| A/A | extreme | full | wall_p95_ms | 0.224549 | FAIL / inconclusive |
| A/A | extreme | full | setup_p95_ms | 0.691418 | FAIL / inconclusive |
| A/A | extreme | second_half | wall_p95_ms | 0.210738 | FAIL / inconclusive |
| A/A | extreme | second_half | setup_p95_ms | 0.689081 | FAIL / inconclusive |
| guard | ordered | full | setup_p95_ms | 1.737178 | FAIL / inconclusive |
| guard | ordered | first_half | wall_p95_ms | 2.869432 | pass |
| guard | ordered | first_half | setup_p95_ms | 1.849330 | FAIL / inconclusive |
| guard | clustered | first_half | wall_p95_ms | 1.327586 | FAIL / inconclusive |
| guard | interleaved | full | wall_p95_ms | 8.838029 | pass |
| guard | interleaved | full | setup_p95_ms | 1.459211 | FAIL / inconclusive |
| guard | interleaved | first_half | prepare_ms | 1.115131 | pass |
| guard | interleaved | second_half | wall_p95_ms | 8.838029 | pass |
| guard | interleaved | second_half | setup_p95_ms | 1.459211 | FAIL / inconclusive |
| guard | duplicates | full | segment_write_ms | 1.129926 | pass |
| guard | duplicates | full | wall_p95_ms | 1.140886 | FAIL / inconclusive |
| guard | duplicates | full | setup_p95_ms | 1.445442 | FAIL / inconclusive |
| guard | duplicates | first_half | segment_write_ms | 1.179519 | pass |
| guard | duplicates | first_half | wall_p95_ms | 1.106621 | pass |
| guard | duplicates | first_half | setup_p95_ms | 1.539124 | FAIL / inconclusive |
| guard | duplicates | second_half | wall_p95_ms | 1.201712 | FAIL / inconclusive |
| guard | late | full | setup_p95_ms | 1.765831 | FAIL / inconclusive |
| guard | late | first_half | prepare_ms | 1.141997 | pass |
| guard | late | first_half | setup_p95_ms | 1.903822 | pass |
| guard | extreme | full | setup_p95_ms | 1.193731 | FAIL / inconclusive |
| guard | extreme | first_half | setup_p95_ms | 1.725856 | pass |
| guard | extreme | second_half | setup_p95_ms | 1.193731 | FAIL / inconclusive |
| goal | clustered | full | wall_ms | 1.015301 | pass |
| goal | clustered | full | prepare_ms | 0.900763 | pass |
| goal | clustered | first_half | wall_ms | 1.055992 | pass |
| goal | clustered | first_half | prepare_ms | 1.011254 | pass |
