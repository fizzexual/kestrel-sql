from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,itertools,json,random,shutil,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-143';P=R/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not W.exists() and load(R/'work/profile142-storage-cleanup-proof.json')['complete']
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
assert head==load(R/'work/profile142-remote-save-proof.json')['head']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n)==h for n,h in core.items())
src=(P/'src/archive.rs').read_text();start=src.index('        let mut indexes = Vec::new();',src.index('    fn publish('));end=src.index('        let metadata = SegmentMetadata',start)
lifted=src[start:end];legacy=lifted.replace('for column in &columns','for column in columns')+'        indexes\n'
candidate=legacy;mark='            indexes.push(Index {\n';assert candidate.count(mark)==1
candidate=candidate.replace(mark,'            let low = *block_min.iter().min().unwrap();\n            let high = *block_max.iter().max().unwrap();\n'+mark,1)
assert candidate.count('min: *column.iter().min().unwrap(),')==1 and candidate.count('max: *column.iter().max().unwrap(),')==1
candidate=candidate.replace('min: *column.iter().min().unwrap(),','min: low,').replace('max: *column.iter().max().unwrap(),','max: high,')
driver=(P/'experiments/compaction_merge_121/compaction_stage_121.rs').read_text();input_source=driver[driver.index('fn columns('):driver.index('fn main()')]
rng=random.Random(20261011);shapes=['ordered','clustered','interleaved','duplicates','late','extreme'];perms=list(itertools.permutations(['baseline_a','baseline_b','candidate']));cases=[]
for half in range(2):
    orders={n:perms.copy() for n in shapes}
    for n in shapes:rng.shuffle(orders[n])
    for offset in range(6):
        round_number=half*6+offset+1;names=shapes.copy();rng.shuffle(names)
        for name in names:
            for variant in orders[name][offset]:cases.append({'index':len(cases),'round':round_number,'seed':round_number,'name':name,'variant':variant})
assert len(cases)==216
policy={'trial':143,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'supported_core_sha256':core,
 'kind':'Index-only independent diagnostic plus minimal extrema-reuse candidate, no Archive change',
 'hypothesis':'Publication rescans each entire column for global extrema after already computing exact block extrema. Reuse block min/max for globals, preserving every other operation; measure the benefit and legacy stage shares before choosing engine changes. Baseline code is lifted from supported publish (identical131 indexes), with only slice iteration borrow adaptation.',
 'cases':cases,'component_configs':shapes,'rounds':12,'rows':32768,'columns':3,'repetitions':16,'schedule_rng':'Random20261011/all6permutations per shape per half',
 'scopes':['full','first_half','second_half'],'AA_lower':.9,'AA_upper':1.1,'candidate_guard_upper':1.1,'index_goal_upper':.95,
 'diagnostic_checks':{'AA':18,'guards':18,'goals':18},'affinity_mask':256,'cooldown_seconds':120,'cooldown_poll_seconds':10,'cooldown_deadline_seconds':7200,
 'scope_exclusions':'No Archive input reads/CRC, merge/sort, index serde serialization, segment/catalog writes/flush/sync, receipts/ACK, service or competitor qualification. Input generation/stable TS sorting/SHA and one separate instrumented legacy profile are outside primary kernel timer. Profile clocks have overhead; do not infer exclusive actual Archive costs.',
 'timer':'16 complete index builds, including all prefix sums/block+global extrema/monotonicity/output payload CRC-byte generation+CRC and all allocations/drop of prior output; black_box inputs/function/result best-effort prevents elimination. Final validation/JSON outside timer.',
 'correctness':'Three fresh example-only tests normal debug/release, including exact wide-i128 typed JSON output, strict example lint; every timed output independently recomputed from declared input/seed, complete input SHA/index fields/i128 prefixes/CRC. All library src/tests/dependencies byte-exact; existing016/131 correctness reused, no engine build/tests repeated.',
 'legacy_index_body_sha256':hashlib.sha256(lifted.encode()).hexdigest(),'research':['https://doc.rust-lang.org/std/hint/fn.black_box.html','https://docs.rs/serde_json/latest/serde_json/value/struct.Serializer.html','https://docs.rs/serde_json/latest/src/serde_json/ser.rs.html'],
 'source_merging_120_not_adopted':True,'prior142_output_failure_preserved':True,'only_output_serializer_changed_vs142_outside_timer':True,'all_original_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'release017_qualified':False,'durable_speed_claim':False,'resource_bound_bytes':1800000000,'timeout_seconds':90,
 'storage':'SHORT private diagnostic/failed checks/useful source, fresh exact remote bytes then native scoped completed cleanup; no raw multiGB bundle',
 'new_protocol':'Strict reset/task/supervisor/global guards before/after all cases;120continuous observed quiet afterprep/freeze; metadata worker idle onstdin duringnative; outside-lifetime waits only if births prove safe; no selected retiming/outlier discard/metric selection.'}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'policy_sha256':sha(W/'policy.json'),'before_implementation_or_timing':True,'diagnostic_only':True},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
template=(R/'work/index_profile_143.template.rs').read_text()
template=template.replace('// MARK_LEGACY',legacy).replace('// MARK_REUSE',candidate).replace('// MARK_INPUT',input_source)
(C/'examples/index_profile_143.rs').write_text(template,encoding='utf-8',newline='\n')
assert all(sha(C/n)==h for n,h in core.items())
for n in ['logs','tmp','binary']:(W/n).mkdir()
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'library_core_byte_exact':True,'kernel_source_sha256':sha(C/'examples/index_profile_143.rs'),'before_timing':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('143 declared216-case index-only diagnostic; actual kernel candidate implemented; supported engine unchanged')
