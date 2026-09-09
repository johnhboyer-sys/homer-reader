# Troy & Troad maps — handoff to the research-led session (2026-07-29)

Supersedes the planning parts of `TROY-MAPS-HANDOFF.md`. That file's source
tables and licence decisions still stand; its "Built and verified" section is
now known to be **misleading**, because every gate it lists was green while the
output was defective. See "Why the gates lied" below.

John's decision, 2026-07-29: **a dedicated session, driven by per-task research
dossiers.** Only the plain and the Troad stay in PR #16. Everything else —
citadel, Shield, plain-schematic, and the whole Chart Room plate path — comes
out and gets rebuilt research-first. "This needs to be a scholar accurate
presentation."

---

## 1. First task: shrink PR #16

PR #16 is DRAFT and stays draft. Take out of it:

| Surface | Mechanism (small, reviewable, reversible — do NOT unpick 40 commits) |
|---|---|
| `/maps/` citadel tab | remove the tab entry in `app/src/components/MapsPage.svelte:93` + its panel block |
| `/maps/` shield tab | same |
| plain-schematic | not currently surfaced on a tab; leave the JSON, ensure nothing loads it |
| Chart Room plate path | force `useIliadPlate = false` (`shared/components/Reader.svelte:874`) so every scene falls back to the pre-existing `renderSceneMap` box |

Keep the JSON, the renderer, the validators and the tests in tree — they are
the foundation the next session builds on. Only the *reader-facing surfaces*
come out. After the change: `npx vitest run` in `shared/` and `app/`,
`npm run build` (expect 4705 pages), preflight 0 errors.

**Do not delete `apparatus/places.json`'s 38 coordless records.** They are the
input to the anchor work in §4.

---

## 2. Why the gates lied (read before trusting any test in this repo)

893 tests, preflight clean, 4705 pages, five plates validating — all green,
all simultaneously true, while:

- the Shield rendered as a **rainbow** (every colour a well-formed `var()`
  whose token was genuinely defined — the test asks whether tokens exist, not
  whether the palette is right);
- the relief contours were **decimated 4–7× then smoothed**, so they read as
  terrain at thumbnail size and as amoebas at 6×;
- **42 Chart Room scenes printed a place name and a certainty badge over a map
  of somewhere else**;
- 28 debug checkboxes named after internal layer ids shipped as reader UI.

**The required gate, from CLAUDE.md (2026-07-28): for anything whose output is
an image, rendering it and LOOKING is a gate, and the agent that made it must
look before reporting done.** These plates predate that rule. Every defect
below was found by looking, none by a test.

### The harness for looking (works, reuse it)

Playwright-MCP screenshots land in a sandbox the orchestrator cannot read back.
What works:

```
# bundle the real TS, no fixtures
cd shared && ./node_modules/.bin/esbuild lib/plate.ts --bundle --format=esm \
  --platform=node --outfile=$SC/plate-fresh.mjs
# render from the real apparatus JSON + real global.css, both themes, then
CH=~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell
"$CH" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=W,H --screenshot=out.png "file://$PWD/page.html"
```

Scripts from this session (copy them into the repo if the next session wants
them permanently): `render-all.mjs` (all five plates, both themes),
`crop.mjs` (lat/lon window at N× zoom — **judge linework on 3.5×+ crops, never
thumbnails**), `chartroom.mjs`, `chartsweep.mjs`. They are in this session's
scratchpad; ask John or re-derive from the recipe above.

`astro dev` binds to **4322** here (siblings hold 4321) — read the port from
the log, never assume.

---

## 3. Defect ledger — measured, not estimated

### 3.1 Relief contours: decimated then smoothed (THE cause of "janky")

Median distance between adjacent vertices, in plate pixels, same sheet:

| layer group | median | p90 |
|---|---|---|
| coastlines (`coast-asia`, `coast-chersonese`, `coast-modern`) | **1.5–2.9 px** | 3.8–7.7 |
| relief contours, Troad (`relief-band-*`, named landforms) | **8.2–11.3 px** | 14–23 |
| relief contours, plain | **15–21 px** | 26–42 |
| `shore-bronze` (reconstructed) | **32.8 px** | 66 |
| `barrier-bronze` (reconstructed) | **22.4 px** | 48 |

