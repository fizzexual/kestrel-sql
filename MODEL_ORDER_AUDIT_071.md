# Correction: checkpoint-model ordering in 069 and 070

An independent review during trial 071 found a scheduling flaw in the two earlier checkpoint compression models. The rotation of size order and the `(round + size_index) % 3` variant rotation cancelled each other. At each fixed size, **all four rounds used the same variant order**:

| Starting receipt history | Actual order in every round |
|---:|---|
| 0 | raw A, raw B, compressed C |
| 50,000 | raw B, compressed C, raw A |
| 99,000 | compressed C, raw A, raw B |

The size order did rotate, but the claim that variant order rotated per size was incorrect. I introduced this flaw and the earlier audit checked actual cases against the frozen plan without independently checking position balance. Repeated order can confound serial comparisons with position, cache and changing host/storage conditions. The reported matched ratios remain the original descriptive calculations; they are not newly qualified causal codec speedups or slowdowns. Both models remain rejected, with no engine integration or supported promotion. Exact byte/CRC/decoder tests, original input hashes, all raw timings and all failed gates remain preserved.

Read this correction alongside [zlib model 069](COMPRESSION_069.md) and [Zstandard level-1 model 070](COMPRESSION_070.md). Neither report, original policy, frozen harness, raw result nor private ZIP was rewritten. The correction applies to those two model cohorts; it does not establish an ordering defect in other benchmarks. No new DuckDB/PostgreSQL claim follows.

The next independent model uses six complete permutations. For every fixed size, each variant appears in every position twice, all six variant orders appear once, and both A-before-B and B-before-A occur three times. Each size appears in each size position twice. The planner and auditor verify those counts independently of elapsed times before any case starts and after completion. Regression tests reject the old cancelling rotation as well as duplicated variants and malformed size groups.

[Historical frozen-plan audit](benchmarks/compression-071/previous-order-audit.json), [auditor source](benchmarks/compression-071/audit_previous_order.py), [new planner and regression tests](benchmarks/compression-071/order_plan.py), [pre-timing balance proof](benchmarks/compression-071/order-balance-pre-timing.json) and [new model report](COMPRESSION_071.md). Prior raw and release evidence remains linked from the original reports. English only; supported KestrelSQL 0.3.16 and the frozen morning report remain unchanged.

Private immutable evidence parts (all required for complete reproduction):

- [kestrel-sql-development-071-core-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-core-evidence.zip).
- [kestrel-sql-development-071-core-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-core-evidence.zip.sha256).
- [kestrel-sql-development-071-raw-a-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-a-evidence.zip).
- [kestrel-sql-development-071-raw-a-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-a-evidence.zip.sha256).
- [kestrel-sql-development-071-raw-b-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-b-evidence.zip).
- [kestrel-sql-development-071-raw-b-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-b-evidence.zip.sha256).
- [kestrel-sql-development-071-zstd-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-zstd-evidence.zip).
- [kestrel-sql-development-071-zstd-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-zstd-evidence.zip.sha256).

Every server digest matches. All 106 previous assets and 20 engine tags/releases remain unchanged. The four ZIPs contain reports before these upload-link paragraphs.
