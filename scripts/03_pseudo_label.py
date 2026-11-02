#!/usr/bin/env python3
"""Pseudo-label external transcripts with a teacher model, then validate hard.

Step 1 (any OpenAI-compatible teacher — frontier API, Fireworks, or a local vLLM on the Spark):
  BASE_URL=http://localhost:8002/v1 API_KEY=none \
    python bench/infer.py --model <teacher> --split data/external/uwb_atcc.jsonl \
      --out data/pseudo/uwb_atcc.preds.jsonl --fewshot 8 --concurrency 16 --json-mode

Step 2 (this script): turn teacher predictions into gold-format rows, keeping only rows where
  - the output parsed as JSON,
  - every callsign/command/value span is a verbatim substring of the transcript (no paraphrase, no hallucination),
  - at least one command maps to a known action, OR there are no commands but ≥1 value or a callsign (callsign-only calls exist in gold),
and take the speaker role from the SOURCE when it is known (UWB ids carry it; ATCOSIM is controller-only).

  python scripts/03_pseudo_label.py data/external/uwb_atcc.jsonl data/pseudo/uwb_atcc.preds.jsonl data/pseudo/uwb_atcc.gold.jsonl

Disclose in the README: these labels are teacher-generated, used for TRAINING ONLY, never for evaluation.
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bench"))
from score import parse_output, as_list, norm_text  # noqa: E402
from normalize import actions_for  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("external")
    ap.add_argument("preds")
    ap.add_argument("out")
    ap.add_argument("--teacher-name", default=None, help="recorded in each row for disclosure")
    args = ap.parse_args()

    ext = {}
    for l in open(args.external, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); ext[r["id"]] = r
    preds = {}
    teacher = args.teacher_name
    for l in open(args.preds, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); preds[r["id"]] = r; teacher = teacher or r.get("model")

    stats = collections.Counter()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    kept = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for rid, r in ext.items():
            p = preds.get(rid)
            if not p:
                stats["missing"] += 1; continue
            d = parse_output(p.get("output"))
            if not d:
                stats["bad_json"] += 1; continue
            text = r["text"]
            spans = {k: [" ".join(str(s).split()) for s in as_list(d.get(k2))] for k, k2 in (("callsign", "callsigns"), ("command", "commands"), ("value", "values"))}
            if any(norm_text(s) not in norm_text(text) or not s for k in spans for s in spans[k]):
                stats["span_not_in_text"] += 1; continue
            acts = actions_for(spans["command"]) - {"OTHER"}
            if spans["command"] and not acts:
                stats["unknown_action"] += 1; continue
            if not spans["command"] and not spans["value"] and not spans["callsign"]:
                stats["empty"] += 1; continue      # nothing extracted at all; callsign-only calls are kept (they exist in gold)
            role = r.get("role") if r.get("role") in ("ATCO", "PILOT") else str(d.get("role", "UNKNOWN")).upper()
            if role not in ("ATCO", "PILOT", "UNKNOWN"):
                role = "UNKNOWN"
            fh.write(json.dumps({
                "id": rid, "airport": r.get("source", "ext"), "facility": r.get("facility", "unknown"),
                "speaker_label": role, "role": role, "text": text, "gold": spans,
                "source": f"pseudo:{r.get('source', 'ext')}", "teacher": teacher,
            }, ensure_ascii=False) + "\n")
            kept += 1; stats["kept"] += 1
    print(f"kept {kept} / {len(ext)}  {dict(stats)}  → {args.out}")


if __name__ == "__main__":
    main()
