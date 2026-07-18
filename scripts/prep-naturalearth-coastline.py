#!/usr/bin/env python3
"""Vendor + simplify Natural Earth 1:50m land polygons for the Mediterranean
basin, for shared/lib/scenemap.ts's build-time SVG scene-maps.

Source: Natural Earth 1:50m Cultural/Physical Vectors, "land" (ne_50m_land),
public domain (https://www.naturalearthdata.com/about/terms-of-use/ — "No
permission is needed to use Natural Earth."). Fetched from the project's own
GitHub mirror (stdlib urllib, no npm/pip deps):
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson

Pipeline (stdlib only — json, math, urllib):
  1. Fetch (or reuse a cached copy passed via --input) the world land GeoJSON.
  2. Clip every ring to the Mediterranean bbox (8W-38E, 30N-46N) with
     Sutherland-Hodgman polygon clipping, so landmasses that extend beyond the
     box (Europe, Africa, Asia Minor) are cut off cleanly at the box edge
     rather than dropped or left open — this is what gives the "suggestive,
     not cartographic" abstracted-headland look in the approved mocks.
  3. Simplify each clipped ring with hand-rolled Douglas-Peucker (degrees
     tolerance, tuned below to hit the <150KB budget while staying
     recognizable at the ~300-400px panel render size).
  4. Drop rings too small to read at that size (post-simplify point count < 3,
     or bbox diagonal below a noise floor).
  5. Reorder each point from GeoJSON's [lon, lat] to this project's [lat, lon]
     convention (matches apparatus/places.json `coords`), round to 3 decimals
     (~111m — far finer than this map will ever render), and emit compact
     (no-whitespace) JSON.

Output: sources/naturalearth/mediterranean-coastline.json
  { "bbox": [minLon, minLat, maxLon, maxLat], "rings": [[[lat, lon], ...], ...] }

Usage:
  python3 scripts/prep-naturalearth-coastline.py [--input path/to/cached.geojson]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_50m_land.geojson"
)

# Mediterranean basin crop, per the scenemap brief.
MIN_LON, MAX_LON = -8.0, 38.0
MIN_LAT, MAX_LAT = 30.0, 46.0

SIMPLIFY_TOLERANCE_DEG = 0.01  # Douglas-Peucker tolerance, in degrees.
MIN_RING_POINTS = 3
MIN_RING_DIAGONAL_DEG = 0.05  # drop islands/specks smaller than this on a side

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sources", "naturalearth", "mediterranean-coastline.json",
)


def fetch_geojson(input_path: str | None) -> dict:
    if input_path:
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Sutherland-Hodgman polygon clipping against the Mediterranean bbox ──────

def _clip_edge(points: list[tuple[float, float]], inside, intersect) -> list[tuple[float, float]]:
    if not points:
        return []
    out: list[tuple[float, float]] = []
    prev = points[-1]
    prev_in = inside(prev)
    for cur in points:
        cur_in = inside(cur)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append(cur)
        elif prev_in:
            out.append(intersect(prev, cur))
        prev, prev_in = cur, cur_in
    return out


def clip_ring_to_bbox(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Clips a (lon, lat) ring to [MIN_LON, MAX_LON] x [MIN_LAT, MAX_LAT]."""
    pts = ring

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    # Left (lon >= MIN_LON)
    pts = _clip_edge(
        pts,
        lambda p: p[0] >= MIN_LON,
        lambda a, b: lerp(a, b, (MIN_LON - a[0]) / (b[0] - a[0])) if b[0] != a[0] else a,
    )
    # Right (lon <= MAX_LON)
    pts = _clip_edge(
        pts,
        lambda p: p[0] <= MAX_LON,
        lambda a, b: lerp(a, b, (MAX_LON - a[0]) / (b[0] - a[0])) if b[0] != a[0] else a,
    )
    # Bottom (lat >= MIN_LAT)
    pts = _clip_edge(
        pts,
        lambda p: p[1] >= MIN_LAT,
        lambda a, b: lerp(a, b, (MIN_LAT - a[1]) / (b[1] - a[1])) if b[1] != a[1] else a,
    )
    # Top (lat <= MAX_LAT)
    pts = _clip_edge(
        pts,
        lambda p: p[1] <= MAX_LAT,
        lambda a, b: lerp(a, b, (MAX_LAT - a[1]) / (b[1] - a[1])) if b[1] != a[1] else a,
    )
    return pts


# ── Hand-rolled Douglas-Peucker ──────────────────────────────────────────────

def _perp_distance(pt, a, b) -> float:
    if a == b:
        return math.hypot(pt[0] - a[0], pt[1] - a[1])
    num = abs((b[0] - a[0]) * (a[1] - pt[1]) - (a[0] - pt[0]) * (b[1] - a[1]))
    den = math.hypot(b[0] - a[0], b[1] - a[1])
    return num / den


def douglas_peucker(points: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    if len(points) < 3:
        return points
    dmax, index = 0.0, 0
    a, b = points[0], points[-1]
    for i in range(1, len(points) - 1):
        d = _perp_distance(points[i], a, b)
        if d > dmax:
            dmax, index = d, i
    if dmax > tolerance:
        left = douglas_peucker(points[: index + 1], tolerance)
        right = douglas_peucker(points[index:], tolerance)
        return left[:-1] + right
    return [a, b]


def ring_diagonal(ring: list[tuple[float, float]]) -> float:
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return math.hypot(max(lons) - min(lons), max(lats) - min(lats))


def iter_rings(geometry: dict):
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    if gtype == "Polygon":
        for ring in coords:
            yield ring
    elif gtype == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                yield ring


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to a cached ne_50m_land.geojson (skips the fetch)")
    args = parser.parse_args()

    data = fetch_geojson(args.input)

    out_rings: list[list[list[float]]] = []
    for feature in data["features"]:
        geom = feature.get("geometry")
        if not geom:
            continue
        for ring in iter_rings(geom):
            pts = [(float(x), float(y)) for x, y in ring]
            clipped = clip_ring_to_bbox(pts)
            if len(clipped) < MIN_RING_POINTS:
                continue
            simplified = douglas_peucker(clipped, SIMPLIFY_TOLERANCE_DEG)
            if len(simplified) < MIN_RING_POINTS:
                continue
            if ring_diagonal(simplified) < MIN_RING_DIAGONAL_DEG:
                continue
            # [lon, lat] -> [lat, lon] (this project's coords convention),
            # rounded to 3 decimals (~111m).
            out_rings.append([[round(lat, 3), round(lon, 3)] for lon, lat in simplified])

    payload = {
        "bbox": [MIN_LON, MIN_LAT, MAX_LON, MAX_LAT],
        "rings": out_rings,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    text = json.dumps(payload, separators=(",", ":"))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(text)

    size_kb = len(text.encode("utf-8")) / 1024
    print(f"wrote {OUT_PATH}: {len(out_rings)} rings, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
