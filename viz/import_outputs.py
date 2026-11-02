#!/usr/bin/env python3
"""Write real model outputs back into scenario JSONs as the 'parsed' blocks (and recompute 'actions')."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list
from normalize import actions_for

preds_path, scenarios = sys.argv[1], sys.argv[2:]
preds = {}
model = None
for l in open(preds_path, encoding="utf-8"):
    if l.strip():
        r = json.loads(l); preds[r["id"]] = r; model = model or r.get("model")
for sp in scenarios:
    s = json.load(open(sp)); tag = os.path.basename(sp)[:-5]; hit = miss = 0
    for v in s["variants"].values():
        for t in v["transmissions"]:
            p = preds.get(f"{tag}#{t['t']}")
            d = parse_output(p["output"]) if p else None
            if d:
                t["parsed"] = {"role": d.get("role"), "callsigns": as_list(d.get("callsigns")), "commands": as_list(d.get("commands")), "values": as_list(d.get("values"))}
                t["actions"] = sorted(actions_for(as_list(d.get("commands"))) - {"OTHER"}); t["parsed_by"] = model; hit += 1
            else:
                miss += 1
    s["parsed_by"] = model; s["parsed_note"] = "'parsed' blocks are model output (not hand-written)"
    json.dump(s, open(sp, "w"), indent=None)
    print(f"{sp}: {hit} transmissions updated from {model}, {miss} missing")
