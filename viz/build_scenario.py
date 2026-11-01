#!/usr/bin/env python3
"""Build an animated runway-incursion scenario on real airport geometry.

  python viz/build_scenario.py viz/ksfo.geojson viz/scenario_sfo_sim1.json --runway 28L

Takes the OSM GeoJSON (from fetch_airport_osm.py), merges the runway segments for the chosen
designator, finds a taxiway that crosses it, and emits a scenario the viewer (index.html) animates:
  - SIM212 on final for the runway, touching down and rolling out
  - RESCUE7 cleared to cross the same runway at the chosen taxiway (two branches: unresolved / hold short)
  - the radio transmissions with their parsed records (what the model produces) at the times they occur
  - the clearance-state timeline and the predicted runway-occupancy overlap window

Fictional callsigns, fictional traffic. Geometry © OpenStreetMap contributors (ODbL).
"""
import argparse, json, math, sys

R = 6371000.0


def to_rad(x):
    return x * math.pi / 180


def bearing(a, b):
    lon1, lat1, lon2, lat2 = map(to_rad, (a[0], a[1], b[0], b[1]))
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def dist(a, b):
    lon1, lat1, lon2, lat2 = map(to_rad, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def destination(a, brg, d):
    lon1, lat1, b = to_rad(a[0]), to_rad(a[1]), to_rad(brg)
    lat2 = math.asin(math.sin(lat1) * math.cos(d / R) + math.cos(lat1) * math.sin(d / R) * math.cos(b))
    lon2 = lon1 + math.atan2(math.sin(b) * math.sin(d / R) * math.cos(lat1), math.cos(d / R) - math.sin(lat1) * math.sin(lat2))
    return [math.degrees(lon2), math.degrees(lat2)]


def merge_segments(lines):
    """Join LineStrings that share endpoints into one polyline (greedy)."""
    lines = [list(map(list, l)) for l in lines]
    merged = lines.pop(0)
    changed = True
    while lines and changed:
        changed = False
        for i, l in enumerate(lines):
            if dist(merged[-1], l[0]) < 5: merged += l[1:]
            elif dist(merged[-1], l[-1]) < 5: merged += l[::-1][1:]
            elif dist(merged[0], l[-1]) < 5: merged = l[:-1] + merged
            elif dist(merged[0], l[0]) < 5: merged = l[::-1][:-1] + merged
            else: continue
            lines.pop(i); changed = True; break
    return merged


def seg_intersect(p1, p2, p3, p4, lat0):
    """Planar intersection of segments p1-p2 and p3-p4 (lon/lat scaled). Returns point or None."""
    k = math.cos(to_rad(lat0))
    x1, y1, x2, y2 = p1[0] * k, p1[1], p2[0] * k, p2[1]
    x3, y3, x4, y4 = p3[0] * k, p3[1], p4[0] * k, p4[1]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-14:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return [(x1 + t * (x2 - x1)) / k, y1 + t * (y2 - y1)]
    return None


def along(poly, d_target):
    """Point at distance d_target along polyline."""
    acc = 0.0
    for a, b in zip(poly, poly[1:]):
        d = dist(a, b)
        if acc + d >= d_target:
            f = (d_target - acc) / d if d else 0
            return [a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])]
        acc += d
    return poly[-1]


def poly_len(poly):
    return sum(dist(a, b) for a, b in zip(poly, poly[1:]))


def dist_along_to_point(poly, pt):
    best, acc, bestd = 0.0, 0.0, 1e18
    for a, b in zip(poly, poly[1:]):
        d = dist(a, b)
        # project pt onto a-b
        k = math.cos(to_rad(a[1]))
        ax, ay, bx, by, px, py = a[0] * k, a[1], b[0] * k, b[1], pt[0] * k, pt[1]
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        f = 0 if L2 == 0 else max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L2))
        proj = [(ax + f * (bx - ax)) / k, ay + f * (by - ay)]
        dd = dist(proj, pt)
        if dd < bestd:
            bestd, best = dd, acc + f * d
        acc += d
    return best


