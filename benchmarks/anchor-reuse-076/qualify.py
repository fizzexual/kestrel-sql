"""Untimed, independent histories and owned process-cut qualification."""
import hashlib
import json
import queue
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
import hybrid_oracle as h
import page_oracle as o

W = Path(__file__).resolve().parent
EXE = W / 'bin/recovery-model.exe'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W / 'qualification-results.json').exists()
proof = load(W / 'build-proof.json')
assert proof['complete'] and sha(EXE) == proof['binary_sha256']
for n, d in proof['source_sha256'].items(): assert sha(W / 'model' / n) == d
assert shutil.disk_usage(W).free >= 2_500_000_000
FIX = W / 'fixtures'; FIX.mkdir()
RAW = W / 'raw'; RAW.mkdir()
INPUTS = W / 'inputs'; INPUTS.mkdir()
commands = []; histories = []; cuts = []; corruptions = []
checks = []; serial = 0
frozen = {p.name: sha(p) for p in W.glob('*.py')}
save(W / 'qualification-policy.json', {'declared_utc': now(), 'before_first_qualification_child': True,
    'model_only': True, 'no_timed_cohort': True, 'binary_sha256': sha(EXE), 'python_sha256': frozen,
    'cuts': {'anchor': ['anchor_partial','anchor_written','anchor_synced','anchor_published'],
             'delta': ['delta_partial','delta_written','delta_synced','delta_published'],
             'checkpoint': ['page_partial','page_written','page_synced','root_partial','root_written','root_synced','root_published']},
    'both_injected_errors_and_owned_kills': True, 'all_histories_exact': True,
    'cut_timeout_seconds': 60, 'child_timeout_seconds': 180, 'no_engine_or_performance_claim': True})

def persist(): save(W / 'qualification-progress.json', {'commands': commands, 'histories': histories, 'cuts': cuts, 'corruptions': corruptions, 'checks': checks})
def run(*args, expected=0):
    global serial
    serial += 1; prefix = RAW / f'{serial:04}'
    argv = [str(EXE), *map(str, args)]; started = now()
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try: out, err = p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill(); out, err = p.communicate(timeout=30)
        (prefix.with_suffix('.stdout')).write_bytes(out); (prefix.with_suffix('.stderr')).write_bytes(err)
        commands.append({'argv': argv, 'pid': p.pid, 'timeout': True, 'exit': p.returncode, 'started_utc': started, 'ended_utc': now()}); persist(); raise
    prefix.with_suffix('.stdout').write_bytes(out); prefix.with_suffix('.stderr').write_bytes(err)
    commands.append({'argv': argv, 'pid': p.pid, 'exit': p.returncode, 'started_utc': started, 'ended_utc': now()}); persist()
    assert (p.returncode == 0) if expected == 0 else (p.returncode != 0), (argv, p.returncode, err)
    return [json.loads(line) for line in out.decode('utf-8').splitlines() if line.startswith('{')]

def killed(*args, cut):
    global serial
    serial += 1; prefix = RAW / f'{serial:04}'; argv = [str(EXE), *map(str, args)]; started = now()
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    q = queue.Queue(); reader = threading.Thread(target=lambda: q.put(p.stdout.readline()), daemon=True); reader.start()
    first = b''
    try:
        first = q.get(timeout=60)
        assert first == f'CUT {cut}\n'.encode() or first == f'CUT {cut}\r\n'.encode(), (argv, first)
        p.kill(); out, err = p.communicate(timeout=30)
        assert p.returncode != 0
    finally:
        if p.poll() is None: p.kill(); out, err = p.communicate(timeout=30)
        reader.join(timeout=5)
        prefix.with_suffix('.stdout').write_bytes(first + out); prefix.with_suffix('.stderr').write_bytes(err)
        commands.append({'argv': argv, 'pid': p.pid, 'exit': p.returncode, 'cut_line': first.decode('utf-8'),
                         'task_owned_popen_kill_and_wait': True, 'started_utc': started, 'ended_utc': now()}); persist()

def check(path, expected, label, native=True):
    summary, ledger, cp, refs = h.read_store(path)
    assert ledger == expected, label
    if native:
        actual = run('hy-inspect', path)[-1]
        assert all(actual[k] == v for k, v in summary.items()), (label, summary, actual)
    checks.append({'label': label, 'path': str(path), 'full_ledger_equal': True, 'native_summary_equal': native, **summary}); persist()
    return summary, cp

def simple_input(n):
    p = INPUTS / f'simple-{n}.ks2'
    ledger = {f'old-{i:06}': {'digest': [i % 256]*32, 'rows': 1, 'generation': 1} for i in range(n)}
    p.write_bytes(o.frame(b'KSQLCAT4', {'generation': 1, 'receipt_base': None, 'table': 'events', 'columns': ['ts','value'], 'segments': [], 'batches': ledger}))
    return p

