# Spark work package 4 — judges' notes on the demo (paste into Claude Code on the Spark after package 3 is pushed)

Same rules as package 3 (`CLAUDE.md`; you own `viz/`, `docs/video/`, `docs/*.png`, `STATUS.md`; commit `viz:` often; never
touch `data/splits/test.jsonl`; keep the LoRA on :8001). Mentors watched the SFO clips and wrote: *"clear inputs and outputs,
check marks and X, reasoning clearly why for the human in the loop (highly visual example)"*. Apply all of this to the
**LaGuardia** scenario from package 3 (`viz/scenario_lga_04.json`) and re-record the two clips. Budget 75 minutes.

## 1. Who is talking — every transmission, every time
A large speaker badge on every transcript card and on a **"NOW ON FREQUENCY"** strip across the top of the map, with a colour per
speaker that is used everywhere (card border, map label, log, timeline):
- `LGA TOWER` (controller) — cyan
- `JAZZ 646 · Air Canada Express 8646 · CRJ900` — white
- `TRUCK 1 · Rescue 35 · Port Authority ARFF` — amber
The strip shows: speaker badge · the spoken words in quotes (large) · `wording: as reported` / `reconstructed` · the wall
clock `23:37:04`. It stays up ~4 s of scenario time and animates in when a new transmission starts. Nobody watching should
ever have to guess who said what.

