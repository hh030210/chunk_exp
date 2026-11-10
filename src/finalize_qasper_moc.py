#!/usr/bin/env python3
"""Merge recovered QASPER MoC documents and require exact source coverage."""
import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def group_chunks(rows, label):
    groups = defaultdict(list)
    for row in rows:
        groups[row["source_doc_id"]].append(row)
    for doc_id, chunks in groups.items():
        chunks.sort(key=lambda x: x["chunk_index"])
        if [x["chunk_index"] for x in chunks] != list(range(len(chunks))):
            raise ValueError(f"{label}: non-contiguous chunk indexes for {doc_id}")
    return groups


def verify_document(doc_id, chunks, document):
    text = document["normalized_text"]
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != document["source_text_sha256"]:
        raise ValueError(f"source hash mismatch for {doc_id}")
    cursor = 0
    pieces = []
    for row in chunks:
        if row["source_text_sha256"] != digest:
            raise ValueError(f"chunk hash mismatch for {doc_id}")
        start, end = row["start_char"], row["end_char"]
        if start != cursor or end <= start or row["text"] != text[start:end]:
            raise ValueError(f"span/source mismatch for {doc_id} chunk {row['chunk_index']}")
        pieces.append(row["text"])
        cursor = end
    if cursor != len(text) or "".join(pieces) != text:
        raise ValueError(f"incomplete source coverage for {doc_id}: {cursor}/{len(text)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--documents", required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--recovery", required=True)
    p.add_argument("--original-failures", required=True)
    p.add_argument("--recovery-failures", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()

    docs = read_jsonl(a.documents)
    by_id = {x["source_doc_id"]: x for x in docs}
    if len(by_id) != len(docs):
        raise ValueError("duplicate source_doc_id in documents")
    failures = read_jsonl(a.original_failures)
    failed_ids = {x["source_doc_id"] for x in failures}
    recovery_failures = read_jsonl(a.recovery_failures)
    if recovery_failures:
        raise ValueError(f"recovery still has {len(recovery_failures)} failed document(s)")

    base_groups = group_chunks(read_jsonl(a.base), "base")
    recovery_groups = group_chunks(read_jsonl(a.recovery), "recovery")
    if set(recovery_groups) != failed_ids:
        raise ValueError(
            f"recovered IDs differ from original failures: expected={sorted(failed_ids)}, "
            f"got={sorted(recovery_groups)}"
        )
    if set(base_groups) & set(recovery_groups):
        raise ValueError("recovery output duplicates documents already in base")
    merged = {}
    merged.update(base_groups)
    merged.update(recovery_groups)
    if set(merged) != set(by_id):
        raise ValueError(
            f"document coverage mismatch: missing={len(set(by_id)-set(merged))}, "
            f"unexpected={len(set(merged)-set(by_id))}"
        )

    rows = []
    for doc in docs:
        doc_id = doc["source_doc_id"]
        chunks = merged[doc_id]
        verify_document(doc_id, chunks, doc)
        rows.extend(chunks)
    write_jsonl(a.output, rows)

    output = Path(a.output)
    base_path = Path(a.base)
    recovery_path = Path(a.recovery)
    base_audit = base_path.with_suffix(base_path.suffix + ".alignment.jsonl")
    recovery_audit = recovery_path.with_suffix(recovery_path.suffix + ".alignment.jsonl")
    audits = read_jsonl(base_audit) + read_jsonl(recovery_audit)
    write_jsonl(output.with_suffix(output.suffix + ".alignment.jsonl"), audits)
    write_jsonl(output.with_suffix(output.suffix + ".failures.jsonl"), recovery_failures)
    print(json.dumps({"output": str(output), "documents": len(docs), "chunks": len(rows),
                      "recovered_documents": len(recovery_groups), "coverage": "exact"}))


if __name__ == "__main__":
    main()
