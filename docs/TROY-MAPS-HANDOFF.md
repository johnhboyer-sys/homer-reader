# Troy & Troad maps — state at pause, 2026-07-28 17:45

Paused at John's request. Everything below is committed and pushed to
`claude/build`. Nothing is half-written; no agent is running.

## Where to look first

- `/maps/` tabs: `troad` (drawn plate, Drawn/Tiles toggle), `plain`, `citadel`,
  `shield`.
- Preview binds to **4323** — sibling projects hold 4321-4322.

## Built and verified

| Piece | Where |
|---|---|
| Shared projection | `shared/lib/geo.ts` (+ `viewportFromBBox`) |
| Plate renderer | `shared/lib/plate.ts` — `parsePlate`, `renderPlate`, `computeCamera`, primitives `hachure` / `stipple` / `waterlines` / `shipRow` / `wallGlyph` / `tumulus` |
| Shield renderer | `shared/lib/shield.ts` |
| Validators | `pipeline/homer_pipeline/apparatus_places.py`, hooked into preflight |
| Gazetteer | `apparatus/places.json` — 280 → **325** records |
| Plates | `apparatus/plates/` — `trojan-plain`, `troad`, `trojan-plain-schematic`, `troy-citadel`, `shield-of-achilles` |
| Page surface | `app/src/components/maps/PlatePanel.svelte`, `MapsPage.svelte` |
| Scene plumbing | `places: string[]` on scenes; `scene-place.ts` precedence |
| Source dossiers | `docs/TROAD-SOURCES.md`, `docs/TROAD-CARTOGRAPHY.md` |

Green: **883** tests in `shared/`, 7 in `app/`, 38 validator tests, preflight 0
errors, 4705 pages build. The one red pytest is the pre-existing χάω test.

## The two registers (CLAUDE.md rule, John's call)

Geographic plates carry only what survey supports. Schematic plates carry the
poem's own spatial logic. Never mixed. Most Homeric topography has no
defensible coordinate, so the schematic register is how the fig tree, the ford
and the Scaean Gate get drawn at all.

## NEXT — in order

1. **Wire the citadel tab's Homeric pins.** `MapsPage.svelte:216-221` builds
   `troadPlatePlaces` and maps only `{id, name, coords, certainty}` — it drops
   `plateAnchors` and `positionBasis`, so every schematic-plate pin resolves to
   undefined. Also the citadel records are tagged `maps: ["troad-plain"]`, not
   `"troad"`, so they are not in that set. Fix both: add the two fields to the
   mapped object, and pass a set filtered per plate.
   **The citadel plate currently renders with no Homeric pins because of this.**
2. **Chart Room per-scene plates.** `Reader.svelte`'s `currentPlateMap` block
   (~798) still calls `renderSceneMap`. Give it an Iliad branch that renders the
   plain plate plus `computeCamera({ places })`, applied as a CSS transform on a
   `<g>` wrapper, gated on `prefers-reduced-motion`. Camera and the plural
   resolution are both already in place.
3. **The 24-book sweep.** Author `places: [id]` onto ~700 Iliad scenes in
   `apparatus/staging/scenes-iliad-*.json`, batches of ~5 books. Then
   `apparatus --work iliad` AND `--work odyssey` (emit shape), 48/48 scenes
   check, preflight. **The drafting agent never signs off its own book.**
   This is what actually retires the one-pin problem.

## Known, deliberately not fixed

- `wallGlyph` picks its tick side from an open polyline's signed area against
  the pixel origin, so on short arcs around an off-origin centre the ticks land
  outside on some circuit stretches and inside on others. Cosmetic.
- Natural Earth's vendored coastline is too coarse here — 3 vertices inside the
  plain bbox, Tenedos absent, Cape Lekton ~4 km out of place. Coasts were
  hand-generalized. `ne_10m` would fix it if fidelity ever matters.
- Form lines are data-only: `plate.ts` parses `shading` but `renderLayer` never
  reads it, so an inferred ridge draws identically to a surveyed one. Two Troad
  layers declare `shading: "form-lines"` and say in their notes that the
  renderer does not yet honour it.

## Open for John

- All plates and new records are `status: "draft"`. The draft → reviewed flip is
  John's alone.
- The Scaean Gate placement on the citadel plate is **the plate's own reading**,
  stated as reversible in its note: Scaean at the West Gate VI U, Dardanian at
  the South Gate VI T, chosen to keep the poem's two named gates distinct. A
  contested identification, so John's call.
- Three things a library visit would settle, recorded in
  `docs/TROAD-CARTOGRAPHY.md` under "Unverified — do not claim publicly": what
  Janko's single map in Cambridge vol. IV depicts, whether Luce 1998 charts the
  fighting scene by scene, and what is in Mey's *Das Schlachtfeld vor Troja*
  (1926) — a PD monograph on exactly this subject that appears never to have
  been scanned.
- Pope's 1716 plate (PD, 2837×3519) is the acknowledged ancestor of the
  schematic register and is not yet on the site. An "About these maps" page
  showing it, with its legend transcribed and its `lib. 22` slip footnoted,
  would credit the tradition we are resuming.
