#!/usr/bin/env python3
"""Score prediction files against the gold split. Same cases, same scorer, every arm.

Usage:
  python bench/score.py data/splits/test.jsonl results/preds_gpt5.jsonl results/preds_qwen3_lora.jsonl \
      --prices results/prices.json --out results/scores.json

Prediction JSONL, one row per gold id:
  {"id": "...", "model": "...", "output": <str | dict>, "latency_ms": 812.4,
   "prompt_tokens": 310, "completion_tokens": 42}

Expected model output (string is parsed; code fences and leading prose are tolerated):
  {"role": "ATCO"|"PILOT"|"UNKNOWN", "callsigns": [..], "commands": [..], "values": [..]}

prices.json maps model name -> {"in": $/1M prompt tokens, "out": $/1M completion tokens}.
"""
import argparse, collections, json, os, re, statistics, sys

sys.path.insert(0, os.path.dirname(__file__))
from normalize import actions_for, RUNWAY_CRITICAL  # noqa: E402

_PUNCT = re.compile(r"[^\w\s]")


def norm_text(s: str) -> str:
    return " ".join(_PUNCT.sub(" ", (s or "").lower()).split())


def parse_output(raw):
    """Return (dict|None). Accepts dicts, JSON strings, fenced JSON, or prose containing one JSON object."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.S)
    try:
        d = json.loads(s)
        return d if isinstance(d, dict) else None
    except Exception:
        pass
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            return d if isinstance(d, dict) else None
        except Exception:
            return None
    return None


def as_list(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    return [str(i) for i in x if i is not None]


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def multiset_counts(gold, pred):
    g, p = collections.Counter(gold), collections.Counter(pred)
    tp = sum((g & p).values())
    return tp, sum(p.values()) - tp, sum(g.values()) - tp


def pct(x):
    return f"{100 * x:.1f}%"


def score_file(gold_rows, pred_path, prices):
    preds = {}
    model_name = None
    with open(pred_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            preds[r["id"]] = r
            model_name = model_name or r.get("model")

    n = len(gold_rows)
    valid = 0
    ent = {k: [0, 0, 0] for k in ("callsign", "command", "value")}
    act = [0, 0, 0]
    act_exact = 0
    crit_n = crit_exact = 0
    crit_tp = crit_fp = crit_fn = 0
    role_n = role_ok = 0
    full_exact = 0
    lat, ptok, ctok = [], 0, 0
    missing = 0

    for g in gold_rows:
        p = preds.get(g["id"])
        if p is None:
            missing += 1
            d = None
        else:
            d = parse_output(p.get("output"))
            if p.get("latency_ms") is not None:
                lat.append(float(p["latency_ms"]))
            ptok += int(p.get("prompt_tokens") or 0)
            ctok += int(p.get("completion_tokens") or 0)
        if d is not None:
            valid += 1
        d = d or {}

        gold_ents = {
            "callsign": [norm_text(x) for x in g["gold"]["callsign"]],
            "command": [norm_text(x) for x in g["gold"]["command"]],
            "value": [norm_text(x) for x in g["gold"]["value"]],
        }
        pred_ents = {
            "callsign": [norm_text(x) for x in as_list(d.get("callsigns"))],
            "command": [norm_text(x) for x in as_list(d.get("commands"))],
            "value": [norm_text(x) for x in as_list(d.get("values"))],
        }
        for k in ent:
            tp, fp, fn = multiset_counts(gold_ents[k], pred_ents[k])
            ent[k][0] += tp; ent[k][1] += fp; ent[k][2] += fn

        ga = actions_for(g["gold"]["command"]) - {"OTHER"}
        pa = actions_for(as_list(d.get("commands"))) - {"OTHER"}
        tp, fp, fn = len(ga & pa), len(pa - ga), len(ga - pa)
        act[0] += tp; act[1] += fp; act[2] += fn
        a_ok = ga == pa
        act_exact += a_ok

        gc, pc = ga & RUNWAY_CRITICAL, pa & RUNWAY_CRITICAL
        if gc:
            crit_n += 1
            crit_exact += (gc == pc)
        crit_tp += len(gc & pc); crit_fp += len(pc - gc); crit_fn += len(gc - pc)

        r_ok = True
        if g.get("role") in ("ATCO", "PILOT"):
            role_n += 1
            r_ok = str(d.get("role", "")).upper() == g["role"]
            role_ok += r_ok

        cs_ok = collections.Counter(gold_ents["callsign"]) == collections.Counter(pred_ents["callsign"])
        full_exact += (cs_ok and a_ok and r_ok)

    price = (prices or {}).get(model_name or "", None)
    cost_total = None
    if price:
        cost_total = ptok / 1e6 * price["in"] + ctok / 1e6 * price["out"]

    def q(v, pctl):
        if not v:
            return None
        v = sorted(v)
        return v[min(len(v) - 1, int(round(pctl * (len(v) - 1))))]

    out = {
        "model": model_name, "file": os.path.basename(pred_path), "n": n, "missing": missing,
        "json_valid": valid / n,
        "callsign_f1": prf(*ent["callsign"])[2],
        "command_span_f1": prf(*ent["command"])[2],
        "value_f1": prf(*ent["value"])[2],
        "action_f1": prf(*act)[2],
        "action_exact": act_exact / n,
        "runway_critical_n": crit_n,
        "runway_critical_exact": crit_exact / crit_n if crit_n else None,
        "runway_critical_f1": prf(crit_tp, crit_fp, crit_fn)[2],
        "role_acc": role_ok / role_n if role_n else None,
        "full_record_exact": full_exact / n,
        "latency_p50_ms": q(lat, 0.5), "latency_p95_ms": q(lat, 0.95),
        "latency_mean_ms": statistics.mean(lat) if lat else None,
        "prompt_tokens": ptok, "completion_tokens": ctok,
        "cost_usd_total": cost_total,
        "cost_usd_per_1k_segments": (cost_total / n * 1000) if cost_total is not None else None,
    }
    return out


def fmt(v, kind="pct"):
    if v is None:
        return "—"
    if kind == "pct":
        return pct(v)
    if kind == "ms":
        return f"{v:.0f}"
    if kind == "usd":
        return f"${v:.4f}"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--prices", help="json: {model: {in: $/M, out: $/M}}")
    ap.add_argument("--out", help="write metrics json here")
    args = ap.parse_args()

    gold = [json.loads(l) for l in open(args.gold, encoding="utf-8") if l.strip()]
    prices = json.load(open(args.prices)) if args.prices else {}
    results = [score_file(gold, p, prices) for p in args.preds]

    cols = [
        ("model", "Model", "s"), ("json_valid", "JSON valid", "pct"),
        ("callsign_f1", "Callsign F1", "pct"), ("command_span_f1", "Cmd span F1", "pct"),
        ("value_f1", "Value F1", "pct"), ("action_f1", "Action F1", "pct"),
        ("runway_critical_exact", "Runway-critical exact", "pct"), ("role_acc", "Role acc", "pct"),
        ("full_record_exact", "Full record exact", "pct"),
        ("latency_p50_ms", "p50 ms", "ms"), ("latency_p95_ms", "p95 ms", "ms"),
        ("cost_usd_per_1k_segments", "$/1k segs", "usd"),
    ]
    print("| " + " | ".join(h for _, h, _ in cols) + " |")
    print("|" + "---|" * len(cols))
    for r in results:
        print("| " + " | ".join(fmt(r[k], kind) if kind != "s" else str(r[k]) for k, _, kind in cols) + " |")
    print(f"\n(n={gold.__len__()} segments; runway-critical subset n={results[0]['runway_critical_n']})")
    for r in results:
        if r["missing"]:
            print(f"WARNING: {r['file']} is missing {r['missing']} of {r['n']} ids — scored as empty")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(results, open(args.out, "w"), indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
