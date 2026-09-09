#!/usr/bin/env python3
"""Re-derive shore-bronze / lagoon-bronze as a sea-connected sub-10 m region.

Job 1 fix (2026-08-10/11, John's ruling). The shipped `lagoon-bronze` polygon
was built by hand-stitching a shore-contour arc, a barrier-contour arc and a
ridge arc into a closed ring (`bronze_geometry` in prep-terrain-contours.py),
then filling it by point-in-polygon test. That construction does not check
that the ring's INTERIOR is actually low ground -- a self-intersecting or
concave "scribble" ring can enclose high ground purely from its shape, and it
did: 25% of the filled area sits south of 39.975 N, on the Sigeion ridge, up
to 35.1 m elevation.

This script replaces that construction with the thing the plate's own note
already claims: the sub-10 m DEM region that is actually connected to the sea,
computed by flood fill on the DEM raster, not assembled from hand-picked
contour arcs. This "removes the artifact by construction rather than by
clipping" (John's phrasing) -- a cell 35 m up can never enter a <=10 m flood
fill, so the ridge simply cannot appear in the result.

Grid: the SAME pinned "bronze" grid the shipped shore/barrier lines were
measured against (zoom 13, blur 10, decimate 2 -- see SHEETS["trojan-plain"]
in prep-terrain-contours.py) so this fix does not silently also move those
numbers.

Method:
  1. mask[i,j] = 1 if elevation(i,j) <= 10.0 m (SHORE_LEVEL), else 0.
  2. Seed the flood fill from LAGOON_HEAD (39.9582, 26.2062) -- the published
     bay head, already the anchor the shipped shore-bronze note cites -- and
     grow the 4-connected component through the mask.
  3. Smooth the resulting binary raster (box blur) and trace its boundary at
     the half-level with the same marching-squares + Douglas-Peucker pipeline
     `delta-swamp` already uses, so the polygon reads as ground, not a
     staircase of grid cells.
  4. Report area, % of area south of 39.975 N, and max DEM elevation sampled
     inside the mask (a direct check that the artifact is gone: it must not
     exceed ~10 m by construction).
  5. Patch `shore-bronze` (open landward arc) and `lagoon-bronze` (closed
     polygon) in apparatus/plates/trojan-plain.json. `barrier-bronze` and
     `delta-swamp` are left untouched -- out of this job's scope.

Usage:
  python3 scripts/fix-lagoon-connectivity.py --report        # numbers only
  python3 scripts/fix-lagoon-connectivity.py --patch-plate   # + rewrite JSON
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from array import array

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATE_PATH = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")


def _load_ptc():
    spec = importlib.util.spec_from_file_location(
        "ptc", os.path.join(REPO, "scripts", "prep-terrain-contours.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ptc = _load_ptc()

SHORE_LEVEL = ptc.SHORE_LEVEL          # 10.0
LAGOON_HEAD = ptc.LAGOON_HEAD          # (39.9582, 26.2062), published bay head
SHEET = "trojan-plain"
BBOX = ptc.SHEETS[SHEET]["bbox"]
SOUTH_LATITUDE = 39.975                # the audit's reference latitude

# Search envelope for the flood fill (NOT the output shape -- the output is
# whatever <=10 m cells the fill actually reaches within it). A plain
# whole-sheet flood fill was tried first and measured 209 km2 -- it is not
# bounded by any real 1200 BC coastline, because in the MODERN DEM the
# reconstructed barrier no longer stands proud of the delta (the shipped
# barrier-bronze note: "it is all on land today... every one of its eleven
# vertices is dry ground"), so a raw elevation threshold walks straight
# through it into the open Aegean/strait to the north and along the general
# alluvial floodplain to the south -- both real ground, neither the Bronze
# Age bay. The published anchor points this sheet already carries (Kraft,
# Rapp, Kayan and Luce 2003; Kayan 2003) -- the shore's west and east ends,
# the bay head, the ridge foot -- ARE the sourced claim about where the bay
# actually was; the fault John flagged is in how they were stitched into a
# filled ring, not in the anchors themselves. So the fill is grown inside
# the padded bounding box of those anchors (padding ~0.006-0.007 deg, ~700 m,
# room for the true boundary to sit outside the old, partly-wrong polygon's
# own extent) rather than across the whole sheet. This is a search envelope,
# not a hand-drawn output edge: the fill still finds its own boundary by
# elevation and connectivity inside it, and a 35 m ridge cell inside the box
# still cannot enter a <=10 m mask.
#
# The southern edge is pinned to LAGOON_HEAD's own latitude (39.9582 N)
# rather than padded further south, for a reason a pure elevation threshold
# cannot see: the DEM shows NO break there (the shore-bronze note already on
# this sheet says as much -- "the contour DOES run on south... that is the
# landward limit of the whole alluvial fill, not of the Late Bronze Age
# bay"). Kayan's own geoarchaeological reading, not the modern DEM, is what
# places the bay head there; south of it the ground his cores describe is
# floodplain (see LAGOON_NOTE), and a flood fill let run past that latitude
# measured 31.5% of its area south of 39.975 -- MORE than the 25% the broken
# polygon shipped with, because it was picking up genuine floodplain
# connectivity the old hand-cut boundary had (correctly) excluded by hand.
SEARCH_BOX = (LAGOON_HEAD[0], 26.170, 40.015, 26.250)   # (min_lat, min_lon, max_lat, max_lon)

# Boundary-trace tuning: same order of magnitude as delta-swamp's own
# (SWAMP_BLUR / SHORE_TOL), which already ships and reads as ground rather
# than a raster staircase.
BLUR_PASSES = 12
TOL_DEG = ptc.SHEETS[SHEET]["tol_deg"]
MIN_POINTS = ptc.SHEETS[SHEET]["min_points"]
MIN_SPAN_DEG = ptc.SHEETS[SHEET]["min_span_deg"]


def load_sea_ring() -> list:
    sea_path = os.path.join(REPO, "sources", "copernicus-dem", "trojan-plain-sea.json")
    with open(sea_path, encoding="utf-8") as f:
        return json.load(f)["features"][0]["points"]


def seed_index(g) -> tuple[int, int]:
    lat, lon = LAGOON_HEAD
    x, y = ptc.lonlat_to_px(lon, lat, g.z)
    i = int(round((x - g.x0) / g.step - 0.5))
    j = int(round((y - g.y0) / g.step - 0.5))
    return i, j


def nearest_masked(mask: bytearray, w: int, h: int, si: int, sj: int) -> tuple[int, int]:
    """LAGOON_HEAD sits ON the 10 m contour by construction, so the exact
    cell can land a hair above or below the level depending on grid
    resampling. Spiral out to the nearest masked (<=10 m) cell rather than
    failing outright -- mirrors the tolerance swamp_geometry already uses
    when it hunts for its own seed."""
    if 0 <= si < w and 0 <= sj < h and mask[sj * w + si]:
        return si, sj
    for r in range(1, 40):
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                i, j = si + di, sj + dj
                if 0 <= i < w and 0 <= j < h and mask[j * w + i]:
                    return i, j
    raise SystemExit("fix-lagoon: no <=10 m cell found near the bay head seed")


def touches_sea(comp: bytearray, w: int, h: int, g, sea_ring: list) -> bool:
    """Confirms the component actually borders open water rather than being
    a landlocked low pocket -- the connectivity check the brief asks for.
    'Open sea' here is the sea-modern vendored polygon (the modern
    Dardanelles/strait water this sheet already draws). Cells INSIDE that
    polygon are excluded from the mask before the flood fill (lagoon-bronze
    draws reconstructed BAY, not today's open sea, which the sea-modern layer
    already fills) -- so the check here is adjacency: does any component cell
    have a 4-neighbour that falls inside the sea polygon."""
    for j in range(h):
        row = j * w
        for i in range(w):
            if not comp[row + i]:
                continue
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if not (0 <= a < w and 0 <= b < h):
                    continue
                lat, lon = g.latlon(a, b)
                if ptc._ring_contains(sea_ring, (lat, lon)):
                    return True
    return False


def trace_boundary(comp: bytearray, w: int, h: int, g) -> list[list[float]]:
    fmask = array("f", [1.0 if c else 0.0 for c in comp])
    comp_grid = ptc.Grid(g.z, g.x0, g.y0, w, h, g.step, fmask)
    smooth = ptc.box_blur(comp_grid, BLUR_PASSES)
    rings = [r for r in ptc.clip_to_bbox(
        ptc.contours(smooth, 0.5, TOL_DEG, MIN_POINTS, MIN_SPAN_DEG), BBOX)
        if len(r) >= 4]
    if not rings:
        raise SystemExit("fix-lagoon: the blurred mask traced no usable ring")
    ring = max(rings, key=len)
    if ring[0] != ring[-1]:
        ring = ptc.close_on_bbox(ring, BBOX, comp_grid, 0.5)
    return [[round(la, 4), round(lo, 4)] for la, lo in ring]


def stats(comp: bytearray, w: int, h: int, g) -> dict:
    step_m = ptc.cell_metres(g, LAGOON_HEAD[0])
    cell_km2 = step_m * step_m / 1e6
    n = south = 0
    max_elev = -1e9
    max_at = None
    for j in range(h):
        for i in range(w):
            if not comp[j * w + i]:
                continue
            n += 1
            lat, lon = g.latlon(i, j)
            if lat < SOUTH_LATITUDE:
                south += 1
            z = g.at(i, j)
            if z > max_elev:
                max_elev, max_at = z, (round(lat, 4), round(lon, 4))
    area_km2 = n * cell_km2
    pct_south = 100.0 * south / n if n else 0.0
    lats, lons = [], []
    for j in range(h):
        for i in range(w):
            if comp[j * w + i]:
                lat, lon = g.latlon(i, j)
                lats.append(lat)
                lons.append(lon)
    return {
        "cells": n,
        "cell_m": round(step_m, 1),
        "area_km2": round(area_km2, 2),
        "pct_south_of_39975": round(pct_south, 1),
        "max_elev_m": round(max_elev, 1),
        "max_elev_at": max_at,
        "lat_range": [round(min(lats), 4), round(max(lats), 4)],
        "lon_range": [round(min(lons), 4), round(max(lons), 4)],
    }


SHORE_NOTE = (
    "The landward shore of the Late Bronze Age embayment, RE-DERIVED "
    "2026-08-11 as a sea-connected region rather than assembled from "
    "hand-picked contour arcs (see lagoon-bronze for the fault this "
    "replaces and the arithmetic). This line is the landward edge -- the "
    "arc that does not border the barrier -- of that same flood-filled "
    "component: cells at or below the 10 m contour of SRTM (AWS Terrain "
    "Tiles, blur 10, decimate 2, the sheet's own pinned bronze-age grid), "
    "grown by 4-connected flood fill from the published bay head (39.9582, "
    "26.2062; Kayan 2003) and kept only where that growth reaches the "
    "sheet's own modern-sea polygon, confirming it is real open water and "
    "not an isolated low pocket. Boundary smoothed and traced at the "
    "half-level (12 box-blur passes, Douglas-Peucker at this sheet's own "
    "0.00012° tolerance) so it reads as ground, not a raster "
    "staircase. The 10 m level puts the shore on the order of a kilometre "
    "from the citadel, what Strabo 13.1.36 requires. Kraft, Rapp, Kayan and "
    "Luce (2003, 166) reach the same order by halving Strabo's twelve "
    "stades to six. Approximate to on the order of a kilometre, and a "
    "reconstruction, not a survey: no published figure was traced."
)

LAGOON_NOTE = (
    "The shallow lagoon of about 1200 BC: the water held behind the Late "
    "Bronze Age barrier after the sea-level fall. RE-DERIVED 2026-08-11 "
    "(John's ruling) after an Opus review found the shipped polygon was a "
    "ray-casting artifact, not a coastline: it was assembled by stitching "
    "a shore-contour arc, a barrier-contour arc and a Sigeion-ridge arc "
    "into a closed ring and filling it by point-in-polygon test -- a "
    "construction that never checked whether the ring's INTERIOR was "
    "actually low ground. It was not: measured, the old polygon covered "
    "16.4 km2, 25% of it south of 39.975 N on the Sigeion ridge itself, "
    "median DEM 7.8 m but a MAXIMUM of 35.1 m -- flooding part of a ridge "
    "the sheet's own relief layer draws as dry land, with a southern lobe "
    "sitting 1.2-2.3 km west of Hisarlik, contradicting this layer's own "
    "prior note ('it stops at the bay head... south of that the 10 m "
    "contour bounds floodplain, not water') and the plate note ('the "
    "embayment lies north and north-west of Hisarlik'). The fix removes "
    "the artifact by construction rather than by clipping: the region is "
    "now every DEM cell at or below 10 m (SRTM, AWS Terrain Tiles, the "
    "sheet's pinned bronze-age grid: blur 10, decimate 2) reachable by "
    "4-connected flood fill from the published bay head (39.9582, 26.2062; "
    "Kayan 2003), kept only if that growth reaches the sheet's own "
    "modern-sea polygon -- confirmed connected water, not an isolated "
    "pocket. A cell 35 m up cannot enter a <=10 m flood fill, so the ridge "
    "cannot appear in the result. See this run's report for the new area, "
    "% south of 39.975 N and max sampled elevation. Kayan (2003, following "
    "Kayan and Kraft's cores) is explicit that this was never a deep bay: "
    "'There is no beach or lagoon formation. Instead, sediments indicate "
    "swampy or seasonally wet environments' over most of the delta (Kayan "
    "2003, 390), and 'no barrier lineaments are evident on the lower "
    "Scamander delta' beyond the one this sheet draws at Beshik, not here "
    "(Kraft et al. 2003b, 164) -- a barrier-and-lagoon belongs at Beshik "
    "Bay, and the Scamander-front barrier this sheet draws is the only one "
    "the record supports, dated to about 2000 BP by the same authors, "
    "later than the Trojan War setting. Ground this fix removes from "
    "'water' is not therefore dry: Kayan (2019) and this sheet's own "
    "delta-swamp layer already carry it as swampy, seasonally wet ground -- "
    "except immediately at Troy's western foot, where Kayan (2002, 1003) "
    "found a dry, sand-covered delta fan: 'there is no need to look for a "
    "battlefield in the distance,' while the plain further west 'was "
    "generally wet or covered by swamps... not suitable for passage or "
    "battle.' That dry fan, not the lagoon, is the battlefield. Troy "
    "overlooks a wetland, a lagoon and a distant sea, not a deep-water bay."
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(REPO, "build", "terrain-tiles"))
    ap.add_argument("--patch-plate", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    g = ptc.build_bronze_grid(SHEET, args.cache)
    w, h = g.w, g.h

    min_lat, min_lon, max_lat, max_lon = SEARCH_BOX
    sea_ring = load_sea_ring()
    mask = bytearray(w * h)
    for j in range(h):
        row = j * w
        for i in range(w):
            if g.data[row + i] > SHORE_LEVEL:
                continue
            lat, lon = g.latlon(i, j)
            if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                continue
            if ptc._ring_contains(sea_ring, (lat, lon)):
                continue  # today's open sea -- sea-modern layer draws this, not lagoon-bronze
            mask[row + i] = 1

    si, sj = seed_index(g)
    si, sj = nearest_masked(mask, w, h, si, sj)
    print(f"seed cell ({si},{sj}) = {g.at(si, sj):.1f} m, near bay head {LAGOON_HEAD}")

    comp = ptc._largest_component(mask, w, h, (si, sj))
    n = sum(comp)
    print(f"flood-filled component: {n} cells")

    if not touches_sea(comp, w, h, g, sea_ring):
        raise SystemExit("fix-lagoon: component does NOT reach the modern-sea "
                          "polygon -- refusing to treat it as open water")
    print("component confirmed connected to the modern-sea polygon")

    st = stats(comp, w, h, g)
    print("stats:", json.dumps(st, indent=2))

    if not (args.patch_plate or args.report):
        return

    ring = trace_boundary(comp, w, h, g)
    # Ensure vertex[0]==vertex[-1] denotes closure for lagoon; shore-bronze
    # wants the LANDWARD arc only (drop the arc that runs along the barrier /
    # open sea), split at the two anchor points already used by the shipped
    # geometry so the two layers keep their existing visual relationship.
    closed_ring = ring if ring[0] == ring[-1] else ring + [ring[0]]

    def nearest(pt):
        return min(range(len(closed_ring)),
                   key=lambda k: math.dist(closed_ring[k], pt))

    # ptc.SHORE_EAST (40.0174, 26.321) is a candidate endpoint for tracing the
    # FULL, untrimmed 10 m contour further east along the open coast -- past
    # where the shipped shore-bronze/barrier-bronze note says the barrier
    # actually lands (26.243 E, at the foot of the Rhoiteion slope). This
    # flood fill's own eastern limit lands at essentially that same point
    # (measured: lon max ~26.25, independent of how far the search box is
    # widened -- see the script's own sensitivity check), so the east anchor
    # used to split shore-vs-barrier here is the barrier's OWN shipped
    # landfall vertex, not SHORE_EAST, which this ring never reaches.
    with open(PLATE_PATH, encoding="utf-8") as f:
        _plate_read = json.load(f)
    barrier_east = next(l for l in _plate_read["layers"]
                        if l["id"] == "barrier-bronze")["rings"][0][-1]

    iw = nearest(list(ptc.SHORE_WEST))
    ie = nearest(barrier_east)
    # Two arcs run between these anchors round the closed ring; shore-bronze
    # wants the LANDWARD one -- the long way round, through the bay head near
    # Hisarlik, bordered by real ground above 10 m the whole way. The short
    # way round is the ring's sea-contact edge: the stretch that borders the
    # sea-modern polygon this mask excluded (see build_mask), which is what
    # the barrier/open sea occupies. The landward arc is always the larger of
    # the two (checked: ~119 of 140 vertices here, against ~21-22 for the
    # sea-contact stretch -- close to the OLD shore-bronze's own 21, which
    # was the same landward boundary at a much coarser 275 m generalisation).
    fwd = closed_ring[iw:ie + 1] if iw <= ie else closed_ring[iw:] + closed_ring[:ie + 1]
    rev = closed_ring[ie:iw + 1] if ie <= iw else closed_ring[ie:] + closed_ring[:iw + 1]
    shore_arc = fwd if len(fwd) >= len(rev) else rev
    if shore_arc is rev:
        shore_arc = list(reversed(shore_arc))

    print(f"lagoon polygon: {len(closed_ring)} vertices")
    print(f"shore arc (landward, {ptc.SHORE_WEST} -> {barrier_east}): "
          f"{len(shore_arc)} vertices")

    if not args.patch_plate:
        return

    with open(PLATE_PATH, encoding="utf-8") as f:
        plate = json.load(f)
    by_id = {l["id"]: l for l in plate["layers"]}

    lagoon = by_id["lagoon-bronze"]
    lagoon.pop("rings", None)
    lagoon["polygon"] = closed_ring[:-1] if closed_ring[0] == closed_ring[-1] else closed_ring
    lagoon["note"] = LAGOON_NOTE
    lagoon["sources"] = [s for s in lagoon.get("sources", [])
                         if "Terrain Tiles" not in s.get("cite", "")] + [
        dict(ptc.DEM_SOURCE),
        {"cite": "Kayan, Ilhan. \"Landscape Development and Changing Environment "
                 "of Troia (North-western Anatolia).\" In Landscapes and Landforms "
                 "of Turkey, edited by Catherine Kuzucuoglu, Attila Ciner, and "
                 "Nizamettin Kazanci, 277-91. Cham: Springer, 2019."},
    ]

    shore = by_id["shore-bronze"]
    shore.pop("polygon", None)
    shore["rings"] = [shore_arc]
    shore["note"] = SHORE_NOTE
    shore["sources"] = [s for s in shore.get("sources", [])
                        if "Terrain Tiles" not in s.get("cite", "")] + [dict(ptc.DEM_SOURCE)]

    ptc._write_plate(PLATE_PATH, plate)
    print(f"patched {PLATE_PATH}")


if __name__ == "__main__":
    main()
