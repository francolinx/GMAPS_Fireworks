#!/usr/bin/env bash
# After the 3-epoch Nemotron jobs finish: submit both LoRA arms as batch evals (reasoning off), collect, rescore everything.
#   source ~/.atc_env; FIREWORKS_ACCOUNT_ID=<acct> scripts/27_fw_v2_nemotron_evals.sh
set -euo pipefail
export FIREWORKS_ACCOUNT_ID="${FIREWORKS_ACCOUNT_ID:?}"
for spec in "yu3izojq atc-nemotron-nano-30b-v2" "d6d7yktb atc-nemotron-lightning-30b-v2"; do
  set -- $spec
  python3 scripts/15_fireworks_sft.py status "$1" | tail -1
  python3 scripts/15_fireworks_sft.py status "$1" --once | grep -q COMPLETED || { echo "job $1 not completed"; exit 1; }
  python3 scripts/25_fw_batch_eval.py submit --model "accounts/$FIREWORKS_ACCOUNT_ID/models/$2" --fewshot 0 --tag "${2}_fwbatch-nothink" --extra '{"reasoning_effort":"none"}' | tail -1
done
for tag in atc-nemotron-nano-30b-v2_fwbatch-nothink atc-nemotron-lightning-30b-v2_fwbatch-nothink; do
  python3 scripts/25_fw_batch_eval.py collect --tag "$tag" | tail -1
done
ls results/test/*v2_fwbatch-nothink*.preds.jsonl
