| Arm | Where it ran | Clearance-state acc (n=69) | Full record exact (n=288) | Action F1 | Callsign F1 | Role acc | JSON valid | p50 / p95 | $/1k |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b-base |  | 91.3% | 42.4% | 87.5% | 87.7% | 57.6% | 100.0% | 2.9 s / 3.9 s | — |
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | DGX Spark, on-prem | 88.4% | 55.2% | 85.8% | 89.0% | 75.0% | 100.0% | 3.0 s / 4.1 s | — |
| Claude Opus 5.5, 5-shot (baseline) | API via OpenRouter | 89.9% | 67.4% | 91.2% | 93.4% | 81.5% | 100.0% | 5.3 s / 7.2 s | $9.922 |
| Claude Opus 5.5, 5-shot (baseline) | API via OpenRouter | 88.4% | 68.1% | 91.1% | 94.3% | 81.9% | 100.0% | 3.8 s / 6.1 s | $14.485 |
| GPT-5.5, 5-shot | API via OpenRouter | 88.4% | 53.1% | 90.9% | 93.2% | 65.9% | 100.0% | 3.7 s / 8.8 s | $10.405 |
| GPT-5.6 Terra, 5-shot | API via OpenRouter | 88.4% | 49.0% | 87.9% | 92.5% | 61.6% | 100.0% | 2.4 s / 3.7 s | $2.623 |

**Paired 95% CIs vs qwen3-8b-base** (row bootstrap on the same 288 transmissions; a Δ interval that excludes 0 is a difference the test set supports):

| Arm | Full record exact | Clearance-state acc | Action F1 | Callsign F1 | Role acc |
|---|---|---|---|---|---|
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | 55.2% (Δ+12.8 [+5.2, +20.1]) | 88.4% (Δ-2.9 [-7.5, +0.0]) | 85.8% (Δ-1.7 [-4.7, +1.2]) | 89.0% (Δ+1.3 [-1.4, +4.3]) | 75.0% (Δ+17.4 [+9.4, +25.0]) |
| Claude Opus 5.5, 5-shot (baseline) | 67.4% (Δ+25.0 [+17.7, +32.3]) | 89.9% (Δ-1.4 [-6.8, +3.2]) | 91.2% (Δ+3.7 [+0.3, +7.2]) | 93.4% (Δ+5.7 [+2.5, +8.9]) | 81.5% (Δ+23.9 [+16.7, +30.9]) |
| Claude Opus 5.5, 5-shot (baseline) | 68.1% (Δ+25.7 [+18.4, +33.0]) | 88.4% (Δ-2.9 [-9.1, +2.8]) | 91.1% (Δ+3.6 [+0.4, +7.1]) | 94.3% (Δ+6.6 [+3.4, +10.1]) | 81.9% (Δ+24.3 [+16.9, +31.4]) |
| GPT-5.5, 5-shot | 53.1% (Δ+10.8 [+4.5, +17.4]) | 88.4% (Δ-2.9 [-8.9, +2.9]) | 90.9% (Δ+3.3 [-0.2, +7.0]) | 93.2% (Δ+5.5 [+2.5, +8.6]) | 65.9% (Δ+8.3 [+2.5, +14.4]) |
| GPT-5.6 Terra, 5-shot | 49.0% (Δ+6.6 [+0.7, +12.5]) | 88.4% (Δ-2.9 [-7.4, +0.0]) | 87.9% (Δ+0.4 [-3.5, +4.4]) | 92.5% (Δ+4.9 [+2.0, +7.8]) | 61.6% (Δ+4.0 [-2.2, +10.3]) |

**Cost at tower scale** (10,000 transmissions/day per hub, list prices × measured token counts, 520 US towers):

| Arm | $/1k | $/day/airport | $/yr, all US towers |
|---|---|---|---|
| qwen3-8b-base | $0.000 | $0.00 | $0 |
| Qwen3-8B + LoRA (ours, Spark dry-run adapter), 0-shot | $0.000 | $0.00 | $0 |
| Claude Opus 5.5, 5-shot (baseline) | $9.922 | $99.22 | $18,831,877 |
| Claude Opus 5.5, 5-shot (baseline) | $14.485 | $144.85 | $27,491,634 |
| GPT-5.5, 5-shot | $10.405 | $104.05 | $19,748,393 |
| GPT-5.6 Terra, 5-shot | $2.623 | $26.23 | $4,978,177 |

On-prem arms carry no per-token cost; the hardware (one DGX Spark per tower, ~$4k) is amortised separately. Only the on-prem arms can run without sending live tower audio off-site.
