
## qwen3-8b-base  (fewshot=5, 2026-11-01T05:54:34Z)

### dev (ATCO2 gold, training airports)
| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b-base | 100.0% | 90.0% | 54.4% | 44.9% | 77.9% | 83.9% | 58.2% | 42.4% | 2792 | 3749 | — |

(n=85 segments; runway-critical subset n=31)
wrote results/dev/qwen3-8b-base.dev.scores.json

### synthetic US stress (gold by construction)
| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b-base | 100.0% | 81.8% | 82.4% | 60.6% | 97.2% | 100.0% | 62.7% | 47.3% | 2969 | 3932 | — |

(n=300 segments; runway-critical subset n=184)
wrote results/dev/qwen3-8b-base.stress.scores.json

## atc-qwen3-8b  (fewshot=0, 2026-11-01T06:00:43Z)

### dev (ATCO2 gold, training airports)
| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| atc-qwen3-8b | 100.0% | 93.8% | 69.8% | 73.5% | 85.7% | 93.5% | 88.1% | 70.6% | 2740 | 3718 | — |

(n=85 segments; runway-critical subset n=31)
wrote results/dev/atc-qwen3-8b.dev.scores.json

### synthetic US stress (gold by construction)
| Model | JSON valid | Callsign F1 | Cmd span F1 | Value F1 | Action F1 | Runway-critical exact | Role acc | Full record exact | p50 ms | p95 ms | $/1k segs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| atc-qwen3-8b | 100.0% | 97.2% | 99.4% | 96.1% | 100.0% | 100.0% | 99.3% | 96.3% | 2956 | 3967 | — |

(n=300 segments; runway-critical subset n=184)
wrote results/dev/atc-qwen3-8b.stress.scores.json
