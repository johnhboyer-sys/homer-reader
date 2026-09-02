# HANDOFF: Troy renditions, map plates, and the navigable panorama
Generated: 2026-08-12 17:47 CDT · Session focus: three visual deliverables for Troy — generated city renditions, rebuilt Landmark map sheets, and a navigable oblique panorama

## 1. Goal

Three artifacts. (a) An artistic rendition of Homer's Troy standing and inhabited — top-down and oblique — generated in Grok Imagine from a researched brief. (b) The Trojan Plain and Troad map sheets rebuilt to Landmark-atlas standard. (c) "The Ships, the Bay, and Ilios" — a navigable raised-oblique plate with level-of-detail tiers, serving as the Chart Room's frame source for scenes at specific places.

## 2. Why This Matters / Background

John saw the Odyssey film and wanted Troy drawn as a movie concept artist who did the research would draw it — explicitly *not* an archaeological plan. Two prior attempts (2026-07-28 and 07-30) were built to completion and killed on sight: "it's just shapes, my 5 year old could draw this" and "an archeological picture of troy is useless." ~104 commits in three days produced nothing shippable.

The structural fix this session: **taste is checked first, on a cheap sample, before production.** Every lane stops at a gate with a rendered image. John directs from the image. It held — four terrain iterations and two style gates, and nothing unusable got built past a checkpoint.

John's standing instruction this session: be concise; show renders at every stage; stop when told.

## 3. Current State

**DONE**
- `docs/research/RESEARCH-TROY-APPEARANCE.md` (933 lines, Grok) — what the *Iliad* says Troy looked like with Greek + book.line, Troy VI elevation archaeology with Chicago citations, ranked comparative analogy, artist's brief, DO-NOT-DRAW list, "not knowable" table. BC/AD clean, ~51 citations.
- `docs/research/TROY-PROMPT-PACK.md` (453 lines) — six image prompts (3 top-down daylight, 3 oblique cinematic), negative block, 12-point scoring checklist, failure-mode table.
- `docs/research/AUDIT-PLATE-LABELS.md` — Grok's label-class table for all 73 places on both geographic sheets, plus defect list.
- `docs/research/TROY-RENDITIONS-APPARATUS.md` — captions for both renditions (attested/analogy/licence split + AI-generation disclosure), label overlay spec, Chicago sources block.
- Bay fix: `panorama/bay-fix` @ `eca265eec`. Verified: shared/ 1046 pass, validate_plate clean, pipeline plate/preflight 75/75.
- Map sheets: `plates/label-class-symbology` @ `3c4a4a9e2`. Verified: shared/ 1045 pass, app/ 17/17, build 4,705 pages, preflight 1 pre-existing error (Shield missing `sources`, untouched).
- Panorama stages 1–3: `panorama/troy-plain` @ `430f8ba01`. SVG 1,150,594 bytes against a 1.5 MB budget.

