"""Independent bounded 074 reader; every logical history is checked in Python."""
import hashlib
import re
from pathlib import Path
import page_oracle as o

def ledger_sha(ledger):
    canonical = {id: {k: r[k] for k in ['digest', 'rows', 'generation']} for id, r in sorted(ledger.items())}
    return hashlib.sha256(o.json.dumps(canonical, separators=(',', ':')).encode()).hexdigest()

def head(path, g):
    p = path / f'head-{g:020}.model'
    with p.open('rb') as stream: magic = stream.read(8)
    budgets = {b'KANC0741': 64*1024*1024, b'KHED0741': 512*1024, b'KDEL0741': 4096}
    assert magic in budgets, ('unknown head magic', p)
    b = o.envelope(p, magic, budgets[magic])
    return magic, o.document(b), o.zlib.crc32(b)

def anchor(path, g):
    magic, v, crc = head(path, g)
    assert magic == b'KANC0741'
    o.fields(v, 'generation receipt_base table columns segments batches')
    o.schema(v); assert type(v['generation']) is int and v['generation'] == g > 0
    assert v['receipt_base'] is None and len(v['batches']) <= o.MAX_IDS
    for id, r in v['batches'].items(): o.record(id, r, g)
    o.positions(v['batches'])
    return v, crc

def read_store(path, generation=None):
    path = Path(path); finals = []; next_generation = 1
    for p in path.iterdir():
        m = re.fullmatch(r'head-([0-9]{20})\.model', p.name)
        if m: finals.append(int(m[1]))
        m = re.fullmatch(r'head-([0-9]{20})\.(model|pending)', p.name) or re.fullmatch(r'hy-receipts-([0-9]{20})-([0-9]{3})\.model', p.name)
        if m and (not p.name.startswith('hy-') or int(m[2]) < 196): next_generation = max(next_generation, int(m[1]) + 1)
    assert finals and max(finals) > 0
    o.integer(next_generation, 1, 2**64-1)
    latest = max(finals) if generation is None else generation
    assert latest in finals and latest > 0
    g = latest; chain = []; referenced = []
    while True:
        magic, v, crc = head(path, g); referenced.append(f'head-{g:020}.model')
        if chain: assert chain[-1]['parent_crc'] == crc
        if magic == b'KDEL0741':
            o.fields(v, 'generation parent parent_crc checkpoint depth receipt_count records')
            assert len(chain) < 31 and type(v['generation']) is int and v['generation'] == g
            o.integer(v['checkpoint'], 1, g-1); o.integer(v['parent'], v['checkpoint'], g-1)
            o.integer(v['parent_crc'], 0, 2**32-1); o.integer(v['depth'], 1, 31)
            o.integer(v['receipt_count'], 0, o.MAX_IDS)
            assert isinstance(v['records'], list) and len(v['records']) <= 1
            if chain: assert chain[-1]['checkpoint'] == v['checkpoint'] and chain[-1]['depth'] == v['depth'] + 1
            chain.append(v); g = v['parent']; continue
        if magic == b'KHED0741':
            o.fields(v, 'generation anchor_generation anchor_crc receipt_count pages')
            assert type(v['generation']) is int and v['generation'] == g
            o.integer(v['anchor_generation'], 1, g-1); o.integer(v['anchor_crc'], 0, 2**32-1)
            o.integer(v['receipt_count'], 0, o.MAX_IDS)
            assert isinstance(v['pages'], list) and len(v['pages']) <= 196
            checkpoint = v
        else:
            a, crc = anchor(path, g)
            checkpoint = {'generation': g, 'anchor_generation': g, 'anchor_crc': crc,
                          'receipt_count': len(a['batches']), 'pages': []}
        if chain: assert chain[-1]['depth'] == 1 and chain[-1]['checkpoint'] == g
        break
    a, crc = anchor(path, checkpoint['anchor_generation'])
    assert crc == checkpoint['anchor_crc']
    anchor_name = f"head-{checkpoint['anchor_generation']:020}.model"
    if anchor_name not in referenced: referenced.append(anchor_name)
    ledger = dict(a['batches'])
    new_count = checkpoint['receipt_count'] - len(ledger)
    assert new_count >= 0 and len(checkpoint['pages']) == (new_count + 511) // 512
    for slot, r in enumerate(checkpoint['pages']):
        o.fields(r, 'generation slot count crc')
        o.integer(r['generation'], checkpoint['anchor_generation'] + 1, checkpoint['generation'])
        o.integer(r['slot'], slot, slot); o.integer(r['count'], 1, 512); o.integer(r['crc'], 0, 2**32-1)
        assert slot == len(checkpoint['pages']) - 1 or r['count'] == 512
        name = f"hy-receipts-{r['generation']:020}-{slot:03}.model"
        b = o.envelope(path / name, b'KPAG0741', 256*1024)
        assert o.zlib.crc32(b) == r['crc']; page = o.document(b)
        o.fields(page, 'generation slot records')
        o.integer(page['generation'], r['generation'], r['generation']); o.integer(page['slot'], slot, slot)
        assert isinstance(page['records'], list) and len(page['records']) == r['count']
        for e in page['records']:
            o.fields(e, 'id record'); o.record(e['id'], e['record'], r['generation'])
            assert e['record']['generation'] > checkpoint['anchor_generation']
            assert e['id'] not in ledger and len(ledger) < o.MAX_IDS
            ledger[e['id']] = e['record']
        referenced.append(name)
    assert len(ledger) == checkpoint['receipt_count']; o.positions(ledger)
    for d in reversed(chain):
        for e in d['records']:
            o.fields(e, 'id record'); o.record(e['id'], e['record'], d['generation'])
            assert e['record']['generation'] == d['generation'] and e['id'] not in ledger and len(ledger) < o.MAX_IDS
            ledger[e['id']] = e['record']
        assert len(ledger) == d['receipt_count']; o.positions(ledger)
    summary = {'generation': latest, 'next_generation': next_generation, 'receipts': len(ledger),
               'pages': len(checkpoint['pages']), 'delta_depth': chain[0]['depth'] if chain else 0,
               'anchor_generation': checkpoint['anchor_generation'], 'ledger_sha256': ledger_sha(ledger),
               'positions': o.positions(ledger)}
    return summary, ledger, checkpoint, referenced
