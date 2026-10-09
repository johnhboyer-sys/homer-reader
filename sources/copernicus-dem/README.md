# sources/copernicus-dem/ — coastlines and islands for the two Troad plates

**Provenance:** Copernicus DEM GLO-30 (global 30 m digital surface model),
**Water Body Mask** auxiliary raster — the `AUXFILES/..._WBM.tif` shipped with
each 1° × 1° DEM tile. Class values: `0` no water, `1` ocean, `2` lake,
`3` river. The boundary of class 1 is a 30 m survey of the coastline.

**Exact source fetched (2026-07-28)**, from the AWS Open Data registry, no
credentials required:

```
https://copernicus-dem-30m.s3.amazonaws.com/
  Copernicus_DSM_COG_10_<TILE>_DEM/AUXFILES/Copernicus_DSM_COG_10_<TILE>_WBM.tif
```

Tiles used: `N38_00_E025_00` … `N40_00_E027_00` (nine 1° tiles covering both
sheets). The raw tiles are **not** committed — they are cached under
`build/basemap-cache/` and re-fetched on demand; only the derived JSON below
is vendored.

## Licence and what it obliges us to do

The Copernicus DEM is published under the ESA/Airbus **"Copernicus DEM
Instrument Data"** terms: a free, worldwide, non-exclusive, royalty-free and
perpetual licence to use, reproduce, modify and distribute the data and
derivatives, **conditional on reproducing this attribution**:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus
> Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European
> Union and ESA; all rights reserved

(the Article 6(b) "adapted or modified data" form — what we ship is traced,
simplified and reprojected, not the raw tiles; see
`docs/research/RESEARCH-BASEMAP-DATA.md` §1.1). Article 6(c) further requires
this liability notice on distribution: "The organisations in charge of the
Copernicus programme by law or by delegation do not incur any liability for
any use of the Copernicus WorldDEM-30."

It is **not** a share-alike licence: nothing downstream of this data inherits
a copyleft obligation, and the site may be published under whatever terms the
project chooses. That is why the base coastline of these plates comes from
here rather than from OpenStreetMap or AWMC, whose ODbL terms would put a
share-alike obligation on every derived file (see `sources/openstreetmap/`,
which we do accept for the river courses because nothing else can supply
them).

The attribution above is carried in three places, so it cannot be lost:
this README, the `license` field of each JSON file below, and the plate-level
`sources` entry of both `apparatus/plates/trojan-plain.json` and
`apparatus/plates/troad.json`.

**US copyright status:** not a US-copyright judgement call in the sense that
`sources/INVENTORY.md`'s literary sources are — this is licensed data, used
inside its licence.

## Derivation

Produced by `scripts/prep-troad-basemap.py` (see its docstring), which:

1. Mosaics the WBM tiles covering a sheet's bbox, padded beyond it.
2. Takes `land = (class != ocean)` and forces the outermost frame of the
   padded window to sea, so every landmass contours as a **closed** ring —
   including the ones running off the sheet. A closed ring is the only thing
   a point-in-polygon test can be run against.
3. Contours that mask by marching squares at the land/water boundary.
4. Sorts each landmass onto its plate layer by testing gazetteer-grade
   anchor points (Ida's summit, the Chersonese interior, Bozcaada) for
   containment — never by proximity, which the 1.3 km Dardanelles narrows
   would defeat.
5. Clips to the sheet as **open polylines** (Liang–Barsky), never as closed
   polygons: a coast is stroked, and closing it along the neatline would draw
   the sheet's own edge as land.
6. Generalises each piece with Douglas–Peucker at about half a pixel of the
   plate's own render size — 0.00012° for the Trojan plain, 0.001° for the
   Troad. Generalising to the sheet is correct cartography; vertices finer
   than half a pixel are bytes no reader can see.

## Files

| File | Rings | Vertices | Note |
|---|---|---|---|
| `trojan-plain-coastline.json` | 4 | 587 | `coast-modern`; the layer it replaces held 15 hand-typed vertices |
| `trojan-plain-sea.json` | 1 | 569 | `sea-modern`, a closed sea polygon: the plain keeps `ground: "land"`, so its water is a filled body over the sheet |
| `troad-coastline.json` | 34 | 2,353 | the four coast layers it replaces held 122 between them; closed rings, because the Troad declares `ground: "sea"` and fills each landmass `land` over it |

Output shape (this project's `[lat, lon]` order, **not** GeoJSON's
`[lon, lat]`):

```json
{ "source": …, "sourceUrl": …, "license": …, "derivation": …,
  "bbox": [minLat, minLon, maxLat, maxLon],
  "features": [ { "id": "coast-asia", "name": "coast-asia#0",
                  "points": [[lat, lon], …] } ] }
```

`id` is the plate layer the feature belongs to.

**Re-running:** `python3 scripts/prep-troad-basemap.py` (emit sources only) or
`--update-plates` (also rewrite the plate layers). Deterministic given the
same tiles. Requires numpy and Pillow — the standard library has no TIFF
decoder, and this is a manual vendoring script, not a build step.

**Why not Natural Earth.** The 1:50m vectors this repo already vendors carry
**three** vertices inside the Trojan-plain sheet; the 1:10m file carries
**fifteen**, still a straight line across a 24 km delta, and neither has
Tenedos. Measured, not assumed.
