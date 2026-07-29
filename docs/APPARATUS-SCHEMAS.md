# Apparatus data schemas (Phase 4) — defined BEFORE fan-out

All authored apparatus is AI-drafted with `"status": "draft"` until John flips
it. Drafting agents return DATA in these exact shapes; non-conforming output is
rejected and re-run, never hand-patched. The drafting agent for a book never
signs off on that book.

## scenes.json (per work: `apparatus/scenes/<work>.json`)

```json
{
  "work": "iliad",
  "status": "draft",
  "books": [
    {
      "book": 1,
      "argument": "<= 15 words, the book in one line>",
      "where": ["Troy", "the Achaean camp"],
      "who": ["Achilles", "Agamemnon", "Chryses", "Apollo"],
      "days": "1-21",
      "scenes": [
        {
          "lines": [1, 7],
          "summary": "<= 20 words, present tense, factual (Landmark register)",
          "location": "Achaean camp",
          "dayNumber": 1
        }
      ]
    }
  ]
}
```

Rules: `lines` are vulgate line numbers within the book, non-overlapping,
ascending, covering the whole book (gaps allowed only at the six known
vulgate gaps). `dayNumber` per the epic's internal calendar (Iliad: 1–51
tradition; Odyssey: story-day of the telling frame); use `null` where a day
is indeterminate (e.g. Olympian scenes outside time). Summaries: no
interpretation beyond the text, no spoiler-avoidance games, Landmark register
("Persia conquers Ionia and the islands.").

## places.json (single file `apparatus/places.json`)

```json
{
  "status": "draft",
  "places": [
    {
      "id": "ismarus",
      "name": "Ismarus",
      "greek": "Ἴσμαρος",
      "pleiades": "https://pleiades.stoa.org/places/501348",
      "certainty": "traditional",
      "tradition": "identified with Maroneia region, Thrace (ancient tradition; Strabo 7 fr.)",
      "coords": [40.65, 25.52],
      "maps": ["wanderings"],
      "mentions": [{"work": "odyssey", "book": 9, "lines": [39, 40]}],
      "note": "<= 40 words"
    }
  ]
}
```

`certainty`: `certain | traditional | speculative | mythical`. A `traditional`
or `speculative` identification MUST name its tradition/proponent in
`tradition`. `mythical` places get no `pleiades`/`coords` unless a traditional
localization exists (then keep certainty `mythical` and put the localization
in `tradition`). NEVER invent an identification. `maps`: which of
`ships | troad | wanderings | greece` panels show it.

A place record may also carry `plateAnchors` (an object mapping plate id to a
`[u, v]` unit pair in 0..1, for placing the feature on a schematic plate that
has no defensible lat/lon) and `positionBasis: "conjectural"` — the two are
required together, never one without the other; that pairing is the honesty
mechanism for a feature drawn without real-world coordinates. A place tagged
for a plate (its `maps` array carries an entry starting with `troad-plain` or
`troy-citadel`) additionally requires `kind` (see the plate schema below) and
at least one `sources` entry — the legacy (pre-plate) 280 records are exempt
from both.

## plates/\<id\>.json (per plate: `apparatus/plates/<id>.json`)

