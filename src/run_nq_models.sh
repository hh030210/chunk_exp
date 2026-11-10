#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
kind="$1"; previous="$2"; gpu="$3"
while kill -0 "$previous" 2>/dev/null || kill -0 1063945 2>/dev/null; do sleep 60; done
test -s results/NQ/documents.jsonl
PY=/home/humq/envs/chunk_baseline/bin/python
MODEL=models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
EMBED=models/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3
case "$kind" in
 b2) test -s results/CRUD-RAG/chunks/B2_semantic.jsonl; threshold=$("$PY" -c 'import json; print(json.load(open("configs/qasper_b2_threshold.json"))["threshold"])'); CUDA_VISIBLE_DEVICES="$gpu" "$PY" src/semantic_chunks.py --documents results/NQ/documents.jsonl --embedding "$EMBED" --tokenizer "$MODEL" --threshold "$threshold" --output results/NQ/chunks/B2_semantic.jsonl;;
 b3) test -s results/CRUD-RAG/chunks/B3_meta_chunking.jsonl; CUDA_VISIBLE_DEVICES="$gpu" "$PY" src/meta_ppl_chunks.py --documents results/NQ/documents.jsonl --model "$MODEL" --output results/NQ/chunks/B3_meta_chunking.jsonl;;
 b4) test -s results/CRUD-RAG/chunks/B4_PIC.jsonl; CUDA_VISIBLE_DEVICES="$gpu" "$PY" src/pic_chunks.py --documents results/NQ/documents.jsonl --model "$MODEL" --embedding "$EMBED" --output results/NQ/chunks/B4_PIC.jsonl;;
 b5) test -s results/CRUD-RAG/chunks/B5_MoC_repaired.jsonl; CUDA_VISIBLE_DEVICES="$gpu" "$PY" src/moc_chunks.4bit.py --documents results/NQ/documents.jsonl --models models/moc_unpacked --tokenizer "$MODEL" --extractor models/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --extractor-4bit --language en --output results/NQ/chunks/B5_MoC_repaired.jsonl;;
 *) exit 2;;
esac