The coasts were cut at the DEM's native posting; the contours were decimated
four to seven times coarser **and then smoothed**. At 9–17 px spacing the
smoothing spline has nothing to follow, so it invents: rounded lobes where it
overshoots, cusps where it doesn't. Fix: re-cut at the coastline's tolerance
and stop smoothing. Geometry carries the shape; the spline must not guess it.

Also degenerate: `relief-band-0100` on the plain is **9 segments**;
`relief-band-0320` is 9. Those are not contours.

Named landforms (`relief-ida`, `relief-chersonese` at 29 vertices,
`relief-samothrace` at 14, `relief-troad-west-highland` at 24) are cut at a
*different* generalisation from the residual bands they interlock with, which
produces sliver artefacts along their shared boundaries (band rings as small as
5 vertices). Decide: one tolerance for everything, or drop the named polygons
as geometry and keep those layers only for their prose and citations.

### 3.2 Text-on-path is garbled

River and road labels render reversed and letter-collided where the path runs
right-to-left: `Cae u ẏve`, `A ερμύ er`, `anla sri ver` on the Troad; an
upside-down `Wagon-road` on the schematic; a clipped vertical `…of Troy` on the
citadel. Fix: flip the path (or use `side="left"`) when its net direction is
leftward, and set spacing from measured glyph advance.

### 3.3 Label collisions

Unreadable heaps: the Dardanelles cluster (Abydos / Arisbe / Sestos / Dardania
/ Hellespont — labels cannot be matched to their pins); Troy / Wall of Troy /
Pergamos on the plain; and on the schematic, `SCAEAN & DARDANIAN GATES`
overprinting `GREAT TOWER OF ILIOS`, plus three camp labels on one line. There
is no label-placement pass at all — labels sit at a fixed offset from their
anchor. Needs real collision avoidance (candidate positions + a penalty
function), not hand-nudging.

### 3.4 The Chart Room asserts falsehoods

Swept all 412 Iliad scenes through the live code path. The reproduction was
verified against the browser's own transform to the decimal
(`scale 8, tx -3054.9, ty -2660.9`), so these numbers describe the real thing:

| | count |
|---|---|
| scenes total | 412 |
| **framed** (camera actually zooms) | **73** |
| **off-sheet only** — heading names a place hundreds of km away, map shows the Troad | **42** |
| unlocated only — whole plate, unzoomed, identical picture | **291** |
| no resolution | 6 |

Distinct place ids that ever drive the camera: **6** (`troy`, `wall-of-troy`,
`pergamos`, `callicolone`, `scamander`, `simoeis`).

Books framing **zero** scenes: 1, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 23 —
the entire middle of the poem.

The 42 off-sheet headings: `olympus` ×30, `ida` ×9, `chryse` ×2, `imbros` ×2,
`samothrace`, `tenedos`, `lemnos`, `lekton`. **Book 1's only two places are
Chryse and Olympus, both off-sheet**, so all 20 of its scenes draw the Trojan
plain with no relevant pin, under a heading reading e.g. "Olympus — CERTAIN".

Worse, the fallback caption (`Reader.svelte:2638`) reads *"This scene's named
places have no fixed position on this plate."* Olympus has a perfectly fixed
position; it is 350 km away in Thessaly. `renderPlate`'s `offCanvas` bucket
draws that distinction correctly and the caption collapses it into the
`unlocated` wording. **An off-sheet place must never render this plate at all** —
say where it is, or route to the `greece` map, which already exists.

Two more: plate labels magnify with the camera (at 8× "Wall of Troy" swallows
the 220×195 panel), and the legend/elevation-ramp/scale-bar sit **outside** the
camera group, so **the scale bar reads "20 stades / 5 km" at every zoom level**
— a map making a false quantitative claim. In a 220 px thumbnail the legend is
illegible clutter regardless; suppress it there.

### 3.5 Layer toggles are debug controls

`PlatePanel.svelte:155` — `togglableLayers = plate.layers.filter(l => l.default
=== 'on' || l.default === 'off')`, and every layer declares `default: "on"`, so
**all 28 become checkboxes** labelled by a mechanical id→text fallback: "Show
relief band 0050", "Show relief ida 800". The component's own comment admits
it: *"PlateLayer carries no display label … not authored copy."*

