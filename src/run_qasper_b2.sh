#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1038593 2>/dev/null; do sleep 10; done
PY=/home/humq/envs/chunk_baseline/bin/python
"$PY" -c 'import torch,transformers; assert tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2]) >= (2, 6); assert torch.cuda.is_available()'
export CUDA_VISIBLE_DEVICES=1
EMBED=models/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3
TOKEN=models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
"$PY" src/semantic_chunks.py --documents data/qasper_dev_calibration/documents.jsonl --embedding "$EMBED" --tokenizer "$TOKEN" --output configs/qasper_b2_threshold.json --calibrate
THRESHOLD=$("$PY" -c 'import json; print(json.load(open("configs/qasper_b2_threshold.json"))["threshold"])')
"$PY" src/semantic_chunks.py --documents results/QASPER/documents.jsonl --embedding "$EMBED" --tokenizer "$TOKEN" --threshold "$THRESHOLD" --output results/QASPER/chunks/B2_semantic.jsonl
