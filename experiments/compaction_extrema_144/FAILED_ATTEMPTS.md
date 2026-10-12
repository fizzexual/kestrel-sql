# Guard holds and preparation failures144

| Attempt | Actual result | Completed prefix and continuation |
| --- | --- | --- |
| Initial correctness build | Exit1 before normal lint; unknown Python appeared | Two86-test suites passed; continuation ran only the unstarted lint/fault suites/artifact |
| First compatibility controller | Exit1 on new Node build before duplicates candidate | Seven native cases retained; five unstarted cases finished later |
| Compatibility continuation | Exit1 before re-auditing an old store; new Node build | Zero new native cases; exact journal still seven |
| First recovery artifact launcher | Global build hold before Cargo | Zero Cargo jobs; v2 built only CLI/seed/fault artifacts, zero tests repeated |
| First recovery controller | Exit1 before segment_synced/exit on new Node build | Four complete cases/16 commands retained; finisher ran only ten unstarted cases |
| Second publication | Exit1 before commit: scoped partial summary detected | Exact failed bytes preserved; only our owned summary restored, final v3 uses UTF-8 |
| First publication | Exit1 before commit: cp1252 decode of UTF-8 summary | Separate v2 uses explicit UTF-8; no engine/result/timing change |
| Recovery finisher preparation | Sandbox PermissionError at first output write | No source/native job created; exact escalated retry succeeded |

Actual failed sources, exit proofs and bounded failure details are preserved.
Safety waits are outside child lifetimes and are not database scheduling. The
first artifact v2 permits ordinary unrelated builds during untimed compilation,
while retaining reset/all timed supervisor guards; performance/wire/recovery
guards are unchanged. No metric selection, repeated native cases, forced
unrelated kills or failed engine correctness assertion occurred in these holds.
