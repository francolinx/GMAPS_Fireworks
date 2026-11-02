# Pre-existing code and AI assistance — disclosure (paste into README before submitting)

Built **before** the event (Oct 31 – Nov 1, 2026), committed with timestamps in this repo's history:

| Area | Files | What it is |
|---|---|---|
| Data prep | `bench/prepare_data.py` | downloads/parses the ATCO2 1h gold set, by-airport split, test-set hash |
| Action table | `bench/normalize.py` | 24 canonical actions, ordered regex rules; committed before any model run |
| Scorer | `bench/score.py` | entity/action/runway-critical/role/full-record metrics, latency, cost |
| SFT builders | `bench/make_sft.py`, `scripts/04_build_sft_mix.py` | chat-format training files, dedup + leakage guard |
| Inference client | `bench/infer.py` | generic OpenAI-compatible client, few-shot from dev only |
| Extra data | `scripts/01_fetch_external.py` | ATCOSIM + UWB-ATCC transcripts (text only), leakage-guarded |
| Synthetic US data | `scripts/02_synth_us_phraseology.py` | JO 7110.65-style generator, gold by construction |
| Pseudo-labelling | `scripts/03_pseudo_label.py` | teacher-labels validated as verbatim spans (training only) |
| Fine-tune script | `scripts/05_finetune_unsloth.py` | LoRA SFT on DGX Spark (Unsloth / TRL) |
| Serving / eval / latency | `scripts/06_serve_vllm.sh`, `scripts/07_eval_dev.sh`, `scripts/08_latency_bench.py` | dev-only evaluation and latency sweep |
| Visualization | `viz/*` | OSM geometry fetch, scenario builder, MapLibre runway monitor page (presentation only) |
| Prompt | `prompts/system.txt` | the extraction schema prompt, shared by every arm |

Pre-event **dry runs** (Nov 1, on the DGX Spark): fine-tunes and dev-split numbers recorded in `STATUS.md`. None of
them are the submitted results; the frozen test split was first evaluated during the build period.

Pre-event changes made during the Nov 1 Spark dry run (Claude Code, unattended; see `git log`):
- `scripts/05_finetune_unsloth.py`: compatibility with TRL >= 1.x (`processing_class=`, warmup as ratio via `warmup_steps`)
- `scripts/07_eval_dev.sh`: optional `EXTRA` passthrough of request fields (used to disable Qwen3 thinking)
- `viz/scenario_sfo_01r.json`: second scenario (01R) generated with `viz/build_scenario.py`; `viz/ksfo.geojson` refreshed from Overpass
- dry-run artifacts: local-teacher pseudo-labels (Nemotron-3-Nano-30B-A3B NVFP4), SFT mix (9478 rows), Qwen3-8B LoRA (1 epoch), dev/stress scores, latency sweep, training logs in `results/`

Built **during** the event (Nov 2, 10:30–16:30 PT) — *fill in Monday*:
- frontier baseline run on the test split (model, version, prompt version)
- Fireworks SFT job(s) (ids), deployment(s), the submitted fine-tuned model
- test-split evaluation of all arms, error analysis, the one prompt revision
- confidence router and blended-cost arm
- README results, tradeoffs, video

Related prior work: GMAPS (runway clearance-state engine, Dell × NVIDIA Boston hackathon, Oct 2026). This submission
reuses *[state exactly which components, if any]*; the scenario viewer in `viz/` was written for this event's pre-work.

AI assistance: Claude (Anthropic) was used to scaffold this repository and during the build; the team is
responsible for the implementation and the reported results.

### Added Nov 2, 07:45–08:30 PT (before check-in, from the cloud session)
| Area | Files | What it is |
|---|---|---|
| Scorer CIs | `bench/score.py` | row-bootstrap 95% CIs and paired deltas vs the first arm |
| Defaults | `bench/infer.py` | `--split` defaults to dev; few-shot pool is the train split |
| Test runner | `scripts/10_eval_test.sh`, `scripts/11_score_test.sh` | hash-checked frozen-test run and joint scoring — written before 10:30, **first executed during the build period** |
| Prices | `results/prices.json` | list prices (OpenAI, Fireworks) as of 2026-11-02 |
| README | `README.md`, `docs/runway_monitor_sfo_28l.png` | narrative, metric framing, business math template, screenshot of the dry-run viewer |
