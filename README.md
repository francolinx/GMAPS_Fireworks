# GMAPS — real tower radio → runway clearance state, on a fine-tuned open model

**Fireworks: Deploy buildathon with Microsoft & NVIDIA · Nov 2, 2026 · San Francisco**

> **Status: pre-event draft.** Every number under *Results* is filled in during the build period from `results/test/`. Delete this line before submitting.

![GMAPS runway monitor — KSFO 28L, SIM212 cleared to land, RESCUE7 cleared to cross at E](docs/runway_monitor_sfo_28l.png)

**One sentence.** A fine-tuned 8B open model parses real air-traffic-control radio into the structured record a runway-conflict engine needs, at **[N]% clearance-state accuracy on 288 real transmissions from three airports it never saw, vs [M]% for [frontier model]**, at 1/[K] the per-transmission cost — and the same adapter runs in the tower on a DGX Spark with no internet.

## 1. Project overview

**The problem.** A runway incursion begins as two clearances that cannot both be true: one aircraft cleared to land on 28L, a vehicle cleared to cross 28L at taxiway E. The words are on the frequency before anything moves; today the cross-check lives in one controller's head. The FAA logged 1,758 runway incursions in FY2024 and over 1,600 in 2025, with severe (Category A/B) events up 44% year over year ([DOT IG FY2024 report](https://www.oig.dot.gov/), [FAASTeam 2025 notice via AVweb](https://www.avweb.com/aviation-news/severe-runway-incursions-jump-44-percent/)).

**What GMAPS does.** It listens to the tower/ground frequency, turns each transmission into a typed record — `{role, callsigns, commands, values}` — and keeps a ledger of who is cleared to do what on each runway. When two authorizations hold one runway at the same time, it warns, names both sides and the rule (FAA JO 7110.65 §3-1-3, §3-7-2), and projects whether the two movers will meet. **Decision support only; the controller decides.** The ledger and the look-ahead are deterministic code; the only learned component is the parser, and that is what this submission benchmarks.

