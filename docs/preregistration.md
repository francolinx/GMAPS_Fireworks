# Pre-registered evaluation plan

Committed **before** the first test-split run (see the commit timestamp of this file; the build period opens Nov 2, 10:30 PT).
Everything below was fixed using only the dev split (85 rows, training airports) and the synthetic stress split.

## Test set
- `data/splits/test.jsonl`, 288 real ATC transmissions, airports YSSY (Sydney), LKPR (Prague), LZIB (Bratislava) — none in training.
- `sha256 = 8660e6dedb571daa3c9c71b598d0890b430b06d1525418954a2e2ff4be8a31cd` (committed Oct 31). `scripts/10_eval_test.sh` refuses to run on a file with a different hash.
- No model, prompt, or scoring rule will be changed after seeing test results, except the single revision policy below.

## Primary comparison
- **Baseline:** Claude Opus 5.5 (`anthropic/claude-opus-5.5` via OpenRouter), 5-shot, temperature 0, `prompts/system.txt`, few-shot examples = the first 5 rows of the **train** split. Chosen because it was the strongest of three frontier models on dev (90.6% full record vs GPT-5.5 83.5%, GPT-5.6 Terra 71.8%).
- **Treatment:** Qwen3-8B + LoRA trained on `data/sft/mix_train_v2.jsonl` (sha256 prefix `36cfb05acc9573cb`, 7,857 examples, no test text — guarded by `scripts/04_build_sft_mix.py`), 0-shot, same system prompt, temperature 0, served on Fireworks.
- **Primary metric:** full-record exact match on all 288 rows (role + callsign multiset + operational action set; ACK/OTHER excluded as fixed in `bench/normalize.py` at 08:40 PT).
- **Decision rule:** paired row-bootstrap 95% CI of (treatment − baseline), 2,000 resamples, `bench/score.py --bootstrap 2000`. CI entirely above 0 → "beats"; straddles 0 → "matches"; entirely below 0 → "reaches X% of". The README headline will use the matching wording from `MONDAY.md` §Headline and no other.

## Secondary metrics (reported, not headlined)
Clearance-state accuracy (runway-critical subset, n≈70), action F1, callsign F1, role accuracy, JSON validity, p50/p95 latency with the measurement location stated, $/1k transmissions from `results/prices.json`.

## Fairness checks for the baseline (reported whatever they show)
- Opus 5.5 at **20-shot** (on dev, 20-shot was 3.5 points *worse* on the primary metric and 20 points better on value-span F1; both will be reported on test).
- Two further frontier models (GPT-5.5, GPT-5.6 Terra) at 5-shot.
- The open base model (Qwen3-8B, prompted, 5-shot) to separate the effect of fine-tuning from the effect of the model family.

## Single-revision policy
One revision is allowed after the first full test run, decided by 12:00 PT: **either** a training change (more epochs / learning rate) **or** a prompt change that is then applied to **every** arm with a full rerun. Never a per-arm change, never cherry-picked rows. The pre- and post-revision tables are both kept in `results/test/`.

## Things we expect and will say
- Test is pilot-heavy (148/288) while training is controller-heavy; dev numbers will not transfer directly.
- The on-prem (DGX Spark, bf16) arm will be ~3 s/transmission; the hosted arm is the latency headline.
- The dry-run adapter (1 epoch, Nov 1, `STATUS.md`) is reported as a separate row and is not the submitted model.
