#!/usr/bin/env python3
"""Join NQ-open records to original-format annotations by exact question and answer set."""
import argparse, collections, hashlib, html, json
from pathlib import Path
import pyarrow.parquet as pq
from bs4 import BeautifulSoup

def main():
 p=argparse.ArgumentParser(); p.add_argument('--queries',required=True); p.add_argument('--annotations',required=True); p.add_argument('--output',required=True); a=p.parse_args()
 queries=[json.loads(x) for x in open(a.queries,encoding='utf8')]; candidates=collections.defaultdict(list)
 for i,q in enumerate(queries): candidates[q['question']].append(i)
 matches=collections.defaultdict(list)
 for file in sorted(Path(a.annotations).glob('*.parquet')):
  parquet=pq.ParquetFile(file); row=0
  for batch in parquet.iter_batches(batch_size=128,columns=['id','question','document','annotations']):
   for r in batch.to_pylist():
    q=r['question']['text']; possible=candidates.get(q,[])
    if possible:
     doc=r['document']; raw=doc['html'].encode('utf8'); answers=set()
     for group in r['annotations']['short_answers']:
      for st,et,sb,eb in zip(group['start_token'],group['end_token'],group['start_byte'],group['end_byte']):
       if et-st<=5:
        answers.add(BeautifulSoup(raw[sb:eb],'lxml').text)
     for idx in possible:
      if answers==set(queries[idx]['answer']): matches[idx].append({'example_id':r['id'],'document_url':html.unescape(doc['url']),'parquet_file':file.name,'row_index':row})
    row+=1
 print('matches:',sum(len(v)==1 for v in matches.values()),'ambiguous:',sum(len(v)>1 for v in matches.values()),'total:',len(queries),flush=True)
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf8') as out:
  for i,q in enumerate(queries):
   hits=matches[i]; raw={'split':'NQ-open.dev','line_index':i};
   if len(hits)==1: raw['official_annotation']=hits[0]
   record={'dataset':'NQ','query_split':'NQ-open.dev','query_id':str(hits[0]['example_id']) if len(hits)==1 else f'NQ:dev:{i}','query_text':q['question'],'raw_locator':raw,'source_doc_ids':[],'query_text_sha256':hashlib.sha256(q['question'].encode()).hexdigest(),'annotation_match_count':len(hits)}
   out.write(json.dumps(record,ensure_ascii=False)+'\n')
if __name__=='__main__': main()