inputs = []
for item in load(W.parent / 'perf-075/input-provenance.json')['inputs']:
    source = Path(item['path']); assert sha(source) == item['sha256']
    dest = INPUTS / source.name; shutil.copy2(source, dest)
    inputs.append({'path': str(dest), 'sha256': sha(dest), 'source_075': str(source), 'source_sha256': sha(source)})
save(W / 'input-provenance.json', {'copied_utc': now(), 'inputs': inputs, 'unchanged_original_068_bytes': True})
for item in inputs:
    old = o.legacy(Path(item['path'])); expected = dict(old['batches']); width = len(old['columns'])
    store = FIX / f"history-{len(expected)}"; run('hy-import', store, item['path'])
    assert len(list(store.iterdir())) == 1
    check(store, expected, 'original anchor')
    assert o.envelope(next(store.iterdir()), b'KANC0741', 64*1024*1024) == o.envelope(Path(item['path']), b'KSQLCAT4', 64*1024*1024)
    offsets = [0, 0]
    for group in range(8):
        start = group*8; run('hy-fill', store, start, 7)
        for i in range(start, start+7): expected[f'new-{i:04}'] = o.new_record(100+i, width, old['generation']+i+1)
        i = start+7; feed = group % 2; name = f'hy074-feed-{feed}'; offset = offsets[feed]
        run('hy-source', store, name, offset, offset+7, 100+i)
        expected[o.source_id(name, offset, offset+7)] = o.new_record(100+i, width, old['generation']+i+1); offsets[feed] += 7
        check(store, expected, f'history-{len(old["batches"])} publication {i+1}')
    # Every retained committed generation has a direct full-history decode.
    historical = dict(old['batches'])
    for count in range(65):
        if count:
            i = count-1
            if i % 8 == 7:
                group = i//8; name = f'hy074-feed-{group%2}'; offset = (group//2)*7
                id = o.source_id(name, offset, offset+7)
            else: id = f'new-{i:04}'
            historical[id] = expected[id]
        summary, ledger, cp, refs = h.read_store(store, old['generation']+count)
        assert ledger == historical
    before = {p.name: sha(p) for p in store.iterdir()}
    first = run('hy-commit', store, 'new-0000', 100)[0]; assert first == {'receipt_generation': old['generation']+1, 'duplicate': True}
    first_source = run('hy-source', store, 'hy074-feed-0', 0, 7, 107)[0]; assert first_source == {'receipt_generation': old['generation']+8, 'duplicate': True}
    run('hy-commit', store, 'new-0000', 9999, expected=1)
    run('hy-source', store, 'hy074-feed-0', 29, 36, 9999, expected=1)
    assert {p.name: sha(p) for p in store.iterdir()} == before
    histories.append({'path': str(store), 'original_receipts': len(old['batches']), 'publications': 64,
                      'source_intervals': 8, 'historical_heads_directly_decoded': 65, 'retries_collision_gap_no_io': True}); persist()
    print('qualified full original history', len(old['batches']), flush=True)

small_input = simple_input(1); old = o.legacy(small_input)
delta_template = FIX / 'delta-template'; run('hy-import', delta_template, small_input)
rollover = FIX / 'rollover-template'; run('hy-import', rollover, small_input)
# 512 publications, 511 new receipts: partial tail of 511. Then 30 ordinary
# receipts and a source interval yield depth31; next commit rewrites two pages.
run('hy-metadata', rollover); run('hy-fill', rollover, 0, 511)
roll_expected = dict(old['batches'])
for i in range(511): roll_expected[f'new-{i:04}'] = o.new_record(100+i, 2, i+3)
summary, cp = check(rollover, roll_expected, 'partial tail at 511')
assert summary['delta_depth'] == 0 and cp['pages'][-1]['count'] == 511
run('hy-fill', rollover, 511, 30)
for i in range(511, 541): roll_expected[f'new-{i:04}'] = o.new_record(100+i, 2, i+3)
run('hy-source', rollover, 'cut-feed', 0, 7, 999)
roll_expected[o.source_id('cut-feed', 0, 7)] = o.new_record(999, 2, 544)
summary, cp = check(rollover, roll_expected, 'checkpoint cut template')
assert summary['generation'] == 544 and summary['delta_depth'] == 31 and cp['pages'][-1]['count'] == 511
histories.append({'path': str(rollover), 'original_receipts': 1, 'publications': 543, 'source_intervals': 1,
                  'partial_page_rollover_and_source_pending': True}); persist()

