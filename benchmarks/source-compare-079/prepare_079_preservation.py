"""Derive bounded full-evidence preservation tools, after native timing has ended."""
from pathlib import Path
import ast
BASE=Path(__file__).resolve().parent;W=BASE/'perf-079'
s=(BASE/'perf-078/maintain_evidence.py').read_text(encoding='utf-8')
s=s.replace('source-state-078','source-compare-079').replace('SOURCE_STATE_078','SOURCE_COMPARE_079').replace('source_state_078','source_compare_079').replace('development-078-source-state','development-079-source-compare').replace('DEVELOPMENT_078','DEVELOPMENT_079')
s=s.replace('no_timed_cohort','fresh_timed_comparison')
def block(name,new):
    global s
    start=s.index('def '+name+'(');end=s.find('\ndef ',start+1)
    assert end!=-1
    s=s[:start]+new.rstrip()+'\n'+s[end:]
block('fixture', '''def fixture(rel):
    return rel.parts[0] in ['fixtures','inputs'] or (rel.parts[0]=='pre-cohort-smoke' and rel.suffix in ['.model','.ks2'])
''')
block('excluded', '''def excluded(rel):return '__pycache__' in rel.parts or rel.parts[0].startswith('audit-restored-')
''')
block('unchanged', '''def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-timing-process-check.json')['active_processes']
    cohort=load(W/'cohort-policy.json');result=load(W/'model-results.json');audit=load(W/'model-audit.json')
    for n,d in cohort['frozen_file_sha256'].items():assert sha(W/n)==d,n
    for n,d in cohort['binary_sha256'].items():assert sha(W/n)==d,n
    assert result['complete'] and not result['failures'] and len(result['cases'])==54 and audit['complete']
    assert not audit['large_source_publication_goals_calibrated_and_passed'] and not audit['all_fresh_comparison_checks_passed'] and not audit['advance_to_engine_design']
    assert len(audit['checks'])==142 and len(audit['failed_checks'])==27
    assert sum(c['kind']=='guard' for c in audit['failed_checks'])==8 and sum(c['kind']=='identity' for c in audit['failed_checks'])==19
    assert audit['file_instances']==3618 and audit['independent_full_decoded_canonical_files']==201
    assert load(W/'goal-calibration.json')['goals_with_matching_control_passed']==3
    for c in result['cases']:
        for suffix,key in [('stdout.json','stdout_sha256'),('status.json','status_sha256'),('stderr.txt','stderr_sha256')]:assert sha(W/'raw'/f"{c['label']}.{suffix}")==c[key]
    old=load(W/'prerequisites/078-qualification-results.json');assert old['complete'] and old['controlled_kills']==15 and old['injected_errors']==15 and old['independent_corruption_cases_rejected']==30
    assert load(W/'prerequisites/078-build-proof.json')['counts']=={'debug':57,'release':57}
    provenance=load(W/'binary-provenance.json')
    for b in provenance['builds'].values():
        assert sha(W/b['binary'])==b['binary_sha256']
        for n,d in b['source_sha256'].items():assert sha(W/b['source_directory']/n)==d,n
    for line in (W/'repository-manifest-pre-079.sha256').read_text(encoding='utf-8').splitlines():
        d,n=line.split('  ',1)
        if n not in UPDATED:assert sha(ROOT/n)==d,('historical payload changed',n)
''')
block('preserve', '''def preserve():
    unchanged();assert not DEST.exists()
    for n,d in load(W/'baseline.json')['core_source_sha256'].items():
        p=W/'released-core-source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p);assert sha(p)==d
    for name in ['prepare_079.py','prepare_079_preservation.py']:shutil.copy2(W.parent/name,W/name)
    inventory={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(W.rglob('*')) if p.is_file() and fixture(p.relative_to(W))}
    assert len(inventory)==4026
    assert len([n for n in inventory if n.startswith('fixtures/')])==3618
    assert len([n for n in inventory if n.startswith('pre-cohort-smoke/') and n.endswith('.model')])==402
    save(W/'bundle-fixture-inventory.json',inventory)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture(rel) and not excluded(rel):
            q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(q)==sha(p);payload[rel.as_posix()]=sha(q)
    result={'preserved_utc':now(),'payload_sha256':payload,'full_fixture_files':len(inventory),'full_fixture_bytes':sum(v['bytes'] for v in inventory.values()),'all_timed_smoke_and_original_input_fixtures_retained':True,'fresh_timed_comparison':True,'default_engine_changed':False,'new_engine_release':False}
    save(ROOT/'benchmarks/source-compare-079-preservation.json',result)
    intro='**Latest measured source-state comparison:** [079 publication gains and failed guards](SOURCE_COMPARE_079.md) measures37.7%/56.6% lower large-history publication totals with stable controls. Only3/4 goals are calibrated;8 guards and19 A/A checks fail. Full qualification fails; supported0.3.16 stays unchanged. All prior reports and failures remain accessible.\\n\\n'
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\\n\\n',1);p.write_text(first+'\\n\\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Fresh source-state benchmark079](SOURCE_COMPARE_079.md) shows calibrated37.7%/56.6% lower50K/99K publication totals and a calibrated99K source-p99 gain.50K source-p99 calibration fails;8 candidate guards and19 A/A checks fail.50K ordinary p50/max and small checkpoint64 tail are calibrated regressions. No adoption, real-engine integration or competitor result;075/077 failures and supported0.3.16 remain unchanged.\\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='payload_sha256'}),flush=True)
''')
s=s.replace("z.writestr('kestrel-sql/SOURCE_COMPARE_079_MANIFEST.sha256'", "z.writestr(f'kestrel-sql/SOURCE_COMPARE_079_PART_{i}_MANIFEST.sha256'")
s=s.replace("z.writestr('kestrel-sql/DEVELOPMENT_079.md',f'Untimed source-state qualification part {i}/{len(groups)}. No speed claim or new engine release.","z.writestr(f'kestrel-sql/DEVELOPMENT_079_PART_{i}.md',f'Fresh source-state comparison part {i}/{len(groups)}. Publication gains,8 guards and19 A/A failures retained. No new engine release.")
s=s.replace("manifest=z.read('kestrel-sql/SOURCE_COMPARE_079_MANIFEST.sha256').decode('utf-8')", "manifest_name=next(n for n in z.namelist() if n.startswith('kestrel-sql/SOURCE_COMPARE_079_PART_') and n.endswith('_MANIFEST.sha256'))\n            manifest=z.read(manifest_name).decode('utf-8')")
s=s.replace("(W/'repository-manifest-pre-078.sha256')", "(W/'repository-manifest-pre-079.sha256')")
s=s.replace("'release_asset_upload_attempted_in078'", "'release_asset_upload_attempted_in079'")
s=s.replace("'untimed_qualification_complete':True", "'fresh_comparison_complete':True,'all_checks_passed':False")
s=s.replace("'fresh_speed_measurement':False", "'fresh_speed_measurement':True")
s=s.replace('No release-asset upload was attempted in 078','No release-asset upload was attempted in079')
s=s.replace('common manifests/notices identify each part','unique manifests/notices identify each part')
s=s.replace('Preserve complete untimed source-state qualification','Preserve complete fresh source-state comparison')
assert 'repository-manifest-pre-078' not in s
ast.parse(s);(W/'maintain_evidence.py').write_text(s,encoding='utf-8')
print('prepared079 preservation tools; no native workload rerun')
