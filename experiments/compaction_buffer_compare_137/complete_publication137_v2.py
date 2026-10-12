"""Finish the saved partial publication; no benchmark or engine byte changes."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import base64, hashlib, json, os, subprocess

R = Path('D:/Codex/Kestrel'); W = R/'work/perf-137'; P = R/'outputs/kestrel-sql'
D = P/'experiments/compaction_buffer_compare_137'
old_source = R/'work/publish_compare137.py'
namespace = {}
text = old_source.read_text(encoding='utf-8')
exec(compile(text[:text.index('a = load(')], str(old_source)+'.helpers', 'exec'), namespace)
git = namespace['git']; sha = namespace['sha']; load = namespace['load']; GH = namespace['GH']
assert load(R/'work/phase137-publication-actual-exits.json')['publication_actual_exit'] == 1
assert not (R/'work/phase137-publication-proof.json').exists()
assert (D/'publish_compare137.py').read_bytes() == old_source.read_bytes()
a = load(W/'audit.json'); life = load(W/'lifecycle-receipt-audit.json'); policy = load(W/'policy.json'); freeze = load(W/'freeze.json')
assert a['correctness_passed'] and a['fresh_cases'] == 216 and len(a['identity_failed']) == 32 and len(a['guards_failed']) == 13
assert all(sha(W/name) == digest for name, digest in freeze['files'].items())
assert life['original_receipts_checked'] == 2304 and life['actual_probes'] == 457 and life['all_probe_intervals_outside_every_native_lifetime']
assert git('rev-parse','HEAD').strip() == policy['source_commit']
allowed = ['COMPACTION_BUFFER_COMPARE_137.md','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256']
assert all(name in allowed or name.startswith('experiments/compaction_buffer_compare_137/') for name in git('diff','--cached','--name-only').splitlines())
core = load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/name) == digest for name, digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']

cleanup = R/'work/close_compare137_storage.ps1'; failed_bytes = cleanup.read_bytes()
assert failed_bytes.count(b'\r\n') == 3
saved_failure = D/'close_compare137_storage.failed-attempt1.ps1.base64'
assert not saved_failure.exists()
saved_failure.write_text(base64.b64encode(failed_bytes).decode()+'\n', encoding='ascii', newline='\n')
assert base64.b64decode(saved_failure.read_text()) == failed_bytes
corrected = failed_bytes.replace(b'\r\n', b'\n')
assert corrected.count(b'phase137-publication-actual-exits.json') == 1
corrected = corrected.replace(b'phase137-publication-actual-exits.json', b'phase137-publication-v2-actual-exits.json')
cleanup.write_bytes(corrected); (D/cleanup.name).write_bytes(corrected)
append = R/'work/append_compare137_closed.py'
append_text = append.read_text(encoding='utf-8')
assert 'no new Rust builds/tests or failed137 attempt.' in append_text
append_text = append_text.replace('no new Rust builds/tests or failed137 attempt.',
    'no new Rust builds/tests or failed timing/audit attempt. Publication attempt1\nexited1 on mixed line endings in the cleanup helper; exact failed source and\nexit retained. Separatev2 normalizes three CRLF lines and uses its actual exit\nproof, without changing the completed cohort, engine, frozen inputs or gates.')
append.write_text(append_text, encoding='utf-8', newline='\n'); (D/append.name).write_bytes(append.read_bytes())
for name in ['README.md']:
    f = D/name; s = f.read_text(encoding='utf-8')
    assert 'No failed137 attempt.' in s
    s = s.replace('No failed137 attempt.', 'No failed timing/preflight/audit attempt. Publication attempt1 exited1 at the\nprecommit whitespace check; see [saved failure](FAILED_PUBLICATION.md).')
    f.write_text(s, encoding='utf-8', newline='\n')
f = P/'COMPACTION_BUFFER_COMPARE_137.md'; s = f.read_text(encoding='utf-8')
assert 'No failed137 attempt.' in s
s = s.replace('No failed137 attempt.', 'No failed timing/preflight/audit attempt. Publication attempt1 failed on mixed\ncleanup-helper line endings before commit; separatev2 corrects those three\nlines and preserves the [actual failed source/exit](experiments/compaction_buffer_compare_137/FAILED_PUBLICATION.md).')
f.write_text(s, encoding='utf-8', newline='\n')
failure_exit = load(R/'work/phase137-publication-actual-exits.json')
(D/'FAILED_PUBLICATION.md').write_text(f'''# Publication attempt1

Actual exit1 at {failure_exit['utc']}, before any commit/push/cleanup. Git's
precommit diff check found three CRLF lines mixed into an LF cleanup helper
(lines11,39,40). The failed publisher source is retained byte-exact as
publish_compare137.py. Exact failed cleanup bytes are in
close_compare137_storage.failed-attempt1.ps1.base64, SHA256
`{hashlib.sha256(failed_bytes).hexdigest()}` ({len(failed_bytes)} bytes).
Separate complete_publication137_v2.py normalizes those three line endings,
uses its separate actual publication-exit proof and finishes the existing
staged report/source. It does not rerun any case or change engine/frozen policy,
schedule, numerical gates, binary bytes or completed audit results. No raw bundle.
''', encoding='utf-8', newline='\n')
for name in ['complete_publication137_v2.py','launch_publish_compare137_v2.ps1']:
    (D/name).write_bytes((R/'work'/name).read_bytes())
tracked = sorted(set(git('ls-files').splitlines()) | {p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name != 'MANIFEST.sha256'), encoding='utf-8', newline='\n')
git('add','--',*allowed,'experiments/compaction_buffer_compare_137'); git('diff','--cached','--check')
assert all(name in allowed or name.startswith('experiments/compaction_buffer_compare_137/') for name in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject buffer-only137 with full audits and preserve failed publication [skip ci]')
head = git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0] == head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/name) == digest for name,digest in core.items())
proof = {'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
    'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':32,'guard_failures':13,'goal_failures':6,
    'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True,'publication_attempt1_actual_exit':1,'failed_source_preserved':True,'completion_attempt':2}
(R/'work/phase137-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(proof), flush=True)
names = allowed + sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote = subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'], timeout=90)
    assert remote == (P/name).read_bytes(), name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: rows = list(pool.map(check,names))
remoteproof = {'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,
    'fresh_remote_text_and_source_byte_exact':True,'all137_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase137-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}), flush=True)
