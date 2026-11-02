#!/usr/bin/env bash
# Fireworks v2 route, unattended: wait for the SFT job → on-demand deployment with the LoRA → frozen-test run (0-shot, same
# prompt/scorer as every arm) → score all arms → tear the deployment down (it bills per GPU-hour while it exists).
#   source ~/.atc_env; FIREWORKS_ACCOUNT_ID=<acct> scripts/21_fw_v2_pipeline.sh <job-id> <output-model-id>
set -euo pipefail
JOB="${1:?job id}"; OUT="${2:?output model id}"; DEP="${DEP:-atc-eval}"
ACCT="${FIREWORKS_ACCOUNT_ID:?}"
python3 scripts/15_fireworks_sft.py status "$JOB" | tail -3
python3 scripts/15_fireworks_sft.py status "$JOB" --once | grep -q COMPLETED || { echo "job not completed"; exit 1; }
python3 scripts/15_fireworks_sft.py deploy-ondemand "$OUT" --deployment-id "$DEP"
MODEL="accounts/$ACCT/models/$OUT#accounts/$ACCT/deployments/$DEP"
export BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY="$FIREWORKS_API_KEY"
export EXTRA='{"chat_template_kwargs":{"enable_thinking":false}}'
# smoke: two rows, then the full run (resumable)
python3 bench/infer.py --model "$MODEL" --split data/splits/dev.jsonl --out /tmp/fw_smoke.preds.jsonl --fewshot 0 --limit 2 --max-tokens 300 --extra "$EXTRA" && head -c 600 /tmp/fw_smoke.preds.jsonl; echo
NAME="atc-qwen3-8b-v2_fireworks" CONC=8 scripts/10_eval_test.sh "$MODEL" 0
scripts/11_score_test.sh results/test/qwen3-8b-base_spark_fs5.preds.jsonl results/test/atc-qwen3-8b_spark_fs0.preds.jsonl results/test/atc-qwen3-8b-v2_fireworks_fs0.preds.jsonl results/test/anthropic_claude-opus-5.5_fs5.preds.jsonl results/test/anthropic_claude-opus-5.5_fs20.preds.jsonl results/test/openai_gpt-5.5_fs5.preds.jsonl results/test/openai_gpt-5.6-terra_fs5.preds.jsonl results/test/router_lora-opus_fs0.preds.jsonl | tail -45
python3 scripts/15_fireworks_sft.py undeploy --deployment-id "$DEP"
