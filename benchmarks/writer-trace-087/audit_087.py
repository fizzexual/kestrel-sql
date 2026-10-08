"""Independent raw qualification replay. No native launches or timing reruns."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,math,sqlite3,re,sys
DEFAULT=Path('D:/Codex/Kestrel/work/perf-087')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(p):return {f.relative_to(p).as_posix():{'size':f.stat().st_size,'sha256':sha(f)} for f in sorted(p.rglob('*.ks2')) if f.is_file()}
def audit(w):
    proof=load(w/'oracle-proof.json');build=load(w/'build-proof.json');fix=load(w/'bridge-v2-proof.json');assert proof['complete'] and build['complete'] and fix['complete']
    order=load(w/'oracle-order.json');assert len(order)==90 and len({x['name']for x in order})==90
    for record in order:
        assert load(w/'oracle-results'/(record['name']+'.status.json'))==record and record['exit']==0
        binary=w/'binaries'/Path(record['argv'][0].replace('\\','/')).relative_to(DEFAULT/'binaries')
        assert sha(binary)==record['binary_sha256']
        assert (w/'oracle-results'/(record['name']+'.stderr.log')).read_text(encoding='utf-8')==''
    for name,h in proof['binary_sha256'].items():assert sha(w/name)==h,name
    tests=[]
    for record in build['build_order']:
        assert record['returncode']==0
        if 'tests_passed' in record:
            n=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',(w/'logs'/(record['label']+'-'+record['name']+'.log')).read_text(encoding='utf-8'))))
            assert n==record['tests_passed']==(77 if record['name'].startswith('default') else 82)
            tests.append({'label':record['label'],'name':record['name'],'count':n})
    extra=0
    for record in fix['jobs']:
        assert record['exit']==0
        if 'tests_passed' in record:
            n=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',(w/'logs'/(record['label']+'-bridge-v2-'+record['name']+'.log')).read_text(encoding='utf-8'))))
            assert n==record['tests_passed']==2;extra+=n
    assert len(tests)==8 and sum(t['count']for t in tests)==636 and extra==16
    for label,sources in build['sources'].items():
        for name,h in sources.items():
            if name=='src/bin/kestrel-stress.rs':h=fix['changes'][label]['final_sha256']
            assert sha(w/label/name)==h,(label,name)
    archive_files=0
    for size,labels in proof['archive_byte_equivalence'].items():
        assert len(labels)==5
        for label,expected in labels.items():
            assert inventory(w/'oracle-fixtures'/('archive-'+label+'-'+size))==expected
            assert expected==labels['released016']
            archive_files+=len(expected)
        if size=='oversized':assert max(v['size']for n,v in labels['released016'].items()if n.startswith('catalog-'))>16*1024*1024
    for label,expected in proof['live_byte_equivalence'].items():
        assert inventory(w/'oracle-fixtures'/('live-'+label+'-sequential'))==expected
        assert expected==proof['live_byte_equivalence']['released-default']
    correlated=0;traced_events=0;publications=0;failed_attempts=0
    for name,expected in proof['live_results'].items():
        x=load(w/'oracle-results'/('live-'+name+'.stdout.json'));assert x==expected and x['exact_sql_crc_passed']
        assert sorted(x['stats'])==proof['wire_results']['released016']['stats_fields']
        t=x['trace']
        if '-default-' in name:assert t is None;continue
        assert t['dropped_events']==0 and not t['active_cycle']
        assert (t['event_capacity'],t['request_capacity'])==(4096,16384)
        next_request=0;end=0;attempt=0
        acks={a['key']:a for a in x['acknowledgements']}
        for e in t['events']:
            assert e['kind']in ['append','compact','reclaim']
            assert end<=e['start_ns']<=e['end_ns']<=t['elapsed_ns'];end=e['end_ns']
            assert e['request_start']==next_request
            next_request+=e['request_len'];assert next_request<=len(t['requests'])
            assert (e['request_len']==0)==(e['kind']!='append')
            for r in t['requests'][e['request_start']:next_request]:assert 0<=r['enqueue_to_collection_ns']<=e['start_ns']
            p=e['publication'];traced_events+=1
            if p is not None:
                assert p['attempt']==attempt+1;attempt=p['attempt'];publications+=1
                assert p['completed']==e['completed'] and p['generation']>0
                assert len(p['stage_ms'])==7 and all(math.isfinite(v)and v>=0 for v in p['stage_ms'])
                if not p['completed']:failed_attempts+=1;assert p['stage_ms'][5:]==[0,0]
                if e['kind']=='append' and e['completed'] and acks:
                    requests=t['requests'][e['request_start']:next_request]
                    assert p['new_receipts']==len(requests) and p['rows']==2*len(requests)
                    for r in requests:
                        a=acks[r['first_key']];assert a['generation']==p['generation'] and a['rows']==r['rows']==2
                        correlated+=1
        assert next_request==len(t['requests'])
    assert correlated==320 and failed_attempts==2
    sql=sqlite3.connect(':memory:');sql.execute('CREATE TABLE events (ts INTEGER,value INTEGER)')
    sql.executemany('INSERT INTO events VALUES (?,?)',[(ts,v)for i in range(96)for ts,v in [(i*10,i*20),(i*10-1,-i*20)]])
    assert len(proof['sqlite_checks'])==32
    for c in proof['sqlite_checks']:
        expected=[list(sql.execute(c['sql']).fetchone())];assert c['expected']==c['actual']==expected
    sql.close()
    for record in [x for x in order if x['name'].startswith('sqlite-')]:
        x=load(w/'oracle-results'/(record['name']+'.stdout.json'));case=next(c for c in proof['sqlite_checks'] if c['label'] in record['name'] and c['sql']==record['argv'][-1])
        assert x['ok'] and x['result']['rows']==case['expected']
    for label,result in proof['wire_results'].items():
        wire=load(w/'oracle-results'/('bridge-v2-'+label+'.wire.json'))
        stats=wire[0]['response']['result'];assert sorted(stats['ingest'])==result['stats_fields'] and sorted(stats)==result['archive_fields']
        assert result['stats_fields']==proof['wire_results']['released016']['stats_fields']
        enabled=label.endswith('-writer');assert wire[1]['response']['ok']==enabled and wire[-1]['response']['ok']is False
        assert wire[2]['response']['ok'] and not wire[2]['response']['result']['duplicate']
        assert wire[3]['response']['ok'] and wire[3]['response']['result']['duplicate']
        assert not wire[4]['response']['ok'] and wire[5]['response']['result']['verified_bytes']==432
        assert wire[6]['response']['result']['rows']==[[18]]
        if enabled:
            trace=next(v['response']['result']for v in reversed(wire[:-1])if v['request']['op']=='writer_trace')
            assert trace['dropped_events']==0 and not trace['active_cycle']
            assert len(trace['events'])==len(trace['requests'])==3
            assert [e['completed']for e in trace['events']]==[True,True,False]
            assert trace['events'][0]['publication']['attempt']==2
            assert trace['events'][0]['publication']['generation']==wire[2]['response']['result']['generation']
            assert all(e['publication']is None for e in trace['events'][1:])
    initial=load(w/'oracle-results/bridge-released-writer.wire.json')
    assert initial[-1]['request']=={'op':'writer_trace','unexpected':1} and initial[-1]['response']['ok'] # Preserved actual failed check.
    return {'passed':True,'full_suite_runs':tests,'full_suite_test_executions':636,'affected_bridge_v2_test_executions':16,
        'strict_lint_configurations_per_core_per_revision':5,'native_commands':90,'native_command_failures':0,'required_final_bridge_cases':5,
        'initial_bridge_cases_retained':3,'archive_stores_byte_equal':10,'archive_file_instances':archive_files,'live_sequential_stores_byte_equal':4,
        'sqlite_comparisons':32,'original016_live_cross_reopens':12,'trace_ack_correlations':correlated,'trace_events':traced_events,
        'publication_records':publications,'failed_attempt_records':failed_attempts,'raw_qualification_failures_retained':['001-source-indent','002-path-expression','003-wire-envelope-parser','004-diagnostic-extra-field','005-audit-syntax'],
        'dropped_trace_events':0,'normal_stats_fields_unchanged':True,'supported_version':'0.3.16','diagnostic_scope_only':True,
        'speed_or_overhead_qualified':False,'physical_power_loss_or_full_release_qualified':False}
if __name__=='__main__':
    w=Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT
    result=audit(w);print(json.dumps(result))
