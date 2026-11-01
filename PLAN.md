# PLAN — unattended Spark run (budget ≈ 5 h; checkpoints in bold)

Work top to bottom. Each phase ends with a check and a commit. Time estimates assume the GB10.

## Phase 0 — environment (10 min)

```
bash scripts/00_env_check.sh
python3 -m pip install -r requirements.txt            # datasets pyarrow huggingface_hub trl peft transformers accelerate
python3 -c "import unsloth" || echo "unsloth missing → follow build.nvidia.com/spark/unsloth, or use --force-trl in phase 4"
```
**Check:** `results/env_check.txt` exists; GPU visible; which teacher key (if any) is set; SSD model folder names noted.

## Phase 1 — data (15 min)

```
python3 bench/prepare_data.py                          # ATCO2 1h → data/atco2_1h_gold.jsonl + splits; prints test sha256
diff <(cut -d' ' -f1 data/splits/test.sha256) <(echo 8660e6dedb571daa3c9c71b598d0890b430b06d1525418954a2e2ff4be8a31cd)   # must be empty
python3 bench/normalize.py data/atco2_1h_gold.jsonl    # action-table coverage; OTHER should be ≤ 1 %
python3 scripts/01_fetch_external.py                   # ATCOSIM + UWB-ATCC text only, leakage-guarded → data/external/
python3 scripts/02_synth_us_phraseology.py             # → data/synthetic/us_train.jsonl (3000) + us_stress.jsonl (300)
```
**Check:** the sha256 diff is empty (identical split to the committed hash). `data/external/SUMMARY.json` shows kept
counts and `leak_dropped` > 0 for nothing or a handful (if a source shows hundreds of leaked rows, it contains ATCO2 —
drop that source). Commit.

## Phase 2 — teacher pseudo-labels (30–60 min)

Pick the teacher per `CLAUDE.md` priority. For a local teacher:
```
scripts/06_serve_vllm.sh /mnt/hackssd/GB10_ARSENAL/models/<Nemotron-3-Nano-30B-A3B-NVFP4 dir> teacher 8002 --max-model-len 4096
export BASE_URL=http://localhost:8002/v1 API_KEY=none TEACHER=teacher
```
For a frontier teacher set `BASE_URL`/`API_KEY`/`TEACHER` accordingly (Anthropic: `https://api.anthropic.com/v1`).
```
for s in uwb_atcc atcosim; do
  python3 bench/infer.py --model "$TEACHER" --split data/external/$s.jsonl --out data/pseudo/$s.preds.jsonl \
          --fewshot 8 --concurrency 16 --json-mode --max-tokens 220
  python3 scripts/03_pseudo_label.py data/external/$s.jsonl data/pseudo/$s.preds.jsonl data/pseudo/$s.gold.jsonl --teacher-name "$TEACHER"
done
docker rm -f vllm-teacher   # free the memory before fine-tuning
```
`--json-mode` may be rejected by some servers; if so drop it. If the teacher is slow, cap with `--limit 8000` per source.
**Check:** each `.gold.jsonl` keeps ≥ 60 % of rows; if the keep rate is < 40 %, the teacher is paraphrasing — raise
`--fewshot` to 12 or switch teacher. Record keep rates in `STATUS.md`. Commit (the pseudo files are gitignored; commit the summary numbers in STATUS).

## Phase 3 — training mix (5 min)

```
python3 scripts/04_build_sft_mix.py --gold data/splits/train.jsonl --dev data/splits/dev.jsonl \
   --synthetic data/synthetic/us_train.jsonl --max-synth 2500 \
   --pseudo data/pseudo/uwb_atcc.gold.jsonl data/pseudo/atcosim.gold.jsonl --max-pseudo 6000 \
   --out data/sft/mix_train.jsonl --dev-out data/sft/dev.jsonl
```
**Check:** composition printed; gold_atco2 ≈ 490 unique (×2), total 6–10k examples. Commit.

