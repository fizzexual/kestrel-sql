$ErrorActionPreference='Stop'
$taskNext='D:\Codex\KESTREL_NEXT.md'
$taskPrevious=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-closed-next-proof.json' -Raw | ConvertFrom-Json -DateKind String
$taskOld=[IO.File]::ReadAllBytes($taskNext)
$taskOldHash=[Convert]::ToHexStringLower([Security.Cryptography.SHA256]::HashData($taskOld))
if($taskOldHash -ne $taskPrevious.new_sha256){throw 'Checkpoint changed; preserve newer prefix'}
$taskPolicy=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\perf-142\policy.json' -Raw | ConvertFrom-Json -DateKind String
if($taskPolicy.trial -ne 142 -or @($taskPolicy.cases).Count -ne 216){throw 'Diagnostic declaration incomplete'}
$taskStamp=(Get-Date).ToUniversalTime().ToString('o')
$taskNote=@"


###142 actual index diagnostic implemented; example prerequisites running — $taskStamp

141 remains CLOSED/rejected/private14c05e5,43files271738B verified and exact
178232310B removed. No closed cohort is replayed. CURRENT142 is a new bounded
INDEX-ONLY diagnostic under work/perf-142/candidate/examples/index_profile_142.rs.
Legacy index loop lifted from supported publish (same131 indexing), with only
slice-iteration borrow adaptation. Candidate computes global min/max from the
already fully computed block min/max arrays, removing two full-column scans;
every sum/CRC serialization+hash/block extrema/monotonicity unchanged. Actual
library src/tests/dependencies and supported016 core are byte-exact. No new
Archive API/durability/default-engine change, no143 integration/adoption yet.

Declaration BEFORE implementation/timing:216cases/12balancedrounds/sixshapes/
32x1024rows/3cols/RNG20261011/all6permutations per shape per half. One executable
uses identical legacy A/B functions and minimal candidate C.16 COMPLETE index
builds per primary timer, all allocations/drop/sums/CRC/output indexes charged;
black_box input/function/result is best effort per primary Rust docs. Inputs
generated and stable-TS-sorted/SHA outside timer; one separately instrumented
legacy stage profile ALSO outside primary timer, with timing overhead disclosed.
No Archive input reads/CRC/merge/input sorting/index JSON/segment/catalog write/
flush/sync/receipts/ACK/service/competitor costs inside kernel. NEVER call this
durable/whole-engine gain or proof that a stage exclusively dominates Archive.
Full/both-half18AA/18guards/18index-only goals, AA[.90,1.10]/guard<=1.10/goal<=.95,
all cases/stalls once, no selected retiming/outlier discard/metric selection.
Independent every inputSHA/full index field/i128 prefix/blockCRC from declared
seed required; no raw multiGB stores, small JSON metadata only.

Check work/build-profile142.log, actual build_index_profile_142 supervisor and
profile142-build-actual-exits.json FIRST. Two new example-only tests debug/release
(expected4fresh tests), one strict example lint/release artifact. Supported
engine tests explicitly REUSED because engine bytes unchanged, no rerun. Build
guard is check_profile142_build_activity.ps1 with exact owned creation identity.
Source and future binary UNSAVED; do not delete early. No142 timing started.
After actual build exit/proofs, prepare independent diagnostic controllers/
preflights then freeze exact source/binary/policy,120 continuous observed quiet
before timings, same reset/task/supervisor/global checks BEFORE/AFTERevery case.
Owned metadataworker idle during native lifetime; only predeclared outside-
lifetime waits. Finish existing cohorts/exits/full independent audit before new
work. Preserve ALL attempted/failed/unstarted prefix if blocked, never replay.

Next actual engine change needs fresh normal/fault debug/release correctness/
lints/independent wire/receipts/generations/recovery, then fair same-D complete
Native/service/sustained qualification. Original324Native/252service/42goals/
153AA/171guards unchanged before adoption, component/kernel cannot release.
Supported0.3.16 exact,0.3.17 UNRELEASED. Keep133limitedgain/125failedcontrols/
126kernel exclusions and ordered regression explicit. No universalwins/ETA.

FIRST reset/all actual supervisors/workers/newerjobs includingrelative
deployment soakDargs; no PID/clock/restartgap as exitproof. Never stop/message
anotherproject/app, forcequit, create stopfiles or alter unrelateddata. Hold
Git/hash/copy/build/package/cleanup/independent audits/otherbenchmarks while
ANYtimer/declaredtimedcohort activeORwaiting. Poll owned sessions/small logs;
no inline status with Pythonfilenames. Inspectglobalbuilds/directJavaMavenGradle.
Resetexpiredneverrearm; oldmigrationDISABLED/oldloop+checkerPAUSED. Preserve
existing ACTIVE30min heartbeat/name/target/notificationprefs, no duplicate or
abandonedchatresume. Allbuilds/testsLOCAL/Actions0Stopusage/evidence skipCI.
SHORTprivate outcomes/everyfailure/usefulsource, freshly verify remotebytes then
native literal absolute scoped no-reparse completed cleanup; no multiGB raw/
oldhistory/ref/tag/release deletion or loss of unique unverifiedexports/kits.
Use LF/no appended EOF; raw CRLF proof bytes as base64 if preservation needed.
Advance CURRENT142 actual artifacts; quiet unchangedbusy, milestonesonly.
"@
$taskNote=$taskNote.Replace("`r`n","`n")+"`n"
$taskNew=[byte[]]::new($taskOld.Length+[Text.Encoding]::UTF8.GetByteCount($taskNote))
[Array]::Copy($taskOld,$taskNew,$taskOld.Length)
[Array]::Copy([Text.Encoding]::UTF8.GetBytes($taskNote),0,$taskNew,$taskOld.Length,[Text.Encoding]::UTF8.GetByteCount($taskNote))
[IO.File]::WriteAllBytes($taskNext,$taskNew)
$taskRead=[IO.File]::ReadAllBytes($taskNext)
if(-not [MemoryExtensions]::SequenceEqual([ReadOnlySpan[byte]]$taskRead,[ReadOnlySpan[byte]]$taskNew)){throw 'Checkpoint append not exact'}
@{utc=$taskStamp;old_sha256=$taskOldHash;new_sha256=[Convert]::ToHexStringLower([Security.Cryptography.SHA256]::HashData($taskNew));old_history_prefix_exact=$true;diagnostic142_implemented=$true;timed_cases_started=0;release017_qualified=$false} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-started-next-proof.json' -Encoding utf8
'Actual142 index diagnostic checkpoint appended'
