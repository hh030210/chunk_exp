#!/usr/bin/env bash
set -euo pipefail
cd /home/humq/chunk-baseline-experiments

# Wait until the current QASPER/CRUD-RAG/NQ MoC queue has released GPU 1.
PIPELINE_PID=2261233
while kill -0 "$PIPELINE_PID" 2>/dev/null; do sleep 60; done

BASE=results/QASPER/chunks/B5_MoC_repaired.jsonl
FAILURES="$BASE.failures.jsonl"
RECOVERY=results/QASPER/chunks/B5_MoC_failure_recovery.jsonl
DOCS=results/QASPER/documents.jsonl
SUBSET=results/QASPER/qasper_moc_failed_documents.jsonl
test -s "$BASE"
test ! -e "$BASE.tmp"
test -s "$FAILURES"

/home/humq/envs/chunk_baseline/bin/python - "$DOCS" "$FAILURES" "$SUBSET" <<'PY'
import json, sys
docs_path, failures_path, subset_path = sys.argv[1:]
failed = {json.loads(line)["source_doc_id"] for line in open(failures_path, encoding="utf-8") if line.strip()}
found = set()
with open(docs_path, encoding="utf-8") as src, open(subset_path, "w", encoding="utf-8") as dst:
    for line in src:
        row = json.loads(line)
        if row["source_doc_id"] in failed:
            dst.write(line)
            found.add(row["source_doc_id"])
if found != failed:
    raise SystemExit(f"failed IDs absent from documents: {sorted(failed-found)}")
print(f"recovery documents: {len(found)}")
PY

mkdir -p logs
TOKEN=models/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
EXTRACT=models/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
CUDA_VISIBLE_DEVICES=1 /home/humq/envs/chunk_baseline/bin/python src/moc_chunks.4bit.py \
  --documents "$SUBSET" --models models/moc_unpacked --tokenizer "$TOKEN" \
  --extractor "$EXTRACT" --extractor-4bit --language en --output "$RECOVERY"

cp "$FAILURES" results/QASPER/chunks/B5_MoC.pre_repair.failures.jsonl
/home/humq/envs/chunk_baseline/bin/python src/finalize_qasper_moc.py \
  --documents "$DOCS" --base "$BASE" --recovery "$RECOVERY" \
  --original-failures "$FAILURES" \
  --recovery-failures "$RECOVERY.failures.jsonl" \
  --output results/QASPER/chunks/B5_MoC.jsonl
