"""Independent complete payload/CRC/receipt and full/half timing audit."""
from pathlib import Path
import hashlib,itertools,json,math,statistics,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as independent
R=Path('D:/Codex/Kestrel');W=R/'work/perf-141'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rows(name,run,seed):
    part=(run*13+seed*7)%32
    out=[]
    for row in range(1024):
        if name=='ordered':key=run*1024+row
        elif name in ['clustered','extreme']:key=(row//64)*2048+part*64+row%64
        elif name=='interleaved':key=row*32+part
        elif name=='duplicates':key=(row//64)*64+row%8
        elif name=='late':key=part%8*512+row-(part//8)*8192
        else:raise AssertionError(name)
        value=[-2**63,-7,0,11,2**63-1][row%5] if name=='extreme' else (run*1024+row)*37%1000-500
        out.append([key,value,run-16])
    return out
def nearest(values,q):return sorted(values)[max(0,math.ceil(len(values)*q)-1)]
assert load(W/'cohort-completion.json')['complete']
policy=load(W/'policy.json');freeze=load(W/'freeze.json');assert all(sha(W/n)==v for n,v in freeze['files'].items())
activity=[json.loads(line) for line in (W/'activity-checks.jsonl').read_text(encoding='utf-8').splitlines()]
case_probes=[row for row in activity if row['place'] in ['before_case','before_case_retry','after_case']]
pauses=[json.loads(line) for line in (W/'between-case-pauses.jsonl').read_text().splitlines()] if (W/'between-case-pauses.jsonl').exists() else []
assert all(row['continuous_quiet_seconds']>=120 and row['no_native_case_repeated'] and row['no_metric_based_selection'] for row in pauses)
assert sum(row['place']=='after_case' for row in case_probes)==216
assert {row['index'] for row in case_probes}==set(range(216))
for probe in case_probes:
    assert probe['exit'] in [0,3]
    if probe['exit']==3:
        mode='after' if probe['place']=='after_case' else 'before'
        assert any(p['mode']==mode and p['index']==probe['index'] and p['initial_probe']==probe for p in pauses)

assert load(W/'cooldown-proof.json')['continuous_quiet_seconds']>=120
assert load(W/'cohort-completion.json')['metadata_worker_actual_exit']==0
worker_exits=[json.loads(line) for line in (W/'worker-exits.jsonl').read_text().splitlines()]
assert all(row['actual_exit']==0 and row['actual_wait_completed'] and not row['forced_owned_worker_kill'] for row in worker_exits)
assert load(W/'protocol-proof.json')['dummy_detected_busy_then_clear']
assert all(row['exit']==0 for row in activity if row['place'].startswith('preflight_'))


cases=[json.loads(line) for line in (W/'component-cases.jsonl').read_text().splitlines()]
assert len(cases)==len(policy['cases'])==216
metrics={};crc=0;case_checks=[]
for case,spec in zip(cases,policy['cases']):
    assert all(case[k]==v for k,v in spec.items()) and case['actual_exit']==0 and case['actual_wait_completed'] and not case.get('timeout')
    before_probe=[p for p in case_probes if p['place'] in ['before_case','before_case_retry'] and p['index']==spec['index']][-1]
    assert before_probe['exit']==0
    after_probe=next(p for p in case_probes if p['place']=='after_case' and p['index']==spec['index'])
    assert before_probe['utc']<=case['started_utc']<=case['completed_utc']<=after_probe['started_utc']<=after_probe['utc']
    assert before_probe['worker_identity']==after_probe['worker_identity'] and before_probe['worker_identity']['affinity_mask']==256
    if after_probe['exit']==3:
        from datetime import datetime,timedelta
        messages=[json.loads(line) for line in after_probe['stdout'].splitlines()]
        assert not messages[0]['reset_jobs']
        jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs'])
        cutoff=max(datetime.fromisoformat(case['completed_utc'])+timedelta(seconds=.1),datetime.fromisoformat(after_probe['started_utc']))
        assert jobs and all(datetime.fromisoformat(job['creation_utc'])>=cutoff for job in jobs)
    for pause in (p for p in pauses if p['index']==spec['index']):
        if pause['mode']=='before':assert pause['completed_utc']<=case['started_utc']
        else:assert case['completed_utc']<=pause['started_utc']<=pause['completed_utc']
        if pause['mode']=='after' and spec['index']<215:assert pause['completed_utc']<=cases[spec['index']+1]['started_utc']

    result=load(W/case['stdout']);assert result['component_only'] and result['all_checks_passed']
    assert result['workload']==spec['name'] and result['seed']==spec['seed'] and case['identity']['affinity_mask']==256
    expected=[item for run in range(32) for item in rows(spec['name'],run,spec['round'])]
    declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if spec['name'] in ['clustered','late'] else []
    assert result['receipts']==declared_receipts,(spec['index'],'original receipt generation')
    receipt_data={id:(rows(spec['name'],run,spec['round']),run+1) for id,run,generation in declared_receipts}
    assert set(receipt_data)==({f'merge121:{run}' for run in range(32)} if spec['name'] in ['clustered','late'] else set())
    checked=independent.check(W/case['fixture'],expected,receipt_data)
    assert checked['rows']==32768 and checked['head']==33 and len(checked['segments'])==1 and checked['full_block_crc_bytes']==result['full_crc_bytes']
    assert result['before']['generation']==32 and result['after']['generation']==33 and result['reduced']==31
    before=result['before']['publication_profile'];after=result['after']['publication_profile']
    stages={key:after[key]['total_ms']-before[key]['total_ms'] for key in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']}
    assert all(value>=0 for value in stages.values())
    assert after['completed']-before['completed']==1 and after['attempts']-before['attempts']==1
    assert result['compaction_ns']>0 and sum(stages.values())<=result['compaction_ns']/1e6+0.001
    values={'wall_ms':result['compaction_ns']/1e6,'setup_ms':result['setup_ns']/1e6,**{key+'_ms':value for key,value in stages.items()}}
    values['write_sync_ms']=stages['segment_write']+stages['segment_sync']
    metrics[(spec['name'],spec['variant'],spec['round'])]=values
    crc+=checked['full_block_crc_bytes'];case_checks.append({'index':spec['index'],'rows':checked['rows'],'CRC_bytes':checked['full_block_crc_bytes'],'generation':checked['head'],'segments':len(checked['segments']),'receipt_ids':len(receipt_data)})
    if len(case_checks)%36==0:print(json.dumps({'independently_checked_cases':len(case_checks),'total':216}),flush=True)
summaries=[]
for name in policy['component_configs']:
    for scope,rounds in [('full',range(1,13)),('first_half',range(1,7)),('second_half',range(7,13))]:
        order=[tuple(case['variant'] for case in cases if case['name']==name and case['round']==r) for r in rounds]
        assert sorted(order)==sorted(list(itertools.permutations(['baseline_a','baseline_b','candidate']))*(len(rounds)//6))
        for metric in policy['metrics']:
            source_metric=metric.replace('_p95_ms','_ms')
            values={v:[metrics[(name,v,r)][source_metric] for r in rounds] for v in ['baseline_a','baseline_b','candidate']}
            a=values['baseline_a'];b=values['baseline_b'];c=values['candidate']
            assert all(x>0 for x in a+b+c)
            if metric.endswith('_p95_ms'):
                aa=nearest(b,.95)/nearest(a,.95);ca=nearest(c,.95)/nearest(a,.95)
            else:aa=statistics.median(y/x for x,y in zip(a,b));ca=statistics.median(y/x for x,y in zip(a,c))
            row={'workload':name,'scope':scope,'metric':metric,'samples_each':len(rounds),'AA_paired':aa,'CA_paired':ca,'AA_pass':.90<=aa<=1.10,'candidate_guard_pass':ca<=1.10,
                 'variants':{v:{'p50':statistics.median(x),'p95':nearest(x,.95),'p99':nearest(x,.99),'max':max(x),'all_samples':x} for v,x in values.items()}}
            if name=='clustered' and metric in ['wall_ms','prepare_ms']:row['goal_pass']=ca<=(.95 if metric=='wall_ms' else .90)
            row['ratio_method']='nearest-rank p95 C/A and B/A' if metric.endswith('_p95_ms') else 'median within-round ratios'
            summaries.append(row)
audit={'complete':True,'component_only':True,'correctness_passed':True,'fresh_cases':216,'full_payload_rows':216*32768,'fully_checked_crc_bytes':crc,'case_checks':case_checks,'summaries':summaries,
       'identity_failed':[s for s in summaries if not s['AA_pass']],'guards_failed':[s for s in summaries if not s['candidate_guard_pass']],
       'clustered_goals_qualified':all(s['goal_pass'] and s['AA_pass'] and s['candidate_guard_pass'] for s in summaries if 'goal_pass' in s),'release017_qualified':False,
       'raw_controller_SHA256':sha(W/'component-cases.jsonl'),'all_original_release_gates_unchanged':True,'between_case_pauses':len(pauses),'all_cases_kept_once_without_metric_selection':True}
assert len(summaries)==144 and sum('goal_pass' in s for s in summaries)==6
assert not (W/'audit.json').exists();(W/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ['summaries','case_checks','identity_failed','guards_failed']}))
print(json.dumps({'identity_failed':len(audit['identity_failed']),'guards_failed':len(audit['guards_failed'])}))
