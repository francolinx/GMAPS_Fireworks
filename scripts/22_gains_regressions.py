#!/usr/bin/env python3
"""Gains and regressions of one arm against another, the way the NVIDIA enablement session asked for them:
not just "accuracy went up", but which rows the new model fixed, which it broke, and whether a broken row would
change what the downstream system (the GMAPS ledger) does.

  python3 scripts/22_gains_regressions.py data/splits/test.jsonl results/test/<before>.preds.jsonl results/test/<after>.preds.jsonl [--show 6] [--md]

Severity of a regression (after is wrong, before was right), judged on the parsed record the ledger ingests:
  ledger-visible  : the runway-critical action set (cleared to land / take off / line up / hold short / cross / vacate …)
                    or the callsign set differs from gold → the ledger would track the wrong aircraft or the wrong clearance.
  role-only       : only the speaker role is wrong (instruction vs read-back); the ledger still sees the right aircraft and action.
  other-action    : a non-runway action (contact, report, speed …) missing or extra; no runway state changes.
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list, norm_text  # noqa: E402
from normalize import actions_for, NON_ACTIONS, RUNWAY_CRITICAL  # noqa: E402


def load(p):
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def rec(g, out):
    d = parse_output(out) or {}
    acts = actions_for(as_list(d.get("commands"))) - NON_ACTIONS
    cs = collections.Counter(norm_text(x) for x in as_list(d.get("callsigns")))
    role = str(d.get("role", "")).upper()
    gacts = actions_for(g["gold"]["command"]) - NON_ACTIONS
    gcs = collections.Counter(norm_text(x) for x in g["gold"]["callsign"])
    r_ok = g["role"] not in ("ATCO", "PILOT") or role == g["role"]
    ok = acts == gacts and cs == gcs and r_ok
    return dict(acts=acts, cs=cs, role=role, ok=ok, gacts=gacts, gcs=gcs, r_ok=r_ok, raw=d)


def severity(r):
    if (r["acts"] & RUNWAY_CRITICAL) != (r["gacts"] & RUNWAY_CRITICAL) or r["cs"] != r["gcs"]:
        return "ledger-visible"
    if not r["r_ok"] and r["acts"] == r["gacts"]:
        return "role-only"
    return "other-action"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold"); ap.add_argument("before"); ap.add_argument("after")
    ap.add_argument("--show", type=int, default=6); ap.add_argument("--md", action="store_true")
    a = ap.parse_args()
    gold = [json.loads(l) for l in open(a.gold, encoding="utf-8") if l.strip()]
    B, A = load(a.before), load(a.after)
    nb = next(iter(B.values()))["model"].split("/")[-1]; na = next(iter(A.values()))["model"].split("/")[-1]
    gains, regs, both, neither = [], [], 0, 0
    for g in gold:
        rb = rec(g, B.get(g["id"], {}).get("output", "")); ra = rec(g, A.get(g["id"], {}).get("output", ""))
        if ra["ok"] and not rb["ok"]:
            gains.append((g, rb, ra))
        elif rb["ok"] and not ra["ok"]:
            regs.append((g, rb, ra))
        elif ra["ok"]:
            both += 1
        else:
            neither += 1
    sev_r = collections.Counter(severity(ra) for _, _, ra in regs)
    sev_g = collections.Counter(severity(rb) for _, rb, _ in gains)  # what kind of error the gain fixed
    crit_regs = sum(1 for g, _, _ in regs if (actions_for(g["gold"]["command"]) & RUNWAY_CRITICAL))
    crit_gains = sum(1 for g, _, _ in gains if (actions_for(g["gold"]["command"]) & RUNWAY_CRITICAL))
    print(f"before = {nb}   after = {na}   n = {len(gold)}")
    print(f"both right {both} | neither {neither} | GAINS (only after right) {len(gains)} | REGRESSIONS (only before right) {len(regs)}")
    print(f"gains fix:        {dict(sev_g)}   (of which on runway-critical rows: {crit_gains})")
    print(f"regressions are:  {dict(sev_r)}   (of which on runway-critical rows: {crit_regs})")
    if a.md:
        print("\n| | rows | of which runway-critical | ledger-visible | role-only | other action |\n|---|---|---|---|---|---|")
        print(f"| Gains — only **{na}** right | {len(gains)} | {crit_gains} | {sev_g['ledger-visible']} | {sev_g['role-only']} | {sev_g['other-action']} |")
        print(f"| Regressions — only **{nb}** right | {len(regs)} | {crit_regs} | {sev_r['ledger-visible']} | {sev_r['role-only']} | {sev_r['other-action']} |")
    def fmt(r):
        return f"role={r['role'] or '∅'} callsigns={sorted(r['cs'])} actions={sorted(r['acts'])}"
    print(f"\n--- {a.show} regressions (ledger-visible first) ---")
    regs.sort(key=lambda t: ["ledger-visible", "other-action", "role-only"].index(severity(t[2])))
    for g, rb, ra in regs[: a.show]:
        print(f"[{severity(ra)}] {g['id']}  \"{g['text']}\"\n   gold : role={g['role']} callsigns={sorted(rec(g, '')['gcs'])} actions={sorted(ra['gacts'])}\n   after: {fmt(ra)}")
    print(f"\n--- {a.show} gains ---")
    for g, rb, ra in gains[: a.show]:
        print(f"[{severity(rb)} before] {g['id']}  \"{g['text']}\"\n   gold  : role={g['role']} actions={sorted(ra['gacts'])}\n   before: {fmt(rb)}")


if __name__ == "__main__":
    main()
