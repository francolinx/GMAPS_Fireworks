# After the event: run the 70.1 % Nemotron-30B adapter on the DGX Spark

The headline model (`atc-nemotron-nano-30b-v1`, 70.1 % full-record on the frozen test split) was trained and evaluated on
Fireworks. The live demo on the Spark runs the Qwen3-8B v1 adapter (55.2 %) because the Nemotron adapter could not be pulled
down during the build period (console sign-in + a 60 GB BF16 base). The same 30B-A3B base already serves on the Spark at
~1.5 s per transmission (NVFP4), so moving the adapter on-prem is a download, not a research step. Steps, one at a time:

```bash
# 0. the repo on the Spark is wherever the build-day session cloned it; everything below runs from there
cd <repo>

# 1. firectl (Fireworks CLI). If the arm64 URL 404s, use the install page: https://docs.fireworks.ai/tools-sdks/firectl
mkdir -p ~/bin && curl -sSL https://storage.googleapis.com/fireworks-public/firectl/stable/linux-arm64.gz | gunzip > ~/bin/firectl \
  && chmod +x ~/bin/firectl && export PATH=$HOME/bin:$PATH
firectl signin                      # browser login on the Spark desktop (or paste the URL)

# 2. pull the adapter (small)
firectl download model atc-nemotron-nano-30b-v1 --output-dir runs/nemotron-30b-lora

# 3a. fastest try: vLLM, NVFP4 base from the SSD + the adapter. Check the exact folder name first:
ls /mnt/hackssd/GB10_ARSENAL/models/            # see results/env_check.txt
docker run --rm --gpus all -p 8005:8000 -v /mnt/hackssd:/mnt/hackssd -v "$PWD/runs:/runs" vllm/vllm-openai:v0.27.1 \
  /mnt/hackssd/GB10_ARSENAL/models/<Nemotron-3-Nano-30B-A3B-NVFP4 folder> --enable-lora \
  --lora-modules gmaps=/runs/nemotron-30b-lora --max-lora-rank 32 --max-model-len 4096 --port 8000
# then point viz/live_server.py at model "gmaps" on :8005

# 3b. if vLLM refuses LoRA on this hybrid Mamba/MoE architecture: merge into the BF16 base and serve the merged model
pip install peft
hf download nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 --local-dir runs/nemotron-30b-bf16      # ~60 GB
python3 - <<'PY'
from peft import PeftModel
from transformers import AutoModelForCausalLM
m = AutoModelForCausalLM.from_pretrained("runs/nemotron-30b-bf16", torch_dtype="bfloat16", trust_remote_code=True)
PeftModel.from_pretrained(m, "runs/nemotron-30b-lora").merge_and_unload().save_pretrained("runs/nemotron-30b-merged")
PY
# serve runs/nemotron-30b-merged with the docker command from 3a, without --enable-lora/--lora-modules

# 4. prove it is the same model: re-run the frozen test split locally and compare with results/test/scores.md
python3 bench/infer.py --base-url http://localhost:8005/v1 --model gmaps --fewshot 0 --tag atc-nemotron-nano-30b-v1_spark
python3 bench/score.py results/test/*.preds.jsonl
```

Port 8000 stays reserved (OpenCode). Stop the :8002 teacher first if `free -g` shows no headroom.
