"""Pure independent validation of post-join publication aggregates and cold SQL."""
import bisect,math,sqlite3
STAGES=['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']
BOUNDS=[.1,1,5,20,100,500,1000]
def check_profile(result):
 p=result['publication_profile_after_writer_join'];stats=result['ingest'];n=len(result['raw_acknowledgements'])
 assert p['attempts']==p['completed']==result['cold_stats']['generation']>0
 assert p['catalog_checkpoints']+p['catalog_deltas']==p['completed'] and p['catalog_bytes_published']>0
 final_compactions=p['completed']-stats['durable_group_commits']
 assert stats['compactions']<=final_compactions<=stats['compactions']+1
 values={};total=0
 for name in STAGES+['replay_validation']:
  stage=p[name];count=stage['count'];hist=stage['histogram'];t=stage['total_ms'];mx=stage['max_ms']
  assert isinstance(count,int) and count>=0 and len(hist)==8 and all(isinstance(v,int) and v>=0 for v in hist) and sum(hist)==count
  assert all(isinstance(v,(float,int)) and math.isfinite(v) and v>=0 for v in [t,mx])
  if count:
   tolerance=max(1e-7,t*1e-10)
   assert mx<=t+tolerance and t<=count*mx+tolerance
   assert max(i for i,v in enumerate(hist) if v)==bisect.bisect_left(BOUNDS,mx)
   lower=[0]+BOUNDS;upper=BOUNDS+[mx]
   assert sum(v*l for v,l in zip(hist,lower))<=t+tolerance
   assert t<=sum(v*min(u,mx) for v,u in zip(hist,upper))+tolerance
  else:assert t==mx==0 and hist==[0]*8
  if name in STAGES:
   assert count==p['attempts'] and t>0
   values['stage/'+name+'/ms_per_ACK']=t/n;total+=t
 values['stage/total/ms_per_ACK']=total/n
 return values,{'post_join_completed':p['completed'],'durable_groups':stats['durable_group_commits'],'post_join_compactions':final_compactions,'sampled_prejoin_compactions':stats['compactions'],'publication_stage_total_ms':total,'catalog_bytes_logical':p['catalog_bytes_published'],'profile':p}
def check_sql(result,rows,cache,key):
 if key not in cache:
  with sqlite3.connect(':memory:') as db:
   db.execute('CREATE TABLE events(ts INTEGER,value INTEGER,device INTEGER)');db.executemany('INSERT INTO events VALUES(?,?,?)',rows)
   cache[key]=[list(r) for r in db.execute('SELECT COUNT(*), SUM(value) FROM events').fetchall()]
 assert result['cold_query_rows']==cache[key]
