"""Frozen original142 gates per balanced block; exhaustive stall/pooled tail diagnostics."""
import importlib.util,json,math,statistics,sys
from collections import defaultdict
from pathlib import Path
W=Path(__file__).resolve().parent

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def quantile(xs,p):
 xs=sorted(xs);at=(len(xs)-1)*p;lo=math.floor(at);hi=math.ceil(at)
 return xs[lo]+(xs[hi]-xs[lo])*(at-lo)

def gates_for(cases,policy,rounds,inputs):
    checks=[];summaries=[]
    metrics=['ordinary_p50_ms','ordinary_p99_ms','ordinary_max_ms','source_p50_ms','total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','source_p99_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes','current_reachable_bytes','noncheckpoint_p50_ms','noncheckpoint_p99_ms','checkpoint_sum_ms','checkpoint_max_ms']+[p+'_'+q+'_ms' for p in ['anchor31','checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']]
    def add(kind,seed,metric,ratio,limit=None,interval=None):
        passed=math.isfinite(ratio) and (interval[0]<=ratio<=interval[1] if interval else ratio<=limit)
        checks.append({'kind':kind,'seed_receipts':seed,'metric':metric,'paired_ratio':ratio,'limit':limit,'interval':interval,'passed':passed})
    for seed in [0,50000,99000]:
        pairs=[]
        for turn in rounds:
            group={c['spec']['variant']:c for c in cases if c['spec']['round']==turn and c['spec']['seed_receipts']==seed}
            a=group['baseline_a'];b=group['baseline_b'];p=group['hybrid']
            pairs.append({'round':turn,'candidate_a':{k:p[k]/a[k] for k in metrics},'identity_b_a':{k:b[k]/a[k] for k in metrics}})
        ratios={label:{k:statistics.median(p[label][k] for p in pairs) for k in metrics} for label in ['candidate_a','identity_b_a']}
        c=ratios['candidate_a'];lim=policy['checks']
        for metric,limit in lim['publication_and_common_guards'].items():add('guard',seed,metric,c[metric],limit)
        for metric,limit in lim['unchanged_checkpoint_guards'].items():add('guard',seed,metric,c[metric],limit)
        for metric,limit in lim['all_anchor_guards'].items():add('guard',seed,metric,c[metric],limit)
        if seed:
            for metric,limit in lim['large_publication_goals'].items():add('goal',seed,metric,c[metric],limit)
        for metric in lim['identity_metrics']:add('identity',seed,metric,ratios['identity_b_a'][metric],interval=lim['identity_interval'])
        display={label:{k:statistics.median(c[k] for c in cases if c['spec']['seed_receipts']==seed and c['spec']['variant']==label) for k in metrics} for label in ['baseline_a','baseline_b','hybrid']}
        summaries.append({'seed_receipts':seed,'actual_receipts':inputs[seed]['actual_receipts'],'pairs':pairs,'median_paired_ratios':ratios,'median_display_only':display})
    assert len(checks)==policy['expected_check_count']
    assert sum(c['kind']=='goal' for c in checks)==4
    return checks,summaries


def orders():
 from order_plan import plan
 old=importlib.util.spec_from_file_location('frozen079orders',W.parent/'perf-079/order_plan.py')
 module=importlib.util.module_from_spec(old);old.loader.exec_module(module)
 cases=plan();blocks=[]
 for start in [0,6]:
  local=[dict(c,round=c['round']-start) for c in cases if start<=c['round']<start+6]
  blocks.append({'first_round':start,'original079_validator':module.validate(local)})
 save(W/'block-order-balance.json',{'complete':True,'blocks':blocks})
 print('Both independent six-round blocks pass unchanged079 order validation.')

def analyze():
 a=load(W/'model-audit.json');assert a['complete']
 policy=load(W/'policy.json');inputs={i['seed_receipts']:i for i in load(W/'input-provenance.json')['inputs']}
 blocks=[]
 for start in [0,6]:
  cases=[c for c in a['cases'] if start<=c['spec']['round']<start+6]
  checks,summaries=gates_for(cases,policy,range(start,start+6),inputs)
  blocks.append({'first_round':start,'cases':len(cases),'checks':checks,'summaries':summaries,'failed_checks':[c for c in checks if not c['passed']],'all142_passed':all(c['passed'] for c in checks)})
 groups=defaultdict(list);events=[];chronology=[]
 for c in a['cases']:
  x=load(W/'raw'/f"{c['label']}.stdout.json");spec=c['spec'];peaks=[]
  for s in x['samples']:
   path='source' if s['source_interval'] else 'ordinary';ms=s['outer_ms'];groups[(spec['seed_receipts'],spec['variant'],path)].append(ms)
   if ms>100:
    event={'case':c['label'],'spec':spec,'path':path,'sequence':s['sequence'],'ms':ms,'over500ms':ms>500,'stages':s['io']};events.append(event);peaks.append(event)
  for r in x['fresh_recovery']:
   path={30:'anchor31',31:'checkpoint32',62:'checkpoint_delta63',63:'checkpoint64'}[r['after_sequence']];ms=r['recovery_ms'];groups[(spec['seed_receipts'],spec['variant'],path)].append(ms)
   if ms>100:
    event={'case':c['label'],'spec':spec,'path':path,'after_sequence':r['after_sequence'],'repetition':r['repetition'],'ms':ms,'over500ms':ms>500};events.append(event);peaks.append(event)
  chronology.append({'case':c['label'],'spec':spec,'over100ms':len(peaks),'over500ms':sum(e['over500ms'] for e in peaks),'max_publication_ms':max(s['outer_ms'] for s in x['samples']),'max_recovery_ms':max(r['recovery_ms'] for r in x['fresh_recovery'])})
 pooled=[{'seed_receipts':k[0],'variant':k[1],'path':k[2],'count':len(xs),'p50_ms':quantile(xs,.5),'p95_ms':quantile(xs,.95),'p99_ms':quantile(xs,.99),'max_ms':max(xs),'over100ms':sum(x>100 for x in xs),'over500ms':sum(x>500 for x in xs)} for k,xs in sorted(groups.items())]
 r={'complete':True,'full_cohort_all142_passed':a['all_fresh_comparison_checks_passed'],'blocks':blocks,'predeclared_robustness_passed':a['all_fresh_comparison_checks_passed'] and all(b['all142_passed'] for b in blocks),'pooled_quantiles_diagnostic_only':pooled,'all_over100ms_events':events,'over500ms_event_count':sum(e['over500ms'] for e in events),'chronology':chronology,'all_samples_retained':True,'no_engine_promotion':True}
 save(W/'robustness-audit.json',r)
 print(json.dumps({'complete':True,'robustness_passed':r['predeclared_robustness_passed'],'full_failed':len(a['failed_checks']),'block_failed':[len(b['failed_checks']) for b in blocks],'over100ms_events':len(events),'over500ms_events':r['over500ms_event_count']}))

if __name__=='__main__':
 if sys.argv[1:]==['--orders']:orders()
 else:assert not sys.argv[1:];analyze()
