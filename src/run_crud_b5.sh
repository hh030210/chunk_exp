#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1065724 2>/dev/null; do sleep 30; done
test -s results/CRUD-RAG/chunks/B2_semantic.jsonl
test -s results/QASPER/chunks/B5_MoC.jsonl
CUDA_VISIBLE_DEVICES=1 /home/humq/envs/chunk_baseline/bin/python src/moc_chunks.py --documents results/CRUD-RAG/documents.jsonl --models models/moc_unpacked --tokenizer models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --language zh --output results/CRUD-RAG/chunks/B5_MoC.jsonl
