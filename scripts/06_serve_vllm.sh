#!/usr/bin/env bash
# Serve a model on the DGX Spark with the vLLM container, OpenAI-compatible, for eval / pseudo-labelling.
#
#   scripts/06_serve_vllm.sh <model_dir_or_hf_id> <served-name> [port] [extra vllm args...]
#
#   # student (merged fine-tune)                                     → BASE_URL=http://localhost:8001/v1
#   scripts/06_serve_vllm.sh runs/qwen3-8b-atc/merged atc-qwen3-8b 8001 --max-model-len 2048
#   # base model for the "open base, prompted" arm
#   scripts/06_serve_vllm.sh Qwen/Qwen3-8B qwen3-8b-base 8001 --max-model-len 2048
#   # teacher for pseudo-labelling (big MoE from the SSD)            → BASE_URL=http://localhost:8002/v1
#   scripts/06_serve_vllm.sh /mnt/hackssd/GB10_ARSENAL/models/<Nemotron-3-Nano-30B-A3B-NVFP4 dir> teacher 8002 --max-model-len 4096
#
# Port 8000 is left alone: that is the qwen3-coder endpoint OpenCode already uses on this machine.
# Memory: the Spark shares 128 GB between everything. Keep --gpu-memory-utilization modest and run ONE server at a time
# unless you have checked `nvidia-smi` / `free -g`.
set -euo pipefail
MODEL="${1:?model dir or HF id}"; NAME="${2:?served name}"; PORT="${3:-8001}"; shift 3 || true
IMAGE="${VLLM_IMAGE:-vllm/vllm-openai:v0.27.1}"
GPU_UTIL="${GPU_UTIL:-0.55}"
VOL=()
if [ -d "$MODEL" ]; then ABS="$(cd "$MODEL" && pwd)"; VOL=(-v "$ABS:/model:ro"); MODEL_ARG="/model"; else MODEL_ARG="$MODEL"; fi
[ -d "${HF_HOME:-$HOME/.cache/huggingface}" ] && VOL+=(-v "${HF_HOME:-$HOME/.cache/huggingface}:/root/.cache/huggingface")
docker rm -f "vllm-$NAME" >/dev/null 2>&1 || true
echo "starting vllm-$NAME on :$PORT from $MODEL (image $IMAGE)"
docker run -d --name "vllm-$NAME" --gpus all --ipc=host -p "$PORT:8000" "${VOL[@]}" \
  -e HF_TOKEN="${HF_TOKEN:-}" "$IMAGE" \
  --model "$MODEL_ARG" --served-model-name "$NAME" --gpu-memory-utilization "$GPU_UTIL" \
  --max-num-seqs 64 --trust-remote-code "$@"
echo -n "waiting for /v1/models "
for i in $(seq 1 120); do
  if curl -fsS "http://localhost:$PORT/v1/models" >/dev/null 2>&1; then echo " ready"; curl -s "http://localhost:$PORT/v1/models" | head -c 300; echo; exit 0; fi
  sleep 5; echo -n "."
done
echo; echo "server did not come up; docker logs vllm-$NAME:"; docker logs --tail 40 "vllm-$NAME"; exit 1
