"""Preserve publication failures/rejection and successful atomic recovery additively."""
import ast,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/source-state-078-finalization'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert load(W/'atomic-final-update.json')['remote_updated'] and load(W/'atomic-api-prepared.json')['exact_original_commit_hash_matched']
assert not (W/'incremental-publication-policy.json').exists() and not (W/'publication078.index').exists()
assert not (D/'completion-record.json').exists();files={}
for p in sorted(W.iterdir()):
    if not p.is_file() or p.name=='git-publication-check.json':continue
    q=D/p.name
    if q.exists():assert sha(q)==sha(p),('existing frozen finalization file differs',p.name)
    else:shutil.copy2(p,q)
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
    elif p.suffix=='.json':load(p)
    files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
record={'recorded_utc':datetime.now(timezone.utc).isoformat(),'initial_verified_commit':'859501c70dc62a1d48017d6a0e60c998b36ec5a5','git_push_server_failures':3,'initial_tool_text_recorded_subsequent_retries_byte_exact':True,'read_only_commit_inspection_404_preserved':True,'incremental_main_proposal_rejected_by_automatic_approval_review_and_not_executed':True,'initial_atomic_preflight_trailing_slash_404_and_exact_helper_preserved':True,'read_only_preflight_url_only_fixed':True,'API_blob_posts':83,'complete_tree_and_original_commit_hash_matched':True,'single_final_nonforced_atomic_main_update_passed':True,'no_intermediate_main_states_published':True,'all_source_binary_fixture_qualification_policy_and_archives_unchanged':True,'no_native_or_timed_rerun':True,'new_engine_release':False,'payload':files}
save(D/'completion-record.json',record)
pub=load(ROOT/'repository-publication.json');pub['source_state_078'].update(publication_recovered=True,publication_recovery_record='benchmarks/source-state-078-finalization/completion-record.json',completed_at_utc=record['recorded_utc']);save(ROOT/'repository-publication.json',pub)
publication=load(ROOT/'benchmarks/source-state-078-publication.json');publication.update(publication_recovered=True,method='complete bounded archives in private Git; exact commit published by one final API reference update',completion_record='benchmarks/source-state-078-finalization/completion-record.json');save(ROOT/'benchmarks/source-state-078-publication.json',publication)
nav=load(ROOT/'repository-navigation-audit.json');nav.update(source_state_publication_recovered=True,updated_at_utc=record['recorded_utc']);save(ROOT/'repository-navigation-audit.json',nav)
p=ROOT/'SOURCE_STATE_078.md';p.write_text(p.read_text(encoding='utf-8')+'\n## Publication recovery, after immutable packaging\n\nThree ordinary/transport-adjusted Git pushes returned GitHub internal-server errors; each authoritative branch read found unchanged prior main. The first failure is retained from tool text and subsequent retry streams are byte-exact. An incremental-main proposal was rejected by automatic approval review and was never executed: no intermediate branch states were published.\n\nThe safer recovery uploaded83 exact file objects through the Git API without changing a branch, verified the complete tree and recreated the exact original commit hash. One separately reviewed non-forced final reference update then published the complete verified commit. A read-only privacy preflight initially used a trailing-slash URL and received404 before any object creation; only that URL construction changed and its original source/error are retained. No native/benchmark rerun, candidate/source/binary/fixture/policy/archive change or engine adoption occurred.\n\n[Complete failure and recovery records](benchmarks/source-state-078-finalization/completion-record.json), [initial push](benchmarks/source-state-078-finalization/initial-push-failure.txt), [exact retry](benchmarks/source-state-078-finalization/retry-1.json), [transport retry](benchmarks/source-state-078-finalization/retry-transport.json), [unexecuted approval rejection](benchmarks/source-state-078-finalization/incremental-publication-rejection.txt), [branch-free object preparation](benchmarks/source-state-078-finalization/atomic-api-prepared.json) and [single final update](benchmarks/source-state-078-finalization/atomic-final-update.json) are additive repository evidence after the immutable ZIPs. Raw streams and exact helper sources accompany these records.\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='payload'}),flush=True)
