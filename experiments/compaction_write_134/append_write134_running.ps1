$ErrorActionPreference='Stop'
$taskNext='D:\Codex\KESTREL_NEXT.md'
$taskPrior=[IO.File]::ReadAllBytes($taskNext)
$taskExpected=(Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase133-closed-next-proof.json' -Raw | ConvertFrom-Json -DateKind String).new_sha256
$taskSha=[Security.Cryptography.SHA256]::HashData($taskPrior)
if([Convert]::ToHexString($taskSha).ToLowerInvariant() -ne $taskExpected){throw 'Checkpoint changed'}
$taskStamp=(Get-Date).ToUniversalTime().ToString('o')
$taskNote=@"


###134 actual bounded compaction write-mode code / local prerequisites RUNNING — $taskStamp

work/perf-134/policy.json declared BEFORE implementation, ZEROtimedcases.
Candidate derives exact private131 patch/module/tests, adding feature
adaptive-segment-write-134 dependentonphase131. WindowsCOMPACTIONonly with
wire<=1MiB uses FILE_FLAG_WRITE_THROUGH(0x80000000), coalesces exact existing
wirebytes in one boundedBufWriter; ordinaryappend/larger/nonWindows retains
original64KiBstreaming. NO NO_BUFFERING/sectorpadding/dependency/unsafe/format/
API/globalsetting change. BOTH segment sync_all and catalogsync/rename/ACK/
faultcutpoints areUNCHANGED; charge ALLwrite/flush costs beforeanybenefitclaim.
ThiscouldMOVEorWORSENsync stalls; benefitUNKNOWN, not a qualifiedreleasechange.

Newsmall2048-row andlarge65534-row fallback compaction test checks complete
groupedtupleSQLreference/retries/mismatch/pins/reclaim/coldreopen. Fourfresh
normal/fault debug/release suites expected86each=344 plus2strictlints/original
driver releasebuild. work/launch_build_write134.ps1/build_write_134.py are
currentLOCALbuild, actualwait/exit proof work/write134-actual-exits.json;
log work/build-write134.log. DoNOTduplicate it. Supervisor/resetguard before
everybuild. No benchmarkoverlap, noappstop/messaging. Source inventoryfrozen;
preserveeveryfailure. Finishactualbuildexit and then ALL16teststores using
work/audit_write134_stores.py (expected352424rows/8458176CRCbytes), recordactual
exit. Also require exact131/134 legacywire bytes and recovery beforeadoption.
New134 source/binary UNSAVED until futureconciseprivatepublication/freshverify;
doNOTdelete whileactive/unverified. Onlycleanupcompletedfixtures aftersave.

133 alreadyCLOSED:216 actualexit0 cases/all7MrowCRCaudits, controlledclustered
whole10.80% lower/prepare29.37% lower fullandbothhalves; OVERALL7/72SYNCidentity
and1/72uncontrolledguardFAIL, materialsync tailsretained. Private17069419493b10d192006636d9e014f37a31f006
shortreport+source16files85895bytes freshverified, exactperf-133 cleanup
178144610bytes/1135files. Source016byteexact/mainclean/zeroaheadatlastcheck.
017stillUNRELEASED. Nextperformance usesfresh135+balanced131A/B vs134C to
isolatewritemode plusoriginal016wholeengine qualification, full/bothhalfAA,
median/tail/write+sync/setup guards andoriginal324Native/252service/42goals/
153AA/171guards/recovery/sustainedgates. Neverdrop/retime badcases/relaxgates.
KestrelACTIVE30min/checkerPAUSED/oldmigrationDISABLED/resetexpired/localtests/
skipCI/Actions0cap/shortprivateoutcomes/freshverify/nativecompletedcleanup.
"@
[IO.File]::AppendAllText($taskNext,$taskNote,[Text.UTF8Encoding]::new($false))
$taskCurrent=[IO.File]::ReadAllBytes($taskNext)
if($taskCurrent.Length -ne $taskPrior.Length+[Text.Encoding]::UTF8.GetByteCount($taskNote)){throw 'Append length mismatch'}
@{utc=$taskStamp;old_sha256=$taskExpected;new_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskCurrent)).ToLowerInvariant();old_history_prefix_exact=$true;134_declared_timed_cases=0;134_build_running=$true;performance_unmeasured=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\write134-running-next-proof.json' -Encoding utf8
'134 declared/code/prerequisite checkpoint appended'
