"""Adapt only preservation plumbing for fresh complete150 prerequisites."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
def write(p,s):
    assert not p.exists(),p
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
s=(R/'publish_payload147.py').read_text(encoding='utf-8').replace('147','150').replace('payload','contiguous')
s=s.replace("def write(p,s):p.write_text(s,encoding='utf-8',newline='\\n')", "def write(p,s):p.write_text(s.rstrip()+'\\n',encoding='utf-8',newline='\\n')")
start=s.index("assert recovery['complete']");end=s.index('assert all(sha(C/n)',start)
s=s[:start]+'''assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128
for name,key,wait in [('contiguous150-source-actual-exits.json','preparation_actual_exit','actual_preparation_wait_completed'),('contiguous150-build-actual-exits.json','build_actual_exit','actual_build_controller_wait_completed'),('contiguous150-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('contiguous150-wire-actual-exits.json','wire_actual_exit','actual_wire_wait_completed'),('contiguous150-recovery-build-actual-exits.json','recovery_artifact_build_actual_exit','actual_recovery_build_wait_completed'),('contiguous150-recovery-actual-exits.json','recovery_actual_exit','actual_recovery_wait_completed')]:
    proof=load(R/name);assert proof[key]==0 and proof[wait],name
'''+s[end:]
s=s.replace("tofile='b/'+name))","tofile='b/'+name,n=0))")
s=s.replace("W/'contiguous-only-change.patch'","W/'contiguous-only-change.patch'")
start=s.index('sources=[');end=s.index('for n in sources:',start)
s=s[:start]+'''sources=['declare_prepare_contiguous_150.py','contiguous150_test.rs','prepare_contiguous150_source.ps1','prepare_contiguous150_prerequisites.py','build_contiguous_150.py','check_contiguous150_prerequisite_activity.ps1','launch_build_contiguous150.ps1',
    'prepare_contiguous150_store_auditor.py','audit_contiguous150_stores.py','launch_audit_contiguous150.ps1','prepare_contiguous150_wire_recovery.py','audit_contiguous150_legacy_wire.py','check_contiguous150_wire_activity.ps1','launch_wire_contiguous150.ps1',
    'build_contiguous150_recovery.ps1','launch_build_contiguous150_recovery.ps1','run_contiguous150_recovery.py','check_contiguous150_recovery_activity.ps1','launch_recovery_contiguous150.ps1',
    'append_contiguous150_started.py','prepare_contiguous150_publication.py','publish_contiguous150.py','verify_contiguous150_remote.py','launch_publish_contiguous150.ps1','close_contiguous150_storage.ps1','append_contiguous150_closed.py']
'''+s[end:]
start=s.index("for n in ['policy.json'");end=s.index("write(D/'README.md'",start)
s=s[:start]+'''for n in ['policy.json','declaration-proof.json','preparation-proof.json','build-proof.json','store-audit.json','legacy-wire-audit.json','legacy-wire-declaration.json','recovery-declaration.json','recovery-artifact-build.json','declaration-rationale-clarification.json']:
    write(D/n,json.dumps(load(W/n),indent=2)+'\\n')
write(D/'recovery-summary.json',json.dumps({k:v for k,v in recovery.items() if k not in ['commands','checks']},indent=2)+'\\n')
for n in ['contiguous150-source-actual-exits.json','contiguous150-build-actual-exits.json','contiguous150-audit-actual-exits.json','contiguous150-wire-actual-exits.json','contiguous150-recovery-build-actual-exits.json','contiguous150-recovery-actual-exits.json','contiguous150-started-next-proof.json']:
    write(D/n,json.dumps(load(R/n),indent=2)+'\\n')
write(D/'DECLARATION_CLARIFICATION.md','The preserved declaration accidentally called prior147 output CRC vectors96.\\nActual output is24 for32768 rows/3 columns with4096-row blocks;96 described\\nearlier input-column temporaries. The clarification was saved separately; no\\nengine, acceptance criterion, test, timer or numerical gate changed. No allocator\\ncausal proof inferred. Every150 build/native/audit/recovery attempt passed.\\n')
'''+s[end:]
start=s.index("write(D/'README.md'");end=s.index("for n,addition in",start)
report='''# Contiguous CRC/output buffer150 — October13,2026 UTC

**Actual allocation change implemented:348 fresh tests/two strict lints,
52 independent stores, six exact supported format pairs and14 recovery cases
pass. Speed UNMEASURED; supported0.3.16 exact,0.3.17 unreleased.**

On exact131+144, small compaction uses one preallocated byte Vec instead of
retaining separate block Vecs. The original little-endian iterator fills it
directly; CRCs use exact newly filled slices and the original64KiB writer consumes
the same block spans. Checked logical bytes and ACTUAL Vec capacity<=1MiB;
overbudget drops it/original stream fallback. One descriptor/other arrays are
additional, not an RSS cap. Drop before explicit flush/sync. Ordinary append and
larger compaction keep original CRC temporary/stream; no cross-publication cache.

Reader/inputCRC/sums/block extrema/monotonicity/phase/merge/sortedness/index/
format/both explicit syncs/catalog rename/receipt/ACK/cutpoints unchanged.
No unsafe/dependency/API/global setting/rejected134/136/138/140/147 code.
[Vec capacity contract](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.with_capacity)
requires checking actual capacity; stable APIs only, below MSRV1.89. No speed
or exclusive allocator/disk cause inferred from those implementation facts.

149 measured ordered preparation+19.26% full/+16.46% first/+21.53% second and
ordered write+12.86% with passing controls; extreme p95 5.615382x with passing
control.149 compared joint131+144+147 versus016 and cannot isolate147. This
allocation/locality hypothesis targets those costs; a complete new comparison
is required, not ratios added across cohorts. Prior147 output is24 vectors for
32768 rows/three columns/4096-row blocks; the original declaration's96 count
was corrected in a separate clarification without engine/gate changes.

Four fresh normal/fault debug/release suites87 each=348, two strict lints and
original durable driver actual0. All52 predeclared stores644636 exact rows/
15471264 CRC bytes/full indexes/original receipt digests/generations pass.
Retained/fallback boundaries2/4095/4096/4097/43690/43691, SQL reference/extreme
values/pins/reclaim/mismatch/cold reopen covered. All12 excluded supported016/
candidate stores393216 rows/9437184 CRC bytes pass; six segment/catalog pairs
byte-exact. Every150 case/build/auditor passed; no passed prerequisite repeated.

All14 publication recovery cases/56 expected commands pass:28672 rows/
688128 CRC bytes/original receipts and generations/cold queries. Seven owned
exits86/seven injected IO errors87; head2 before publication/head3 after. IO
errors poison writer while old snapshot remains readable. No forced unrelated
kill or physical power-loss proof. Recovery artifact builds did not repeat tests.

Future fresh151+ complete216 balanced same-D supported016 A/B versus
joint131+144+150 C does not isolate150. Full/both-half144 A/A/144 guards/six
clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10, whole/setup
p95=max and all input/readCRC/phase/index/write/flush/sync charged unchanged.
No selected retiming/outlier discard/gate loosening. Original release324 Native/
252 service/42 goals/153 A/A/171 guards plus correctness/recovery/sustained
service remain before adoption. [Exact source/proofs](experiments/compaction_contiguous_150/README.md).
Short private outcomes/source/failures freshly verified before native completed
fixture/build cleanup; useful kits/history/tags/releases retained, no raw bundle.
'''
readme='''# Reproduce isolated contiguous150

Apply candidate.patch to supported016 using git apply --unidiff-zero; copy
merge_runs_131.rs to src and compaction_150.rs to tests. Feature:
contiguous-compaction-payload-150. Original121 driver and099 independent
decoder apply. Use fresh paths/numbers; never rerun historical150. Actual
source, fixed untimed policy and complete correctness/wire/recovery proofs
saved.348 fresh tests/two lints/52 stores/six wire pairs/14 recovery cases pass.
Speed unmeasured, no adoption. See declaration clarification; no raw bundle.
'''
s=s[:start]+"write(D/'README.md',"+repr(readme)+")\nreport="+repr(report)+"\nwrite(P/'COMPACTION_CONTIGUOUS_150.md',report)\n"+s[end:]
s=s.replace('COMPACTION_PAYLOAD_150','COMPACTION_CONTIGUOUS_150')
s=s.replace('Reuse bounded compaction CRC contiguous150 with full correctness and recovery','Use one bounded contiguous compaction CRC buffer150 with full correctness and recovery')
write(R/'publish_contiguous150.py',s)
verify=(R/'verify_payload147_remote.py').read_text(encoding='utf-8').replace('147','150').replace('payload','contiguous').replace('COMPACTION_PAYLOAD_150','COMPACTION_CONTIGUOUS_150')
write(R/'verify_contiguous150_remote.py',verify)
close=(R/'close_payload147_storage_v2.ps1').read_text(encoding='utf-8').replace('147','150').replace('payload','contiguous')
close=close.replace('contiguous150-recovery-finish-actual-exits.json','contiguous150-recovery-actual-exits.json').replace('contiguous150-publication-v2-actual-exits.json','contiguous150-publication-actual-exits.json')
close=close.replace(' -or $taskRecovery.new_native_commands -ne 53','').replace(' -or -not $taskRecovery.no_native_case_repeated','')
write(R/'close_contiguous150_storage.ps1',close)
print('150 concise publisher/verification/native cleanup prepared; no save/delete yet')
