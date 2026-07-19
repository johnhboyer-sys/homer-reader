# sources/naturalearth/ — Mediterranean coastline (scene-map background)

**Provenance:** Natural Earth 1:50m Cultural/Physical Vectors, "land" layer
(`ne_50m_land`). Public domain — Natural Earth's terms of use: "No permission
is needed to use Natural Earth. Crediting the authors is unnecessary."
(https://www.naturalearthdata.com/about/terms-of-use/).

**Exact source fetched (2026-07-18):**
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson
(the Natural Earth project's own GitHub mirror, `nvkelso/natural-earth-vector`,
also public domain — it re-serves the same NE data as GeoJSON).

**US copyright status:** public domain (Natural Earth is explicitly PD-dedicated
by its authors; not a US-copyright judgment call the way the literary sources
in `sources/INVENTORY.md` are).

## Derivation

`mediterranean-coastline.json` is NOT the raw Natural Earth file. It is
produced by `scripts/prep-naturalearth-coastline.py` (stdlib-only Python: json,
math, urllib — no new deps), which:

1. Fetches (or reads a cached copy of) the world `ne_50m_land` polygons.
2. Clips every ring to the Mediterranean basin bbox (8°W–38°E, 30°N–46°N) with
   hand-rolled Sutherland-Hodgman polygon clipping — landmasses that extend
   past the box (Europe, Africa, Asia Minor) are cut cleanly at the box edge.
3. Simplifies each clipped ring with hand-rolled Douglas-Peucker (tolerance
   0.006° as of 2026-07-18, was 0.01° — see the script's --tolerance flag) — detailed enough for a small (~300-400px) stylized panel map, not
   a navigational chart.
4. Drops rings too small to read at that size (post-simplify bbox diagonal
   < 0.05°).
5. Reorders each point from GeoJSON's `[lon, lat]` to this project's `[lat,
   lon]` convention (matches `apparatus/places.json` `coords`), rounds to 3
   decimals (~111m — far finer than this map ever renders), and writes compact
   (no-whitespace) JSON.

Output shape:

```json
{ "bbox": [minLon, minLat, maxLon, maxLat], "rings": [[[lat, lon], ...], ...] }
```

**Re-running:** `python3 scripts/prep-naturalearth-coastline.py` (fetches
live) or `python3 scripts/prep-naturalearth-coastline.py --input
path/to/cached-ne_50m_land.geojson` (offline, using a previously-downloaded
copy). Deterministic given the same input.

**Size:** 70 rings, ~34KB (budget was <150KB).

**Consumer:** `shared/lib/scenemap.ts` (pure SVG scene-map library for the
reader's context-panel maps). The library does not read this file itself —
callers load/parse the JSON and pass it in, keeping the library pure and unit
testable without file I/O.
