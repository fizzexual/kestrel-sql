from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,shutil,re
ROOT=Path('D:/Codex/Kestrel');REPO=ROOT/'outputs/kestrel-sql';OUT=REPO/'benchmarks/writer-trace-087';W=ROOT/'work/perf-087'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*argv):return subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),'-C',str(REPO),*argv],text=True).strip()
assert load(OUT/'preservation-proof.json')['complete']and load(OUT/'restored-audit-proof.json')['passed']
assert git('rev-parse','HEAD')=='b29bef3ba32e49d220337f8aa6cb763fe554a62c'
base=load(ROOT/'work/perf-086/previous-062-baseline.json');assert all(sha(REPO/n)==h for n,h in base['core_source_sha256'].items())
assert sha(REPO/'OVERNIGHT_2026-10-07.md')=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
nextfile=ROOT.parent/'KESTREL_NEXT.md';backup=ROOT/'work/KESTREL_NEXT-before-087.md';assert not backup.exists();shutil.copy2(nextfile,backup)
addition='''
## Completed bounded real-writer diagnostics087, October8,2026

Trial087 is a diagnostic correctness milestone, not a speed change or supported release. Read repository WRITER_TRACE_087.md and benchmarks/writer-trace-087/audit.json. Both exact released/clean061 copies now carry an optional bounded writer-trace feature based on qualified068 publication traces. Default modules/fields/getter/private operation/clocks are absent; original Stats fields match the actual0.3.16 bridge. Writer events capture queue-to-collected-group wait, append/new attempt/generation/seven stages, compaction and reclaim. No bridge parse/dispatch clock, exclusive p99 decomposition or physical cause is established.

Each core freshly passes77 default and82 traced tests in debug/release, all five strict lint configurations,90 successful external native commands,32 SQLite comparisons,10 byte-identical Archive stores and4 byte-identical sequential Live stores. All320 traced sequential/concurrent ACKs map exactly to request keys and publication generations.12 Live stores reopen with original0.3.16. Controlled pending-directory failures, poison behavior, cold retry/generation-gap/reset, compaction/reclaim/pinned data, stale no-op/error records and retention bounds pass. Full historical061/068 SQL/crash/source suites are retained, not all newly rerun; these checks do not qualify physical power loss or release readiness.

The diagnostic unit-variant operation initially accepted unexpected fields. Its exact failed wire/binary/store remains preserved. Revision2 empty struct variant rejects extra fields, passes16 affected bridge-bin test executions, repeat strict lint and a fresh complete five-binary protocol cohort. Two preparation stops, an envelope-parser correction and an audit syntax stop remain preserved. Completed native commands were parsed from their existing raw outputs, not replayed over old stores.

Evidence:6 ZIP parts,13299 files under benchmarks/writer-trace-087; complete CRC/member-SHA/size/file-set checks and exact independent restored audit pass with zero native launches/timing reruns. Originals stay work/perf-087 and restoration work/restored-writer-087. Only regenerable targets/temp/Python caches are omitted from ZIPs; originals are not deleted. Supported0.3.16 core and the frozen overnight report are unchanged. No remote publication.

Next engineering:088 or later must predeclare fresh D: balanced normal-build/original-core compatibility and tracer-overhead controls before using diagnostics to attribute service tails. Use repeated unchanged binaries as A/A; fixed full-cohort and balanced-block guard/calibration checks; complete arrival/loss/ACK accounting and attempt/generation/key correlation. Keep getters/audit/build/hash/package outside arrival windows; reject dropped trace records and preserve every slow/unqualified block. No timing was performed in087. Keep086's calibrated write-tail regressions and all previous failures intact. Trace retention4096 events/16384 requests and snapshot cloning need explicit memory/overhead qualification; no peak-RSS claim exists. Use measured individual queue/publication/maintenance evidence to justify a real writer edit, preserving synchronization, receipts and queue budgets. Full native/six-profile service/memory/source/retry/crash/corruption/compatibility/competitor/reproducibility gates still precede any integrated0.3.17 promotion.

Before any work, check task-owned jobs and the prepared offline reset. It remains separately armed/waiting; never interfere with execution, force-close apps, widen cleanup, reactivate old tasks/automation or restore abandoned chats. The current hourly D: heartbeat remains authorized and quiet on unchanged states. A fresh-profile reset may discard it by design; follow the existing post-reset new-chat verification instructions.
'''
addition=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',addition)
nextfile.write_text(nextfile.read_text(encoding='utf-8')+addition,encoding='utf-8',newline='\n')
# Expose the formatted, actually compiled module alongside the preserved preparation source.
shutil.copy2(W/'released/src/writer_trace_087.rs',OUT/'compiled-writer_trace_087.rs')
shutil.copy2(W/'released/examples/writer_trace_probe.rs',OUT/'compiled-writer_trace_probe_087.rs')
allowed=['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','WRITER_TRACE_087.md','benchmarks/writer-trace-087']
git('add','--',*allowed)
subprocess.check_call(['git','-c','safe.directory='+REPO.as_posix(),'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),'diff','--cached','--check'])
git('commit','-m','Qualify bounded optional service-writer diagnostics and preserve trial087')
head=git('rev-parse','HEAD');assert not git('status','--porcelain')
subprocess.check_call(['git','-c','safe.directory='+REPO.as_posix(),'-C',str(REPO),'merge-base','--is-ancestor','b29bef3ba32e49d220337f8aa6cb763fe554a62c','HEAD'])
with nextfile.open('a',encoding='utf-8',newline='\n')as f:f.write('\n087 reports, code/evidence and release navigation are saved in local commit `'+head+'`, with a clean working tree and all preceding commits retained. Remote unchanged.\n')
save(ROOT/'work/commit-087-proof.json',{'head':head,'clean':True,'parent_preserved':True,'supported_core_unchanged':True,'overnight_unchanged':True,'remote_unchanged':True,'utc':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'head':head,'clean':True,'supported':'0.3.16','diagnostic_qualification_only':True}))
