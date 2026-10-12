# Archive lazy merge workspace131 — October12,2026

**Actual isolated code improvement: ordered input no longer creates merge
ranges.340 fresh tests/two strict lints/eight independent store audits pass.
Performance is UNMEASURED; supported0.3.16 unchanged/0.3.17 unreleased.**

Kernel126 measured an ordered +12.27% elapsed regression. Phase127 removed
ordered merge planning but still eagerly allocated and filled its ranges.
131 constructs those ranges only when charged CRC/input collection establishes
disorder. It reconstructs exact offsets from selected run row counts enforced
by the existing reader, then uses the byte-identical bounded122 merge. Ordered,
chunked and fragmented/small fallback phases keep the same data semantics.
The final publication sortedness check/sort/index/CRCs/syncs/receipts/ACK stays.
This removes unnecessary source-level workspace work; neither an allocation
counter nor a speed measurement was run. No benefit magnitude is inferred.
[Rust Vec allocation contract](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees).

Four normal/fault debug/release suites actually exited0 with85 tests each;
two clippy all-targets strict checks exited0. Baseline154 tests/binary are
REUSED. The added unequal unordered test has1/4097/37/8195-row runs, signed
values, complete grouped row comparison against Database, exact retry/mismatch
outcomes, pinned snapshots, reclamation and cold reopen. Existing corrupt/
truncated input rejection before publication and fault tests passed unchanged.
Full independent decode of all four ordered and four unequal stores checks
82,096 exact attached row triples/1,970,304
CRC bytes, all indexes, original receipt digests/generations and one output
segment. Independent audit actualexit0. This is not physical power-loss proof
or separate whole-engine/service/sustained recovery qualification.

Before declaration a visible Java build held preparation's measurement gate;
no131 timer was started. Since there was no live timed supervisor, untimed
source/tests proceeded. The first inline build launcher triggered the legacy
PowerShell .py matcher: controller73292/creation134362561657616299, wrapper
50584 created05:22:42.121198Z. Actualexit1, zero Cargo jobs/zero tests. Its
failure/source remains. A separate fixed-file launcher retained the strict
guard and unchanged engine source; all seven declared build jobs then exited0.
No unrelated job/app stopped or messaged, no Actions job triggered.

An external timed run began four seconds after build exit and held the pending
audit/save/cleanup. After actual supervisor termination/settled terminal report,
127.53 observed clear seconds preceded the full independent audit. The first
quiet waiter falsely rejected JSON date coercion; a separate DateKind String
correction kept exact UTC checks. Reset bytes never changed. Both wait sources
and the exact no-hash appendix verification are retained; builds were not rerun.

All timing cases remained UNDECLARED/UNSTARTED in131. Interrupted130's44 correct
cases/172 unstarted and129's seven/209 remain failed prefixes, not new gains.
Before adoption use a new-number balanced same-D comparison, passing full and
both-half controls and no material regressions, then original324Native/
252service/42goals/153AA/171guards plus correctness/recovery/sustained service.
No release ETA, numerical gate change or universal benchmark-win claim.

Candidate binary SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
Policy SHA256:`e09eb3f4a531c122dce42ec1f3efea1e3e9f95b82f8f366c28f4bbb74952d87d`.
Merge module SHA256:`3654a9794eb8d144b79212fd18d699af08f0692416eb93100a45593f836f36f6`.
[Actual code, tests and failed/final controllers](experiments/compaction_phase_131/README.md).
Short outcome/useful source privately saved and freshly verified, then scoped
completed stores/regenerable output removal. A small reusable binary is kept;
no raw bundle or old remote history/ref/release deletion.
