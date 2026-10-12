"""New132 protocol: one owned idle metadata worker, unchanged safety/numerical gates."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
assert not (R/'perf-132').exists() and not (R/'run_phase_compare_132.py').exists()
def renamed(s):return s.replace('perf-130','perf-132').replace('_130','_132').replace('phase130','phase132').replace('-130','-132').replace('candidate127','candidate131').replace('phase127','phase131')
run=renamed((R/'run_phase_compare_130.py').read_text(encoding='utf-8'))
run=run.replace('import ctypes,hashlib,json,os,subprocess,time,traceback','import ctypes,hashlib,json,os,subprocess,time,traceback,queue,threading')
a=run.index('def activity_check(');b=run.index('\npolicy=load(',a)
api='''class SafetyWorker:
    def __init__(self):
        times=[wintypes.FILETIME() for _ in range(4)]
        assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
        self.owner_creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)
        self.child=subprocess.Popen(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'activity_worker_132.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(self.owner_creation)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8-sig',bufsize=1,creationflags=0x08000000)
        self.identity=identity(self.child);self.messages=queue.Queue();self.errors=[];self.number=0
        assert self.identity['affinity_mask']==256
        def reader():
            for line in self.child.stdout:
                self.messages.put(line)
            self.messages.put(None)
        def errors():
            for line in self.child.stderr:
                assert sum(map(len,self.errors))<1000000,'Metadata stderr cap exceeded'
                self.errors.append(line)
        self.output_thread=threading.Thread(target=reader,daemon=True);self.error_thread=threading.Thread(target=errors,daemon=True)
        self.output_thread.start();self.error_thread.start()
        with (W/'worker-sessions.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps({'utc':utc(),'owner_pid':os.getpid(),'owner_creation_filetime':self.owner_creation,'worker_identity':self.identity,'owned_stdin_stdout_only':True})+'\\n')
    def check(self,place,index=None):
        assert self.child.poll() is None,('Metadata worker exited',self.child.returncode,self.errors)
        started=utc();number=self.number;self.number+=1
        self.child.stdin.write(json.dumps({'operation':'check','request_id':number,'place':place,'index':index})+'\\n');self.child.stdin.flush()
        line=self.messages.get(timeout=20)
        assert line is not None and len(line)<1000000,('Metadata worker EOF/response cap',self.errors)
        response=json.loads(line)
        assert response['request_id']==number and response['place']==place and response['index']==index and response['no_probe_during_native_case']
        row={'started_utc':started,'utc':utc(),'place':place,'index':index,'exit':response['exit'],'stdout':'\\n'.join(json.dumps(m) for m in response['messages']),'stderr':'','worker_identity':self.identity,'request_id':number}
        with (W/'activity-checks.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps(row,separators=(',',':'))+'\\n')
        messages=response['messages'];assert messages and messages[0]['verified_controller_pid']==os.getpid() and messages[0]['verified_controller_creation_filetime']==self.owner_creation
        assert messages[0]['persistent_worker_pid']==self.identity['pid'] and messages[0]['worker_blocks_on_input_between_requests']
        if row['exit']==0:assert len(messages)==2 and messages[0]['no_other_task_work'] and messages[1]['no_visible_build_jobs']
        elif row['exit']==3:assert not messages[0]['no_other_task_work'] or (len(messages)==2 and not messages[1]['no_visible_build_jobs'])
        else:raise AssertionError(('Safety protocol error',row))
        return row
    def stop(self):
        forced=False
        if self.child.poll() is None:
            self.child.stdin.write(json.dumps({'operation':'stop'})+'\\n');self.child.stdin.flush();self.child.stdin.close()
            try:self.child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.child.kill();self.child.wait(timeout=10);forced=True
        self.output_thread.join(timeout=2);self.error_thread.join(timeout=2)
        proof={'utc':utc(),'actual_exit':self.child.returncode,'actual_wait_completed':self.child.poll() is not None,'forced_owned_worker_kill':forced,'worker_identity':self.identity,'requests':self.number,'stderr':''.join(self.errors)}
        with (W/'worker-exits.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps(proof)+'\\n')
        return proof
worker=None
def activity_check(place,index=None):
    assert worker is not None
    return worker.check(place,index)
'''
run=run[:a]+api+run[b:]
run=run.replace("'check_round_activity_132.ps1'","'activity_worker_132.ps1'")
run=run.replace("    assert mask(own)[0]==256\n", "    assert mask(own)[0]==256\n    worker=SafetyWorker()\n",1)
run=run.replace("    assert len(completed)==216\n", "    assert len(completed)==216\n    worker_exit=worker.stop();worker=None\n    assert worker_exit['actual_exit']==0 and worker_exit['actual_wait_completed'] and not worker_exit['forced_owned_worker_kill']\n",1)
run=run.replace("'A_B_identical_supported016_and_C_exact_phase131':True", "'A_B_identical_supported016_and_C_exact_phase131':True,'metadata_worker_actual_exit':worker_exit['actual_exit']")
run=run.replace("finally:\n    assert k.SetProcessAffinityMask", "finally:\n    if worker is not None:\n        worker.stop();worker=None\n    assert k.SetProcessAffinityMask")
ast.parse(run);(R/'run_phase_compare_132.py').write_text(run,encoding='utf-8',newline='\n')
audit=renamed((R/'audit_phase_compare_130.py').read_text(encoding='utf-8'))
needle="assert load(W/'cooldown-proof.json')['continuous_quiet_seconds']>=120"
audit=audit.replace(needle,needle+'''
assert load(W/'cohort-completion.json')['metadata_worker_actual_exit']==0
worker_exits=[json.loads(line) for line in (W/'worker-exits.jsonl').read_text().splitlines()]
assert all(row['actual_exit']==0 and row['actual_wait_completed'] and not row['forced_owned_worker_kill'] for row in worker_exits)
''')
needle="    result=load(W/case['stdout']);assert result['component_only'] and result['all_checks_passed']"
audit=audit.replace(needle,'''    before_probe=next(p for p in case_probes if p['place']=='before_case' and p['index']==spec['index'])
    after_probe=next(p for p in case_probes if p['place']=='after_case' and p['index']==spec['index'])
    assert before_probe['utc']<=case['started_utc']<=case['completed_utc']<=after_probe['started_utc']<=after_probe['utc']
    assert before_probe['worker_identity']==after_probe['worker_identity'] and before_probe['worker_identity']['affinity_mask']==256
'''+needle)
ast.parse(audit);(R/'audit_phase_compare_132.py').write_text(audit,encoding='utf-8',newline='\n')
prepare=renamed((R/'prepare_phase_compare_130.py').read_text(encoding='utf-8'))
prepare=prepare.replace("assert head == '6870bb7d9dab6f81e306957f6be2d1a36a70f37f'", "assert head == load(R/'phase131-publication-proof.json')['private_main']")
prepare=prepare.replace("load(R/'phase129-storage-cleanup-proof.json')['completed129_prefix_stores_closed'] and not (R/'perf-129').exists()", "load(R/'phase131-storage-cleanup-proof.json')['completed131_test_stores_and_build_outputs_closed'] and not (R/'perf-131').exists()")
prepare=prepare.replace('compaction-kit-127','compaction-kit-131').replace("load(R/'phase127-storage-cleanup-proof.json')['completed127_test_stores_and_build_outputs_closed']", "load(R/'phase131-storage-cleanup-proof.json')['completed131_test_stores_and_build_outputs_closed']")
prepare=prepare.replace("'trial':130", "'trial':132").replace("'candidate_tests':336", "'candidate_tests':340")
prepare=prepare.replace('This tests the combined127 implementation versus016, not isolated caller effect versus122.', 'This tests combined131 versus016, not the isolated131 effect versus127; ordered workspace is only constructed after disorder.')
prepare=prepare.replace("'new_protocol':'Same engine/input multiset/RNG seed as128/129; corrected log paths and log-only status polling.129 complete seven-case failed prefix independently audited and saved,209 unstarted; no selected retiming. Continuous clear120-second interval after all preparation, reset on busy observations; per-case pre/post safety probes outside compaction timing. No workload or numerical gate changes.'", "'new_protocol':'One owned persistent PowerShell metadata worker blocks on stdin between requests; identical reset/task/supervisor/global-build checks before/after every native case and during120-second continuous quiet window. Worker does no probe during native lifetime and must actually exit0 after all cases. No engine/numerical gate/input reduction; removed repeated PowerShell startup is outside compaction clock. Bounded nonsecret blocker reasons retained; no command-line dumping.'")
prepare=prepare.replace("'check_round_activity_132.ps1'", "'activity_worker_132.ps1'").replace("'prepare_continuation_132.py'", "'derive_phase_compare_132.py'")
ast.parse(prepare);(R/'prepare_phase_compare_132.py').write_text(prepare,encoding='utf-8',newline='\n')
print('New132 protocol sources prepared; no policy declared, fixture copied or timer started')