Illustrated, hand-drawn Landmark-style map plates (the Trojan plain, the
Troad, the Troy citadel, Achilles' shield). Plate *geometry* is authored here
in lat/lon (`kind: "geographic"`) or unit-space (`kind: "schematic"`) JSON,
validated by `pipeline/homer_pipeline/apparatus_places.py`'s `validate_plate`
(cross-checked against the gazetteer's `validate_places`) and shipped
verbatim to `build/dist/plates/<id>.json` by `scripts/build-public.mjs`.
Projecting this geometry into rendered SVG is a later phase, not this schema.

```json
{
  "id": "trojan-plain",
  "title": "The Trojan Plain",
  "kind": "geographic",
  "status": "draft",
  "seed": 20260728,
  "bbox": [39.86, 26.12, 40.02, 26.36],
  "size": [880, 620],
  "layers": [
    {
      "id": "coast-bronze",
      "kind": "coast",
      "style": "stipple",
      "default": "on",
      "rings": [[[39.98, 26.18], [39.97, 26.19]]],
      "note": "Reconstructed c.1200 BC shoreline; provisional pending the cartography phase.",
      "sources": [
        {"cite": "Kraft, John C., Ilhan Kayan, and Oğuz Erol. \"Geomorphic Reconstructions in the Environs of Ancient Troy.\" Science 209 (1980): 776-82."}
      ]
    },
    {
      "id": "scamander",
      "kind": "river",
      "placeId": "scamander",
      "path": [[39.90, 26.15], [39.95, 26.20]],
      "width": 2.2
    }
  ]
}
```

`kind` (plate-level): `geographic` (layers use real `[lat, lon]` pairs,
contained in `bbox`) | `schematic` (unit `[u, v]` pairs in 0..1, no geography).

A **geographic** plate must carry `bbox` and `layers`: it is drawn by
projecting lat/lon through `shared/lib/geo.ts`, so it has to declare the extent
it projects into.

A **schematic** plate carries neither — demanding a `bbox` of it would be
demanding a coordinate for something that has none. It must declare at least
one of:
- `bands` — concentric rings, used by `shield-of-achilles.json`, each
  `{id, title, greek, lines: [from, to], summary, ring}`. Band ids are unique.
- `layers` — the same layer shapes as a geographic plate, but with unit `[u, v]`
  coordinates. This is how the Trojan plain is drawn *as the poem lays it out*
  (the camp order of Il. 8.222-26, the road and its waypoints) rather than as
  survey knows it. See CLAUDE.md's two-register rule.

`bbox`: `[minLat, minLon, maxLat, maxLon]`. `size`: `[widthPx, heightPx]`.
`seed`: required whenever any layer uses a stochastic draw style (`stipple`,
`hachure`) — determinism for the render phase.

Layer `kind`: `coast | river | relief | shipRow | wall | route | region |
band | tumulus`. Optional per layer: `placeId` (must resolve in the
gazetteer), `note`, `sources` (same cite/url shape as places.json, Chicago
citation rule), `default` (`"on" | "off"` for a toggleable layer), `style`,
`width`, `shading`, `rows`, `count`, `fill` (`region`/`band`/`coast`, see
below), `elevation` (`relief`, see below),
`label` (see below), and the coordinate-geometry fields `rings` (a list of rings, each a
list of pairs), `path`, `polygon`, `baseline`, `trace` (each a flat list of
pairs). Apparatus honesty: geometry not yet sourced from real cartography
must say so in `note` rather than presenting placeholder points as surveyed.

`tumulus` draws a burial-mound glyph (a dome profile with nested shading
arcs, e.g. the tombs of Ilos and Batieia) at one point per entry in its
`path` field — reusing that existing flat coordinate field rather than
inventing a new one, so it needs no separate geometry-field wiring on
either side of the schema. **Not yet in the pipeline's `LAYER_KIND_ENUM`**
(`pipeline/homer_pipeline/apparatus_places.py`) — a plate JSON file using
`kind: "tumulus"` will fail `validate_plate` until that enum is updated to
match.

### Relief: hypsometric bands vs hachures (`elevation`)

A `relief` layer draws in one of two registers, and the field that chooses
between them is `elevation` — the contour level in metres above sea level the
body was cut at (a number ≥ 0; sea level itself is legal).

- **With `elevation`** — the **hypsometric** register, for relief cut from a
  DEM. The layer is filled from a twelve-step graduated ramp
  (`--plate-relief-1` … `--plate-relief-12`) and edged with a hairline
  (`--plate-contour`). Nothing is hachured. The step a band gets is its RANK
  among the distinct elevations on the SAME plate: the lowest takes step 1,
  which is tuned to sit within about 1.05:1 of the sheet's own ground colour
  so the first band has no visible seam, and the highest takes step 12. The
  ramp is therefore keyed to each sheet's own relief range, as a physical
  map's always is — the same tint means 320 m on the Trojan plain and 1400 m
  on the Troad, and each sheet draws its own graduated key in the margin
  saying so. Such a layer may carry either one `polygon` (a named landform)
  or `rings` (several disjoint bodies at one level sharing one layer, so a
  sheet does not need sixty layers with sixty notes). Bands must be listed in
  ASCENDING elevation: that is the paint order, and a higher band lies inside
  a lower one.
- **Without `elevation`** — the **hachure** register, for relief authored by
  hand (`trojan-plain-schematic.json`, `troy-citadel.json`). One `polygon`,
  filled `--plate-upland`, hachured in `--flaxman-hachure` at a density read
  out of how the plate's relief polygons nest.

The division is the historical one: hachuring was the SUBSTITUTE for
hypsometric tinting where no elevation data existed. Where there is a DEM
(`scripts/prep-terrain-contours.py`), use the ramp. The `shading:
"form-lines"` value is retired on the two contoured sheets for the same
reason — it claimed the extent was sketched, and it is contoured.

### Land and water (the `ground` + `fill` contract)

**The renderer never guesses which shape is water.** A plate says so, in two
fields, and a plate that says neither draws land-coloured shapes on a
land-coloured sheet — which is exactly the "it's just shapes, no geography"
defect of 2026-07-28.

`ground` (plate level, optional, `"land" | "sea"`, default `"land"`): what the
bare sheet is under every layer.

- **Mostly-dry extent** (the Trojan plain): leave the default, and draw each
  body of water as a `region` layer with `fill: "sea"` or `fill: "lagoon"`.
- **Coastal/marine extent** (the Troad): declare `"ground": "sea"`, and give
  each `coast` layer whose rings are CLOSED landmasses `"fill": "land"`. The
  rings are then filled `evenodd` under the shoreline — the same construction
  `shared/lib/scenemap.ts` uses for the Mediterranean coastline. **The rings
  must actually close**, or the fill leaks across the sheet.

`fill` (layer level, optional) names the TERRAIN a `region`/`band` layer is, or
the terrain a `coast` layer's rings enclose. Closed whitelist in
`shared/lib/plate.ts` — never a pass-through of the JSON value, so a plate file
can never inject arbitrary CSS into the emitted SVG:

| `fill` | token | role |
|---|---|---|
| `plain` (**default**) | `--plate-plain` | dry usable ground |
| `marsh` | `--plate-marsh` | wetland, wet delta |
| `lagoon` | `--plate-lagoon` | shallow/silting water |
| `sea` | `--scene-map-sea` | open water |
| `land` | `--scene-map-land` | landmass on a `ground: "sea"` plate |
| `tint` | `--plate-tint` | translucent **apparatus zone** (e.g. "the Achaean camp") |

The default **changed 2026-07-28** from `tint` to `plain`. `--plate-tint`
resolves to `var(--accent-light)`, the site's wine wayfinding accent, so every
undeclared landform was painted in the UI highlight colour. A landform is not a
highlight: terrain is the default and the accent wash is opt-in.

**The pipeline validator mirrors this table exactly.**
`pipeline/homer_pipeline/apparatus_places.py` carries `REGION_FILL_ENUM` (all
seven roles) and `GROUND_ENUM`, checked in `validate_plate`. The two
implementations of this schema have drifted more than once: if a fill role or
a ground value is ever added on one side, it is added on the other in the same
change, or `build:public` rejects a plate the renderer draws perfectly well.

#### Rivers, and where they stop

**A river is painted BENEATH any water it crosses.** No field configures this
and none should: it is a property of the drawing, not a claim in the data, so
there is nothing to author, nothing to forget on the next river, and nothing
for the two implementations of this schema to drift on. The renderer splits a
`river` layer at the edge of every water body on the sheet (`fill: "sea"` /
`"lagoon"`, plus the whole sheet when `ground: "sea"`) and hands each submerged
reach to that water layer's own paint slot, immediately under its fill.

Why it matters: our rivers are modern OSM watercourses, and their lower reaches
cross ground that was under water in 1200 BC. Drawn over the reconstructed
lagoon they asserted a Bronze Age river exactly where the plate's own evidence
says there was sea.

Three consequences worth knowing when authoring a sheet:

- **Nothing is cut from the data.** The union of what is drawn is still exactly
  the surveyed course; only the paint order changes. A river's mouth is
  therefore a function of *which shoreline you are drawing* — switch the
  reconstructed lagoon off and the water that was hiding the reach goes with
  it, so the river runs on to the modern mouth. The clip follows the layer
  toggles for free, because the water itself is what hides the reach.
- **A water fill must stay opaque** (`sea`, `lagoon` — see the opacity table in
  `shared/lib/plate.ts`). A translucent water body would leak the drowned river
  back through it.
- **`marsh` is not water for this purpose.** A channel through a wetland is a
  channel; the Scamander crossing the delta swamp draws over it, as it should.
  A reach drowned by a `ground: "sea"` sheet is simply not drawn — the ground
  is the bottom of the paint stack, and it carries no toggle.

If a river's drawn end is now somewhere its `note` did not anticipate, **fix the
note**: `simoeis` on the plain sheet stops at two different places (the Bronze
Age shore with the reconstruction on, the end of the OSM survey with it off),
and its note says both, because "the survey stops here" and "the water began
here" are different claims and neither may be allowed to impersonate the other.

### Lettering

`label` (layer level, optional): the name to letter onto the sheet for this
feature. When absent, the renderer falls back to the gazetteer name of
`placeId` — and only when that place is not itself pinned on this plate, so a
feature is lettered once, not twice. Author `label` whenever the gazetteer name
is a catalogue entry rather than a map label: "Kesik Tepe (the 'Demetrius
tumulus'), claimed tomb of Achilles" is the former. (Gazetteer-derived names are
shortened to their head form automatically; the full name still rides on the
pin's `<title>`.)

**Pins carry the certainty tier as an inner mark, never as a hole** (changed
2026-07-29). A map symbol is never transparent to its own basemap: three of the
four tiers used to be drawn `fill: none` or as a 0.16 wash, so at 3.5x a pin
over the hypsometric ramp had contour lines running straight through the middle
of it. Every tier now has an opaque body — `--accent` for a location the
gazetteer stands behind, `--text-mid` for one it does not — and the tier is
carried by shape, in the sheet's own label-halo colour:

| `certainty` | symbol |
|---|---|
| `certain` | solid, no inner mark |
| `traditional` | solid + a closed inner ring |
| `speculative` | solid + a broken inner ring |
| `mythical` | solid + a broken outline |

A `positionBasis: "conjectural"` pin keeps its own dashed outline on top of
whichever tier it is. This is a deliberate divergence from `shared/lib/scenemap.ts`
and `LandmarkMap.svelte`, which draw small dots on flat insets and are unchanged.

Linear layers (`river`, `coast`, `wall`, `route`) are named ALONG their own run
with `<textPath>` when the run is long enough to carry the name; area layers
(`region`, `band`, `relief`) are named across their extent in letterspaced
caps. Neither needs any extra authoring — both come from `label`/`placeId`.

The renderer also draws a **double neatline**, a **bar scale** computed from the
plate's own viewport (stades over kilometres, geographic plates only), and a
**legend derived from what the sheet actually drew** — every register on the map
appears in the key, and every row in the key can be found on the map.

## characters.json (single file `apparatus/characters.json`)

```json
{
  "status": "draft",
  "characters": [
    {
      "id": "achilles",
      "name": "Achilles",
      "greek": "Ἀχιλλεύς",
      "epithets": ["swift-footed", "son of Peleus"],
      "role": "<= 12 words",
      "genealogy": {"tree": "aeacus", "father": "peleus", "mother": "thetis"},
      "note": "<= 60 words, draft",
      "dicesId": null
    }
  ]
}
```

Genealogy trees: `atreus | aeacus | troy | olympians`. `dicesId` filled by the
speech-span stage join, not by drafters.

Genealogy honesty (added after the 2026-07-17 Grok gate): a parent link not
attested in Homer may remain in the structured fields ONLY when the tree needs
it to connect, and must then be flagged: `"genealogy": {..., "nonHomeric":
["father"]}` with the source tradition named in `note`. The UI renders
flagged links visually distinct (dashed). Unflagged links assert Homeric
attestation. Figures never named in Homer get no entry unless a tree
structurally requires them (then the whole entry's note states the source).

## catalogue.json (single file `apparatus/catalogue.json` — Catalogue of Ships)

```json
{
  "status": "draft",
  "achaean": [
    {
      "id": "boeotians",
      "name": "Boeotians",
      "lines": [494, 510],
      "leaders": ["peneleos", "leitus"],
      "ships": 50,
      "places": ["hyria", "aulis"],
      "note": "<= 30 words"
    }
  ],
  "trojan": [
    { "id": "trojans", "name": "Trojans", "lines": [816, 818],
      "leaders": ["hector"], "ships": null, "places": ["troy"] }
  ]
}
```

`lines` are vulgate lines within Il. 2 (Achaean 494–759, Trojan 816–877),
non-overlapping, ascending. `ships` = the number Homer states (null for the
Trojan catalogue, which counts no ships). `leaders`/`places` are kebab-case
ids; leaders SHOULD resolve to characters.json when the figure is there,
else remain plain strings (catalogue-only leaders are NOT added to
characters.json). `places` entries MUST exist in places.json (the ships-map
entries added by the same lane). Ship counts are data: verify each against
the Greek line that states it.

## speeches.json (per work, from DICES: `apparatus/speeches/<work>.json`)

Computed from sources/dices/speechdb.json (CC-BY 4.0), not authored:
`{work, status: "imported", speeches: [{id, book, lines: [fi, la], speaker:
[charId], addressee: [charId], level, cluster, part, type}]}`. Spans crossing
book boundaries are flagged `crossBook: true`, never split silently. Nesting
`level >= 1` renders flagged (Apologoi rule); coloring only for
high-confidence spans (level 0 and clean level 1).

## Pope scene anchors (per work: `sources/pope/scene-anchors-<work>.json`)

Not apparatus data proper — this is the curated dataset the `third` (Pope)
translation overlay resolves against so its scene ticks land on Pope's actual
verse rather than a book-level or proportional guess. Loaded and
schema-checked by `load_scene_anchor_dataset` in
`pipeline/homer_pipeline/stage1_pope.py`; a missing file is a hard stage1
error once a work declares a Pope `third` slot.

```json
{
  "_source": "<provenance note>",
  "_semantics": "<one-paragraph explanation, see below>",
  "work": "iliad",
  "anchors": [
    {
      "book": 1,
      "n": 8,
      "anchor": "For Chryses sought with costly gifts to gain",
      "status": "verified",
      "note": "<drafting/verification rationale>"
    }
  ]
}
```

`status`: `verified | draft | unanchored`. `anchor` is a verbatim substring of
that book's emitted Pope verse text for `verified`/`draft` entries and MUST be
`null` for `unanchored` (no tick emitted; not a build failure). `n` is the
scene's first Greek vulgate line, matched against the staged scene starts from
`apparatus/scenes/<work>.json` — every scene start except each book's first
(which gets an automatic offset-0 tick) needs exactly one anchor entry.
`anchor` must occur **exactly once** in the book's Pope text and begin at a
verse-line start (offset 0, or immediately preceded by `\n`); stage1 hard-fails
on zero/multiple occurrences, a mid-line start, or non-increasing resolved
offsets — a scene dataset that disagrees with Pope's actual text is a data bug
to fix, not something to degrade around.

**Verification provenance (2026-07-21):** all 742 entries (388 Iliad + 354
Odyssey) were AI-drafted per book, then adversarially verified by a second
model against each scene's Murray-derived opening (`murrayOpening` in the
drafting packet). 19 entries failed first-pass verification and were
redrafted; a recheck pass re-verified all 19 (17 correct outright). The
remaining 2 (Odyssey 11 n=628, Odyssey 16 n=266) needed a senior adjudication
pass after failing recheck too — their `note` starts with `"Opus
adjudication:"`. Every entry in the shipped dataset carries `status:
"verified"`. Full corrected-entry list: `docs/POPE-ANCHOR-REVIEW.md`.

**Maintenance coupling:** this dataset's `n` values are load-bearing against
`apparatus/scenes/<work>.json`'s scene starts (via `resolve_scene_anchors` in
`stage1_pope.py`). Any future scene-boundary edit — including entries in
`shared/lib/scene-boundary-overrides.json` that shift a scene's *first* line —
changes the staged n-set stage1 checks the anchor dataset against, and stage1
will hard-fail loudly (not silently degrade) until this dataset is updated to
match. Treat a scene-boundary edit and its corresponding anchor-dataset update
as one change.

## Computed stages (4d — no authoring)

- epithets: `build/dist/<work>/epithets.json` — per named entity:
  `{entity, formulas: [{text, lemmaKeys, count, refs: [{book, line}]}]}`.
- repetitions: `build/dist/repetitions.json` — exact repeated lines + 4-word+
  n-grams occurring >= 2x, cross-epic: `{key, text, count, refs}`.
Maximal-n-gram rule (both stages, explosion control): a shorter candidate is
dropped only when a strictly longer *accepted* candidate contains it as a
contiguous sub-sequence AND has the identical ref set; a shorter candidate
with a broader/different ref set is kept independently.
Both deterministic, pipeline-tested (fixture + determinism test re-run twice,
byte-identical output).

## The phrase index, and how it differs from repetitions and epithets

Stage 8 (`stage8_ngrams.py`) emits a third index over recurring word
sequences: `build/dist/ngrams/` (form 68,550 phrases, lemma 158,973,
English 118,695 — 34 MB total) plus `build/dist/lemma-map/` (764 KB),
which widens a typed surface form to the headwords it can belong to. This
is not a replacement for repetitions or epithets; it answers a different
question. Repetitions and epithets are philological claims: exact surface
text or lemma sequence, matched within one line only, pruned by the
maximal-n-gram rule, so each entry is a scholarly assertion about a
specific recurring phrase. The phrase index is a search tool: it folds
away accent and case, matches across all three streams (Greek form,
lemma, and English), crosses line ends unless the reader turns that off,
and keeps anything occurring twice or more anywhere in the corpus. Nothing
in repetitions or epithets is derived from it, and nothing in it is
folded back into them — keeping the three separate keeps the published
philological claims exact while still letting a reader search loosely.
The phrase index also deliberately keeps phrases that straddle a verse
end, because the within-one-verse filter is a query-time toggle, not a
build-time cut; Homeric formula is mostly a within-line phenomenon, which
is the reason that toggle exists at all.
