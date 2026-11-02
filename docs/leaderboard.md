| System | Full-record accuracy | Clearance-state accuracy | vs base Qwen3-8B | Cost of the 288-transmission run |
|---|---|---|---|---|
| **Nemotron-3-Nano-30B-A3B + LoRA** (1 epoch, Fireworks) | **70.1%** | 88.4% | +27.8, significant | $0.06 |
| **Nemotron-3-Nano-30B-A3B + LoRA** (3 epochs, Fireworks) | **69.8%** | 89.9% | +27.4, significant | $0.06 |
| Claude Opus 5.5, 20-shot | 68.1% | 88.4% | +25.7, significant | $4.17 |
| Claude Opus 5.5, 5-shot | 67.4% | 89.9% | +25.0, significant | $2.86 |
| Gemini 4 Argon, 5-shot | 63.5% | 89.9% | +21.2, significant | $0.57 |
| Nemotron-3.5-Lightning-30B-A3B + LoRA (3 epochs, Fireworks) | 62.2% | 91.3% | +19.8, significant | $0.06 |
| Nemotron-3.5-Lightning-30B-A3B + LoRA (1 epoch, Fireworks) | 60.4% | 94.2% | +18.1, significant | $0.06 |
| Qwen3-8B + LoRA v2 (3 epochs, Fireworks) | 59.7% | 89.9% | +17.4, significant | $0.02 |
| Router: LoRA v1 → Opus on weak outputs | 56.9% | 88.4% | +14.6, significant | — |
| GPT-6.1 Terra Pro, 5-shot | 56.2% | 89.9% | +13.9, significant | $1.44 |
| Qwen3-8B + LoRA v1 (1 epoch, DGX Spark) | 55.2% | 88.4% | +12.8, significant | ~$0 (on-prem) |
| GPT-5.5, 5-shot | 53.1% | 88.4% | +10.8, significant | $3.00 |
| GPT-5.6 Terra, 5-shot | 49.0% | 88.4% | +6.6, significant | $0.76 |
| Nemotron-30B + LoRA, reasoning on (first attempt) | 49.0% | 85.5% | +6.6, significant | $0.15 |
| Qwen3-8B off the shelf (baseline), 5-shot | 42.4% | 91.3% |  | ~$0 (on-prem) |
| Nemotron-3.5-Lightning-30B-A3B off the shelf, 5-shot | 40.6% | 92.8% | -1.7, not significant | $0.13 |
| Nemotron-3-Nano-30B-A3B off the shelf, 5-shot | 39.2% | 81.2% | -3.1, not significant | $0.13 |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b, 20-shot | 32.6% | 81.2% | -9.7, significant loss | $0.31 |
| Nemotron-30B off the shelf, reasoning on (first attempt), 5-shot | 29.5% | 59.4% | -12.8, significant loss | $0.27 |
