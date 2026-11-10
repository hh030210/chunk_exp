#!/usr/bin/env python3
"""Prepare QASPER official test questions and canonical full-text documents."""
import argparse, hashlib, json
from pathlib import Path

def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--input', required=True); p.add_argument('--output',required=True); p.add_argument('--split',choices=['train','validation','test'],default='test'); a=p.parse_args()
 source=Path(a.input); dest=Path(a.output); dest.mkdir(parents=True,exist_ok=True)
 raw=json.loads(source.read_text(encoding='utf8')); seen=set(); nq=0
 with (dest/'documents.jsonl').open('w',encoding='utf8') as docs, (dest/'queries_eval.jsonl').open('w',encoding='utf8') as queries:
  for paper_id, paper in raw.items():
   pieces=[]; paragraphs=[]; offset=0
   for si, section in enumerate(paper['full_text']):
    name=section.get('section_name')
    if name: pieces.append(str(name)); offset+=len(str(name))+2
    for pi, text in enumerate(section['paragraphs']):
     if not isinstance(text,str): raise ValueError(f'{paper_id}: non-string paragraph')
     start=offset; pieces.append(text); offset+=len(text)+2
     paragraphs.append({'id':f'section_{si}:paragraph_{pi}', 'start_char':start,'end_char':start+len(text)})
   text='\n\n'.join(pieces)
   doc={'dataset':'QASPER','source_doc_id':paper_id,'raw_locator':{'paper_id':paper_id},'title':paper['title'],'canonical_url':None,'source_text_sha256':digest(text),'normalized_text':text,'paragraphs':paragraphs}
   docs.write(json.dumps(doc,ensure_ascii=False)+'\n')
   for q in paper['qas']:
    qid=paper_id+':'+q['question_id']
    if qid in seen: raise ValueError('duplicate query ID '+qid)
    seen.add(qid); query=q['question']
    queries.write(json.dumps({'dataset':'QASPER','query_split':a.split,'query_id':qid,'query_text':query,'raw_locator':{'paper_id':paper_id,'question_id':q['question_id']},'source_doc_ids':[paper_id],'query_text_sha256':digest(query)},ensure_ascii=False)+'\n'); nq+=1
 print(json.dumps({'documents':len(raw),'queries':nq,'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}))
if __name__=='__main__': main()
