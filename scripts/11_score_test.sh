#!/usr/bin/env bash
# Score every test-split prediction file together so the paired bootstrap deltas are against the FIRST file given.
#   scripts/11_score_test.sh results/test/gpt-5_fs5.preds.jsonl results/test/*.preds.jsonl
# (list the frontier baseline first; duplicates are fine, the scorer handles each file once in order)
set -euo pipefail
[ $# -ge 1 ] || { echo "give the baseline preds file first, then the rest"; exit 1; }
mkdir -p results/test
# de-duplicate while preserving order
FILES=(); for f in "$@"; do skip=0; for g in "${FILES[@]:-}"; do [ "$f" = "$g" ] && skip=1; done; [ $skip = 0 ] && FILES+=("$f"); done
python3 bench/score.py data/splits/test.jsonl "${FILES[@]}" --prices results/prices.json --bootstrap 5000 --out results/test/scores.json | tee results/test/scores.md
