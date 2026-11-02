#!/usr/bin/env python3
"""The 'what a strong result looks like' chart, from results/test/scores.json.

Horizontal bars of the primary metric per arm, the before (off-the-shelf) arm hatched, every other arm annotated with its
paired delta vs the baseline and whether the 95% CI excludes zero ("significant") — the format the organizers showed at kickoff.

  python3 scripts/18_results_chart.py results/test/scores.json --baseline accounts/fireworks/models/qwen3-8b \
          --metric full_record_exact --out docs/results_full_record.png
  python3 scripts/18_results_chart.py results/test/scores.json --baseline accounts/fireworks/models/qwen3-8b \
          --metric runway_critical_exact --out docs/results_clearance_state.png

Requires the scores file to have been produced with the BASELINE FIRST in the arguments to bench/score.py (the paired
deltas are computed against the first arm). If it was not, pass --rescore to recompute deltas from the per-row records
(needs the preds files next to scores.json).
"""
import argparse, json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABELS = {  # model name → display name; the shot count is appended from the preds file name (_fsN)
    "accounts/fireworks/models/qwen3-8b": "Qwen3-8B off the shelf",
    "anthropic/claude-opus-5.5": "Claude Opus 5.5",
    "openai/gpt-5.5": "GPT-5.5",
    "openai/gpt-5.6-terra": "GPT-5.6 Terra",
    "openai/gpt-5.6-luna": "GPT-5.6 Luna",
    "atc-qwen3-8b": "Qwen3-8B + LoRA (dry-run adapter, DGX Spark)",
    "qwen3-8b-base": "Qwen3-8B off the shelf (DGX Spark)",
    "accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval": "Qwen3-8B + LoRA v2 (Fireworks SFT, hosted)",
    "router:lora->opus": "Router: LoRA → Opus on weak outputs",
}
import re


def display(r, labels):
    name = labels.get(r["model"], r["model"])
    m = re.search(r"_fs(\d+)", r.get("file", "") or "")
    if m:
        name += f", {m.group(1)}-shot" if m.group(1) != "0" else ", 0-shot"
    return name
TITLES = {"full_record_exact": "Full-record accuracy on the ATCO2 held-out airports (%)",
          "runway_critical_exact": "Clearance-state accuracy, runway-critical transmissions (%)",
          "action_f1": "Action F1 (%)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scores"); ap.add_argument("--baseline", required=True); ap.add_argument("--metric", default="full_record_exact")
    ap.add_argument("--out", required=True); ap.add_argument("--labels", help="json {model: label} overrides")
    ap.add_argument("--title", default="Before → after: does SFT beat the baseline?")
    ap.add_argument("--subtitle", default=None)
    args = ap.parse_args()
    res = json.load(open(args.scores))
    labels = dict(LABELS)
    if args.labels:
        labels.update(json.load(open(args.labels)))
    # the baseline is the FIRST arm in scores.json (that is what the paired deltas were computed against)
    if res[0]["model"] != args.baseline:
        raise SystemExit(f"first arm in scores.json is {res[0]['model']}, not {args.baseline}; "
                         "rerun scripts/11_score_test.sh with the baseline preds file first")
    m = args.metric
    rows = []
    for i, r in enumerate(res):
        v = r.get(m)
        if v is None:
            continue
        name = display(r, labels) + ("  (baseline)" if i == 0 else "")
        d = (r.get("delta_vs_first") or {}).get(m) or {}
        rows.append((name, 100 * v, d.get("delta"), d.get("ci95"), i == 0))
    rows.sort(key=lambda x: x[1])
    n = res[0]["n"] if m != "runway_critical_exact" else res[0]["runway_critical_n"]

    fig, ax = plt.subplots(figsize=(11, 0.55 * len(rows) + 2.2), dpi=160)
    palette = ["#1b1b1b", "#d6a77a", "#c2185b", "#2b0a3d", "#b3123e", "#e07b5a", "#c92a4f", "#d9cfae", "#4a4e69", "#8d99ae"]
    for i, (name, val, delta, ci, is_base) in enumerate(rows):
        color = "#e07b5a" if is_base else palette[i % len(palette)]
        ax.barh(i, val, color=color, hatch="////" if is_base else None, edgecolor="black" if is_base else color, height=0.62)
        ax.text(val + 0.8, i, f"{val:.1f}%", va="center", fontsize=10)
        if not is_base and delta is not None and ci:
            sig = (ci[0] > 0) or (ci[1] < 0)
            ax.text(104, i, f"{100 * delta:+.1f}pp  {'significant' if sig else 'n.s.'}", va="center", fontsize=9.5,
                    fontweight="bold" if sig else "normal", color="#7a1f1f" if sig else "#555")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_xlim(0, 100); ax.set_xlabel(TITLES.get(m, m)); ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(args.title, loc="left", fontsize=14, pad=18)
    fig.text(0.125, 0.93, args.subtitle or f"{n} held-out real transmissions · same prompt, scorer and rows for every arm · Δ = paired vs baseline, 95% bootstrap CI", fontsize=9, color="#444")
    fig.tight_layout(rect=(0, 0, 0.98, 0.94))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, bbox_inches="tight")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
