"""Executed data-engineering demo: Parquet microbatches, safe retries and late data.
This uses the prototype loopback adapter; it is not a production SQL endpoint.
"""
import argparse
import concurrent.futures
import hashlib
import json
import random
import time
from pathlib import Path

import duckdb
from stress_compare import Engine

ROOT=Path(__file__).resolve().parents[1]


def import_file(engine,source):
    with source.open('rb') as file:
        source_hash=hashlib.file_digest(file,'sha256').hexdigest()
    db=duckdb.connect()
    db.execute('SELECT ts,value,device FROM read_parquet(?)',[str(source)])
    batches=[]
    number=0
    while data:=db.fetchmany(100):
        batches.append((f'{source_hash}:{number}',[list(row) for row in data]))
        number+=1
    db.close()
    def ingest(item):
        identifier,data=item
        connection=engine.connect()
        try: return connection.call({'op':'append','id':identifier,'data':data})
        finally: connection.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        receipts=list(pool.map(ingest,batches))
    return {'source_sha256':source_hash,'batches':len(receipts),'rows':sum(r['affected'] for r in receipts),
        'duplicate_batches':sum(r['duplicate'] for r in receipts)},batches


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--binary',type=Path,default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--work',type=Path,default=ROOT.parent.parent/'work'/f'live-pipeline-{time.time_ns()}')
    args=parser.parse_args()
    args.work.mkdir(parents=True)
    base,late=args.work/'base.parquet',args.work/'late-backfill.parquet'
    db=duckdb.connect()
    db.execute('SET threads=1')
    db.execute('CREATE TABLE base AS SELECT i::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS "value", ((i*17)%97)::BIGINT AS device FROM range(25000) t(i)')
    db.execute('CREATE TABLE late AS SELECT ((i*13)%5000)::BIGINT AS ts, ((i*11)%1000-500)::BIGINT AS "value", ((i*7)%97)::BIGINT AS device FROM range(5000) t(i)')
    db.execute('COPY base TO ? (FORMAT PARQUET)',[str(base)])
    db.execute('COPY late TO ? (FORMAT PARQUET)',[str(late)])
    engine=Engine('kestrel',args.work/'store',0,args.binary.resolve(),{})
    report={'engine_version':engine.version,'workflow':'two Parquet sources, durable source-hash/chunk IDs, each source replayed',
        'initial_rows':25000,'late_backfill_rows':5000,'imports':[]}
    try:
        first,batches=import_file(engine,base)
        replay,_=import_file(engine,base)
        assert first['duplicate_batches']==0 and replay['duplicate_batches']==replay['batches']
        connection=engine.connect()
        before=connection.query('SELECT COUNT(*), SUM(value) FROM events WHERE ts >= 1000 AND ts < 3000')
        connection.close()
        backfill,_=import_file(engine,late)
        replay_late,_=import_file(engine,late)
        assert backfill['duplicate_batches']==0 and replay_late['duplicate_batches']==replay_late['batches']
        report['imports']=[first,replay,backfill,replay_late]
        engine.reopen()
        connection=engine.connect()
        assert connection.query('SELECT COUNT(*) FROM events')==[[30000]]
        db.execute('CREATE VIEW expected AS SELECT * FROM base UNION ALL SELECT * FROM late')
        rng=random.Random(20261006)
        queries=['SELECT COUNT(*), SUM(value) FROM events',
            'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device']
        for _ in range(40):
            lo=rng.randrange(25000); hi=lo+rng.randrange(1,10000)
            queries.append(f'SELECT COUNT(*), SUM(value), MIN(value), MAX(value) FROM events WHERE ts >= {lo} AND ts < {hi}')
        for sql in queries:
            actual=connection.query(sql)
            expected=[list(row) for row in db.execute(sql.replace('FROM events','FROM expected')).fetchall()]
            assert actual==expected,(sql,actual,expected)
        after=connection.query('SELECT COUNT(*), SUM(value) FROM events WHERE ts >= 1000 AND ts < 3000')
        identifier,data=batches[0]
        changed=[row[:] for row in data]; changed[0][1]+=1
        try:
            connection.call({'op':'append','id':identifier,'data':changed})
            raise AssertionError('changed content accepted under committed batch ID')
        except RuntimeError as error:
            assert 'different content' in str(error)
        assert connection.query('SELECT COUNT(*) FROM events')==[[30000]]
        scrub=connection.call({'op':'verify'})
        report.update({'exact_sql_cases_against_duckdb':len(queries),'replayed_sources_not_duplicated':True,
            'changed_content_rejected':True,'window_before_backfill':before,'window_after_backfill':after,
            'late_data_correctly_changes_prior_metrics':before!=after,'full_scrub':scrub,
            'final_stats':connection.call({'op':'stats'}),'limits':'batch idempotency for this archive, not end-to-end exactly-once delivery; BIGINT metrics only'})
        assert before!=after and scrub['verified_bytes']==30000*24
        connection.close()
    finally:
        engine.finish(); db.close()
    output=ROOT/'portfolio'/'live-pipeline-results.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
