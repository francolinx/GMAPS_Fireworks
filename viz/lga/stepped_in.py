#!/usr/bin/env python3
"""When would GMAPS have alerted with each parser? Replays each arm's parsed records for the eight LaGuardia lines through
the same action normaliser the benchmark uses and reports the first t at which the ledger holds BOTH an active landing
clearance on runway 4 (with a callsign) AND a crossing clearance on runway 4 (with a callsign) — the conflict rule.

  python3 viz/lga/stepped_in.py            # reads viz/lga/model_outputs/*.jsonl → viz/lga/stepped_in.json (+ prints a table)

Reference points from the NTSB preliminary timeline (t = s after 23:35:00 EDT): controller's first "stop" t=132 (23:37:12),
Truck 1 enters runway 4 at t=142 (23:37:22).
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "bench"))
from score import parse_output, as_list, norm_text  # noqa: E402
from normalize import actions_for  # noqa: E402

CONTROLLER_STOP_T, TRUCK_ON_RUNWAY_T = 132, 142


def runway_of(values):
    for v in as_list(values):
        m = re.search(r"runway\s+(four|zero four|04|4)\b", norm_text(v))
        if m:
            return "4"
    return None


def alert_time(rows_by_id, lines):
    landing, crossing = None, None
    for ln in lines:
        d = parse_output(rows_by_id.get(ln["id"], {}).get("output", "")) or {}
        acts = actions_for(as_list(d.get("commands")))
        cs = [norm_text(c) for c in as_list(d.get("callsigns"))]
        rwy = runway_of(d.get("values")) or runway_of(d.get("commands"))
        if "CLEARED_TO_LAND" in acts and cs and rwy == "4" and str(d.get("role", "")).upper() == "ATCO":
            landing = (ln["t"], cs[0])
        if "CROSS_RUNWAY" in acts and cs and rwy == "4" and str(d.get("role", "")).upper() == "ATCO":
            crossing = (ln["t"], cs[0])
        if landing and crossing:
            return ln["t"], landing, crossing
    return None, landing, crossing


def main():
    lines = [json.loads(l) for l in open(os.path.join(HERE, "lga_transmissions.jsonl"), encoding="utf-8")]
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "model_outputs", "*.jsonl"))):
        arm = os.path.basename(p)[:-6]
        rows = {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
        t, landing, crossing = alert_time(rows, lines)
        out[arm] = {"alert_t": t, "clock": (f"23:{35 + t // 60}:{t % 60:02d}" if t is not None else None),
                    "lead_over_controller_s": (CONTROLLER_STOP_T - t) if t is not None else None,
                    "lead_over_truck_s": (TRUCK_ON_RUNWAY_T - t) if t is not None else None,
                    "landing_seen": landing, "crossing_seen": crossing}
    json.dump(out, open(os.path.join(HERE, "stepped_in.json"), "w"), indent=1)
    print(f"{'arm':40s} alert_t  clock     vs controller  vs truck on runway")
    for arm, v in out.items():
        print(f"{arm:40s} {str(v['alert_t']):7s}  {str(v['clock']):9s} {str(v['lead_over_controller_s']):13s}  {v['lead_over_truck_s']}")
    print(f"{'controller first stop':40s} {CONTROLLER_STOP_T:<7d}  23:37:12")
    print(f"{'Truck 1 enters runway 4':40s} {TRUCK_ON_RUNWAY_T:<7d}  23:37:22")


if __name__ == "__main__":
    main()
