| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b-base | 100.0% | 87.7% | 65.5% | 54.3% | 87.5% | 91.3% | 57.6% | 42.4% | 2864 | 3936 | $0.0000 |
| atc-qwen3-8b | 100.0% | 89.0% | 68.4% | 52.7% | 85.8% | 88.4% | 75.0% | 55.2% | 3040 | 4120 | $0.0000 |
| accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 | 100.0% | 89.4% | 69.1% | 57.9% | 87.5% | 89.9% | 79.3% | 59.7% | 701 | 7611 | $0.0859 |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 100.0% | 88.1% | 62.7% | 48.5% | 86.6% | 81.2% | 50.0% | 39.2% | — | — | $0.4454 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 100.0% | 94.0% | 73.1% | 63.0% | 92.8% | 88.4% | 83.0% | 70.1% | — | — | $0.2179 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 | 100.0% | 93.8% | 75.0% | 66.1% | 92.0% | 89.9% | 84.8% | 69.8% | — | — | $0.2180 |
| accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b | 100.0% | 88.1% | 57.0% | 50.2% | 92.5% | 92.8% | 51.4% | 40.6% | — | — | $0.4464 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 | 100.0% | 90.2% | 69.6% | 59.7% | 91.8% | 94.2% | 75.7% | 60.4% | — | — | $0.2182 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 | 100.0% | 90.7% | 67.4% | 60.7% | 91.7% | 91.3% | 75.4% | 62.2% | — | — | $0.2182 |
| anthropic/claude-opus-5.5 | 100.0% | 93.4% | 70.7% | 58.7% | 91.2% | 89.9% | 81.5% | 67.4% | 5258 | 7210 | $9.9220 |
| anthropic/claude-opus-5.5 | 100.0% | 94.3% | 72.1% | 66.6% | 91.1% | 88.4% | 81.9% | 68.1% | 3794 | 6137 | $14.4845 |
| openai/gpt-6.1-terra-pro | 100.0% | 92.2% | 73.0% | 60.3% | 90.8% | 89.9% | 72.1% | 56.2% | 4052 | 8039 | $5.0094 |
| openai/gpt-5.5 | 100.0% | 93.2% | 71.1% | 57.9% | 90.9% | 88.4% | 65.9% | 53.1% | 3750 | 8782 | $10.4048 |
| openai/gpt-5.6-terra | 100.0% | 92.5% | 67.3% | 58.0% | 87.9% | 88.4% | 61.6% | 49.0% | 2434 | 3655 | $2.6229 |
| router:lora->opus | 100.0% | 89.8% | 67.8% | 55.1% | 87.1% | 88.4% | 75.4% | 56.9% | 3319 | 8442 | — |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 71.2% | 76.0% | 43.0% | 39.7% | 67.7% | 59.4% | 36.2% | 29.5% | — | — | $0.9221 |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 92.4% | 89.2% | 69.0% | 57.1% | 85.5% | 85.5% | 59.8% | 49.0% | — | — | $0.5204 |

(n=288 segments; runway-critical subset n=69)

(bootstrap resamples whole recordings: 159 recordings in 288 segments)

95% CIs (recording-cluster bootstrap, 5000 iters); Δ is paired vs. qwen3-8b-base:

