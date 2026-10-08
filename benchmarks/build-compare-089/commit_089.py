"""Save verified 089 evidence/docs in private local history without maintenance."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/build-compare-089'
W = ROOT / 'work/perf-089'
PARENT = 'b6c47bf68cbacea09effde619e6e2bd0653b3b4f'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(*args):
    return ['git', '-c', 'safe.directory=' + REPO.as_posix(), '-c', 'gc.auto=0',
        '-c', 'maintenance.auto=false', '-C', str(REPO), *args]


def git(*args):
    return subprocess.check_output(command(*args), text=True).strip()


preservation, restored = load(OUT / 'preservation-proof.json'), load(OUT / 'restored-audit-proof.json')
assert preservation['complete'] and restored['passed']
assert restored['native_launches'] == restored['timing_reruns'] == 0
assert git('rev-parse', 'HEAD') == PARENT
assert all(sha(REPO / name) == digest for name, digest in load(W / 'unchanged-supported-source.json').items())
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
for name in ['BUILD_COMPARE_089.md', 'RELEASE_TARGET_0_3_17.md', 'README.md', 'BENCHMARK_HISTORY.md']:
    for target in re.findall(r'\]\(([^)]+)\)', (REPO / name).read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        assert (REPO / target.split('#')[0]).exists(), (name, target)
assert not (OUT / 'commit_089.py').exists()
shutil.copy2(ROOT / 'work/commit_089.py', OUT / 'commit_089.py')
for name in ['finish-089.log', 'check_final_state_089.ps1', 'prepare_final_guard_089.py']:
    assert not (OUT / name).exists()
    shutil.copy2(ROOT / 'work' / name, OUT / name)
nextfile = ROOT.parent / 'KESTREL_NEXT.md'
backup = ROOT / 'work/KESTREL_NEXT-after-active-before-completed-089.md'
assert not backup.exists()
shutil.copy2(nextfile, backup)
addition = f'''
## Completed controlled default-build comparison 089, October 8, 2026

Read repository BUILD_COMPARE_089.md, benchmarks/build-compare-089/audit.json, policy.json and restored-audit-proof.json. Three fresh matched-toolchain isolated controls use untouched supported 0.3.16 sources, stock sources with only the self-package version changed to 0.3.17-dev.87-released, and corrected 087 released-core diagnostic sources normalized to 0.3.16 with diagnostics disabled. Exact original 0.3.16 remains the artifact control. All original source bytes are preserved except declared version edits and identical untimed byte-oracle fixture additions. Prior 087 diagnostic line endings remain exact; source paths/metadata/compiler/artifact effects prevent exclusive causality. Original-version labels are isolated controls, not supported promotion.

Fresh separate D: targets use rustc/cargo 1.97.1, locked offline existing dependencies, thin LTO/one codegen unit, incremental off and no ambient extra flags. All three debug/release suites and strict default lint pass: 464 native test executions. Eight sequence/oversized stores are byte-equivalent, 32 cross-reopens and 32 independent SQLite checks pass; 72 external native oracle commands and four default-wire checks succeed. Default tracing/fault controls remain absent. All four smokes pass and are excluded. Earlier broad crash/source qualification is explicitly reused, not newly run.

Twelve rounds/two independently complete six-permutation pair/slot-balanced halves run three families (original/rebuilt, package-version-only, diagnostic-default-same-version), two profiles and three variants: 216 fresh serial stores, 1M seed, 64 clients, 100-row anonymous batches, zero deliberate grouping delay, read 2000/s and 25%-write 500/s for 8 seconds. All fixed 088 compatibility limits remain unchanged, including zero loss and Native peak ratio/additional 2 MiB guards. Full and both halves are required; C/B is diagnostic only. No tracing is enabled in any tested variant.

All 2,160,000 offers succeed with zero errors/loss/drops/expiries/unexecuted requests. All 110,268 acknowledged batches survive reopen with exact atomic count/sum reconciliation and no ambiguous committed outcome. 4,320 independent NumPy windows and 5,448,643,200 full-CRC row-data bytes pass. All 307 >100 ms service samples remain included. No candidate criterion fails (0/117), but A/A fails 8/117 criteria across six of nine scopes. Every family fails at least one required scope. All rate/loss/memory and write-profile query criteria pass; control failures cover rebuild write overall in full/both halves, diagnostic write overall in full/first half and append in first half, version-only read overall/query in second half. Full/half/read metrics overlap and are not independent statistical observations.

Full rebuild write overall paired C/A=1.069345, matching A/A=0.874794 fails; diagnostic overall C/A=0.969807, A/A=1.254208 fails. Diagnostic append full A/A narrowly passes 1.099998, but its first-half append calibration fails. Neither a numerical pass nor a passing individual scope establishes a gain, complete compatibility, tracer overhead or a release. New 089 does not replace or invalidate 088's preserved calibrated regressions; normalized-version diagnostic artifacts differ from the earlier candidate. Supported 0.3.16 and frozen overnight report remain byte-exact. No competitor refresh, six-profile integrated release qualification or 0.3.17 date is established.

All Native jobs stopped at timing completion before audit/preservation. {len(preservation['parts'])} bounded ZIP parts preserve {preservation['files']:,} files/{preservation['logical_bytes']:,} logical bytes at benchmarks/build-compare-089. Every raw sample/ACK, service/smoke/oracle/cargo-test fixture, binary/source/lock, policy/harness/helper/log and failed step is preserved. Only regenerable target/Python caches are excluded with explicit path/size inventory, and all originals remain intact at work/perf-089. Whole ZIP/member CRC/SHA/size/exact-set checks, original-byte revalidation, exact frozen raw-audit replay and post-replay member hashes/sizes/sets pass. Restoration is work/restored-build-089; zero Native or timer reruns. Completed stdout logs were excluded from frozen dependencies and copied only after closure. A nonexistent-file read error and the initial reporting helper's flat-vs-nested source-hash schema failure are retained with their raw logs/exact failed helper; the frozen Native audit passed first try and no timed data changed.

Post-timing stock/diagnostic source comparison retains full diff and exact hashes. Two unconditional maintenance-result/control-flow rewrites remain in feature-disabled diagnostic sources; this is a source hypothesis, not measured root-cause proof. Next use 090 or later to restore the original feature-disabled execution shape in an isolated diagnostic trial, verify correctness/bytes/protocol/recovery and predeclare stronger complete balanced controls before timing. Diagnostic investigation does not substitute for a measured writer improvement. Preserve every 086–089 failure and every raw block; no selective repeat, gate relaxation, durability reduction, candidate/B substitution or rejected-reader adoption. A concrete integrated improvement still needs full native/six-profile/minute/overload/scan/memory/source/retry/crash/corrupt/old-format/exclusive-writer/competitor/restored-audit release gates.

Before further heavy work, check live task-owned jobs and prepared reset. Latest post-timing check verified no jobs, exact waiting worker identity/owner and waiting-for-full-codex-exit; reset remains prepared, not executed. Never force-close apps, interfere with executing reset, resume the abandoned chat, widen cleanup, enable old migration task/automation or resurrect a discarded heartbeat. Current D: continuation remains authorized and quiet on unchanged state; follow existing post-reset physical roots/new D: chat guidance.
'''
nextfile.write_text(nextfile.read_text(encoding='utf-8') + addition, encoding='utf-8', newline='\n')
allowed = ['README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md',
    'BUILD_COMPARE_089.md', 'benchmarks/build-compare-089']
git('add', '--', *allowed)
staged = git('diff', '--cached', '--name-only').splitlines()
assert staged and all(name in allowed or name.startswith('benchmarks/build-compare-089/') for name in staged)
subprocess.check_call(command('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff', '--cached', '--check'))
git('commit', '-m', 'Preserve controlled build-source comparison and complete trial089 evidence')
head = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain')
subprocess.check_call(command('merge-base', '--is-ancestor', PARENT, 'HEAD'))
subprocess.check_call(command('merge-base', '--is-ancestor', '14155d52d36faafe31654de19914e12cd3e805d3', 'HEAD'))
assert all(sha(REPO / name) == digest for name, digest in load(W / 'unchanged-supported-source.json').items())
with nextfile.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n089 reports and complete evidence are saved in private local commit `' + head + '`, with a clean tree, prior history retained and no remote publication.\n')
proof = {'head': head, 'clean': True, 'all_prior_history_preserved': True,
    'supported_core_and_overnight_unchanged': True, 'no_remote_publication': True,
    'supported': '0.3.16', 'qualification_failed_due_to_AA': True,
    'utc': datetime.now(timezone.utc).isoformat()}
(ROOT / 'work/commit-089-proof.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
