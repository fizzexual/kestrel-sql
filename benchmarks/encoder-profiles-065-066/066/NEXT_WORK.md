# Next engine experiment after encoder profiles 065/066

The original 065 calibration failure remains a failure. Separate 066 has twelve paired rounds and passes all 43 predeclared checks, using the same binary and thresholds. Its fixed-input reuse total ratios are 0.7888/0.7720 for 50,250/99,250 receipts. First encodes are slightly slower. These are serializer models, not engine speedups.

Start a new candidate from exact released 0.3.16, excluding failed fan-in 064, unqualified parser 061 and SDK 058/060. Compare a bounded writer-owned JSON buffer strategy, with exact existing stored bytes and synchronization. Fresh reservation with a conservative capacity estimate is also worth testing; the exact-size model's future-length oracle is not deployable.

Measure retained working set and peak commit under real growing catalogs. Avoid cloning the buffer into reader snapshots. Handle small deltas following large checkpoints and read-only/cold-open paths. Retaining 16 MiB indefinitely could offset CPU gains or fail memory guards; a model's peak counter does not establish an engine's memory bound.

Predeclare all metrics before the candidate's first timing. Verify escaped IDs, wide receipt counters, checkpoint/delta order, errors, reopen and generation-preserving retries. Run full differential/publication/source/reader recovery qualification before any native candidate comparison. Only passing native goals, memory guards and identical-baseline calibration justify service tests. Keep slower rounds and failed attempts; no threshold relaxation or competitor change.
