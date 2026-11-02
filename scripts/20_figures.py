#!/usr/bin/env python3
"""Two README figures: the training-loss curve(s) and per-action recall of the test arms.

  python3 scripts/20_figures.py loss  results/train_log_qwen3-8b-atc.json[:label] [results/fw_metrics_v2.jsonl:label ...] --out docs/loss_curve.png
  python3 scripts/20_figures.py recall data/splits/test.jsonl results/test/<base>.preds.jsonl results/test/<lora>.preds.jsonl [more preds] --out docs/per_action_recall.png

Loss inputs: the local TRL log (dict with `log_history` of {step, loss, epoch}) or a Fireworks metrics.jsonl (one JSON per
line with step/loss-like keys). Recall: gold rows containing an action class vs. the arm's predicted action set
(`bench/normalize.py`, identical to the scorer) — the per-class view behind "where we still lose to Opus".
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list  # noqa: E402
from normalize import actions_for, NON_ACTIONS, RUNWAY_CRITICAL  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, PAPER, MUTED = "#0b1220", "#f4f1ea", "#6a7179"
COLORS = ["#0b1220", "#c2185b", "#e07b5a", "#39a0c8", "#3ddc84", "#ffb13b"]


def read_loss(spec):
    path, _, label = spec.partition(":")
    label = label or os.path.basename(path)
    if path.endswith(".json"):
        d = json.load(open(path))
        hist = d.get("log_history", d if isinstance(d, list) else [])
        pts = [(h.get("epoch") or h.get("step"), h["loss"]) for h in hist if "loss" in h and h.get("step")]
        x_is_epoch = any(h.get("epoch") is not None for h in hist)
    else:
        pts, x_is_epoch = [], False
        for l in open(path):
            if not l.strip():
                continue
            h = json.loads(l)
            loss = h.get("loss", h.get("train_loss", h.get("loss_mean")))
            x = h.get("epoch", h.get("step"))
            if loss is not None and x is not None:
                pts.append((float(x), float(loss)))
                x_is_epoch = x_is_epoch or ("epoch" in h)
    return label, pts, x_is_epoch


def cmd_loss(args):
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    xlabel = "step"
    for i, spec in enumerate(args.logs):
        label, pts, is_epoch = read_loss(spec)
        if not pts:
            print("no points in", spec); continue
        xs, ys = zip(*pts)
        ax.plot(xs, ys, lw=2, color=COLORS[i % len(COLORS)], label=label)
        xlabel = "epoch" if is_epoch else "step"
    ax.set_xlabel(xlabel, color=INK); ax.set_ylabel("training loss per token (log scale)", color=INK); ax.set_yscale("log")
    ax.set_title(args.title, color=INK, loc="left", fontsize=12, fontweight="bold")
    ax.grid(True, color="#d9d4c7", lw=0.6); ax.tick_params(colors=MUTED)
    for s in ax.spines.values(): s.set_color("#d9d4c7")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(args.out, facecolor=PAPER); print("wrote", args.out)


def cmd_recall(args):
    gold = [json.loads(l) for l in open(args.gold, encoding="utf-8") if l.strip()]
    arms = []
    for p in args.preds:
        rows = {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
        name = next(iter(rows.values()))["model"].split("/")[-1]
        tag = os.path.basename(p).replace(".preds.jsonl", "")
        fs = tag.rsplit("_fs", 1)[-1]
        arms.append((f"{name}, {fs}-shot" if fs != "0" else f"{name}, 0-shot", rows))
    class_n = collections.Counter(); hits = {a: collections.Counter() for a, _ in arms}
    for g in gold:
        gacts = actions_for(g["gold"]["command"]) - NON_ACTIONS
        for a in gacts:
            class_n[a] += 1
        for name, rows in arms:
            d = parse_output(rows.get(g["id"], {}).get("output", "")) or {}
            pacts = actions_for(as_list(d.get("commands"))) - NON_ACTIONS
            for a in gacts & pacts:
                hits[name][a] += 1
    classes = [a for a, n in class_n.most_common() if n >= args.min_n]
    fig, ax = plt.subplots(figsize=(10, 0.42 * len(classes) + 1.6), dpi=160)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    import numpy as np
    y = np.arange(len(classes)); h = 0.8 / len(arms)
    for i, (name, _) in enumerate(arms):
        vals = [100 * hits[name][c] / class_n[c] for c in classes]
        ax.barh(y + (i - (len(arms) - 1) / 2) * h, vals, height=h * 0.95, color=COLORS[i % len(COLORS)], label=name)
    ax.set_yticks(y); ax.set_yticklabels([f"{c}{' ●' if c in RUNWAY_CRITICAL else ''}  (n={class_n[c]})" for c in classes], color=INK, fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("recall on gold rows containing the action, %", color=INK)
    ax.set_title("Per-action recall on the frozen test split  (● runway-critical)", color=INK, loc="left", fontsize=12, fontweight="bold")
    ax.grid(True, axis="x", color="#d9d4c7", lw=0.6); ax.tick_params(colors=MUTED)
    for s in ax.spines.values(): s.set_color("#d9d4c7")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=len(arms), fontsize=9)
    fig.tight_layout(); fig.savefig(args.out, facecolor=PAPER, bbox_inches="tight"); print("wrote", args.out)
    for c in classes:
        print(f"{c:22s} n={class_n[c]:3d} " + "  ".join(f"{name}: {100*hits[name][c]/class_n[c]:5.1f}%" for name, _ in arms))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("loss"); p.add_argument("logs", nargs="+"); p.add_argument("--out", default="docs/loss_curve.png")
    p.add_argument("--title", default="LoRA training loss, Qwen3-8B"); p.set_defaults(fn=cmd_loss)
    p = sub.add_parser("recall"); p.add_argument("gold"); p.add_argument("preds", nargs="+"); p.add_argument("--out", default="docs/per_action_recall.png")
    p.add_argument("--min-n", type=int, default=5); p.set_defaults(fn=cmd_recall)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
