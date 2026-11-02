#!/usr/bin/env python3
"""Turn results/test/scores.json (from scripts/11_score_test.sh) into the README §4 markdown: the arm table,
the paired-CI table and the cost-at-tower-scale paragraph from measured token counts.

  python3 scripts/14_results_md.py results/test/scores.json --labels labels.json > results/test/README_results.md

labels.json (optional) maps the served model name → {"label": "...", "where": "..."}; unknown names fall back to the model id.
Tower-scale assumptions are printed with the numbers so a reader can redo the arithmetic.
"""
import argparse, json

DEFAULT_LABELS = {
    "anthropic/claude-opus-5.5": {"label": "Claude Opus 5.5, 5-shot (baseline)", "where": "API via OpenRouter"},
    "openai/gpt-5.5": {"label": "GPT-5.5, 5-shot", "where": "API via OpenRouter"},
    "openai/gpt-5.6-terra": {"label": "GPT-5.6 Terra, 5-shot", "where": "API via OpenRouter"},
    "accounts/fireworks/models/qwen3-8b": {"label": "Qwen3-8B base, 5-shot", "where": "Fireworks serverless"},
    "atc-qwen3-8b": {"label": "Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot", "where": "DGX Spark, on-prem"},
}
TRANSMISSIONS_PER_DAY = 10_000     # per major hub, all tower/ground frequencies — estimate, see README §1
US_TOWERS = 520                    # FAA + federal contract towers, approx.


def pct(x):
    return "—" if x is None else f"{100 * x:.1f}%"


def ms(x):
    return "—" if x is None else f"{x / 1000:.1f} s"


def usd(x, nd=2):
    return "—" if x is None else f"${x:,.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scores")
    ap.add_argument("--labels")
    ap.add_argument("--per-day", type=int, default=TRANSMISSIONS_PER_DAY)
    ap.add_argument("--towers", type=int, default=US_TOWERS)
    args = ap.parse_args()
    res = json.load(open(args.scores))
    labels = dict(DEFAULT_LABELS)
    if args.labels:
        labels.update(json.load(open(args.labels)))

    def lab(r):
        m = r.get("model") or r.get("file")
        L = labels.get(m, {})
        # file names carry _fsN; show the shot count if the label doesn't
        return L.get("label", m), L.get("where", "")

    n = res[0]["n"]; crit_n = res[0]["runway_critical_n"]
    print(f"| Arm | Where it ran | Clearance-state acc (n={crit_n}) | Full record exact (n={n}) | Action F1 | Callsign F1 | Role acc | JSON valid | p50 / p95 | $/1k |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in res:
        label, where = lab(r)
        print(f"| {label} | {where} | {pct(r['runway_critical_exact'])} | {pct(r['full_record_exact'])} | {pct(r['action_f1'])} | "
              f"{pct(r['callsign_f1'])} | {pct(r['role_acc'])} | {pct(r['json_valid'])} | {ms(r['latency_p50_ms'])} / {ms(r['latency_p95_ms'])} | "
              f"{usd(r['cost_usd_per_1k_segments'], 3) if r['cost_usd_per_1k_segments'] else '—'} |")

    base = res[0]
    print(f"\n**Paired 95% CIs vs {lab(base)[0]}** (row bootstrap on the same {n} transmissions; a Δ interval that excludes 0 is a difference the test set supports):\n")
    metrics = [("full_record_exact", "Full record exact"), ("runway_critical_exact", "Clearance-state acc"), ("action_f1", "Action F1"),
               ("callsign_f1", "Callsign F1"), ("role_acc", "Role acc")]
    print("| Arm | " + " | ".join(h for _, h in metrics) + " |")
    print("|---|" + "---|" * len(metrics))
    for r in res[1:]:
        cells = []
        for k, _ in metrics:
            d = (r.get("delta_vs_first") or {}).get(k) or {}
            if d.get("ci95") and d.get("delta") is not None:
                cells.append(f"{pct(r[k])} (Δ{100 * d['delta']:+.1f} [{100 * d['ci95'][0]:+.1f}, {100 * d['ci95'][1]:+.1f}])")
            else:
                cells.append(pct(r.get(k)))
        print(f"| {lab(r)[0]} | " + " | ".join(cells) + " |")

    print(f"\n**Cost at tower scale** ({args.per_day:,} transmissions/day per hub, list prices × measured token counts, {args.towers} US towers):\n")
    print("| Arm | $/1k | $/day/airport | $/yr, all US towers |")
    print("|---|---|---|---|")
    for r in res:
        c = r.get("cost_usd_per_1k_segments")
        if c is None:
            continue
        day = c / 1000 * args.per_day
        print(f"| {lab(r)[0]} | {usd(c, 3)} | {usd(day)} | {usd(day * 365 * args.towers, 0)} |")
    print("\nOn-prem arms carry no per-token cost; the hardware (one DGX Spark per tower, ~$4k) is amortised separately. "
          "Only the on-prem arms can run without sending live tower audio off-site.")


if __name__ == "__main__":
    main()
