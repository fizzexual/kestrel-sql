"""Additive077 package correction: retain original frozen maintainer and oversized draft."""
import ast,hashlib,json,shutil,sys,zipfile
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/recovery-compare-077-finalization'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=load(ROOT/'benchmarks/recovery-compare-077-preservation.json')
assert sha(W/'maintain_evidence.py')==proof['payload_sha256']['maintain_evidence.py']
s=(W/'maintain_evidence.py').read_text(encoding='utf-8');s=s[:s.index('assert len(sys.argv)==2')]
ns={'__file__':str(W/'maintain_evidence.py'),'__name__':'preservation_contract'};exec(compile(s,str(W/'maintain_evidence.py'),'exec'),ns)
def correction():
    ns['unchanged']();assert not D.exists();D.mkdir()
    old=ROOT.parent/'kestrel-sql-development-077-recovery-evidence-part-1-of-3.zip';assert old.stat().st_size==63800418
    verified_files=0
    with zipfile.ZipFile(old) as z:
        assert z.testzip() is None
        manifest=z.read('kestrel-sql/RECOVERY_077_PART_1_MANIFEST.sha256').decode()
        for line in manifest.splitlines():
            digest,name=line.split('  ',1)
            with z.open('kestrel-sql/'+name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
            verified_files+=1
        (D/'REPORT-before-package-correction.md').write_bytes(z.read('kestrel-sql/RECOVERY_COMPARE_077.md'))
    (D/'initial-package-size-failure.txt').write_text('First package stage stopped after creating part1of3 at63,800,418bytes, above the50MiB archive limit. AssertionError: kestrel-sql-development-077-recovery-evidence-part-1-of-3.zip. All timed cases and frozen policy/source/inputs/binaries/oracles remained unchanged. No native case rerun. The full oversized draft is retained locally and byte-exact chunks on private Git, with wholeSHA/memberSHA/CRC proof. Corrected packaging uses one timed round per six disjoint ZIPs; all parts remain below50MiB. No benchmark gate relaxed.\n',encoding='utf-8')
    chunks=[]
    with old.open('rb') as f:
        for index in [1,2]:
            p=ROOT.parent/(old.name+f'.draft-chunk-{index}-of-2');assert not p.exists();p.write_bytes(f.read(32*1024*1024));chunks.append({'artifact':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
        assert not f.read(1)
    rebuilt=hashlib.sha256()
    for item in chunks:
        with (ROOT.parent/item['artifact']).open('rb') as f:
            while block:=f.read(1024*1024):rebuilt.update(block)
    assert rebuilt.hexdigest()==sha(old)
    save(D/'initial-package-draft-check.json',{'artifact':old.name,'bytes':old.stat().st_size,'sha256':sha(old),'verified_crc_and_all_member_sha256':True,'verified_payload_files':verified_files,'full_draft_retained_locally':True,'byte_exact_private_git_chunks':chunks,'concatenate_chunks_in_order_to_reconstruct_original_zip':True,'all_original_preservation_payload_hashes_unchanged':True,'no_timed_case_rerun':True})
    shutil.copyfile(W/'finalize_evidence.py',D/'finalize_evidence.py')
    (D/'REPRODUCTION_LAYOUT.md').write_text('''# Corrected complete077 layout

Restore all six `kestrel-sql-development-077-recovery-evidence-part-N-of-6.zip` archives into one staging directory. They have disjoint payloads under the same kestrel-sql prefix. Part1 contains all original harness/source/binary/crates/proofs/raw records, all original input anchors and correctness smoke files plus timed round0. Parts2..6 add one full timed round each. The original preserved REPRODUCE.md and maintainer planned three parts; this additive layout corrects that package count and leaves their hashes unchanged. Other reproduction commands and predeclared benchmark gates are unchanged. The assembly helper should reside at work/prepare_077.py when generating an empty fresh perf077 directory; it is saved inside the evidence directory for preservation.

The first part1of3 package was complete but exceeded the50MiB per-file limit and halted before upload/verification. We independently checked its full CRC/memberSHA and preserve exact bytes locally plus two ordered draft chunks in private Git. Concatenate those two binary chunks to reconstruct the original oversized draft; their whole/member hashes are in initial-package-draft-check.json. That draft is failure evidence, not a required current reproduction part. Its original report planned three parts; current root report and this layout use six. No observed timing/native case was rerun and no benchmark gate or frozen file changed.
''',encoding='utf-8')
    p=ROOT/'RECOVERY_COMPARE_077.md';text=p.read_text(encoding='utf-8').replace('Three complete077 ZIP parts','Six complete077 ZIP parts').replace('all three parts together','all six parts together')
    text+='\nThe initial package plan stopped because its first ZIP was63,800,418bytes, above50MiB. [Additive corrected reproduction layout](benchmarks/recovery-compare-077-finalization/REPRODUCTION_LAYOUT.md) uses six disjoint complete ZIPs; the original three-part plan and full oversized draft remain preserved. [Draft archive and byte-exact chunk proof](benchmarks/recovery-compare-077-finalization/initial-package-draft-check.json). No native case rerun, policy relaxation or original payload change.\n'
    p.write_text(text,encoding='utf-8')
    print(json.dumps({'draft_verified_payload_files':verified_files,'draft_bytes':old.stat().st_size,'draft_chunks':chunks,'six_parts_planned':True}))
def package():
    ns['unchanged']()
    for n,d in proof['payload_sha256'].items():assert sha(ns['DEST']/n)==d,n
    parts=[{} for _ in range(6)]
    for p in ns['DEST'].rglob('*'):
        if p.is_file():parts[0][p.relative_to(ROOT).as_posix()]=p
    for p in D.rglob('*'):
        if p.is_file():parts[0][p.relative_to(ROOT).as_posix()]=p
    for n in ['RECOVERY_COMPARE_077.md','benchmarks/recovery-compare-077-preservation.json']:parts[0][n]=ROOT/n
    for n,d in load(W/'bundle-fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];part=int(n.split('/')[1].split('-')[1][1:]) if n.startswith('fixtures/') else 0
        parts[part]['benchmarks/recovery-compare-077/'+n]=p
    assert len(set().union(*(set(p) for p in parts)))==sum(len(p) for p in parts)
    artifacts=[]
    for index,files in enumerate(parts,1):
        archive=ROOT.parent/f'kestrel-sql-development-077-recovery-evidence-part-{index}-of-6.zip';assert not archive.exists()
        hashes={n:sha(p) for n,p in files.items()}
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
            for n,p in sorted(files.items()):z.write(p,'kestrel-sql/'+n)
            z.writestr(f'kestrel-sql/RECOVERY_077_PART_{index}_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
            z.writestr(f'kestrel-sql/DEVELOPMENT_077_PART_{index}.md',f'Part {index}/6 of disjoint complete metadata evidence. Restore all six together. Four calibrated recovery goals pass;4guards/2A-A fail. No supported engine adoption or competitor result.\n')
        assert archive.stat().st_size<50*1024*1024
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist())==len(hashes)+2
            for n,d in hashes.items():
                with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
        archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
        artifacts.append({'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'part':index,'parts':6,'all_zip_crc_and_member_sha256_verified':True})
        print(json.dumps(artifacts[-1]),flush=True)
    save(ROOT/'benchmarks/recovery-compare-077-bundle-check.json',{'artifacts':artifacts,'full_fixture_files':proof['full_fixture_files'],'full_fixture_bytes':proof['full_fixture_bytes'],'full_fixture_inventory_complete_and_disjoint':True,'all_full_fixtures_bundled':True,'packaged_utc':ns['now'](),'new_engine_release':False,'initial_oversized_draft_proof':'benchmarks/recovery-compare-077-finalization/initial-package-draft-check.json'})
def prepare_git():
    ns['prepare_git']()
    draft=load(D/'initial-package-draft-check.json');added=[]
    for item in draft['byte_exact_private_git_chunks']:
        source=ROOT.parent/item['artifact'];assert sha(source)==item['sha256'];dest=ROOT/'benchmarks'/source.name;assert not dest.exists();shutil.copy2(source,dest)
        added.append({'repository_path':dest.relative_to(ROOT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha(dest),'git_blob_sha':ns['subprocess'].check_output(['git','hash-object','--no-filters',str(dest)],cwd=ROOT,text=True).strip(),'repository_url':'https://github.com/fizzexual/kestrel-sql/blob/main/'+dest.relative_to(ROOT).as_posix(),'role':'byte-exact initial oversized package failure evidence'})
    for path,key in [(ROOT/'benchmarks/recovery-compare-077-publication.json',None),(ROOT/'repository-publication.json','recovery_compare_077')]:
        data=load(path);target=data if key is None else data[key];target['repository_artifacts'].extend(added)
        if key:target['full_evidence_method']='six disjoint complete private Git ZIPs plus original oversized draft chunks'
        save(path,data)
    report=ROOT/'RECOVERY_COMPARE_077.md';text=report.read_text(encoding='utf-8').replace('all three parts together','all six parts together').replace('These three complete ZIPs','These six complete ZIPs')
    text+='\nByte-exact oversized draft failure evidence (concatenate both chunks in order):\n\n'+''.join('- ['+a['repository_path'].split('/')[-1]+']('+a['repository_path']+').\n' for a in added)
    report.write_text(text,encoding='utf-8')
    print(json.dumps({'total_git_artifacts':14,'draft_failure_chunks':2,'frozen_maintainer_unchanged':True}))
if __name__=='__main__':
    assert len(sys.argv)==2
    {'--correct':correction,'--package':package,'--prepare-git':prepare_git,'--verify':ns['verify']}[sys.argv[1]]()
