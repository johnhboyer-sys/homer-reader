# RESEARCH-BASEMAP-DATA.md — geometry authority for the Troad/plain contour re-cut

**Scope discipline.** This dossier carries **geometry authority only** —
sources, licences, extraction parameters, and the re-cut spec for the two
plates' coastlines and relief. It makes **no place identifications and no
claims about what a place is** (that is `RESEARCH-TROAD-TOPOGRAPHY.md` and
`RESEARCH-POEM-TOPOGRAPHY.md`'s territory). It does not touch the Bronze Age
shore/barrier/lagoon/marsh geometry — that is derived from published
measurements, not the modern DEM, and is `RESEARCH-PALEOGEOGRAPHY.md`'s
territory (`sources/terrain-tiles/README.md:104-111`; script comment at
`scripts/prep-terrain-contours.py:654-655`, "The Bronze Age geometry is
deliberately NOT taken from the post-blurred grid … it was derived against
published measurements and must not move").

Consumed by: the contour re-cut lane, any future coastline work.

Output schema per claim: **claim — citation — authority kind: geometry
(source | licence | parameter | spec) — verified how.**

---

## 0. What already exists (read this before re-deriving anything)

The two plates in scope (`apparatus/plates/troad.json`,
`apparatus/plates/trojan-plain.json`) already have real vendored source
pipelines, each with its own README. **They are not what §3.1 of the handoff
complains about was hand-authored — the defect is a parameter choice inside
an already-correct pipeline**, not a missing one.

| Directory | What it produces | Script |
|---|---|---|
| `sources/copernicus-dem/` | coastlines + islands (`coast-*` layers) | `scripts/prep-troad-basemap.py` |
| `sources/openstreetmap/` | river courses (`scamander`, `simoeis`, etc.) | `scripts/prep-troad-basemap.py` |
| `sources/terrain-tiles/` | relief contours (`relief-band-*`, named landforms) | `scripts/prep-terrain-contours.py` |
| `sources/naturalearth/` | Mediterranean coastline for the small scene-panel maps — **not** the Troad/plain plates | `scripts/prep-naturalearth-coastline.py` |

- Claim: the coastline and relief pipelines are separate scripts with
  separate, independently-chosen generalisation tolerances, which is the
  root cause of §1's mismatch.
- Citation: `scripts/prep-troad-basemap.py` (coast/rivers) vs.
  `scripts/prep-terrain-contours.py` (relief), confirmed by grep — no shared
  tolerance constant between the two files.
- Authority kind: geometry / source.
- Verified how: read both scripts' top-level constants (`PLAIN_TOL`/
  `TROAD_TOL` at `scripts/prep-troad-basemap.py:129-130` vs. `SHEETS[...]
  ["tol_deg"]` at `scripts/prep-terrain-contours.py:664,675`).

---

## 1. Data sources and licences

### 1.1 Coastlines and islands — Copernicus DEM GLO-30 Water Body Mask

- Claim: the coastline/island layers on both plates (`coast-asia`,
  `coast-chersonese`, `coast-islands`, `coast-tenedos`, `coast-modern`,
  `sea-modern`) are contoured from the **Water Body Mask** auxiliary raster
  shipped with each Copernicus DEM GLO-30 tile — class `1 = ocean`, boundary
  traced by marching squares, 30 m posting. **Not AWMC, not Natural Earth,
  not OSM** — those were considered and rejected (see §1.4).
- Citation: `sources/copernicus-dem/README.md:1-7`; fetch pattern
  `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_<TILE>_DEM/AUXFILES/Copernicus_DSM_COG_10_<TILE>_WBM.tif`,
  tiles `N38_00_E025_00` … `N40_00_E027_00` (nine 1° tiles), fetched
  2026-07-28, no credentials, [AWS Open Data
  registry](https://registry.opendata.aws/copernicus-dem/).
- Authority kind: geometry / source.
- Verified how: read the README; independently confirmed the registry page
  exists and states GLO-30 is free for the general public (WebFetch,
  `https://registry.opendata.aws/copernicus-dem/`, 2026-07-29).

**Resolution:** 30 m (native DEM/WBM posting). **Access:** public S3 bucket,
no auth, per-tile HTTPS GET.

**Licence — verified against the primary document, not a secondary summary.**
Fetched and read in full: *"Licence for Copernicus DEM instance
COP-DEM-GLO-30-F Global 30m Full, Free & Open"*
(`https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf`,
fetched 2026-07-29, read in full via PDF extraction — 3 pages, Articles 1-9).

- Claim: Article 4 grants reproduction, distribution, communication to the
  general public, **and** adaptation/modification/combination, worldwide, no
  time limit. Article 5: free of charge. **No share-alike clause anywhere in
  the document** — Article 9 (IPRs) explicitly states the Licensor/Provider
  claim no rights over IP the User creates while exercising these rights.
- Citation: licence PDF, Articles 4, 5, 9 (page 2-3), fetched and read in
  full 2026-07-29.
- Authority kind: geometry / licence.
- Verified how: WebFetch of the PDF, then full-document read via the Read
  tool (PDF extraction) — primary source, not a summary page.

- Claim: **two different attribution notices exist, and the project is
  currently using the wrong one.** Article 6(a) (unmodified data): *"©
  DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided
  under COPERNICUS by the European Union and ESA; all rights reserved."*
  Article 6(b) (**adapted or modified data**): *"produced using Copernicus
  WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH
  2014-2018 provided under COPERNICUS by the European Union and ESA; all
  rights reserved"*. The vendored geometry (a marching-squares-traced,
  Douglas-Peucker-simplified, reordered-and-rounded coastline) is squarely
  "adapted or modified" data under Article 6(b), not the raw WorldDEM-30
  under 6(a).
- Citation: licence PDF Article 6(a)/(b); current (6a, unmodified) wording
  in use at `sources/copernicus-dem/README.md:28-29` and
  `app/src/pages/attribution.astro:374-378`.
- Authority kind: geometry / licence.
- Verified how: primary-document text comparison against the two files
  currently shipping the string, both read directly.
- **This is a live compliance gap, not a hypothetical** — see §5 (licence
  obligations the site does not currently meet).

**US copyright status:** licensed data used inside its licence terms — not a
US public-domain determination.

### 1.2 Relief — SRTM via AWS Terrain Tiles (Tilezen/Mapzen, terrarium encoding)

- Claim: relief contours on both plates come from SRTM elevation data,
  fetched as terrarium-encoded PNG tiles from the `elevation-tiles-prod`
  bucket, no key/auth: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`,
  height decoded as `R*256 + G + B/256 - 32768`.
- Citation: `sources/terrain-tiles/README.md:3-21`.
- Authority kind: geometry / source.
- Verified how: read the README; the Tilezen provenance claim (mosaic of
  regional DEMs, SRTM for the global fill including Turkey) matches Tilezen's
  own published attribution document (see licence check below).

**Resolution:** ~30 m SRTM posting, resampled into Mercator tiles at the
zoom level fetched (z11 troad, z13 plain — see §2).

**Licence.** Verified against Tilezen's own attribution document,
`https://github.com/tilezen/joerd/blob/master/docs/attribution.md` (fetched
2026-07-29):

