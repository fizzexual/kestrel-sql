from pathlib import Path
import hashlib,json,zipfile
w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql';d=root/'benchmarks/trial-050-generation-identity'
package=root.parent/'kestrel-sql-development-cat5-050-correctness-evidence.zip';assert not package.exists()
assert json.loads((d/'correctness-audit.json').read_text(encoding='utf-8'))['all_14_final_external_gates_passed']
files=[*sorted(p for p in d.rglob('*') if p.is_file()),root/'TRIAL_050.md',root/'TRIAL_049.md',root/'benchmarks/trial-049-follow-up.json',root/'benchmarks/trial-050-preservation.json',root/'benchmarks/baseline-0.3.16-provenance.json']
inventory={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with zipfile.ZipFile(package,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,'kestrel-sql/'+p.relative_to(root).as_posix())
    z.writestr('kestrel-sql/TRIAL_050_MANIFEST.sha256',''.join(f'{digest}  {name}\n' for name,digest in sorted(inventory.items())))
    z.writestr('kestrel-sql/TRIAL_050_BUNDLE.md','# Unreleased generation identity hardening 050\n\nThis is development evidence, not a supported KestrelSQL release. Candidate source and binaries are isolated. Their inherited version string is 0.3.16; CAT5 and trial labels distinguish them. See TRIAL_050.md for correctness qualification and every failure. Fresh performance is pending; historical 049 measurements are separate. Original 0.3.16 release archives remain immutable. The adjacent manifest covers all copied payloads.\n')
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    for name,digest in inventory.items():assert hashlib.sha256(z.read('kestrel-sql/'+name)).hexdigest()==digest
    assert len(z.namelist())==len(inventory)+2
digest=hashlib.file_digest(package.open('rb'),'sha256').hexdigest();package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n',encoding='utf-8')
proof={'artifact':package.name,'bytes':package.stat().st_size,'sha256':digest,'payload_files':len(inventory),'zip_entries':len(inventory)+2,'all_payloads_and_zip_crc_verified':True,'trial_promoted':False,'default_engine_changed':False,'original_release_archive_replaced':False}
(root/'benchmarks/trial-050-bundle-check.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
