# GMAPS — 120-second video script

Screen recording + voice. Numbers are from `results/test/scores.md` (final, 13:30 PT). The 120 s cut in `docs/video/gmaps_fireworks_120s.mp4` is silent; this is the voice-over to record on top. Speak at a normal pace; this is ~280 words.

---

**[0:00–0:15] Problem — the runway monitor on screen, paused at t=0.**

> Runway incursions start as two clearances that can't both be true. "Cleared to land two eight left." "Cross two eight left at echo." Today the cross-check lives in one controller's head. The FAA logged over sixteen hundred incursions last year.

**[0:10–0:46] As-is — `docs/video/sfo_28l_asis_2x.mp4`, no rule runs.**

> Tower: "Maple two one two, runway two eight left, cleared to land." Ground: "Rescue seven, cross runway two eight left at echo." Both are valid clearances. Watch the right-hand panel: the parser on the DGX Spark reads every transmission — role, callsign, instruction, runway — in about three seconds. But nothing compares them. Rescue 7 rolls onto the runway as Maple 212 crosses the threshold. *(freeze: "AS-IS: two valid clearances, nobody cross-checked them")*

**[0:46–1:16] With GMAPS — `docs/video/sfo_28l_gmaps_2x.mp4`.**

> Same radio, same parser. At twenty-eight seconds the second clearance lands in the ledger and it flags the pair: possible conflict, 28L, Maple 212 cleared to land versus Rescue 7 cleared to cross at echo, FAA 7110.65 cited. Ground issues hold short. Rescue 7 stops at the hold line on echo. *(green caption)* Decision support only; the controller decides.

**[1:16–1:24] The test — card.**

> The only learned part is the parser, so that's what we benchmarked: 288 real tower transmissions from three airports the models never saw, gold-labelled by the dataset authors, hash frozen on October 31. Same prompt, same scorer, every arm.

**[1:24–1:48] Before → after — the chart.**

> Off the shelf, Qwen3-8B gets 42 percent of records fully right; with our LoRA, 60. NVIDIA's Nemotron-30B goes from 39 to 70 — a statistical tie with Claude Opus 5.5 at 67, at a forty-fifth of the cost. One epoch, ten dollars of training on Fireworks. Every gap is tested two ways, McNemar and a recording-level bootstrap, and we report the two experiments that didn't help.

**[1:40–2:00] Tradeoffs + close.**

> It's narrow — ATC phraseology only. The test airports are European and Australian; US phraseology is synthetic in training. On the Spark the 8B runs at three seconds a transmission in bf16; Nemotron Lightning in NVFP4 at one and a half. Everything — data pipeline, scorer, adapter, hashes — is in the repo. GMAPS: the cross-check that was in the controller's head, now on the frequency.

---

Recording checklist: 1440×900 window, dark theme, viz at 2× speed, table as a rendered markdown page (not a terminal), no cursor wandering, one take per section and splice.
