#!/usr/bin/env bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments

B3_PARENT=1065730
B4_PARENT=1066346
GPU=""
while [[ -z "$GPU" ]]; do
  if ! kill -0 "$B3_PARENT" 2>/dev/null; then
    GPU=2
  elif ! kill -0 "$B4_PARENT" 2>/dev/null; then
    GPU=3
  else
    sleep 30
  fi
done

test -s results/NQ/documents.jsonl
if [[ -e results/NQ/chunks/B3_meta_chunking.jsonl || -e results/NQ/chunks/B3_meta_chunking.jsonl.tmp ]]; then
  echo "NQ B3 output already exists; refusing duplicate launch."
  exit 1
fi
CUDA_VISIBLE_DEVICES="$GPU" /home/humq/envs/chunk_baseline/bin/python \
  src/meta_ppl_chunks.py \
  --documents results/NQ/documents.jsonl \
  --model models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a \
  --output results/NQ/chunks/B3_meta_chunking.jsonl