policy = load(W / 'qualification-policy.json')
for kind, stages in policy['cuts'].items():
    for mode in ['error', 'hold']:
        for cut in stages:
            path = FIX / f'{kind}-{mode}-{cut}'
            if kind == 'anchor':
                args = ('hy-import-probe', path, small_input, cut, mode)
                if mode == 'error': run(*args)
                else: killed(*args, cut=cut)
                if cut.endswith('_published'): check(path, old['batches'], f'{mode}-{cut}')
                else:
                    try: h.read_store(path)
                    except (AssertionError, ValueError, FileNotFoundError): pass
                    else: raise AssertionError(('unpublished import accepted', path))
                    run('hy-inspect', path, expected=1)
                run('hy-import', path, small_input, expected=1)
                cuts.append({'kind': kind, 'mode': mode, 'cut': cut, 'path': str(path), 'old_or_new_complete_anchor': True,
                             'retry_cannot_overwrite_retained_directory': True}); persist(); continue
            template = delta_template if kind == 'delta' else rollover
            expected = dict(old['batches']) if kind == 'delta' else dict(roll_expected)
            shutil.copytree(template, path)
            before, _, _, _ = h.read_store(path); abandoned = before['next_generation']
            id = 'cut-new' if kind == 'delta' else o.source_id('cut-feed', 7, 14)
            args = ('hy-probe', path, cut, mode, id, 12345)
            if mode == 'error':
                output = run(*args); assert output[0]['poisoned'] and output[0]['second_commit_rejected']
            else: killed(*args, cut=cut)
            published = cut.endswith('_published')
            if published: expected[id] = o.new_record(12345, 2, abandoned)
            summary, cp = check(path, expected, f'{mode}-{cut} after interruption')
            assert summary['next_generation'] > abandoned
            if kind == 'checkpoint' and published:
                assert len(cp['pages']) == 2 and cp['pages'][0]['count'] == 512 and cp['pages'][1]['count'] == 31
            result = run('hy-commit', path, id, 12345)[0]
            assert result['duplicate'] == published
            if published: assert result['receipt_generation'] == abandoned
            else:
                assert result['receipt_generation'] > abandoned
                expected[id] = o.new_record(12345, 2, result['receipt_generation'])
            check(path, expected, f'{mode}-{cut} exact retry')
            cuts.append({'kind': kind, 'mode': mode, 'cut': cut, 'path': str(path),
                         'old_or_new_full_ledger': True, 'abandoned_generation_skipped': True,
                         'exact_retry_generation': result['receipt_generation'], 'duplicate_after_published_only': result['duplicate'],
                         'source_history_and_two_page_rollover': kind == 'checkpoint'}); persist()
        print('qualified', kind, mode, len(stages), 'cuts', flush=True)

# Directly altered valid-CRC or malformed fixtures must fail both implementations.
cp_template = FIX / 'checkpoint-corruption-template'; shutil.copytree(rollover, cp_template)
run('hy-commit', cp_template, o.source_id('cut-feed', 7, 14), 12345)
dt_template = FIX / 'delta-corruption-template'; shutil.copytree(delta_template, dt_template); run('hy-fill', dt_template, 0, 2)
for kind, n in [('delta', 11), ('checkpoint', 10)]:
    for which in range(n):
        path = FIX / f'corrupt-{kind}-{which:02}'; shutil.copytree(dt_template if kind == 'delta' else cp_template, path)
        summary, ledger, cp, refs = h.read_store(path); p = path / f'head-{summary["generation"]:020}.model'
        magic, v, crc = h.head(path, summary['generation'])
        raw = None
        if kind == 'delta':
            if which == 0: v['depth'] = 32
            elif which == 1: v['parent'] = summary['generation']
            elif which == 2: v['parent_crc'] ^= 1
            elif which == 3: v['checkpoint'] = summary['generation']
            elif which == 4: v['receipt_count'] = 100001
            elif which == 5: v['records'][0]['record']['generation'] -= 1
            elif which == 6: v['records'][0]['id'] = 'new-0000'
            elif which == 7: v['records'] = v['records'] * 2
            elif which == 8: del v['parent_crc']
            elif which == 9: v['unknown'] = True
            else:
                body = o.json.dumps(v, separators=(',', ':')); body = '{"depth":2,' + body[1:]
                b = body.encode(); raw = magic + o.struct.pack('<II', len(b), o.zlib.crc32(b)) + b
        else:
            if which == 0: v['anchor_crc'] ^= 1
            elif which == 1: v['anchor_generation'] = summary['generation']
            elif which == 2: v['receipt_count'] += 1
            elif which == 3: v['pages'][0]['slot'] = 1
            elif which == 4: v['pages'][0]['count'] = 511
            elif which == 5: v['pages'][0]['generation'] = 1
            elif which == 6: v['pages'][0]['crc'] ^= 1
            elif which == 7: del v['anchor_crc']
            elif which == 8: v['unknown'] = True
            else:
                ref = v['pages'][0]; page_path = path / f"hy-receipts-{ref['generation']:020}-000.model"
                page = o.document(o.envelope(page_path, b'KPAG0741', 256*1024)); page['records'][1] = page['records'][0]
                page_body = o.json.dumps(page, separators=(',', ':')).encode(); ref['crc'] = o.zlib.crc32(page_body)
                page_path.write_bytes(o.frame(b'KPAG0741', page))
        p.write_bytes(raw if raw is not None else o.frame(magic, v))
        try: h.read_store(path)
        except (AssertionError, ValueError, KeyError, FileNotFoundError): pass
        else: raise AssertionError(('oracle accepted corrupt fixture', path))
        run('hy-inspect', path, expected=1)
        corruptions.append({'path': str(path), 'kind': kind, 'which': which, 'native_and_python_rejected': True}); persist()
