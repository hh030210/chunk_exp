#!/usr/bin/env python3
"""Adjacent-sentence embedding segmentation; calibrate threshold on validation only."""
import argparse, hashlib, json, os, re
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer, PreTrainedTokenizerFast

def main():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--embedding',required=True); p.add_argument('--tokenizer',required=True); p.add_argument('--output',required=True); p.add_argument('--calibrate',action='store_true'); p.add_argument('--threshold',type=float); p.add_argument('--device',default='cuda:0'); a=p.parse_args()
 if not a.calibrate and a.threshold is None: p.error('--threshold required outside calibration')
 embedtok=AutoTokenizer.from_pretrained(a.embedding,local_files_only=True,padding_side='right'); model=AutoModel.from_pretrained(a.embedding,local_files_only=True,torch_dtype=torch.float16).to(a.device).eval(); tok=PreTrainedTokenizerFast(tokenizer_file=str(Path(a.tokenizer)/'tokenizer.json'),clean_up_tokenization_spaces=False)
 def sentences(text):
  bounds=[0]+[m.end() for m in re.finditer(r'(?<=[.!?。！？])(?:\s+|(?=[^\s]))|\n\n+',text)]+[len(text)]; bounds=sorted(set(bounds)); return [(x,y) for x,y in zip(bounds,bounds[1:]) if x<y]
 def n(text): return len(tok(text,add_special_tokens=False,verbose=False)['input_ids'])
 def embeddings(seq):
  out=[]
  with torch.inference_mode():
   for start in range(0,len(seq),32):
    inp=embedtok(seq[start:start+32],padding=True,truncation=True,max_length=512,return_tensors='pt').to(a.device); hidden=model(**inp).last_hidden_state; positions=inp['attention_mask'].sum(1)-1; v=hidden[torch.arange(len(positions),device=hidden.device),positions].float(); v=torch.nn.functional.normalize(v,p=2,dim=1); out.append(v.cpu())
  return torch.cat(out) if out else torch.empty((0,1))
 scores=[]; outpath=Path(a.output); outpath.parent.mkdir(parents=True,exist_ok=True); temp=outpath.with_suffix(outpath.suffix+'.tmp'); out=None if a.calibrate else temp.open('w',encoding='utf8'); count=0
 try:
  for line in open(a.documents,encoding='utf8'):
   d=json.loads(line); text=d['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==d['source_text_sha256']; spans=sentences(text)
   if not spans: continue
   v=embeddings([text[s:e] for s,e in spans]); sim=(v[:-1]*v[1:]).sum(dim=1).tolist()
   if a.calibrate: scores.extend(sim); continue
   bounds=[0]; start=0
   for i,score in enumerate(sim):
    end=spans[i][1]; size=n(text[start:end]); nextsize=n(text[start:spans[i+1][1]])
    if (score<a.threshold and size>=256) or nextsize>512:
     if end>start: bounds.append(end); start=end
   bounds.append(len(text)); bounds=sorted(set(bounds)); fixed=[]
   for s,e in zip(bounds,bounds[1:]):
    while n(text[s:e])>1024:
     offsets=tok(text[s:e],add_special_tokens=False,return_offsets_mapping=True,verbose=False)['offset_mapping']; cut=s+offsets[511][1]
     while cut>s and n(text[s:cut])>512: cut-=1
     if cut<=s: raise ValueError('token boundary failed')
     fixed.append((s,cut)); s=cut
    if s<e: fixed.append((s,e))
   for i,(s,e) in enumerate(fixed):
    row={'dataset':d['dataset'],'baseline_id':'B2_semantic','source_doc_id':d['source_doc_id'],'chunk_id':f"{d['source_doc_id']}::chunk_{i:05d}",'chunk_index':i,'text':text[s:e],'start_char':s,'end_char':e,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':d['source_text_sha256'],'token_count':n(text[s:e]),'source_paragraph_ids':[x['id'] for x in d.get('paragraphs',[]) if x['start_char']<e and x['end_char']>s]}; out.write(json.dumps(row,ensure_ascii=False)+'\n'); count+=1
 finally:
  if out: out.close()
 if a.calibrate:
  if not scores: raise ValueError('no validation sentence pairs')
  temp.write_text(json.dumps({'threshold':float(np.quantile(scores,.25)),'quantile':.25,'sentence_pairs':len(scores),'validation_documents':a.documents},ensure_ascii=False)+'\n')
 os.replace(temp,outpath); print(json.dumps({'output':str(outpath),'chunks':count,'pairs':len(scores)}))
if __name__=='__main__': main()
