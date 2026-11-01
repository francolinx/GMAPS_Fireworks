#!/usr/bin/env bash
# Run one model over the DEV split and the synthetic US stress split, then score both. Never touches test.jsonl.
#
#   BASE_URL=http://localhost:8001/v1 API_KEY=none scripts/07_eval_dev.sh atc-qwen3-8b [fewshot]
#   BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY=$FIREWORKS_API_KEY scripts/07_eval_dev.sh accounts/fireworks/models/qwen3-8b 5
#
# Results land in results/dev/<safe-name>.{dev,stress}.preds.jsonl and results/dev/scores.md is appended.
set -euo pipefail
MODEL="${1:?model name as served}"; FEWSHOT="${2:-0}"
SAFE="$(echo "$MODEL" | tr '/:' '__')"
mkdir -p results/dev
python3 bench/infer.py --model "$MODEL" --split data/splits/dev.jsonl --out "results/dev/$SAFE.dev.preds.jsonl" --fewshot "$FEWSHOT" --concurrency "${CONC:-8}" ${JSON_MODE:+--json-mode}
python3 bench/infer.py --model "$MODEL" --split data/synthetic/us_stress.jsonl --out "results/dev/$SAFE.stress.preds.jsonl" --fewshot "$FEWSHOT" --concurrency "${CONC:-8}" ${JSON_MODE:+--json-mode}
{
  echo; echo "## $MODEL  (fewshot=$FEWSHOT, $(date -u +%FT%TZ))"; echo; echo "### dev (ATCO2 gold, training airports)"
  python3 bench/score.py data/splits/dev.jsonl "results/dev/$SAFE.dev.preds.jsonl" --prices results/prices.json --out "results/dev/$SAFE.dev.scores.json"
  echo; echo "### synthetic US stress (gold by construction)"
  python3 bench/score.py data/synthetic/us_stress.jsonl "results/dev/$SAFE.stress.preds.jsonl" --prices results/prices.json --out "results/dev/$SAFE.stress.scores.json"
} | tee -a results/dev/scores.md
