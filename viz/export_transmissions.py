#!/usr/bin/env python3
"""Export a scenario's transmissions as a split JSONL that bench/infer.py can run.

  python3 viz/export_transmissions.py viz/scenario_sfo_sim1.json viz/scenario_sfo_01r.json --out viz/transmissions.jsonl
  BASE_URL=... API_KEY=... python3 bench/infer.py --model <served> --split viz/transmissions.jsonl --out viz/transmissions.preds.jsonl --fewshot 0
  python3 viz/import_outputs.py viz/transmissions.preds.jsonl viz/scenario_sfo_sim1.json viz/scenario_sfo_01r.json
"""
import argparse, json, os

ap = argparse.ArgumentParser(); ap.add_argument("scenarios", nargs="+"); ap.add_argument("--out", required=True)
a = ap.parse_args()
n = 0
with open(a.out, "w", encoding="utf-8") as fo:
    for sp in a.scenarios:
        s = json.load(open(sp)); tag = os.path.basename(sp)[:-5]
        seen = set()
        for vname, v in s["variants"].items():
            for i, t in enumerate(v["transmissions"]):
                key = (t["t"], t["text"])
                if key in seen:
                    continue
                seen.add(key)
                fo.write(json.dumps({"id": f"{tag}#{t['t']}", "airport": s["airport"], "facility": f"{s['airport']} {'Tower' if t['speaker'] in ('TWR',) else 'Ground' if t['speaker'] == 'GND' else 'Tower'}",
                                     "text": t["text"], "role": "ATCO" if t["speaker"] in ("TWR", "GND") else "PILOT",
                                     "gold": {"callsign": [], "command": [], "value": []}}, ensure_ascii=False) + "\n"); n += 1
print(f"wrote {n} transmissions → {a.out}")
