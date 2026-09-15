# HANDOFF: Troy plates and the Chart Room — the 2026-09-02 redo
Generated: 2026-09-03 09:14 CDT · Session focus: rebuild the schematic sheet on real ground, split the panorama, fix the Chart Room postcard, enrich the geographic sheet

## 1. Goal
A Landmark-quality set of Troy plates for the Homer reader: a geographic Trojan Plain sheet, a schematic sheet that puts the poem's own features on the real ground, two oblique plates of the bay and the camp, and a Chart Room postcard that frames each Iliad scene on the right sheet — all draft apparatus until John flips it.

## 2. Why This Matters / Background
John judged the July schematic diagram ugly and geographically false (no bay, misplaced rivers, colliding labels) and the panorama wrong about the camp's side of the ridge. Ruling set of 2026-09-02, all recorded in `docs/TROY-MAPS-TODO.md` § "Rulings 2026-09-02" (1–8): real ground plus poem features, east-up, camp on the Aegean flank from one shared zone, two panorama plates, water rule schematic-only, Pope's numbered key for dense clusters, area captions never over drawn features, American spelling. Nothing here is deployed; `main` is untouched.

## 3. Current State
- DONE, merged and gated on `claude/plates-integration-2026-09-02` at 9fd16d3b2 (origin): the five August branches; the Chart Room postcard (label-aware camera, sheet clamp, ghost/omit, descale, locator, click-through); stage 1 shared camp zone (`places.json` → `achaean-camp.zone`); stage 2 panorama as `--plate A|B` presets in `scripts/panorama-stage3.py` with the fleet on the Aegean flank; stages 3a/3b renderer support (rotation inside the projection, margin band, ground wash, bbox declares coordinate space) and the ground sheet; stage 4 the poem's features from Opus's 54 records, corrected by a Grok content gate (17 of 18 findings fixed); stage 5a reader wiring (tier-2 labels by zoom, postcard on the map frame, schematic ink token); stage 5b camp block; stage 5c Pope's key (32 numbered features, six groups, hover/focus in PlatePanel and the postcard); geographic enrichment (Beşik Bay, Thymbrios label, Pınarbaşı, Ajax's tomb at Rhoiteion, Kesik cut, Aegean); spelling sweep + `pipeline/tests/test_house_style.py`.
- Gate at 9fd16d3b2: shared vitest 1235, app 27, pytest 765, `build:public` 4,704 pages, preflight ok, 0 broken links.
- PARTIAL: ship-glyph comps. John: "too big, ugly, obtrusive." The lane was stopped mid-option-1; `.claude/worktrees/plates-shipcomp` (branch `claude/plates-shipcomp-2` checked out, `-1` exists) holds UNCOMMITTED edits to `shared/lib/plate.ts`, `shared/__tests__/plate.test.ts`, `apparatus/plates/trojan-plain-schematic.json`, and a render under `build/plate-review/shipcomp/opt1`.
- NOT STARTED: stage 6 (Sol adversarial review of the whole diff, PR to main); the Troy VI lower-city ditch; a `/maps/` tab for the schematic sheet.

## 4. Key Decisions (and why)
- Schematic = geographic ground layers synced by `scripts/sync-schematic-ground.py` and locked by a parity test, not a second copy: rivers and bay agree by construction.
- East-up puts Troy at the sheet's centre, not the top; the containment rule forbids cropping the geographic extent, so Pope's vantage was kept and his composition dropped. Ida is a margin note, not a drawn mountain.
- Two panorama plates because one camera cannot show the fleet on the Aegean flank and Troy across the bay; Troy is invisible from Luce's camp, and the caption says so.
- Pope's key (numerals at the pin, names in the margin and on hover) instead of a per-zoom label solver: eleven pins sit inside 25 px before the walls; names there cannot be solved, only replaced.
- Water-label rule binds the schematic register only; on geographic sheets coastal names may sit over water with a leader (Kum Tepe, Kesik Tepe).
- Group opacity for the ground wash rather than a muted palette (18 tokens × 2 themes avoided).
- Achilles holds the camp's north end, Ajax the south: Od. 24.80–84 and Strabo's Sigeion cult fix Achilles; Ajax's Rhoiteion tomb is across the bay and cannot place him, so the poem's "two ends" relation decides. No left/right anywhere (ruling D1).
- The two springs are drawn with their absence stated once; Book 22 counts the chase's laps at them.

