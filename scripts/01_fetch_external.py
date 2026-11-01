#!/usr/bin/env python3
"""Fetch extra ATC transcripts (text only) for pseudo-labelling, with a leakage guard against ATCO2.

Sources (all on the Hugging Face Hub, research licences — do not redistribute, cite in README):
  Jzuluaga/atcosim_corpus   ATCOSIM, ~9.5k utterances, Eurocontrol real-time simulation (controller speech)
  Jzuluaga/uwb_atcc         UWB-ATCC, ~14k utterances, Czech airspace, pilot + controller (CC BY-NC-SA 4.0)

NOT used on purpose: jlvdoorn/atco2-asr*, luigisaetta/atco2*, Maulik1528/ATCO2* — they contain the ATCO2 1h set,
i.e. our held-out TEST airports. Pulling them would leak test transcripts into training.

Column projection: only `id` and `text` are read from the parquet files, so the multi-GB audio never downloads.

  python scripts/01_fetch_external.py --gold data/atco2_1h_gold.jsonl --out data/external
"""
import argparse, json, os, re, sys

SOURCES = {
    "atcosim": {"repo": "Jzuluaga/atcosim_corpus", "splits": ["train", "test"], "license": "research use (TU Graz / Eurocontrol)"},
    "uwb_atcc": {"repo": "Jzuluaga/uwb_atcc", "splits": ["train", "test"], "license": "CC BY-NC-SA 4.0"},
}
BRACKET = re.compile(r"\[[^\]]*\]|<[^>]*>|\([^)]*\)")
PUNCT = re.compile(r"[^a-z0-9' ]")


def norm(s):
    s = BRACKET.sub(" ", (s or "").lower())
    s = s.replace("~", " ").replace("=", " ").replace("_", " ")
    s = PUNCT.sub(" ", s)
    return " ".join(s.split())


def read_parquet_text(repo, split):
    """Read id,text columns only. Try pyarrow over HfFileSystem (cheap), then datasets (downloads audio too)."""
    try:
        import pyarrow.parquet as pq
        from huggingface_hub import HfFileSystem
        fs = HfFileSystem()
        files = fs.glob(f"datasets/{repo}@~parquet/default/{split}/*.parquet")
        rows = []
        for f in files:
            with fs.open(f, "rb") as fh:
                t = pq.read_table(fh, columns=["id", "text"])
            rows += [{"id": i, "text": x} for i, x in zip(t.column("id").to_pylist(), t.column("text").to_pylist())]
        if rows:
            return rows
    except Exception as e:
        print(f"  pyarrow path failed for {repo}/{split}: {e!r}; falling back to datasets", file=sys.stderr)
    from datasets import load_dataset
    ds = load_dataset(repo, split=split)
    ds = ds.remove_columns([c for c in ds.column_names if c not in ("id", "text")])
    return [{"id": r["id"], "text": r["text"]} for r in ds]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/atco2_1h_gold.jsonl", help="ATCO2 gold (all 877) for the leakage guard")
    ap.add_argument("--out", default="data/external")
    ap.add_argument("--sources", nargs="+", default=list(SOURCES))
    ap.add_argument("--min-words", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    guard = set()
    if os.path.exists(args.gold):
        for l in open(args.gold, encoding="utf-8"):
            guard.add(norm(json.loads(l)["text"]))
    print(f"leakage guard: {len(guard)} ATCO2 texts")

    summary = {}
    for name in args.sources:
        src = SOURCES[name]
        out_path = os.path.join(args.out, f"{name}.jsonl")
        n_in = n_out = n_leak = n_dup = 0
        seen = set()
        with open(out_path, "w", encoding="utf-8") as fh:
            for split in src["splits"]:
                print(f"fetching {src['repo']} [{split}] ...")
                for r in read_parquet_text(src["repo"], split):
                    n_in += 1
                    t = norm(r["text"])
                    if len(t.split()) < args.min_words:
                        continue
                    if t in guard:
                        n_leak += 1; continue
                    if t in seen:
                        n_dup += 1; continue
                    seen.add(t)
                    # speaker role is gold where the source gives it: UWB ids end in _AT (controller) / _PI (pilot);
                    # ATCOSIM is controller-only speech.
                    rid = str(r["id"])
                    role = "ATCO" if name == "atcosim" else ("ATCO" if rid.endswith("_AT") else "PILOT" if rid.endswith("_PI") else "UNKNOWN")
                    fh.write(json.dumps({"id": f"{name}:{split}:{rid}", "source": name, "split_origin": split,
                                         "text": t, "role": role, "facility": "unknown"}, ensure_ascii=False) + "\n")
                    n_out += 1
        summary[name] = {"in": n_in, "kept": n_out, "leak_dropped": n_leak, "dup_dropped": n_dup, "license": src["license"]}
        print(f"  {name}: kept {n_out} / {n_in} (leak {n_leak}, dup {n_dup}) → {out_path}")
    json.dump(summary, open(os.path.join(args.out, "SUMMARY.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
