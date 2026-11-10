#!/usr/bin/env python3
"""Prepare author's line-oriented corpus and query records, using exact text links only."""
import argparse, hashlib, json
from pathlib import Path

def sha(s): return hashlib.sha256(s.encode('utf8')).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--corpus',required=True); p.add_argument('--queries',required=True); p.add_argument('--output',required=True); a=p.parse_args(); root=Path(a.corpus); out=Path(a.output); out.mkdir(parents=True,exist_ok=True); index={}; count=0; empty=[]
 with (out/'documents.jsonl').open('w',encoding='utf8') as f:
  for path in sorted(root.iterdir()):
   if not path.is_file(): continue
   with path.open(encoding='utf8',newline='') as src:
    for i,line in enumerate(src):
     text=line.removesuffix('\n').removesuffix('\r'); docid=f'CRUD:{path.name}:{i}'; h=sha(text)
     index.setdefault(h,[]).append(docid)
     if not text: empty.append(docid)
     f.write(json.dumps({'dataset':'CRUD-RAG','source_doc_id':docid,'raw_locator':{'relative_path':path.name,'line_index':i},'title':None,'canonical_url':None,'source_text_sha256':h,'normalized_text':text},ensure_ascii=False)+'\n'); count+=1
 data=json.loads(Path(a.queries).read_text(encoding='utf8')); totals={}; matched=0
 with (out/'queries_eval.jsonl').open('w',encoding='utf8') as f:
  for key in ['questanswer_1doc','questanswer_2docs']:
   totals[key]=len(data[key])
   for i,record in enumerate(data[key]):
    q=record['questions']; ids=[]
    for field in ['news1','news2']:
     if field in record: ids.extend(index.get(sha(record[field]),[]))
    ids=list(dict.fromkeys(ids)); matched+=bool(ids)
    f.write(json.dumps({'dataset':'CRUD-RAG','query_split':'author_eval_1doc' if key.endswith('1doc') else 'author_eval_2docs','query_id':f'CRUD:{key}:{i}','query_text':q,'raw_locator':{'task_key':key,'raw_array_index':i},'source_doc_ids':ids,'query_text_sha256':sha(q)},ensure_ascii=False)+'\n')
 print(json.dumps({'documents':count,'queries':totals,'queries_with_exact_text_match':matched,'empty_documents':empty},ensure_ascii=False))
if __name__=='__main__': main()
