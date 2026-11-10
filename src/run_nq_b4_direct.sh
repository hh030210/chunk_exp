#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
CUDA_VISIBLE_DEVICES=0 /home/humq/envs/chunk_baseline/bin/python src/pic_chunks.py --documents results/NQ/documents.jsonl --model models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --embedding models/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 --output results/NQ/chunks/B4_PIC.jsonl
