#!/usr/bin/env python3
"""Fixed-token contiguous chunks with recoverable Unicode character spans."""
import argparse, hashlib, json, os
from pathlib import Path
from transformers import PreTrainedTokenizerFast

def run():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--tokenizer',required=True); p.add_argument('--size',type=int,choices=[256,512,1024],required=True); p.add_argument('--output',required=True); args=p.parse_args()
 tok=PreTrainedTokenizerFast(tokenizer_file=str(Path(args.tokenizer)/'tokenizer.json'))
 output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True); temp=output.with_suffix(output.suffix+'.tmp'); total=0
 with open(args.documents,encoding='utf8') as source, temp.open('w',encoding='utf8') as out:
  for line in source:
   doc=json.loads(line); text=doc['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==doc['source_text_sha256']; pos=0; index=0
   while pos < len(text):
    encoding=tok(text[pos:],add_special_tokens=False,return_offsets_mapping=True,truncation=False,verbose=False); offsets=encoding['offset_mapping']
    if not offsets: end=len(text)
    elif len(offsets)<=args.size: end=len(text)
    else:
     end=pos+offsets[args.size-1][1]
     if end<=pos: raise ValueError('Tokenizer made no progress')
     while end>pos and len(tok(text[pos:end],add_special_tokens=False)['input_ids'])>args.size: end-=1
     if end<=pos: raise ValueError('Could not find legal boundary')
    part=text[pos:end]; count=len(tok(part,add_special_tokens=False)['input_ids']); assert count<=args.size
    row={'dataset':doc['dataset'],'baseline_id':f'B0_fixed_{args.size}_o0','source_doc_id':doc['source_doc_id'],'chunk_id':f"{doc['source_doc_id']}::chunk_{index:05d}",'chunk_index':index,'text':part,'start_char':pos,'end_char':end,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':doc['source_text_sha256'],'token_count':count,'source_paragraph_ids':[p['id'] for p in doc.get('paragraphs',[]) if p['start_char']<end and p['end_char']>pos]}
    out.write(json.dumps(row,ensure_ascii=False)+'\n'); index+=1; total+=1; pos=end
 os.replace(temp,output); print(json.dumps({'output':str(output),'chunks':total}))
if __name__=='__main__': run()
