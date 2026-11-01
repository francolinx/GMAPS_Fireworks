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

## Visualization
- `viz/index.html` served on :8080 — ok / issue:
- scenario(s) built:

## Problems / open questions for Monday
- Dev few-shot leakage: `bench/infer.py` takes shots from the **first N dev rows**, and those rows are also scored, so the 5-shot base arm is slightly flattered on dev. On test this does not apply (shots from dev, scored on test).
- `bench/infer.py` defaults `--split` to `data/splits/test.jsonl` — every call today passed `--split` explicitly. Consider changing the default before Monday.
- `scripts/07_eval_dev.sh` had no way to disable Qwen3 thinking; added optional `EXTRA` passthrough (used for both arms today).
- Phase 0: host has no torch; data scripts run in in-repo `.venv` (datasets/pyarrow/hf_hub); fine-tune runs in `nvcr.io/nvidia/pytorch:25.11-py3`. No teacher API key set → local vLLM teacher on :8002.
- Phase 0: SSD teacher folders are `reasoning/nemotron-3-nano-30b-a3b-nvfp4` and `reasoning/qwen3.5-35b-a3b-fp8` (not the names in CLAUDE.md). Port 8080 is taken by `openshell-gateway` → viz served on another port.

## Left running
- vLLM `atc-qwen3-8b` on :8001 (container `vllm-atc-qwen3-8b`): yes / no
