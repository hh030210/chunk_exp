#!/usr/bin/env python3
"""Resolve NQ annotation URLs through Wikipedia revision IDs to stable page IDs."""
import argparse,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

def main():
 p=argparse.ArgumentParser(); p.add_argument('--queries',required=True); p.add_argument('--output',required=True); a=p.parse_args(); ids={}
 for line in open(a.queries,encoding='utf8'):
  q=json.loads(line); raw=q['raw_locator'].get('official_annotation',{}); url=raw.get('document_url',''); parsed=urllib.parse.urlparse(url); old=urllib.parse.parse_qs(parsed.query).get('oldid',[])
  if old and old[0].isdigit(): ids.setdefault(old[0],[]).append(q['query_id'])
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
 result=json.loads(path.read_text(encoding="utf8"))["revisions"] if path.exists() else {}; keys=[k for k in ids if k not in result]
 for i in range(0,len(keys),50):
  batch=keys[i:i+50]; qs=urllib.parse.urlencode({'action':'query','format':'json','formatversion':'2','prop':'revisions','rvprop':'ids','revids':'|'.join(batch)})
  req=urllib.request.Request('https://en.wikipedia.org/w/api.php?'+qs,headers={'User-Agent':'ChunkingResearch/1.0 (dataset reproducibility; anonymous; python urllib)'})
  for attempt in range(10):
   try:
    with urllib.request.urlopen(req,timeout=30) as r: obj=json.load(r)
    if 'error' in obj: raise RuntimeError(str(obj['error']))
    break
   except Exception as exc:
    if attempt==9: raise
    delay=max(30, int(exc.headers.get("Retry-After", "30"))) if isinstance(exc,urllib.error.HTTPError) and exc.code==429 else min(60,2**attempt)
    print(f"retrying in {delay}s: {exc}",flush=True); time.sleep(delay)
  for page in obj.get('query',{}).get('pages',[]):
   for revision in page.get('revisions',[]):
    rid=str(revision['revid']); result[rid]={'page_id':str(page['pageid']),'title':page['title']}
  path.write_text(json.dumps({'source':'Wikipedia MediaWiki API prop=revisions; original annotation URL oldid','revisions':result,'requested':len(ids)},ensure_ascii=False),encoding='utf8')
  print(f'{min(i+50,len(keys))}/{len(keys)} revisions processed',flush=True); time.sleep(3)
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({'source':'Wikipedia MediaWiki API prop=revisions; original annotation URL oldid','revisions':result,'requested':len(keys)},ensure_ascii=False),encoding='utf8')
 print(f'{len(result)} resolved of {len(keys)}')
if __name__=='__main__':main()
