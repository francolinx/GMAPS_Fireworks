#!/usr/bin/env python3
"""Assemble the training mix in chat format for fine-tuning.

  python scripts/04_build_sft_mix.py \
      --gold data/splits/train.jsonl \
      --synthetic data/synthetic/us_train.jsonl --max-synth 2500 \
      --pseudo data/pseudo/uwb_atcc.gold.jsonl data/pseudo/atcosim.gold.jsonl --max-pseudo 6000 \
      --dev data/splits/dev.jsonl \
      --out data/sft/mix_train.jsonl --dev-out data/sft/dev.jsonl

Rules baked in:
  - the ATCO2 TEST split can never be an input (refused by filename)
  - every text is deduplicated across sources (first source wins: gold > synthetic > pseudo)
  - any row whose text equals a dev/test text is dropped
  - the gold ATCO2 train rows are up-weighted (--gold-repeat) so real phraseology dominates
"""
import argparse, collections, json, os, random, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from make_sft import user_message, target  # noqa: E402
from score import norm_text  # noqa: E402


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--dev", required=True)
    ap.add_argument("--synthetic", nargs="*", default=[])
    ap.add_argument("--pseudo", nargs="*", default=[])
    ap.add_argument("--max-synth", type=int, default=2500)
    ap.add_argument("--max-pseudo", type=int, default=6000)
    ap.add_argument("--gold-repeat", type=int, default=2)
    ap.add_argument("--system", default="prompts/system.txt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev-out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    for p in [args.gold, args.dev] + args.synthetic + args.pseudo:
        if "test" in os.path.basename(p):
            sys.exit(f"refusing to use a test split as training input: {p}")

    rng = random.Random(args.seed)
    system = open(args.system, encoding="utf-8").read().strip()
    dev = load(args.dev)
    blocked = {norm_text(r["text"]) for r in dev}
    try:  # also block the test texts if present locally (never printed, only hashed into the guard)
        for r in load(os.path.join(os.path.dirname(args.gold), "test.jsonl")):
            blocked.add(norm_text(r["text"]))
    except FileNotFoundError:
        pass

    seen = set()
    mix, comp = [], collections.Counter()

    def take(rows, label, cap=None):
        rng.shuffle(rows)
        n = 0
        for r in rows:
            if cap is not None and n >= cap:
                break
            t = norm_text(r["text"])
            if not t or t in seen or t in blocked:
                continue
            seen.add(t)
            mix.append((label, r)); n += 1
        comp[label] += n

    gold = load(args.gold)
    take(gold, "gold_atco2")
    for p in args.synthetic:
        take(load(p), "synthetic_us", args.max_synth)
    for p in args.pseudo:
        take(load(p), "pseudo:" + os.path.basename(p).split(".")[0], args.max_pseudo)

    rows = []
    for label, r in mix:
        reps = args.gold_repeat if label == "gold_atco2" else 1
        for _ in range(reps):
            rows.append({"messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message(r)},
                {"role": "assistant", "content": json.dumps(target(r), ensure_ascii=False)},
            ], "source": label})
    rng.shuffle(rows)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(args.dev_out, "w", encoding="utf-8") as fh:
        for r in dev:
            fh.write(json.dumps({"messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message(r)},
                {"role": "assistant", "content": json.dumps(target(r), ensure_ascii=False)},
            ], "source": "gold_dev"}, ensure_ascii=False) + "\n")
    print(f"train examples: {len(rows)} (unique texts {len(mix)}; gold repeated x{args.gold_repeat})  composition: {dict(comp)}")
    print(f"dev examples: {len(dev)}  → {args.out}, {args.dev_out}")


if __name__ == "__main__":
    main()
