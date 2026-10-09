"""Fresh byte/old-reader/SQLite/Live retry controls, full Native/wire journals; no load timers."""
from pathlib import Path
from datetime import datetime,timezone
import concurrent.futures,hashlib,json,os,runpy,shutil,subprocess,sys,traceback
R=Path('D:/Codex/Kestrel');W=R/'work/perf-096';H=W/'oracle-harness';RAW=W/'oracle-native-raw'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def utc():return datetime.now(timezone.utc).isoformat()
assert json.loads((R/'work/guard-precorrectness-096.json').read_text(encoding='utf-8-sig'))['active_processes']==[]
assert (W/'worker-recovery-proof-v2.json').exists() and not H.exists() and not RAW.exists();H.mkdir();RAW.mkdir()
assert not (W/'oracles').exists()
p=R/'work/perf-093/oracles_093.py';b=p.read_bytes();(H/'oracles_093.py.original').write_bytes(b)
assert b.count(b"W=ROOT/'work/perf-093'")==1;b=b.replace(b"W=ROOT/'work/perf-093'",b"W=ROOT/'work/perf-096'")
b=b.replace(b"W/'binaries/baseline'",b"W/'binaries/incremental'").replace(b"W/'binaries/candidate'",b"W/'binaries/async'")
b=b.replace(b"ROOT/'work/perf-090/binaries/released016'",b"W/'binaries/released016'")
b=b.replace(b"sys.path.insert(0,str(W/'harness'))",b"sys.path.insert(0,str(W/'oracle-harness'))")
(H/'oracles_096.py').write_bytes(b)
shutil.copy2(R/'outputs/kestrel-sql/benchmarks/stress_compare.py',H/'stress_compare.py')
shutil.copy2(Path(__file__),W/Path(__file__).name)
save(W/'oracle-harness-derivation.json',{'original_oracles_sha256':sha(p),'relocated_oracles_sha256':sha(H/'oracles_096.py'),'only_work_path_and_baseline_incremental_candidate_async_aliases_changed':True,'stress_compare_sha256':sha(H/'stress_compare.py'),'new_speed_or_load_timers':False,'bridge_termination':'Original controlled owned-process termination/reopen, NOT graceful background shutdown proof; existing fresh Native Live drop tests cover joining'})
freeze={p.relative_to(W).as_posix():sha(p) for folder in [H,W/'binaries'] for p in folder.rglob('*') if p.is_file()}
freeze['run_oracles_096.py']=sha(W/'run_oracles_096.py');save(W/'oracle-freeze.json',{'files':freeze,'utc':utc()})
records=[];bridges=[];wire=[];active=[]
original_run=subprocess.run;original_popen=subprocess.Popen
def journal_run(argv,*args,**kwargs):
 assert not args and kwargs.get('capture_output');argv=list(map(str,argv));idx=len(records);stem=RAW/f'command-{idx:04d}'
 rec={'index':idx,'argv':argv,'started_utc':utc(),'stdout':stem.with_suffix('.stdout').relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix()};records.append(rec);save(W/'oracle-native-run-order.json',records)
 try:r=original_run(argv,**kwargs)
 except subprocess.TimeoutExpired as e:
  stem.with_suffix('.stdout').write_bytes(e.stdout or b'');stem.with_suffix('.stderr').write_bytes(e.stderr or b'');rec['timeout']=True;save(W/'oracle-native-run-order.json',records);raise
 assert isinstance(r.stdout,bytes) and isinstance(r.stderr,bytes)
 stem.with_suffix('.stdout').write_bytes(r.stdout);stem.with_suffix('.stderr').write_bytes(r.stderr)
 rec.update(returncode=r.returncode,completed_utc=utc(),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')));save(W/'oracle-native-run-order.json',records);return r
sys.path.insert(0,str(H));import stress_compare as sc
original_call=sc.KestrelConnection.call
def call(self,message):
 rec={'index':len(wire),'request':message}
 try:rec['result']=original_call(self,message);return rec['result']
 except BaseException as e:rec['error']=repr(e);raise
 finally:
  wire.append(rec)
  with (RAW/'wire.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,separators=(',',':'))+'\n')
def start(self,rows):
 idx=len(bridges);stem=RAW/f'bridge-{idx:03d}';self._stderr=(self.directory/'bridge.log').open('ab')
 argv=[str(self.binary),str(self.directory/'archive'),str(rows),*map(str,self.bridge_args)]
 self.process=original_popen(argv,stdout=subprocess.PIPE,stderr=self._stderr,creationflags=0x08000000);active.append(self)
 rec={'index':idx,'argv':argv,'pid':self.process.pid,'owned_Popen_process_handle':True,'started_utc':utc(),'startup_stdout':stem.with_suffix('.stdout').relative_to(W).as_posix()};bridges.append(rec);save(W/'oracle-bridge-run-order.json',bridges)
 pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);future=pool.submit(self.process.stdout.readline)
 try:line=future.result(timeout=15)
 except BaseException:self.process.kill();self.process.wait(timeout=10);pool.shutdown(wait=True);raise
 pool.shutdown(wait=True);stem.with_suffix('.stdout').write_bytes(line);info=json.loads(line);assert info['version']=='0.3.16'
 self.version=info['version'];self.bridge_info=info;host,port=info['address'].split(':');self.address=(host,int(port))
def finish(self):
 if self.process:
  self.process.terminate();self.process.wait(timeout=10);tail=self.process.stdout.read();self.process.stdout.close();self._stderr.close()
  rec=next(x for x in reversed(bridges) if x['pid']==self.process.pid and 'completed_utc' not in x)
  with (W/rec['startup_stdout']).open('ab') as f:f.write(tail)
  rec.update(completed_utc=utc(),returncode=self.process.returncode,controlled_owned_process_termination=True);save(W/'oracle-bridge-run-order.json',bridges);self.process=None
def reopen(self):finish(self);start(self,0)
sc.KestrelConnection.call=call;sc.Engine.start_bridge=start;sc.Engine.finish=finish;sc.Engine.reopen=reopen;subprocess.run=journal_run
try:
 with (RAW/'oracles.stdout').open('w',encoding='utf-8') as out,(RAW/'oracles.stderr').open('w',encoding='utf-8') as err:
  import contextlib
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):runpy.run_path(str(H/'oracles_096.py'))
 assert all(sha(W/n)==h for n,h in freeze.items());proof=json.loads((W/'oracle-proof.json').read_text());assert proof['complete']
 save(W/'oracle-journal-proof.json',{'complete':True,'native_commands':len(records),'bridge_launches':len(bridges),'wire_requests':len(wire),'native_commands_expected':56,'fresh_named_acks':320,'new_timing_or_load':False,'frozen_inputs_exact':True,'controlled_owned_termination_not_graceful_shutdown':True})
 assert len(records)==56 and len(bridges)==4 and all('completed_utc' in x for x in bridges)
 print(json.dumps({'complete':True,'native_commands':len(records),'bridges':len(bridges),'wire_requests':len(wire),'new_named_acks':320}),flush=True)
except BaseException:
 for engine in active:
  if engine.process:finish(engine)
 save(W/'oracle-failure.json',{'error':traceback.format_exc(),'native_commands':len(records),'bridges':bridges,'all_started_and_unstarted_original_checks_retained':True});raise
