# STATUS — Spark run hand-off

_(Claude Code: overwrite this file as phases complete. Numbers only from `bench/score.py` / `08_latency_bench.py` output. No keys.)_

## Run summary
- started (UTC): 2026-11-01T02:36Z
- machine: spark-6771 — see `results/env_check.txt`
- phases completed: 0 1 2 3 4 5 6 7 8 — all ran; deviations: 1 epoch instead of 2, Nemotron-Nano student skipped, viz on :8081, pseudo cap 3000/source

## Data
- ATCO2 split verified against committed hash: **yes** (8660e6de…; train 504 / dev 85 / test 288). Action table OTHER = 5 spans (≈0.6 %).
- external: uwb_atcc kept 12840 / 14113 (leak_dropped 1, dup 252), atcosim kept 7398 / 9539 (leak_dropped 1, dup 1879)
- synthetic: us_train 3000, us_stress 300 (regenerated; sha256 matches data/synthetic/us_stress.sha256)
- pseudo-labels: teacher = local vLLM `nemotron-3-nano-30b-a3b-nvfp4` (thinking off, 8-shot, json mode); keep rate uwb **73.6 %** (5889 / 8000, capped with --limit 8000), atcosim **81.7 %** (6047 / 7398; drops: empty 747, unknown_action 533, span_not_in_text 71)
- training mix: **9478** examples (gold 489 unique ×2 = 978, synthetic 2500, pseudo 6000 = 3000 uwb + 3000 atcosim). `--max-pseudo` is a **per-source** cap; PLAN's 6000 gave 15367 rows (> the 6–10k target), so phase 3 used `--max-pseudo 3000`. dev 85.

## Fine-tunes
| run | base | examples | epochs | train loss | eval loss | wall time | merged? |
|---|---|---|---|---|---|---|---|
| qwen3-8b-atc | Qwen/Qwen3-8B | 9478 | **1** | 0.170 | 0.208 (step 50) → **0.123** (step 593) | 124 min | yes (`runs/qwen3-8b-atc/merged`, bf16, 16 GB) |
| nemotron-nano-8b-atc | nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | — | — | — | — | — | not run (no time left after 8B; Monday) |

Fine-tune notes: TRL + PEFT in `nvcr.io/nvidia/pytorch:25.11-py3` (container `atc-train`; unsloth not installed), LoRA r16/α32 on all proj, lr 2e-4 cosine, bsz 8×2, max-seq 1024. Measured 1.27 samples/s → PLAN's 2 epochs would be ~4.2 h, so **1 epoch**. Loss includes prompt tokens (no response-only masking without unsloth). Container stack pinned to transformers 4.57.1 / trl 0.24.0 / peft 0.17.1 (TRL 1.17 + container torch 2.10a: chunked-loss dtype crash; peft 0.21 rejects container torchao 0.14 → torchao removed in the container). `05_finetune_unsloth.py` patched for TRL ≥1 API (processing_class, warmup). Logs: `results/train_log_qwen3-8b-atc.json`, `results/train_log_smoke.json`.

## Dev results (paste `results/dev/scores.md` tables)

### dev (ATCO2 gold, training airports — NOT the test set)
| arm | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B base, 5-shot (thinking off) | 100.0% | 90.0% | 54.4% | 44.9% | 77.9% | 83.9% | 58.2% | 42.4% | 2792 | 3749 |
| atc-qwen3-8b LoRA, 0-shot | 100.0% | 93.8% | 69.8% | 73.5% | 85.7% | 93.5% | 88.1% | 70.6% | 2740 | 3718 |

(n=85; runway-critical n=31. Latency = client wall clock at concurrency 8, vLLM on the Spark.)

### synthetic US stress
| arm | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B base, 5-shot (thinking off) | 100.0% | 81.8% | 82.4% | 60.6% | 97.2% | 100.0% | 62.7% | 47.3% | 2969 | 3932 |
| atc-qwen3-8b LoRA, 0-shot | 100.0% | 97.2% | 99.4% | 96.1% | 100.0% | 100.0% | 99.3% | 96.3% | 2956 | 3967 |

(n=300; runway-critical n=184. Caveat: the fine-tune trained on 2500 rows from the same synthetic generator, so stress is in-distribution for it — not evidence of US generalisation.)

## Latency (vLLM on Spark, localhost)
| concurrency | p50 ms | p95 ms | rps |
|---|---|---|---|
| 1 | 3020 | 3899 | 0.33 |
| 4 | 2930 | 3735 | 1.30 |
| 16 | 3034 | 3916 | 4.58 |

