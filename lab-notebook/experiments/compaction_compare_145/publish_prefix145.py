"""Save a concise rejected145 outcome and useful immutable source privately."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145';P=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
D=P/'experiments/compaction_compare_145'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1500:],c.stderr[-1500:]);return c.stdout.decode('utf-8')
policy=load(W/'policy.json');audit=load(W/'prefix-audit.json');life=load(W/'prefix-lifecycle-audit.json')
assert audit['complete_prefix_audit'] and audit['independent_correctness_passed'] and audit['completed_cases']==118
assert audit['unstarted_indices']==list(range(118,216)) and life['complete'] and life['no_performance_qualification']
assert load(R/'phase145-prefix-audit-actual-exits.json')['prefix_audit_actual_exit']==0
assert load(R/'phase145-prefix-lifecycle-actual-exits.json')['lifecycle_actual_exit']==0
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
frozen=load(W/'freeze.json')
sources=[n for n in frozen['files'] if n.endswith(('.py','.ps1'))]
sources+=['audit_prefix145.py','audit_prefix145_lifecycle.py','prepare_prefix145_helpers.py','launch_prefix145_audits.ps1',
    'finish_prefix145_audits.ps1','wait_prefix145_audit_quiet.ps1','wait_launch_phase145.ps1','wait_preflight_phase145.ps1',
    'prepare_phase145_launch_gate.py','complete_phase145_preflight_logging.py','append_phase145_preflight_ready.py',
    'append_phase145_preparation_pending.py','prepare_extrema_compare145.ps1','publish_prefix145.py',
    'launch_publish_prefix145.ps1','launch_publish_prefix145_v2.ps1','wait_finish_prefix145.ps1',
    'close_prefix145_storage.ps1','append_prefix145_closed.py','verify_prefix145_remote.py']
for name in sorted(set(sources)):
    source=R/name
    if name in frozen['files']:assert sha(source)==sha(W/name)==frozen['files'][name]
    content=source.read_bytes();assert b'\r' not in content,name
    assert content.endswith(b'\n') and not content.endswith(b'\n\n'),name
    (D/name).write_bytes(content)
for name in ['policy.json','freeze.json','cooldown-proof.json','cohort-failure.json','protocol-proof.json','smoke-proof.json','prefix-lifecycle-audit.json']:
    write(D/name,json.dumps(load(W/name),indent=2)+'\n')
write(D/'prefix-audit-summary.json',json.dumps({k:v for k,v in audit.items() if k!='case_checks'},indent=2)+'\n')
write(D/'worker-exits.json',json.dumps([json.loads(s) for s in (W/'worker-exits.jsonl').read_text(encoding='utf-8').splitlines()],indent=2)+'\n')
for name in ['phase145-actual-exits.json','phase145-cohort-launch-wait-started.json','phase145-cohort-launch-wait-actual-exits.json',
    'phase145-preflight-actual-exits.json','phase145-preflight-wait-actual-exits.json','phase145-preparation-actual-exits.json',
    'phase145-prefix-audit-actual-exits.json','phase145-prefix-lifecycle-actual-exits.json','phase145-prefix-audit-quiet-proof.json',
    'phase145-running-next-proof.json']:
    write(D/name,json.dumps(load(R/name),indent=2)+'\n')
for name in ['phase145-cohort-launch-wait-metadata.jsonl','phase145-prefix-audit-quiet-observations.jsonl']:
    write(D/name,''.join(json.dumps(json.loads(s),separators=(',',':'))+'\n' for s in (R/name).read_text(encoding='utf-8-sig').splitlines()))
write(D/'preflight-source-before-exit-journal.base64',(W/'preflight-source-before-exit-journal.base64').read_text(encoding='utf-8').rstrip()+'\n')
write(D/'audit-preparation-attempts.md','''# Audit helper preparation attempts

The first sandboxed Python preparation raised PermissionError before creating
wait_prefix145_audit_quiet.ps1. Its dependent launcher then exited1 on a missing
script before any quiet wait or independent auditor started. Exact preparation
was retried with authorized host access and completed0; the actual audit launch
then waited for120 observed clear seconds. No native case or Rust build repeated.
No engine, frozen timing source, policy, numerical gate or measured case changed.

The first publication launcher exited1 in its pre-publication task guard on
new Sprout qualification/compiler activity. The Python publisher never started,
no repository file was changed, and no commit existed. Its source/log remain
preserved. A separate v2 launcher preserves that guard log and can proceed only
after actual supervisors/builds are clear; it changes no engine/timing bytes.
''')
report=f'''# Compaction comparison145 interrupted prefix — October12,2026

**118 independently correct cases;98 indices118..215 unstarted. Performance
qualification rejected for possible overlapping activity. No speed result.**

Supported016 identical A/B versus joint131+144 C; this would not isolate144.
Declared216 same-D cases,12 balanced rounds/six shapes/32x1024 rows/3 columns,
RNG20261011/all six permutations per shape per half. All read/CRC/phase/index/
write/flush/sync costs charged inside compact_small. CPU8 belongs only to owned
jobs. Baseline154/candidate344 tests/two lints/wire/recovery were reused; no new
Rust tests/builds. Six excluded preflights196608 rows/4718592 CRC bytes passed.

Controller89996 actually exited1 at20:40:03Z after case117; both metadata
workers actually exited0 without forced kills. The final post-case guard found
Python78572 born20:39:59.559031Z, before native117 began20:40:00.351394Z and
exited20:40:00.661959Z. Its action is unknown. Its lifetime was not proven
outside the case, so the entire prefix is unqualified. This is neither an
engine correctness regression nor evidence of faster/slower compaction.

Independent auditors actually exited0 after fresh observed quiet: all
{audit['full_payload_rows']:,} exact rows/{audit['fully_checked_crc_bytes']:,} CRC bytes,
all indexes, original receipt digests/declared run+1 generations, head33/one
segment. All frozen bytes/order stayed exact; no case repeated or stall removed.
Every {life['actual_probes']} recorded probe was checked against all {life['native_lifetimes']}
preflight/prefix native lifetimes ({life['probe_native_interval_pairs_checked']:,} pairs).
{life['outside_lifetime_pauses']} permitted earlier waits were outside native lifetimes;
the final rejected busy observation was never treated as a permitted wait.
The one launch-gate metadata interval preceded controller/native work. A manual
read-only metadata probe has a conservative envelope inside the before17 wait;
its exact start was not recorded and that limitation is saved explicitly.

All144 full/both-half controls,144 guards and six goals remain unevaluated.
Do not retime/resume145 or adopt144 from this prefix. Next unused146+ must keep
the original release324 Native/252 service/42 goals/153 A/A/171 guards plus
correctness/recovery/sustained-service gates. Supported0.3.16 stays byte-exact;
0.3.17 remains unreleased. [Actual source/proofs](experiments/compaction_compare_145/README.md).
Short private save is freshly byte-verified before exact completed-fixture
cleanup. Useful kits/old history/tags/releases retained; no raw multiGB bundle.
'''
write(P/'COMPACTION_PREFIX_145.md',report)
write(D/'README.md','''# Rejected comparison145

The concise outcome is [COMPACTION_PREFIX_145.md](../../COMPACTION_PREFIX_145.md).
All118 attempted cases are accounted for and independently decoded;98 were
never started. No performance controls/goals evaluated or cases selected for
retiming. Actual frozen timing sources, fixed policy, original failures, both
independent audit sources and bounded exit/lifecycle proofs are saved here.
Large regenerable stores and raw streams are intentionally not uploaded.
The journal/policy/frozen source hashes identify the original rejected cohort.
Audit preparation's sandbox/missing-script attempts are preserved separately.
Supported source and every historical private ref/tag/release remain unchanged.
''')
for name,addition in [
    ('BENCHMARK_HISTORY.md','\n- [Interrupted comparison145](COMPACTION_PREFIX_145.md):118 correct,98 unstarted; possible overlap rejects performance.\n'),
    ('VERSION_SUMMARY.md','\nComparison145 stopped after118 independently correct cases;98 unstarted.\nPossible overlapping Python activity rejects performance; all full/both-half\ncontrols/goals remain unevaluated.144 stays unadopted,017 unreleased.\n[Complete prefix outcome](COMPACTION_PREFIX_145.md).\n'),
    ('README.md','\n[Comparison145 interrupted prefix](COMPACTION_PREFIX_145.md):118 independently\ncorrect cases,98 unstarted; no speed qualification because of possible overlap.\n')]:
    text=(P/name).read_text(encoding='utf-8');assert 'COMPACTION_PREFIX_145.md' not in text
    write(P/name,text.rstrip()+'\n'+addition)
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_PREFIX_145.md'}|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--','COMPACTION_PREFIX_145.md','experiments/compaction_compare_145','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256')
git('diff','--cached','--check')
assert all(n in ['COMPACTION_PREFIX_145.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_compare_145/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Preserve118-case145 prefix and reject possible benchmark overlap [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,
    'report_path':'COMPACTION_PREFIX_145.md','completed_cases':118,'unstarted_cases':98,'no_speed_qualification':True,'no_raw_bundle_uploaded':True}
write(R/'phase145-publication-proof.json',json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_prefix145_remote.py')],check=True)
