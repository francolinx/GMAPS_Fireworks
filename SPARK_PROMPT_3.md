# Spark work package 3 — the LaGuardia reconstruction (paste into Claude Code on the Spark)

You are Claude Code on Franco's DGX Spark in the GMAPS repo (git pull first; the cloud session edits README/results/deck, you
own `viz/`, `docs/video/`, `docs/*.png`, `STATUS.md`; commit often with messages starting `viz:`). `CLAUDE.md` hard rules
hold: never read or use `data/splits/test.jsonl`; no keys in the repo; port 8000 is not yours. Keep the LoRA on :8001 (the live
panel calls it). Budget 75 minutes; push after each deliverable.

## Why this scenario

On March 22, 2026 at 23:37 EDT, Air Canada Express 8646 — **JAZZ 646**, a CRJ900, registration C-GNJZ, operated by Jazz
Aviation — landing on **runway 4 at LaGuardia** collided with **Rescue 35 ("Truck 1")**, an Oshkosh Striker 1500 Port Authority
ARFF vehicle that had been cleared to cross runway 4 at **taxiway D** while the aircraft was on a quarter-mile final. Both pilots,
Captain Antoine Forest and First Officer Mackenzie Gunther, were killed; 39 people went to hospital. The NTSB preliminary
report (DCA26MA161, April 23, 2026) gives the timeline below. This is exactly the failure GMAPS exists for: two valid
clearances on one runway, no cross-check. Replace the fictional SFO scenario with this one. **It is a reconstruction of a real
accident in which two people died: no crash animation, no sound effects, no blame.** The investigation is ongoing.

## NTSB preliminary timeline (use these times; t = seconds after 23:35:00 EDT)

| clock | t | event | source |
|---|---|---|---|
| 23:31:42 | −198 | ground emergency declared near Terminal B (an airliner after two rejected takeoffs); six ARFF vehicles + one PAPD car respond, gather at taxiways BB/D | NTSB prelim |
| 23:35:07 | 7 | Tower (LC) clears JZA646 to land runway 4; aircraft on 5-mile final, ~1,900 ft | NTSB prelim |
| 23:35:47 | 47 | Truck 7 tries to call tower; blocked by a simultaneous transmission | NTSB prelim |
| 23:36:21 | 81 | Truck 7 tries again; before ATC answers, Truck 1 takes over the call. Aircraft ~2.3 nm, ~650 ft | NTSB prelim |
| 23:36:44 | 104 | LC asks which vehicle needs to cross a runway. Aircraft ~1.5 nm, ~400 ft | NTSB prelim |
| 23:36:51 | 111 | Runway-entrance lights at 4/D illuminate. Aircraft ~1.2 nm, ~287 ft. Truck 1 stopped ~460 ft from the runway edge | NTSB prelim |
| 23:36:56 | 116 | Truck 1: "Truck 1 and company" (quoted); requests to cross runway 4 at D | NTSB prelim |
| 23:37:04 | 124 | **LC clears Truck 1 to cross runway 4 at D.** Aircraft ~130 ft AGL, ¼-mile final, ~4,400 ft from D | NTSB prelim |
| 23:37:07 | 127 | Truck 1 reads back and begins to move. Aircraft 87 ft, ~3,700 ft from D | NTSB prelim |
| 23:37:11 | 131 | Aircraft crosses the runway 4 threshold. Truck 1 10 kt, ~410 ft from the runway edge | NTSB prelim |
| 23:37:12 | 132 | LC gives a taxi instruction to another aircraft, then tells Truck 1 to stop (Truck 1 crossing taxiway AA). Aircraft 30 ft, 133 kt | NTSB prelim |
| 23:37:17 | 137 | Main-gear touchdown ~1,450 ft from D, 128 kt | NTSB prelim |
| 23:37:20 | 140 | LC tells Truck 1 to stop again; Truck 1 just over 100 ft from the runway at ~29 mph | NTSB prelim |
| 23:37:21 | 141 | Runway-entrance lights extinguish (by design, 2–3 s before the aircraft reaches the intersection) | NTSB prelim |
| 23:37:22 | 142 | Nose-gear touchdown ~400 ft from D, 106 kt. Truck 1 enters runway 4 at 30 mph | NTSB prelim |
| ~23:37:25 | ~145 | Collision at the intersection of runway 4 and taxiway D; last recorded ground speed 90 kt | NTSB prelim |

Facts also from the report: ASDE-X raised no alert (the trucks have no transponders and could not be tracked reliably); the
runway status lights worked as designed; two controllers were on duty and the LC was transmitting on both tower and ground.
Public radio quotes (press, not the report): "Frontier 4195, just stop there please. Stop, stop, stop, stop, Truck 1, stop,
stop, stop. Stop, Truck 1." The **exact wording of the landing and crossing clearances is not public** — use standard FAA
phraseology and mark those lines `wording: standard phraseology (reconstructed)` in the transcript panel; mark the quoted
ones `wording: as reported`.