John, 2026-07-29: replace with a **certainty filter** — `certain /
traditional / speculative / mythical` — plus relief and rivers, and the
Bronze-Age/modern shoreline toggle that was actually designed.

### 3.6 Two plates claim authority they do not carry

```
troy-citadel            title: "The Citadel of Troy as the Spade Found It"   sources: 0
trojan-plain-schematic  title: "The Plain of Troy as the Iliad Lays It Out"  sources: 0
```

The citadel claims an excavation finding with **no sources at all** and no
survey geometry — concentric ellipse arcs, 45% of the sheet empty. The plan
required `sources` on plated *records*; nobody required them on the *plates*.
**Make `sources` mandatory on every plate in `validate_plate`.**

### 3.7 The Shield is a ring chart, not the Shield

Ten flat concentric bands in spectrum order — jewel tones in light, pastels in
dark. Recolouring will not fix it: Homer does not describe bands, he describes
**scenes** (wedding and lawsuit, besieged city and river ambush, ploughing,
the king's estate at harvest with a boy on the lyre, vineyard, lions taking a
bull, the dancing floor). It needs figuration. Metals are named at 18.474-75:
χρυσός, ἄργυρος, χαλκός, κασσίτερος, and κύανος for the dark inlay.

### 3.8 Gazetteer gaps

`uvecik-tepe` and `besik-bay` are `certainty: certain` with **no coords**.
Real surveyed sites — they need coordinates, not anchors.

---

### 3.9 Granular naming shipped; granular DRAWING did not — and the deployed site is older still

John, 2026-07-29: *"the point of the chart room updates was to have more
granular locations, like the achaean camp and battle sites, rather than having
most scenes simply be 'Troy'. Bloody unhelpful saying 'these are all at Troy'.
Yes, but WHERE at Troy?"*

Two separate things were tangled here; keep them apart.

**(a) `normalizeBookData` threw the whole sweep away. FIXED — commit `060022166`.**

`shared/lib/data.ts`'s `normalizeBookData` is the single normalizer both the
client fetch path and ReaderShell.astro's SSR path use to map the pipeline's
`apparatus.scenes` onto `Scene`. It copied five fields — summary, startLine,
endLine, place, day — and **not `places`**. `RawBookData` did not declare the
field either, so the compiler could not see the drop.

Consequence: `Scene.places` was `undefined` for all 412 Iliad scenes,
`scene-place.ts` fell through to the prose dictionary every time, and the site
showed exactly the one-pin behaviour the 24-book sweep existed to remove. Book
2's opening scene — Zeus sending the Dream to Agamemnon **in his hut** — read
"Troy (Ilios), certain". It now reads "The hut of Agamemnon, speculative".

Two corrections that follow from this, both of which were briefly asserted
wrongly in conversation and must not be repeated:

- **It was never a stale-deploy problem.** The bug reproduced on `localhost`
  with correct data being served. (The deployed `gh-pages` copy separately has
  `places: null` because it predates the sweep, which is a red herring.)
- **The §3.4 sweep numbers describe the DATA, not what the site was showing.**
  That sweep read `book.apparatus.scenes` directly and so bypassed the broken
  normalizer. What a reader actually saw before `060022166` was worse than
  73 framed / 42 off-sheet / 291 unlocated. **Re-run the sweep through
  `normalizeBookData` before quoting any of those figures.**

Lesson for the next session: every existing `normalizeBookData` test asserted
only the five fields that were already copied, so the suite was green and blind.
The new test names the field and fails on the old mapping.

**(b) On the branch, the naming is granular and the drawing is not.**

`achaean-assembly-place` is coordless, so it is one of the 291: the heading
becomes accurate while the picture stays the whole five-kilometre plain with a
pin on Troy. The reader gets a correct name and no position.

**This is why §4 is the centre of the next session, not a refinement of it.**
It is the only thing that converts 291 correct-but-useless headings into
positions a reader can see. Naming without drawing does not answer "where at
Troy".

### 3.10 The drawn plates need their own zoom

John, 2026-07-29: *"the troad and plain drawings look good, BUT they should be
zoomable rather than me having to zoom in on the whole page."*

