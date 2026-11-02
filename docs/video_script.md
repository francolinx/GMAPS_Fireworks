# GMAPS — 120-second video script

Screen recording + voice. Numbers are from `results/test/scores.md` (final, 13:30 PT). The 120 s cut in `docs/video/gmaps_fireworks_120s.mp4` is silent; this is the voice-over to record on top. Speak at a normal pace; this is ~280 words.

---

**[0:00–0:15] Problem — the runway monitor on screen, paused at t=0.**

> Runway incursions start as two clearances that can't both be true. "Cleared to land two eight left." "Cross two eight left at echo." Today the cross-check lives in one controller's head. The FAA logged over sixteen hundred incursions last year.

**[0:10–0:40] As-is — `docs/video/lga_04_asis_2x.mp4`: LaGuardia, March 22, 2026, from the NTSB timeline. No rule runs.**

> 23:35:07 — tower clears Jazz 646, a CRJ900 with 76 people on board, to land on runway 4. 23:37:04 — with the aircraft a quarter mile out, tower clears Truck 1, a Port Authority fire truck, to cross runway 4 at Delta. Both are valid clearances. Watch the right-hand panel: the parser on the DGX Spark reads every transmission — who, which callsign, which instruction, which runway — in about three seconds. Nothing compares them. 23:37:12, "stop". 23:37:20, "stop, Truck 1". 23:37:22, the truck is on the runway. *(freeze)*

**[0:40–0:59] With GMAPS — `docs/video/lga_04_gmaps_2x.mp4`.**

> Same radio, same parser. The instant the crossing clearance is parsed — 23:37:04 — the ledger holds two authorizations for runway 4 and flags it: Jazz 646 cleared to land versus Truck 1 cleared to cross at Delta, FAA 7110.65 cited, both movers at Delta within twenty seconds. That is eight seconds before the first "stop" and eighteen before the truck entered the runway. Whether it changes the outcome is for the NTSB to say. Decision support only; the controller decides. *(in memory card)*

**[0:59–1:07] The test — card.**

> The only learned part is the parser, so that's what we benchmarked: 288 real tower transmissions from three airports the models never saw, gold-labelled by the dataset authors, hash frozen on October 31. Same prompt, same scorer, every arm.

**[1:07–1:31] Before → after — the chart.**

> Off the shelf, Qwen3-8B gets 42 percent of records fully right; with our LoRA, 60. NVIDIA's Nemotron-30B goes from 39 to 70 — a statistical tie with Claude Opus 5.5 at 67, at a forty-fifth of the cost; a second, three-epoch run lands at 69.8 and ties again. Ten dollars of training on Fireworks each. And on the LaGuardia lines, the off-the-shelf models read the crossing clearance as a pilot read-back and never alert; the fine-tuned ones alert at 23:37:04. Every gap is tested two ways, McNemar and a recording-level bootstrap, and the experiments that didn't help are in the table.

**[1:31–1:43] Tradeoffs + close.**

> It's narrow — ATC phraseology only. The test airports are European and Australian; US phraseology is synthetic in training. On the Spark the 8B runs at three seconds a transmission in bf16; Nemotron Lightning in NVFP4 at one and a half. Everything — data pipeline, scorer, adapter, hashes — is in the repo. GMAPS: the cross-check that was in the controller's head, now on the frequency.

---

Recording checklist: 1440×900 window, dark theme, viz at 2× speed, table as a rendered markdown page (not a terminal), no cursor wandering, one take per section and splice.
