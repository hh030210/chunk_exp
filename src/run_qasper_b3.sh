#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1038593 2>/dev/null; do sleep 10; done
PY=/home/humq/envs/chunk_baseline/bin/python
"$PY" -c 'import torch,transformers; assert tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2]) >= (2,6); assert torch.cuda.is_available()'
CUDA_VISIBLE_DEVICES=2 "$PY" src/meta_ppl_chunks.py --documents results/QASPER/documents.jsonl --model models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --output results/QASPER/chunks/B3_meta_chunking.jsonl
