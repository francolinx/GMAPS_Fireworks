#!/usr/bin/env bash
# THE frozen-test run. First executed during the build period (Nov 2, >= 10:30 PT). Same prompt, same shots, same scorer for every arm.
#
#   BASE_URL=https://api.openai.com/v1            API_KEY=$OPENAI_API_KEY    scripts/10_eval_test.sh gpt-5 5
#   BASE_URL=https://api.openai.com/v1            API_KEY=$OPENAI_API_KEY    scripts/10_eval_test.sh gpt-5 20        # fairness check: more shots for the baseline
#   BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY=$FIREWORKS_API_KEY scripts/10_eval_test.sh accounts/fireworks/models/qwen3-8b 5
#   BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY=$FIREWORKS_API_KEY scripts/10_eval_test.sh accounts/<you>/deployedModels/<lora> 0
#   BASE_URL=http://<spark>:8001/v1                API_KEY=none              scripts/10_eval_test.sh atc-qwen3-8b 0  # on-prem arm
#
# Few-shot examples come from data/splits/train.jsonl (bench/infer.py default) — never from test.
# EXTRA='{"chat_template_kwargs":{"enable_thinking":false}}' for Qwen3 base models; JSON_MODE=1 if the server supports it.
set -euo pipefail
MODEL="${1:?model name as served}"; FEWSHOT="${2:-0}"; TAG="${3:-}"
SAFE="$(echo "$MODEL" | tr '/:' '__')${TAG:+_$TAG}_fs$FEWSHOT"
mkdir -p results/test
test -f data/splits/test.jsonl || { echo "run bench/prepare_data.py first"; exit 1; }
sha256sum data/splits/test.jsonl | awk '{print $1"  test.jsonl"}' | diff - data/splits/test.sha256 || { echo "TEST SET HASH MISMATCH — stop"; exit 1; }
# MAX_TOKENS defaults to 1500: reasoning models count their hidden reasoning against max_tokens, and a truncated
# baseline would be a weakened baseline. The JSON itself is ~60 tokens.
python3 bench/infer.py --model "$MODEL" --split data/splits/test.jsonl --out "results/test/$SAFE.preds.jsonl" \
        --fewshot "$FEWSHOT" --concurrency "${CONC:-8}" --max-tokens "${MAX_TOKENS:-1500}" --timeout "${TIMEOUT:-150}" \
        ${JSON_MODE:+--json-mode} ${EXTRA:+--extra "$EXTRA"}
echo "preds → results/test/$SAFE.preds.jsonl  (score all arms together: scripts/11_score_test.sh)"
