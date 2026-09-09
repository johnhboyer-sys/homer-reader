# sources/terrain-tiles/ — contours for the Troy plates, from a real DEM

**Provenance:** Terrain Tiles on
[AWS Open Data](https://registry.opendata.aws/terrain-tiles/) — the
Tilezen/Mapzen `elevation-tiles-prod` bucket, terrarium-encoded PNG tiles, no
key and no authentication:

```
https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png
```

Terrarium packs height into the three colour channels:

```
height_m = (R * 256 + G + B / 256) - 32768
```

**Which DEM this actually is, over the Troad:** SRTM. The tileset is a mosaic —
3DEP and NED in the United States, EU-DEM in western Europe, national DEMs
elsewhere, SRTM and GMTED2010 for global fill. Turkey is SRTM country, so every
tile used here is SRTM-derived, at about 30 m posting.

**Licence and what we owe.** Tilezen's
[attribution document](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
opens: *"Attribution is required for many terrain tile data providers. Example
language is provided below, but you are responsible for researching each
project to follow their license terms."* SRTM itself is US-government work
— *"No domestic copyright will be asserted"* — but the USGS asks for credit on
redistribution, resale or publication, and the document's suggested wording is:

> **SRTM data courtesy of the U.S. Geological Survey**

That single line is the whole obligation for this project. It is not
share-alike, it is not non-commercial, and no attribution is owed to AWS or to
Tilezen for hosting. The string is carried in the data (`attribution` in each
JSON below, and a `sources` entry on every plate layer derived from it), so it
travels with the geometry rather than living only in a credits page.

**US copyright status:** public domain (a US-government work; not a
US-copyright judgment call the way the literary sources in
`sources/INVENTORY.md` are).

## Derivation

`troad-contours.json` and `trojan-plain-contours.json` are NOT the tiles. They
are produced by `scripts/prep-terrain-contours.py` (stdlib-only Python — json,
math, zlib, array, subprocess; the PNG decoder is hand-rolled so the script
adds no dependency), which:

1. Fetches the terrarium tiles covering each sheet's bbox at the chosen zoom,
   via `curl` (Python's `urllib` fails SSL verification in this environment),
   caching each tile under `build/terrain-tiles/` so re-runs are offline and
   deterministic. The tiles themselves are never committed.
2. Decodes and mosaics them into one height grid, clipped to the bbox.
3. Box-blurs and decimates. A contour traced at the DEM's raw posting is a
   hairball at a 200 m/px sheet; smoothing is what turns a DEM into a map.
4. Traces contours with marching squares, sewing the per-cell segments into
   closed rings and open lines.
5. Simplifies each line with Douglas-Peucker so the plate JSON stays reviewable.
6. Reorders to this project's `[lat, lon]` convention (matches
   `apparatus/places.json` `coords`) and rounds to 4 decimals (~11 m).

**Zoom and interval, and why those.** Zoom is chosen against each sheet's own
render scale, not maximised — a contour carrying detail finer than one screen
pixel is noise in the diff and noise on the page.

| sheet | render scale | zoom | sample | interval | why that interval |
|---|---|---|---|---|---|
| `troad` | 840 px / 2.15° lon ≈ 218 m/px | z11 | 152 m | 200 m | 0–1757 m of relief. At 100 m the contours on Ida close to within a pixel of each other and read as a smudge. |
| `trojan-plain` | 880 px / 0.28° lon ≈ 27 m/px | z13 | 38 m | 20 m to 100 m, then 50 m | 0–379 m, and the story is LOW relief: Hisarlık is 36 m and the Sigeion ridge 36 m. |

**Elevation sanity check** (measured on these grids, not asserted):

| ground | measured | published |
|---|---|---|
| Kaz Dağı (Ida) summit | **1757.4 m** at 39.6995 N, 26.8653 E | 1774 m, ~39.70 N, 26.87 E |
| Hisarlık (Troy) | 36.1 m | mound c.38 m |
| Sigeion ridge crest | 36.0 m | "30 to 40 m" (Cook) |
| Trojan plain, centre | 13.6 m | a delta plain |
| Aegean and Dardanelles | 0.0 m | sea |

Output shape:

```json
{
  "sheet": "troad",
  "bbox": [minLat, minLon, maxLat, maxLon],
  "zoom": 11,
  "source": "...", "attribution": "SRTM data courtesy of the U.S. Geological Survey",
  "derivation": { "blur_passes": 4, "decimate": 2, "simplify_tolerance_deg": 0.008, "sample_spacing_m": 152.4 },
  "elevation_stats": { "raw": {...}, "smoothed": {...} },
  "levels": [ { "elevation_m": 200, "lines": [[[lat, lon], ...], ...] }, ... ]
}
```

**Re-running:** `python3 scripts/prep-terrain-contours.py` writes this
directory; `--patch-plates` also rewrites the relief and Bronze-Age-shore
geometry inside `apparatus/plates/troad.json` and
`apparatus/plates/trojan-plain.json`, touching only those layers and leaving
every other layer byte-identical. `--stats` reports elevations and stops;
`--probe LEVEL...` reports body and vertex counts at chosen levels.
Deterministic given the same tile cache.

**Modern terrain, and what that does and does not license.** These contours are
a survey of rock. Ridges have not moved since the Bronze Age, so they are
correct for relief. They are NOT the Bronze Age coastline: the bay silted up,
and the 0 m contour here is today's shore. The one place the modern DEM is used
to reason about the ancient shore is `trojan-plain.json`'s `shore-bronze`,
where the flat infilled delta lets a low contour stand as a proxy for the
alluvial fill boundary — calibrated against published constraints and labelled
as a reconstruction in the layer note.

**Consumers:** the relief layers of `apparatus/plates/troad.json` and
`apparatus/plates/trojan-plain.json`, and that plate's derived Bronze Age
shore, barrier, lagoon and marsh. Nothing reads these JSON files at runtime —
they are the vendored record of what the plates were cut from.
