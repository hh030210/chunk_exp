#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 "${SMOKE_PID:?set SMOKE_PID to the smoke-test PID}" 2>/dev/null; do sleep 15; done
test -s results/QASPER/moc_4bit_smoke.jsonl
test "$(wc -l < results/QASPER/moc_4bit_smoke.jsonl)" -gt 0
test ! -s results/QASPER/moc_4bit_smoke.jsonl.failures.jsonl
PY=/home/humq/envs/chunk_baseline/bin/python
TOKEN=models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
EXTRACT=models/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
CUDA_VISIBLE_DEVICES=1 "$PY" src/moc_chunks.4bit.py --documents results/QASPER/documents.jsonl --models models/moc_unpacked --tokenizer "$TOKEN" --extractor "$EXTRACT" --extractor-4bit --language en --output results/QASPER/chunks/B5_MoC_repaired.jsonl
CUDA_VISIBLE_DEVICES=1 "$PY" src/moc_chunks.4bit.py --documents results/CRUD-RAG/documents.jsonl --models models/moc_unpacked --tokenizer "$TOKEN" --extractor "$EXTRACT" --extractor-4bit --language zh --output results/CRUD-RAG/chunks/B5_MoC_repaired.jsonl
while kill -0 1067228 2>/dev/null; do sleep 60; done
CUDA_VISIBLE_DEVICES=1 "$PY" src/moc_chunks.4bit.py --documents results/NQ/documents.jsonl --models models/moc_unpacked --tokenizer "$TOKEN" --extractor "$EXTRACT" --extractor-4bit --language en --output results/NQ/chunks/B5_MoC_repaired.jsonl
