| Arm | Where it ran | Clearance-state acc (n=69) | Full record exact (n=288) | Action F1 | Callsign F1 | Role acc | JSON valid | p50 / p95 | $/1k |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b-base |  | 91.3% | 42.4% | 87.5% | 87.7% | 57.6% | 100.0% | 2.9 s / 3.9 s | — |
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | DGX Spark, on-prem | 88.4% | 55.2% | 85.8% | 89.0% | 75.0% | 100.0% | 3.0 s / 4.1 s | — |
| accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 |  | 89.9% | 59.7% | 87.5% | 89.4% | 79.3% | 100.0% | 0.7 s / 7.6 s | $0.086 |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b |  | 81.2% | 39.2% | 86.6% | 88.1% | 50.0% | 100.0% | — / — | $0.445 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 |  | 88.4% | 70.1% | 92.8% | 94.0% | 83.0% | 100.0% | — / — | $0.218 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 |  | 89.9% | 69.8% | 92.0% | 93.8% | 84.8% | 100.0% | — / — | $0.218 |
| accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b |  | 92.8% | 40.6% | 92.5% | 88.1% | 51.4% | 100.0% | — / — | $0.446 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 |  | 94.2% | 60.4% | 91.8% | 90.2% | 75.7% | 100.0% | — / — | $0.218 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 |  | 91.3% | 62.2% | 91.7% | 90.7% | 75.4% | 100.0% | — / — | $0.218 |
| Claude Opus 5.5, 5-shot (baseline) | API via OpenRouter | 89.9% | 67.4% | 91.2% | 93.4% | 81.5% | 100.0% | 5.3 s / 7.2 s | $9.922 |
| Claude Opus 5.5, 5-shot (baseline) | API via OpenRouter | 88.4% | 68.1% | 91.1% | 94.3% | 81.9% | 100.0% | 3.8 s / 6.1 s | $14.485 |
| openai/gpt-6.1-terra-pro |  | 89.9% | 56.2% | 90.8% | 92.2% | 72.1% | 100.0% | 4.1 s / 8.0 s | $5.009 |
| GPT-5.5, 5-shot | API via OpenRouter | 88.4% | 53.1% | 90.9% | 93.2% | 65.9% | 100.0% | 3.7 s / 8.8 s | $10.405 |
| GPT-5.6 Terra, 5-shot | API via OpenRouter | 88.4% | 49.0% | 87.9% | 92.5% | 61.6% | 100.0% | 2.4 s / 3.7 s | $2.623 |
| router:lora->opus |  | 88.4% | 56.9% | 87.1% | 89.8% | 75.4% | 100.0% | 3.3 s / 8.4 s | — |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b |  | 59.4% | 29.5% | 67.7% | 76.0% | 36.2% | 71.2% | — / — | $0.922 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 |  | 85.5% | 49.0% | 85.5% | 89.2% | 59.8% | 92.4% | — / — | $0.520 |

**Paired 95% CIs vs qwen3-8b-base** (row bootstrap on the same 288 transmissions; a Δ interval that excludes 0 is a difference the test set supports):

