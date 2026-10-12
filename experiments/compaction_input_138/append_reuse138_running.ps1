$ErrorActionPreference='Stop'
$taskNext='D:\Codex\KESTREL_NEXT.md'
$taskOld=[IO.File]::ReadAllBytes($taskNext)
$taskExpected=(Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase137-closed-next-proof.json' -Raw | ConvertFrom-Json -DateKind String).new_sha256
$taskOldSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskOld)).ToLowerInvariant()
if($taskOldSha -ne $taskExpected){throw 'Latest checkpoint changed; do not overwrite history'}
$taskPolicy=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\perf-138\policy.json' -Raw | ConvertFrom-Json -DateKind String
if($taskPolicy.trial -ne 138 -or $taskPolicy.timed_cases_declared -ne 0){throw 'Unexpected138 declaration'}
$taskUtc=(Get-Date).ToUniversalTime().ToString('o')
$taskNote=@"


### 138 actual compaction allocation fix: untimed prerequisites running — $taskUtc

The human objected to repetitive scheduled updates and explicitly expects
actual engineering progress.138 is DECLARED and IMPLEMENTED, not a rerun of
writer134/136 or calibration137. Exact131 merge/phase plus original64KiB writer.
The compaction loop reuses one decoded block Vec and one raw-byte scratch Vec
across all selected inputs, using existing Reader.read_block_into and safe
mem::take. Both buffers are released before arranging/publication. Every input
CRC/read/decode and phase check stays charged; ordinary reads/publication,
both explicit syncs, final sortedness/index/CRC, receipts/ACK/format/cutpoints
remain unchanged. No unsafe, dependency, API, cache or global setting change.
32x1024 rows/three columns previously create96 decoded/32scratch temporary Vec
lifetimes; new loop keeps one each. This is a SOURCE count, not elapsed speed
or allocator/syscall measurements. Benefit unknown; no adoption/release claim.

New growing/shrinking two-compaction test checks block boundaries, late rows,
full SQL reference, original receipts/replay mismatch, pinned view/reclaim and
cold reopen; final24733 rows/head13. Existing late CRC/truncation and signed/
ordered/unequal tests run too. Four fresh86 suites=344 tests/two strict lints
and original durable driver are declared. Current owned launch_build_reuse138/
build_reuse_138 controller logs work/build-reuse138.log, actual wait proof
work/reuse138-actual-exits.json. Check live identity/log before doing anything;
finish actual exit and do not duplicate jobs or rerun passed identical suites.
At append time the first three suites86 each and first lint have passed;
fault-release is in progress. No timed138 cases declared.

After actual build exit0, independently decode ALL12 ordered/unequal/new-growth
stores:181028 exact rows/4344672 CRC bytes; derive original receipts/generations
from inputs. Finish exact legacy131/138 wire pairs and14 publication recovery
cases/actual exits before performance. New source/binary is UNSAVED until short
private publication and fresh byte verification; never delete it early.
Future139-or-later complete balanced same-D exact131 A/B versus138 C, full/both-
half A/A, all stage medians/whole+setup p95 guards; predeclared clustered whole
<=.95 and preparation<=.90 goals. All writes/syncs/input/phase charged. Original
324Native/252service/42goals/153AA/171guards and recovery/sustained service remain.
No selected retiming or loosening gates; finish complete cohorts and independent
payload/CRC/receipt/generation/lifetime/frozen-byte proofs or preserve whole
failed/unstarted prefixes.120 continuous observed quiet after preparation;
strict reset/task/supervisor/global-build checks before/after every actual case.

137 is CLOSED/rejected and deleted only after private9e946b8/32files223987B
fresh verification:178246238B/1139 files removed. It had32 A/A/13 guards/all six
goals fail despite3.145% clustered paired whole reduction. All results/failures
are retained; first mixed-line-ending publication failure saved, v2actual0.
Do not rerun137. Both prior writer variants remain rejected.0.3.16 supported
core byte-exact,0.3.17 unreleased, no reliable ETA. Existing heartbeat stays
ACTIVE30minutes in this chat, next prompt must name this actual138 job/artifacts
and advance them, not replay closed work. First check actual reset/live jobs;
hold heavy actions while timers/cohorts active/waiting. Never stop/message other
projects/apps or alter unrelated data. Reset expired, never rearm; oldmigration
disabled/oldloop/checkerpaused. Local builds/tests, Actions0 Stop usage/skipCI.
Short private outcomes/failures/useful source, fresh remote bytes then native
absolute literal no-reparse completed cleanup; no multiGB bundles/history loss.
"@
$taskBytes=[Text.UTF8Encoding]::new($false).GetBytes($taskNote)
$taskCombined=[byte[]]::new($taskOld.Length+$taskBytes.Length)
[Array]::Copy($taskOld,0,$taskCombined,0,$taskOld.Length)
[Array]::Copy($taskBytes,0,$taskCombined,$taskOld.Length,$taskBytes.Length)
[IO.File]::WriteAllBytes($taskNext,$taskCombined)
if(-not [Linq.Enumerable]::SequenceEqual([byte[]][IO.File]::ReadAllBytes($taskNext),[byte[]]$taskCombined)){throw 'Append verification failed'}
@{utc=$taskUtc;old_sha256=$taskExpected;new_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskCombined)).ToLowerInvariant();old_history_prefix_exact=$true;reuse138_build_running=$true;timed_cases_declared=0;performance_unmeasured=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\reuse138-running-next-proof.json' -Encoding utf8
Write-Output 'Actual138 implementation/build checkpoint appended'
