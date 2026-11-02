# MONDAY — master plan (Nov 2, TERRA, 511 Harrison St · all times Pacific)

Submission closes **16:30**; organizers want it by **15:30**. Everything meets in `git`. Three workers:
**F** = Franco (Fireworks, Spark, video, submit) · **T** = teammate (viz, router, latency, error analysis) · **C** = cloud Claude (baselines, scoring, README, docs).

## What we know at 08:00 (dev split, n=85, not test)

Claude Opus 5.5 5-shot: 84.7% full record · our 1-epoch LoRA 0-shot: 70.6% · GPT-5.5: 78.8% · GPT-5.6 Terra: 64.7%.
Our clear win is value spans (+25). Opus is better or tied on everything operational. **Baseline = Opus 5.5** (strongest).
Headline is decided at 12:30 by the paired CI on test — three versions are pre-written in §Headline below.

## Before 09:00

- **F:** OpenRouter +$10 credit. Teammate on the roster. Go.
- **Spark (paste to its Claude Code):**
  ```
  git pull
  git add -f results/dev/atc-qwen3-8b.dev.preds.jsonl && git commit -m "dev preds for paired analysis" && git push
  python3 scripts/12_filter_sft.py data/sft/mix_train.jsonl data/sft/mix_train_v2.jsonl     # drops UNKNOWN-role rows
  hf auth login   # token from huggingface.co/settings/tokens (darkstar008)
  hf upload darkstar008/atc-sft-data data/sft . --private --repo-type dataset
  hf upload darkstar008/atc-qwen3-8b-lora runs/qwen3-8b-atc/adapter . --private --repo-type model
  ```
  Only if the Spark stays reachable all day: stop `vllm-atc-qwen3-8b`, start Llama-3.1-Nemotron-Nano-8B-v1 LoRA on `mix_train_v2.jsonl`, 1 epoch, completion-only loss, in tmux; re-serve on :8003 when done.
- **C:** Opus 20-shot on dev (does more context close the frontier's value-span gap?); `12_filter_sft.py`; `13_router.py`; this file.

## 09:00–10:30 — check-in, sponsor sessions

- Get the **Fireworks API key + credits**. `firectl login`. Create datasets: `firectl create dataset atc-mix-v2 <mix_train_v2.jsonl>` and `atc-dev <dev.jsonl>` (download from the HF repo). **Do not start the job before 10:30.**
- Ask organizers: Microsoft / NVIDIA track criteria; confirm disclosed pre-work is fine (it is, §4 of the rules — note who said so).
- Split: one of you in the Fireworks session (what they want to see for their track), one in NVIDIA's.

## 10:30 — test is unfrozen. Parallel start.

| Who | Command | Expect |
|---|---|---|
| C | `scripts/10_eval_test.sh anthropic/claude-opus-5.5 5` · `openai/gpt-5.5 5` · `openai/gpt-5.6-terra 5` (OpenRouter) | 15 min, ~$7 |
| C | `scripts/10_eval_test.sh anthropic/claude-opus-5.5 20` — only if dev 20-shot moved Opus by >3 pts | ~$3.5 |
| F | Fireworks SFT: base `qwen3-8b`, dataset `atc-mix-v2`, eval `atc-dev`, **3 epochs**, lr 1e-4, LoRA r16, `--turbo` | 20–40 min |
| C | `scripts/10_eval_test.sh accounts/fireworks/models/qwen3-8b 5` with `EXTRA='{"chat_template_kwargs":{"enable_thinking":false}}'` (Fireworks key) | open-base arm |
| T | `BASE_URL=http://<spark>:8001/v1 API_KEY=none scripts/10_eval_test.sh atc-qwen3-8b 0 spark` | on-prem dry-run adapter on test |

## 11:15–12:30 — fine-tune on test, one revision, freeze

- F: LoRA job done → deploy (serverless if the base supports LoRA addons, else on-demand) → `scripts/10_eval_test.sh accounts/<acct>/deployedModels/<name> 0 fw`.
- C: `scripts/11_score_test.sh results/test/anthropic_claude-opus-5.5_fs5.preds.jsonl results/test/*.preds.jsonl` → table + paired CIs. Error analysis LoRA vs Opus by action class and role.
- **One revision only**, decided by 12:00: (a) +1 epoch / lr change on Fireworks, or (b) a prompt change — which then **re-runs every arm** on test. Never a per-arm tweak. Rerun by 12:30. Freeze: `git tag frozen-results`.
- T: `python3 scripts/13_router.py results/test/<lora>.preds.jsonl results/test/anthropic_claude-opus-5.5_fs5.preds.jsonl --out results/test/router.preds.jsonl` → 4th arm. Latency sweep from the laptop: `08_latency_bench.py` vs the Fireworks LoRA and vs the Spark.

## 12:30–13:30 — write it up

- C: README §4 (table, paired CI table, cost at tower scale from measured tokens), §5, §7 with job/deployment ids. Headline per §Headline.
- T: wire viz — run the SIM-1 and 01R transmissions through the Fireworks LoRA (`bench/infer.py --split viz/scenario_*.jsonl` after a 10-line export), paste real outputs into the scenario JSONs, note "parsed = model output" in each, screenshot → `docs/`.
- F: Nemotron arm on test if it trained; else delete that row. Fill `results/prices.json` key for the LoRA deployment name.

## 13:30–14:30 — docs final

- Paste `DISCLOSURE.md` into README §9 with today's items added. Team §8. Delete the "Status: pre-event draft" line. Repo public, open in incognito, note the commit hash.

## 14:30–15:15 — video (120 s)

0–15 s problem: the incursion stat, "two clearances that cannot both be true." 15–60 s demo: map playing at 2×, radio line → parsed JSON → ledger → conflict at t=28 → hold-short → cleared. 60–100 s the table: Opus vs ours with CIs, cost, latency, on-prem. 100–120 s tradeoffs in one breath + "decision support only; the controller decides."

## 15:15–15:45 — submit. Nothing changes after.

## Headline (pick by the paired CI of full-record exact, LoRA − Opus, on test)

- **CI entirely > 0:** "A fine-tuned 8B open model beats Claude Opus 5.5 on real tower radio — [N]% vs [M]% — at 1/120th the cost, 10× lower latency, and it runs in the tower."
- **CI straddles 0:** "A fine-tuned 8B open model matches Claude Opus 5.5 on real tower radio ([N]% vs [M]%, paired 95% CI [a, b]) at 1/120th the cost and 10× lower latency — and it is the only one of the two that can run inside the tower."
- **CI entirely < 0:** "A fine-tuned 8B open model reaches [N/M]% of Claude Opus 5.5's quality on real tower radio, beats GPT-5.6 Terra outright, costs 1/120th as much, answers 10× faster, and runs in the tower; a confidence router recovers [R]% of Opus quality at [c]% of its cost."

## Business value — the answer to "who buys this"

Tower supervisors / ATC training programs; decision support only. Pilot via university aviation programs (Embry-Riddle, CCBC contacts). Why open: live tower audio cannot leave the building; ~10k transmissions/day per hub across all frequencies; ~520 US towers. Cost line from measured tokens: frontier ≈ $[x]/day/airport vs ours ≈ $[y]/day — but lead with on-prem, not dollars.
