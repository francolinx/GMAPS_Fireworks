#!/usr/bin/env bash
# The 10:30 command: all frontier arms on the frozen test split, in sequence, via OpenRouter.
#   TEST_UNFROZEN=1 OPENROUTER_API_KEY=... scripts/17_run_test_frontier.sh
# Then: scripts/11_score_test.sh results/test/anthropic_claude-opus-5.5_fs5.preds.jsonl results/test/*.preds.jsonl
set -euo pipefail
[ "${TEST_UNFROZEN:-0}" = "1" ] || { echo "set TEST_UNFROZEN=1 — the build period must have started (Nov 2, 10:30 PT)"; exit 1; }
export BASE_URL=https://openrouter.ai/api/v1 API_KEY="${OPENROUTER_API_KEY:?}"
export CONC="${CONC:-6}"
scripts/10_eval_test.sh anthropic/claude-opus-5.5 5
scripts/10_eval_test.sh openai/gpt-5.5 5
scripts/10_eval_test.sh openai/gpt-5.6-terra 5
scripts/10_eval_test.sh anthropic/claude-opus-5.5 20
echo "frontier arms done → results/test/"
