# GMAPS — 120-second video script

Screen recording + voice. Numbers in [brackets] come from `results/test/README_results.md` at 12:30. Speak at a normal pace; this is ~280 words.

---

**[0:00–0:15] Problem — the runway monitor on screen, paused at t=0.**

> Runway incursions start as two clearances that can't both be true. "Cleared to land two eight left." "Cross two eight left at echo." Today the cross-check lives in one controller's head. The FAA logged over sixteen hundred incursions last year.

**[0:15–0:60] Demo — press play at 2×.**

> GMAPS listens to the frequency. Every transmission becomes a typed record — role, callsign, instruction, runway. *(point at the JSON appearing on the left)* The ledger tracks who holds each runway. At twenty-eight seconds the second clearance lands and the ledger flags it: possible conflict, both sides named, the rule cited. *(banner, red runway)* Ground issues hold short — *(switch to the resolved variant)* — and the conflict clears. Decision support only. The controller decides.

**[0:60–1:40] Results — the table.**

> The only learned part is the parser, so that's what we benchmarked. Two hundred eighty-eight real tower transmissions from three airports the model never saw, gold-labelled by the dataset authors, frozen before the event. Same prompt, same scorer, every arm.
>
> Claude Opus 5.5: [M]% full-record accuracy at [c₁] dollars per thousand transmissions, [p₁] seconds each.
> Our fine-tuned 8B open model, trained on Fireworks in [t] minutes for about [$]: [N]% at [c₂] dollars per thousand, [p₂] seconds. *(paired CI line)* Same adapter, running on a DGX Spark in the tower with no internet: [N′]%, [p₃] seconds.
>
> A tower produces ten thousand transmissions a day. That's [x] dollars a day on a frontier API — or [y] on an open model you own, the only one of the two that's allowed to hear live tower audio in the first place.

**[1:40–2:00] Tradeoffs + close.**

> It's narrow — ATC phraseology only. The test airports are European and Australian; US phraseology is synthetic in training. The on-prem number is bandwidth-bound and will drop with an FP8 model. Everything — data pipeline, scorer, adapter, hashes — is in the repo. GMAPS: the cross-check that was in the controller's head, now on the frequency.

---

Recording checklist: 1440×900 window, dark theme, viz at 2× speed, table as a rendered markdown page (not a terminal), no cursor wandering, one take per section and splice.
