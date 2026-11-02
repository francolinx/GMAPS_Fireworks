#!/usr/bin/env python3
"""The five-second table: one row per system, sorted by the headline metric, with the paired verdict vs the first arm
(the off-the-shelf baseline) and the list-price cost of the 288-row test run. Same shape as the organizers' sample project.

  python3 scripts/28_leaderboard.py results/test/scores.json [--labels labels.json] > docs/leaderboard.md
"""
import argparse, json, re

LABELS = {
    "qwen3-8b-base_spark_fs5": "Qwen3-8B off the shelf (baseline)",
    "atc-qwen3-8b_spark_fs0": "Qwen3-8B + LoRA v1 (1 epoch, DGX Spark)",
    "atc-qwen3-8b-v2_fireworks_fs0": "Qwen3-8B + LoRA v2 (3 epochs, Fireworks)",
    "nemotron-nano-30b-base_fwbatch-nothink_fs5": "Nemotron-3-Nano-30B-A3B off the shelf",
    "atc-nemotron-nano-30b-v1_fwbatch-nothink_fs0": "**Nemotron-3-Nano-30B-A3B + LoRA** (1 epoch, Fireworks)",
    "atc-nemotron-nano-30b-v2_fwbatch-nothink_fs0": "**Nemotron-3-Nano-30B-A3B + LoRA** (3 epochs, Fireworks)",
    "nemotron-lightning-30b-base_fwbatch-nothink_fs5": "Nemotron-3.5-Lightning-30B-A3B off the shelf",
    "atc-nemotron-lightning-30b-v1_fwbatch-nothink_fs0": "Nemotron-3.5-Lightning-30B-A3B + LoRA (1 epoch, Fireworks)",
    "atc-nemotron-lightning-30b-v2_fwbatch-nothink_fs0": "Nemotron-3.5-Lightning-30B-A3B + LoRA (3 epochs, Fireworks)",
    "anthropic_claude-opus-5.5_fs5": "Claude Opus 5.5",
    "anthropic_claude-opus-5.5_fs20": "Claude Opus 5.5, 20-shot",
    "openai_gpt-6.1-terra-pro_fs5": "GPT-6.1 Terra Pro",
    "openai_gpt-5.5_fs5": "GPT-5.5",
    "openai_gpt-5.6-terra_fs5": "GPT-5.6 Terra",
    "google_gemini-4-argon_fs5": "Gemini 4 Argon",
    "router_lora-opus_fs0": "Router: LoRA v1 → Opus on weak outputs",
    "nemotron-nano-30b-base_fwbatch_fs5": "Nemotron-30B off the shelf, reasoning on (first attempt)",
    "atc-nemotron-nano-30b-v1_fwbatch_fs0": "Nemotron-30B + LoRA, reasoning on (first attempt)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scores"); ap.add_argument("--labels"); ap.add_argument("--metric", default="full_record_exact")
    a = ap.parse_args()
    labels = dict(LABELS)
    if a.labels:
        labels.update(json.load(open(a.labels)))
    res = json.load(open(a.scores))
    base = res[0]
    rows = []
    for i, r in enumerate(res):
        stem = r["file"].replace(".preds.jsonl", "")
        name = labels.get(stem, r["model"])
        m = re.search(r"_fs(\d+)$", stem)
        shots = int(m.group(1)) if m else 0
        if shots and "shot" not in name and "LoRA" not in name:
            name += f", {shots}-shot"
        acc = 100 * r[a.metric]; rc = 100 * r["runway_critical_exact"]
        cost = r.get("cost_usd_total")
        cost_s = "—" if cost is None else ("~$0 (on-prem)" if cost == 0 else f"${cost:.2f}")
        if i == 0:
            vs = ""
        else:
            d = r["delta_vs_first"][a.metric]; mc = r.get("mcnemar_vs_first", {})
            lo, hi = d["ci95"]; p = mc.get("p")
            sig = (lo > 0 or hi < 0) and (p is not None and p < 0.05)
            if sig and d["delta"] > 0:
                vs = f"+{100*d['delta']:.1f}, significant"
            elif sig:
                vs = f"{100*d['delta']:.1f}, significant loss"
            else:
                vs = f"{100*d['delta']:+.1f}, not significant"
        rows.append((acc, name, rc, vs, cost_s, i == 0))
    rows.sort(key=lambda t: -t[0])
    print("| System | Full-record accuracy | Clearance-state accuracy | vs base Qwen3-8B | Cost of the 288-transmission run |")
    print("|---|---|---|---|---|")
    for acc, name, rc, vs, cost_s, is_base in rows:
        b = "**" if (name.startswith("**") or False) else ""
        nm = name if not is_base else f"{name}"
        print(f"| {nm} | {b}{acc:.1f}%{b} | {rc:.1f}% | {vs} | {cost_s} |")


if __name__ == "__main__":
    main()
