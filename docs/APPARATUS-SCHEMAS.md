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
`width`, `shading`, `rows`, `count`, `fill` (`region`/`band` only, see
below), and the coordinate-geometry fields `rings` (a list of rings, each a
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

`region`/`band` layers fill with `--plate-tint` by default (a translucent
area tint). A layer may instead declare `fill: "sea"` to pick up the site's
water colour (`--scene-map-sea`) for a body of water on a schematic plate
(e.g. the Hellespont on the Trojan-plain schematic) — resolved through a
closed whitelist in `shared/lib/plate.ts` (`tint | sea`), never a
pass-through of the JSON value, so a plate file can never inject arbitrary
CSS into the emitted SVG.

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