# Additional valid-CRC malformed anchor inputs directly exercise changed decoding.
for which in range(9):
    path = FIX / f'corrupt-anchor-{which:02}'; shutil.copytree(delta_template, path)
    p = path / f'head-{1:020}.model'; magic,v,crc=h.head(path,1);raw=None
    if which==0:v['unknown']=True
    elif which==1:del v['table']
    elif which==2:
        body=o.json.dumps(v,separators=(',',':'));b=('{"generation":1,'+body[1:]).encode();raw=magic+o.struct.pack('<II',len(b),o.zlib.crc32(b))+b
    elif which==3:
        record=o.json.dumps(v['batches']['old-000000'],separators=(',',':'))
        b=('{"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":{"same":'+record+',"same":'+record+'}}').encode();raw=magic+o.struct.pack('<II',len(b),o.zlib.crc32(b))+b
    elif which==4:v['generation']=2
    elif which==5:v['receipt_base']=1
    elif which==6:v['batches']['old-000000']['generation']=2
    elif which==7:
        record=v['batches']['old-000000'];v['batches']={o.source_id('bad-feed',0,7):record,o.source_id('bad-feed',8,14):record}
    else:v['columns']=[]
    p.write_bytes(raw if raw is not None else o.frame(magic,v))
    try:h.read_store(path)
    except (AssertionError,ValueError,KeyError,FileNotFoundError):pass
    else:raise AssertionError(('oracle accepted malformed anchor',path))
    run('hy-inspect',path,expected=1)
    corruptions.append({'path':str(path),'kind':'anchor','which':which,'native_and_python_rejected':True});persist()
print('qualified 30 independent corrupted fixtures',flush=True)
# The changed reader must not alter any deterministic publication byte.
wire_comparisons=[]
for history in histories[:3]:
    current=Path(history['path']);old_store=W.parent/'perf-074/fixtures'/current.name
    now_files={p.name:sha(p) for p in current.iterdir() if p.is_file()}
    old_files={p.name:sha(p) for p in old_store.iterdir() if p.is_file()}
    assert now_files==old_files,('publication bytes changed',current)
    wire_comparisons.append({'history':current.name,'files':len(now_files),'all_full_file_sha_equal_original_074':True})
save(W/'publication-byte-equivalence.json',{'complete':True,'histories':wire_comparisons,'all_201_original_history_files_equal':sum(v['files'] for v in wire_comparisons)==201})

assert len(histories) == 4 and len(cuts) == 30 and len(corruptions) == 30
assert all(p['exit'] == 0 for p in commands if not ('hy-inspect' in p['argv'] or 'hy-import' in p['argv'] or 'hy-source' in p['argv'] or 'hy-commit' in p['argv']) and 'task_owned_popen_kill_and_wait' not in p)
assert sha(EXE) == proof['binary_sha256']
for n, d in proof['source_sha256'].items(): assert sha(W / 'model' / n) == d
save(W / 'fixture-inventory.json', {p.relative_to(FIX).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(FIX.rglob('*')) if p.is_file()})
result = {'complete': True, 'model_only': True, 'no_timed_cohort': True, 'histories': histories,
          'full_history_checks': checks, 'cuts': cuts, 'corruptions': corruptions,
          'native_commands': len(commands), 'all_owned_children_exited_or_killed_and_waited': True,
          'controlled_kills': 15, 'injected_errors': 15, 'direct_historical_heads_decoded': 195,
          'independent_corruption_cases_rejected': 30, 'binary_sha256': sha(EXE), 'completed_utc': now(),
          'default_engine_changed': False, 'physical_power_loss_qualified': False, 'reader_changed_only': True, 'publication_bytes_unchanged': True}
save(W / 'qualification-results.json', result)
print(json.dumps({k: v for k, v in result.items() if k not in ['histories','full_history_checks','cuts','corruptions']}))
