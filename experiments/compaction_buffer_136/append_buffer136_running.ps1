$ErrorActionPreference='Stop'
$taskNext='D:\Codex\KESTREL_NEXT.md'
$taskOld=[IO.File]::ReadAllBytes($taskNext)
$taskExpected=(Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase135-closed-next-proof.json' -Raw | ConvertFrom-Json).new_sha256
$taskOldHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskOld)).ToLowerInvariant()
if($taskOldHash -ne $taskExpected){throw 'Checkpoint prefix changed'}
$taskPolicy=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\perf-136\policy.json' -Raw | ConvertFrom-Json
if($taskPolicy.trial -ne 136 -or $taskPolicy.timed_cases_declared -ne 0){throw 'Unexpected declaration'}
$taskStamp=(Get-Date).ToUniversalTime().ToString('o')
$taskNote=@"


###136 actual bounded-buffer-only code / LOCAL prerequisites RUNNING — $taskStamp

135 isCLOSED, private951c30079e0bac0eddb688b57dc35afaf9b9a076/23files187065B
freshverified; exact178468910B/1139files removed. All216correct but24/144AA,
35/144guards/ALL6goalsFAIL. Combined134WRITE_THROUGH+buffer moves latencyfrom
syncinto writes; no durablegain. Preserveeveryfailure; neveradopt134.

136policy declaredBEFOREimplementation, ZEROtimedcases. Newisolatedactual
Archive code keeps exact<=1MiB Windows compaction-only BufWriter, REMOVES
FILE_FLAG_WRITE_THROUGH/customFlags. Ordinary/larger/nonWindows64KiB original
stream stays. BOTHexplicit segment/catalogsyncs, rename/ACK/order/receipts/
format/faultpoints unchanged. Samebyte-exact131 merge/phase. New small/large
test labels buffer136, samecompleteSQLreference/retry/mismatch/pin/reclaim/
coldreopen behavior. Buffer-only maystillregress; speedUNKNOWN, no syscall
count measured or physicalpowerloss qualification. No unsafe/dependency/API/
globalsettings/Source016 change.

Current work/launch_build_buffer136.ps1/build_buffer_136.py executes fourfresh
normal/faultdebug/release suites86each=344, two strictlints/originaldurable
driver artifact. Log work/build-buffer136.log; actualwaitproof
work/buffer136-actual-exits.json. DoNOTduplicate thisjob orrerun passedbuilds.
Strict verifiedowner/reset/task/supervisor guards beforeeachjob; alltestsLOCAL.
Finishactualexit then ALL16independentfreshstores with
work/audit_buffer136_stores.py (352424rows/8458176CRCbytes), exactlegacy131/136
wire pairs and14publicationrecoverychecks beforeadoption. Newsource/binary
UNSAVED untilfutureconciseprivatepublication/freshbyteverify; neverremoveearly.
Allfailures/prefixespreserved. No136performancecases declared. Future137+ only
fullbalanced sameD131A/B/newC/fullandbothhalfAA/median/tail/setup/write+sync
guards, allinput/phase/write/flush costscharged and originalrelease324Native/
252service/42goals/153AA/171guards/recovery/sustainedUNCHANGED.017UNRELEASED,
016supportedbyteexact. Check allactualjobs/resetFIRST; noheavywhiletimedwork,
continuous120secquiet beforetimers. Nootherproject/appstop/message/forcequit.
KestrelheartbeatACTIVE30min/samechat, oldloop/checkerpaused, oldmigrationdisabled,
resetexpiredneverrearm; Actions0cap/evidence skipCI/shortprivateoutcomes/fresh
verify/nativeno-reparse completedcleanup; no multiGBbundles/history/refdeletion.
"@
$taskNoteBytes=[Text.UTF8Encoding]::new($false).GetBytes($taskNote)
$taskCombined=[byte[]]::new($taskOld.Length+$taskNoteBytes.Length)
[Array]::Copy($taskOld,0,$taskCombined,0,$taskOld.Length)
[Array]::Copy($taskNoteBytes,0,$taskCombined,$taskOld.Length,$taskNoteBytes.Length)
[IO.File]::WriteAllBytes($taskNext,$taskCombined)
$taskNew=[IO.File]::ReadAllBytes($taskNext)
if(-not [Linq.Enumerable]::SequenceEqual[byte]($taskNew,$taskCombined)){throw 'Append bytes differ'}
@{utc=$taskStamp;old_sha256=$taskExpected;new_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskNew)).ToLowerInvariant();old_history_prefix_exact=$true;buffer136_build_running=$true;timed_cases_declared=0;performance_unmeasured=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\buffer136-running-next-proof.json' -Encoding utf8
'136 source/build running checkpoint appended'
