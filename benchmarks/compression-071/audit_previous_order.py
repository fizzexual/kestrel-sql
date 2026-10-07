"""Additive historical correction; old policies, raw metrics and reports stay intact."""
from collections import Counter
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=[]
for trial in [69,70]:
    old=W.parent/f'perf-{trial:03}';cohort=load(old/'cohort-policy.json');results=load(old/'model-results.json')
    assert cohort['harness_sha256']==sha(old/'run_model.py') and cohort['policy_sha256']==sha(old/'policy.json')
    assert results['cohort_policy_sha256']==sha(old/'cohort-policy.json') and [c['spec'] for c in results['cases']]==cohort['cases']
    assert sha(ROOT/f'benchmarks/compression-{trial:03}/cohort-policy.json')==sha(old/'cohort-policy.json')
    seeds=[]
    for seed in [0,50000,99000]:
        orders=[tuple(c['variant'] for c in cohort['cases'] if c['round']==turn and c['seed_receipts']==seed) for turn in range(4)]
        assert len(set(orders))==1 and all(len(x)==3 for x in orders)
        slots={v:{str(slot):sum(order[slot]==v for order in orders) for slot in range(3)} for v in ['baseline_a','baseline_b','compressed']}
        seeds.append({'seed_receipts':seed,'actual_orders_each_round':orders,'unique_orders':len(set(orders)),'variant_slot_counts':slots})
    out.append({'trial':trial,'cohort_sha256':sha(old/'cohort-policy.json'),'policy_sha256':sha(old/'policy.json'),
        'harness_sha256':sha(old/'run_model.py'),'actual_cases_match_frozen_plan':True,'size_rotation_cancelled_variant_rotation':True,'seeds':seeds})
result={'audited_utc':datetime.now(timezone.utc).isoformat(),'historical_trials':out,
    'prior_raw_values_hashes_and_policies_unchanged':True,'prior_claim_of_variant_rotation_corrected':True,
    'old_rejected_models_not_promoted':True,'scope':'069 and070 ordering only; no inference about other cohorts or SQL engines'}
(W/'previous-order-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
text='''# Correction: checkpoint-model ordering in 069 and 070

An independent review during trial 071 found a scheduling flaw in the two earlier checkpoint compression models. The rotation of size order and the `(round + size_index) % 3` variant rotation cancelled each other. At each fixed size, **all four rounds used the same variant order**:

| Starting receipt history | Actual order in every round |
|---:|---|
| 0 | raw A, raw B, compressed C |
| 50,000 | raw B, compressed C, raw A |
| 99,000 | compressed C, raw A, raw B |

The size order did rotate, but the claim that variant order rotated per size was incorrect. I introduced this flaw and the earlier audit checked actual cases against the frozen plan without independently checking position balance. Repeated order can confound serial comparisons with position, cache and changing host/storage conditions. The reported matched ratios remain the original descriptive calculations; they are not newly qualified causal codec speedups or slowdowns. Both models remain rejected, with no engine integration or supported promotion. Exact byte/CRC/decoder tests, original input hashes, all raw timings and all failed gates remain preserved.

Read this correction alongside [zlib model 069](COMPRESSION_069.md) and [Zstandard level-1 model 070](COMPRESSION_070.md). Neither report, original policy, frozen harness, raw result nor private ZIP was rewritten. The correction applies to those two model cohorts; it does not establish an ordering defect in other benchmarks. No new DuckDB/PostgreSQL claim follows.

The next independent model uses six complete permutations. For every fixed size, each variant appears in every position twice, all six variant orders appear once, and both A-before-B and B-before-A occur three times. Each size appears in each size position twice. The planner and auditor verify those counts independently of elapsed times before any case starts and after completion. Regression tests reject the old cancelling rotation as well as duplicated variants and malformed size groups.

[Historical frozen-plan audit](benchmarks/compression-071/previous-order-audit.json), [auditor source](benchmarks/compression-071/audit_previous_order.py), [new planner and regression tests](benchmarks/compression-071/order_plan.py), [pre-timing balance proof](benchmarks/compression-071/order-balance-pre-timing.json) and [new model report](COMPRESSION_071.md). Prior raw and release evidence remains linked from the original reports. English only; supported KestrelSQL 0.3.16 and the frozen morning report remain unchanged.
'''
target=ROOT/'MODEL_ORDER_AUDIT_071.md';assert not target.exists();target.write_text(text,encoding='utf-8')
print(json.dumps({'historical_order_defect_confirmed':True,'trials':[69,70],'all_original_evidence_unchanged':True}))
