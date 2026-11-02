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

## Addendum — Nov 2, 10:58 PT (after the kickoff talk, before any test result was scored)

The organizers' kickoff (recorded 10:24 PT) defines the graded comparison as **before → after on the same open model**: "just by
asking some model off the shelf to do this task, [vs] do it our way — by how much?"; closed models are explicitly *not required*
and were shown as reference bars. Accordingly, two comparisons are reported, both with the paired-CI rule above, both on the same 288 rows:

1. **Primary (event definition): before → after.** Qwen3-8B off the shelf, 5-shot (`accounts/fireworks/models/qwen3-8b`) → Qwen3-8B + LoRA, 0-shot. Full-record exact; paired Δ with 95% CI.
2. **Reference: vs the strongest closed model**, Claude Opus 5.5 5-shot, as pre-registered above. Headline wording follows `MONDAY.md` §Headline for this comparison; it is reported whether or not it favours us.

No model, prompt, data, or scorer change accompanies this addendum; it changes which comparison is called primary, to match the rubric as stated by the organizers. The frontier test runs were started at 10:53 PT; no result had been scored when this was written.

## Addendum 2 — Nov 2, 12:05 PT (after the test results were scored; a stricter decision rule, not a looser one)

The Fireworks implementation session (Sinan Ozdemir, 11:30 PT) showed the organizers' sample project calling a difference real
only if it passes **both** an exact McNemar test and a **cluster** bootstrap. We adopted that rule as an addition on top of the
pre-registered one, because our test rows are not independent: the 288 segments come from 159 recordings, and a row bootstrap
overstates the certainty. `bench/score.py` now resamples recordings (`--cluster recording`, 5,000 resamples) and reports the
exact McNemar p-value against the first arm; "significant" means both.

Verdicts did not change. Under the pre-registered row bootstrap (2,000 resamples) the before→after gap was +12.8 [+5.2, +20.1];
under the recording bootstrap it is +12.8 [+5.9, +19.7] with McNemar p = 0.001. Opus vs LoRA: row [−18.1, −5.9], recording
[−18.4, −5.7], p = 0.0002. The router's +1.7 over the LoRA alone and Opus 20-shot's +0.7 over 5-shot fail both tests under both rules.
No model, prompt, data, scorer-metric, or arm change accompanies this addendum.

## Addendum 3 — Nov 2, 12:50 PT (Nemotron arms: reasoning setting, decided after seeing test numbers)

Two extra arms were added during the build period on a second open model, Nemotron-3-Nano-30B-A3B (off the shelf, 5-shot;
+ our LoRA, 0-shot), following the same protocol as the Qwen3-8B before→after (same prompt, shots from train, same scorer,
`max_tokens` 1,500). The first run used the model's default (reasoning on): the base spent ~1,000 tokens per transmission
thinking and 82/288 answers never reached the JSON before the cap; the LoRA lost 17 rows the same way. We re-ran **both**
Nemotron arms with `reasoning_effort: "none"` — the setting the NVIDIA enablement session used for this model, and the
equivalent of the `enable_thinking: false` every Qwen3 arm already had. Because this was decided after seeing test numbers,
both versions are kept in `results/test/` and both are in the README table; the reasoning-off version is the one in the
headline. The primary pre-registered comparison (Qwen3-8B before→after) is unchanged by this addendum. The Nemotron-vs-Opus
comparison is reported with the two-test rule and is a tie (+2.8, [−2.0, +7.4], p = 0.30).
