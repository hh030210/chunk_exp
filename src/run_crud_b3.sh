#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1059718 2>/dev/null; do sleep 30; done
test -s results/QASPER/chunks/B3_meta_chunking.jsonl
CUDA_VISIBLE_DEVICES=2 /home/humq/envs/chunk_baseline/bin/python src/meta_ppl_chunks.py --documents results/CRUD-RAG/documents.jsonl --model models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --output results/CRUD-RAG/chunks/B3_meta_chunking.jsonl
