from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144';N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'preparation-proof.json')['complete'] and load(R/'extrema144-source-actual-exits.json')['preparation_actual_exit']==0
prior=load(R/'profile143-storage-closed-next-proof.json');before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
now=datetime.now(timezone.utc).isoformat()
note=f'''\n## Actual Archive extrema144 implemented; prerequisites running ({now})

143 timing/audits/private publication and storage cleanup are all complete.
Private6ac46ed413596b694c3b47f57fe95a53acd5265f saved45files283351bytes; fresh
remote bytes verified again, native exactperf143 removed215056382bytes/1196files.
Earlier cleanup guard hold caused no deletion. Useful index-kit-143 remains.

New144 is actual code in work/perf-144/candidate: reuse existing block_min/max
for published column global bounds. Only global-bound expressions and feature
gating change from exact131 Archive; merge/Reader/ordinary64KiBwriter/inputCRC/
sums/otherindex fields/finalsortedness/bothsyncs/rename/receipts/ACK/cutpoints
unchanged. Feature reuse-publish-extrema-144 depends on exact131. Supported016
main source/tests/dependencies remain byte-exact. No rejected134/136/138/140 code.
Declaration preceded implementation. Source outside publication exact131;
index-only-change.patch shows precise delta. New test exercises1/4095/4096/4097/
8193 rows across two ordinary batches, signed extrema/filter pruning/pins,
compaction/reclaim/cold reopen/original receipt replay+mismatch.

Untimed builder work/build_extrema_144.py is running through
launch_build_extrema144.ps1; check actual live identities, small log
work/build-extrema144.log and work/extrema144-actual-exits.json FIRST.
Expected4fresh normal/fault debug/release suites86 each=344, two strict lints,
original durable driver artifact. These are EXPECTED, not passed yet. Do not
rerun completed jobs. No144 timing cases declared; speed UNMEASURED; source and
binary UNSAVED until later publication. After actual build exit, finish
audit_extrema144_stores.py on all28 stores245952 rows/5902848 CRCbytes with exact
independent indexes/payload/original receipt digests+generations. Then six
original016 exactwire pairs and14 publication recovery cases/56command exits,
all actual waits/audits required. Reuse identical passed prerequisites explicitly.
Only afterward predeclare fresh145-or-later balanced sameD supported016 A/B
versus JOINT131+144 candidate C; charge all phase/input/readCRC/index/write/
flush/sync. Full/both-half144AA/144guards/sixclustered whole<=.95/prepare<=.90
goals and original324Native/252service/42goals/153AA/171guards plus correctness/
retry/recovery/sustained service unchanged. No kernel-only adoption/release/ETA.

Current143 empirical scope: five shapes pass all full/both-half kernel goals,
full paired medians13.5–23.3% lower; ordered second-halfAA0.858189 fails so
that gain is inconclusive. All Archive I/O/phase/sync/ACK/service excluded.
It justifies144 source, cannot predict durable gain. Neverretime143/closedjobs.
FIRST actual reset/ALLsupervisors/newjobs, neverstop/message anotherproject/app
or rearm expiredreset. Timed/declared cohort activeORwaiting blocks Git/hash/
copy/build/package/cleanup/independent audits/otherbenchmarks. All futuretimers
need120continuous observedquiet afterprep/freezes andstrictbefore/aftercase
guards; metadataidlewhileNative; onlypredeclaredprovenoutside-lifetimewaits,
missingtime/reset/possibleoverlaprejectwholeprefix. Everycase/stall/failure/
unstarted index preserved, no selectedretime/metric choice. Localbuilds/tests,
Actions$0Stopusage/evidence skipCI; SHORTprivateoutcomes/source,freshremotebytes
thenliteralabsolute native no-reparse completedcleanup, no rawmultiGB/history
ref/tag/releasedeletion. KeepACTIVE30minsamechat loop/name/prefs, oldloop/checker
paused/migrationdisabled; no abandonedchatresume. Advance actual144 artifacts.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
out={'utc':now,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'144_actual_code_implemented':True,'timed_cases_declared':0,'release017_qualified':False}
(R/'extrema144-started-next-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out),flush=True)