- Claim: the document opens by stating attribution is required for many
  terrain-tile providers, and its suggested wording for SRTM is exactly
  *"SRTM data courtesy of the U.S. Geological Survey"* — matching what the
  repo uses verbatim.
- Citation: Tilezen `attribution.md` (fetched); repo's copy at
  `sources/terrain-tiles/README.md:29-31` and the `attribution` field of
  both vendored JSON files (`sources/terrain-tiles/troad-contours.json`,
  `sources/terrain-tiles/trojan-plain-contours.json`).
- Authority kind: geometry / licence.
- Verified how: WebFetch of the primary Tilezen document, text compared
  against the repo's copy — matches.

**US copyright status:** SRTM is US-government work, public domain; the
credit line is a courtesy USGS requests, not a copyright condition.

**Gap found:** the site's public attribution page does **not** carry this
credit anywhere — see §5.

### 1.3 Rivers — OpenStreetMap via Overpass

- Claim: the four/five named river courses drawn on the two plates
  (Scamander/Karamenderes, Simoeis/Dümrek Su, Granicus/Biga Çayı,
  Aesepus/Gönen Çayı, Satnioeis/Tuzla Çayı) come from OSM `waterway` ways,
  queried from Overpass on 2026-07-28:
  `https://overpass-api.de/api/interpreter` with
  `way["waterway"~"^(river|stream)$"](<bbox>); out geom;`.
- Citation: `sources/openstreetmap/README.md:1-11`.
- Authority kind: geometry / source.
- Verified how: read the README.

**Licence — ODbL 1.0.** Verified against the primary licence text,
`https://opendatacommons.org/licenses/odbl/1-0/` (fetched 2026-07-29):

- Claim: §4.3 requires a "reasonably calculated" notice of source; the
  suggested form is *"Contains information from DATABASE NAME, which is
  made available here under the Open Database License (ODbL)."* §4.4/4.4.a
  requires a **Derivative Database** (created by extracting/restructuring
  substantial content) to be published only under ODbL or a compatible
  licence; §4.4.b defines "Derivative Database" to include extracting a
  substantial part of the content into a new database. §4.6 requires
  offering the derivative database (or documentation of the alterations) at
  no charge if distributed online. §1.0 defines a **Produced Work**
  (an image, text, etc. resulting from using the content) as triggering only
  the §4.3 notice, **not** the derivative-database obligations.
- Citation: ODbL 1.0 text, §§1.0, 4.3, 4.4, 4.4.a, 4.4.b, 4.6 (fetched
  2026-07-29).
- Authority kind: geometry / licence.
- Verified how: WebFetch of the primary licence text.
- What this means concretely for this project (already correctly reasoned
  in-repo, and matches the primary text): the **rendered plate image** is a
  Produced Work (notice only), but `sources/openstreetmap/*.json` and the
  `path` geometry of the river layers inside `apparatus/plates/*.json` (and
  their `build/dist/plates/` copies) are themselves a **Derivative
  Database**, obliging the project to offer that geometry under ODbL if it
  publishes it — which it does, by shipping the plate JSON. `sources/openstreetmap/README.md:13-40`
  frames this as **John's decision, not yet made** ("Accept it" vs. "Drop
  the rivers"), and states `app/src/pages/attribution.astro` does not yet
  carry the ODbL notice.
- **Correction to that framing:** `app/src/pages/attribution.astro:380-388`
  (read directly, 2026-07-29) **already carries** the OSM/ODbL attribution
  and states the river geometry is offered under ODbL. The decision recorded
  as pending in the README appears to have been made since the README was
  last touched. This dossier does not resolve which of the two files is
  stale — that is a one-line reconciliation for whoever next edits either
  file, not a geometry question — but flags it so the re-cut lane does not
  assume the obligation is still undecided.

### 1.4 AWMC ancient-world GeoJSON — considered, not used for this project's coastline

- Claim: AWMC's vector data (`https://github.com/AWMC/geodata`) is licensed
  **ODbL 1.0**, and its own README states it is *"derived from the
  Barrington Atlas of the Greek and Roman World, and uses AWMC modifications
  to OpenStreetMap … which is under the ODC Open Database License."*
- Citation: AWMC/geodata GitHub README (fetched via WebSearch + WebFetch,
  2026-07-29; the wordpress URL first tried, `awmc.unc.edu/wordpress/tag/geojson/`,
  404s). The GitHub repo carries the ODbL statement in BOTH its README License
  section and a dedicated `LICENSE.txt` (Grok verification, 2026-07-29).
- Authority kind: geometry / licence.
- Verified how: WebFetch of `https://github.com/AWMC/geodata`.
- Claim: this project explicitly evaluated AWMC as a river-course candidate
  and rejected it on data-quality grounds, not licence grounds (its licence
  is the same ODbL burden as raw OSM): *"AWMC's ODbL data was checked too:
  its `inland-water-OSM` layer is lake and swamp polygons, 419 vertices in
  the whole Troad sheet, and carries no named river here"* — measured, not
  assumed.
