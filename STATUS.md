# STATUS — Spark run hand-off

_(Claude Code: overwrite this file as phases complete. Numbers only from `bench/score.py` / `08_latency_bench.py` output. No keys.)_

## Run summary
- started (UTC):
- machine: spark-6771 — see `results/env_check.txt`
- phases completed: 0 1 2 3 4 5 6 7 8  _(strike through what did not finish)_

## Data
- ATCO2 split verified against committed hash: yes / no
- external: uwb_atcc kept __ / __ (leak_dropped __), atcosim kept __ / __
- synthetic: us_train __, us_stress __ (sha256 in data/synthetic/us_stress.sha256)
- pseudo-labels: teacher = ______ ; keep rate uwb __ %, atcosim __ %
- training mix: __ examples (gold ×2 = __, synthetic __, pseudo __)

## Fine-tunes
| run | base | examples | epochs | train loss | eval loss | wall time | merged? |
|---|---|---|---|---|---|---|---|
| qwen3-8b-atc | Qwen/Qwen3-8B | | | | | | |
| nemotron-nano-8b-atc | nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | | | | | | |

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
-

## Left running
- vLLM `atc-qwen3-8b` on :8001 (container `vllm-atc-qwen3-8b`): yes / no
