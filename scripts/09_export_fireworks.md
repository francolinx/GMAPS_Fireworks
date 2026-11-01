# Getting the model onto Fireworks (Monday)

Two routes. Do the first one Sunday as a dry run so Monday is mechanical.

## A. Train on Fireworks (cleanest for the Fireworks track)

```
firectl login
firectl create dataset atc-mix-v1 data/sft/mix_train.jsonl
firectl create dataset atc-dev-v1 data/sft/dev.jsonl
firectl create sftj --base-model accounts/fireworks/models/qwen3-8b \
   --dataset atc-mix-v1 --evaluation-dataset atc-dev-v1 \
   --output-model atc-qwen3-8b-v1 --epochs 2 --learning-rate 1e-4 --lora-rank 16 --turbo
firectl get sftj <job-id>          # poll until COMPLETED
# then "Deploy this LoRA" (serverless if the base supports it; otherwise an on-demand deployment)
```
The dataset format this repo writes (`{"messages":[system,user,assistant]}`) is the SFT v2 chat format.
Check the base model shows **Tunable: true** in the model library first (`firectl get model -a fireworks qwen3-8b`).

## B. Train on the Spark, upload the adapter

Fireworks accepts LoRA adapters trained elsewhere for supported base architectures. Upload `runs/<run>/adapter/`
(the PEFT folder: `adapter_config.json` + `adapter_model.safetensors`) as a model, then deploy it on top of the
same base. Keep `r` and `target_modules` standard (this repo uses r=16 on all linear projections).

## What to record for the README, whichever route

- base model id and revision; adapter rank; epochs; learning rate; dataset ids and sizes
- the job id / deployment id and the exact served model name used in `results/prices.json`
- list prices for the base model (serverless $/M tokens) — that is the cost column
