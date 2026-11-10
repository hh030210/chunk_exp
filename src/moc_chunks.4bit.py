#!/usr/bin/env python3
"""MoC router and four released experts; preserve source spans and log alignment failures."""
import argparse, hashlib, json, os, re
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from rapidfuzz.fuzz import partial_ratio_alignment

ROUTER='''你是一名文本分析方面的专家，给定一篇文章，你需要根据文章的内容判断其适合的分块粒度。分块粒度分为4个类别，具体分类如下：
0: 0-120个字符
1: 120-150个字符
2: 150-180个字符
3: 大于180个字符

输出要求：根据文章内容，从上述0~3之间选择一个合适的分块粒度。

文章内容：{}

文章的分块粒度类别为：'''
EXPERT='''这是一个文本分块任务，你是一名文本分割方面的专家，负责将给定的文本分割成文本块。你必须遵守以下四个条件：
1. 将内容相关的若干个连续句子组合成文本块，使得每个文本块都具有完整的逻辑表达。
2. 避免文本块过短，在识别内容转换与分块长度之间取得良好平衡。
3. 输出的分块结果是一个列表格式，其中的每个元素表示文档中的一个文本块。
4. 其中输出的每个文本块由文本块开头和结尾几个字符组成，中间内容由“[MASK]”来代替，输出格式如下：
[
    "文本块1的开头几个字符[MASK]文本块1的结尾几个字符",
    ......
]

如果你理解，请将以下文本分割成文本块，并通过上述要求输出列表格式。

文档内容：{}\n\n分割好的文本块的列表格式输出：'''

