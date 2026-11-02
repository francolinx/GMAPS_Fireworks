#!/usr/bin/env python3
"""Confidence router: use the cheap model's answer unless it looks unreliable, then fall back to the frontier.

Pure post-processing on two prediction files for the same split — no API calls, fully reproducible.

  python3 scripts/13_router.py results/test/<lora>.preds.jsonl results/test/anthropic_claude-opus-5.5_fs5.preds.jsonl \
      --out results/test/router.preds.jsonl --name "router:lora->opus"

Fallback triggers (any): output does not parse as JSON; no callsign extracted; no command AND no value; role UNKNOWN.
The routed row carries the latency and token counts of whichever model answered (plus the cheap model's cost when it
was consulted first and rejected), so bench/score.py reports blended cost and latency honestly. Prices: add the router
name to results/prices.json as {"in":0,"out":0} and read cost from the per-row 'cost_usd' field this script writes,
or — simpler — report the blended cost printed at the end.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list  # noqa: E402


def load(p):
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def unreliable(d):
    if not d:
        return "no_json"
    if not as_list(d.get("callsigns")):
        return "no_callsign"
    if not as_list(d.get("commands")) and not as_list(d.get("values")):
        return "empty_record"
    if str(d.get("role", "")).upper() not in ("ATCO", "PILOT"):
        return "role_unknown"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cheap"); ap.add_argument("frontier")
    ap.add_argument("--out", required=True); ap.add_argument("--name", default="router")
    ap.add_argument("--prices", default="results/prices.json")
    args = ap.parse_args()
    cheap, front = load(args.cheap), load(args.frontier)
    prices = json.load(open(args.prices)) if os.path.exists(args.prices) else {}

    def cost(r):
        p = prices.get(r.get("model", ""), {})
        return (r.get("prompt_tokens") or 0) / 1e6 * p.get("in", 0) + (r.get("completion_tokens") or 0) / 1e6 * p.get("out", 0)

    n = routed = 0; reasons = {}; total_cost = 0.0; cheap_only_cost = 0.0
    with open(args.out, "w", encoding="utf-8") as fo:
        for rid, c in cheap.items():
            n += 1
            d = parse_output(c.get("output"))
            why = unreliable(d)
            cheap_only_cost += cost(c)
            if why and rid in front:
                f = front[rid]; routed += 1; reasons[why] = reasons.get(why, 0) + 1
                row = dict(f); row["model"] = args.name; row["routed_from"] = c.get("model"); row["route_reason"] = why
                row["latency_ms"] = (c.get("latency_ms") or 0) + (f.get("latency_ms") or 0)
                row["cost_usd"] = cost(c) + cost(f)
            else:
                row = dict(c); row["model"] = args.name; row["cost_usd"] = cost(c)
            total_cost += row["cost_usd"]
            fo.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{args.name}: {routed}/{n} rows routed to frontier ({100 * routed / n:.1f}%)  reasons={reasons}")
    print(f"blended cost ${total_cost:.4f} for {n} rows = ${1000 * total_cost / n:.4f}/1k  (cheap-only would be ${1000 * cheap_only_cost / n:.4f}/1k)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
