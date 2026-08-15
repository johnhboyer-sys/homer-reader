# HANDOFF: The Troy plates — a lit panorama, two geographic sheets, a schematic sheet
Generated: 2026-08-15 12:15 CDT · Session focus: making "The Ships, the Bay, and Ilios" read as a drawn landscape, plus accuracy fixes across the sister plates

## 1. Goal

Three Troy artifacts in one edition: a navigable raised-oblique panorama ("The Ships, the Bay, and Ilios"), two geographic map sheets (Trojan Plain, Troad), and a schematic sheet carrying the poem's own spatial logic. The panorama is the piece John cares most about and the one that took this session; the Chart Room is meant eventually to hang scene frames off it.

## 2. Why This Matters / Background

Two earlier sessions built complete plates that were killed on sight ("it's just shapes", "an archeological picture of troy is useless"). The prior session fixed that by gating on rendered images. This session's arc: the panorama was accurate and dead — John's word was **"it looks like a video game"** — and most of the work was finding out why and fixing it.

John directs from images, one observation at a time, and is usually right about the symptom while the cause is somewhere else entirely. Several of his one-line notes ("troy looks like it's floating", "the ships look buried", "stubble on a man's chin") each turned out to sit on top of a real arithmetic bug.

## 3. Current State

**The panorama — `panorama/lit-plate` @ `b373fd1a0`, worktree `../homer-reader-takeA`, pushed.** This is the live artifact and the only branch carrying the current plate.

- DONE: monotonic height curve; mesh resolving Troy's bluff; slope shading + real cast shadows from a low afternoon sun; ground-cover colour replacing hypsometric bands; all lattice-derived lines smoothed; contours off by default; aerial perspective by Beer–Lambert; Fresnel water; legend moved off the map face into a margin below the neatline; the poem's vegetation as mass; the fleet redrawn as ships on props in ordered ranks.
- PARTIAL: the margin — John's last note was **"legend is too busy"**. A lane was briefed and stopped before it edited anything; brief is in this session's history, nothing on disk.
- NOT STARTED: night mode (full moon, Book 8 watchfires — Il. 8.553-65); Chart Room wiring; `apparatus/panorama/troy-panorama-camera-targets.json` still carries the old exaggeration string and is consumed by nothing.

**Geographic sheets — `claude/build` @ `9bf6e303f`, pushed.** Both sheets, all of the previous day's fixes, data preflight 0 errors, 4,705 pages build. `plates/label-class-symbology` @ `e3846758b` carries the same plus the barrier deletion and is not merged into `claude/build`.

**Schematic sheet — `plates/schematic-comp` @ `e966484dd`, pushed.** Achilles-corner pile-up fixed; type hierarchy and engraved marks from the earlier recut. Still WIP; hill silhouettes faceted, inset two-thirds empty.

**Engraved comp — `panorama/engraved-comp` @ `919990151`, pushed.** Parked, not a candidate. Preserved for its finding, not its output.

Nothing is deployed. `main` is untouched and does not contain `shared/lib/plate.ts` at all.

## 4. Key Decisions (and why)

- **The wash won over the engraved take.** Both were built blind to each other and judged side by side. B failed because it layered hatching *over* the existing wash instead of replacing it — a real engraving has nothing underneath.
- **Sun at bearing 228.4°, altitude 9.9°** — a low afternoon sun, the only light of three tried in which Troy's bluff reads. An early-August morning sun was shipped first to match the poem's season; John overruled it: the siege stood ten years, so the season is free. The cartouche states bearing and altitude only — no season, no solstice.
- **Colour says what the ground is, not how high it is.** Hypsometric banding is a plan-view device; in an oblique it says height twice and reads as stacked terraces. Ground-cover classes replaced it; the elevation key became a ground-cover key.
- **The 1.5 MB SVG budget is retired.** It measured raw bytes, which track nothing: gzipped the plate is ~250–485 KB with under 12k elements. The real ungated question is pan/zoom frame rate on a phone, which nobody has measured.
- **Vegetation density is a drawing rule, the class is the evidence.** Scrub cover follows DEM curvature, slope and aspect; 66% of the ridge is bare. The key says so.
- **Ship count is a declared convention; ship SIZE now is too.** The key already licensed drawing fewer hulls than the Catalogue's 1,186. It did not license enlarging them, which is what a lane had quietly done — now ×2.5 with length and beam together, declared.
- **The 44% of the sheet marked "not classified" stays that way.** The three ridge layers are cut at the 20, 40 and 100 m contours — three thresholds, not one criterion to extend — and the unclassified region contains Mount Ida, which Il. 23.117 calls forest.

## 5. Traps & Dead Ends

