#!/usr/bin/env python3
"""PIC: document-summary cosine scores and document mean threshold."""
import argparse, hashlib, json, os, re
from pathlib import Path
import torch
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

def main():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--model',required=True); p.add_argument('--embedding',required=True); p.add_argument('--output',required=True); p.add_argument('--device',default='cuda:0'); a=p.parse_args()
 tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True); lm=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.float16,local_files_only=True).to(a.device).eval()
 etok=AutoTokenizer.from_pretrained(a.embedding,local_files_only=True,padding_side='right'); em=AutoModel.from_pretrained(a.embedding,torch_dtype=torch.float16,local_files_only=True).to(a.device).eval()
 def n(s): return len(tok(s,add_special_tokens=False,verbose=False)['input_ids'])
 def summary(text):
  prompt='Summarize the main topics and key information of the following document in at most 256 tokens.\n\n'+text
  templated=tok.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  inp=tok(templated,return_tensors='pt').to(a.device)
  with torch.inference_mode(): out=lm.generate(**inp,max_new_tokens=256,do_sample=False)
  return tok.decode(out[0,inp['input_ids'].shape[1]:],skip_special_tokens=True)
 def summarize_full(text):
  # Hierarchical summaries cover all of long documents; 4096-token blocks, then recursively summarize.
  ids=tok(text,add_special_tokens=False,verbose=False)['input_ids']; levels=0
  while len(ids)>4096:
   summaries=[summary(tok.decode(ids[i:i+4096],skip_special_tokens=False)) for i in range(0,len(ids),4096)]
   reduced='\n'.join(summaries); new=tok(reduced,add_special_tokens=False,verbose=False)['input_ids']; levels+=1
   if len(new)>=len(ids): raise ValueError('summary reduction failed')
   ids=new
  return summary(tok.decode(ids,skip_special_tokens=False)),levels
 def embed(seq):
  result=[]
  with torch.inference_mode():
   for i in range(0,len(seq),24):
    data=etok(seq[i:i+24],padding=True,truncation=True,max_length=512,return_tensors='pt').to(a.device); hidden=em(**data).last_hidden_state; ind=data['attention_mask'].sum(1)-1; vec=hidden[torch.arange(len(ind),device=hidden.device),ind].float(); result.append(torch.nn.functional.normalize(vec,p=2,dim=1).cpu())
  return torch.cat(result)
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); side=path.with_suffix(path.suffix+'.summary.jsonl.tmp'); total=0
 with open(a.documents,encoding='utf8') as source,tmp.open('w',encoding='utf8') as out,side.open('w',encoding='utf8') as audit:
  for line in source:
   d=json.loads(line); text=d['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==d['source_text_sha256']
   if not text: audit.write(json.dumps({'source_doc_id':d['source_doc_id'],'empty':True})+'\n'); continue
   summ,levels=summarize_full(text); bounds=sorted(set([0]+[m.end() for m in re.finditer(r'(?<=[.!?。！？])(?:\s+|(?=[^\s]))|\n\n+',text)]+[len(text)])); spans=list(zip(bounds,bounds[1:])); v=embed([summ]+[text[s:e] for s,e in spans]); sims=(v[1:]*v[0]).sum(dim=1); threshold=float(sims.mean()); cuts=[0]
   for i in range(1,len(spans)):
    if (float(sims[i-1])>=threshold)!=(float(sims[i])>=threshold): cuts.append(spans[i][0])
   cuts.append(len(text)); chunks=[]
   for s,e in zip(cuts,cuts[1:]):
    while n(text[s:e])>1024:
     offs=tok(text[s:e],add_special_tokens=False,return_offsets_mapping=True,verbose=False)['offset_mapping']; end=s+offs[511][1]
     while end>s and n(text[s:end])>512: end-=1
     if end<=s: raise ValueError('no token boundary')
     chunks.append((s,end)); s=end
    if s<e:
     if chunks and n(text[chunks[-1][0]:e])<=512: chunks[-1]=(chunks[-1][0],e)
     else: chunks.append((s,e))
   audit.write(json.dumps({'source_doc_id':d['source_doc_id'],'summary':summ,'hierarchical_levels':levels,'threshold_mean':threshold},ensure_ascii=False)+'\n')
   for i,(s,e) in enumerate(chunks):
    row={'dataset':d['dataset'],'baseline_id':'B4_PIC','source_doc_id':d['source_doc_id'],'chunk_id':f"{d['source_doc_id']}::chunk_{i:05d}",'chunk_index':i,'text':text[s:e],'start_char':s,'end_char':e,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':d['source_text_sha256'],'token_count':n(text[s:e]),'source_paragraph_ids':[x['id'] for x in d.get('paragraphs',[]) if x['start_char']<e and x['end_char']>s]}; out.write(json.dumps(row,ensure_ascii=False)+'\n'); total+=1
 os.replace(tmp,path); os.replace(side,path.with_suffix(path.suffix+'.summary.jsonl')); print(json.dumps({'output':str(path),'chunks':total}))
if __name__=='__main__': main()