## Phase 4 — fine-tune (60–120 min)

Smoke test first, then the real run. Qwen3-8B first (Fireworks-tunable, so Monday's Fireworks job matches), then the
NVIDIA student if time allows.
```
python3 scripts/05_finetune_unsloth.py --base Qwen/Qwen3-8B --out runs/smoke --max-steps 20 --no-merge
python3 scripts/05_finetune_unsloth.py --base Qwen/Qwen3-8B --out runs/qwen3-8b-atc --epochs 2
python3 scripts/05_finetune_unsloth.py --base nvidia/Llama-3.1-Nemotron-Nano-8B-v1 --out runs/nemotron-nano-8b-atc --epochs 2   # if ≥ 90 min left
```
If a model from the SSD is preferred (no download), pass its folder as `--base` (Qwen3-4B-Instruct-2507 is a good
fast student). If `unsloth` is unusable: add `--force-trl` (slower, same output).
**Check:** `runs/*/train_log.json` has an eval loss that went down; `runs/*/merged/` exists. Commit the log only.

## Phase 5 — dev evaluation (20 min)

```
scripts/06_serve_vllm.sh Qwen/Qwen3-8B qwen3-8b-base 8001 --max-model-len 2048
BASE_URL=http://localhost:8001/v1 API_KEY=none scripts/07_eval_dev.sh qwen3-8b-base 5
docker rm -f vllm-qwen3-8b-base
scripts/06_serve_vllm.sh runs/qwen3-8b-atc/merged atc-qwen3-8b 8001 --max-model-len 2048
BASE_URL=http://localhost:8001/v1 API_KEY=none scripts/07_eval_dev.sh atc-qwen3-8b 0
```
(The fine-tuned model is run zero-shot: it learned the format. The base is run 5-shot: that is the fair prompted arm.)
If a frontier key is set, also run the baseline on dev: `BASE_URL=https://api.openai.com/v1 API_KEY=$OPENAI_API_KEY scripts/07_eval_dev.sh gpt-5 5`
**Check:** `results/dev/scores.md` has a table per arm. Put the table in `STATUS.md`. Commit.

## Phase 6 — latency sweep (10 min)

```
BASE_URL=http://localhost:8001/v1 API_KEY=none python3 scripts/08_latency_bench.py --model atc-qwen3-8b --out results/latency_spark_local.json --note "vLLM on DGX Spark, localhost"
```
**Check:** p50/p95 at concurrency 1/4/16 in `STATUS.md`.

## Phase 7 — visualization (15 min)

```
python3 viz/fetch_airport_osm.py KSFO viz/ksfo.geojson --bbox 37.595,-122.415,37.645,-122.345   # refresh; committed copy is fine if Overpass is down
python3 viz/build_scenario.py viz/ksfo.geojson viz/scenario_sfo_sim1.json --runway 28L
cd viz && python3 -m http.server 8080 &  # open http://<spark>:8080/ — play the scenario, both variants
```
Optional if time remains: a second scenario on 01R (`--runway 01R`), and wire `viz/scenario_*.json` transmissions
through the real model (`bench/infer.py` on the four transmissions) so the "parsed" blocks are model output, not
hand-written — note which it is in the scenario file.
**Check:** page loads, runway 28L flashes at t=28, RESCUE7 stops at the hold line in the resolved variant. Commit.

## Phase 8 — hand-off (10 min)

Fill `STATUS.md` (template inside). Append anything new you built to `DISCLOSURE.md`. Final commit:
`git log --oneline` should show one commit per phase. Leave the fine-tuned server running on :8001 so Franco can
try it over Tailscale.

## Stop conditions

- Disk < 20 GB free → stop downloads, note it.
- Any phase > 2× its estimate → finish the current step, write STATUS, continue to the next phase.
- Anything that would require touching `test.jsonl` → don't; note the question for Monday.
