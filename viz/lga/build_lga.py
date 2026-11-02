#!/usr/bin/env python3
"""LaGuardia runway 4 / taxiway D reconstruction (March 22, 2026) for the runway monitor.

  python3 viz/lga/build_lga.py viz/klga.geojson viz/scenario_lga_04.json

Positions come straight from the NTSB preliminary report DCA26MA161 (distance-to-D and distance-to-runway-edge at the
report's clock times), interpolated linearly in time on the OSM geometry: JAZZ 646 on the runway 4 extended centreline and
then the OSM runway line; TRUCK 1 on the OSM taxiway D centreline (ways 1102894296 + 1361480359 + 5783993, joined west→east).
t = seconds after 23:35:00 EDT. Collision ≈ t=144 (report: nose-gear touchdown at 23:37:22 was "roughly 2 seconds before").
Transcript lines and their scripted records come from viz/lga/lga_transmissions.jsonl. Geometry © OpenStreetMap (ODbL).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "bench"))
from build_scenario import along, bearing, destination, dist_along_to_point, poly_len  # noqa: E402
from normalize import actions_for  # noqa: E402

FT = 0.3048
NM = 1852.0
X = [-73.878884, 40.775525]          # OSM D × 04/22 (NTSB est. collision point 40.775521, -73.878882)
RWY_HALF_WIDTH_FT = 75.0             # LGA runway 4/22 is 150 ft wide

# JAZZ 646: distance to taxiway D (ft) at report times. t=7 is "5-mile final" (from the threshold).
THR_TO_D_FT = None  # filled from OSM
AC_KEYS = lambda thr: [(7, 5 * NM / FT + thr), (47, 3.7 * NM / FT), (81, 2.3 * NM / FT), (104, 1.5 * NM / FT),
                       (111, 1.2 * NM / FT), (124, 4400), (127, 3700), (131, thr), (132, 2550), (137, 1450),
                       (142, 400), (144, 0), (146, -300)]
# TRUCK 1: distance to the runway-4 edge along D (ft). Before 23:36:44 it is at the BB/D gathering point.
TR_KEYS = [(0, 600), (104, 600), (111, 460), (127, 460), (131, 410), (137, 200), (140, 100), (142, 0),
           (144, -RWY_HALF_WIDTH_FT), (146, -RWY_HALF_WIDTH_FT - 40)]


def interp(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return keys[-1][1]


def main():
    geo, out = sys.argv[1], sys.argv[2]
    F = json.load(open(geo))["features"]
    W = {f["properties"].get("osm_id"): f["geometry"]["coordinates"] for f in F}
    rw = [f for f in F if f["properties"].get("kind") == "runway" and f["properties"].get("ref") == "04/22"][0]["geometry"]["coordinates"]
    rw = rw[::-1] if rw[0][1] > rw[-1][1] else rw            # threshold 4 (south-west end) first
    thr = rw[0]
    sX_rw = dist_along_to_point(rw, X)
    thr_ft = sX_rw / FT
    brg = bearing(rw[0], rw[-1])
    D = W[1102894296] + W[1361480359][::-1][1:] + W[5783993][::-1][1:]
    sX_d = dist_along_to_point(D, X)

    def ac_pos(d_ft):
        d = d_ft * FT
        if d <= sX_rw:
            return along(rw, sX_rw - d)
        return destination(thr, (brg + 180) % 360, d - sX_rw)

    def tr_pos(edge_ft):
        return along(D, sX_d - (edge_ft + RWY_HALF_WIDTH_FT) * FT)

    ts = sorted(set([i * 2.0 for i in range(0, 52)] + [x * 0.5 for x in range(200, 293)]))
    ac_keys = AC_KEYS(thr_ft)
    lander = [{"t": t, "p": ac_pos(interp(ac_keys, t))} for t in ts if t >= 0]
    truck = [{"t": t, "p": tr_pos(interp(TR_KEYS, t))} for t in ts]
    hold = along(D, sX_d - 285 * FT)  # OSM holding position 3060033678 on D

    lines = [json.loads(l) for l in open(os.path.join(HERE, "lga_transmissions.jsonl"), encoding="utf-8")]
    spk = {"TWR": "TWR", "JAZZ646": "JAZZ646", "TRUCK1": "TRUCK1"}
    tx = []
    for ln in lines:
        rec = {"role": ln["role"], "callsigns": ln["gold"]["callsign"], "commands": ln["gold"]["command"], "values": ln["gold"]["value"]}
        acts = sorted(set(actions_for(ln["gold"]["command"])))
        if "request" in " ".join(ln["gold"]["command"]):
            acts = ["REQUEST_CROSS"]  # a request is not an authorization; the ledger only takes ATCO clearances anyway
        elif ln["role"] != "ATCO" and "cross" in " ".join(ln["gold"]["command"]):
            acts = ["CROSS_RUNWAY"]  # read-back chip, as on the SFO page
        tx.append({"t": float(ln["t"]), "id": ln["id"], "speaker": spk[ln["speaker_label"]], "text": ln["text"], "parsed": rec,
                   "actions": acts, "wording": ln["wording"], "facility": ln["facility"].lower()})

    ac_at_d = 144.0
    scenario = {
        "airport": "KLGA", "runway": "4", "crossing_taxiway": "D", "clock0": [23, 35, 0],
        "title": "LaGuardia, March 22, 2026",
        "attribution": "Geometry © OpenStreetMap contributors (ODbL). Timeline: NTSB preliminary report DCA26MA161.",
        "geo": "klga.geojson", "center": [X[0] - 0.0036, X[1] - 0.0040], "zoom": 14.75,
        "runway_line": rw, "intersection": X, "hold_point": hold, "crossing_path": D,
        "actors": {"JAZZ646": "JAZZ 646 — Air Canada Express 8646, CRJ900 C-GNJZ",
                   "TRUCK1": "TRUCK 1 — Rescue 35, Oshkosh Striker 1500, Port Authority ARFF"},
        "actor_short": {"JAZZ646": "JAZZ 646", "TRUCK1": "TRUCK 1", "TWR": "LGA TOWER"},
        "alert": {"t": 124.0, "id": "w0001", "rule": "R1 crossing vs active landing",
                  "text": "POSSIBLE CONFLICT — RWY 4: JAZZ 646 cleared to land vs TRUCK 1 cleared to cross at D",
                  "lookahead": {"lander_at_intersection": ac_at_d, "lander_window": [ac_at_d - 6, ac_at_d + 3],
                                "crosser_window": [142.0, 146.0], "overlap": [142.0, 146.0],
                                "lander_to_d_s": 20, "truck_to_runway_s": 18},
                  "cites": ["JO 7110.65 3-1-3", "JO 7110.65 3-7-2"],
                  "note": "Decision support only; the controller decides."},
        "freeze": {"asis": 142.0, "gmaps": 124.0},
        "captions": {"asis": "23:37:22 — Truck 1 enters runway 4. NTSB DCA26MA161, preliminary.",
                     "gmaps": "Alert at 23:37:04 — 18 seconds before Truck 1 entered the runway. Whether that changes the outcome is for the NTSB to say. Decision support only; the controller decides."},
        "cards": {"open": ["LaGuardia, March 22, 2026",
                           "Reconstruction from the NTSB preliminary report DCA26MA161",
                           "Wording of most transmissions is not public and is reconstructed · names and quoted audio from press reports",
                           "Investigation ongoing"],
                  "close": ["In memory of Captain Antoine Forest and First Officer Mackenzie Gunther."]},
        "events": [{"t": 111, "text": "runway-entrance lights at 4/D on"}, {"t": 131, "text": "JAZZ 646 over the threshold"},
                   {"t": 137, "text": "main-gear touchdown, 1,450 ft from D"}, {"t": 141, "text": "runway-entrance lights off (by design)"},
                   {"t": 142, "text": "nose-gear touchdown 400 ft from D · Truck 1 enters runway 4"}],
        "variants": {v: {"transmissions": tx,
                         "aircraft": [{"id": "JAZZ646", "kind": "airliner", "label": "JAZZ 646 — Air Canada Express 8646", "path": lander},
                                      {"id": "TRUCK1", "kind": "vehicle", "label": "TRUCK 1 — Rescue 35, PA ARFF", "path": truck}]}
                     for v in ("unresolved", "resolved")},
        "duration": 146.0,
    }
    json.dump(scenario, open(out, "w"))
    print(f"rwy 4 heading {brg:.0f}°, threshold→D {thr_ft:.0f} ft (report ≈2,775); D centreline at {sX_d / FT:.0f} ft along D; "
          f"hold line 285 ft before centreline (OSM); {len(tx)} transmissions → {out}")


if __name__ == "__main__":
    main()
