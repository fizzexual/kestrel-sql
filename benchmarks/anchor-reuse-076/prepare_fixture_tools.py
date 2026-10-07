"""Scope completed 075 duplicate cleanup; never lower qualification disk guard."""
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-075'
s=(OLD/'prepare_reclamation.py').read_text(encoding='utf-8').replace('073','075').replace('receipt-cycles-075','hybrid-cycles-075').replace('120','122').replace('6420','3546')
(W/'prepare_fixture_reclamation.py').write_text(s,encoding='utf-8')
s=(OLD/'reclaim_duplicates.ps1').read_text(encoding='utf-8').replace('073','075').replace('6420','3546')
(W/'reclaim_fixture_duplicates.ps1').write_text(s,encoding='utf-8')
trace='''2026-10-07T14:51:14Z: qualification disk guard stopped before any child/output directory.
Command: python work/perf-076/qualify.py
Exit:1
Traceback (most recent call last):
  File "work/perf-076/qualify.py", line 24, in <module>
    assert shutil.disk_usage(W).free >= 2_500_000_000
AssertionError
Recorded pre-qualification free bytes:2018971648.
No qualification fixture/input/raw directory or policy/result was created. No observed case rerun. Minimum 2.5GB unchanged; free space recovered only from fully archived completed 075 duplicates.
'''
(W/'qualification-disk-guard-failure.txt').write_text(trace,encoding='utf-8')
