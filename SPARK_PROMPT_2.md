# Spark work package 2 — demo video + live DGX Spark panel (paste into Claude Code on the Spark)

You are Claude Code on Franco's DGX Spark in `~/gmaps_fireworks` (git pull first; the cloud session is editing README/results,
so **only touch `viz/`, `docs/video/`, `docs/*.png`, `scripts/08_*`, `STATUS.md`** and commit/push often with messages that start
with `viz:`). Hard rules from `CLAUDE.md` still apply: never read or use `data/splits/test.jsonl`; no keys in the repo; port 8000 is
not yours. Budget: 75 minutes. Deliverables are files in `docs/video/`, pushed.

## What is wrong with the current demo (Franco watched `docs/video/gmaps_fireworks_120s.mp4`)

1. **RESCUE7 is drawn off the taxiway.** The fire truck must move *on* the OSM taxiway geometry (`viz/ksfo.geojson`, taxiway E
   to the 28L intersection in `viz/scenario_sfo_sim1.json`), not on an offset straight line. Snap its path to the taxiway
   centreline polyline and the hold-short point (`hold_point`); same for the aircraft on the runway centreline (`runway_line`).
2. **Name the actors on screen.** Persistent labels next to the icons and in the transcript panel:
   `RESCUE 7 — ARFF fire truck` and the aircraft as a flight with a number, e.g. `MPL212 — Maple Air 212, short final 28L`
   (fictional airline; keep the callsign spoken in the transcript consistent: "maple two one two"). Update the scenario JSON
   (transcripts, parsed callsigns, alert text) so the spoken words, the parsed JSON and the labels all match.
3. **As-is first, then GMAPS.** Record two clips from the same scenario:
   - `docs/video/sfo_28l_asis_2x.mp4` — variant *unresolved*: both clearances are read on the radio ("cleared to land 28L",
     "cross 28L at E"), the transcript → parsed record panel shows each transmission being parsed **but no rule runs**;
     the truck enters the runway while the aircraft is on short final; freeze on the overlap at the intersection with a red
     caption "AS-IS: two valid clearances, nobody cross-checked them" (no explosion, no "simulated" caption).
   - `docs/video/sfo_28l_gmaps_2x.mp4` — variant *resolved*: same radio, GMAPS alert fires at t=28 s
     ("POSSIBLE CONFLICT — 28L: MPL212 cleared to land vs RESCUE 7 cleared to cross at E", cites JO 7110.65 3-1-3 / 3-7-2),
     GND issues hold short, RESCUE 7 stops at the hold line, aircraft lands; green caption "Decision support only; the
     controller decides."
   Both 1440×900, 25 fps, 2× speed, headless Chromium (Playwright is installed; `viz/README.md` has the http.server command).
4. **Live "DGX Spark" side panel.** Add a right-hand panel to `viz/index.html` that shows the parser running on this machine,
   for real: for every transmission the page POSTs the text to a tiny local proxy `viz/live_server.py` (FastAPI or
   http.server, port 8090) which calls the vLLM server on **:8001** serving `runs/qwen3-8b-atc/merged` (start it with
   `scripts/06_serve_vllm.sh ... student 8001` if it is not up; `curl :8001/v1/models` to check) with the exact system prompt in
   `prompts/system.txt`, 0-shot, `temperature 0`, `max_tokens 300`, `chat_template_kwargs: {"enable_thinking": false}`.
   The panel prints: model name, `GB10 · bf16 · vLLM`, the returned JSON, latency in ms per call, tokens in/out, and a running
   GPU line from `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader` polled every 2 s by the proxy.
   If the recording is made with the panel live, the latencies in the clip are real; say so in a caption ("live on DGX Spark,
   Qwen3-8B + GMAPS LoRA, 0-shot").
5. **Still frames.** Save `docs/runway_monitor_sfo_28l_asis.png` (the freeze frame) and `docs/runway_monitor_sfo_28l_gmaps.png`
   (alert + hold short) at 1920×1200.

## Order of work (stop at 75 min, push whatever is done)

1. `git pull`; rename SIM212 → MPL212 / "maple two one two" in `viz/scenario_sfo_sim1.json` (both variants, alert text,
   parsed callsigns). Fix the truck/aircraft paths to the OSM geometry. Add the labels. Check in a browser screenshot.
2. `viz/live_server.py` + the side panel. Verify with one transmission that the JSON and latency come from :8001.
3. Record the two clips and the two stills (`scripts/08_record_viz.sh` if it exists; otherwise a short Playwright script in
   `viz/record.py`). Watch the first 5 s of each clip (`ffmpeg -ss 0 -t 5 -i … frame%03d.png`, open a frame) before pushing.
4. Append to `STATUS.md` under "## Demo (Nov 2 pm)": what was recorded, the measured per-call latency range from the live panel,
   and anything that did not get done. `git add viz docs STATUS.md && git commit -m "viz: …" && git push`.

Do not re-cut `docs/video/gmaps_fireworks_120s.mp4`; the cloud session re-cuts the 120 s video from your two clips.
