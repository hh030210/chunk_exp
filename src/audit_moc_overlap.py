#!/usr/bin/env python3
"""Report exact training-document containment in the evaluation corpus."""
import argparse,collections,hashlib,json
import ahocorasick

def main():
 p=argparse.ArgumentParser(); p.add_argument('--training',required=True); p.add_argument('--documents',required=True); p.add_argument('--output',required=True); a=p.parse_args(); refs={}; patterns=collections.defaultdict(list); missing=[]
 for i,line in enumerate(open(a.training,encoding='utf8')):
  row=json.loads(line); prompt=row['conversation'][0]['human']; before='文档内容：'; after='\n\n分割好的文本块的列表格式输出：'
  if before not in prompt or after not in prompt: missing.append(i); continue
  text=prompt.split(before,1)[1].rsplit(after,1)[0]; refs[i]=text
  if len(text)>=80:
   for s in set([0,max(0,len(text)//2-40),max(0,len(text)-80)]): patterns[text[s:s+80]].append(i)
 auto=ahocorasick.Automaton()
 for pattern,ids in patterns.items(): auto.add_word(pattern,ids)
 auto.make_automaton(); hits=collections.defaultdict(set)
 for line in open(a.documents,encoding='utf8'):
  d=json.loads(line); text=d['normalized_text']; candidates=set()
  for _,v in auto.iter(text): candidates.update(v)
  for idx in candidates:
   if refs[idx] in text: hits[idx].add(d['source_doc_id'])
 with open(a.output,'w',encoding='utf8') as f:
  for idx in sorted(hits): f.write(json.dumps({'training_index':idx,'training_text_sha256':hashlib.sha256(refs[idx].encode()).hexdigest(),'source_doc_ids':sorted(hits[idx]),'match':'exact_training_text_contained_in_source'},ensure_ascii=False)+'\n')
 print(json.dumps({'training_rows':len(refs),'parse_failures':len(missing),'training_rows_with_exact_match':len(hits),'matched_source_documents':len(set().union(*hits.values()) if hits else set()),'limitations':'Exact training text contained in corpus only; misses edits and cases where corpus text is contained in longer training text.'}))
if __name__=='__main__':main()
