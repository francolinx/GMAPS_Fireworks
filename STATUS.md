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