| Metric | qwen3-8b-base | atc-qwen3-8b | accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 | accounts/fireworks/models/nemotron-nano-3-30b-a3b | accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 | accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b | accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 | accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 | anthropic/claude-opus-5.5 | anthropic/claude-opus-5.5 | openai/gpt-6.1-terra-pro | openai/gpt-5.5 | openai/gpt-5.6-terra | router:lora->opus | accounts/fireworks/models/nemotron-nano-3-30b-a3b | accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Callsign F1 | 87.7% [83.5%, 91.4%] | 89.0% [84.9%, 92.5%] Δ+1.3 [-1.7, +4.4] | 89.4% [85.3%, 92.9%] Δ+1.7 [-1.3, +4.7] | 88.1% [83.7%, 92.2%] Δ+0.4 [-3.1, +4.2] | 94.0% [90.7%, 96.8%] Δ+6.3 [+2.9, +10.0] | 93.8% [90.6%, 96.6%] Δ+6.1 [+2.7, +9.8] | 88.1% [83.7%, 92.1%] Δ+0.4 [-2.7, +3.6] | 90.2% [86.5%, 93.6%] Δ+2.5 [-1.3, +6.4] | 90.7% [86.9%, 94.2%] Δ+3.0 [-0.3, +6.5] | 93.4% [89.7%, 96.4%] Δ+5.7 [+2.7, +8.9] | 94.3% [90.6%, 97.3%] Δ+6.6 [+3.6, +10.0] | 92.2% [88.2%, 95.7%] Δ+4.5 [+0.8, +8.3] | 93.2% [89.5%, 96.3%] Δ+5.5 [+2.7, +8.6] | 92.5% [89.0%, 95.6%] Δ+4.9 [+2.2, +7.8] | 89.8% [85.7%, 93.2%] Δ+2.1 [-1.1, +5.3] | 76.0% [70.6%, 81.1%] Δ-11.7 [-17.0, -6.4] | 89.2% [85.2%, 92.8%] Δ+1.5 [-1.7, +4.9] |
| Action F1 | 87.5% [83.7%, 91.2%] | 85.8% [81.9%, 89.4%] Δ-1.7 [-4.8, +1.7] | 87.5% [83.8%, 90.8%] Δ-0.1 [-3.5, +3.3] | 86.6% [82.1%, 90.6%] Δ-0.9 [-5.6, +3.4] | 92.8% [90.0%, 95.3%] Δ+5.3 [+1.5, +9.2] | 92.0% [89.3%, 94.6%] Δ+4.5 [+0.7, +8.4] | 92.5% [89.8%, 94.9%] Δ+4.9 [+1.8, +8.3] | 91.8% [88.7%, 94.6%] Δ+4.2 [+0.4, +8.2] | 91.7% [88.5%, 94.4%] Δ+4.1 [+0.8, +7.5] | 91.2% [87.8%, 94.3%] Δ+3.7 [+0.2, +7.4] | 91.1% [87.7%, 94.1%] Δ+3.6 [-0.0, +7.3] | 90.8% [87.5%, 93.6%] Δ+3.2 [-0.5, +6.9] | 90.9% [87.4%, 93.9%] Δ+3.3 [-0.6, +7.3] | 87.9% [83.4%, 91.7%] Δ+0.4 [-3.9, +4.5] | 87.1% [83.2%, 90.5%] Δ-0.4 [-3.3, +2.8] | 67.7% [60.6%, 74.4%] Δ-19.8 [-27.5, -12.4] | 85.5% [81.2%, 89.3%] Δ-2.1 [-6.4, +2.0] |
| Action exact | 84.0% [79.5%, 88.4%] | 81.6% [76.8%, 86.2%] Δ-2.4 [-6.4, +1.7] | 83.3% [79.0%, 87.5%] Δ-0.7 [-4.3, +2.9] | 83.0% [77.8%, 87.6%] Δ-1.0 [-5.4, +3.1] | 89.6% [85.8%, 93.1%] Δ+5.6 [+1.1, +9.8] | 87.8% [83.7%, 91.8%] Δ+3.8 [-0.7, +8.3] | 87.8% [83.6%, 91.9%] Δ+3.8 [-0.3, +7.9] | 88.5% [84.6%, 92.2%] Δ+4.5 [+0.3, +8.8] | 88.5% [84.6%, 92.2%] Δ+4.5 [+0.7, +8.4] | 87.8% [83.6%, 91.7%] Δ+3.8 [-0.3, +8.1] | 87.5% [83.2%, 91.5%] Δ+3.5 [-1.0, +7.7] | 86.5% [82.4%, 90.3%] Δ+2.4 [-2.1, +6.9] | 87.5% [83.4%, 91.4%] Δ+3.5 [-1.0, +7.9] | 85.1% [80.4%, 89.3%] Δ+1.0 [-3.5, +5.5] | 83.0% [78.3%, 87.5%] Δ-1.0 [-4.8, +3.1] | 71.2% [65.5%, 76.8%] Δ-12.8 [-18.6, -7.3] | 83.3% [78.9%, 87.5%] Δ-0.7 [-4.8, +3.4] |
| Runway-critical exact | 91.3% [83.8%, 97.3%] | 88.4% [78.9%, 96.1%] Δ-2.9 [-7.5, +0.0] | 89.9% [82.4%, 96.4%] Δ-1.4 [-6.5, +3.3] | 81.2% [70.1%, 91.0%] Δ-10.1 [-19.0, -2.9] | 88.4% [79.3%, 95.9%] Δ-2.9 [-11.3, +4.6] | 89.9% [81.0%, 97.0%] Δ-1.4 [-9.4, +5.7] | 92.8% [84.6%, 98.7%] Δ+1.4 [-6.4, +8.6] | 94.2% [88.0%, 98.7%] Δ+2.9 [-2.4, +9.1] | 91.3% [83.8%, 97.3%] Δ+0.0 [-5.7, +5.7] | 89.9% [81.3%, 97.0%] Δ-1.4 [-8.3, +4.3] | 88.4% [79.1%, 96.2%] Δ-2.9 [-10.6, +3.2] | 89.9% [81.0%, 97.1%] Δ-1.4 [-9.3, +5.9] | 88.4% [78.5%, 96.8%] Δ-2.9 [-10.1, +3.2] | 88.4% [79.4%, 96.1%] Δ-2.9 [-7.1, +0.0] | 88.4% [78.9%, 96.1%] Δ-2.9 [-7.5, +0.0] | 59.4% [46.6%, 71.6%] Δ-31.9 [-43.8, -20.0] | 85.5% [76.6%, 93.2%] Δ-5.8 [-12.7, +0.0] |
| Role acc | 57.6% [52.4%, 62.8%] | 75.0% [69.4%, 80.3%] Δ+17.4 [+10.4, +24.4] | 79.3% [73.6%, 84.8%] Δ+21.7 [+15.5, +27.8] | 50.0% [45.1%, 54.8%] Δ-7.6 [-13.7, -1.4] | 83.0% [77.3%, 88.2%] Δ+25.4 [+17.7, +32.6] | 84.8% [79.2%, 89.8%] Δ+27.2 [+20.2, +34.0] | 51.4% [46.7%, 56.1%] Δ-6.2 [-12.1, -0.3] | 75.7% [70.6%, 80.8%] Δ+18.1 [+12.0, +24.2] | 75.4% [70.1%, 80.3%] Δ+17.8 [+11.8, +23.9] | 81.5% [75.5%, 86.9%] Δ+23.9 [+16.7, +31.2] | 81.9% [75.7%, 87.5%] Δ+24.3 [+17.1, +31.4] | 72.1% [66.4%, 77.6%] Δ+14.5 [+8.0, +21.2] | 65.9% [61.1%, 70.6%] Δ+8.3 [+2.9, +13.8] | 61.6% [56.8%, 66.2%] Δ+4.0 [-1.5, +9.5] | 75.4% [69.4%, 81.0%] Δ+17.8 [+10.7, +24.9] | 36.2% [30.8%, 41.8%] Δ-21.4 [-27.7, -15.0] | 59.8% [54.3%, 65.2%] Δ+2.2 [-4.1, +8.6] |
| Full record exact | 42.4% [37.4%, 47.2%] | 55.2% [48.9%, 61.2%] Δ+12.8 [+5.9, +19.7] | 59.7% [53.2%, 66.2%] Δ+17.4 [+10.5, +24.5] | 39.2% [34.4%, 43.9%] Δ-3.1 [-9.2, +3.1] | 70.1% [63.7%, 76.0%] Δ+27.8 [+19.4, +35.8] | 69.8% [63.2%, 75.9%] Δ+27.4 [+19.4, +35.3] | 40.6% [36.1%, 45.3%] Δ-1.7 [-8.0, +4.6] | 60.4% [55.0%, 66.1%] Δ+18.1 [+11.2, +25.0] | 62.2% [56.8%, 67.5%] Δ+19.8 [+13.0, +26.7] | 67.4% [60.6%, 73.7%] Δ+25.0 [+16.8, +33.1] | 68.1% [61.1%, 74.6%] Δ+25.7 [+17.5, +33.6] | 56.2% [50.0%, 62.4%] Δ+13.9 [+5.9, +22.0] | 53.1% [47.7%, 58.4%] Δ+10.8 [+4.0, +17.3] | 49.0% [44.1%, 54.0%] Δ+6.6 [+0.3, +13.0] | 56.9% [50.5%, 63.0%] Δ+14.6 [+7.2, +21.9] | 29.5% [24.6%, 34.6%] Δ-12.8 [-18.6, -7.1] | 49.0% [43.4%, 54.4%] Δ+6.6 [+0.4, +12.6] |

