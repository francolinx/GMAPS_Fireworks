#!/usr/bin/env python3
"""Where do two arms disagree, and who is right? For the 11:15 error-analysis step.

  python3 scripts/16_error_analysis.py data/splits/test.jsonl results/test/<lora>.preds.jsonl results/test/<opus>.preds.jsonl --show 25

Prints: per-action-class recall for each arm, the role confusion for each arm, counts of rows where only A is fully
right / only B / both / neither, and the first --show rows where the two arms disagree (text, gold, both outputs).
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list, norm_text  # noqa: E402
from normalize import actions_for, NON_ACTIONS, RUNWAY_CRITICAL  # noqa: E402


def load(p):
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def record(g, d):
    d = d or {}
    acts = actions_for(as_list(d.get("commands"))) - NON_ACTIONS
    cs = collections.Counter(norm_text(x) for x in as_list(d.get("callsigns")))
    role = str(d.get("role", "")).upper()
    gacts = actions_for(g["gold"]["command"]) - NON_ACTIONS
    gcs = collections.Counter(norm_text(x) for x in g["gold"]["callsign"])
    r_ok = g["role"] not in ("ATCO", "PILOT") or role == g["role"]
    return {"acts": acts, "cs": cs, "role": role, "ok": (acts == gacts and cs == gcs and r_ok), "gacts": gacts, "gcs": gcs, "r_ok": r_ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold"); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--show", type=int, default=20)
    args = ap.parse_args()
    gold = [json.loads(l) for l in open(args.gold, encoding="utf-8") if l.strip()]
    A, B = load(args.a), load(args.b)
    na = next(iter(A.values()))["model"]; nb = next(iter(B.values()))["model"]

    per_class = {na: collections.Counter(), nb: collections.Counter()}; class_n = collections.Counter()
    role_conf = {na: collections.Counter(), nb: collections.Counter()}
    quad = collections.Counter(); crit_quad = collections.Counter(); disagreements = []
    for g in gold:
        ra = record(g, parse_output((A.get(g["id"]) or {}).get("output")))
        rb = record(g, parse_output((B.get(g["id"]) or {}).get("output")))
        for act in ra["gacts"]:
            class_n[act] += 1
            per_class[na][act] += act in ra["acts"]; per_class[nb][act] += act in rb["acts"]
        if g["role"] in ("ATCO", "PILOT"):
            role_conf[na][(g["role"], ra["role"] or "∅")] += 1; role_conf[nb][(g["role"], rb["role"] or "∅")] += 1
        key = ("A" if ra["ok"] else "-") + ("B" if rb["ok"] else "-")
        quad[key] += 1
        if ra["gacts"] & RUNWAY_CRITICAL:
            crit_quad[key] += 1
        if ra["ok"] != rb["ok"]:
            disagreements.append((g, ra, rb, A.get(g["id"], {}).get("output", ""), B.get(g["id"], {}).get("output", "")))

    print(f"A = {na}\nB = {nb}\nn = {len(gold)}\n")
    print("Full-record outcome   (AB = both right, A- = only A, -B = only B, -- = neither)")
    print("  all rows:            ", dict(quad))
    print("  runway-critical rows:", dict(crit_quad))
    print("\nPer-action recall (gold rows containing the action):")
    print(f"  {'action':22s} {'n':>4s}  {na[:28]:>28s}  {nb[:28]:>28s}")
    for act, n in sorted(class_n.items(), key=lambda x: -x[1]):
        print(f"  {act:22s} {n:4d}  {100 * per_class[na][act] / n:27.1f}%  {100 * per_class[nb][act] / n:27.1f}%")
    for name in (na, nb):
        errs = {k: v for k, v in role_conf[name].items() if k[0] != k[1]}
        print(f"\nRole errors {name}: {errs or 'none'}")
    print(f"\n{len(disagreements)} rows where exactly one arm is fully right; first {args.show}:")
    for g, ra, rb, oa, ob in disagreements[: args.show]:
        who = "A right" if ra["ok"] else "B right"
        print(f"\n[{who}] {g['id']}  role={g['role']}\n  TEXT: {g['text']}\n  GOLD: cs={list(g['gold']['callsign'])} acts={sorted(ra['gacts'])} cmds={g['gold']['command']}")
        print(f"  A:    {str(oa)[:220]}\n  B:    {str(ob)[:220]}")


if __name__ == "__main__":
    main()
