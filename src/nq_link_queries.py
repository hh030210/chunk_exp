#!/usr/bin/env python3
"""Link NQ annotation old revision IDs to page IDs verified in the fixed snapshot."""
import argparse,json,os,urllib.parse

def main():
 p=argparse.ArgumentParser(); p.add_argument('--queries',required=True); p.add_argument('--revision-map',required=True); p.add_argument('--documents',required=True); a=p.parse_args(); mapping=json.load(open(a.revision_map,encoding='utf8'))['revisions']; rows=[json.loads(x) for x in open(a.queries,encoding='utf8')]; ids=set(); revision_by_query={}
 for r in rows:
  url=r['raw_locator'].get('official_annotation',{}).get('document_url',''); revision=urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('oldid',[None])[0]; revision_by_query[r['query_id']]=revision
  if revision in mapping: ids.add(str(mapping[revision]['page_id']))
 found=set()
 for line in open(a.documents,encoding='utf8'):
  d=json.loads(line); page=str(d['source_doc_id'])
  if page in ids: found.add(page)
  if len(found)==len(ids): break
 tmp=a.queries+'.tmp'; linked=0
 with open(tmp,'w',encoding='utf8') as f:
  for r in rows:
   revision=revision_by_query[r['query_id']]; page=str(mapping[revision]['page_id']) if revision in mapping else None
   r['source_doc_ids']=[page] if page in found else []; linked+=bool(r['source_doc_ids']); f.write(json.dumps(r,ensure_ascii=False)+'\n')
 os.replace(tmp,a.queries); print(json.dumps({'queries':len(rows),'linked':linked,'requested_unique_pageids':len(ids),'found_pageids':len(found)}))
if __name__=='__main__': main()
