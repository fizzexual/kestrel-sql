"""Save concise complete outcomes and actual source; preserve supported016."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, subprocess

R = Path('D:/Codex/Kestrel'); W = R/'work/perf-137'; P = R/'outputs/kestrel-sql'
D = P/'experiments/compaction_buffer_compare_137'
GH = 'C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def git(*args):
    result = subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args], capture_output=True, timeout=300,
        env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert result.returncode == 0, (args, result.stdout[-2000:], result.stderr[-2000:])
    return result.stdout.decode()

a = load(W/'audit.json'); life = load(W/'lifecycle-receipt-audit.json')
policy = load(W/'policy.json'); freeze = load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases'] == 216
assert a['full_payload_rows'] == 7077888 and a['fully_checked_crc_bytes'] == 169869312
assert len(a['summaries']) == 144 and len(a['identity_failed']) == 32 and len(a['guards_failed']) == 13
goals = [s for s in a['summaries'] if 'goal_pass' in s]
assert len(goals) == 6 and not any(s['goal_pass'] for s in goals)
assert life['complete'] and life['actual_probes'] == 457 and life['original_receipts_checked'] == 2304
assert life['probe_native_interval_pairs_checked'] == 98712 and life['all_probe_intervals_outside_every_native_lifetime']
assert a['between_case_pauses'] == life['between_case_pauses'] == 0
assert all(sha(W/n) == digest for n, digest in freeze['files'].items())
for name, key in [('phase137-actual-exits.json','cohort_actual_exit'), ('phase137-audit-actual-exits.json','audit_actual_exit'), ('phase137-lifecycle-actual-exits.json','lifecycle_actual_exit')]:
    assert load(R/'work'/name)[key] == 0
assert load(R/'work/phase137-audit-quiet-proof.json')['continuous_observed_clear_seconds'] >= 120
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('rev-parse','HEAD').strip() == policy['source_commit']
core = load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n) == digest for n, digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists(); D.mkdir()
sources = [name for name in freeze['files'] if name.endswith(('.py','.ps1'))]
sources += ['prepare_buffer_compare137.ps1','buffer137-controller-derivation.json','analyze_compare137.py','inspect_compare137.ps1',
            'wait_compare137_audit_quiet.ps1','publish_compare137.py','launch_publish_compare137.ps1',
            'close_compare137_storage.ps1','append_compare137_closed.py']
for name in sorted(set(sources)):
    source = R/'work'/name
    if (W/name).exists(): assert source.read_bytes() == (W/name).read_bytes()
    (D/name).write_bytes(source.read_bytes())

failed = []
for family, items, key in [('A/A',a['identity_failed'],'AA_paired'), ('guard',a['guards_failed'],'CA_paired'), ('goal',goals,'CA_paired')]:
    for s in items:
        failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL / inconclusive'} |")
assert len(failed) == 51
(D/'FAILED_CHECKS.md').write_text('''# Every failed check —137

32/144 A/A,13/144 guards and6/6 speed goals fail. Five failed guards have
passing corresponding controls. Failed A/A makes that comparison inconclusive.
P95 uses nearest-rank quantile ratios (max with12/full or6/half samples); other
metrics use median within-round ratios. Every sample stayed; no selected retiming.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
''' + '\n'.join(failed) + '\n', encoding='utf-8', newline='\n')
(D/'README.md').write_text('''# Complete bounded-buffer comparison137

Exact131 A/B versus exact136 C; same original compaction_merge_121 durable
driver and independent099 decoder.216 cases/12 rounds/six shapes/32x1024 rows/
three columns/RNG20261011, all six permutations per shape per half. Reuse131's
340 tests and136's344 tests/two lints/six exact wire pairs/14 recovery cases.
No new Rust build/test. Every CRC/input/read/phase/index/write/flush/sync cost
is charged inside Archive.compact_small; setup and safety waits are outside.

Actual controller/native children/two metadata workers/two auditors exited0.
All216 full payload/index/CRC/original receipt/generation checks pass. Original
receipt generations are derived from declared run+1, independently of stdout.
Every457 metadata probe is checked against every216 native lifetime (98,712
pairs). Frozen source/decoder/binary bytes remain exact. Both explicit syncs,
ACK/receipt order and format remain. No physical power-loss proof.

120 continuous observed clear seconds after preparation/freezes; reset on busy.
Owned CPU8 only, no global settings or unrelated process changed. One owned
metadata worker blocks on stdin during each native lifetime. Declared outside-
lifetime waits unchanged: before busy starts no timer; after busy only when all
blocker births>=native exit+100ms AND>=post-probe start. Missing times/reset
activity/possible overlap rejects the prefix. Zero actual pauses occurred.
All cases/order/stalls kept exactly once; no metric selection or retiming.

Fresh six excluded preflights/idle dummy/five classification checks passed.
No failed137 attempt. Main and additive audits started only after actual cohort
termination and127.22 observed clear seconds. Snapshot checks cannot exclude
every brief unseen task. Results fail32 A/A/13 guards/all six goals; do not adopt
136 from this component trial. Full/both-half whole clustered medians are lower
with passing corresponding controls, but miss the goals; five calibrated
regressions remain. Tail comparisons with failed controls stay inconclusive.

Use fresh numbers/paths/current provenance to reproduce, never overwrite137.
Original324 Native/252 service/42 goals/153 A/A/171 guards plus correctness,
recovery and sustained service remain before supported adoption.0.3.16 unchanged,
0.3.17 unreleased. Source and short outcomes privately fresh-byte verified,
then native exact completed cleanup; no multiGB raw bundle or history deletion.
''', encoding='utf-8', newline='\n')

def summary(shape, metric, scope='full'):
    return next(s for s in a['summaries'] if s['workload'] == shape and s['metric'] == metric and s['scope'] == scope)
table = []
for shape in policy['component_configs']:
    w = summary(shape, 'wall_ms'); tail = summary(shape, 'wall_p95_ms'); io = summary(shape, 'write_sync_ms')
    table.append(f"| {shape} | {w['variants']['baseline_a']['p50']:.5f} | {w['variants']['candidate']['p50']:.5f} | {(w['CA_paired']-1)*100:+.2f}% | {(io['CA_paired']-1)*100:+.2f}% | {tail['variants']['baseline_a']['p95']:.4f}/{tail['variants']['candidate']['p95']:.4f} | {'pass' if tail['AA_pass'] else 'FAIL / inconclusive'} |")
cluster_halves = [summary('clustered', 'wall_ms', scope) for scope in ['full','first_half','second_half']]
assert all(s['AA_pass'] and s['candidate_guard_pass'] and s['CA_paired'] < 1 for s in cluster_halves)
calibrated = [s for s in a['guards_failed'] if s['AA_pass']]
assert len(calibrated) == 5
regressions = '\n'.join(f"- {s['workload']}, {s['scope']}, {s['metric']}: C/A{s['CA_paired']:.6f}, A/A{s['AA_paired']:.6f}." for s in calibrated)
report = f'''# Buffer-only comparison137 — October12,2026

**REJECTED: all216 stores are independently correct, but32/144 identity checks,
13/144 guards and all six goals fail. Five failed guards have passing controls.
Supported0.3.16 stays unchanged;0.3.17 is unreleased.**

Exact131 A/B versus [bounded buffer136](COMPACTION_BUFFER_136.md) isolates
buffering without WRITE_THROUGH. It does not combine ratios across earlier
133/135 runs or qualify whole-engine/service/competitor performance.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired write+sync change | Before/after p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

Clustered whole p50 is5.59750->5.43275ms; paired whole time is3.15% lower and
write+sync4.26% lower. Whole full/first-half/second-half ratios are0.968549,
0.956605,0.988157 with passing corresponding controls/guards. All six clustered
goals still FAIL: whole<=.95/write+sync<=.90. None of these ratios qualify release.
The other five full whole paired medians are0.48–1.86% higher.

Median changes use medians of within-round C/A, which can differ from quotients
of the displayed medians. P95 uses nearest-rank B/A,C/A quantile ratios; with12
full or6 half samples, p95/p99/max coincide. Every stall stays. All six full
whole p95 controls FAIL, so apparent full-tail gains/losses are inconclusive.
For example interleaved40.7862->7.8491ms has failed A/A1.269219; ordered baselineB
has a large stall (full p95 A/A8.751698), so neither establishes a reliable tail
improvement. Late second-half p95 has passing A/A and a calibrated loss below.
This locates measured intervals and comparisons, not an exclusive disk cause.

The five calibrated failed guards are:

{regressions}

[Every51 failed check](experiments/compaction_buffer_compare_137/FAILED_CHECKS.md)
includes32 identity failures,13 guards and six goals. No discarded outlier or
selected retiming. Other guard failures with failed corresponding controls are
inconclusive rather than established engine regressions.

All216 native children/controller/both metadata workers/main and additive
auditors actually exited0, no forced kills. Independently checked7,077,888 exact
rows /169,869,312 CRC bytes, all indexes, head generations and original receipts.
457 probe intervals checked against every native lifetime (98,712 pairs),2304
original receipt generations derived from declared run+1. All frozen controller,
decoder and binary bytes exact; zero actual between-case pauses. Both explicit
syncs/receipt/ACK ordering and format remain; no physical power-loss claim.

12 fixed balanced rounds/six shapes/32x1024 rows/three columns, same physicalD,
owned CPU8,120 continuous observed clear seconds after preparation/freezes.
Fresh six excluded preflights checked196608 rows /4718592 CRC bytes; owned idle
dummy busy-clear/five birth classification tests passed.131340/136344 tests,
two lints/six exact wire pairs/14 recovery cases are REUSED, no new Rust build.
No failed137 attempt. Audits followed actual controller exit and127.22 observed
clear seconds. Sampling cannot exclude every brief hidden background task.

Policy SHA256:`{sha(W/'policy.json')}`.
Raw journal SHA256:`{a['raw_controller_SHA256']}`.
131 SHA256:`{policy['binary_sha256']['baseline.exe']}`.
136 SHA256:`{policy['binary_sha256']['candidate136.exe']}`.
[Actual controllers and independent auditors](experiments/compaction_buffer_compare_137/README.md).
Useful source/concise failures privately verified before exact native cleanup;
no new raw bundle or historical private refs/releases removed. Original324
Native/252 service/42 goals/153 A/A/171 guards plus recovery/sustained gates
remain. Next improvements must target measured preparation/merge/read costs
or service bottlenecks; no selected rerun of137 or unsupported adoption of136.
'''
(P/'COMPACTION_BUFFER_COMPARE_137.md').write_text(report, encoding='utf-8', newline='\n')
for name, marker, addition in [
    ('BENCHMARK_HISTORY.md', '- [Untimed buffer-only alternative136]', '- [Complete buffer-only comparison137](COMPACTION_BUFFER_COMPARE_137.md)\n'),
    ('VERSION_SUMMARY.md', 'New buffer-only alternative136', 'Complete137 is rejected:216 independently correct stores,32/144 A/A,13/144\nguards and all six goals fail. Clustered paired whole time is3.15% lower, short\nof its goal; five calibrated regressions remain. [Results and failures](COMPACTION_BUFFER_COMPARE_137.md).\n\n'),
    ('README.md', '[Buffer-only alternative136]', '[Complete buffer-only comparison137](COMPACTION_BUFFER_COMPARE_137.md):216 correct\ncases,32 controls/13 guards/all six goals fail;0.3.17 remains unreleased.\n\n'),
]:
    f = P/name; text = f.read_text(encoding='utf-8')
    assert text.count(marker) == 1, (name, marker)
    f.write_text(text.replace(marker, addition + marker, 1), encoding='utf-8', newline='\n')
f = P/'VERSION_SUMMARY.md'; text = f.read_text(encoding='utf-8')
assert 'Speed remains\nunmeasured. [Code and correctness](COMPACTION_BUFFER_136.md).' in text
text = text.replace('Speed remains\nunmeasured. [Code and correctness](COMPACTION_BUFFER_136.md).', 'Performance was measured and rejected in137. [Code and correctness](COMPACTION_BUFFER_136.md).')
f.write_text(text, encoding='utf-8', newline='\n')
tracked = sorted(set(git('ls-files').splitlines()) | {'COMPACTION_BUFFER_COMPARE_137.md'} | {p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name != 'MANIFEST.sha256'), encoding='utf-8', newline='\n')
git('add','--','COMPACTION_BUFFER_COMPARE_137.md','experiments/compaction_buffer_compare_137','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256')
git('diff','--cached','--check')
assert all(name in ['COMPACTION_BUFFER_COMPARE_137.md','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256'] or name.startswith('experiments/compaction_buffer_compare_137/') for name in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject buffer-only137 after full cohort and independent lifecycle audits [skip ci]')
head = git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0] == head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n) == h for n, h in core.items())
proof = {'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
    'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':32,'guard_failures':13,'goal_failures':6,
    'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/phase137-publication-proof.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(proof), flush=True)
names = ['COMPACTION_BUFFER_COMPARE_137.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256'] + sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote = subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'], timeout=90)
    assert remote == (P/name).read_bytes(), name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: rows = list(pool.map(check, names))
remoteproof = {'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,
    'fresh_remote_text_and_source_byte_exact':True,'all137_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase137-remote-save-proof.json').write_text(json.dumps(remoteproof, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}), flush=True)
