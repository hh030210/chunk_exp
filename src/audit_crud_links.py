#!/usr/bin/env python3
"""Find exact unique body-substring links without using answers or approximate title matches."""
import argparse,collections,json
import ahocorasick

def main():
 p=argparse.ArgumentParser(); p.add_argument('--data',required=True); p.add_argument('--documents',required=True); p.add_argument('--output',required=True); a=p.parse_args(); data=json.load(open(a.data,encoding='utf8')); automaton=ahocorasick.Automaton(); patterns=collections.defaultdict(list); refs={}
 for key in ['questanswer_1doc','questanswer_2docs']:
  for i,r in enumerate(data[key]):
   for field in ['news1','news2']:
    if field not in r: continue
    full=r[field]; body=full.split('正文：',1)[-1]; ref=(key,i,field); refs[ref]=body
    if len(body)<80: continue
    for start in set([0,max(0,len(body)//2-40),max(0,len(body)-80)]): patterns[body[start:start+80]].append(ref)
 for pattern,values in patterns.items(): automaton.add_word(pattern,values)
 automaton.make_automaton(); hits=collections.defaultdict(set)
 for line in open(a.documents,encoding='utf8'):
  d=json.loads(line); text=d['normalized_text']; candidates=set()
  for _,v in automaton.iter(text): candidates.update(v)
  for ref in candidates:
   # Full source article body must be contained exactly; no similarity threshold.
   if refs[ref] and refs[ref] in text: hits[ref].add(d['source_doc_id'])
 with open(a.output,'w',encoding='utf8') as out:
  for ref in refs:
   ids=sorted(hits[ref]); out.write(json.dumps({'task_key':ref[0],'raw_array_index':ref[1],'field':ref[2],'exact_full_body_source_doc_ids':ids},ensure_ascii=False)+'\n')
 print(json.dumps({'references':len(refs),'unique_exact_full_body':sum(len(hits[r])==1 for r in refs),'multiple_matches':sum(len(hits[r])>1 for r in refs),'unmatched':sum(not hits[r] for r in refs)}))
if __name__=='__main__': main()
