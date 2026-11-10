#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1038593 2>/dev/null; do sleep 10; done
PY=/home/humq/envs/chunk_baseline/bin/python
"$PY" -c 'import torch; assert tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2]) >= (2,6); assert torch.cuda.is_available()'
CUDA_VISIBLE_DEVICES=3 "$PY" src/pic_chunks.py --documents results/QASPER/documents.jsonl --model models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --embedding models/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 --output results/QASPER/chunks/B4_PIC.jsonl
