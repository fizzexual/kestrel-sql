"""Short private148 outcome/source save before completed fixture cleanup."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148';P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_compare_148'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1500:],c.stderr[-1500:]);return c.stdout.decode('utf-8')
policy=load(W/'policy.json');audit=load(W/'prefix-audit.json');life=load(W/'prefix-lifecycle-audit.json')
assert audit['independent_correctness_passed'] and audit['completed_cases']==10 and audit['unstarted_indices']==list(range(10,216))
assert life['complete'] and life['no_qualification_metrics_evaluated'] and life['probe_native_interval_pairs_checked']==1248
for name,key in [('phase148-prefix-audit-actual-exits.json','prefix_audit_actual_exit'),('phase148-prefix-lifecycle-actual-exits.json','prefix_lifecycle_actual_exit')]:assert load(R/name)[key]==0
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
frozen=load(W/'freeze.json');sources=[n for n in frozen['files'] if n.endswith(('.py','.ps1'))]
sources+=['audit_prefix148.py','audit_prefix148_lifecycle.py','prepare_prefix148_audits.py','launch_prefix148_audits.ps1','wait_prefix148_audit_quiet.ps1',
    'prepare_payload_compare148.ps1','append_phase148_ready.py','wait_quiet_preflight148.py','launch_ready_preflight148.ps1',
    'prepare_quiet_preflight148_v2.py','activity_quiet_preflight148_v2.ps1','wait_quiet_preflight148_v2.py','launch_ready_preflight148_v2.ps1',
    'publish_prefix148.py','verify_prefix148_remote.py','launch_publish_prefix148.ps1','launch_publish_prefix148_v2.ps1','close_prefix148_storage.ps1','append_prefix148_closed.py','prepare_prefix148_publication.py']
for name in sorted(set(sources)):
    p=R/name
    if name in frozen['files']:assert sha(p)==sha(W/name)==frozen['files'][name]
    data=p.read_bytes();assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'),name
    (D/name).write_bytes(data)
for name in ['policy.json','freeze.json','cooldown-proof.json','cohort-failure.json','protocol-proof.json','smoke-proof.json','prefix-lifecycle-audit.json']:
    write(D/name,json.dumps(load(W/name),indent=2))
write(D/'prefix-audit-summary.json',json.dumps({k:v for k,v in audit.items() if k!='case_checks'},indent=2))
write(D/'worker-exits.json',json.dumps([json.loads(s) for s in (W/'worker-exits.jsonl').read_text(encoding='utf-8').splitlines()],indent=2))
for name in ['phase148-actual-exits.json','phase148-preparation-actual-exits.json','phase148-preflight-actual-exits.json','phase148-preflight-quiet-actual-exits.json',
    'phase148-preflight-quiet-v2-actual-exits.json','phase148-preflight-quiet-v2-proof.json','phase148-quiet-helper-correction.json',
    'phase148-prefix-audit-actual-exits.json','phase148-prefix-lifecycle-actual-exits.json','phase148-prefix-audit-quiet-proof.json',
    'phase148-running-next-proof.json','payload148-controller-derivation.json']:
    write(D/name,json.dumps(load(R/name),indent=2))
write(D/'failed-quiet-helper.log',(R/'phase148-preflight-quiet.log').read_text(encoding='utf-8-sig'))
write(D/'attempts.md','''# Preserved148 harness attempts

The first metadata-only quiet helper failed before any native case. The original
worker's exact owner allowlist rejected the helper name; cleanup then attempted
a closed stdin. Actual helper exit1 is saved; that worker's actual exit was not
separately waited or saved. The separate v2 permits only the exact quiet-helper
owner path/PID/FILETIME and keeps every reset/task/supervisor/build check. V2
observed123.656 continuous clear seconds, worker exited0, then all six excluded
native preflights ran once. The main worker/source, binaries/policy/order/gates
did not change. Before freeze, the auditor's preflight condition separated
metadata-only quiet[0,3] from strict native preflight_before/after exit0, with
final quiet>=120 and worker0 required. The original146 parent sources and actual
deriver identify the exact pre-adjustment code; the frozen148 source is saved.

Prefix helper creation was sandbox-denied before writing audit_prefix148.py.
Its dependent launcher failed on the absent script before any auditor started.
The exact authorized host retry completed0; both auditors then ran once after
122.434 continuously observed clear seconds/two busy resets. No engine case,
passed prerequisite or qualification timing was repeated.

The first publication launcher was guard-held before Python publisher creation;
no destination, repository edit or commit existed. Its source remains preserved.
A separate v2 launcher uses fresh guards and separate logs; no engine, frozen
cohort source, native case or already-passed audit changed or repeated.
''')
report=f'''# Compaction comparison148 interrupted — October13,2026

**10 independently correct cases;206 indices10..215 unstarted. Speed
qualification rejected for possible overlapping activity; no speed result.**

Supported0.3.16 identical A/B versus joint131+144+147 C; this does not isolate147.
Declared216 balanced same-D cases,12 rounds/six shapes/32x1024 rows/three
columns,RNG20261011/all six permutations per shape per half. All input/readCRC/
phase/index/write/flush/sync work charged inside compact_small. Baseline154 and
candidate348 tests/two lints/52 stores/wire/recovery explicitly reused; no new
Rust build/test. Six fresh excluded preflights196608 rows/4718592 CRC bytes pass.

Controller actual exit1 at23:06:48Z after case9; all10 native exits0. The final
case lived23:06:44.579360..23:06:45.004443Z. New pwsh103508 and Python51924
were born inside that native lifetime; later Python87544/Sprout101672 were also
observed. Their actions are unknown; overlap with the inner compaction clock
is neither proved nor disproved. The guard rejects the entire prefix rather
than allowing a wait. No unrelated process was stopped or messaged.

Both independent auditors actual exit0 after122.434 observed clear seconds:
all{audit['full_payload_rows']:,} exact rows/{audit['fully_checked_crc_bytes']:,} CRC bytes,
full indexes, original receipt digests and{life['original_receipts_checked']} independently
declared generations, head33/one segment pass. All78 recorded metadata probes
were outside all16 native lifetimes ({life['probe_native_interval_pairs_checked']:,} pairs).
Frozen source/policy/binaries remained exact; every attempted sample/stall kept
once. Three successfully started metadata workers actual exit0/no forced kills.
An earlier rejected quiet-only helper has an unrecorded worker exit; this
limitation and all failed/corrected sources are saved separately.

All144 full/both-half A/A controls,144 guards and six goals remain UNEVALUATED.
Do not resume/retime148 or adopt147 from it. Original release324 Native/252
service/42 goals/153 A/A/171 guards plus correctness/retry/recovery/sustained
service remain unchanged. Supported0.3.16 stays exact;0.3.17 unreleased.
[Actual source and bounded proofs](experiments/compaction_payload_compare_148/README.md).
Short private save is freshly byte-verified before exact completed-fixture
cleanup; useful kits and old private history/tags/releases remain. No raw bundle.
'''
write(P/'COMPACTION_PREFIX_148.md',report)
write(D/'README.md','''# Rejected148 prefix

[Concise outcome](../../COMPACTION_PREFIX_148.md). All10 attempted cases were
independently decoded;206 never started. All performance controls/goals remain
unevaluated. No selected retiming, outlier discard or engine adoption. Actual
frozen controllers, fixed policy, failed/corrected helpers and bounded proof
summaries are saved. Journal/policy/source hashes identify the original cohort.
Large regenerable stores/raw streams intentionally are not uploaded.
''')
for name,addition in [
    ('BENCHMARK_HISTORY.md','- [Interrupted payload comparison148](COMPACTION_PREFIX_148.md):10 correct,206 unstarted; possible overlap rejects performance.'),
    ('VERSION_SUMMARY.md','Comparison148:10 independently correct cases;206 unstarted. Possible background overlap rejects performance;147 speed unqualified,017 unreleased. [Outcome](COMPACTION_PREFIX_148.md).'),
    ('README.md','[Payload comparison148](COMPACTION_PREFIX_148.md):10 correct,206 unstarted; no speed qualification because of possible background overlap.')]:
    old=(P/name).read_text(encoding='utf-8');assert 'COMPACTION_PREFIX_148.md' not in old
    write(P/name,old.rstrip()+'\n\n'+addition)
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_PREFIX_148.md'}|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--','COMPACTION_PREFIX_148.md','experiments/compaction_payload_compare_148','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256')
git('diff','--cached','--check')
assert all(n in ['COMPACTION_PREFIX_148.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_payload_compare_148/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Preserve ten-case148 prefix and reject possible background overlap [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'completed_cases':10,'unstarted_cases':206,'no_speed_qualification':True,'report_path':'COMPACTION_PREFIX_148.md','no_raw_bundle_uploaded':True}
write(R/'phase148-publication-proof.json',json.dumps(proof,indent=2));print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_prefix148_remote.py')],check=True)
