#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1062265 2>/dev/null; do sleep 30; done
test -s configs/qasper_b2_threshold.json
test -s results/QASPER/chunks/B2_semantic.jsonl
PY=/home/humq/envs/chunk_baseline/bin/python
THRESHOLD=$("$PY" -c 'import json; print(json.load(open("configs/qasper_b2_threshold.json"))["threshold"])')
CUDA_VISIBLE_DEVICES=1 "$PY" src/semantic_chunks.py --documents results/CRUD-RAG/documents.jsonl --embedding models/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 --tokenizer models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --threshold "$THRESHOLD" --output results/CRUD-RAG/chunks/B2_semantic.jsonl
