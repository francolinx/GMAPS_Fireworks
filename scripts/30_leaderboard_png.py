#!/usr/bin/env python3
"""The leaderboard as a picture in the organizers' table format (System · Accuracy · secondary · vs base · cost), with our
fine-tuned rows highlighted so they read in two seconds on a projector.

  python3 scripts/30_leaderboard_png.py results/test/scores.json --out docs/leaderboard.png
"""
import argparse, json, re, sys, os

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABELS = {
    "qwen3-8b-base_spark_fs5": "Qwen3-8B off the shelf, 5-shot (baseline)",
    "atc-qwen3-8b_spark_fs0": "Qwen3-8B + GMAPS LoRA, 1 epoch (DGX Spark)",
    "atc-qwen3-8b-v2_fireworks_fs0": "Qwen3-8B + GMAPS LoRA, 3 epochs (Fireworks)",
    "nemotron-nano-30b-base_fwbatch-nothink_fs5": "Nemotron-3-Nano-30B-A3B off the shelf, 5-shot",
    "nemotron-nano-30b-base_fwbatch-nothink_fs20": "Nemotron-3-Nano-30B-A3B off the shelf, 20-shot",
    "atc-nemotron-nano-30b-v1_fwbatch-nothink_fs0": "Nemotron-3-Nano-30B-A3B + GMAPS LoRA, 1 epoch",
    "atc-nemotron-nano-30b-v2_fwbatch-nothink_fs0": "Nemotron-3-Nano-30B-A3B + GMAPS LoRA, 3 epochs",
    "nemotron-lightning-30b-base_fwbatch-nothink_fs5": "Nemotron-3.5-Lightning-30B-A3B off the shelf, 5-shot",
    "nemotron-lightning-30b-base_fwbatch-nothink_fs20": "Nemotron-3.5-Lightning-30B-A3B off the shelf, 20-shot",
    "atc-nemotron-lightning-30b-v1_fwbatch-nothink_fs0": "Nemotron-3.5-Lightning-30B-A3B + GMAPS LoRA, 1 epoch",
    "atc-nemotron-lightning-30b-v2_fwbatch-nothink_fs0": "Nemotron-3.5-Lightning-30B-A3B + GMAPS LoRA, 3 epochs",
    "anthropic_claude-opus-5.5_fs5": "Claude Opus 5.5, 5-shot",
    "anthropic_claude-opus-5.5_fs20": "Claude Opus 5.5, 20-shot",
    "google_gemini-4-argon_fs5": "Gemini 4 Argon, 5-shot",
    "openai_gpt-6.1-terra-pro_fs5": "GPT-6.1 Terra Pro, 5-shot",
    "openai_gpt-5.5_fs5": "GPT-5.5, 5-shot",
    "openai_gpt-5.6-terra_fs5": "GPT-5.6 Terra, 5-shot",
    "router_lora-opus_fs0": "Router: Qwen LoRA → Opus on weak outputs",
}
SKIP = ("nemotron-nano-30b-base_fwbatch_fs5", "atc-nemotron-nano-30b-v1_fwbatch_fs0")   # reasoning-on first attempts: in the README table, not on the card


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("scores"); ap.add_argument("--out", default="docs/leaderboard.png")
    ap.add_argument("--top", type=int, default=0, help="only the first N rows (0 = all)"); a = ap.parse_args()
    res = json.load(open(a.scores))
    rows = []
    for i, r in enumerate(res):
        stem = r["file"].replace(".preds.jsonl", "")
        if stem in SKIP:
            continue
        ours = "+ GMAPS LoRA" in LABELS.get(stem, "")
        acc = 100 * r["full_record_exact"]; rc = 100 * r["runway_critical_exact"]
        if i == 0:
            vs = "baseline"
        else:
            d = r["delta_vs_first"]["full_record_exact"]; p = (r.get("mcnemar_vs_first") or {}).get("p", 1); lo, hi = d["ci95"]
            sig = (lo > 0 or hi < 0) and p < 0.05
            vs = f"{100*d['delta']:+.1f}, " + ("significant" if sig else "not significant")
        cost = r.get("cost_usd_per_1k_segments")
        cost_s = "mixed" if cost is None else ("~$0 on-prem" if cost == 0 else f"${cost:.2f}")
        rows.append((acc, LABELS.get(stem, r["model"]), f"{acc:.1f}%", f"{rc:.1f}%", vs, cost_s, ours, i == 0))
    rows.sort(key=lambda t: -t[0])
    if a.top:
        rows = rows[: a.top]
    n = len(rows)
    fig, ax = plt.subplots(figsize=(12.5, 0.34 * n + 0.9), dpi=170); fig.patch.set_facecolor("#ffffff"); ax.set_axis_off()
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.06)
    cols = ["System", "Full record", "Clearance-state", "vs base Qwen3-8B", "Cost / 1k"]
    cells = [[r[1], r[2], r[3], r[4], r[5]] for r in rows]
    tbl = ax.table(cellText=cells, colLabels=cols, loc="center", cellLoc="left", colLoc="left", colWidths=[0.47, 0.12, 0.14, 0.17, 0.10], bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(10)
    for (ri, ci), cell in tbl.get_celld().items():
        cell.set_edgecolor("#e3e6ec"); cell.set_linewidth(0.6)
        if ri == 0:
            cell.set_facecolor("#0b1220"); cell.get_text().set_color("#ffffff"); cell.get_text().set_fontweight("bold")
            continue
        acc, _, _, _, _, _, ours, base = rows[ri - 1]
        if ours:
            cell.set_facecolor("#e3f6ea"); cell.get_text().set_color("#0b5d2a"); cell.get_text().set_fontweight("bold")
        elif base:
            cell.set_facecolor("#fff4e0"); cell.get_text().set_color("#0b1220")
        else:
            cell.set_facecolor("#ffffff" if ri % 2 else "#f5f6f8"); cell.get_text().set_color("#0b1220")
        if ci == 1:
            cell.get_text().set_fontweight("bold")
    fig.suptitle("GMAPS parser benchmark — 288 real tower transmissions, 3 unseen airports (ATCO2 gold, frozen Oct 31)",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color="#0b1220")
    fig.text(0.01, 0.005, "green = our fine-tuned models · amber = the pre-registered baseline · significant = McNemar p < 0.05 and recording-bootstrap 95% CI excludes 0 · cost = list price × measured tokens · results/test/scores.md",
             fontsize=7.5, color="#6a7179")
    fig.savefig(a.out, facecolor="#ffffff"); print("wrote", a.out, n, "rows")


if __name__ == "__main__":
    main()