**Why an open model, and why fine-tuned.** Three constraints, in order:
1. **It cannot leave the building.** Live tower audio is safety-critical operational data; no ANSP will stream it to a third-party API. The parser has to run on hardware in the tower. That rules out closed models before cost is even considered.
2. **It runs on every frequency, all day.** A major hub produces on the order of 10,000 transmissions/day across its tower and ground frequencies (≈1,100 daily operations × 6–10 transmissions each — our estimate from SFO's ~400k annual operations). The parser must keep up with all of them at once.
3. **It must be right in the words that matter.** "cleared to land" vs "cleared for takeoff" vs "line up and wait" vs "hold short" — the ledger is only as good as the span the parser extracts. A general model paraphrases; a fine-tuned one learns the convention.

**Intended user.** Tower supervisors and ATC training programs — a second set of eyes on the frequency, not an automation. Adoption path: pilot with university aviation programs (we have working contacts at Embry-Riddle and CCBC from earlier GMAPS work) → contract towers → FAA towers.

## 2. Task definition

**Input:** one radio transmission as an ASR-style transcript (lower-case, numbers spelled out) plus the facility it was heard on.
**Output:** `{"role": ATCO|PILOT|UNKNOWN, "callsigns": [...], "commands": [...], "values": [...]}` — spans as spoken, no normalization (the prompt is `prompts/system.txt`, identical for every arm).
**Downstream:** command spans are mapped to canonical actions (`bench/normalize.py`, rule table committed before the event); the ledger consumes `(callsign, action, runway)`. Two classes are **not** actions and are dropped from both gold and prediction before any action metric: `ACK` (acknowledgements, read-back filler, requests — "confirm", "say again", "is approved", "make") and `OTHER` (unmapped). The ledger never consumes them, and ATCO2 tags them inconsistently; scoring them would reward mimicking annotation habits rather than extracting instructions. This rule was fixed on Nov 2 at 08:40 PT, before any test-split run, after inspecting frontier errors on the *dev* split (`results/dev/`); it raises every arm's action scores, the frontier's included.

## 3. Evaluation

**Test set — real, third-party gold, frozen before the event.**
- [ATCO2-test-set-1h](https://www.atco2.org/data) (Idiap Research Institute / ATCO2 project): real recordings from 7 airports in 4 countries, manually transcribed, with gold callsign / command / value annotations produced by the dataset authors — not by us, not by a model. Research license; not redistributed here (`bench/prepare_data.py` downloads and reproduces the split).
- **Split by airport, no leakage:** test = Sydney (YSSY) + Prague (LKPR) + Bratislava (LZIB) = **288 transmissions, three countries the model never sees in training**. Train 504 / dev 85 from Bern, Sion, Zurich, Brno. Test is pilot-heavy (148 pilot / 128 controller) while train is controller-heavy — a real distribution shift, reported as such.
- `sha256(test.jsonl) = 8660e6de…31cd`, committed Oct 31 (`data/splits/test.sha256`); `scripts/10_eval_test.sh` refuses to run if the hash changes. Test was first evaluated during the build period.

**Metrics** (`bench/score.py`, identical for every arm, with row-bootstrap 95% CIs and *paired* deltas vs the baseline on the same 288 rows):

| Metric | What it answers |
|---|---|
| **Clearance-state accuracy** (`runway_critical_exact`, n=70) | After this transmission, would the ledger hold the correct runway state? Exact match of the runway-occupancy action set (cleared-to-land / takeoff / line-up / hold-short / cross / vacate / go-around) on the subset where gold contains one. **This is the number that matters operationally.** |
| **Full-record exact** (n=288) | Role + callsigns + action set all correct — the record the ledger ingests. Headline quality metric. |
| Action F1 | Per-action precision/recall over all 288 |
| Callsign / command-span / value F1 | Span-level extraction (multiset, text-normalized) |
| Role accuracy | Controller vs pilot (gold from the dataset) |
| JSON validity | Share of outputs that parse |
| p50 / p95 latency | Client wall-clock, each arm measured from the same laptop in the same session; where it was measured is stated per row |
| $/1k transmissions | From list prices in `results/prices.json` × measured token counts |

**Training data (training only — never scored):** ATCO2 train airports (gold, ×2); 6,000 ATCOSIM + UWB-ATCC transcripts pseudo-labelled by a local teacher (Nemotron-3-Nano-30B) and kept only when every span is a verbatim substring of the transcript (keep rate 74–82%); 2,500 synthetic US-phraseology rows (JO 7110.65 grammar, gold by construction). Total 9,478 examples; `scripts/01–04`.

**Baseline.** [frontier model, exact version] with the same system prompt, temperature 0, few-shot examples from the *train* split, run at **5-shot and 20-shot** — we report the better of the two so the comparison cannot be called a weakened baseline. Also reported: the same open base model, prompted, before fine-tuning.

**Secondary (synthetic, in-distribution):** 300 synthetic US-phraseology transmissions (`data/synthetic/us_stress.sha256`). The fine-tune saw 2,500 rows from the same generator, so this measures US-phraseology *coverage*, not generalization. Reported in the appendix only.

## 4. Results

*Produced by `scripts/11_score_test.sh <baseline> <arms…>` from `results/test/`; all four frontier reference arms were run 10:53–12:05 PT on Nov 2.*

**What the frontier models do on unseen airports.** Claude Opus 5.5 at 5-shot scores 67.4% full-record exact (95% CI [61.5, 72.6]); giving it 20 examples instead of 5 changes nothing (68.1%, paired Δ +0.7, CI [−2.4, +3.5]) at 1.5× the cost. GPT-5.5 (53.1%) and GPT-5.6 Terra (49.0%) are significantly worse. All three lose mostly on **speaker role** (Opus 81.5%, GPT-5.5 65.9%, Terra 61.6%): on a pilot-heavy test set they read read-backs as instructions. The cue they miss is positional and learnable — in the gold data controllers put the callsign *first* in 91% of transmissions, pilots put it *last* in 55% — and it is exactly the kind of regularity 500 real training rows teach a small model and twenty prompt examples do not. On the operational subset (clearance-state accuracy, n=69) the frontier models are strong (88–90%): they know what "cleared to land" means; what they get wrong is who said it.

| Arm | Where it ran | Clearance-state acc (n=70) | Full record exact (n=288) | Action F1 | Callsign F1 | Role acc | JSON valid | p50 / p95 ms | $/1k |
|---|---|---|---|---|---|---|---|---|---|
| [frontier], 5-shot | API | | | | | | | | |
| [frontier], 20-shot | API | | | | | | | | |
| Qwen3-8B base, 5-shot | Fireworks serverless | | | | | | | | |
| **Qwen3-8B + LoRA (ours), 0-shot** | **Fireworks serverless** | | | | | | | | |
| Qwen3-8B + LoRA (ours), 0-shot | DGX Spark, on-prem | | | | | | | | ~0 |
| Nemotron-Nano-8B + LoRA (ours), 0-shot | DGX Spark, on-prem | | | | | | | | ~0 |
| Router: LoRA → frontier on low confidence | mixed | | | | | | | | |

**Paired deltas with 95% CIs** (fine-tune − frontier, same rows): *table from `results/test/scores.md`*.

**Cost at tower scale** (10,000 transmissions/day, list prices, measured token counts): frontier 5-shot ≈ $[x]/day/airport; fine-tuned 0-shot ≈ $[y]/day; across the ~520 FAA and contract towers in the US that is $[X]/yr vs $[Y]/yr — and only one of the two can run inside the tower at all.

**Dry runs (dev split, 85 in-distribution rows — not the test set; `results/dev/`, reported for transparency only).** Nov 1 on the Spark: the 1-epoch LoRA lifted full-record exact from 42.4% to 70.6% over the prompted base (scored under the earlier rule that still counted ACK). Nov 2, 08:00 PT, frontier models at 5-shot under the final rule: Claude Opus 5.5 **90.6%**, GPT-5.5 83.5%, GPT-5.6 Terra 71.8%; Opus at 20-shot 87.1%. These set the bar the test run has to meet.

## 5. Tradeoffs and limitations

- **Narrow by design.** The adapter parses ATC phraseology and nothing else; it is not a chat model.
- **Test airports are European and Australian English.** US phraseology is covered in training only synthetically; a US gold test set does not exist publicly. We say this rather than hide it behind the synthetic score.
- **Distribution shift is real and reported:** test is pilot-heavy, train is controller-heavy.
- **Clearance-state subset is small (n=70)** — hence the CIs. Full-record exact on 288 is the headline; clearance-state is the operational framing.
- **Command→action table is heuristic** (0.6% of gold spans map to OTHER). It is applied identically to gold and to every arm.
- **Pseudo-labels came from a 30B open teacher**, validated by substring checks, not by humans. They are training data only.
- **Latency depends on where you run it.** Hosted on Fireworks: [p50] ms. On the DGX Spark in bf16: ~3 s per transmission (bandwidth-bound; 16 concurrent requests at the same latency ≈ 4.6 req/s, enough for ~30 frequencies). FP8/NVFP4 or the 4B student would bring the on-prem number down; we report what we measured.
- **The ledger and look-ahead are not evaluated here.** They are deterministic, pre-existing GMAPS code; this submission measures the parser that feeds them. The viewer in `viz/` runs scripted scenarios on real KSFO geometry (© OpenStreetMap contributors) with fictional traffic.

## 6. Reproduce

```
pip install -r requirements.txt
python3 bench/prepare_data.py                               # ATCO2 1h → gold jsonl + by-airport split; prints the test hash
python3 bench/normalize.py data/atco2_1h_gold.jsonl         # action-table coverage report
python3 scripts/01_fetch_external.py && python3 scripts/02_synth_us_phraseology.py
# pseudo-label with any OpenAI-compatible teacher, then validate:
BASE_URL=... API_KEY=... python3 bench/infer.py --model <teacher> --split data/external/uwb_atcc.jsonl --out data/pseudo/uwb_atcc.preds.jsonl --fewshot 8
python3 scripts/03_pseudo_label.py data/external/uwb_atcc.jsonl data/pseudo/uwb_atcc.preds.jsonl data/pseudo/uwb_atcc.gold.jsonl
python3 scripts/04_build_sft_mix.py --gold data/splits/train.jsonl --dev data/splits/dev.jsonl --synthetic data/synthetic/us_train.jsonl \
        --pseudo data/pseudo/uwb_atcc.gold.jsonl data/pseudo/atcosim.gold.jsonl --max-pseudo 3000 --out data/sft/mix_train.jsonl --dev-out data/sft/dev.jsonl
# fine-tune: Fireworks (scripts/09_export_fireworks.md) or locally (scripts/05_finetune_unsloth.py)
# evaluate on the frozen test split (hash-checked), then score all arms together:
BASE_URL=... API_KEY=... scripts/10_eval_test.sh <model-as-served> <fewshot>
scripts/11_score_test.sh results/test/<baseline>.preds.jsonl results/test/*.preds.jsonl
```
`bench/` needs only the Python 3.10+ standard library. Training data derived from ATCO2 / UWB-ATCC / ATCOSIM is not redistributed (research / CC BY-NC-SA licenses); the exact training mix is available to judges on request.

## 7. Sponsor tracks

- **Fireworks.** Supervised fine-tuning (LoRA, SFT v2) of Qwen3-8B on the 9,478-example mix; serverless LoRA deployment; all hosted arms evaluated through the Fireworks OpenAI-compatible API. *[job id, deployment id]*
- **NVIDIA.** Nemotron student (Llama-3.1-Nemotron-Nano-8B) fine-tuned on a DGX Spark; the on-prem deployment arm runs the adapter on the Spark with vLLM — the "parser in the tower" configuration. Pseudo-label teacher: Nemotron-3-Nano-30B.
- **Microsoft.** *[Phi-4-mini as a third student if time allowed; otherwise not entered — state which.]*

## 8. Team

*[names, GitHub handles, who did what]*

## 9. Pre-existing work and AI assistance (disclosure)

*Paste `DISCLOSURE.md` here before submitting.* In short: the benchmark harness, data pipelines, synthetic generator, Spark scripts and the viewer were built Oct 31 – Nov 1 and are in this repo's history with timestamps; a dry-run fine-tune and dev-split numbers were produced Nov 1 (`STATUS.md`). The frozen test split was first evaluated during the build period; every result in §4, the Fireworks training and deployment, the router and the video were produced during the event. GMAPS's ledger / look-ahead engine is prior work from the Dell × NVIDIA Boston hackathon (Oct 2026) and is not evaluated here. Claude (Anthropic) was used to scaffold this repository and during the build; the team is responsible for the implementation and the reported results.

## Repository map

```
bench/      data prep, action table, scorer (with bootstrap CIs), SFT builder, inference client — the benchmark
scripts/    data sources, synthetic US phraseology, pseudo-labelling, fine-tune, serve, dev eval, latency, TEST eval + scoring
viz/        GMAPS runway monitor — OSM geometry for KSFO, scenario builder, MapLibre page (presentation only)
prompts/    the one system prompt every arm uses
data/       gitignored; the committed hashes freeze the test split and the synthetic stress split
results/    prices.json (list prices), dev/ (dry run), test/ (the submission numbers), latency json
docs/       screenshots
CLAUDE.md, PLAN.md, MONDAY.md, DISCLOSURE.md, STATUS.md — run books and the hand-off from the dry run
```
