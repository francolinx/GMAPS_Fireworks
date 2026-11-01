# ATC Clearance Extraction — open model vs. closed frontier baseline

**Fireworks: Deploy buildathon with Microsoft & NVIDIA · Nov 2, 2026 · San Francisco**

> Status: pre-event scaffold. Everything under "Results" is filled in during the build period.

## Project overview

**Task.** Parse a single air-traffic-control radio transmission (ASR-style transcript) into a structured
record: speaker role (controller / pilot), aircraft callsign(s), the instruction(s) given, and their
parameters (runway, level, frequency, heading…). The record feeds a deterministic runway-clearance state
engine (GMAPS) that flags conflicting runway authorizations — e.g. an aircraft cleared to cross a runway
another aircraft was just cleared to land on.

**Intended user.** Tower supervisors and ATC training programs (decision support only; the controller decides).

**Why a small open model.** A tower frequency produces a transmission every few seconds, 24/7. The parser
must be sub-second, cheap enough to run continuously on every frequency, and able to run on local hardware
(a DGX Spark in the tower) with no internet dependency. Closed frontier models are too slow and too
expensive per transmission for this workload, and cannot run on-prem.

**Approach.** TODO (Monday): prompted frontier baseline → prompted open base → LoRA fine-tuned open model
on Fireworks (and/or Nemotron on DGX Spark) → optional confidence router.

## Evaluation

- **Training data (disclosed):** ATCO2 train airports (gold), ATCOSIM + UWB-ATCC transcripts pseudo-labelled by a teacher model (validated as verbatim spans; training only), and synthetic US phraseology (JO 7110.65 style, gold by construction). Test is never any of these.
- **Dataset:** ATCO2-test-set-1h (Idiap / ATCO2 project), real recordings from 7 airports in 4 countries,
  with **gold** callsign / command / value annotations produced by the dataset authors, not by us.
  Source: https://www.atco2.org/data (research license — not redistributed here; `bench/prepare_data.py`
  downloads and parses it).
- **Split (by airport, no leakage):** test = Sydney (YSSY) + Prague (LKPR) + Bratislava (LZIB) = **288 segments**,
  three countries the model never sees in training. Train 504 / dev 85 from Bern, Sion, Zurich, Brno.
  Test-set hash committed before the build period: `data/splits/test.sha256`.
- **Metrics** (`bench/score.py`, identical for every arm):
  - callsign / command-span / value F1 (multiset, text-normalized)
  - **action F1** and action-set exact match after mapping command spans to 23 canonical actions
    (`bench/normalize.py`, rule table committed before the event)
  - **runway-critical exact match** on the subset whose gold actions include cleared-to-land / takeoff /
    line-up / hold-short / cross / vacate / go-around (n=70)
  - speaker-role accuracy, full-record exact match, JSON validity
  - latency p50/p95 (client-side wall clock, same machine for every arm), cost per 1k segments from
    published list prices (`results/prices.json`)
- **Baseline:** TODO (closed frontier model name, version, settings). Same system prompt, same few-shot
  examples (drawn from dev, never test), temperature 0, same scorer.

## Results

TODO — filled during the build period. Table produced by:

```
python bench/score.py data/splits/test.jsonl results/preds_*.jsonl --prices results/prices.json --out results/scores.json
```

| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| closed frontier (baseline) | | | | | | | | | | | |
| open base, prompted | | | | | | | | | | | |
| open, LoRA fine-tuned | | | | | | | | | | | |

## Tradeoffs and limitations

TODO. Known going in: the fine-tuned model is narrow (ATC phraseology only); test airports are European
and Australian English — US phraseology untested; the command→action table is heuristic (0.6% of gold
spans map to OTHER); the runway-critical subset is small (n=70); latency measured from a laptop over the
public internet, not in a tower.

## Repository map

```
bench/      data prep, action table, scorer, SFT builder, inference client (the benchmark)
scripts/    Spark work package: external data, synthetic US phraseology, pseudo-labelling, fine-tune, serve, eval, latency
viz/        GMAPS runway monitor — OSM geometry for KSFO, scenario builder, MapLibre page (presentation only)
prompts/    the one system prompt every arm uses
data/       gitignored; `splits/test.sha256` is committed (frozen before the event)
results/    scores and latency json; `prices.json` holds list prices per served model name
CLAUDE.md, PLAN.md, MONDAY.md, DISCLOSURE.md, STATUS.md — run books and disclosure
```

## Reproduce

```
python bench/prepare_data.py                      # download + parse + split, prints test sha256
python bench/normalize.py data/atco2_1h_gold.jsonl   # action-table coverage report
python bench/make_sft.py data/splits/train.jsonl data/sft/train.jsonl
python bench/make_sft.py data/splits/dev.jsonl   data/sft/dev.jsonl
BASE_URL=... API_KEY=... python bench/infer.py --model <name> --out results/preds_<name>.jsonl --fewshot 5
python bench/score.py data/splits/test.jsonl results/preds_*.jsonl --prices results/prices.json
```

The benchmark (`bench/`) needs only the Python 3.10+ standard library. `scripts/` needs `requirements.txt`; fine-tuning needs a GPU (we used a DGX Spark) and Unsloth or TRL.

## Pre-existing code and AI assistance (disclosure)

See `DISCLOSURE.md` — paste it here before submitting.

## Team

TODO

## Sponsor tracks

TODO — Fireworks (fine-tuning + serving), NVIDIA (Nemotron / DGX Spark), Microsoft (Phi) — state the
concrete technology use for each track entered.