**PARTIAL**
- Image renditions: one usable oblique exists (John's "image 2" — city, campfire plain, ships on the far shore). Scored 2 clear fails on gating items (plumb walls, rectangular plan) plus crenellations. **No top-down has ever been generated.**
- Panorama: direction approved at stage 3, "still not detailed enough." Held.

**NOT STARTED**
- Chart Room wiring. `apparatus/panorama/troy-panorama-camera-targets.json` (20 rows) is emitted; nothing consumes it.
- Label overlay for the top-down rendition (spec written, no image to overlay).
- Merging any of the three branches.

**NOT MERGED — merge order matters:** `panorama/bay-fix` first; the other two render its geometry.

## 4. Key Decisions (and why)

- **Renditions are generated (Grok Imagine), not coded SVG** — free tier only, and it is the movie-artist path. Claude cannot generate; John runs the batches.
- **Captions state plainly that images are AI-generated** from a researched brief (John's ruling), with attested / analogy / licence split.
- **Panorama subject changed on evidence.** Began as "the plain from the Achaean camp." Kayan's conclusion, already in our own dossier: the ground between camp and Troy was water and swamp, "not suitable for passage or battle," with the battlefield a dry sand fan at Troy's immediate western foot. So the bay *is* the subject, not an obstacle. This also explains why the ships mattered.
- **Panorama is schematic register.** Terrain is true DEM projection; waypoints are the poem's order along the ground with `positionBasis: "conjectural"`. Almost nothing on that plain has a defensible coordinate.
- **Bronze Age water re-derived by connectivity** (John chose this over clipping or demoting to marsh): flood-fill DEM cells ≤10 m from Kayan's published bay head (39.9582, 26.2062), keep only what reaches open sea. Removes the artifact by construction, and the layer note states the arithmetic.
- **Built heights stay TRUE (×1); only the ground is exaggerated** (4× ≤100 m, tapering to 1× above 300 m). Exaggerating built heights made the fleet look like it was riding at anchor.
- **Ilios stays a small labelled mark on the panorama.** The detailed city is the separate rendition — which is what John asked for originally.
- **Architecture deferred by John's call.** Sol's re-scope (7 blocking findings) was set aside: no outer-sheet/camera contract, no Chart Room fixes, no leader lines, no solver rewrite. Map sheets keep the legend inside the map canvas.
- **Camera settled by an Opus decision lane**: viewpoint 39.9755 N 26.1785 E, heading 104.0°, hfov 72°, alt 800 m, setback 1500 m, pitch ≈16° down. Do not re-derive.
- **Plate captioned "above the Achaean camp," not "from" it** — Luce's camp sits on the ridge's outer Aegean flank, from which Troy is invisible.
- **Rejected 3.5 km camp-to-Troy** (Luce asserting Strabo's 20 stades in prose) in favour of 5.56 km — the same paper's own figure draws the camp at 5.4 km.

## 5. Traps & Dead Ends

- **Four terrain renders failed before anyone suspected the data instead of the camera.** `lagoon-bronze` was a hand-stitched ring filled without checking its interior was low ground: 16.4 km², max elevation 35.1 m, flooding the ridge the camp sits on. When renders keep failing geometrically, check the source layer.
- **Eye-level panorama cannot carry labels.** Everything on the plain compresses into a couple of degrees near the horizon. Depth bands separate foreground from background but *not* near from far along one line of sight. Raised oblique fixed it.
- **Stage 2's verdict ("the camera defeats the subject", Ilios at 50 px) was against the wrong bar** — the brief omitted that this plate zooms. At 4× the ships are ~64 px and Ilios ~200 px. Do not re-derive that conclusion.
- **Image-to-image locks in the seed.** Feeding an empty-fort result back produced four generations of empty forts. Prompt text cannot overcome a bad reference at low strength.
- **Over-emphasising the wall batter deleted the city.** Four forceful sentences about wall geometry crowded out the interior; "like the flank of an earthen dam" pushed it to a bare earthwork. In prompts, every sentence competes with every other.
- **A straight wagon-road from Ilios to the camp crosses the bay** and prints the oak, fig, springs and tomb of Ilos on open water. There is now a guard that hard-fails if any road point lands in the lagoon.
- **`LabelRole` in `shared/lib/plate.ts:1425` has four values**, not five. The five-class scheme is print Landmark convention from `docs/TROAD-CARTOGRAPHY.md`, not the codebase. Briefs asserted otherwise for hours.
- **Ships keyed to `--text` invert to white in dark theme** — Homer's black ships go pale. They need their own per-theme token pair.
- **The World History Encyclopedia battlefield map is in copyright.** Study and cross-check only; never trace or reproduce.
- **Red tile roofs are the wrong millennium**, not a stylistic quibble. Flat clay roofs are *attested* at Troy (Tolman §9), not inferred. Every image generator produces tile by default.

## 6. Relevant Files & Pointers

- `docs/PANORAMA-RESUME.md` — panorama brief; **superseded** on two points (raised oblique not eye-level panorama; subject is now the bay).
- `docs/research/RESEARCH-TROY-APPEARANCE.md` §1.11 — "Commonly assumed — NOT in the text." The best honesty content in the file. §2.1 — wall scarp ratios per sector (Tolman & Scoggin 1903, PD): West 0.40, East 0.37, South 0.23 m setback per metre, i.e. 13–22° from vertical. §6.2 — DO NOT DRAW, 14 items. §7 — "Not knowable."
- `docs/research/RESEARCH-PALEOGEOGRAPHY.md:3699-3798` §3.3 — the finding that killed the Bronze Age barrier and the lagoon depending on it. `:844-895` — Kayan 2002, 1003 on the dry delta fan being the battlefield.
- `docs/research/TROY-PROMPT-PACK.md` — six prompts; scoring checklist at ~:391.
- `shared/lib/plate.ts:1425` — `LabelRole`. `:3650` — the `role: 'settlement'` hardcode (fixed on the plates branch). `:1579` — `placeLabelCandidates()` greedy solver.
- `scripts/panorama-stage3.py` (panorama worktree) — the current renderer, all camera params.
- `scripts/fix-lagoon-connectivity.py` — reproducible bay derivation.
- `apparatus/panorama/troy-panorama-camera-targets.json` — 20 Chart Room camera rows, unconsumed.
- `docs/TROY-MAPS-TODO.md` §"Chart Room diagnosis" (~:345) — the "postcard + plate" design, drafted, never signed off.
- Worktrees: `../homer-reader-panorama` (`panorama/troy-plain`), `../homer-reader-plates` (`plates/label-class-symbology`).
- Renders: `../homer-reader-panorama/build/panorama/stage3-*.png`.

## 7. Open Work (status, with dependencies)

**Awaiting John's rulings — nothing downstream can proceed without these:**
- Two image picks. No top-down has been generated; the oblique candidate has plumb walls and a rectangular plan.
- Scaean Gate naming on the renditions and panorama: Homeric names, or Dörpfeld letters? The apparatus lane recommends Homeric names with a speculative-tier mark, reasoning that the cartographic plates use letters *because* they trace surveyed geometry and a picture claims no such thing.
- The agora: point label, or omitted? Poem gives location, no extent, no analogy supplies a footprint.
- The Achaean wall conflict: Homer's order is sea → ships → wall → ditch → plain, but on the reconstructed bay the wall lands on the ridge with Troy across water. Drawn that way and flagged in the plate note.

**Known gaps:**
- The Akrotiri analogy is ranked in `RESEARCH-TROY-APPEARANCE.md` §3.4 with no primary citation, and it is load-bearing in both rendition captions — it licenses the second storeys. Needs Doumas or Marinatos, or the clause comes out.
- Callicolone's gazetteer pin sits 8 km east of Troy against Strabo's 40 stades.
- The `river` suffix is inconsistent on the Troad sheet (Granicus/Aesepus/Satnioeis have it, Scamander doesn't). Chryse's coordinate is ~65 km from the Strabo 13.1.63 location its own note cites.
- Mount Ida keeps a dot on the Troad sheet the audit wanted dropped.

**Panorama, held after stage 3:** direction approved, "still not detailed enough." Weak points named by its maker: the bottom third is the ridge's back slope carrying the cartouche rather than solved; Ida is faint at 66 km and its label points at little; portrait drops to tier 1 because tier-2 labels are anchored across the full width and get sliced.

**Chart Room integration** depends on the panorama reaching sufficient detail. It was absent from every panorama brief until stage 3 and is central, not optional.

---
## Prompt for the Fresh Agent

You are picking up work on the homer-reader project (`~/Developer/homer-reader`, branch `claude/build`) — a digital Landmark-style edition of the Iliad and Odyssey. Read `CLAUDE.md` first; it carries the standing rules and this handoff does not repeat them. This file is `HANDOFF.md` in the repo root; paths below are relative to it unless stated otherwise.

Three visual deliverables are in flight: generated artistic renditions of Homer's Troy, rebuilt Landmark map sheets for the Trojan Plain and Troad, and a navigable raised-oblique panorama titled "The Ships, the Bay, and Ilios." Research is complete and committed. Three branches exist and none is merged; `panorama/bay-fix` must merge before the other two because they render its geometry.

John reviews a rendered image at every stage and directs from it. Two previous sessions built complete plates that were killed on sight, so no lane runs long without a visual gate. Several rulings are outstanding and are his alone.

Before responding, read every file listed under "Relevant Files & Pointers" above. Do not summarize, paraphrase, or claim you already have context — actually read each file. Treat every claim in this handoff as context to verify against the code, not facts to trust blindly. Then wait for my instructions before taking any action.
