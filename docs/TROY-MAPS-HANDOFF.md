# Troy & Troad maps — complete, 2026-07-28

Shipped as PR #16. This file is the map of the work; the PR body is the summary.

All three "NEXT" steps below are DONE. Kept for the file map, the
deliberate limitations, and what still needs John.

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
| Gazetteer | `apparatus/places.json` — 280 → **330** records, status `draft` |
| Plates | `apparatus/plates/` — `trojan-plain`, `troad`, `trojan-plain-schematic`, `troy-citadel`, `shield-of-achilles` |
| Page surface | `app/src/components/maps/PlatePanel.svelte`, `MapsPage.svelte` |
| Scene plumbing | `places: string[]` on scenes; `scene-place.ts` precedence |
| Scene annotation | 406/412 Iliad scenes, **42 distinct place ids** (was 1) |
| Chart Room | `Reader.svelte` — plate once per book, camera per scene |
| Source dossiers | `docs/TROAD-SOURCES.md`, `docs/TROAD-CARTOGRAPHY.md` |

Green: **893** tests in `shared/`, 8 in `app/`, 499 in pipeline, preflight 0
errors, 48/48 books carry scenes, 4705 pages build. The one red pytest is the
pre-existing χάω test.

## The two registers (CLAUDE.md rule, John's call)

Geographic plates carry only what survey supports. Schematic plates carry the
poem's own spatial logic. Never mixed. Most Homeric topography has no
defensible coordinate, so the schematic register is how the fig tree, the ford
and the Scaean Gate get drawn at all.

## Done (was "NEXT")

1. ~~Wire the citadel tab's Homeric pins~~ — done. Four conjectural pins render,
   each carrying `data-position-basis="conjectural"`; the eight citadel records
   are split between pinned and drawn-by-layer, and "named, not drawn" is empty.
2. ~~Chart Room per-scene plates~~ — done. The plain plate renders once per book;
   per-scene framing is a CSS transform on a `<g>` wrapper, proved not to
   re-render by asserting SVG node identity across paging.
3. ~~The 24-book sweep~~ — done. **406 of 412 Iliad scenes, 42 distinct place
   ids** (was 1). Verified by a Grok content gate against the Greek; six
   confirmed defects fixed, including four consecutive Book 7 scenes wrongly
   tagged with the camp assembly-place.

Also closed: the five missing camp places (`hut-of-nestor`, `trojan-camp`,
`thracian-camp`, `pyre-of-patroclus`, `funeral-games-ground`) that the sweep
lanes reported rather than invented around.


## Known, deliberately not fixed

(The "drawn as a layer is listed not-drawn" defect recorded here earlier was
FIXED: `renderPlate` now has a `drawnByLayer` bucket and `PlatePanel` lists it
as "Drawn as part of the map".)

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
