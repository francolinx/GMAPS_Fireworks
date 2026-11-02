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

Built **during** the event (Nov 2, from 10:30 PT):
- 10:53–12:05 — four frontier reference arms on the frozen test split via OpenRouter (Claude Opus 5.5 at 5- and 20-shot, GPT-5.5, GPT-5.6 Terra), `results/test/*.preds.jsonl`
- ~12:10 — on the Spark: the off-the-shelf Qwen3-8B (5-shot) and the Nov 1 dry-run LoRA (0-shot) on the frozen test split
- 12:15 — joint scoring with paired bootstrap CIs (`results/test/scores.md`), error analysis, router arm (reported; not helpful)
- 12:30–13:00 — README §4 results, chart (`docs/results_full_record.png`), the 118-second video (`docs/video/`), the slide deck for the live round
- no prompt revision was made after seeing test results; the scorer rule fixed at 08:40 PT (ACK/OTHER as non-actions) predates every test run
- Fireworks SFT (v2 training mix, 3 epochs): *[job id / "not run — no API key reached the cloud session before the deadline"]*

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
| Dev baselines | `results/dev/*_fs5.dev.preds.jsonl`, `results/dev/frontier_fs5.dev.scores.json` | Nov 2 08:00 PT dry run of three frontier models on the DEV split via OpenRouter (not test) |
| Mix filter | `scripts/12_filter_sft.py` | drops UNKNOWN-role training rows |
| Router | `scripts/13_router.py` | post-processing confidence router over two prediction files (written 08:10, first run during the build period) |
| Plan | `MONDAY.md` | build-day run book |

### Added Nov 2, 08:10–09:20 PT (cloud session, before the build period)
| Area | Files | What it is |
|---|---|---|
| Teacher test | `results/dev/openai_gpt-5.6-luna_fs5.dev.preds.jsonl` | GPT-5.6 Luna on dev (teacher candidate) |
| Pseudo-labels v2 | `data/pseudo/*.luna.preds.jsonl` (gitignored) | 8,000 external rows labelled by GPT-5.6 Luna, 12-shot from train; validated by `scripts/03_pseudo_label.py` |
| Role fill | `data/pseudo/train_unk_roles.json` (gitignored), `scripts/04_build_sft_mix.py --role-fill` | Claude Opus 5.5 assigned speaker roles to the 95 UNKNOWN-role gold train rows (spans stay gold; training only) |
| Scorer rule | `bench/normalize.py`, `bench/score.py` | ACK/OTHER excluded from action sets; guard rules; fixed before any test run |
| Fireworks route | `scripts/15_fireworks_sft.py` | dataset upload / SFT / status / deploy via the Python SDK |
| Docs | `scripts/14_results_md.py`, `docs/video_script.md`, `viz/export_transmissions.py`, `viz/import_outputs.py` | results tables generator, video script, viz wiring |

### Build period, Nov 2, 10:30–16:30 PT (all new work; listed for completeness)

| Item | Where | Notes |
|---|---|---|
| Frozen-test runs of all arms | `results/test/*.preds.jsonl`, `scores.*` | first test-set use 10:53 PT; every arm with the same prompt/shots/scorer |
| Fireworks SFT jobs `rtkwkax2`, `g0tr55s3`, `zdi4wg97` and their evals | `scripts/15_fireworks_sft.py`, `21_*`, `23_*`, `25_*` | launched 12:08, 12:44, 14:40 PT |
| Significance testing (McNemar + recording bootstrap), gains/regressions, figures | `bench/score.py`, `scripts/20_*`, `22_*` | after the Fireworks and NVIDIA sessions; prereg addenda 2–3 |
| README §4, deck, video re-cut, Spark work package 2 (`SPARK_PROMPT_2.md`) | — | written during the build period with Claude (cloud session) |