Correct, and it is the natural consequence of the plates now carrying real
detail — ~1,900 and ~4,200 vertices is more than a fixed 840 px sheet can show.
Needs in-panel pan/zoom on the SVG (wheel + drag + `+`/`−` + keyboard, with a
reset), applied as a transform on a camera `<g>` — the mechanism
`applyPlateCamera` already uses in the Chart Room, so the renderer does not
change. Two things must be handled or the zoom makes the map worse:

- **The scale bar must track the zoom** (it currently does not — §3.4).
- **Labels must not magnify with the camera.** Counter-scale them, or better,
  switch to zoom-dependent labelling (more names as you go in).

### 3.11 The Tiles view goes blank at zoom — CAWM drops the burst

At z8 over the Troad, **11 of 12 tile requests fail in-browser with
`net::ERR_ABORTED`** while the identical URLs return HTTP 200 over `curl`:

```
z6   12/12 OK
z7   12/13 OK
z8    1/12 OK   <- 11 aborted
```

The tiles exist (a z8 tile is a real 59 KB PNG with coastline, islands and
relief). Tiles per view quadruples each zoom step, CAWM stops serving the
burst, and Leaflet never retries — so the fallback "ground" colour fills the
panel, which is what looks like a broken map.

`LandmarkMap.svelte` sets map `maxZoom: 8` (:1280) and tile-layer `maxZoom: 12`
(:1325) — inconsistent, and neither sets `maxNativeZoom`. Fix: **`maxNativeZoom:
7`**, so Leaflet upscales tiles it already holds instead of firing a batch that
gets dropped. Consider an `errorTileUrl` too.

### 3.12 "More locations in the drawn map than in the tiles" — two renderers, one gazetteer

28 places are tagged `troad`; **18 have coordinates, 10 do not**. The Tiles view
pins only points, so it lists those 10 under **"Not locatable"** — while the
drawn plate *draws three of them* as river layers and reports them honestly as
"Drawn as part of the map":

| id | kind | tier | on the drawn sheet? |
|---|---|---|---|
| satnioeis, aisepos, granikos | river | traditional / certain / traditional | **drawn as `river-*` layers** |
| rhodios, rhesos-heptaporos-karesos | river | speculative | not drawn |
| gargaron | mountain | traditional | not drawn |
| cilla, thebe-hypoplacia, pedasus-troad | settlement | speculative / traditional / speculative | not drawn |
| adramyttion | settlement | **certain** | not drawn |

So the same gazetteer gives two different answers about what is on the map, and
the Tiles view's wording is **false** for the three rivers it can see drawn on
the other tab. Beyond that, the drawn plate carries ~45 features (terrain,
coasts, rivers) that have no equivalent in the Tiles view at all, which is a
generic raster with pins on top.

Fixes: give `LandmarkMap` the same three-bucket honesty as `PlatePanel`
(`located` / `offCanvas` / `drawnByLayer`), and stop saying "Not locatable"
about a river with a known course. **`adramyttion` is `certain` with no
coords** — a third instance of the §3.8 gap, alongside `uvecik-tepe` and
`besik-bay`. Those three want coordinates, not anchors.

## 4. The anchor + tier-filter design (John's idea, 2026-07-29)

> "why not have best estimates in the map and have the option to select between
> Certain / Speculative / Traditional?"

The mechanism already exists and was under-used: **`plateAnchors` +
`positionBasis: "conjectural"`** — a position on the *sheet*, in unit
coordinates, never a lat/lon, never entering the gazetteer as `coords`. Both
validators reject either field without the other. Only **4 places** in the
whole gazetteer use it, all on the citadel.

Meanwhile 49 places are tagged `troad-plain` and **38 have no coordinate**:

| tier | n | ids |
|---|---|---|
| speculative | 29 | batieia, washing-troughs, scaean-gate, dardanian-gates, great-tower-of-ilios, oak-of-zeus, fig-tree, lookout-skopie, wagon-road, two-springs-of-scamander, tomb-of-ilos, tomb-of-aesyetes, scamander-simoeis-confluence, ford-of-the-scamander, achaean-camp, achaean-wall-and-ditch, achaean-assembly-place, hut-of-odysseus, hut-of-ajax, hut-of-achilles, hut-of-agamemnon, tomb-of-achilles-and-patroclus, tomb-of-hector, kesik-basin, hut-of-nestor, trojan-camp, thracian-camp, pyre-of-patroclus, funeral-games-ground |
| traditional | 4 | thymbra, troy-lower-city, tomb-of-ajax-in-tepe, thymbrios |
| certain | 4 | scamandrian-plain, bay-of-troy, uvecik-tepe, besik-bay |
| mythical | 1 | wall-of-heracles |

Anchoring these on the schematic sheet also **fixes the Chart Room**: every top
offender in the 291 unlocated scenes is on this list — `scamandrian-plain`
(125 scenes), `achaean-camp` (44), `hut-of-achilles` (33),
`achaean-wall-and-ditch` (27), `achaean-assembly-place` (23). Anchor them,
route the Chart Room to the schematic plate when a scene's places are
schematic-only, and ~280 scenes gain a real frame.

**Register discipline is absolute.** Anchors go on the *schematic* sheet only.
A conjectural anchor on the geographic sheet is the fabricated coordinate
CLAUDE.md forbids. Recommended defaults: schematic shows all four tiers (that
sheet exists to carry the poem's logic, and the `mythical` tier is a category,
not a warning); geographic defaults to certain + traditional and never accepts
an anchor at all.

---

## 5. The research dossiers

One document per task, so each subagent gets only what it needs and nothing it
must skim. **Copyright:** per CLAUDE.md, apparatus may draw on in-copyright
scholarship as a SOURCE — cited precisely, quoted briefly, never republished.
Site *translations* stay PD-only. That rule is unchanged; John reconfirmed
2026-07-29: "if we don't host it, we can still use it as a reference."

Every dossier carries, for each claim: the citation (Chicago for books and
articles; hyperlink for web resources and databases), **what kind of authority
it is — geometry vs identification vs prose**, and a `verified how` note. Plus
a closing **"Unverified — do not claim publicly"** section. That section is why
we never asserted what Janko's map depicts, and it stays mandatory.

| Dossier | Consumed by | Contents |
|---|---|---|
| `RESEARCH-BASEMAP-DATA.md` | contour re-cut, coastlines | DEM sources and licences (Copernicus GLO-30, SRTM via AWS terrain-tiles), AWMC ancient-world vectors, OSM/Overpass; extraction parameters; **target vertex spacing in plate px**; generalisation tolerance; the morphological-opening filter that removed tidal-reach artefacts (186 m / 90 m elliptical) and the proof the Dardanelles, Beşik Bay and the Gulfs of Gera and Kalloni survived it. **Geometry authority only — no identifications.** |
| `RESEARCH-PALEOGEOGRAPHY.md` | Bronze Age shore, bay, barrier, marsh | Kraft, Kayan and Erol (*Science* 209, 1980); Kraft, Rapp, Kayan and Luce (*Geology* 31, 2003); Kayan's Turkish survey work; Brückner; regional sea-level curves. The derivation that fixed the 10 m contour (passes 1.2 km N of Hisarlık; 8 m gives 2.8 km, 12 m gives 0.7 km, both outside the published range) and the one constraint that could **not** be confirmed (fill runs ~7.5 km S inside the sheet against a published 10 km). Luce's dissenting reconstruction (camp on the Sigeum ridge) must be stated, not buried. |
| `RESEARCH-TROAD-TOPOGRAPHY.md` (extend existing `TROAD-SOURCES.md`) | gazetteer, tiers, traditions | Cook, *The Troad* (1973); Leaf, *Troy* (1912); Luce, *Celebrating Homer's Landscapes* (1998); Strabo 13.1; Pleiades / AWMC ids; the 2020 hydrochemical survey finding **no hot-and-cold spring pair exists near Troy**. Every `traditional` tier must name its tradition. |
| `RESEARCH-CITADEL.md` | citadel plate rebuild | Dörpfeld 1902; Blegen, *Troy* I–IV; Korfmann, *Studia Troica*; Rose, *The Archaeology of Greek and Roman Troy* (2014). **Georeferenced or scaled site plans** — gates VI T / VI U / VI S, tower VI h, the ramp, the megara, the lower-city ditch. Without scaled geometry the citadel stays schematic and must be **retitled** so it stops claiming the spade. |
| `RESEARCH-POEM-TOPOGRAPHY.md` | schematic plate, the 38 anchors | Every Iliadic topographic passage catalogued with Greek: camp order 8.222-26 and 11.806-8; **14.31-32** (first-hauled ships furthest inland, wall at their sterns — the camp has depth, not merely length); wagon gate at the left 12.118-19; the fig tree at 11.166 *and* 22.145; Protesilaus's ship 13.681 vs 15.704-6 vs 16.286. Cambridge commentary (Kirk, Hainsworth, Janko, Edwards, Richardson); Trachsel; Clay, *Homer's Trojan Theater*. **Contradictions get recorded, never drawn over.** |
| `RESEARCH-SHIELD.md` | Shield redesign | Il. 18.478-608 with each `Ἐν δὲ` boundary verified; Edwards, *Iliad* Books 17-20 (Cambridge vol. V); Becker, *The Shield of Achilles and the Poetics of Ekphrasis*; Taplin; Hardie. The five metals of 18.474-75 and Bronze Age inlay technique (Mycenaean inlaid daggers, niello) as the visual register. **This is a figuration brief, not a palette brief.** |
| `TROAD-CARTOGRAPHY.md` (exists, 625 lines) | every drawing lane | Who has mapped this before; the PD vs in-copyright table; linework craft. Pope's 1716 plate (PD, 2837×3519) is the acknowledged ancestor of the schematic register. Keep its "Unverified" section current. |

