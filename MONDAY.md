# MONDAY — Nov 2, TERRA, 511 Harrison St (all times Pacific; clocks fell back Sunday)

Submission closes **16:30**. Organizers want you submitting by 15:30. Team of 2+ on the roster, everyone checked in.

| Time | Who | What |
|---|---|---|
| 09:00 | all | check in; ask organizers the two open questions: sponsor-track criteria (Microsoft / NVIDIA), and confirm pre-built scaffold + disclosure is acceptable (it is per §4, but ask and note who said so) |
| 09:30–10:30 | split | one person at the Fireworks session (what they want to see for the Fireworks track), one at NVIDIA's |
| **10:30** | A | **first touch of test:** `BASE_URL=... scripts/07_eval_test.sh <frontier> 5` — frontier baseline on `data/splits/test.jsonl` with the same prompt + 5 dev shots. Log the exact model id/version. (Create `07_eval_test.sh` by copying `07_eval_dev.sh` and swapping dev→test; this is deliberately not pre-built.) |
| 10:30 | B | start the Fireworks SFT job on `data/sft/mix_train.jsonl` (see `scripts/09_export_fireworks.md`); while it runs, run the **open base prompted** arm on test (Fireworks serverless Qwen3-8B, 5-shot) |
| 11:15 | A | baseline done → score. Look at the 20 worst frontier errors. Decide the fairness tweak once (schema wording / shots), rerun baseline **and** base once with the final prompt. Freeze the prompt. Commit. |
| 11:30–12:30 | B | Fireworks LoRA done → deploy → run on test zero-shot → score. If Spark adapter is better on dev, also upload it (route B in `09_export_fireworks.md`). Record cost table from list prices into `results/prices.json`. |
| 12:30–13:30 | A | error analysis of the fine-tune on test by action class; one iteration if there is a clear fix (prompt or 1 more epoch). **No cherry-picking: every rerun replaces the whole test file.** |
| 12:30–13:30 | B | router: confidence gate (JSON invalid or no callsign → fall back to frontier); report blended cost + accuracy as a 4th arm. Latency sweep from the laptop against Fireworks and against the Spark over Tailscale (`08_latency_bench.py`, note the network). |
| 13:30–14:30 | A | README: fill Results table from `results/scores.json`, Tradeoffs, Sponsor tracks, Team, what-was-built-during-event. Commit. |
| 13:30–14:30 | B | viz: run the four SIM-1 transmissions through the fine-tuned model and drop the real outputs into `scenario_sfo_sim1.json` ("parsed" = model output). Record the screen. |
| 14:30–15:15 | both | 120-second video: 0–20 s the problem (radio + runway), 20–75 s the demo (SFO map, conflict, hold-short resolution, parsed JSON), 75–115 s the results table (quality parity / cost / latency), 115–120 s tradeoffs line. |
| 15:15–15:45 | A | submit: repo public, incognito check, commit hash, video, sponsor tracks, every team member listed |
| 15:45–16:30 | both | nothing changes after the submit. Prep the 30-second visual opener for finals. |

## Finals (6 teams)

Open with the map playing at 2× (runway flashes at t=28) — the visual first, then the table. One sentence per rubric
line: who benefits, task, how success is measured, what improved vs the frontier (with numbers), tradeoffs.

## Business value — the answer when asked "who buys this"

Tower supervisors and ATC training programs, decision support only. Pilot path through university aviation programs
(Embry-Riddle / CCBC contacts from the Boston build). Why a small open model: a tower frequency is a transmission every
few seconds, 24/7, per frequency — it must be sub-second, cheap enough to run continuously, and able to run on local
hardware in the tower with no internet. That is a DGX Spark, not an API call.