def main():
 p=argparse.ArgumentParser(); p.add_argument('--documents',required=True); p.add_argument('--models',required=True); p.add_argument('--tokenizer',required=True); p.add_argument('--output',required=True); p.add_argument('--language',choices=['zh','en'],required=True); p.add_argument('--extractor'); p.add_argument('--extractor-4bit',action='store_true'); p.add_argument('--device',default='cuda:0'); a=p.parse_args()
 names=['moerouter','trainmoe_0_120','trainmoe_120_150','trainmoe_150_180','trainmoe_over180']; base=Path(a.models)
 tokenizers=[AutoTokenizer.from_pretrained(base/x,local_files_only=True) for x in names]; models=[AutoModelForCausalLM.from_pretrained(base/x,local_files_only=True,torch_dtype=torch.float16).to(a.device).eval() for x in names]; lengthtok=AutoTokenizer.from_pretrained(a.tokenizer,local_files_only=True); extractor=None; extractor_tok=None
 def tokens(s): return len(lengthtok(s,add_special_tokens=False,verbose=False)['input_ids'])
 def generate(i,prompt,max_new=1280,temperature=.1,top_p=.1):
  t=tokenizers[i]; m=models[i]; text=t.apply_chat_template([{'role':'system','content':' You are a helpful assistant.'},{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True); x=t(text,return_tensors='pt').to(a.device)
  with torch.inference_mode(): y=m.generate(**x,max_new_tokens=max_new,temperature=temperature,top_p=top_p,do_sample=False)
  return t.decode(y[0,x['input_ids'].shape[1]:],skip_special_tokens=True).strip()
 def fallback(segment):
  nonlocal extractor,extractor_tok
  if not a.extractor: return None
  if extractor is None:
   extractor_tok=AutoTokenizer.from_pretrained(a.extractor,local_files_only=True)
   extractor=AutoModelForCausalLM.from_pretrained(a.extractor,local_files_only=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.float16),device_map={'':a.device}).eval() if a.extractor_4bit else AutoModelForCausalLM.from_pretrained(a.extractor,local_files_only=True,torch_dtype=torch.float32).eval()
  if a.language=='en':
   prompt='You are an expert in text segmentation. Split the following English document into consecutive, semantically complete chunks. Preserve the original English wording exactly: do not translate, paraphrase, omit, or add text. Separate chunks with the literal delimiter `\n---\n` and output only the chunks.\n\nDocument:\n{}\n\nChunks:\n'.format(segment)
  else:
   prompt='这是一个文本分块任务，你是一名文本分割方面的专家，负责将给定的文本分割成文本块。你必须遵守以下四个条件：\n1. 根据文本的逻辑和语义结构对文本进行分割，使得每个文本块都具有完整的逻辑表达。\n2. 避免文本块过长或过短，在识别内容转换与分块长度之间取得良好平衡。\n3. 不要改变文本的原始词汇或内容。\n4. 不要添加任何新词或符号。\n如果你理解，请将以下文本分割成文本块，他们之间严格通过“\n---\n”来分隔。\n\n文档内容：{}\n\n分割好的文本块为：'.format(segment)
  chat=extractor_tok.apply_chat_template([{'role':'system','content':' You are a helpful assistant.'},{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True); x=extractor_tok(chat,return_tensors='pt'); x=x.to(a.device) if a.extractor_4bit else x
  with torch.inference_mode(): y=extractor.generate(**x,max_new_tokens=2048,do_sample=False)
  return [z.strip() for z in extractor_tok.decode(y[0,x['input_ids'].shape[1]:],skip_special_tokens=True).split('\n---\n') if z.strip()]
 def find_anchor(segment,needle,start):
  if not needle.strip(): return None
  pos=segment.find(needle,start)
  if pos>=0: return (pos,pos+len(needle),'exact')
  hit=partial_ratio_alignment(needle,segment[start:],score_cutoff=85)
  if hit is None: return None
  return (start+hit.dest_start,start+hit.dest_end,'fuzzy')
 def windows(text):
  # Author pre-segments at punctuation with a 512-word English or 512-character Chinese budget.
  b=sorted(set([0]+[m.end() for m in re.finditer(r'(?<=[.!?。！？；])(?:\s+|(?=[^\s]))|\n\n+',text)]+[len(text)])); parts=[]; start=0; end=0
  for s,e in zip(b,b[1:]):
   measure=(lambda v: len(v.split())) if a.language=='en' else len
   if end>start and measure(text[start:e])>512: parts.append((start,end)); start=s
   end=e
  if end>start: parts.append((start,end))
  return parts
 path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); fail=path.with_suffix(path.suffix+'.failures.jsonl'); auditpath=path.with_suffix(path.suffix+'.alignment.jsonl'); count=0
 with open(a.documents,encoding='utf8') as source,tmp.open('w',encoding='utf8') as out,fail.open('w',encoding='utf8') as errors,auditpath.open('w',encoding='utf8') as audit:
  for line in source:
   d=json.loads(line); text=d['normalized_text']; assert hashlib.sha256(text.encode()).hexdigest()==d['source_text_sha256']; cuts=[0]; bad=[]; inferred=[]
   for s,e in windows(text):
    segment=text[s:e]; route=generate(0,ROUTER.format(segment),max_new=1).strip(); expert=int(route) if route in ['0','1','2','3'] else 0; result=None; raw=''
    for attempt in range(4):
     raw=generate(expert+1,EXPERT.format(segment),temperature=.1 if attempt==0 else .5,top_p=.1 if attempt==0 else .5)
     try:
      value=json.loads(raw)
      if isinstance(value,list) and all(isinstance(x,str) for x in value): result=value; break
     except (ValueError,TypeError): pass
    if result is None:
     fallback_chunks=fallback(segment)
     inferred.append({'span':[s,e],'method':'author_extractor_fallback'})
     if not fallback_chunks: bad.append({'span':[s,e],'reason':'invalid expert JSON and fallback unavailable','router_output':route,'expert_output':raw}); continue
     result=[x[:20]+'[MASK]'+x[-20:] if len(x)>40 else x for x in fallback_chunks]
    cursor=0; local_cuts=[]; alignment_errors=[]
    for pattern in result:
     if '[MASK]' not in pattern: alignment_errors.append({'reason':'missing MASK','pattern':pattern}); continue
     probe=cursor; anchors=[]; failed=False
     for anchor_text in pattern.split('[MASK]'):
      if not anchor_text.strip(): continue
      anchor=find_anchor(segment,anchor_text,probe)
      if not anchor: failed=True; break
      anchors.append(anchor); probe=anchor[1]
     if failed or not anchors: alignment_errors.append({'reason':'anchor alignment failed','pattern':pattern}); continue
     end=anchors[-1][1]
     if any(x[2]=='fuzzy' for x in anchors): inferred.append({'span':[s,e],'pattern':pattern,'anchors':anchors,'method':'fuzzy_anchor_score_at_least_85'})
     if end>cursor and end<len(segment): local_cuts.append(end)
     cursor=end
    # The released MoC implementation uses Qwen2.5 to recover source text from
    # expert masks when its regex cannot extract a span. Apply that same recovery
    # to failed source alignments, then require every recovered chunk to match
    # the original segment in order before accepting its boundaries.
    if alignment_errors:
     recovered=fallback(segment)
     recovered_cuts=[]; recovered_cursor=0; recovery_alignments=[]
     for chunk in recovered or []:
      pos=segment.find(chunk,recovered_cursor) if chunk else -1
      if pos>=0:
       recovered_cursor=pos+len(chunk); recovery_alignments.append({'method':'exact','score':100})
      else:
       hit=partial_ratio_alignment(chunk,segment[recovered_cursor:],score_cutoff=85) if chunk else None
       if hit is None:
        recovered_cuts=[]; break
       recovered_cursor+=hit.dest_end
       recovery_alignments.append({'method':'fuzzy','score':hit.score,'source_span':[hit.src_start,hit.src_end],'target_span':[hit.dest_start,hit.dest_end]})
      if recovered_cursor<len(segment): recovered_cuts.append(recovered_cursor)
     if recovered and recovered_cuts:
      local_cuts=recovered_cuts
      inferred.append({'span':[s,e],'method':'author_qwen_extractor_source_recovery','quantization':'4-bit' if a.extractor_4bit else 'none','recovered_chunks':len(recovered),'alignments':recovery_alignments})
     else:
      bad.extend([{'span':[s,e],**item,'extractor_chunks':recovered,'recovery_alignments':recovery_alignments} for item in alignment_errors]); continue
    cuts.extend(s+end for end in local_cuts)
    if e<len(text): cuts.append(e)
   if bad:
    errors.write(json.dumps({'source_doc_id':d['source_doc_id'],'errors':bad,'handling':'document omitted pending alignment repair'},ensure_ascii=False)+'\n'); errors.flush(); continue
   audit.write(json.dumps({'source_doc_id':d['source_doc_id'],'inferred':inferred},ensure_ascii=False)+'\n'); audit.flush()
   cuts=sorted(set(cuts+[len(text)]))
   for i,(s,e) in enumerate(zip(cuts,cuts[1:])):
    row={'dataset':d['dataset'],'baseline_id':'B5_MoC','source_doc_id':d['source_doc_id'],'chunk_id':f"{d['source_doc_id']}::chunk_{i:05d}",'chunk_index':i,'text':text[s:e],'start_char':s,'end_char':e,'offset_unit':'unicode_codepoint_zero_based_half_open','offset_basis':'normalized_text','source_text_sha256':d['source_text_sha256'],'token_count':tokens(text[s:e]),'source_paragraph_ids':[x['id'] for x in d.get('paragraphs',[]) if x['start_char']<e and x['end_char']>s]}; out.write(json.dumps(row,ensure_ascii=False)+'\n'); count+=1
   out.flush()
 os.replace(tmp,path); print(json.dumps({'output':str(path),'chunks':count,'failure_log':str(fail)}))
if __name__=='__main__': main()
