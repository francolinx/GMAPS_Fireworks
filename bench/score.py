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
from normalize import actions_for, RUNWAY_CRITICAL, NON_ACTIONS  # noqa: E402

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
    # greedy first (handles a single object with trailing prose), then the first non-nested object
    # (handles models that append a second object or commentary with braces). The schema has no nested objects.
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, s, re.S)
        if m:
            try:
                d = json.loads(m.group(0))
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
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
    per_row = []   # one record per gold row: the pieces every aggregate metric is built from

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
        parsed_ok = d is not None
        if parsed_ok:
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

        ga = actions_for(g["gold"]["command"]) - NON_ACTIONS
        pa = actions_for(as_list(d.get("commands"))) - NON_ACTIONS
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
        per_row.append({
            "valid": parsed_ok,
            "cs": multiset_counts(gold_ents["callsign"], pred_ents["callsign"]),
            "act": (tp, fp, fn), "a_ok": a_ok,
            "crit": (gc == pc) if gc else None,
            "role": r_ok if g.get("role") in ("ATCO", "PILOT") else None,
            "full": bool(cs_ok and a_ok and r_ok),
        })

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
        "_rows": per_row,
    }
    return out


BOOT_METRICS = ("callsign_f1", "action_f1", "action_exact", "runway_critical_exact", "role_acc", "full_record_exact")


def aggregate(rows):
    """Recompute the headline metrics from a list of per-row records (used by the bootstrap)."""
    n = len(rows) or 1
    cs = [sum(r["cs"][i] for r in rows) for i in range(3)]
    act = [sum(r["act"][i] for r in rows) for i in range(3)]
    crit = [r["crit"] for r in rows if r["crit"] is not None]
    role = [r["role"] for r in rows if r["role"] is not None]
    return {
        "callsign_f1": prf(*cs)[2], "action_f1": prf(*act)[2],
        "action_exact": sum(r["a_ok"] for r in rows) / n,
        "runway_critical_exact": (sum(crit) / len(crit)) if crit else None,
        "role_acc": (sum(role) / len(role)) if role else None,
        "full_record_exact": sum(r["full"] for r in rows) / n,
    }


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p-value: b = only A right, c = only B right; under H0 b ~ Binomial(b+c, 1/2)."""
    from math import comb
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def bootstrap(results, iters=2000, seed=0, clusters=None):
    """Resampled 95% CIs per arm and PAIRED CIs for (arm − first arm) on the same resampled rows.

    clusters: optional list (len = rows) of cluster ids (e.g. the recording a segment came from). When given, whole
    clusters are resampled with replacement (segments from one recording share a speaker, channel and airport, so they
    are not independent); otherwise single rows are. Also computes exact McNemar on full-record exact vs the first arm.
    """
    import random
    rng = random.Random(seed)
    n = len(results[0]["_rows"])
    samples = {i: {m: [] for m in BOOT_METRICS} for i in range(len(results))}
    diffs = {i: {m: [] for m in BOOT_METRICS} for i in range(1, len(results))}
    groups = None
    if clusters:
        groups = {}
        for j, c in enumerate(clusters):
            groups.setdefault(c, []).append(j)
        keys = list(groups)
    base_full = [r["full"] for r in results[0]["_rows"]]
    for i, res in enumerate(results):
        if i == 0:
            continue
        arm_full = [r["full"] for r in res["_rows"]]
        b = sum(1 for x, y in zip(arm_full, base_full) if x and not y)   # only this arm right
        c = sum(1 for x, y in zip(arm_full, base_full) if y and not x)   # only the baseline right
        res["mcnemar_vs_first"] = {"only_arm_right": b, "only_first_right": c, "p": mcnemar_exact(b, c)}
    for _ in range(iters):
        if groups:
            idx = [j for k in (rng.choice(keys) for _ in range(len(keys))) for j in groups[k]]
        else:
            idx = [rng.randrange(n) for _ in range(n)]
        aggs = [aggregate([res["_rows"][j] for j in idx]) for res in results]
        for i, a in enumerate(aggs):
            for m in BOOT_METRICS:
                if a[m] is not None:
                    samples[i][m].append(a[m])
                    if i > 0 and aggs[0][m] is not None:
                        diffs[i][m].append(a[m] - aggs[0][m])

    def ci(v):
        if not v:
            return None
        v = sorted(v)
        return [v[int(0.025 * (len(v) - 1))], v[int(0.975 * (len(v) - 1))]]
    for i, res in enumerate(results):
        res["ci95"] = {m: ci(samples[i][m]) for m in BOOT_METRICS}
        if i > 0:
            res["delta_vs_first"] = {m: {"delta": (res[m] - results[0][m]) if res[m] is not None and results[0][m] is not None else None,
                                         "ci95": ci(diffs[i][m])} for m in BOOT_METRICS}


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
    ap.add_argument("--bootstrap", type=int, default=2000, help="bootstrap iterations for 95%% CIs (0 to skip)")
    ap.add_argument("--cluster", choices=["none", "recording"], default="recording",
                    help="resample whole recordings (id prefix before '#') instead of single rows; default recording")
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

    if args.bootstrap and results and results[0]["_rows"]:
        clusters = [g["id"].split("#")[0] for g in gold] if args.cluster == "recording" else None
        bootstrap(results, iters=args.bootstrap, clusters=clusters)
        if clusters:
            print(f"\n(bootstrap resamples whole recordings: {len(set(clusters))} recordings in {len(gold)} segments)")
        labels = {"callsign_f1": "Callsign F1", "action_f1": "Action F1", "action_exact": "Action exact",
                  "runway_critical_exact": "Runway-critical exact", "role_acc": "Role acc", "full_record_exact": "Full record exact"}
        kind = "recording-cluster bootstrap" if clusters else "row bootstrap"
        print(f"\n95% CIs ({kind}, {args.bootstrap} iters); Δ is paired vs. {results[0]['model']}:\n")
        print("| Metric | " + " | ".join(str(r["model"]) for r in results) + " |")
        print("|---|" + "---|" * len(results))
        for m in BOOT_METRICS:
            cells = []
            for i, r in enumerate(results):
                c = r["ci95"].get(m)
                cell = "—" if r.get(m) is None or not c else f"{pct(r[m])} [{pct(c[0])}, {pct(c[1])}]"
                if i > 0 and r.get("delta_vs_first", {}).get(m, {}).get("ci95"):
                    d = r["delta_vs_first"][m]
                    cell += f" Δ{100 * d['delta']:+.1f} [{100 * d['ci95'][0]:+.1f}, {100 * d['ci95'][1]:+.1f}]"
                cells.append(cell)
            print(f"| {labels[m]} | " + " | ".join(cells) + " |")
        print("\nA Δ interval that excludes 0 is a difference the test set supports; one that straddles 0 is a tie.")
        print("\nExact McNemar on full-record exact vs the first arm (rows where exactly one is right):\n")
        print("| Arm | only arm right | only first right | McNemar p | verdict |")
        print("|---|---|---|---|---|")
        for r in results[1:]:
            mc = r.get("mcnemar_vs_first")
            if not mc:
                continue
            ci = (r.get("delta_vs_first") or {}).get("full_record_exact", {}).get("ci95")
            both = mc["p"] < 0.05 and ci and (ci[0] > 0 or ci[1] < 0)
            verdict = "significant (both tests)" if both else "not significant"
            print(f"| {r['model']} | {mc['only_arm_right']} | {mc['only_first_right']} | {mc['p']:.2g} | {verdict} |")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump([{k: v for k, v in r.items() if k != "_rows"} for r in results], open(args.out, "w"), indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
