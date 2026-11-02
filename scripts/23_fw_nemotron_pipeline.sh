#!/usr/bin/env bash
# Nemotron arm, unattended: wait for the SFT job → ONE on-demand deployment of the base with addons → base 5-shot and
# LoRA 0-shot through the same deployment (before → after on identical hardware) → score all arms → tear down.
#   source ~/.atc_env; FIREWORKS_ACCOUNT_ID=<acct> scripts/23_fw_nemotron_pipeline.sh <job-id> <output-model-id>
set -euo pipefail
JOB="${1:?job id}"; OUT="${2:?output model id}"; DEP="${DEP:-atc-nemo}"; BASE="accounts/fireworks/models/nemotron-nano-3-30b-a3b"
ACCT="${FIREWORKS_ACCOUNT_ID:?}"
cleanup() { python3 scripts/15_fireworks_sft.py undeploy --deployment-id "$DEP" || true; }
python3 scripts/15_fireworks_sft.py status "$JOB" | tail -3
python3 scripts/15_fireworks_sft.py status "$JOB" --once | grep -q COMPLETED || { echo "job not completed"; exit 1; }
trap cleanup EXIT
python3 scripts/15_fireworks_sft.py deploy-ondemand "$OUT" --deployment-id "$DEP" --base "$BASE" --count 0 --precision default
export BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY="$FIREWORKS_API_KEY"
export EXTRA='{"chat_template_kwargs":{"enable_thinking":false}}'
B="$BASE#accounts/$ACCT/deployments/$DEP"; L="accounts/$ACCT/models/$OUT#accounts/$ACCT/deployments/$DEP"
python3 bench/infer.py --model "$B" --split data/splits/dev.jsonl --out /tmp/nemo_smoke.preds.jsonl --fewshot 5 --limit 2 --max-tokens 1500 --extra "$EXTRA" && head -c 700 /tmp/nemo_smoke.preds.jsonl; echo
NAME="nemotron-nano-30b-base_fireworks" CONC=8 scripts/10_eval_test.sh "$B" 5
NAME="atc-nemotron-nano-30b-v1_fireworks" CONC=8 scripts/10_eval_test.sh "$L" 0
ls results/test/*.preds.jsonl