def sample_path(poly, t0, t1, n=40):
    """Evenly spaced (in distance) samples with linear time between t0 and t1."""
    L = poly_len(poly)
    return [{"t": round(t0 + (t1 - t0) * i / n, 2), "p": along(poly, L * i / n)} for i in range(n + 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("geojson")
    ap.add_argument("out")
    ap.add_argument("--runway", default="28L", help="landing designator, e.g. 28L")
    ap.add_argument("--taxiway", help="force a crossing taxiway ref; default picks one near mid-runway")
    ap.add_argument("--airport", default="KSFO")
    args = ap.parse_args()

    gj = json.load(open(args.geojson))
    feats = gj["features"]
    des = args.runway.upper()
    num = int("".join(ch for ch in des if ch.isdigit()))
    rw_segs = [f["geometry"]["coordinates"] for f in feats
               if f["properties"]["kind"] == "runway" and f["properties"].get("ref") and des in f["properties"]["ref"].replace("0", "", 1).split("/") + f["properties"]["ref"].split("/")]
    if not rw_segs:
        sys.exit(f"no runway with designator {des} in {args.geojson}")
    rw = merge_segments(rw_segs)
    # orient so travel direction ≈ designator heading (magnetic ≈ true within ~15°, good enough to pick an end)
    want = (num * 10) % 360
    b_fwd = bearing(rw[0], rw[-1])
    if min(abs(b_fwd - want), 360 - abs(b_fwd - want)) > 90:
        rw = rw[::-1]
    threshold, far_end = rw[0], rw[-1]
    rw_len = poly_len(rw)
    rw_brg = bearing(threshold, far_end)

    # crossing taxiways: intersect each taxiway way with the runway polyline
    lat0 = threshold[1]
    crossings = []
    for f in feats:
        if f["properties"]["kind"] != "taxiway":
            continue
        tw = f["geometry"]["coordinates"]
        for a, b in zip(tw, tw[1:]):
            for c, d in zip(rw, rw[1:]):
                x = seg_intersect(a, b, c, d, lat0)
                if x:
                    dalong = dist_along_to_point(rw, x)
                    if 300 < dalong < rw_len - 300:  # ignore end stubs
                        crossings.append({"ref": f["properties"].get("ref"), "point": x, "d_along": dalong, "line": tw})
    if not crossings:
        sys.exit("no taxiway crosses this runway in the data")
    if args.taxiway:
        cands = [c for c in crossings if (c["ref"] or "").upper() == args.taxiway.upper()]
        if not cands:
            sys.exit(f"taxiway {args.taxiway} does not cross {des}; crossing refs: {sorted({c['ref'] for c in crossings})}")
        crossing = cands[0]
    else:
        named = [c for c in crossings if c["ref"]]
        crossing = min(named or crossings, key=lambda c: abs(c["d_along"] - rw_len * 0.55))
    X = crossing["point"]
    tw_ref = crossing["ref"] or "taxiway"
    # crossing direction: approach from the side of the taxiway with more length (its first point), move through X
    tw_line = crossing["line"]
    # pick the taxiway endpoint farther from the runway as the start
    far_pt = max([tw_line[0], tw_line[-1]], key=lambda p: dist(p, X))
    tw_brg = bearing(far_pt, X)
    hold_pt = destination(X, (tw_brg + 180) % 360, 75)   # hold line ~75 m from centerline
    start_pt = destination(hold_pt, (tw_brg + 180) % 360, 250)  # taxiing in from 250 m out
    entry_pt = destination(X, (tw_brg + 180) % 360, 30)  # runway edge
    exit_pt = destination(X, tw_brg, 30)
    beyond_pt = destination(X, tw_brg, 200)
    approach_start = destination(threshold, (rw_brg + 180) % 360, 4000)
    rollout_end = along(rw, min(rw_len - 100, max(crossing["d_along"] + 500, rw_len * 0.75)))
    rollout_poly = [threshold] + [p for p in rw[1:] if dist_along_to_point(rw, p) < dist_along_to_point(rw, rollout_end)] + [rollout_end]

    # --- timing (seconds) -------------------------------------------------------------------
    T_CLEAR_LAND, T_CROSS_CLR, T_ALERT, T_HOLD_SHORT = 0.0, 28.0, 28.0, 34.0
    V_APP, V_ROLL_AVG, V_TAXI = 75.0, 45.0, 5.0
    t_touch = T_CLEAR_LAND + 4000 / V_APP                      # ~53 s
    t_roll_end = t_touch + poly_len(rollout_poly) / V_ROLL_AVG
    t_land_at_x = t_touch + crossing["d_along"] / V_ROLL_AVG   # lander reaches the intersection
    d_start_to_hold = dist(start_pt, hold_pt)
    t_at_hold = T_CROSS_CLR + d_start_to_hold / V_TAXI
    t_enter = t_at_hold + dist(hold_pt, entry_pt) / V_TAXI
    t_exit = t_enter + dist(entry_pt, exit_pt) / V_TAXI
    t_clear = t_exit + dist(exit_pt, beyond_pt) / V_TAXI
    lander_window = [round(t_land_at_x - 12, 1), round(t_land_at_x + 8, 1)]
    crosser_window = [round(t_enter, 1), round(t_exit, 1)]
    overlap = [max(lander_window[0], crosser_window[0]), min(lander_window[1], crosser_window[1])]
    overlap = overlap if overlap[0] < overlap[1] else None

    lander_path = sample_path([approach_start, threshold], T_CLEAR_LAND, t_touch, 30) + \
                  sample_path(rollout_poly, t_touch, t_roll_end, 30)[1:]
    crosser_unresolved = sample_path([start_pt, hold_pt], T_CROSS_CLR, t_at_hold, 20) + \
                         sample_path([hold_pt, entry_pt, X, exit_pt, beyond_pt], t_at_hold, t_clear, 30)[1:]
    crosser_resolved = sample_path([start_pt, hold_pt], T_CROSS_CLR, t_at_hold, 20) + \
                       [{"t": round(t_clear + 60, 2), "p": hold_pt}]

    rw_num = " ".join({"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
                       "7": "seven", "8": "eight", "9": "niner"}[c] for c in str(num))
    side = {"L": " left", "R": " right", "C": " center"}.get(des[-1], "")
    rw_spoken = f"runway {rw_num}{side}"
    tw_spoken = " ".join(list(tw_ref.lower())) if len(tw_ref) <= 2 else tw_ref.lower()
    transmissions = [
        {"t": T_CLEAR_LAND, "speaker": "TWR", "text": f"sim two one two {rw_spoken} cleared to land wind two niner zero at one two",
         "parsed": {"role": "ATCO", "callsigns": ["sim two one two"], "commands": ["cleared to land"], "values": [rw_spoken, "wind two niner zero at one two"]},
         "actions": ["CLEARED_TO_LAND"]},
        {"t": 4.0, "speaker": "SIM212", "text": f"cleared to land {rw_spoken} sim two one two",
         "parsed": {"role": "PILOT", "callsigns": ["sim two one two"], "commands": ["cleared to land"], "values": [rw_spoken]},
         "actions": ["CLEARED_TO_LAND"]},
        {"t": T_CROSS_CLR, "speaker": "GND", "text": f"rescue seven cross {rw_spoken} at {tw_spoken}",
         "parsed": {"role": "ATCO", "callsigns": ["rescue seven"], "commands": ["cross"], "values": [rw_spoken, f"at {tw_spoken}"]},
         "actions": ["CROSS_RUNWAY"]},
        {"t": T_CROSS_CLR + 3, "speaker": "RESCUE7", "text": f"crossing {rw_spoken} at {tw_spoken} rescue seven",
         "parsed": {"role": "PILOT", "callsigns": ["rescue seven"], "commands": ["crossing"], "values": [rw_spoken, f"at {tw_spoken}"]},
         "actions": ["CROSS_RUNWAY"]},
    ]
    resolved_extra = [
        {"t": T_HOLD_SHORT, "speaker": "GND", "text": f"rescue seven hold short {rw_spoken} traffic on short final",
         "parsed": {"role": "ATCO", "callsigns": ["rescue seven"], "commands": ["hold short"], "values": [rw_spoken]},
         "actions": ["HOLD_SHORT"]},
        {"t": T_HOLD_SHORT + 3, "speaker": "RESCUE7", "text": f"holding short {rw_spoken} rescue seven",
         "parsed": {"role": "PILOT", "callsigns": ["rescue seven"], "commands": ["holding short"], "values": [rw_spoken]},
         "actions": ["HOLD_SHORT"]},
    ]

    scenario = {
        "airport": args.airport, "runway": des, "crossing_taxiway": tw_ref,
        "attribution": "Geometry © OpenStreetMap contributors (ODbL). Fictional traffic.",
        "center": [(threshold[0] + far_end[0]) / 2, (threshold[1] + far_end[1]) / 2],
        "runway_line": rw, "intersection": X, "hold_point": hold_pt,
        "alert": {
            "t": T_ALERT, "id": "w0001", "rule": "R1 crossing vs active landing",
            "text": f"POSSIBLE CONFLICT — {des}: SIM212 cleared to land vs RESCUE7 cleared to cross at {tw_ref}",
            "lookahead": {"lander_at_intersection": round(t_land_at_x, 1), "lander_window": lander_window,
                          "crosser_window": crosser_window, "overlap": overlap},
            "cites": ["JO 7110.65 3-1-3", "JO 7110.65 3-7-2"],
            "note": "Decision support only; the controller decides.",
        },
        "variants": {
            "unresolved": {"transmissions": transmissions,
                           "aircraft": [{"id": "SIM212", "kind": "airliner", "path": lander_path},
                                        {"id": "RESCUE7", "kind": "vehicle", "path": crosser_unresolved}]},
            "resolved": {"transmissions": transmissions + resolved_extra,
                         "aircraft": [{"id": "SIM212", "kind": "airliner", "path": lander_path},
                                      {"id": "RESCUE7", "kind": "vehicle", "path": crosser_resolved}]},
        },
        "duration": round(max(t_roll_end, t_clear) + 5, 1),
    }
    json.dump(scenario, open(args.out, "w"))
    print(f"runway {des}: {rw_len:.0f} m, heading {rw_brg:.0f}°; crossing at taxiway {tw_ref} "
          f"{crossing['d_along']:.0f} m from threshold; touchdown t={t_touch:.0f}s, lander at crossing t={t_land_at_x:.0f}s, "
          f"crosser on runway {crosser_window}; overlap {overlap}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
