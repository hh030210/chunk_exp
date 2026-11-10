#!/bin/bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments
while kill -0 1015863 2>/dev/null; do sleep 30; done
if ! grep -q '100 34.7G' logs/kilt_download.log; then echo 'Download completeness not verified; stopping.'; exit 1; fi
sha256sum data/NQ/kilt_knowledgesource.json > data/NQ/kilt_knowledgesource.sha256
python3 src/nq_prepare_corpus.py --input data/NQ/kilt_knowledgesource.json --output results/NQ/documents.jsonl
mkdir -p results/NQ/chunks
for size in 256 512 1024; do
 nohup /home/humq/envs/denoise_qa/bin/python src/fixed_chunks.py --documents results/NQ/documents.jsonl --tokenizer models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --size "$size" --output "results/NQ/chunks/B0_fixed_${size}_o0.jsonl" > "logs/nq_b0_${size}.log" 2>&1 </dev/null & echo "NQ_B0_${size} PID=$!"
done
nohup /home/humq/envs/denoise_qa/bin/python src/recursive_chunks.py --documents results/NQ/documents.jsonl --tokenizer models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a --output results/NQ/chunks/B1_recursive.jsonl > logs/nq_b1.log 2>&1 </dev/null & echo NQ_B1_PID=$!
