# Spark work package 5 — last pass before 16:30 PT (paste into Claude Code on the Spark; 30 minutes, push every 10)

Same rules (`CLAUDE.md`; you own `viz/`, `docs/video/`, `docs/*.png`, `STATUS.md`; commit `viz:`; never touch `data/splits/test.jsonl`).
Keep :8001, :8002, :8004 and :8090 up — the live demo runs on them. Mentor feedback after watching the page:

1. **Don't stop at 23:37:04 in GMAPS mode.** Keep the alert banner up and let the scenario run on through the two "stop" calls
   to 23:37:22, then freeze there (truck at the runway edge; still no collision). The alert card stays red from :04 to :22 and
   its caption keeps the "8 s before the first stop, 18 s before the truck" line. The as-is mode is unchanged.
2. **Airport picker.** A dropdown in the top bar: `LaGuardia KLGA (reconstruction)` · `San Francisco KSFO (scripted)` ·
   plus two static diagrams with no traffic, just the OSM runways/taxiways and the runway labels, so the judges see the
   geometry pipeline is general: `Boston KBOS` and `Atlanta KATL` (`viz/fetch_airport_osm.py KBOS viz/kbos.geojson --bbox
   42.350,-71.050,42.385,-70.985` and `KATL … --bbox 33.615,-84.470,33.660,-84.390`; if Overpass is slow use the kumi mirror,
   if it fails twice skip that airport and say so in STATUS). KSFO loads `viz/index_sfo.html`'s scenario; the static ones show
   the map with a caption `geometry only — no scenario`.
3. **Accuracy card → the organizers' table format.** Replace the accuracy card (in the clips' closing cards and the page's
   `?view=results` if there is one) with `docs/leaderboard.png` (the cloud session is pushing it now: System | Full record |
   Clearance-state | vs base | cost, our rows highlighted in green). Same card in both clips.
4. **Live panel label.** Under "DGX SPARK · LIVE PARSER" add one line: `best model on the benchmark: Nemotron-30B + GMAPS LoRA, 70.1%
   (Fireworks) · running here: Qwen3-8B + GMAPS LoRA, 59.7%/55.2%` so nobody thinks the live model is the headline model.
5. **Economics card:** replace the "Audio leaves the building: yes/no" row with `Audio stays in the building` ✓ (green, Spark)
   / ✗ (red, hosted and API) — no yes/no wording anywhere.
6. Re-record **only the GMAPS clip** (`docs/video/lga_04_gmaps_2x.mp4`) with 1 and 3–5 applied; the as-is clip stays. Push.
   If time remains, a 10 s clip of the airport picker switching KLGA → KSFO → KBOS (`docs/video/airport_picker_2x.mp4`).
7. STATUS.md: "## Package 5" — what landed, what didn't.
