#!/usr/bin/env python3
"""Drop training examples whose target role is UNKNOWN (and optionally those with an empty record).

UNKNOWN comes from ATCO2 rows whose speaker label is UNK-*. Keeping them teaches the model to answer UNKNOWN,
which is always scored as wrong on rows whose gold role is ATCO/PILOT (the frontier never says UNKNOWN).

  python3 scripts/12_filter_sft.py data/sft/mix_train.jsonl data/sft/mix_train_v2.jsonl
"""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
drop_empty = "--drop-empty" in sys.argv
kept = dropped_unk = dropped_empty = 0
with open(src, encoding="utf-8") as fi, open(dst, "w", encoding="utf-8") as fo:
    for line in fi:
        if not line.strip():
            continue
        ex = json.loads(line)
        tgt = json.loads(ex["messages"][-1]["content"])
        if str(tgt.get("role", "")).upper() == "UNKNOWN":
            dropped_unk += 1; continue
        if drop_empty and not (tgt.get("callsigns") or tgt.get("commands") or tgt.get("values")):
            dropped_empty += 1; continue
        fo.write(line if line.endswith("\n") else line + "\n"); kept += 1
print(f"kept {kept}, dropped UNKNOWN-role {dropped_unk}, dropped empty {dropped_empty} → {dst}")
