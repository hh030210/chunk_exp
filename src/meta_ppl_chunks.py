#!/usr/bin/env python3
"""Meta-Chunking PPL minima with bounded-context scoring and source-preserving spans."""
import argparse, hashlib, json, os, re
from pathlib import Path
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--model',required=True); p.add_argument('--output',required=True); p.add_argument('--threshold',type=float,default=0.0); p.add_argument('--device',default='cuda:0'); a=p.parse_args()
 tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True); model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.float16,local_files_only=True).to(a.device).eval()
 def size(text): return len(tok(text,add_special_tokens=False,verbose=False)['input_ids'])
 def split(text):
  b=sorted(set([0]+[m.end() for m in re.finditer(r'(?<=[.!?。！？])(?:\s+|(?=[^\s]))|\n\n+',text)]+[len(text)])); result=[]
  for s,e in zip(b,b[1:]):
   while size(text[s:e])>512:
    z=tok(text[s:e],add_special_tokens=False,return_offsets_mapping=True,verbose=False)['offset_mapping']; cut=s+z[511][1]
    while cut>s and size(text[s:cut])>512: cut-=1
    if cut<=s: raise ValueError('no token boundary')
    result.append((s,cut)); s=cut
   if s<e: result.append((s,e))
  return result
 def score(text,s,e):
  # Score the sentence with up to 512 preceding tokens as causal context.
  prior=tok(text[:s],add_special_tokens=False,verbose=False)['input_ids'][-512:]; current=tok(text[s:e],add_special_tokens=False,verbose=False)['input_ids']
  ids=prior+current
  if len(ids)<2: return 0.0
  t=torch.tensor([ids],device=a.device)
  with torch.inference_mode():
   logits=model(t,use_cache=False).logits[0,:-1].float(); labels=t[0,1:]; loss=F.cross_entropy(logits,labels,reduction='none'); start=max(len(prior)-1,0); return float(loss[start:].mean().item())
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); total=0
 with open(a.documents,encoding='utf8') as source, tmp.open('w',encoding='utf8') as out:
  for line in source:
   d=json.loads(line); text=d['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==d['source_text_sha256']; spans=split(text); scores=[score(text,s,e) for s,e in spans]; cut=[0]
   for i in range(1,len(scores)-1):
    if scores[i]<scores[i-1] and scores[i]<=scores[i+1] and max(scores[i-1]-scores[i],scores[i+1]-scores[i])>=a.threshold: cut.append(spans[i][1])
   cut.append(len(text)); cut=sorted(set(cut)); chunks=[]
   for s,e in zip(cut,cut[1:]):
    while size(text[s:e])>1024:
     offsets=tok(text[s:e],add_special_tokens=False,return_offsets_mapping=True,verbose=False)['offset_mapping']; end=s+offsets[511][1]
     while end>s and size(text[s:end])>512: end-=1
     if end<=s: raise ValueError('no token boundary')
     chunks.append((s,end)); s=end
    if s<e:
     if chunks and size(text[chunks[-1][0]:e])<=512: chunks[-1]=(chunks[-1][0],e)
     else: chunks.append((s,e))
   for i,(s,e) in enumerate(chunks):
    row={'dataset':d['dataset'],'baseline_id':'B3_meta_chunking','source_doc_id':d['source_doc_id'],'chunk_id':f"{d['source_doc_id']}::chunk_{i:05d}",'chunk_index':i,'text':text[s:e],'start_char':s,'end_char':e,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':d['source_text_sha256'],'token_count':size(text[s:e]),'source_paragraph_ids':[x['id'] for x in d.get('paragraphs',[]) if x['start_char']<e and x['end_char']>s]}; out.write(json.dumps(row,ensure_ascii=False)+'\n'); total+=1
 os.replace(tmp,path); print(json.dumps({'output':str(path),'chunks':total}))
if __name__=='__main__': main()