`atc-qwen3-8b` (bf16 merged) on vLLM v0.27.1, localhost, n=85 dev rows per level, 5-shot prompt (script default), 0 errors. `results/latency_spark_local.json`.
**Not sub-second:** bf16 8B decode on the GB10 is bandwidth-bound (~16 GB weights / 273 GB/s), so per-request latency is ~3 s regardless of concurrency. README's "sub-second" claim needs FP8/NVFP4 serving, a 4B student, or a 0-shot prompt — measure before claiming it.

## Visualization
- `viz/index.html` served on **:8081** (8080 is taken by `openshell-gateway` on this machine) — **ok**. Headless Chrome check (CDP): page + MapLibre load with no JS errors; 28L conflict inactive at t=27.5, active + banner at t=30 (alert t=28); resolved variant ends with "CONFLICT CLEARED", RESCUE7 at the hold point (0 m). Same check passes for 01R.
- scenario(s) built: `scenario_sfo_sim1.json` (28L, TWY E; rebuilt from refreshed OSM — 8 runways, 257 taxiways, 86 holding positions) and `scenario_sfo_01r.json` (01R, TWY F; open with `?scenario=scenario_sfo_01r.json`). "parsed" blocks are still the hand-written ones (not model output) — Monday wires the final model in.

## Problems / open questions for Monday
- Dev few-shot leakage: `bench/infer.py` takes shots from the **first N dev rows**, and those rows are also scored, so the 5-shot base arm is slightly flattered on dev. On test this does not apply (shots from dev, scored on test).
- `bench/infer.py` defaults `--split` to `data/splits/test.jsonl` — every call today passed `--split` explicitly. Consider changing the default before Monday.
- `scripts/07_eval_dev.sh` had no way to disable Qwen3 thinking; added optional `EXTRA` passthrough (used for both arms today).
- Monday: Nemotron-Nano-8B student not trained; Fireworks SFT on `data/sft/mix_train.jsonl` (9478 rows) is the planned final run. If retraining on the Spark, use response-only loss (unsloth or TRL completion-only) and consider 2 epochs (~4 h at measured speed).
- Phase 0: host has no torch; data scripts run in in-repo `.venv` (datasets/pyarrow/hf_hub); fine-tune runs in `nvcr.io/nvidia/pytorch:25.11-py3`. No teacher API key set → local vLLM teacher on :8002.
- Phase 0: SSD teacher folders are `reasoning/nemotron-3-nano-30b-a3b-nvfp4` and `reasoning/qwen3.5-35b-a3b-fp8` (not the names in CLAUDE.md). Port 8080 is taken by `openshell-gateway` → viz served on another port.

## Left running
- vLLM `atc-qwen3-8b` on :8001 (container `vllm-atc-qwen3-8b`): **yes** — `BASE_URL=http://<spark>:8001/v1`, pass `"chat_template_kwargs":{"enable_thinking":false}`
- viz static server on :8081 (`python3 -m http.server`, from `viz/`): **yes**
- container `atc-train` (pytorch 25.11 + pinned TRL stack, idle, `sleep infinity`): yes — `docker rm -f atc-train` to free it
- teacher `vllm-teacher` on :8002: stopped. Port 8000 untouched.