- Citation: `sources/openstreetmap/README.md:33-36`.
- Authority kind: geometry / source.
- Verified how: read the README's own measurement claim; not independently
  re-run (would require fetching the same AWMC GeoJSON and re-counting
  vertices — flagged in §6 as unverified-by-this-dossier, low priority since
  the project already made the call not to use it).
- **AWMC was never a coastline candidate for the base layer** — the
  Copernicus DEM was chosen specifically to *avoid* ODbL's share-alike reach
  (`sources/copernicus-dem/README.md:19-23`), and AWMC (like OSM) carries
  that obligation. If the re-cut lane is ever asked to reconsider AWMC for
  anything, the attribution obligation is identical to OSM's (§1.3): a
  Produced Work needs only a notice, but a published derivative database
  needs to be offered under ODbL.

### 1.5 Natural Earth — not a source for these two plates

- Claim: Natural Earth is used elsewhere in this repo (the scene-panel
  background map, `shared/lib/scenemap.ts`) but **not** for the Troad or
  Trojan-plain plates. It was measured and rejected as a coastline source
  for the Troad/plain sheets specifically: *"the 1:50m vectors this repo
  already vendors carry **three** vertices inside the Trojan-plain sheet;
  the 1:10m file carries **fifteen**, still a straight line across a 24 km
  delta, and neither has Tenedos. Measured, not assumed."*
