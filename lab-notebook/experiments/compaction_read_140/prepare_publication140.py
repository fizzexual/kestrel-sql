from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
def adapt(s):
    return s.replace('138','140').replace('reuse140','coalesce140').replace('reuse_140','coalesce_140').replace('compaction_input_140','compaction_read_140').replace('COMPACTION_INPUT_140','COMPACTION_READ_140').replace('344','352').replace('all20_compaction_stores_checked','all36_compaction_stores_checked').replace('312252','525380').replace('7494048','33056352').replace('independent20_stores','independent36_stores')
s=adapt((R/'publish_reuse138.py').read_text(encoding='utf-8'))
start=s.index('names=['); end=s.index('for name in names:',start)
s=s[:start]+'''names=['coalesce140_test.rs','reuse138_test.rs','declare_prepare_coalesce_140.py','prepare_coalesce140.ps1',
 'build_coalesce_140.py','check_coalesce140_prerequisite_activity.ps1','launch_build_coalesce140.ps1','append_coalesce140_started.py',
 'prepare_coalesce140_auditor.py','archive_audit_140.py','audit_coalesce140_stores.py','launch_audit_coalesce140.ps1',
 'prepare_correctness140.py','audit_coalesce140_legacy_wire.py','check_coalesce140_wire_activity.ps1','launch_wire_coalesce140.ps1',
 'build_coalesce140_recovery.ps1','launch_build_recovery140.ps1','run_coalesce140_recovery.py','check_coalesce140_recovery_activity.ps1',
 'launch_recovery_coalesce140.ps1','prepare_publication140.py','publish_coalesce140.py','launch_publish_coalesce140.ps1',
 'close_coalesce140_storage.ps1','append_coalesce140_closed.py']
'''+s[end:]
start=s.index("(D/'README.md').write_text(");end=s.index("(P/'COMPACTION_READ_140.md').write_text",start)
s=s[:start]+'''(D/'README.md').write_text("""# Bounded compaction input reads140

Apply candidate.patch to byte-exact supported016 with git apply --unidiff-zero,
copy merge_runs_131.rs to src and compaction_140.rs to tests; use feature
coalesced-compaction-read-140. This adds a <=1MiB full-run read/CRC/decode path
to exact131 phase/merge and original64KiB writer. Larger input uses the original
block path. No rejected138 reuse or134/136 writer is included.

Every column/block CRC is checked before decoding or appending. Existing
read_exact_at short/Interrupted/EOF loop, Reader and complete publication code
remain. Each temporary byte Vec is local to one run; no cross-run cache. All
input/CRC/phase costs stay inside compaction. Both explicit syncs, indexes,
receipts/ACK, faultpoints and wire format remain. No unsafe/dependency/API/global
setting change. Source counts96->32 read requests and96->0 decoded temporaries
for32x1024rows/3columns are not measured syscalls, allocations or speed.

352 fresh tests/two strict lints, ALL36 independent stores525380 exact rows/
33056352 CRC bytes, six exact wire pairs/12 excluded cases and14 recovery cases/
56 expected commands pass. Wide16-column inputs test8191/8192/8193 rows on both
sides of the cutoff. Last-column partial-block CRC and truncation fail before
publication, then restore successfully. Original receipt digests/generations,
SQL reference, pins/reclaim, growth/late rows and cold reopen checked.
Original099 decoder is separately extended only for exactly ts,c1..c15; every
envelope/index/payload/CRC/receipt check remains. Actual sources are saved.

Every prerequisite controller exited0; no failed140 attempt or passed suite
repeat. No140 timed cohort, SPEED UNMEASURED. Seven controlled exits86/seven
injected IO errors87 are not physical power-loss proof. Use fresh141+ paths for
complete balanced comparison and unchanged full/both-half/release gates. Never
overwrite140.0.3.16 exact,0.3.17 unreleased; source/short results private-verified
before native exact completed cleanup. No raw multiGB bundle/history deletion.
""",encoding='utf-8',newline='\\n')
report=f"""# Bounded compaction reads140 — October12,2026

**New code passed correctness and recovery. Speed is unmeasured; supported
0.3.16 stays unchanged and0.3.17 is unreleased.**

The131 compaction path requested every column block separately.140 reads a
contiguous immutable run when its payload is<=1MiB, checks every block CRC,
then decodes directly into final columns. Larger runs follow the original path.
The32x1024-row/three-column source structure changes96->32 positional read
requests and96->0 temporary decoded vectors. Each run has one bounded byte
buffer, dropped before the next run/merge/publication. These are structural
counts, not measured syscall/allocation counts or elapsed gains.

This targets preparation that remained roughly1–2.5ms in139.139 rejected
allocation reuse: clustered full preparation improved9.92% but did not hold in
both halves, while controlled regressions remained.140 starts from exact131;
rejected138 reuse and134/136 writer code are absent. Its phase choice depends
on actual payload size, with the existing ordered/disordered merge choice.

Every read/CRC/phase/index/write/flush/sync is charged inside compaction.
Existing Reader and publication functions are exact: final sortedness/indexes/
CRC, both explicit syncs, catalog rename, receipts/ACK/cutpoints remain. No unsafe,
new dependency/API/format/cache/global change. [Rust FileExt permits short reads](https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html#tymethod.seek_read);
the existing read_exact_at loop remains, with absolute offsets and Interrupted/
EOF handling. A full-run request is not an unchecked single-read assumption.

| Completed prerequisite | Fresh evidence |
| --- | --- |
| Normal/fault debug/release |88 each,352 tests; two strict lints; actual exit0 |
| Independent test stores |36 stores,525380 exact rows,33056352 CRC bytes |
| Compatibility |Six exact131/140 wire pairs;12 excluded cases,393216 rows |
| Publication recovery |14 faults,56 expected commands;28672 rows,688128 CRC bytes |

Wide16-column8191/8192/8193-row tests cover below/exact/above1MiB, all-column SQL
references, pins, original retries/mismatches and cold reopen. Multi-block final
column CRC/truncation tests leave head/catalogs/segments unchanged, then restore
and compact. All36 stores independently checked for complete tuples/indexes/
CRCs/original receipt digests/generations. The independent099 decoder changes
only its metadata whitelist to permit exactly the declared16 columns.

All controllers actually exited0; no failed140 attempt or passed suite repeat.
Seven owned controlled exits86/seven IO errors87 preserve original receipts,
head2 before publication/head3 afterward and cold queries. IO errors poison
the writer while the old snapshot stays readable. No unrelated process kill or
physical power-loss claim. Candidate SHA256:`{build['candidate_sha256']}`.
[Actual patch, tests and controllers](experiments/compaction_read_140/README.md).

Future141+ must compare exact131A/B versus140C in the complete balanced same-D
216-case cohort, full/both-half144 A/A/144 guards and six unchanged clustered
whole<=.95/prepare<=.90 goals. Retain stage/write+sync/whole/setup-tail guards,
every stall, independent lifetimes/receipts/frozen bytes and actual exits. No
selected retiming. Original324Native/252service/42goals/153AA/171guards plus
correctness/retry/recovery/sustained service remain before adoption. This code
alone cannot qualify release. Short private outcomes/source freshly byte-verified
before exact native completed cleanup; useful kit/history retained, no raw bundle.
"""
'''+s[end:]
start=s.index('for name,mark,add in [');end=s.index('tracked=sorted',start)
s=s[:start]+'''for name,mark,add in [
 ('BENCHMARK_HISTORY.md','- [Complete input-allocation comparison139]','- [Bounded compaction reads140](COMPACTION_READ_140.md)\\n'),
 ('README.md','[Complete input-allocation comparison139]','[Bounded compaction reads140](COMPACTION_READ_140.md) passed352 tests,36 independent\\nstores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.\\n\\n'),
 ('VERSION_SUMMARY.md','Complete139 rejects input reuse138:','New bounded-read140 passed352 fresh tests/two lints,36 independent stores,\\nsix exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).\\n\\n')]:
    f=P/name; text=f.read_text(encoding='utf-8'); assert text.count(mark)==1,(name,mark)
    f.write_text(text.replace(mark,add+mark,1),encoding='utf-8',newline='\\n')
'''+s[end:]
s=s.replace("git('commit','-m','Reuse compaction input workspaces with full correctness and recovery checks [skip ci]')", "git('commit','-m','Add bounded compaction reads140 with full correctness and recovery [skip ci]')")
ast.parse(s)
target=R/'publish_coalesce140.py';assert not target.exists();target.write_text(s,encoding='utf-8',newline='\n')
for old,new in [('close_reuse138_storage.ps1','close_coalesce140_storage.ps1'),('launch_publish_reuse138.ps1','launch_publish_coalesce140.ps1')]:
    target=R/new;assert not target.exists();target.write_text(adapt((R/old).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
print('140 publisher/native scoped cleanup prepared; no publication or deletion yet')
