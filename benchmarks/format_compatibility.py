"""Explicit legacy catalog read and old-binary downgrade rejection checks."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--old-binary', type=Path, required=True)
    parser.add_argument('--new-catalog-magic', default='KSQLCAT3', choices=['KSQLCAT3','KSQLCAT4'])
    parser.add_argument('--receipt-binary', type=Path, help='Also upgrade a CAT3 archive from this older bridge')
    parser.add_argument('--binary', type=Path, default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--output', type=Path, default=ROOT/'benchmarks'/'format-v03.json')
    parser.add_argument('--work', type=Path, default=ROOT.parent.parent/'work'/f'format-v03-{time.time_ns()}')
    args = parser.parse_args()
    directory = args.work/'store'
    directory.mkdir(parents=True)
    archive = directory/'archive'
    old = args.old_binary.resolve()
    subprocess.check_output([str(old), '--archive', str(archive), '--scale', '1000', '3'], text=True)
    assert next(archive.glob('catalog-*.ks2')).read_bytes()[:8] == b'KSQLCAT2'
    engine = Engine('kestrel', directory, 0, args.binary.resolve(), {}, existing=True)
    try:
        connection = engine.connect()
        assert connection.query('SELECT COUNT(*) FROM events') == [[1000]]
        request = {'op':'append','id':'upgrade:one','data':[[1001,7,1]]}
        assert not connection.call(request)['duplicate']
        connection.close()
        engine.finish()
        newest_catalog = max(archive.glob('catalog-*.ks2'), key=lambda p: int(p.stem.split('-')[-1]))
        assert newest_catalog.read_bytes()[:8] == args.new_catalog_magic.encode()
        downgraded = subprocess.run([str(old), '--archive', str(archive), '--sql', 'SELECT COUNT(*) FROM events'], capture_output=True, text=True)
        assert downgraded.returncode != 0 and 'invalid archive format signature' in downgraded.stderr
        engine.start_bridge(0)
        connection = engine.connect()
        assert connection.call(request)['duplicate']
        assert connection.query('SELECT COUNT(*) FROM events') == [[1001]]
        assert connection.call({'op':'verify'})['verified_bytes'] == 1001*24
        connection.close()
    finally:
        engine.finish()
    result = {'legacy_binary_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
        'binary_sha256':hashlib.sha256(args.binary.resolve().read_bytes()).hexdigest(),
        'legacy_catalog_read':True,'new_catalog_magic':args.new_catalog_magic,
        'older_binary_rejects_new_catalog':True,'downgrade_error':downgraded.stderr.strip(),
        'receipt_preserved_after_reopen':True,'full_scrub_passed':True}
    if args.receipt_binary:
        assert args.new_catalog_magic == 'KSQLCAT4'
        prior = Engine('kestrel', args.work/'receipt-upgrade', 1000, args.receipt_binary.resolve(), {})
        request = {'op':'append','id':'legacy:receipt','data':[[1000,11,1]]}
        try:
            connection = prior.connect()
            original = connection.call(request)
            assert not original['duplicate']
            connection.close()
        finally:
            prior.finish()
        current = Engine('kestrel', args.work/'receipt-upgrade', 0, args.binary.resolve(), {}, existing=True)
        try:
            connection = current.connect()
            replay = connection.call(request)
            assert replay['duplicate'] and replay['generation'] == original['generation']
            assert not connection.call({'op':'append','id':'cat4:receipt','data':[[1001,17,1]]})['duplicate']
            connection.close()
            current.finish()
            archive = args.work/'receipt-upgrade'/'archive'
            rejected = subprocess.run([str(args.receipt_binary.resolve()), str(archive), '0'], capture_output=True, text=True, timeout=10)
            assert rejected.returncode != 0 and 'invalid archive format signature' in rejected.stderr
            current.start_bridge(0)
            connection = current.connect()
            assert connection.call(request)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1002,-500+11+17]]
            assert connection.call({'op':'verify'})['verified_bytes'] == 1002*24
            assert connection.call({'op':'stats'})['catalog_chain_files'] == 2
            connection.close()
        finally:
            current.finish()
        result.update(cat3_catalog_read_and_upgrade=True, cat3_original_receipt_generation_preserved=True,
                      cat3_binary_rejects_cat4=True, cat3_downgrade_error=rejected.stderr.strip(),
                      cat3_binary_sha256=hashlib.sha256(args.receipt_binary.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
