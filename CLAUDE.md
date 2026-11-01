# GMAPS × Fireworks: Deploy — Spark work package

You are Claude Code running unattended on Franco's DGX Spark (GB10, 128 GB unified memory, aarch64, CUDA).
Mission: by the time Franco checks back (~5–6 h), have the **data, pipelines, a first fine-tuned ATC parser, dev
numbers, a latency sweep, and the SFO visualization** ready, so Monday's build day (Nov 2, 10:30–16:30 PT) is
spent on final training runs, the frozen test set, the router, the README and the video.

Read `PLAN.md` and work through the phases **in order**. After each phase: run its check, update `STATUS.md`,
`git add -A && git commit`. If a phase fails twice, write what happened in `STATUS.md` and move on — a finished
pipeline with one gap beats a stalled one.

## What this project is

An open small model (Qwen3-8B / Qwen3-4B / Llama-3.1-Nemotron-Nano-8B) fine-tuned to parse one ATC radio
transmission into `{role, callsigns, commands, values}`, benchmarked against a closed frontier model on the
**ATCO2 gold test split** (288 real segments, 3 held-out airports in 3 countries, hash in `data/splits/test.sha256`).
The parsed record feeds GMAPS, a deterministic runway-clearance conflict engine. Judging: benchmark 40 %,
business value 25 %, technical 20 %, presentation 10 %, docs 5 %.

## Hard rules (these protect the submission — do not trade them for speed)

1. **Never read, print, evaluate on, or train on `data/splits/test.jsonl`.** Its first use is Monday 10:30 PT.
   Everything today runs on `data/splits/dev.jsonl` and `data/synthetic/us_stress.jsonl`.
2. **No test leakage.** `scripts/01_fetch_external.py` drops any external transcript that matches an ATCO2 text;
   `scripts/04_build_sft_mix.py` refuses test files. Do not add data sources beyond the two in `01_fetch_external.py`
   without the same guard. Do **not** scrape LiveATC or any site whose terms forbid it.
3. **No secrets in the repo.** API keys stay in the environment (`~/.atc_env`, sourced, gitignored). Never commit
   `results/*.preds.jsonl` that contain keys, and never paste keys into `STATUS.md`.
4. **Everything you build today is pre-event work and must be disclosed.** `DISCLOSURE.md` lists it; append to that
   list, don't shrink it. Results you produce today are *dry-run* numbers for `STATUS.md`, not for the README.
5. **Licences:** ATCO2 1h (research), UWB-ATCC (CC BY-NC-SA 4.0), ATCOSIM (research). Keep the data out of git
   (`.gitignore` already does); keep the citations in `README.md`.
6. **Don't touch port 8000** (OpenCode's qwen3-coder endpoint). Students serve on 8001, teacher on 8002.
   Run one vLLM server at a time unless `free -g` shows headroom; stop the teacher before fine-tuning.
7. **Stay in this repo.** Model downloads go to the HF cache or `runs/`; nothing else on the machine changes.

## Environment facts

- Models on the SSD: `/mnt/hackssd/GB10_ARSENAL/models/` — Qwen3-4B-Instruct-2507, Qwen3-1.7B, Nemotron-3-Nano-4B-BF16
  (student candidates, already local); Nemotron-3-Nano-30B-A3B-NVFP4, Qwen3.6-35B-A3B-NVFP4 (teacher candidates for
  vLLM); exact folder names: see `results/env_check.txt` after phase 0.
- Containers: `vllm/vllm-openai:v0.27.1` (arm64), `nvcr.io/nvidia/pytorch:25.11-py3`. Use the vLLM container for
  serving (`scripts/06_serve_vllm.sh`). Fine-tune in the host env if `unsloth` imports; otherwise inside the pytorch
  container with TRL + PEFT (`--force-trl`).
- Unsloth on DGX Spark: NVIDIA playbook `build.nvidia.com/spark/unsloth`, Unsloth docs
  `docs.unsloth.ai/basics/fine-tuning-llms-with-nvidia-dgx-spark-and-unsloth`.
- Teacher priority for pseudo-labelling: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` if set (frontier teacher, ~$15 for
  20k rows) → else `FIREWORKS_API_KEY` with a large open model → else local vLLM teacher from the SSD on :8002.
- Qwen3 chat template: build training text with `enable_thinking=False`; when serving Qwen3 with vLLM for this task
  pass `"chat_template_kwargs": {"enable_thinking": false}` via `--extra` in `bench/infer.py`, or rely on the fine-tune
  (it learns to answer with JSON directly).

## Reporting

`STATUS.md` is the hand-off. Keep it factual and short: what ran, what the numbers are (dev + stress, base vs
fine-tuned, latency sweep), what failed, what Monday needs. Numbers only from `bench/score.py` output.
Commit after each phase with a message that starts with the phase number.
