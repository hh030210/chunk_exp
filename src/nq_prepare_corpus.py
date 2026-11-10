#!/usr/bin/env python3
"""Convert the fixed KILT Wikipedia snapshot into source-preserving documents."""
import argparse,hashlib,json,os
from pathlib import Path

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args(); src=Path(a.input); dest=Path(a.output); dest.parent.mkdir(parents=True,exist_ok=True); tmp=dest.with_suffix(dest.suffix+'.tmp'); n=0
 with src.open(encoding='utf8') as source,tmp.open('w',encoding='utf8') as output:
  for i,line in enumerate(source):
   x=json.loads(line); page_id=str(x['wikipedia_id']); text='\n\n'.join(x['text']); title=x['wikipedia_title']; digest=hashlib.sha256(text.encode()).hexdigest(); d={'dataset':'NQ','source_doc_id':page_id,'raw_locator':{'file':src.name,'line_index':i,'wikipedia_id':page_id},'title':title,'canonical_url':None,'source_text_sha256':digest,'normalized_text':text}; output.write(json.dumps(d,ensure_ascii=False)+'\n'); n+=1
 os.replace(tmp,dest); print(json.dumps({'documents':n,'output':str(dest)}))
if __name__=='__main__':main()
