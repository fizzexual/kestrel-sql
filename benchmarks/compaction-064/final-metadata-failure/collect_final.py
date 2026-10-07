"""Post-timing metadata and labelled diagnostics, with raw metadata untouched."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,platform,sqlite3,sys,statistics
import duckdb,numpy
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
a=load(W/'native-audit.json');assert a['complete']
assert not load(W/'post-qualification-process-check.json')['active_processes']
snapshots={}
for name in ['native-process-preflight.json','native-process-postflight.json']:
    p=W/name;assert p.stat().st_size==0
    # No pipeline object was emitted when no process matched; preserve that raw fact.
    snapshots[name]={'bytes':0,'sha256':sha(p),'file_modified_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),'meaning':'Raw empty PowerShell pipeline: zero matching processes; not a JSON document'}
save(W/'process-snapshot-note.json',{'after_timing_note':True,'raw_snapshots_unchanged':snapshots})
q=load(W/'qualification.json');assert q['trial']==61 and q['version']=='0.3.17-dev.64'
save(W/'qualification-metadata-note.json',{'raw_qualification_sha256':sha(W/'qualification.json'),'inherited_numeric_trial_label':61,'actual_trial':64,
    'raw_record_unchanged':True,'version_all_harness_names_sources_and_commands_identify_064':True,'no_suite_rerun':True})
save(W/'runtime-provenance.json',{'collected_utc':datetime.now(timezone.utc).isoformat(),'after_all_timed_workloads':True,
    'python':sys.version,'platform':platform.platform(),'duckdb':duckdb.__version__,'sqlite':sqlite3.sqlite_version,'numpy':numpy.__version__,
    'fresh_competitor_performance_run':False,'oracle_packages_only_no_dependency_change_during_workloads':True})
diagnostics=[]
for size in [0,50000,99000]:
    for variant in ['baseline_a','baseline_b','candidate']:
        cases=[c for c in a['cases'] if c['spec']['seed_receipts']==size and c['spec']['variant']==variant]
        sync=[];encode=[]
        for c in cases:
            stages=c['stage_deltas_including_maintenance'];total=sum(v['total_ms'] for v in stages.values())
            sync.append(sum(v['total_ms'] for k,v in stages.items() if k.endswith('_sync'))/total)
            encode.append(stages['catalog_encode']['total_ms']/total)
        diagnostics.append({'size':size,'variant':variant,'median_sync_fraction_of_summed_stages':statistics.median(sync),
            'median_catalog_encode_fraction_of_summed_stages':statistics.median(encode),'slow_over_500ms':sum(c['slow_over_500ms'] for c in cases)})
save(W/'posthoc-stage-diagnostics.json',{'posthoc':True,'changes_no_policy':True,'stage_totals_include_compaction_exclude_queueing_setup_and_other_work':True,
    'not_a_causal_decomposition_of_p99':True,'rows':diagnostics})
print(json.dumps({'metadata_collected':True,'all_timed_processes_stopped':True,'diagnostics':diagnostics}))