- Citation: `sources/copernicus-dem/README.md:78-82` ("Why not Natural
  Earth" section); scene-panel usage at `sources/naturalearth/README.md`.
- Authority kind: geometry / source.
- Verified how: read the README's stated measurement; not independently
  re-counted (the raw NE file is not vendored at that granularity in this
  repo — re-counting would require re-fetching `ne_50m_land.geojson` and
  `ne_10m_land.geojson` and clipping to the plain's bbox, which is out of
  this dossier's budget given the project already excluded this source for
  these two plates).

**Licence** (for completeness, since the task requires it in the source
table even though this source isn't used for the plates in scope): verified
against `https://www.naturalearthdata.com/about/terms-of-use/` (fetched
2026-07-29) — *"All versions of Natural Earth raster + vector map data found
on this website are in the public domain … No permission is needed to use
Natural Earth. Crediting the authors is unnecessary."* Matches
`sources/naturalearth/README.md:3-5` exactly.

- Authority kind: geometry / licence.
- Verified how: WebFetch of the primary terms-of-use page.

### 1.6 Source/licence/attribution summary table

| Source | Used for | Resolution | Access | Licence | Attribution string required |
|---|---|---|---|---|---|
| Copernicus DEM GLO-30 WBM | coastlines, islands (both plates) | 30 m | S3, no auth, per-1°-tile | free, no share-alike ([primary licence PDF](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf)) | Art. 6(b), modified-data form (see §1.1 — currently shipping the wrong one) |
| SRTM via AWS Terrain Tiles (Tilezen) | relief contours (both plates) | ~30 m | S3 PNG tiles, no auth | US-government PD; courtesy credit requested ([Tilezen attribution doc](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)) | "SRTM data courtesy of the U.S. Geological Survey" — missing from `attribution.astro` (see §5) |
| OpenStreetMap (Overpass) | river courses (both plates) | vector, survey-grade | Overpass API, no auth | ODbL 1.0, share-alike on the derivative database ([primary licence](https://opendatacommons.org/licenses/odbl/1-0/)) | "© OpenStreetMap contributors" + ODbL notice — present in `attribution.astro` |
| AWMC ancient-world GeoJSON | **not used** (considered for rivers, rejected on data quality) | vector | GitHub raw files, no auth | ODbL 1.0, same obligations as OSM ([repo README](https://github.com/AWMC/geodata)) | n/a — not shipped |
| Natural Earth 1:50m/1:10m | **not used for these plates** (used for the unrelated scene-panel map) | ~50 m / ~10 m cartographic scale | GitHub raw GeoJSON mirror | public domain, no attribution required ([terms of use](https://www.naturalearthdata.com/about/terms-of-use/)) | none required; repo credits it anyway in `attribution.astro:320-324` |

---

## 2. Extraction parameters as found (with file:line)

### 2.1 Coastlines — `scripts/prep-troad-basemap.py`

| Parameter | Value | Citation |
|---|---|---|
| Plain bbox | `(39.86, 26.10, 40.05, 26.38)` | `scripts/prep-troad-basemap.py:121` |
| Troad bbox | `(38.95, 25.35, 40.60, 27.50)` | `scripts/prep-troad-basemap.py:122` |
| Douglas-Peucker tolerance, plain | `PLAIN_TOL = 0.00012` deg | `scripts/prep-troad-basemap.py:129` |
| Douglas-Peucker tolerance, troad | `TROAD_TOL = 0.00100` deg | `scripts/prep-troad-basemap.py:130` |
| Stated rationale | "about half a pixel at each plate's own render size" | `scripts/prep-troad-basemap.py:124-128` |
| Min ring area, plain | `PLAIN_MIN_AREA = 2.0e-7` deg² (≈0.19 ha at lat 40° — the script's own comment says ≈2.5 ha, a ~10× conversion slip; the cull uses deg², so no operational effect) | `scripts/prep-troad-basemap.py:133` |
| Min ring area, troad | `TROAD_MIN_AREA = 8.0e-6` deg² (≈7.6 ha at lat 40° — script comment says ≈80 ha, same ~10× slip) | `scripts/prep-troad-basemap.py:134` |
| Tidal-reach filter | `CHANNEL_MAX_WIDTH_M = 186.0`, `CHANNEL_MIN_DEPTH_M = 90.0` | `scripts/prep-troad-basemap.py:533-534` (see §4) |

- Authority kind: geometry / parameter.
- Verified how: read the script's constant declarations directly.

### 2.2 Rivers — same script, same tolerances as coastlines (half-pixel), chained across OSM way splits and clipped by Liang-Barsky (`scripts/prep-troad-basemap.py` — chaining logic documented in `sources/openstreetmap/README.md:42-49`).

### 2.3 Relief — `scripts/prep-terrain-contours.py`

The `SHEETS` dict (`scripts/prep-terrain-contours.py:657-680`) is the single
source of truth:

```python
SHEETS = {
    "troad": {
        "bbox": (38.95, 25.35, 40.6, 27.5), "zoom": 11,
        "blur": 4, "decimate": 2, "post_blur": 5,
        "tol_deg": 0.005, "min_points": 5, "min_span_deg": 0.07,
        "levels": [50, 100, 200, 300, 400, 600, 800, 1000, 1200, 1400],
    },
    "trojan-plain": {
        "bbox": (39.86, 26.1, 40.05, 26.38), "zoom": 13,
        "blur": 10, "decimate": 2, "post_blur": 2,
        "tol_deg": 0.0009, "min_points": 5, "min_span_deg": 0.012,
        "levels": [10, 15, 20, 25, 30, 40, 60, 100, 150, 200, 320],
    },
}
```

- Claim: exact values as above.
- Citation: `scripts/prep-terrain-contours.py:657-680`.
- Authority kind: geometry / parameter.
- Verified how: direct file read.

Definitions, from the script's own comments and code:

- `blur` — box-blur passes on the raw elevation grid **before** decimation,
  to suppress sensor noise so the contour is not a staircase
  (`scripts/prep-terrain-contours.py:223` `box_blur`, rationale at
  `:22-25`).
- `decimate` — integer downsample factor applied after blur
  (`:246` `decimate`).
- `post_blur` — **extra** blur passes applied after decimation, to the grid
  the contour is actually traced on; rationale: *"a contour is only as
  smooth as the ground under it: simplifying a line at 685 m … when the
  surface still carries 124 m wiggles does not generalise it, it turns every
  wiggle into a spike"* (`scripts/prep-terrain-contours.py:647-655`).
- `tol_deg` — the Douglas-Peucker tolerance applied to every traced line at
  `contours()` (`:399,415`), used identically for named landforms and
  residual bands (see §3.3 — this matters for the "single tolerance" spec
  item).
- `min_points` — rings simplified below this vertex count are dropped
  (`:399,418`).
- `min_span_deg` — rings whose bbox diagonal is below this are dropped as
  specks (`:399,422-423`).
- `sample_spacing_m` — the **raw grid cell spacing actually traced**, in
  ground metres, computed as `156543.03392 * cos(mean_lat) / 2^zoom *
  decimate` (`scripts/prep-terrain-contours.py:1581-1583`). This is not a
  simplification tolerance — it is the finest possible vertex spacing
  Douglas-Peucker could ever preserve, because DP only removes points.
  **This value governs §3's spec at least as much as `tol_deg` does** — see
  §3.2.

Vendored derivation blocks (machine output, read directly, not re-derived):

| sheet | blur | decimate | post_blur | tol_deg | sample_spacing_m |
|---|---|---|---|---|---|
| troad | 4 | 2 | 5 | 0.005 | 117.5 |
| trojan-plain | 10 | 2 | 2 | 0.0009 | 29.3 |

- Citation: `sources/terrain-tiles/troad-contours.json` (`derivation` key),
  `sources/terrain-tiles/trojan-plain-contours.json` (`derivation` key).
- Authority kind: geometry / parameter.
- Verified how: `python3 -c "import json; print(json.load(open(...))
  ['derivation'])"` against both files, 2026-07-29.

### 2.4 Tidal-reach filter — see §4 (kept separate per the task's structure).

---

## 3. The re-cut spec

### 3.1 Deriving px→m for both sheets, shown in full

Both plate JSONs carry `size: [width_px, height_px]` and `bbox: [minLat,
minLon, maxLat, maxLon]` (this project's convention — confirmed at
`apparatus/plates/troad.json:7-8` and `apparatus/plates/trojan-plain.json:7-8`).

**Troad** — `size: [840, 839]`, `bbox: [38.95, 25.35, 40.6, 27.5]`:

```
lat span  = 40.6 - 38.95           = 1.65 deg   over 839 px (height)
          => 1.65 / 839            = 0.0019666 deg/px (vertical)
lon span  = 27.5 - 25.35           = 2.15 deg   over 840 px (width)
          => 2.15 / 840            = 0.0025595 deg/px (horizontal)

m/deg lat = 111320                 (constant)
mean lat  = (38.95 + 40.6) / 2     = 39.775 deg
m/deg lon = 111320 * cos(39.775deg)= 111320 * 0.76856 = 85556 m/deg

vertical  m/px = 0.0019666 * 111320 = 218.92 m/px  (~219 m/px)
horizontal m/px = 0.0025595 * 85556 = 218.98 m/px  (~219 m/px — near-square
                                                      pixels at this latitude,
                                                      as expected)
```

**Trojan plain** — `size: [880, 779]`, `bbox: [39.86, 26.1, 40.05, 26.38]`:

```
lat span  = 40.05 - 39.86          = 0.19 deg   over 779 px
          => 0.19 / 779            = 0.00024390 deg/px
lon span  = 26.38 - 26.1           = 0.28 deg   over 880 px
          => 0.28 / 880            = 0.00031818 deg/px

mean lat  = (39.86 + 40.05) / 2    = 39.955 deg
m/deg lon = 111320 * cos(39.955deg)= 111320 * 0.76648 = 85327 m/deg

vertical  m/px = 0.00024390 * 111320 = 27.15 m/px
horizontal m/px = 0.00031818 * 85327 = 27.15 m/px  (consistent)
```

- Claim: as computed above.
- Citation: `apparatus/plates/troad.json:7-8`,
  `apparatus/plates/trojan-plain.json:7-8` for `bbox`/`size`; arithmetic is
  this dossier's own, cross-checked against the render-scale figures already
  stated in `sources/terrain-tiles/README.md:67-70` ("troad … ≈ 218 m/px",
  "trojan-plain … ≈ 27 m/px") — independent match.
- Authority kind: geometry / spec.
- Verified how: recomputed from the plate JSON's own `size`/`bbox` fields,
  not copied from the README.

### 3.2 The tolerance target: same as the coastlines, stated in both units

The coastline tolerances are already the correct target — they were cut at
"about half a pixel" per `scripts/prep-troad-basemap.py:124-128`, confirmed
by the arithmetic below:

| sheet | coastline tol_deg | tol in px | tol in m |
|---|---|---|---|
| troad | 0.00100 | 0.00100 / 0.0019666 = **0.509 px** | 0.00100 × 111320 = **111.3 m** |
| trojan-plain | 0.00012 | 0.00012 / 0.00024390 = **0.492 px** | 0.00012 × 111320 = **13.4 m** |

**Spec: set the relief `tol_deg` to the same value as that sheet's
coastline `tol_deg`.**

| sheet | current relief tol_deg | target relief tol_deg | change |
|---|---|---|---|
| troad | 0.005 (`scripts/prep-terrain-contours.py:664`) | **0.00100** (`TROAD_TOL`, `scripts/prep-troad-basemap.py:130`) | 5.0× tighter |
| trojan-plain | 0.0009 (`scripts/prep-terrain-contours.py:675`) | **0.00012** (`PLAIN_TOL`, `scripts/prep-troad-basemap.py:129`) | 7.5× tighter |

This 5.0× / 7.5× figure independently reproduces the handoff's measured "4
to 7 times coarser" claim (`docs/TROY-MAPS-HANDOFF-2.md:96`), from the
tolerance ratio alone rather than from measured on-screen vertex spacing —
two independent methods agreeing.

- Authority kind: geometry / spec.
- Verified how: direct constant comparison + arithmetic shown above.

### 3.3 The tolerance alone is not sufficient — the raw grid must be dense enough to have vertices for DP to keep

Douglas-Peucker can only **remove** points; it cannot invent vertices the raw
traced polyline never had. `sample_spacing_m` (§2.3) is the ground spacing of
the grid the contour is actually traced on, **after** `decimate`. Comparing
it to the target tolerance in §3.2:

| sheet | raw grid spacing (current `decimate`) | target tolerance | verdict |
|---|---|---|---|
| troad | 117.5 m | 111.3 m | raw spacing is *already* close to target — tightening `tol_deg` alone gets most of the way there. Recommend `decimate: 1` (→ 58.8 m raw spacing) for real margin, but `decimate: 2` is defensible as "close enough." |
| trojan-plain | 29.3 m | 13.4 m | raw spacing is **2.2× coarser than target** — tightening `tol_deg` alone **will not reach the target density**, because DP has nothing finer than 29.3 m to keep. `decimate` must drop to 1 (→ 14.65 m, ~9% coarser than target — close) or, for real margin, `zoom` must rise to 14 (→ 7.3 m at `decimate: 1`, well under target). |

- Claim: as computed. Arithmetic for troad at `decimate=1`:
  `156543.03392 * cos(39.775°) / 2^11 * 1 = 58.8 m`. For trojan-plain at
  `zoom=14, decimate=1`: `156543.03392 * cos(39.955°) / 2^14 * 1 = 7.3 m`.
- Citation: formula at `scripts/prep-terrain-contours.py:1581-1583`; current
  values in §2.3's table.
- Authority kind: geometry / spec.
- Verified how: same formula the script itself uses, recomputed by hand for
  the proposed parameter changes.
- **This is the dossier's one substantive addition to the handoff's own
  diagnosis**: simply editing `tol_deg` and re-running, without touching
  `decimate`/`zoom`, will visibly improve the troad sheet but will **not**
  fix the trojan-plain sheet's relief density, because its raw grid is
  coarser than the target tolerance to begin with. The re-cut lane must
  change both.

### 3.4 No smoothing — and a needed distinction between two different "smoothings"

The handoff's "then smoothed" (`docs/TROY-MAPS-HANDOFF-2.md:96`) and this
dossier's investigation point to **two separate mechanisms**, and the fix is
different for each:

1. **Pre-trace grid blur** (`blur`, `post_blur` in `SHEETS`) — this
   suppresses genuine sensor noise in the 30 m SRTM grid *before* marching
   squares runs, so the raw contour isn't a jagged staircase. This is
   legitimate and should **not** be removed; it should not be *increased*
   to compensate for a coarse `tol_deg`/`decimate` either (which is close to
   what happened: `trojan-plain`'s `blur: 10` is 2.5× `troad`'s `blur: 4`,
   for a much lower-relief, smaller sheet — worth re-examining once
   `decimate`/`zoom` are corrected per §3.3, but out of this dossier's scope
   to re-tune without re-running the pipeline).
2. **Draw-time corner rounding** (`shared/lib/plate.ts:2059-2131`,
   `smoothFrame`/`smoothPolyline`/`smoothPathD`) — a bounded quadratic-Bézier
   rounding applied to every line on a *geographic* plate at render time,
   added the same day as the handoff
   (`shared/lib/plate.ts:2025-2044`, comment dated 2026-07-29). It is
   provably bounded: each rounded corner stays inside the triangle formed by
   the vertex and its two adjacent edge-midpoints, which themselves lie on
   the original line — it cannot invent geometry beyond that triangle. This
   is **not** the defect; it is a legitimate draw-time treatment that
   depends on having enough source vertices to have real corners to round.
   At 8-21 px vertex spacing, a "rounded corner" spans most of the visible
   feature, which is what reads as an invented lobe.

- **Spec: "no smoothing" means (a) do not add or increase geometry-level
  smoothing beyond what §3.4.1 already does to suppress sensor noise, and
  (b) do not compensate for a coarse re-cut by leaning on `smoothPathD` —
  fix the vertex density (§3.2, §3.3) so the existing, already-bounded
  corner-rounder has real detail to round.** No code change to
  `shared/lib/plate.ts` is implied by this dossier.
- Citation: `shared/lib/plate.ts:2015-2048` (doc comment), `:2059-2131`
  (implementation).
- Authority kind: geometry / spec.
- Verified how: read the renderer source directly; traced the "triangle
  containment" claim through `smoothFrame`'s `mid()` construction
  (`shared/lib/plate.ts:2065-2073`) — the entry/exit points are genuinely
  edge midpoints of the original polyline, confirming the bound.

### 3.5 Minimum-ring-vertex threshold — the rule, and why the current one let two 9-segment rings through

- Claim: `relief-band-0100` and `relief-band-0320` on the trojan-plain plate
  each carry **10 coordinate entries (9 segments)** — 0100 as a closed ring
  (first == last, 9 unique points), 0320 as an **open, frame-clipped polyline**
  (first ≠ last, ending near the east neatline at lon 26.38).
- Citation: `apparatus/plates/trojan-plain.json:2009-2021` (`relief-band-0100`),
  `:2533-2544` (`relief-band-0320`).
- Authority kind: geometry / source (measured directly from the plate JSON).
- Verified how: `python3 -c "import json; ..."` counting ring vertices in
  both files, 2026-07-29 — reproduces the handoff's claim exactly
  (`docs/TROY-MAPS-HANDOFF-2.md:102-103`).

- Claim: the current culling rule (`min_points: 5` at
  `scripts/prep-terrain-contours.py:665,676`) does not catch either ring —
  both have 10 ≥ 5 points — and `min_span_deg` (0.012 for trojan-plain,
  `:677`) doesn't either: `relief-band-0100`'s bbox diagonal is
  `hypot(0.0117, 0.0188) = 0.0222 deg`, above the 0.012 threshold.
- Citation: as above; diagonal computed by this dossier from the vendored
  coordinates.
- Authority kind: geometry / parameter (diagnostic).
- Verified how: direct computation from the ring's own lat/lon extent.

**The rule, stated as a spec:** the coastline pipeline already has a working
precedent for this — `TROAD_MIN_AREA`/`PLAIN_MIN_AREA`
(`scripts/prep-troad-basemap.py:133-134`) culls by **ground area**, not
vertex count, so a genuine small feature with few vertices (a small,
correctly-simple polygon) is not confused with a degenerate trace. Vertex
COUNT alone is the wrong signal — `relief-band-0100`'s 10-vertex ring spans
about 90 px diagonally on the trojan-plain sheet (0.0222 deg ×
111320 m/deg ÷ 27.15 m/px ≈ 91 px), which is not a tiny feature; it is a
real-sized feature traced with far too few vertices for its size, which
`min_span_deg`/`min_points` cannot detect because neither measures vertex
*density*.

- **Spec: replace or supplement the vertex-count/span culls with a
  density check — cull (or force a re-trace at a finer level) any ring
  whose vertex count is less than its bbox-diagonal-in-px divided by a
  fixed target spacing** (e.g., the same ~1 px/vertex the coastlines
  achieve; a ring covering 91 px diagonally should carry on the order of
  tens of vertices, not 10). A ring failing this check after the §3.2/§3.3
  tolerance and density fixes are applied is either genuinely degenerate
  (numerical artefact of the tracer) and should be dropped, or is evidence
  the fix wasn't applied correctly and the pipeline should fail loudly
  rather than silently emit it — this dossier recommends failing loudly
  (`raise SystemExit`, matching the existing style at
  `scripts/prep-terrain-contours.py:415,799`), not silently dropping,
  because a dropped ring is a missing feature and Homer's "absences are
  content" rule (`CLAUDE.md`, map-register section) cuts the other way for
  real terrain: real terrain that fails to trace should be visible as a
  build failure, not silently absent.
- Authority kind: geometry / spec (this dossier's recommendation, not an
  existing repo convention — flagged as such).

### 3.6 One generalisation tolerance for all relief on a sheet — already true in code; the handoff's framing needs one correction

- Claim: contrary to a literal reading of the handoff's "cut at a different
  generalisation" language (`docs/TROY-MAPS-HANDOFF-2.md:99-101`), **there
  is only one `tol_deg` per sheet in the code**, and it is applied
  identically to named landforms and residual bands. `relief_block()`
  (`scripts/prep-terrain-contours.py:1399-1432`) calls `sheet_bodies(name,
  g, level)` once per elevation level — this traces every closed body at
  that level, using the sheet's single `tol_deg`
  (threaded through `contours()` at `:399,415`) — and then simply sorts the
  resulting bodies into "claimed by a named seed point" vs. "everything
  else at that level" (`:1407-1425`). No boolean subtraction, clip, or
  second tolerance is involved.
- Citation: `scripts/prep-terrain-contours.py:1399-1432` (`relief_block`),
  `:794-800` (`body_containing`), `:399-424` (`contours`, showing the single
  `tol_deg` parameter threading through).
- Authority kind: geometry / parameter (code-reading, not a repo claim being
  quoted).
- Verified how: read the full call chain from `SHEETS[...]["tol_deg"]`
  through to the vertex list written for both named and residual layers.

- What actually varies, then, is body **complexity relative to a single
  coarse tolerance**: a large, complex outline (`relief-ida`, 177 vertices)
  survives a coarse tolerance because it has enough genuine direction
  changes to keep; a small or simple outline at the same tolerance collapses
  toward the `min_points` floor (the 5-9-vertex rings). The apparent
  vertex-count mismatch between named landforms and bands in the handoff's
  table (`relief-chersonese` 29, `relief-samothrace` 14,
  `relief-troad-west-highland` 24 — all independently reconfirmed by this
  dossier at those exact counts, `apparatus/plates/troad.json`) is a
  side-effect of shape complexity under one tolerance, not evidence of two
  tolerances.
- Citation: vertex counts reconfirmed by direct JSON read, 2026-07-29
  (`relief-chersonese`: 29, `relief-troad-west-highland`: 24,
  `relief-samothrace`: 14, `relief-ida`: 177 — note `relief-ida` was **not**
  given a vertex count in the handoff table and is not a low-vertex case).
- Authority kind: geometry / source (measured).
- Verified how: `python3` script counting `polygon`/`rings[0]` length per
  named layer in `apparatus/plates/troad.json`.

- **Spec: the "one tolerance for the whole sheet" rule the task asks for is
  already satisfied structurally.** What must change is (a) the *value* of
  that single tolerance, per §3.2, and (b) adding the density-based cull of
  §3.5 so that small/simple bodies at the corrected tolerance don't still
  fall through as slivers. **No code restructuring of `relief_block` is
  required** — this narrows the re-cut lane's blast radius considerably
  relative to what the handoff's phrasing might suggest.
- The alternative the task also asks to record: **dropping named polygons
  as geometry** (keeping `relief-ida` etc. only for their prose/citations,
  drawing them as part of the generic band instead). This dossier does not
  recommend it — `relief_block`'s named-body selection is a `placeId`
  lookup by seed point, not a geometric special case, so it costs nothing
  extra once the tolerance/density fixes land, and separating "Ida" as its
  own layer is what lets the gazetteer's `mythical`-tier
  Callicolone/Gargaron/etc. anchor to a real landform boundary rather than
  a point. Recorded as an option per the task's instruction, not adopted.

---

## 4. The tidal-reach filter (morphological opening)

- Claim: implemented at `scripts/prep-troad-basemap.py:600-629`
  (`close_channels`), with the structuring-element and threshold logic at
  `:493-568` (`_ellipse`, `_shifted`, constants). Parameters:
  `CHANNEL_MAX_WIDTH_M = 186.0`, `CHANNEL_MIN_DEPTH_M = 90.0`
  (`:533-534`).
- Citation: as above.
- Authority kind: geometry / parameter.
- Verified how: direct file read of the implementation and its extensive
  inline rationale comment (`:493-532`).

**Why 186 m / 90 m — the stated reasoning, verified against the code's own
measurements (not re-derived independently):**

- The Water Body Mask classes a river's tidal reach as `ocean` (class 1),
  not `river` (class 3), so a naive trace of the ocean boundary follows the
  Karamenderes and Dümrek mouths 300-500 m inland and back out, producing
  "a pair of thin fjords meeting at a point and a hook that doubles back on
  itself" (`:498-513`, five measured intrusions listed, e.g. `40.0047N
  26.2103E, 43 cells, 494 m inland, ≤2 cells wide`).
- The filter is a morphological opening: erode by a disk of radius
  `CHANNEL_MAX_WIDTH_M/2`, then dilate by the same disk. This can only ever
  convert water to land — it cannot delete a cape, spit, or island, because
  opening never grows a region beyond its original extent (`:515-520`).
- `CHANNEL_MAX_WIDTH_M = 186.0` (six cells at 30 m posting) was chosen
  because the narrowest *genuine* water on either sheet — the Dardanelles at
  ~1.2 km, Beşik Bay's mouth at ~1.5 km — is "two orders of magnitude" wider
  than the widest measured artefact channel (three cells, ~90 m) (`:522-525`).
- `CHANNEL_MIN_DEPTH_M = 90.0` (three cells) is the second half of the rule:
  narrow water is only closed if it *also* reaches more than 90 m inland
  from wider water the opening keeps — this protects a concave real
  coastline corner (which the opening can shave slightly) from being
  mistaken for a channel, because a shaved corner sits immediately against
  the water it was cut from, while a genuine channel runs on (`:527-532`).
- The structuring element is a ground-circular disk, not a pixel-circular
  one: at 40°N a WBM cell is ~30.9 m tall and ~23.7 m wide, so the disk is
  computed as an ellipse in (row, col) space to keep the 186 m/90 m
  thresholds meaning actual metres in both directions
  (`_ellipse`, `:538-551`).

- Authority kind: geometry / parameter (all of the above).
- Verified how: read the implementation and its inline comments in full;
  the "narrowest genuine water" figures (Dardanelles ~1.2 km, Beşik Bay
  ~1.5 km) are asserted in the code comment, not independently re-measured
  by this dossier from the raw WBM (would require re-fetching and
  re-mosaicking the tiles — see §6).

### 4.1 Which named waters are claimed to survive, and where each claim lives

| water body | claimed to survive | citation | independently spot-checked by this dossier? |
|---|---|---|---|
| Dardanelles (~1.2 km narrows) | yes | `scripts/prep-troad-basemap.py:205,254`, layer note at `apparatus/plates/troad.json` `coast-asia`/`coast-modern` notes | no — narrows sits mostly outside the vendored coastline JSON's easily-isolable region; not re-measured |
| Beşik Bay mouth (~1.5 km) | yes | `scripts/prep-troad-basemap.py:255` (troad), `:190,205` (trojan-plain note) | no |
| Gulf of Gera (Lesbos) | yes, explicitly named | `scripts/prep-troad-basemap.py:255` — *"the mouth of Besik Bay and the entrance to the Gulf of Gera are all far above it and all survive intact"* | no |
| **Gulf of Kalloni (Lesbos)** | **not named anywhere in the repo's code, comments, or layer notes** | — (absence confirmed by `grep -rn "Kalloni"` across `.py`/`.json`/`.md`, no hits) | **yes — see below** |

**Kalloni is not part of the repo's own claim.** The task's brief names
"the Gulfs of Gera and Kalloni" as a pair, but the repo only ever asserts
Gera survived; Kalloni is never mentioned. This dossier ran an independent,
cheap geometric check rather than assert or silently drop the claim:

- Method: loaded `sources/copernicus-dem/troad-coastline.json`, isolated
  `coast-islands#2` (609 vertices, bbox lat 38.962-39.390, lon
  25.832-26.616 — matching Lesbos's real extent, confirming this is the
  Lesbos ring). Restricted to points in the Gulf of Kalloni's approximate
  area (lat 39.00-39.30, lon 26.05-26.35, 113 candidate vertices) and
  searched for the pair of ring-index-distant points (index gap > 8, i.e.
  not adjacent-neighbour artefacts) with the smallest ground distance
  between them — the geometric signature of a strait or bay mouth's two
  shores.
- Result: the closest such pair is 0.88 km apart (ring indices 294 and 358,
  points `[39.09764, 26.11611]` and `[39.105, 26.11236]`), and the ring's
  traced extent inside this window runs from lat 39.00 to lat 39.30 — i.e.
  the coastline does trace a deep, narrow indentation consistent with the
  Gulf of Kalloni's real shape, and the two shores at its narrowest measured
  point (0.88 km) remain **~4.7× wider than the 186 m filter threshold**, so
  they were never close to being closed by the opening.
- Authority kind: geometry / spec (verification, this dossier's own).
- Verified how: direct computation against
  `sources/copernicus-dem/troad-coastline.json`, 2026-07-29 (script run
  inline, not saved to the repo).
- Caveat, stated plainly: this is a **spot-check of ring geometry**, not a
  toponymic confirmation that this indentation is "the Gulf of Kalloni" —
  that would be an identification claim, out of scope for a geometry-only
  dossier (see the top-of-file scope note). It establishes that *some*
  large, narrow bay in the right location on Lesbos survived the filter
  with wide margin; it does not itself name the bay. Naming it is
  `RESEARCH-TROAD-TOPOGRAPHY.md`'s job if the schematic/geographic gazetteer
  ever wants a `gulf-of-kalloni` place.

---

## 5. Licence/attribution obligations the site does not currently meet

Three concrete gaps found, all narrow and all fixable without touching
geometry (the third added at Grok verification, 2026-07-29):

1. **Copernicus DEM attribution uses the wrong notice.** Both
   `sources/copernicus-dem/README.md:28-29` and
   `app/src/pages/attribution.astro:374-378` carry the Article 6(a)
   ("unmodified data") notice, but the vendored/published geometry is
   Article 6(b) "adapted or modified" data (traced, simplified, reordered,
   rounded). The correct string per the primary licence text (§1.1) is:
   *"produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and ©
   Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the
   European Union and ESA; all rights reserved"*.
2. **SRTM/USGS credit is missing from the public attribution page.**
   `sources/terrain-tiles/README.md` and every relief layer's `sources`
   field in both plate JSONs carry "SRTM data courtesy of the U.S.
   Geological Survey" (confirmed present at, e.g.,
   `apparatus/plates/trojan-plain.json:2024-2029`), but
   `app/src/pages/attribution.astro` never mentions SRTM, Terrain Tiles, or
   USGS anywhere (confirmed by `grep -n "USGS\|Terrain Tiles\|SRTM" 
   app/src/pages/attribution.astro` — no hits). Copernicus and OSM both get
   both per-layer citations *and* a public-page credit; SRTM only gets the
   former. Since USGS's ask is specifically about "redistribution, resale,
   presentation or publication" credit and this project publishes the
   relief contours, this is the one gap worth closing to match the
   project's own established pattern for the other two sources.
3. **Copernicus Article 6(c) liability notice is absent.** Beyond 6(a)/6(b),
   Article 6 of the primary licence requires a sentence disclaiming the
   liability of the Copernicus programme organisations on distribution of
   the (modified or unmodified) data. Neither `attribution.astro` nor the
   two READMEs carry it. Same fix vehicle as gap 1: one sentence on the
   attribution page (Grok verification against the licence PDF, 2026-07-29).
   The exact Article 6(c) sentence, pulled verbatim from the primary licence
   PDF (2026-07-30, attribution lane): "The organisations in charge of the
   Copernicus programme by law or by delegation do not incur any liability
   for any use of the Copernicus WorldDEM-30." Applied to
   `attribution.astro` the same day; the two READMEs still lack it.

All three are attribution-string edits, not geometry changes — out of this
dossier's blast radius to fix directly (this is a geometry-authority
dossier), but recorded here because the task explicitly asked for any
obligation the site currently fails to meet.

- Authority kind: geometry / licence (both items).
- Verified how: direct comparison of primary licence text against the
  exact strings currently shipping in the repo, both read in full.

---

## 6. Needs paywalled access

None. Every source and licence document used in this dossier (Copernicus
DEM licence PDF, Tilezen attribution doc, ODbL 1.0 text, Natural Earth terms
of use, AWMC repo README, AWS Open Data registry pages) is free and
publicly accessible without a login or paywall.

## 7. Unverified — do not claim publicly

- **The 186 m/90 m filter's "narrowest genuine water" figures** (Dardanelles
  ~1.2 km, Beşik Bay mouth ~1.5 km) are asserted in the script's own inline
  comments (`scripts/prep-troad-basemap.py:522-525,254-255`) but were not
  independently re-measured by this dossier from the raw Water Body Mask
  grid — doing so would require re-fetching and re-mosaicking the same nine
  Copernicus tiles, which is within budget for a future verification pass
  but wasn't run here. Treat as repo-asserted, not dossier-verified.
- **AWMC's "419 vertices, no named river" measurement** for its
  `inland-water-OSM` layer (`sources/openstreetmap/README.md:33-36`) is
  quoted from the repo, not independently re-run against AWMC's live
  GeoJSON.
- **Natural Earth's "3 vertices in the plain sheet / 15 in the 1:10m file"**
  measurement (`sources/copernicus-dem/README.md:78-82`) is likewise quoted
  from the repo, not independently re-counted.
- **The Gulf of Kalloni identification.** §4.1's spot-check establishes that
  a large, narrow bay-shaped indentation in the right location on the
  Lesbos ring survived the tidal-reach filter with wide margin. It does
  **not** establish that this indentation is toponymically "the Gulf of
  Kalloni" — no place-name claim is made or implied by this dossier (see
  the scope note at the top of this file).
- **Whether `sources/openstreetmap/README.md`'s "decision not yet made"
  framing for the OSM/ODbL share-alike obligation is simply stale**, or
  whether there was an actual decision conversation with John that both
  updated `attribution.astro` and left the README un-synced. This dossier
  flags the discrepancy (§1.3) but does not resolve which file is
  authoritative — that is an editorial reconciliation, not a geometry
  question.
- **Whether `trojan-plain`'s `blur: 10` (vs. `troad`'s `blur: 4`) is itself
  miscalibrated** once `decimate`/`zoom` are corrected per §3.3 — flagged
  as worth re-examining in §3.4 but not re-tuned or re-run here, since doing
  so requires actually re-running the pipeline against live tile fetches,
  which is implementation work for the re-cut lane, not dossier research.
