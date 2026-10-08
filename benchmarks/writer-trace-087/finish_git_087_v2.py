from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/writer-trace-087'
FAIL = OUT / 'commit-whitespace-check-failure'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + REPO.as_posix(), '-C', str(REPO), *args], text=True).strip()

assert git('rev-parse', 'HEAD') == 'b29bef3ba32e49d220337f8aa6cb763fe554a62c'
assert not (FAIL / 'finish-git-087-run.log').exists()
shutil.copy2(ROOT / 'work/finish-git-087-run.log', FAIL / 'finish-git-087-run.log')
shutil.copy2(ROOT / 'work/finish_git_087_v2.py', OUT / 'finish_git_087_v2.py')
proof_path = OUT / 'commit-whitespace-validation.json'
proof = json.loads(proof_path.read_text(encoding='utf-8'))
transcripts = {}
for path in sorted(FAIL.glob('*.log')):
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    trailing = [(i + 1, line) for i, line in enumerate(lines) if line.rstrip() != line]
    assert len(trailing) == 16 and all(line in ['+ ', '++ '] for _, line in trailing), trailing
    transcripts[path.name] = {'sha256': sha(path), 'only_whitespace_is_quoted_required_context_markers': True, 'lines': [i for i, _ in trailing]}
command = ['git', '-c', 'safe.directory=' + REPO.as_posix(), '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', '-C', str(REPO), 'diff', '--cached', '--check', '--', '.', ':(exclude)benchmarks/writer-trace-087/*.diff', ':(exclude)benchmarks/writer-trace-087/commit-whitespace-check-failure/*.log']
proof['command'] = command
proof['frozen_failure_transcripts_independently_validated'] = transcripts
proof['explanation'] = 'Exact frozen diff context markers and their quoted diagnostic transcripts retain required spaces. Every other staged file receives all default whitespace checks; no source/raw bytes or global Git config change.'
proof_path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
report = REPO / 'WRITER_TRACE_087.md'
text = report.read_text(encoding='utf-8')
old = 'applies every default whitespace check to all other staged files and independently checks the sixteen context markers.'
new = 'applies every default whitespace check to all other staged files and independently checks the sixteen context markers and their exact quoted failure transcripts.'
assert text.count(old) == 1
report.write_text(text.replace(old, new), encoding='utf-8', newline='\n')
allowed = ['README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md', 'WRITER_TRACE_087.md', 'benchmarks/writer-trace-087']
git('add', '--', *allowed)
paths = git('diff', '--cached', '--name-only').splitlines()
assert all(name in allowed or name.startswith('benchmarks/writer-trace-087/') for name in paths)
subprocess.check_call(command)
git('commit', '-m', 'Qualify bounded optional service-writer diagnostics and preserve trial087')
head = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain')
subprocess.check_call(['git', '-c', 'safe.directory=' + REPO.as_posix(), '-C', str(REPO), 'merge-base', '--is-ancestor', 'b29bef3ba32e49d220337f8aa6cb763fe554a62c', 'HEAD'])
with (ROOT.parent / 'KESTREL_NEXT.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n087 reports, sources/evidence and release navigation are saved in local commit `' + head + '`, with a clean working tree and all preceding commits retained. Remote unchanged. Supplemental Git checks preserve exact raw context markers/failure transcripts; all other default whitespace checks and independent marker/transcript validation pass.\n')
result = {'head': head, 'clean': True, 'parent_preserved': True, 'remote_unchanged': True, 'supported': '0.3.16', 'utc': datetime.now(timezone.utc).isoformat()}
(ROOT / 'work/commit-087-proof.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
