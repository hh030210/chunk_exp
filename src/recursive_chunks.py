#!/usr/bin/env python3
"""Recursively split canonical text at section/paragraph, sentence and token boundaries."""
import argparse, hashlib, json, os, re
from pathlib import Path
from transformers import PreTrainedTokenizerFast

def main():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--tokenizer',required=True); p.add_argument('--output',required=True); p.add_argument('--target',type=int,default=512); p.add_argument('--limit',type=int,default=1024); a=p.parse_args()
 tok=PreTrainedTokenizerFast(tokenizer_file=str(Path(a.tokenizer)/'tokenizer.json'),clean_up_tokenization_spaces=False)
 def n(s): return len(tok(s,add_special_tokens=False,verbose=False)['input_ids'])
 def pieces(text,start,end):
  if n(text[start:end])<=a.target: return [(start,end)]
  boundaries=[start]+[start+m.end() for m in re.finditer(r'\n\n+',text[start:end])]+[end]
  boundaries=sorted(set(boundaries))
  if len(boundaries)<=2: boundaries=[start]+[start+m.end() for m in re.finditer(r'(?<=[.!?。！？])\s+',text[start:end])]+[end]; boundaries=sorted(set(boundaries))
  if len(boundaries)>2:
   result=[]
   for x,y in zip(boundaries,boundaries[1:]):
    if x<y: result.extend(pieces(text,x,y))
   return result
  result=[]
  while start<end:
   enc=tok(text[start:end],add_special_tokens=False,return_offsets_mapping=True,verbose=False)['offset_mapping']
   cut=end if len(enc)<=a.target else start+enc[a.target-1][1]
   while cut>start and n(text[start:cut])>a.target: cut-=1
   if cut<=start: raise ValueError('no token boundary')
   result.append((start,cut)); start=cut
  return result
 outpath=Path(a.output); outpath.parent.mkdir(parents=True,exist_ok=True); tmp=outpath.with_suffix(outpath.suffix+'.tmp'); total=0
 with open(a.documents,encoding='utf8') as f, tmp.open('w',encoding='utf8') as out:
  for line in f:
   doc=json.loads(line); text=doc['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==doc['source_text_sha256']
   segments=pieces(text,0,len(text)) if text else []; merged=[]
   for s,e in segments:
    if merged and n(text[merged[-1][0]:e])<=a.target: merged[-1]=(merged[-1][0],e)
    else: merged.append((s,e))
   for i,(s,e) in enumerate(merged):
    part=text[s:e]; count=n(part); assert count<=a.limit
    row={'dataset':doc['dataset'],'baseline_id':'B1_recursive','source_doc_id':doc['source_doc_id'],'chunk_id':f"{doc['source_doc_id']}::chunk_{i:05d}",'chunk_index':i,'text':part,'start_char':s,'end_char':e,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':doc['source_text_sha256'],'token_count':count,'source_paragraph_ids':[x['id'] for x in doc.get('paragraphs',[]) if x['start_char']<e and x['end_char']>s]}
    out.write(json.dumps(row,ensure_ascii=False)+'\n'); total+=1
 os.replace(tmp,outpath); print(json.dumps({'chunks':total,'output':str(outpath)}))
if __name__=='__main__': main()
