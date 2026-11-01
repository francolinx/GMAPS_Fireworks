#!/usr/bin/env python3
"""Latency / throughput sweep against any OpenAI-compatible endpoint, same prompts for every arm.

  BASE_URL=http://localhost:8001/v1 API_KEY=none python scripts/08_latency_bench.py --model atc-qwen3-8b --out results/latency_local.json
  BASE_URL=https://api.fireworks.ai/inference/v1 API_KEY=... python scripts/08_latency_bench.py --model accounts/fireworks/models/qwen3-8b ...

Uses the first N dev rows, concurrency sweep 1 / 4 / 16, reports p50 / p95 / mean per request and
requests-per-second. Report "measured from <where> over <network>" with the numbers — latency is only comparable
across arms when it was measured from the same machine in the same session.
"""
import argparse, json, os, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from infer import build_messages, call, load_jsonl  # noqa: E402


def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rows", type=int, default=96)
    ap.add_argument("--conc", nargs="+", type=int, default=[1, 4, 16])
    ap.add_argument("--fewshot", type=int, default=5)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    base_url, api_key = os.environ["BASE_URL"], os.environ["API_KEY"]
    system = open("prompts/system.txt", encoding="utf-8").read().strip()
    rows = load_jsonl("data/splits/dev.jsonl")[: args.rows]
    shots = load_jsonl("data/splits/dev.jsonl")[-args.fewshot:] if args.fewshot else []

    def one(row):
        payload = {"model": args.model, "messages": build_messages(system, shots, row), "max_tokens": args.max_tokens, "temperature": 0}
        _, ms, pt, ct, err = call(base_url, api_key, payload, timeout=120, retries=1)
        return ms, err

    # warm-up
    for r in rows[:2]:
        one(r)
    results = {"model": args.model, "base_url": base_url, "rows": len(rows), "note": args.note, "sweep": []}
    for c in args.conc:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(c) as ex:
            outs = list(ex.map(one, rows))
        wall = time.perf_counter() - t0
        lat = [ms for ms, err in outs if ms is not None]
        errs = sum(1 for _, err in outs if err)
        rec = {"concurrency": c, "n": len(lat), "errors": errs, "p50_ms": q(lat, .5) if lat else None, "p95_ms": q(lat, .95) if lat else None,
               "mean_ms": statistics.mean(lat) if lat else None, "rps": len(lat) / wall if wall else None, "wall_s": wall}
        results["sweep"].append(rec)
        print(f"conc={c:3d}  p50={rec['p50_ms'] and round(rec['p50_ms'])} ms  p95={rec['p95_ms'] and round(rec['p95_ms'])} ms  rps={rec['rps']:.2f}  errors={errs}")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(results, open(args.out, "w"), indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