Three library-visit items stay in `TROAD-CARTOGRAPHY.md` under "Unverified —
do not claim publicly": what Janko's single map in Cambridge vol. IV depicts,
whether Luce 1998 charts the fighting scene by scene, and what is in Mey's
*Das Schlachtfeld vor Troja* (1926) — a PD monograph on exactly this subject
that appears never to have been scanned.

### Dossier discipline

1. A dossier lane's output is **verified by a different model family** against
   the actual sources before any drawing lane consumes it. A hallucinated
   citation in a dossier propagates to every agent that trusts it — this is the
   highest-leverage place in the whole pipeline for a fabrication to do damage.
2. **Never mix authorities.** Scholarship settles identifications, tiers and
   prose. Geometry comes from DEM, AWMC, OSM, or a georeferenced published
   plan. The single worst failure of 2026-07-28 was treating a reading list as
   a substitute for vector data: *"it's just shapes. no geography at all."*
3. No silent caps. A dossier that samples rather than covers says so.

---

## 6. Still John's alone

- `draft → reviewed` on `apparatus/places.json` and every plate. Nothing is
  ready for this yet.
- The contested **Scaean / Dardanian** pairing (currently Scaean at West Gate
  VI U, Dardanian at South Gate VI T, stated as reversible in the layer note).
  **[SUPERSEDED, John, 2026-07-30 16:29, ruling 2e-ii — TROY-MAPS-TODO.md:
  the plate now carries Dörpfeld letters only, no Homeric gate name drawn;
  this pairing lives in the note only. This handoff's snapshot is kept as
  history, not current instruction.]**
- The Shield's visual register: literal metallics vs the site's terracotta
  family.
- Whether the citadel gets real survey geometry or an honest retitle.
- Deploys, money, domains, canon/scope.

## 7. What is genuinely good and must not be lost

The plain and the Troad are real maps: ~1,900 and ~4,200 vertices from
measured DEM data, hypsometric tinting cut from the terrain, a **derived**
Bronze Age shoreline (arithmetic on published measurements, working recorded in
the layer note so a reviewer can redo it), rivers painted beneath the water
they cross, and a barrier that ends where it stops being a barrier — cut at the
landfall from what a bar *is* (ground with water on both sides: lagoon width
381–1950 m across the delta, 123 m at the landfall, 7–44 m beyond).

Terrain was sanity-checked before anything was drawn: Kaz Dağı 1757.4 m
measured against 1774 published; Hisarlık 36.1 m against c.38; Sigeion crest
36.0 m against Cook's "thirty to forty".

Those two sheets need the contour re-cut and the label work. They do not need
rebuilding.