## Lightning 3.5 on the Spark (Nov 2 pm)
- Model: `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` (21.6 GB, 52 shards) at `~/ssd/GB10_ARSENAL/models/reasoning/nemotron-3.5-lightning-30b-a3b-nvfp4` — the external SSD is not mounted at `/mnt/hackssd`, so this is the local-disk copy. The `-DSpark` repo is only the 1.35 GB speculative-decoding drafter (no tokenizer, can't be served alone) and was **not** used: no speculative decoding, which keeps it the under-cap configuration.
- Served: `scripts/06_serve_vllm.sh <dir> nemotron-lightning-3.5-30b 8002 --max-model-len 4096 --moe-backend marlin --kv-cache-dtype fp8 --enable-prefix-caching --mamba-backend flashinfer --mamba-cache-mode align --reasoning-parser nemotron_v3` (vLLM v0.27.1, GPU_UTIL 0.55).
- Request: 5-shot (shots from `train.jsonl`), `max_tokens 1500`, `{"reasoning_effort":"none"}` → clean JSON, no reasoning text, ~40 output tokens/segment. Concurrency 4.
- **Dev (n=85):** JSON valid 100.0% · Callsign F1 90.4% · Cmd span F1 60.8% · Value F1 40.6% · Action F1 94.6% · Runway-critical exact 100.0% (n=29) · Role acc 65.7% · **Full record exact 58.8%**
- **Latency on the Spark:** p50 **1518 ms**, p95 **1977 ms** per transmission (at concurrency 4).
- Files: `results/dev/nemotron-lightning-3.5_spark_fs5.preds.jsonl`, `results/dev/nemotron-lightning-3.5_spark_fs5.dev.scores.json`. Test split not touched.

## Demo (Nov 2 pm)
- **Recorded** (headless Chromium via `viz/record.py`, 1440×900, 25 fps H.264, page at 2×, live panel on):
  - `docs/video/sfo_28l_asis_2x.mp4` (54 s): `?mode=asis&variant=unresolved&freeze=98`. Both clearances are read and parsed, chips say "no rule run", no alert. RESCUE 7 enters 28L at E while MPL212 rolls through the intersection, and the clip freezes at t=98 s on the overlap with the red caption "AS-IS: two valid clearances, nobody cross-checked them".
  - `docs/video/sfo_28l_gmaps_2x.mp4` (63 s): `?mode=gmaps&variant=resolved`. The GMAPS alert fires at t=28 s ("POSSIBLE CONFLICT — 28L: MPL212 cleared to land vs RESCUE 7 cleared to cross at E", JO 7110.65 3-1-3 / 3-7-2). GND issues hold short at 34 s, RESCUE 7 stops at the hold line, MPL212 lands, and the green caption reads "Decision support only; the controller decides."
  - Stills at 1920×1200: `docs/runway_monitor_sfo_28l_asis.png` (freeze frame) and `docs/runway_monitor_sfo_28l_gmaps.png` (t=60 s, conflict cleared and holding short).
- **Geometry fix:** `viz/build_scenario.py` now builds RESCUE 7's path from the OSM polylines: the last 250 m of TWY F, then TWY E (way 23718372). It stops at the **real OSM holding position on E**, 80 m before the 28L centreline (way node 10038658994). In the as-is run it crosses and stops 119 m past 28L, short of 28R (E crosses 28R 244 m further on). The truck's speed (7.0 m/s) is solved so it reaches the centreline at t≈97.6 s, as MPL212 arrives (98.1 s). MPL212 flies the extended centreline, then follows the OSM runway line.
- **Names:** SIM212 → `MPL212 — Maple Air 212, short final 28L` / "maple two one two" in the transcripts, parsed callsigns, alert text, map labels and transcript speakers. `RESCUE 7 — ARFF fire truck`. Only the text changed; the transmissions are otherwise identical to the earlier build. `scenario_sfo_01r.json` was **not** rebuilt and still uses SIM212.
- **Live DGX Spark panel:** `viz/live_server.py` (stdlib, :8090) serves `viz/`. It POSTs each transmission to vLLM :8001 (`runs/qwen3-8b-atc/merged`, served as `student`, GPU_UTIL 0.25) using `prompts/system.txt` and `bench/make_sft.user_message`, 0-shot, temp 0, max_tokens 300, enable_thinking false. It polls `nvidia-smi` every 2 s. On GB10, `memory.used` is `[N/A]` (unified memory), so the panel shows the summed per-process GPU memory instead. Open with `http://<spark>:8090/?live=1`.
- **Measured per-call latency (live panel, during recording): 2.7–3.7 s per transmission**, median ≈3.0 s, about 385 tokens in and 35–49 out. Lightning was idle on :8002 alongside. The first call after a pause is the slowest (~3.7 s).
- **Live vs scripted record:** the live model matches the scripted record on the clearance-to-land pair and the "holding short" readback. It differs on "at e" (model: `"e"`) and adds "traffic on short final" as a value. The panel shows "≠ differs from the scripted record" for those, as recorded. The map and conflict engine still run on the scripted records.
- **Not done:** the 120 s video was not re-cut (by design; the cloud session does that). The old `sfo_28l_{unresolved,resolved}_2x.mp4` were left in place. The 01R scenario was not rebuilt.
- **Left running:** `vllm-student` :8001, `vllm-nemotron-lightning-3.5-30b` :8002, `viz/live_server.py` :8090 (`pkill -f viz/live_server.py`).

## LaGuardia reconstruction (Nov 2 pm)
- **Sources checked:** NTSB preliminary report DCA26MA161 (PDF, 15 pp) and the NTSB investigation page (updated 23 April 2026). Every time, distance, altitude, speed and name in SPARK_PROMPT_3's table was checked against them. **Differences, report value used:**
  1. Collision ≈ **23:37:24 (t≈144)**, not ~23:37:25. The report says nose-gear touchdown at 23:37:22 was "roughly 2 seconds before the collision", and the REL section says the lights went out "about 3 seconds prior to the collision" (23:37:21). So the look-ahead is "JAZZ 646 at D in ~20 s", not 21.
  2. 23:36:21: the report says Truck 7 *coordinated with* R35 (Truck 1) to contact the tower. The prompt said "Truck 1 takes over the call".
  3. Name: the report body says "Air Canada flight 8646"; the investigation page title says "Air Canada **Express** Flight 8646". The label keeps "Air Canada Express 8646".
  4. Added from the report (not in the prompt's table): 23:37:12, aircraft about 2,550 ft from D; 23:37:17, Truck 1 "had crossed the hold short line" at about 24 mph.
  5. The quoted "Frontier 4195 … stop" audio is **not** in the report. The report has the Truck 1 turret operator recalling "stop stop stop" and "Truck 1 stop stop stop" on the tower frequency, and the ASDE-X image shows FFT4195 nearby. The quote is kept and labelled as press-sourced. The victims' names are from press reports too. The title card says "names and quoted audio from press reports".
  - Confirmed as in the prompt: 23:31:42 emergency (the GC/CIC was coordinating an airplane that had made two rejected takeoffs; six ARFF vehicles and one PA police vehicle responding), 23:35:07 / 5-mile final / 1,900 ft, 23:35:47, 23:36:44 (1.5 nm, 400 ft), 23:36:51 (1.2 nm, 287 ft; Truck 1 460 ft from the edge), 23:36:56 "Truck 1 and company", 23:37:04 (130 ft, ¼-mile final, 4,400 ft from D), 23:37:07 (87 ft, 3,700 ft), 23:37:11 (threshold; truck 10 kt, 410 ft), 23:37:12 (30 ft, 133 kt), 23:37:17 (1,450 ft, 128 kt), 23:37:20 (just over 100 ft, 29 mph), 23:37:22 (400 ft, 106 kt; truck 30 mph entering), last ground speed 90 kt. Also: no ASDE-X alert (vehicles had no transponders), two controllers on duty, LC transmitting on both GC and LC frequencies, C-GNJZ, CL-600-2D24 (CRJ-900), R35 Oshkosh Striker 1500, 2 fatal / 6 serious / 39 to hospital.
- **Geometry:** `viz/klga.geojson` from Overpass. The first try timed out because of my 300 s cap, not the server; the next run succeeded. Runway 04/22 plus taxiways D, AA and BB. The OSM D × 04/22 intersection (40.775525, −73.878884) is within about 0.5 m of the NTSB's estimated collision point (40.775521, −73.878882). Taxiway D is three OSM ways (1102894296, 1361480359, 5783993), two of which are stored east-to-west and had to be reversed before joining. Measured along D, west of the runway 4 centreline: OSM hold line 285 ft (210 ft from the 150-ft runway's edge), AA 382 ft, BB 640 ft. Runway 4 threshold to D: 2,734 ft in OSM (the report's speeds imply about 2,775 ft). Names agree with the report's figures 1, 2 and 8 (BB and AA west of runway 4 on D, D crossing runway 4). **The FAA LGA airport diagram was not separately downloaded**; the NTSB figures were the cross-check.
- **Scenario:** `viz/lga/build_lga.py` → `viz/scenario_lga_04.json`. Both paths are interpolated linearly through the report's own (time, distance) points rather than modelled speeds: JAZZ 646's distance to D, and Truck 1's distance to the runway edge along the OSM D centreline. Truck 1 starts at the BB/D gathering point, reaches its stop point 460 ft from the edge at 23:36:51, and moves from 23:37:07. Using the OSM AA position, it crosses AA about 2–3 s after the report's 23:37:12 "crossing AA". That difference is within the precision of the preliminary figures and is left as is. The eight transcript lines are from `viz/lga/lga_transmissions.jsonl`. "As reported": "truck one and company" (callsign), and the 23:37:12 and 23:37:20 stop calls (press quote). Everything else is shown as "standard phraseology (reconstructed)".
- **Clips** (recorded at **1×** in headless Chromium, then sped up in ffmpeg with `setpts=PTS/2`, so each live-parser result lands in the panel when it actually arrived; 1440×900, 25 fps, no audio; 3 s title card and 3 s closing card):
  - `docs/video/lga_04_asis_2x.mp4` (84 s): both clearances parsed, no rule runs, stop calls at 23:37:12 and 23:37:20. Freezes at **t=142** with "23:37:22 — Truck 1 enters runway 4. NTSB DCA26MA161, preliminary." Nothing is animated past that point.
  - `docs/video/lga_04_gmaps_2x.mp4` (75 s): the alert fires at 23:37:04, and the clip freezes there with the caption. Known flaw: at the freeze, JAZZ 646 (4,400 ft out) is underneath the caption box. Fixed in the package-4 re-record.
- **Live parser latencies (Qwen3-8B + LoRA, :8001, 0-shot, during the 1× recordings): 2.0–3.7 s per call**, median about 2.8 s (13 calls).
- **Not done in this pass:** the stills (made in the package-4 re-record, same layout).
