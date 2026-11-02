#!/usr/bin/env python3
"""Before → after, every open model we fine-tuned, on one picture: a dumbbell per base model (off the shelf → + our LoRA),
with the frontier reference models as vertical lines. Reads results/test/scores.json.

  python3 scripts/29_before_after_chart.py results/test/scores.json --out docs/before_after.png
"""
import argparse, json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, PAPER, MUTED = "#0b1220", "#f4f1ea", "#6a7179"
PAIRS = [  # (label, before file stem, after file stem, after label)
    ("Nemotron-3-Nano-30B-A3B", "nemotron-nano-30b-base_fwbatch-nothink_fs5", "atc-nemotron-nano-30b-v1_fwbatch-nothink_fs0", "+ our LoRA, 1 epoch"),
    ("Nemotron-3-Nano-30B-A3B", "nemotron-nano-30b-base_fwbatch-nothink_fs5", "atc-nemotron-nano-30b-v2_fwbatch-nothink_fs0", "+ our LoRA, 3 epochs"),
    ("Nemotron-3.5-Lightning-30B-A3B", "nemotron-lightning-30b-base_fwbatch-nothink_fs5", "atc-nemotron-lightning-30b-v2_fwbatch-nothink_fs0", "+ our LoRA, 3 epochs"),
    ("Nemotron-3.5-Lightning-30B-A3B", "nemotron-lightning-30b-base_fwbatch-nothink_fs5", "atc-nemotron-lightning-30b-v1_fwbatch-nothink_fs0", "+ our LoRA, 1 epoch"),
    ("Qwen3-8B", "qwen3-8b-base_spark_fs5", "atc-qwen3-8b-v2_fireworks_fs0", "+ our LoRA, 3 epochs (Fireworks)"),
    ("Qwen3-8B", "qwen3-8b-base_spark_fs5", "atc-qwen3-8b_spark_fs0", "+ our LoRA, 1 epoch (DGX Spark)"),
]
REFS = [("Claude Opus 5.5", "anthropic_claude-opus-5.5_fs5", "#c2185b"), ("Gemini 4 Argon", "google_gemini-4-argon_fs5", "#2b8a6e"),
        ("GPT-6.1 Terra Pro", "openai_gpt-6.1-terra-pro_fs5", "#e07b5a"), ("GPT-5.5", "openai_gpt-5.5_fs5", "#d6a77a")]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("scores"); ap.add_argument("--out", default="docs/before_after.png")
    ap.add_argument("--metric", default="full_record_exact"); a = ap.parse_args()
    res = {r["file"].replace(".preds.jsonl", ""): r for r in json.load(open(a.scores))}
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=170); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    ys = list(range(len(PAIRS)))[::-1]
    for y, (base, bf, af, alab) in zip(ys, PAIRS):
        b = 100 * res[bf][a.metric]; f = 100 * res[af][a.metric]
        ax.plot([b, f], [y, y], color=INK, lw=3, solid_capstyle="round", zorder=2)
        ax.scatter([b], [y], s=140, color=PAPER, edgecolor=INK, lw=2.2, zorder=3)
        ax.scatter([f], [y], s=160, color=INK, zorder=4)
        ax.text(b - 1.2, y, f"{b:.1f}", ha="right", va="center", fontsize=9.5, color=MUTED)
        ax.text(f + 1.2, y, f"{f:.1f}  (+{f - b:.1f})", ha="left", va="center", fontsize=10, color=INK, fontweight="bold")
        ax.text(20.5, y + 0.36, f"{base}  {alab}", ha="left", va="center", fontsize=9, color=MUTED)
    for i, (name, stem, col) in enumerate(REFS):
        v = 100 * res[stem][a.metric]
        ax.axvline(v, color=col, lw=1.6, ls=(0, (4, 3)), zorder=1)
        ax.text(v, len(PAIRS) - 0.55 + (i % 2) * 0.55, f"{v:.1f}", ha="center", va="bottom", fontsize=8.5, color=col, fontweight="bold")
        ax.text(99, len(PAIRS) - 0.1 - i * 0.42, f"— {name}, 5-shot  {v:.1f}", ha="right", va="center", fontsize=9, color=col)
    ax.set_xlim(20, 100); ax.set_ylim(-0.8, len(PAIRS) + 1.0)
    ax.set_yticks([]); ax.set_xlabel("Full-record accuracy on the 288 frozen test transmissions (%)  ·  ○ off the shelf, 5-shot   ● + our LoRA, 0-shot", color=INK, fontsize=9.5)
    ax.set_title("Before → after: the same recipe on three open models, next to the frontier", loc="left", color=INK, fontsize=13, fontweight="bold", pad=34)
    ax.grid(True, axis="x", color="#d9d4c7", lw=0.6); ax.tick_params(colors=MUTED)
    for s in ax.spines.values(): s.set_color("#d9d4c7")
    fig.text(0.01, 0.01, "Same prompt, scorer and rows for every arm. Every before→after gap is significant (McNemar p < 0.05 and recording-bootstrap 95% CI excludes 0). results/test/scores.md", fontsize=7.5, color=MUTED)
    fig.tight_layout(); fig.savefig(a.out, facecolor=PAPER, bbox_inches="tight"); print("wrote", a.out)


if __name__ == "__main__":
    main()