A Δ interval that excludes 0 is a difference the test set supports; one that straddles 0 is a tie.

Exact McNemar on full-record exact vs the first arm (rows where exactly one is right):

| Arm | only arm right | only first right | McNemar p | verdict |
|---|---|---|---|---|
| atc-qwen3-8b | 79 | 42 | 0.00098 | significant (both tests) |
| accounts/francolinjo-co18wqhx/models/atc-qwen3-8b-v2#accounts/francolinjo-co18wqhx/deployments/atc-eval2 | 76 | 26 | 7.4e-07 | significant (both tests) |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 46 | 55 | 0.43 | not significant |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 117 | 37 | 7.2e-11 | significant (both tests) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v2 | 113 | 34 | 4.2e-11 | significant (both tests) |
| accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b | 44 | 49 | 0.68 | not significant |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v1 | 75 | 23 | 1.3e-07 | significant (both tests) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-lightning-30b-v2 | 78 | 21 | 6.9e-09 | significant (both tests) |
| anthropic/claude-opus-5.5 | 102 | 30 | 2.3e-10 | significant (both tests) |
| anthropic/claude-opus-5.5 | 104 | 30 | 9.3e-11 | significant (both tests) |
| openai/gpt-6.1-terra-pro | 81 | 41 | 0.00037 | significant (both tests) |
| openai/gpt-5.5 | 59 | 28 | 0.0012 | significant (both tests) |
| openai/gpt-5.6-terra | 48 | 29 | 0.04 | significant (both tests) |
| router:lora->opus | 85 | 43 | 0.00026 | significant (both tests) |
| accounts/fireworks/models/nemotron-nano-3-30b-a3b | 20 | 57 | 2.9e-05 | significant (both tests) |
| accounts/francolinjo-co18wqhx/models/atc-nemotron-nano-30b-v1 | 50 | 31 | 0.045 | significant (both tests) |
wrote results/test/scores.json