## What to build

1. **Geometry.** `python3 viz/fetch_airport_osm.py KLGA viz/klga.geojson --bbox 40.760,-73.895,40.790,-73.850` (Overpass; the
   kumi mirror if the main server times out — see `viz/fetch_airport_osm.py`). Runway 4/22, taxiway D, taxiways BB and AA, the
   hold line at 4/D. Verify the runway and taxiway names against the FAA LGA airport diagram (public domain) before using them.
2. **Scenario `viz/scenario_lga_04.json`** built with `viz/build_scenario.py` (extend it if it only knows SFO): aircraft path = runway
   4 final approach course to the 4/D intersection, speeds from the table (133 kt at threshold, 128 at touchdown, 90 at D);
   Truck 1 path = from the staging point near BB/D, across AA, to the 4/D hold line and onto the runway, 10 kt → 30 mph, timed
   so it enters the runway at t=142 and reaches the intersection at t≈145. Labels: `JAZZ 646 — Air Canada Express 8646, CRJ900 C-GNJZ`
   and `TRUCK 1 — Rescue 35, Oshkosh Striker 1500, Port Authority ARFF`. Transcript lines (speaker, t, text, parsed record):
   - t=7 TWR → JAZZ 646: "jazz six four six runway four cleared to land" (standard phraseology, reconstructed)
   - t=10 JAZZ 646: "cleared to land runway four jazz six four six" (reconstructed read-back)
   - t=104 TWR: "which vehicle needs to cross the runway" (reconstructed)
   - t=116 TRUCK 1: "truck one and company request cross runway four at delta" ("truck one and company" as reported)
   - t=124 TWR → TRUCK 1: "truck one and company cross runway four at delta" (standard phraseology, reconstructed)
   - t=127 TRUCK 1: "cross runway four at delta truck one" (reconstructed read-back)
   - t=132 TWR: "frontier forty one ninety five just stop there please stop stop stop stop truck one stop stop stop" (as reported)
   - t=140 TWR: "stop truck one" (as reported)
   Parsed records must come from the real parser on :8001 (the live panel) and the scripted record; the ledger runs on the
   scripted record as now.
3. **Two modes, two clips (1440×900, 25 fps, 2× speed, headless Chromium, no audio):**
   - `docs/video/lga_04_asis_2x.mp4` — what the NTSB timeline records: both clearances parsed, no rule runs, the stop calls
     arrive at t=132 and t=140, Truck 1 enters the runway at t=142. **Freeze at t=142** (truck at the runway edge, aircraft
     on the roll) with the caption `23:37:22 — Truck 1 enters runway 4. NTSB DCA26MA161, preliminary.` Do not animate past it.
   - `docs/video/lga_04_gmaps_2x.mp4` — same radio. At **t=124**, the instant "cross runway four at delta" is parsed, the ledger
     holds `4: cleared to land JAZZ 646 (active, on short final)` and `4: cross at D TRUCK 1` → alert
     `POSSIBLE CONFLICT — RWY 4: JAZZ 646 cleared to land vs TRUCK 1 cleared to cross at D`, cites JO 7110.65 3-1-3 / 3-7-2,
     look-ahead: aircraft at D in ~21 s, truck at D in ~18 s. Caption: `Alert at 23:37:04 — 18 seconds before Truck 1 entered
     the runway. Whether that changes the outcome is for the NTSB to say. Decision support only; the controller decides.`
     Freeze there; do not play the collision.
   Both clips open with a 3-second title card: `LaGuardia, March 22, 2026 · reconstruction from the NTSB preliminary report
   DCA26MA161 · wording of most transmissions is not public and is reconstructed · investigation ongoing` and close with
   `In memory of Captain Antoine Forest and First Officer Mackenzie Gunther.`
4. **Stills** `docs/runway_monitor_lga_04_asis.png` (t=142) and `docs/runway_monitor_lga_04_gmaps.png` (t=124 alert), 1920×1200.
5. **STATUS.md** → "## LaGuardia reconstruction (Nov 2 pm)": what geometry was used, which lines are reconstructed vs reported,
   measured live-parser latencies, anything not done. Keep the SFO scenario files; the index page should default to LGA.

Order: geometry → scenario JSON with the real timeline → one screenshot to check the paths → live-panel check on one line →
record → stills → STATUS → push. If the Overpass fetch fails twice, build the runway/taxiway lines from the FAA diagram
coordinates by hand and say so in STATUS.md.
