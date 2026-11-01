# STATUS — Spark run hand-off

_(Claude Code: overwrite this file as phases complete. Numbers only from `bench/score.py` / `08_latency_bench.py` output. No keys.)_

## Run summary
- started (UTC): 2026-11-01T02:36Z
- machine: spark-6771 — see `results/env_check.txt`
- phases completed: 0 1 2 3 4 5 6 7 8  _(strike through what did not finish)_

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

### synthetic US stress

## Latency (vLLM on Spark, localhost)
| concurrency | p50 ms | p95 ms | rps |
|---|---|---|---|

## Visualization
- `viz/index.html` served on :8080 — ok / issue:
- scenario(s) built:

## Problems / open questions for Monday
- Phase 0: host has no torch; data scripts run in in-repo `.venv` (datasets/pyarrow/hf_hub); fine-tune runs in `nvcr.io/nvidia/pytorch:25.11-py3`. No teacher API key set → local vLLM teacher on :8002.
- Phase 0: SSD teacher folders are `reasoning/nemotron-3-nano-30b-a3b-nvfp4` and `reasoning/qwen3.5-35b-a3b-fp8` (not the names in CLAUDE.md). Port 8080 is taken by `openshell-gateway` → viz served on another port.

## Left running
- vLLM `atc-qwen3-8b` on :8001 (container `vllm-atc-qwen3-8b`): yes / no