## 2. Input → output, with a check mark and the "why"
Each transcript card becomes two columns: **INPUT** (the radio text) → **OUTPUT** (the parsed record from the live parser on
:8001, pretty-printed: role / callsigns / commands / values). Under the output, one line per field with ✓ or ✗ against the
scripted gold record in the scenario JSON (`gold` in `viz/lga/lga_transmissions.jsonl` has the same lines), and one
plain-language **why** line the ledger would show a human: e.g. `✓ "cross" + "runway four" → CROSS_RUNWAY on RWY 4 at D → checks
against active landing clearance` or `✗ callsign "truck one and company" read as "truck one" — same vehicle, no ledger
effect`. The ledger's rule firing shows its own why: `RWY 4: landing clearance JAZZ 646 active (short final, 21 s to D) + crossing
clearance TRUCK 1 at D (18 s to runway) → overlap → ALERT (JO 7110.65 3-1-3, 3-7-2)`.

## 3. The clock and the "who stepped in when" timeline
- A wall clock `23:3m:ss EDT` (t + 23:35:00) always visible, large, bottom-left, next to the scenario time.
- A **timeline bar** across the bottom of the map from 23:35:00 to 23:37:30 with a moving cursor and fixed markers:
  - `23:35:07 landing clearance` · `23:37:04 crossing clearance` · `23:37:12 controller: "stop"` · `23:37:20 controller: "stop"` ·
    `23:37:22 Truck 1 enters runway 4` (red)
  - one marker per **model** for the moment its parsed records first put both clearances on runway 4 in the ledger, i.e. when
    GMAPS *with that parser* would have alerted. Compute it from real outputs, not by hand:
    `viz/lga/model_outputs/<arm>.jsonl` — the cloud session is producing these for the Fireworks-hosted arms
    (Nemotron-30B LoRA, Nemotron-30B base, Lightning LoRA, Lightning base; files appear in the repo within ~20 min — `git pull`);
    you produce them on the Spark for `qwen3-8b-base` (5-shot, :8001 base is not up — serve `Qwen/Qwen3-8B` on :8003 with
    `enable_thinking:false`, 5-shot from train) and `atc-qwen3-8b` (0-shot, :8001), and for `nemotron-lightning-3.5-30b` base on :8002
    (5-shot, `reasoning_effort: none`). Use `bench/infer.py --split viz/lga/lga_transmissions.jsonl --fewshot N --out viz/lga/model_outputs/<arm>.jsonl`.
    Run each file through the ledger (`viz/import_outputs.py` or the page's ledger code) and record, per arm: the first t at
    which the ledger holds an active `CLEARED_TO_LAND` on runway 4 **and** a `CROSS_RUNWAY` on runway 4 → `alert_t`, or `never`
    (e.g. a base model that drops the callsign or reads "cross" as something else may never trigger). Write
    `viz/lga/stepped_in.json`: `{arm: {"alert_t": 124 | null, "clock": "23:37:04", "lead_over_controller_s": 8, "lead_over_truck_s": 18}}`.
  - Timeline legend ("KEY"): `★ GMAPS + Nemotron-30B LoRA (ours)`, `☆ GMAPS + Qwen3-8B LoRA (ours)`, `○ GMAPS + off-the-shelf
    Qwen3-8B`, `○ GMAPS + off-the-shelf Nemotron-30B`, `▲ controller`, `■ Truck 1 on runway`. Each with its clock time and
    "x s before the truck entered the runway" or "never alerted". This is the slide the judges asked for: how early ours
    stepped in vs the controller vs the non-fine-tuned model.
- Caption under the bar in the GMAPS clip: `Alert at 23:37:04 — 8 s before the first "stop", 18 s before Truck 1 entered runway 4.
  Whether that changes the outcome is for the NTSB to say.`

## 4. Three full-screen cards (3 s each) inside the clips, after the freeze
1. **Cost** — per 1,000 transmissions, from `results/test/scores.md`: Claude Opus 5.5 $9.92 · GPT-6.1 Terra Pro $5.01 · GPT-5.5 $10.40 ·
   **Nemotron-30B + LoRA $0.22** · **Qwen3-8B + LoRA $0.09** · on the DGX Spark ≈ $0 marginal. One line: `a hub does ~10,000
   transmissions a day → Opus ≈ $99/day, ours ≈ $2/day or $0`.
2. **Speed** — p50 per transmission: Opus 5.3 s · GPT-6.1 4.1 s · GPT-5.5 3.7 s · Qwen3-8B LoRA hosted 0.70 s · on the Spark: Qwen3-8B bf16
   3.0 s, Nemotron-3.5-Lightning NVFP4 **1.5 s** (measured in this session — use the real numbers from `STATUS.md`).
3. **Accuracy** — the leaderboard, top 6 rows of `docs/leaderboard.md` (Nemotron-30B LoRA 70.1 · Opus 67.4 · Lightning LoRA 60.4 · Qwen
   LoRA 59.7 · GPT-6.1 56.2 · …), with `tie with Opus (p = 0.30)` under the first row. If `git pull` brings 3-epoch rows, use those.

## 5. Two side screens (also exported as stills)
- **LOG** — `docs/runway_monitor_lga_log.png`: the historical input → output log, one row per transmission: clock · speaker badge ·
  input text · output record (compact) · ✓/✗ · latency ms · a small coloured dot per output (green = matches gold, amber = differs,
  no ledger effect, red = differs, ledger-visible). Same data the panel already has; make it a dedicated view (`?view=log`).
- **SPARK** — `docs/runway_monitor_lga_spark.png`: the DGX Spark panel as its own view (`?view=spark`): model name, GB10 · bf16 ·
  vLLM, a **live GPU-utilisation sparkline** (poll `nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader` every second
  in `viz/live_server.py`; it must visibly rise during a call), per-call latency bars, tokens in/out, calls so far, and the
  three model endpoints (:8001 LoRA, :8002 Lightning, :8003 base) with a green/red up indicator. Record a 15 s clip of it under
  load (`docs/video/lga_spark_panel_2x.mp4`) — send the eight LGA lines through all three endpoints while recording.

## 6. Re-record and push
`docs/video/lga_04_asis_2x.mp4` and `docs/video/lga_04_gmaps_2x.mp4` with everything above; stills for the alert, the freeze, the
log and the Spark view; `STATUS.md` → "## Package 4" with what was done, the per-arm `alert_t` table and the measured
latencies/utilisation. Push after each deliverable. The cloud session re-cuts the 120 s video from your clips.