## 5. Traps & Dead Ends
- A preset with `setback 0` drives the panorama camera's pitch to 46° (`Camera` derives pitch from `atan2(alt, setback)`); plate B's first two presets came from that mistake.
- The wall and ditch on plate B were invisible because their group carried a tier-2 class hidden at the overview tier, not because of stroke weight.
- A placement check that diffs moved label boxes misses DROPPED labels; gate on the SET of `data-label-for` ids per sheet (CLAUDE.md registry entry).
- Region captions are centred on their polygon with no collision check ("THE CENTRE" over the ranks, "KESIK CUT" over the camp name); stage 5c gave `centred` requests collision treatment.
- `render-plates.mjs` expects Playwright's headless shell at an old path; two symlinks in the cache dir bridge it (CLAUDE.md).
- Grok forwarders end their turn while the CLI run continues; poll `ps` or nudge, then a Sonnet look-and-fix; John judges the image at every checkpoint.
- `parsePlate` does not check that a `featureKey` placeId is anchored on the plate; the Python validator does. A bad edit passes TS and vanishes the feature.
- The reconstructed Simoeis and Scamander do not meet on this ground; the confluence sits at their closest approach inside the bay, flagged.
- Do not trace the Troy VI lower-city plan: facts (trench positions) with citation are usable, the drawing is not; the dossiers hold only grid-square positions (n28, i25, g28) with the grid-to-easting conversion unresolved.

## 6. Relevant Files & Pointers
- `docs/TROY-MAPS-TODO.md` § "Rulings 2026-09-02" — the eight rulings that bind every lane.
- `docs/HANDOFF-2026-09-02.md` — the short handoff (same state, pushed).
- `apparatus/plates/trojan-plain-schematic.json` — the new sheet: `featureKey`, `sceneKey`, `rotationDeg 90`, `marginRight 340`, `groundOpacity 0.55`, inset `frame`s at y 955.
- `apparatus/places.json` — 35 schematic anchors in lat/lon, `achaean-camp.zone`, tiers/sizes.
- `shared/lib/plate.ts` — `badgeMarkup`/`placeKeyBadges`/`featureKeyMarkup`, `computeCamera` label-aware clamp, `waterReservationBoxes` (schematic only), `labelTier`/`labelSize`, `suppressLayerLabels`, `frame` on `PlateResult`.
- `shared/lib/geo.ts` — `rotationDeg` inside `project`/`viewportFromBBox`.
- `shared/components/Reader.svelte` — `applyPlateCamera` (postcard: focus, descale, locator, badges, `FURNITURE_SELECTOR`).
- `app/src/components/maps/PlatePanel.svelte` — `focusIds`, `plate-zoomed`, badge tooltip, key-row highlight, certainty filter.
- `scripts/panorama-stage3.py` — `plate_presets()` A/B, `aegean_fleet`, `defence_strokes`, camera CLI flags; `docs/PANORAMA-RESUME.md` § "Two plates".
- `scripts/render-plates.mjs` — `--tiers 1|all`, `--places`, `--pxcrop`.
- `scripts/sync-schematic-ground.py` — the 27 ground layers.
- Session scratchpad (may be gone): `stage4-anchors.json/.md` (Opus's 54 records), `stage5c-design.md`; both are reflected in the data and the plate.
- Memory: `~/.claude/projects/-Users-johnboyer-Developer-homer-reader/memory/plates-chart-room-state.md`.

## 7. Open Work (status, with dependencies)
- Ship glyph comps are half-built (see 3); John wants to SEE both before choosing; nothing else on the schematic sheet's camp should change until he does.
- John's rulings outstanding: the Trojan bivouac (fan vs the literal ground between river and ridge), the two panorama plates as rendered, the download of Blindow–Hübner–Jansen 2014 (open access, DOI 10.15496/publikation-14981) for the Troy VI ditch, a live browser look at the postcard and tooltip (the last lane's sandbox could not reach localhost; wiring is proven by component tests only).
- Stage 6 depends on the ship glyphs and the bivouac call: Sol review of `git diff main...claude/plates-integration-2026-09-02`, then the PR to main, which also carries the July-28 cross-epic dual search and phrases filter. Deploy is John's.
- Parked: a `/maps/` tab for the schematic sheet (291 postcards have no click-through today); the `parsePlate` anchoring check.

---
## Prompt for the Fresh Agent
The Troy plates redo of 2026-09-02 is merged and gated on `claude/plates-integration-2026-09-02` (9fd16d3b2); main is untouched and nothing is deployed. The schematic sheet now sits on the real ground east-up with Pope's numbered key; the panorama is two plates; the geographic sheet carries seven new features; the Chart Room postcard frames scenes on the map frame. One lane was stopped mid-work: the ship-glyph comps in `.claude/worktrees/plates-shipcomp`, uncommitted. John has four rulings outstanding and stage 6 (review and PR) has not started. Every ruling that binds is in `docs/TROY-MAPS-TODO.md` § "Rulings 2026-09-02".

Before responding, read every file listed under "Relevant Files & Pointers" above.
Do not summarize, paraphrase, or claim you already have context — actually read each
file. Treat every claim in this handoff as context to verify against the code, not
facts to trust blindly. Then wait for my instructions before taking any action.
