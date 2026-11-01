#!/usr/bin/env bash
# First thing to run on the Spark. Writes results/env_check.txt. Nothing here changes the machine.
set -uo pipefail
mkdir -p results
{
  echo "== $(date -u +%FT%TZ) on $(hostname) =="
  echo "--- GPU"; nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv 2>&1 | head -3
  echo "--- memory"; free -g | head -2
  echo "--- disk"; df -h / /mnt/hackssd 2>/dev/null | head -4
  echo "--- python"; python3 --version; python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())" 2>&1 | tail -1
  for m in unsloth trl peft transformers datasets pyarrow huggingface_hub vllm; do python3 -c "import $m; print('$m', getattr($m,'__version__','?'))" 2>/dev/null || echo "$m: not installed"; done
  echo "--- docker"; docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -Ei 'vllm|pytorch' | head; docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null
  echo "--- ports in use"; (ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null) | grep -E ':800[0-9]' || echo "none of 8000-8009 in use"
  echo "--- SSD model candidates (students: Qwen3-4B / Nemotron-3-Nano-4B; teachers: *30B* / *35B* / *27B*)"
  ls -d /mnt/hackssd/GB10_ARSENAL/models/*/ /mnt/hackssd/GB10_ARSENAL/models/*/*/ 2>/dev/null | grep -Ei 'qwen3-4b|qwen3-8b|qwen3-1.7|nemotron|35b|27b' | head -20
  echo "--- HF auth"; python3 -c "from huggingface_hub import whoami; print(whoami().get('name'))" 2>/dev/null || echo "not logged in (fine for public datasets)"
  echo "--- keys present (names only)"; for k in FIREWORKS_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY; do [ -n "${!k:-}" ] && echo "$k: set" || echo "$k: not set"; done
  echo "--- tmux"; tmux ls 2>/dev/null || echo "no tmux sessions"
} 2>&1 | tee results/env_check.txt
