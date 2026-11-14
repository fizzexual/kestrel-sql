from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
def adapt(s):return s.replace('139','141').replace('138','140').replace('compaction_input_compare_141','compaction_read_compare_141').replace('COMPACTION_INPUT_COMPARE_141','COMPACTION_READ_COMPARE_141')
s=adapt((R/'publish_compare139.py').read_text(encoding='utf-8'))
s=s.replace("==27", "==20").replace("==22", "==15").replace("len(calibrated)==10", "len(calibrated)==8").replace("len(failed)==53", "len(failed)==39")
s=s.replace("'identity_failures':27", "'identity_failures':20").replace("'guard_failures':22", "'guard_failures':15")
s=s.replace("assert all(s['AA_pass'] for s in a['summaries'] if s['ratio_method']=='median within-round ratios')", "assert sum(s['AA_pass'] for s in a['summaries'] if s['ratio_method']=='median within-round ratios')==107")
start=s.index('sources+=[');end=s.index('for name in sorted(set(sources)):',start)
s=s[:start]+'''sources+=['prepare_read_compare141.ps1','read141-controller-derivation.json','analyze_compare141.py','inspect_compare141.ps1',
 'wait_compare141_audit_quiet.ps1','prepare_publication141.py','publish_compare141.py','launch_publish_compare141.ps1',
 'close_compare141_storage.ps1','append_compare141_closed.py']
'''+s[end:]
start=s.index("(D/'FAILED_CHECKS.md').write_text(");end=s.index('\ndef summary(',start)
s=s[:start]+'''(D/'FAILED_CHECKS.md').write_text("""# Every failed check —141

20/144 A/A,15/144 guards and4/6 goals fail. Eight failed guards have passing
corresponding controls.107/108 median controls pass; one catalog-sync median,
four whole-p95 and15 setup-p95 controls fail. All full/both-half samples/stalls
remain. P95 uses nearest-rank quantile ratios (max with12/full or6/half samples);
other metrics use within-round medians. No selected retiming/gate change.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
"""+'\\n'.join(failed)+'\\n',encoding='utf-8',newline='\\n')
'''+s[end:]
start=s.index("report=f'''");end=s.index("for name,marker,addition in [",start)
s=s[:start]+'''report=f"""# Bounded-read comparison141 — October12,2026

**REJECTED:216 independently correct stores,20/144 A/A,15/144 guards and4/6
goals fail. Eight failed guards have passing controls. Supported0.3.16 remains
exact;0.3.17 is unreleased.140 is not adopted.**

Exact131 A/B versus [bounded reads140](COMPACTION_READ_140.md) isolates input
coalescing/direct decode on original64KiB writer. No rejected138 reuse or134/
136 writer code. This component cannot qualify whole-engine/service release.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

Clustered full preparation is12.48% lower, first-half3.94% lower, second-half
14.41% lower. Full/second preparation goals pass; first-half fails10%. Whole
time is2.00% lower full,+2.91% first-half,-2.12% second-half, missing all three
5% goals. Corresponding controls pass. Full/both-half qualification therefore
fails. Displayed p50 quotients differ from medians of paired within-round ratios;
do not combine these ratios with133's separate combined131-versus016 results.

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
{goal_table}

All whole/prepare median controls pass.107/108 median controls pass overall;
one catalog-sync median/four whole-p95/15 setup-p95 controls fail. Ordered full
p95 is5.7109->6.9718ms,1.220788x with passing A/A0.973402. Late apparent full
p95 loss6.133659x has failed A/A0.894549 and is inconclusive. Interleaved full
apparent tail gain also has failed controls. Every stall stays; these intervals
do not identify an exclusive disk/allocator cause. The eight calibrated guards:

{regressions}

[Every39 failed check](experiments/compaction_read_compare_141/FAILED_CHECKS.md)
includes every identity/guard/failed goal. No discarded outliers, retiming or
threshold changes. Whole/setup p95 uses nearest-rank quantile ratios with12/full
or6/half samples=max. Both explicit syncs/receipts/ACK/format remain; no physical
power-loss proof. Preparation improves in several shapes; interleaved full
change is only-0.33%. Further read/merge/index profiling is needed to locate
the remaining costs; that difference alone is not an exclusive cause.

All216 native children/controller/two metadata workers/two auditors actually
exited0. Independently checked7,077,888 exact rows/169,869,312 CRC bytes, indexes,
head and original receipts. All457 probes vs every216 native lifetime (98,712
pairs),2304 original generations from declared run+1. Frozen sources/decoder/
binaries exact; zero actual pauses, all samples once. No failed141 attempt.

Complete216 same-D cases/12 balanced rounds/six shapes/32x1024rows/three columns,
RNG20261011/all6permutations per shape per half, ownedCPU8.120 continuous
observed quiet after preparation/freezes; strict reset/task/supervisor/global
checks before/after every case. Declared outside-lifetime waits unchanged.
All input/read/CRC/phase/index/write/flush/sync charged inside compact_small.
Six excluded preflights196608rows/4718592CRC bytes and idle-dummy/five boundary
tests pass.131340/140352 tests/two lints/36 independent stores/wire/recovery
explicitly REUSED, no Rust build. Audits followed actual exit and
{quiet['continuous_observed_clear_seconds']:.2f} continuously observed clear seconds.
Snapshots cannot exclude every brief unseen task; safety waits are not DB phases.

Policy SHA256:`{sha(W/'policy.json')}`.
Raw journal SHA256:`{a['raw_controller_SHA256']}`.
131 SHA256:`{policy['binary_sha256']['baseline.exe']}`.
140 SHA256:`{policy['binary_sha256']['candidate140.exe']}`.
[Actual controllers and auditors](experiments/compaction_read_compare_141/README.md).
Short source/outcomes/failures privately fresh-byte verified before native exact
completed cleanup; useful kits and all old history/tags/releases retained.
Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service remain. No component-only release/universal-win/ETA.
Use new142+ numbers for justified changes, never overwrite or selected-retime141.
"""
(P/'COMPACTION_READ_COMPARE_141.md').write_text(report,encoding='utf-8',newline='\\n')
(D/'README.md').write_text("""# Complete bounded-read comparison141

Exact131 A/B versus140 C, fixed216-case balanced same-D cohort. Actual inputs,
order, probes, CRC/payload/index/receipt/generation/frozen-byte proofs and all
native/controller/worker/auditor exits pass.20 controls/15 guards/4 goals fail;
eight calibrated guards remain,140 is not adopted. See the main report and
FAILED_CHECKS.md for every failure and the limited preparation reductions.
Every actual frozen source is saved byte-exact. Reused352 tests/wire/recovery,
no build or failed141 attempt. Original full/both-half/numerical/release gates
remain. No selected retiming/outlier discard or DB scheduling claim. Use fresh
142+ numbers/current provenance, never overwrite141. Short private outcomes/
source freshly verified before native exact cleanup; no raw bundle/history loss.
0.3.16 exact,0.3.17 unreleased, all builds/tests local under Actions0 Stop usage.
""",encoding='utf-8',newline='\\n')
'''+s[end:]
start=s.index('for name,marker,addition in [');end=s.index("allowed=['COMPACTION_READ_COMPARE_141.md'",start)
s=s[:start]+'''for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Bounded compaction reads140]','- [Complete bounded-read comparison141](COMPACTION_READ_COMPARE_141.md)\\n'),
 ('VERSION_SUMMARY.md','New bounded-read140 passed352','Complete141 rejects bounded reads140:216 independently correct cases,20/144\\nA/A,15/144 guards and4/6 goals fail. Full clustered preparation is12.48% lower\\nbut its goal misses first-half; whole time is2.00% lower, ordered p95+22.08%.\\n[Complete outcome](COMPACTION_READ_COMPARE_141.md).\\n\\n'),
 ('README.md','[Bounded compaction reads140]','[Complete bounded-read comparison141](COMPACTION_READ_COMPARE_141.md):216\\ncorrect cases,20 controls/15 guards/4 goals fail;140 is not adopted.\\n\\n')]:
    f=P/name; text=f.read_text(encoding='utf-8'); assert text.count(marker)==1
    f.write_text(text.replace(marker,addition+marker,1),encoding='utf-8',newline='\\n')
f=P/'VERSION_SUMMARY.md'; text=f.read_text(encoding='utf-8')
assert text.count('six exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).')==1
text=text.replace('six exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).','six exact wire pairs and14 recovery cases. Performance measured and rejected in141. [Actual code](COMPACTION_READ_140.md).')
f.write_text(text,encoding='utf-8',newline='\\n')
f=P/'README.md'; text=f.read_text(encoding='utf-8')
assert text.count('stores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.')==1
f.write_text(text.replace('stores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.','stores and14 recovery cases. Performance measured and rejected in141;0.3.17 unreleased.'),encoding='utf-8',newline='\\n')
'''+s[end:]
s=s.replace('Reject input reuse141 after complete controlled comparison and independent audits','Reject bounded reads141 after complete controlled comparison and independent audits')
ast.parse(s)
target=R/'publish_compare141.py';assert not target.exists();target.write_text(s,encoding='utf-8',newline='\n')
for old,new in [('launch_publish_compare139.ps1','launch_publish_compare141.ps1'),('close_compare139_storage.ps1','close_compare141_storage.ps1')]:
    text=adapt((R/old).read_text(encoding='utf-8')).replace('-ne 27','-ne 20').replace('-ne 22','-ne 15').replace('compaction-kit-140','compaction-kit-140')
    target=R/new;assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
print('141 complete rejected outcome publisher/native exact cleanup prepared')