- **John's diagnosis is usually right; mine was usually wrong about the cause.** Documented instances this session: the terrain blur cost 1.14 m RMS, not the factor of three I claimed (the real smoother was `SHADE_SMOOTH`, σ ≈ 190 m of ground); "no stroke on the reconstructed shore" was refuted by measurement (fill contrast 1.41:1, nothing would have been visible); drawing ships at true scale *understates* them threefold because a galley end-on down a 17° depression foreshortens to a third of herself.
- **Tests pass while the plate is broken.** A malformed CSS comment silently killed the scrub rule and Chrome painted whole hillsides opaque black — every test green. Rendering and looking is the only gate that catches this class.
- **The label-contrast annulus method measures terrain the lettering never touches.** It had capped the plate's tone at `SHADE_MAX` 0.40 for nothing; with the halo credited every label was already at 7.48:1.
- **Do NOT re-run the engraved take layered over the wash.** If revived it must be line-only on bare ground.
- **Do not scale marks with zoom.** Mark-based treatments only survive magnification if regenerated per tier.
- Three separate token-inversion bugs were found (river, contours, city walls, then the hulls again). Dark theme is not the light theme inverted; whatever is darker than its ground by day stays darker at night. Regression tests now assert this.
- `lagoon-bronze` in `apparatus/plates/trojan-plain.json` has a real connectivity gap at the bay mouth that `fix-lagoon-connectivity.py` never reached. Patched in the panorama script only.

## 6. Relevant Files & Pointers

- `scripts/panorama-stage3.py` (in `../homer-reader-takeA`) — the entire panorama renderer. Camera, curve, shading, shadows, ground cover, vegetation, fleet, margin.
- `pipeline/tests/test_panorama_relief.py` — 153 tests; several deliberately assert that *old* buggy behaviour inverts, so the defects stay documented.
- `docs/research/GROUND-COVER-TROJAN-PLAIN.md` — the classes, their evidence grades, the DEM-derivable rules, and the DO-NOT-DRAW list. Input to the renderer, not a narrative.
- `docs/research/DRAWN-LANDSCAPE-DIRECTION.md` — the diagnosis that a continuous gradient has no unit to withhold, so selectivity is unavailable to a wash. LoC Panoramic Maps (~1,800 PD sheets, our exact projection) named as the flat-ground reference.
- `docs/research/DEPICTIONS-OF-TROY.md` — Pope/Harris 1716 and the fleet-as-repeating-glyph lesson.
- `docs/research/PHOTOGRAPHS-OF-THE-TROAD.md` — PD photographs of this ground; Schliemann 1874 Atlas plates IV–V are the reciprocal view.
- `docs/TROAD-CARTOGRAPHY.md` — binding aesthetic. Note its hillshade ban rests partly on "a raster cannot be re-themed", which is why every colour on the plate is a `var()` token.
- The commit messages on `panorama/lit-plate` carry the measurements and the rejected alternatives; they are the real record and are not duplicated here.

## 7. Open Work (status, with dependencies)

- The margin is too busy; nothing has been changed. The question is which glosses must travel with the image and which the page around it can carry — the glosses are the honesty mechanism, so cutting them thoughtlessly makes the plate assert silently.
- The huts are identical straw slabs; more conspicuous now the beach is calmer.
- The rampart still wears the citadel's masonry token and reads salmon against the new camp.
- Two Homeric itineraries — the ἀμαξιτός under the wall (Il. 22.146) and Priam's night ride (24.349-51) — are drawn as one continuous road, which the plate's own note admits the poem never joins. Affects both the panorama and the schematic sheet.
- KESIK TEPE fails contrast on the geographic sheets because it letters across the shoreline glow; it is a placement problem, not a halo one.
- Night mode depends on nothing; the shadow machinery is a light direction and a palette away. Watchfires are point lights and are the one thing `ShadowField` does not model.
- Chart Room wiring depends on the camera-targets file being regenerated for the current curve.
- `panorama/lit-plate` is not merged into `claude/build`; the plates and schematic branches are not merged into each other. Deploy builds from `main`, which none of this has reached.

---
## Prompt for the Fresh Agent

You are picking up the Troy visual work on the homer-reader project (`~/Developer/homer-reader`) — a digital Landmark-style edition of the Iliad and Odyssey. Read `CLAUDE.md` first; it carries the standing rules and this handoff does not repeat them.

The live artifact is a raised-oblique panorama, "The Ships, the Bay, and Ilios," on branch `panorama/lit-plate` in the worktree `../homer-reader-takeA`. Two geographic map sheets and a schematic sheet exist on separate unmerged branches. Nothing is deployed and `main` contains none of the plate system.

John reviews a rendered image at every stage and directs from it. His observations are reliable about the symptom and the cause is frequently elsewhere — several one-line notes this session each sat on top of a distinct arithmetic bug. Rendering an image and looking at it is a required gate; tests have repeatedly stayed green while the plate was visibly broken.

Before responding, read every file listed under "Relevant Files & Pointers" above. Do not summarize, paraphrase, or claim you already have context — actually read each file. Treat every claim in this handoff as context to verify against the code, not facts to trust blindly. Then wait for my instructions before taking any action.
