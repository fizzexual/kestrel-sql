# Archive comparison 128 preflight — October 11, 2026

**All216 declared timings are UNSTARTED. Supported0.3.16 is unchanged;
0.3.17 remains unreleased. There is no new measured speed result.**

This attempted a fresh comparison of the exact [phase127 repair](COMPACTION_PHASE_127.md)
against byte-identical supported A/B, charging actual input CRC/read, phase
selection, index building and durable sync. Twelve randomized balanced rounds,
six shapes/32x1024 rows/three columns, RNG20261011, logicalCPU8 and120-second
cooldown were declared. All six permutations appear once per shape per half.
The72 controls,72 guards and six goals remain **unevaluated**, with their
original thresholds unchanged. No failed case was selectively retimed.

Six excluded seed5 ordered/clustered A/B/C stores passed fresh native checks
and independent exact payload/index/CRC/receipt/generation audits: 196,608
rows / 4,718,592 CRC bytes. Baseline154 tests, candidate336 tests and two strict
lints were reused, not rerun. The timed-cohort auditor was **unstarted**.
This adds correctness preflight evidence, not durable performance evidence.

A different project's30-minute soak test first held preparation. Its relative
supervisor exposed a wait-check gap between worker restarts. Only our verified
idle waiter65552/creation2026-10-11T19:21:13.2043650Z was stopped before any
declaration/copy/timing, then supervisor-aware v2 waited for natural completion.
An initial process-scope lookup refused to stop an ambiguous match; no process
changed until exact PID/path/creation were verified. Failed wait source remains.

After actual preflight success and120-second cooldown, the first round probe
at 2026-10-11T19:45:43.6400682Z detected new visible builds: pwsh.exe PID39100 created2026-10-11T19:45:31.1972190Z; java.exe PID67376 created2026-10-11T19:45:33.5726650Z.
The controller's PID69040/creation-filetime134362214138990016 was correctly
verified; reset/task jobs were idle. Guard exit3 caused actual controller
exit1 at 2026-10-11T19:45:43.7591679Z, before creating a case journal or starting case0.
The entire216-case unstarted list is accounted for. This is a safety hold,
not evidence that the candidate is slow. No other process/app was stopped.

The next declaration must use a new number and a continuous clear interval,
then finish every case/audit or preserve its complete failed prefix. Existing
125's51/144 failed identical controls and126's ordered regression remain
unresolved. No original release gate was relaxed:324 Native/252 service/
42 goals/153 controls/171 guards plus correctness/recovery/sustained load.

Baseline SHA256:`2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7`.
Candidate SHA256:`c39997c0dff47dd29683590f7501734fbb964235a712aec28d155ef3652085cd`.
Policy SHA256:`73c79a40a0ba54500a00f3eeb34b35b07ee34dd0c8a283c8404d1bce3bd49a16`.
[Actual controllers, failed wait and reproduction](experiments/compaction_compare_128/README.md).
Short outcome/useful source are privately saved and freshly verified before
scoped preflight cleanup. No raw bundle, release upgrade or history rewrite.
