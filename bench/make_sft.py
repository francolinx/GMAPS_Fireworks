#!/usr/bin/env python3
"""Build a Fireworks supervised-fine-tuning dataset (chat JSONL) from the train/dev splits.

  python bench/make_sft.py data/splits/train.jsonl data/sft/train.jsonl
  python bench/make_sft.py data/splits/dev.jsonl   data/sft/dev.jsonl

Each line: {"messages": [{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]}
The assistant target is the gold record in exactly the schema prompts/system.txt asks for,
so the fine-tuned model and the prompted baselines are scored by the same parser.

NEVER run this on test.jsonl.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from normalize import actions_for  # noqa: E402


def user_message(row):
    return f"facility: {row['facility'].lower()}\ntransmission: {row['text']}"


def target(row, with_actions=False):
    t = {
        "role": row.get("role", "UNKNOWN"),
        "callsigns": row["gold"]["callsign"],
        "commands": row["gold"]["command"],
        "values": row["gold"]["value"],
    }
    if with_actions:
        t["actions"] = sorted(actions_for(row["gold"]["command"]) - {"OTHER"})
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("split")
    ap.add_argument("out")
    ap.add_argument("--system", default="prompts/system.txt")
    ap.add_argument("--with-actions", action="store_true", help="also teach the canonical action labels")
    args = ap.parse_args()
    if "test" in os.path.basename(args.split):
        sys.exit("refusing to build SFT data from a test split")

    system = open(args.system, encoding="utf-8").read().strip()
    rows = [json.loads(l) for l in open(args.split, encoding="utf-8") if l.strip()]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({"messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message(r)},
                {"role": "assistant", "content": json.dumps(target(r, args.with_actions), ensure_ascii=False)},
            ]}, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} examples → {args.out}")


if __name__ == "__main__":
    main()