| Arm | Full record exact | Clearance-state acc | Action F1 | Callsign F1 | Role acc |
|---|---|---|---|---|---|
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | 55.2% (Δ+12.8 [+5.9, +19.7]) | 88.4% (Δ-2.9 [-7.5, +0.0]) | 85.8% (Δ-1.7 [-4.8, +1.7]) | 89.0% (Δ+1.3 [-1.7, +4.4]) | 75.0% (Δ+17.4 [+10.4, +24.4]) |
| accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 | 59.7% (Δ+17.4 [+10.5, +24.5]) | 89.9% (Δ-1.4 [-6.5, +3.3]) | 87.5% (Δ-0.1 [-3.5, +3.3]) | 89.4% (Δ+1.7 [-1.3, +4.7]) | 79.3% (Δ+21.7 [+15.5, +27.8]) |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 39.2% (Δ-3.1 [-9.2, +3.1]) | 81.2% (Δ-10.1 [-19.0, -2.9]) | 86.6% (Δ-0.9 [-5.6, +3.4]) | 88.1% (Δ+0.4 [-3.1, +4.2]) | 50.0% (Δ-7.6 [-13.7, -1.4]) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 70.1% (Δ+27.8 [+19.4, +35.8]) | 88.4% (Δ-2.9 [-11.3, +4.6]) | 92.8% (Δ+5.3 [+1.5, +9.2]) | 94.0% (Δ+6.3 [+2.9, +10.0]) | 83.0% (Δ+25.4 [+17.7, +32.6]) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 | 69.8% (Δ+27.4 [+19.4, +35.3]) | 89.9% (Δ-1.4 [-9.4, +5.7]) | 92.0% (Δ+4.5 [+0.7, +8.4]) | 93.8% (Δ+6.1 [+2.7, +9.8]) | 84.8% (Δ+27.2 [+20.2, +34.0]) |
| accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b | 40.6% (Δ-1.7 [-8.0, +4.6]) | 92.8% (Δ+1.4 [-6.4, +8.6]) | 92.5% (Δ+4.9 [+1.8, +8.3]) | 88.1% (Δ+0.4 [-2.7, +3.6]) | 51.4% (Δ-6.2 [-12.1, -0.3]) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 | 60.4% (Δ+18.1 [+11.2, +25.0]) | 94.2% (Δ+2.9 [-2.4, +9.1]) | 91.8% (Δ+4.2 [+0.4, +8.2]) | 90.2% (Δ+2.5 [-1.3, +6.4]) | 75.7% (Δ+18.1 [+12.0, +24.2]) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 | 62.2% (Δ+19.8 [+13.0, +26.7]) | 91.3% (Δ+0.0 [-5.7, +5.7]) | 91.7% (Δ+4.1 [+0.8, +7.5]) | 90.7% (Δ+3.0 [-0.3, +6.5]) | 75.4% (Δ+17.8 [+11.8, +23.9]) |
| Claude Opus 5.5, 5-shot (baseline) | 67.4% (Δ+25.0 [+16.8, +33.1]) | 89.9% (Δ-1.4 [-8.3, +4.3]) | 91.2% (Δ+3.7 [+0.2, +7.4]) | 93.4% (Δ+5.7 [+2.7, +8.9]) | 81.5% (Δ+23.9 [+16.7, +31.2]) |
| Claude Opus 5.5, 5-shot (baseline) | 68.1% (Δ+25.7 [+17.5, +33.6]) | 88.4% (Δ-2.9 [-10.6, +3.2]) | 91.1% (Δ+3.6 [-0.0, +7.3]) | 94.3% (Δ+6.6 [+3.6, +10.0]) | 81.9% (Δ+24.3 [+17.1, +31.4]) |
| openai/gpt-6.1-terra-pro | 56.2% (Δ+13.9 [+5.9, +22.0]) | 89.9% (Δ-1.4 [-9.3, +5.9]) | 90.8% (Δ+3.2 [-0.5, +6.9]) | 92.2% (Δ+4.5 [+0.8, +8.3]) | 72.1% (Δ+14.5 [+8.0, +21.2]) |
| GPT-5.5, 5-shot | 53.1% (Δ+10.8 [+4.0, +17.3]) | 88.4% (Δ-2.9 [-10.1, +3.2]) | 90.9% (Δ+3.3 [-0.6, +7.3]) | 93.2% (Δ+5.5 [+2.7, +8.6]) | 65.9% (Δ+8.3 [+2.9, +13.8]) |
| GPT-5.6 Terra, 5-shot | 49.0% (Δ+6.6 [+0.3, +13.0]) | 88.4% (Δ-2.9 [-7.1, +0.0]) | 87.9% (Δ+0.4 [-3.9, +4.5]) | 92.5% (Δ+4.9 [+2.2, +7.8]) | 61.6% (Δ+4.0 [-1.5, +9.5]) |
| router:lora->opus | 56.9% (Δ+14.6 [+7.2, +21.9]) | 88.4% (Δ-2.9 [-7.5, +0.0]) | 87.1% (Δ-0.4 [-3.3, +2.8]) | 89.8% (Δ+2.1 [-1.1, +5.3]) | 75.4% (Δ+17.8 [+10.7, +24.9]) |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 29.5% (Δ-12.8 [-18.6, -7.1]) | 59.4% (Δ-31.9 [-43.8, -20.0]) | 67.7% (Δ-19.8 [-27.5, -12.4]) | 76.0% (Δ-11.7 [-17.0, -6.4]) | 36.2% (Δ-21.4 [-27.7, -15.0]) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 49.0% (Δ+6.6 [+0.4, +12.6]) | 85.5% (Δ-5.8 [-12.7, +0.0]) | 85.5% (Δ-2.1 [-6.4, +2.0]) | 89.2% (Δ+1.5 [-1.7, +4.9]) | 59.8% (Δ+2.2 [-4.1, +8.6]) |

**Cost at tower scale** (10,000 transmissions/day per hub, list prices × measured token counts, 520 US towers):

| Arm | $/1k | $/day/airport | $/yr, all US towers |
|---|---|---|---|
| qwen3-8b-base | $0.000 | $0.00 | $0 |
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | $0.000 | $0.00 | $0 |
| accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 | $0.086 | $0.86 | $162,985 |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | $0.445 | $4.45 | $845,447 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | $0.218 | $2.18 | $413,655 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 | $0.218 | $2.18 | $413,692 |
| accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b | $0.446 | $4.46 | $847,220 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 | $0.218 | $2.18 | $414,074 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 | $0.218 | $2.18 | $414,159 |
| Claude Opus 5.5, 5-shot (baseline) | $9.922 | $99.22 | $18,831,877 |
| Claude Opus 5.5, 5-shot (baseline) | $14.485 | $144.85 | $27,491,634 |
| openai/gpt-6.1-terra-pro | $5.009 | $50.09 | $9,507,833 |
| GPT-5.5, 5-shot | $10.405 | $104.05 | $19,748,393 |
| GPT-5.6 Terra, 5-shot | $2.623 | $26.23 | $4,978,177 |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | $0.922 | $9.22 | $1,750,193 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | $0.520 | $5.20 | $987,767 |

On-prem arms carry no per-token cost; the hardware (one DGX Spark per tower, ~$4k) is amortised separately. Only the on-prem arms can run without sending live tower audio off-site.
