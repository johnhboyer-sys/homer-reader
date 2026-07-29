#!/usr/bin/env python3
"""Derive real contour lines for the Troy plates from a real DEM.

Source: AWS Open Data "Terrain Tiles" (the Tilezen/Mapzen `elevation-tiles-prod`
bucket), terrarium-encoded PNG tiles, no key and no auth:

    https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png

Over the Troad the underlying DEM is SRTM (NASA/NGA, distributed by the USGS,
no domestic copyright asserted; the USGS asks to be credited on
redistribution). Terrarium encodes height in the three colour channels:

    height_m = (R * 256 + G + B / 256) - 32768

Pipeline (stdlib only -- json, math, zlib, array, subprocess; the PNG decoder
below is hand-rolled so this script adds no dependency):

  1. Fetch the terrarium tiles covering a bbox at a chosen zoom, via `curl`
     (Python's urllib fails SSL verification in this environment), caching
     each tile so re-runs are offline and deterministic.
  2. Decode and mosaic them into one height grid, then clip to the bbox.
  3. Box-blur and optionally decimate -- a contour traced at the DEM's raw
     30 m posting is a hairball at a 200 m/px sheet; smoothing is what turns
     a DEM into a map.
  4. Trace contours at the requested levels with marching squares, stitching
     the per-cell segments into closed rings and open lines.
  5. Simplify each line with Douglas-Peucker (tolerance in degrees) so the
     plate JSON stays reviewable by a human.
  6. Convert Web-Mercator pixel coordinates to this project's [lat, lon]
     convention (matches apparatus/places.json `coords`) and write both a
     vendored derived product under sources/terrain-tiles/ and, with
     --patch-plates, the relief geometry inside apparatus/plates/*.json.

The vendored product is the DERIVED contour geometry, not the tiles: hundreds
of PNGs have no business in a git history, and the contours are what the
plates consume.

Usage:
  python3 scripts/prep-terrain-contours.py --stats          # elevation report
  python3 scripts/prep-terrain-contours.py                  # write sources/
  python3 scripts/prep-terrain-contours.py --patch-plates   # + edit the plates
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import zlib
from array import array
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
DEFAULT_CACHE = os.path.join(REPO, "build", "terrain-tiles")
OUT_DIR = os.path.join(REPO, "sources", "terrain-tiles")

TILE_PX = 256


# ── Web Mercator ────────────────────────────────────────────────────────────

def lonlat_to_px(lon: float, lat: float, z: int) -> tuple[float, float]:
    n = TILE_PX * (2 ** z)
    x = (lon + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def px_to_lonlat(x: float, y: float, z: int) -> tuple[float, float]:
    n = TILE_PX * (2 ** z)
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


# ── Hand-rolled PNG decode (8-bit, non-interlaced, truecolour) ───────────────

def decode_png(data: bytes) -> tuple[int, int, int, bytes]:
    """Returns (width, height, channels, raw pixel bytes). Terrarium tiles are
    8-bit RGB or RGBA, non-interlaced, which is all this handles."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    width = height = channels = 0
    idat = bytearray()
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width = int.from_bytes(body[0:4], "big")
            height = int.from_bytes(body[4:8], "big")
            bit_depth, colour_type = body[8], body[9]
            if bit_depth != 8 or body[12] != 0:
                raise ValueError(f"unsupported PNG (depth {bit_depth}, interlace {body[12]})")
            channels = {2: 3, 6: 4}.get(colour_type, 0)
            if not channels:
                raise ValueError(f"unsupported PNG colour type {colour_type}")
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))

    bpp = channels
    stride = width * bpp
    out = bytearray(stride * height)
    prev = bytes(stride)
    p = 0
    for row in range(height):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 0:
            pass
        elif ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                b = prev[i]
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        else:
            raise ValueError(f"bad PNG filter type {ft}")
        out[row * stride:(row + 1) * stride] = line
        prev = bytes(line)
    return width, height, channels, bytes(out)


# ── Tile fetch + mosaic ─────────────────────────────────────────────────────

def fetch_tile(z: int, x: int, y: int, cache: str) -> bytes:
    path = os.path.join(cache, str(z), str(x), f"{y}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url = TILE_URL.format(z=z, x=x, y=y)
    # urllib fails SSL verification in this environment; curl works.
    subprocess.run(
        ["curl", "-sS", "--fail", "--retry", "3", "-o", path, url],
        check=True,
    )
    with open(path, "rb") as f:
        return f.read()


class Grid:
    """A height grid in Web-Mercator pixel space at zoom `z`. Sample (i, j)
    sits at global pixel (x0 + i * step + step/2, y0 + j * step + step/2)."""

    def __init__(self, z: int, x0: int, y0: int, w: int, h: int, step: int, data: array):
        self.z, self.x0, self.y0 = z, x0, y0
        self.w, self.h, self.step = w, h, step
        self.data = data

    def at(self, i: int, j: int) -> float:
        return self.data[j * self.w + i]

    def latlon(self, fi: float, fj: float) -> tuple[float, float]:
        x = self.x0 + (fi + 0.5) * self.step
        y = self.y0 + (fj + 0.5) * self.step
        lon, lat = px_to_lonlat(x, y, self.z)
        return lat, lon


def build_grid(z: int, bbox: tuple[float, float, float, float], cache: str,
               verbose: bool = True) -> Grid:
    """bbox is [minLat, minLon, maxLat, maxLon] (this project's order)."""
    min_lat, min_lon, max_lat, max_lon = bbox
    x_lo, y_lo = lonlat_to_px(min_lon, max_lat, z)
    x_hi, y_hi = lonlat_to_px(max_lon, min_lat, z)
    x0, y0 = int(math.floor(x_lo)), int(math.floor(y_lo))
    x1, y1 = int(math.ceil(x_hi)), int(math.ceil(y_hi))
    w, h = x1 - x0, y1 - y0
    data = array("f", bytes(4 * w * h))

    tx0, tx1 = x0 // TILE_PX, (x1 - 1) // TILE_PX
    ty0, ty1 = y0 // TILE_PX, (y1 - 1) // TILE_PX
    total = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    done = 0
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            png = fetch_tile(z, tx, ty, cache)
            tw, th, ch, px = decode_png(png)
            for row in range(th):
                gy = ty * TILE_PX + row - y0
                if not (0 <= gy < h):
                    continue
                base = row * tw * ch
                dst = gy * w
                for col in range(tw):
                    gx = tx * TILE_PX + col - x0
                    if not (0 <= gx < w):
                        continue
                    o = base + col * ch
                    data[dst + gx] = (px[o] * 256 + px[o + 1] + px[o + 2] / 256.0) - 32768.0
            done += 1
            if verbose and done % 20 == 0:
                print(f"  decoded {done}/{total} tiles")
    return Grid(z, x0, y0, w, h, 1, data)


# ── Smoothing and decimation ────────────────────────────────────────────────

def box_blur(g: Grid, passes: int) -> Grid:
    w, h = g.w, g.h
    src = g.data
    for _ in range(passes):
        tmp = array("f", bytes(4 * w * h))
        for j in range(h):                       # horizontal
            row = j * w
            for i in range(w):
                a = src[row + (i - 1 if i > 0 else 0)]
                b = src[row + i]
                c = src[row + (i + 1 if i < w - 1 else w - 1)]
                tmp[row + i] = (a + b + c) / 3.0
        out = array("f", bytes(4 * w * h))
        for j in range(h):                       # vertical
            up = (j - 1 if j > 0 else 0) * w
            mid = j * w
            dn = (j + 1 if j < h - 1 else h - 1) * w
            for i in range(w):
                out[mid + i] = (tmp[up + i] + tmp[mid + i] + tmp[dn + i]) / 3.0
        src = out
    return Grid(g.z, g.x0, g.y0, w, h, g.step, src)


def decimate(g: Grid, k: int) -> Grid:
    """Mean-pools k x k blocks. Mean, not sample: a sampled decimation drops
    summits, and the sanity check is a summit height."""
    if k <= 1:
        return g
    w, h = g.w // k, g.h // k
    out = array("f", bytes(4 * w * h))
    for j in range(h):
        for i in range(w):
            s = 0.0
            for dj in range(k):
                row = (j * k + dj) * g.w + i * k
                for di in range(k):
                    s += g.data[row + di]
            out[j * w + i] = s / (k * k)
    return Grid(g.z, g.x0, g.y0, w, h, g.step * k, out)


# ── Marching squares ────────────────────────────────────────────────────────

# Segment table, keyed by the 4-bit corner mask
# (1 = top-left above level, 2 = top-right, 4 = bottom-right, 8 = bottom-left).
# Edges: 'T' top, 'R' right, 'B' bottom, 'L' left. Segments are directed so
# that ground above the level lies to the left of travel, which makes the
# stitching below a simple follow-the-arrow walk.
_CASES: dict[int, tuple[tuple[str, str], ...]] = {
    0: (), 15: (),
    1: (("T", "L"),),
    2: (("R", "T"),),
    3: (("R", "L"),),
    4: (("B", "R"),),
    5: (("T", "L"), ("B", "R")),      # saddle
    6: (("B", "T"),),
    7: (("B", "L"),),
    8: (("L", "B"),),
    9: (("T", "B"),),
    10: (("R", "T"), ("L", "B")),     # saddle
    11: (("R", "B"),),
    12: (("L", "R"),),
    13: (("T", "R"),),
    14: (("L", "T"),),
}


def trace_contour(g: Grid, level: float) -> list[list[tuple[float, float]]]:
    """Returns polylines in grid (fi, fj) coordinates. Closed rings repeat
    their first point as their last."""
    w, h = g.w, g.h
    d = g.data
    segs: list[tuple[tuple[float, float], tuple[float, float]]] = []

    def interp(v0: float, v1: float) -> float:
        if v1 == v0:
            return 0.5
        return (level - v0) / (v1 - v0)

    for j in range(h - 1):
        r0, r1 = j * w, (j + 1) * w
        for i in range(w - 1):
            a, b = d[r0 + i], d[r0 + i + 1]
            c, e = d[r1 + i + 1], d[r1 + i]
            mask = (1 if a >= level else 0) | (2 if b >= level else 0) \
                | (4 if c >= level else 0) | (8 if e >= level else 0)
            if mask in (0, 15):
                continue
            cases = _CASES[mask]
            if mask in (5, 10):
                centre = (a + b + c + e) / 4.0
                if (centre >= level) != (mask == 5):
                    cases = (cases[0][::-1], cases[1][::-1])
            pts = {
                "T": (i + interp(a, b), float(j)),
                "R": (float(i + 1), j + interp(b, c)),
                "B": (i + interp(e, c), float(j + 1)),
                "L": (float(i), j + interp(a, e)),
            }
            for s, t in cases:
                segs.append((pts[s], pts[t]))

    if not segs:
        return []

    def key(p: tuple[float, float]) -> tuple[int, int]:
        return (round(p[0] * 4096), round(p[1] * 4096))

    outgoing: dict[tuple[int, int], list[int]] = defaultdict(list)
    incoming: set[tuple[int, int]] = set()
    for n, (p, q) in enumerate(segs):
        outgoing[key(p)].append(n)
        incoming.add(key(q))

    used = [False] * len(segs)
    lines: list[list[tuple[float, float]]] = []

    def walk(start: int) -> list[tuple[float, float]]:
        chain = [segs[start][0], segs[start][1]]
        used[start] = True
        cur = key(segs[start][1])
        while True:
            nxt = [n for n in outgoing.get(cur, ()) if not used[n]]
            if not nxt:
                return chain
            n = nxt[0]
            used[n] = True
            chain.append(segs[n][1])
            cur = key(segs[n][1])
            if cur == key(chain[0]):
                return chain

    # Open lines first (they start where nothing arrives), then closed rings.
    for n, (p, _q) in enumerate(segs):
        if not used[n] and key(p) not in incoming:
            lines.append(walk(n))
    for n in range(len(segs)):
        if not used[n]:
            lines.append(walk(n))
    return lines


# ── Douglas-Peucker ─────────────────────────────────────────────────────────

def _perp(pt, a, b) -> float:
    if a == b:
        return math.hypot(pt[0] - a[0], pt[1] - a[1])
    num = abs((b[0] - a[0]) * (a[1] - pt[1]) - (a[0] - pt[0]) * (b[1] - a[1]))
    return num / math.hypot(b[0] - a[0], b[1] - a[1])


def douglas_peucker(points: list, tol: float) -> list:
    if len(points) < 3:
        return points
    stack = [(0, len(points) - 1)]
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    while stack:
        lo, hi = stack.pop()
        if hi - lo < 2:
            continue
        dmax, idx = 0.0, lo
        a, b = points[lo], points[hi]
        for i in range(lo + 1, hi):
            dist = _perp(points[i], a, b)
            if dist > dmax:
                dmax, idx = dist, i
        if dmax > tol:
            keep[idx] = True
            stack.append((lo, idx))
            stack.append((idx, hi))
    return [p for p, k in zip(points, keep) if k]


# ── Contour extraction to [lat, lon] ────────────────────────────────────────

def contours(g: Grid, level: float, tol_deg: float, min_points: int,
             min_span_deg: float, decimals: int = 4) -> list[list[list[float]]]:
    """One contour level, as [lat, lon] polylines.

    The order of operations matters and cost an afternoon: the tracer's greedy
    walk breaks a contour into several chains wherever it re-enters a cell it
    has already used, so the chains MUST be sewn back together (on exact
    endpoint equality -- adjacent cells compute a shared edge crossing from the
    same two heights, so the ends match bit for bit) BEFORE anything is
    simplified or filtered. Filtering first drops the short connector chains
    and leaves a ring open by one cell, which then gets closed against the
    frame and draws a wedge of false upland across open sea."""
    raw = [[list(g.latlon(fi, fj)) for fi, fj in line] for line in trace_contour(g, level)]
    out: list[list[list[float]]] = []
    for line in join_runs(raw, 0.0):
        closed = len(line) > 3 and line[0] == line[-1]
        simp = douglas_peucker(line, tol_deg)
        if closed and len(simp) >= 3 and simp[0] != simp[-1]:
            simp.append(simp[0])
        if len(simp) < min_points:
            continue
        lats = [p[0] for p in simp]
        lons = [p[1] for p in simp]
        if math.hypot(max(lats) - min(lats), max(lons) - min(lons)) < min_span_deg:
            continue
        out.append([[round(la, decimals), round(lo, decimals)] for la, lo in simp])
    return out


def clip_to_bbox(lines: list[list[list[float]]],
                 bbox: tuple[float, float, float, float]) -> list[list[list[float]]]:
    """Cuts each line at the sheet's neatline. A contour running off the sheet
    is split there, with the crossing interpolated so the cut end lands exactly
    on the edge -- which is what lets close_on_bbox below sew it shut again.
    The plate validator rejects any vertex outside the bbox, so this is not
    optional."""
    min_lat, min_lon, max_lat, max_lon = bbox

    def inside(p) -> bool:
        return min_lat <= p[0] <= max_lat and min_lon <= p[1] <= max_lon

    def crossing(a, b):
        """The point where segment a->b meets the rectangle, walking from a."""
        best = 1.0
        for lo_bound, hi_bound, axis in ((min_lat, max_lat, 0), (min_lon, max_lon, 1)):
            for bound in (lo_bound, hi_bound):
                if a[axis] == b[axis]:
                    continue
                t = (bound - a[axis]) / (b[axis] - a[axis])
                if not (0.0 < t <= 1.0):
                    continue
                p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
                other = 1 - axis
                lo2, hi2 = (min_lat, max_lat) if other == 0 else (min_lon, max_lon)
                if lo2 - 1e-9 <= p[other] <= hi2 + 1e-9 and t < best:
                    best = t
        return [a[0] + (b[0] - a[0]) * best, a[1] + (b[1] - a[1]) * best]

    out: list[list[list[float]]] = []
    for line in lines:
        run: list[list[float]] = []
        prev = None
        for p in line:
            if inside(p):
                if prev is not None and not inside(prev):
                    run.append(crossing(p, prev))
                run.append(list(p))
            else:
                if prev is not None and inside(prev):
                    run.append(crossing(prev, p))
                    if len(run) >= 2:
                        out.append(run)
                run = []
            prev = p
        if len(run) >= 2:
            out.append(run)
    return out


# ── Closing an open contour against the neatline ────────────────────────────

def _perimeter_s(p, bbox) -> float:
    """Position of a point on the sheet's rectangular boundary, 0..4,
    anticlockwise from the south-west corner."""
    min_lat, min_lon, max_lat, max_lon = bbox
    dlat = max_lat - min_lat
    dlon = max_lon - min_lon
    la, lo = p
    d_s, d_n = abs(la - min_lat), abs(max_lat - la)
    d_w, d_e = abs(lo - min_lon), abs(max_lon - lo)
    m = min(d_s, d_n, d_w, d_e)
    if m == d_s:
        return 0.0 + (lo - min_lon) / dlon
    if m == d_e:
        return 1.0 + (la - min_lat) / dlat
    if m == d_n:
        return 2.0 + (max_lon - lo) / dlon
    return 3.0 + (max_lat - la) / dlat


def _corner(i: int, bbox) -> list[float]:
    min_lat, min_lon, max_lat, max_lon = bbox
    return [[min_lat, min_lon], [min_lat, max_lon],
            [max_lat, max_lon], [max_lat, min_lon]][i % 4]


def _ring_contains(ring: list[list[float]], pt) -> bool:
    la, lo = pt
    c = False
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        if (a[0] > la) != (b[0] > la):
            x = (b[1] - a[1]) * (la - a[0]) / (b[0] - a[0]) + a[1]
            if lo < x:
                c = not c
    return c


def close_on_bbox(line: list[list[float]], bbox, g: Grid, level: float) -> list[list[float]]:
    """Sews an open contour shut along the neatline, on whichever side the
    ground is above `level`. A filled relief body has to be a closed ring, and
    a contour that leaves the sheet is closed by the frame -- exactly as a
    printed map does it."""
    if line[0] == line[-1]:
        return line
    s_end = _perimeter_s(line[-1], bbox)
    s_start = _perimeter_s(line[0], bbox)

    def walk(forward: bool) -> list[list[float]]:
        """Runs along the frame from the line's far end back to its start,
        picking up every corner passed on the way."""
        out = list(line)
        if forward:
            end = s_start if s_start > s_end else s_start + 4
            c = math.floor(s_end) + 1
            while c < end:
                out.append(_corner(c, bbox))
                c += 1
        else:
            end = s_start if s_start < s_end else s_start - 4
            c = math.ceil(s_end) - 1
            while c > end:
                out.append(_corner(c, bbox))
                c -= 1
        return out

    a, b = walk(True), walk(False)
    # Keep the closure that actually holds the high ground. The test is the
    # FRACTION of interior samples above `level`, not their mean (2026-07-29,
    # a defect the 50 m contour exposed): every point inside a contour body is
    # above the contour by definition, so the right closure scores near 1 and
    # its complement -- which contains the sea and all the lowland -- scores
    # low. The mean this replaced compared averages, and on the Troad sheet
    # the mean of the WHOLE SHEET is 148 m, so at 50 m a stray fragment closed
    # the long way round all four corners scored 148 > 50, won, and painted
    # the Aegean beige.
    return a if _interior_above(a, g, level)[0] >= _interior_above(b, g, level)[0] else b


def _interior_above(ring: list[list[float]], g: Grid, level: float,
                    samples: int = 1600) -> tuple[float, int]:
    """(fraction of interior samples at or above `level`, number of samples
    that landed inside). A thin sliver may catch nothing on the first grid, so
    the sampling is refined once before giving up."""
    lats = [p[0] for p in ring]
    lons = [p[1] for p in ring]
    lo_la, hi_la = min(lats), max(lats)
    lo_lo, hi_lo = min(lons), max(lons)
    for total_samples in (samples, samples * 9):
        above, n = 0, 0
        k = int(math.sqrt(total_samples)) or 1
        for a in range(1, k + 1):
            for b in range(1, k + 1):
                la = lo_la + (hi_la - lo_la) * a / (k + 1)
                lo = lo_lo + (hi_lo - lo_lo) * b / (k + 1)
                if not _ring_contains(ring, (la, lo)):
                    continue
                x, y = lonlat_to_px(lo, la, g.z)
                i = int(round((x - g.x0) / g.step - 0.5))
                j = int(round((y - g.y0) / g.step - 0.5))
                if 0 <= i < g.w and 0 <= j < g.h:
                    n += 1
                    if g.at(i, j) >= level:
                        above += 1
        if n:
            return above / n, n
    return 0.0, 0


def grid_stats(g: Grid) -> dict:
    d = g.data
    lo = min(d)
    hi = max(d)
    n = len(d)
    total = math.fsum(d)
    hi_i = d.index(hi)
    lat, lon = g.latlon(hi_i % g.w, hi_i // g.w)
    return {
        "samples": n,
        "min_m": round(lo, 1),
        "max_m": round(hi, 1),
        "mean_m": round(total / n, 1),
        "max_at": [round(lat, 4), round(lon, 4)],
        "sea_fraction": round(sum(1 for v in d if v <= 0.0) / n, 3),
    }




# ── Sheet definitions ───────────────────────────────────────────────────────
#
# Zoom is chosen against the sheet's own render scale, not maximised: a contour
# carrying detail finer than one screen pixel is noise in the diff and noise on
# the page.
#
#   troad        840 px across 2.15 deg lon (~183 km) -> 218 m/px on screen.
#                z11 = 76 m/px, a 3x oversample. z12 would quadruple the
#                download for detail the sheet cannot show.
#   trojan-plain 880 px across 0.28 deg lon (~24 km) -> 27 m/px on screen.
#                z13 = 19 m/px, which is also about SRTM's native 30 m posting
#                over Turkey -- past this the DEM has nothing more to give.
#
# Contour interval (REVISED 2026-07-29, the hypsometric lane). The first cut
# of these sheets drew five filled relief bodies on the plain and eleven on
# the Troad, every one of them the same flat tan under the same hachure
# texture -- a diagram OF terrain rather than terrain. The bands below are
# cut to be COLOURED, as a hypsometric ramp, so the interval is chosen for
# the number of visible steps it puts on the sheet, not for how many contour
# LINES stay legible:
#
#   troad        0-1749 m over 183 km. Non-linear: 50 and 100 m, then 100 m
#                to 400, then 200 m to the summit. Ten bands, so eleven
#                visible steps counting the lowland ground itself. The fine
#                low end is deliberate -- the poem happens between 0 and
#                300 m, and a linear 200 m interval washes all of it into one
#                flat field.
#   trojan-plain 0-376 m over 24 km, and the story is LOW relief: Hisarlik is
#                36 m, the Sigeion ridge 36 m, and the battlefield is the
#                floor between them. So the interval is 5 m to 30, then
#                widening steeply -- eleven bands, twelve steps, but with SIX
#                of them under 45 m. An even interval keyed to the sheet's
#                376 m maximum would put the whole subject of the sheet in
#                the palest two tints, which is how the first cut of this
#                ramp failed. 10 and 20 m stay in the set whatever else
#                moves: they are the levels the Bronze Age shore, barrier and
#                swamp are derived from (see bronze_geometry).
#
# `post_blur` is extra box-blur applied AFTER decimation, i.e. to the grid the
# contours are actually traced on. It exists because a contour is only as
# smooth as the ground under it: simplifying a line at 685 m (the Troad's
# tolerance) when the surface still carries 124 m wiggles does not generalise
# it, it turns every wiggle into a spike, and at a 3x zoom the Troad's relief
# read as torn paper. The rule of thumb these two sheets are tuned to is
# smoothing sigma at roughly half the simplification tolerance. The Bronze Age
# geometry is deliberately NOT taken from the post-blurred grid (see main) --
# it was derived against published measurements and must not move.

SHEETS: dict[str, dict] = {
    "troad": {
        "bbox": (38.95, 25.35, 40.6, 27.5),
        "zoom": 11,
        "blur": 4,
        "decimate": 2,
        "post_blur": 5,
        "tol_deg": 0.005,
        "min_points": 5,
        "min_span_deg": 0.07,
        "levels": [50, 100, 200, 300, 400, 600, 800, 1000, 1200, 1400],
    },
    "trojan-plain": {
        "bbox": (39.86, 26.1, 40.05, 26.38),
        "zoom": 13,
        "blur": 10,
        "decimate": 2,
        "post_blur": 2,
        "tol_deg": 0.0009,
        "min_points": 5,
        "min_span_deg": 0.012,
        "levels": [10, 15, 20, 25, 30, 40, 60, 100, 150, 200, 320],
    },
}

DEM_SOURCE = {
    "cite": "Terrain Tiles on AWS Open Data (Tilezen/Mapzen `elevation-tiles-prod`), terrarium-encoded SRTM. SRTM data courtesy of the U.S. Geological Survey.",
    "url": "https://registry.opendata.aws/terrain-tiles/",
}


def build_sheet(name: str, cache: str) -> tuple[Grid, dict]:
    spec = SHEETS[name]
    print(f"[{name}] grid at z{spec['zoom']} over {spec['bbox']}")
    g = build_grid(spec["zoom"], spec["bbox"], cache)
    raw = grid_stats(g)
    print(f"[{name}] raw {g.w}x{g.h}: {raw}")
    g = decimate(box_blur(g, spec["blur"]), spec["decimate"])
    sm = grid_stats(g)
    print(f"[{name}] smoothed+decimated {g.w}x{g.h}: {sm}")
    return g, {"raw": raw, "smoothed": sm}


def relief_grid(name: str, g: Grid) -> tuple[Grid, dict]:
    """The grid the RELIEF bands are traced on: `g` with `post_blur` further
    passes. Separate from `g` itself because the Bronze Age shore and barrier
    were derived against published measurements on the unblurred grid and must
    not move -- see the SHEETS comment."""
    passes = SHEETS[name].get("post_blur", 0)
    if not passes:
        return g, grid_stats(g)
    out = box_blur(g, passes)
    st = grid_stats(out)
    print(f"[{name}] +{passes} post-blur passes: {st}")
    return out, st


def sheet_lines(name: str, g: Grid, level: float, tol: float | None = None):
    spec = SHEETS[name]
    return clip_to_bbox(
        contours(g, level, tol if tol is not None else spec["tol_deg"],
                 spec["min_points"], spec["min_span_deg"]),
        spec["bbox"])


def _on_frame(p, bbox, eps: float = 2.5e-3) -> bool:
    min_lat, min_lon, max_lat, max_lon = bbox
    return (abs(p[0] - min_lat) < eps or abs(p[0] - max_lat) < eps
            or abs(p[1] - min_lon) < eps or abs(p[1] - max_lon) < eps)


def join_runs(lines: list, tol: float) -> list:
    """Sews contour runs that share an end back together. Marching squares
    breaks a chain at a saddle cell, leaving the two pieces ending a cell
    apart rather than at the same point, so the join is by proximity (`tol`
    is one and a half grid cells) and not by equality. Without this a piece
    gets closed against the frame on its own and draws a straight chord across
    open sea."""
    out = [list(map(list, ln)) for ln in lines]

    def near(p, q) -> bool:
        return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

    changed = True
    while changed:
        changed = False
        for i, a in enumerate(out):
            if near(a[0], a[-1]):
                continue                       # already a closed ring
            for j, b in enumerate(out):
                if i == j or near(b[0], b[-1]):
                    continue
                if near(a[-1], b[0]):
                    out[i] = a + b[1:]
                elif near(a[-1], b[-1]):
                    out[i] = a + b[::-1][1:]
                elif near(a[0], b[-1]):
                    out[i] = b + a[1:]
                elif near(a[0], b[0]):
                    out[i] = b[::-1] + a[1:]
                else:
                    continue
                out.pop(j)
                changed = True
                break
            if changed:
                break
    return out


def sheet_bodies(name: str, g: Grid, level: float) -> list[list[list[float]]]:
    """Closed relief bodies at `level`: every contour ring on the sheet, with
    the ones that run off the sheet sewn shut along the neatline."""
    bbox = SHEETS[name]["bbox"]
    out = []
    for line in join_runs(sheet_lines(name, g, level), 0.0):
        closed = line[0] == line[-1]
        # A run that neither closes on itself nor reaches the neatline at both
        # ends is a broken chain: there is no honest way to close it, so it is
        # not drawn.
        if not closed and not (_on_frame(line[0], bbox) and _on_frame(line[-1], bbox)):
            continue
        ring = close_on_bbox(line, bbox, g, level)
        if len(ring) < 4:
            continue
        # Every point inside a contour ring is above the contour by
        # definition, so a ring most of whose interior is below it is not a
        # body -- either a closure that went the wrong way round the frame, or
        # a basin traced as a hole. Drop it rather than draw it. The bar is
        # 0.6 rather than 1.0 because the grid is smoothed and the line is
        # simplified, so the boundary is fuzzy by a cell or two either way.
        if _interior_above(ring, g, level)[0] < 0.6:
            continue
        out.append([[round(a, 4), round(b, 4)] for a, b in ring])
    return out


def body_containing(name: str, g: Grid, level: float, pt) -> list[list[float]]:
    """The contour body at `level` that encloses `pt` -- the smallest one, so
    a nested pair resolves to the inner ring rather than its parent."""
    hits = [r for r in sheet_bodies(name, g, level) if _ring_contains(r, pt)]
    if not hits:
        raise SystemExit(f"{name}: no {level} m body contains {pt}")
    return min(hits, key=lambda r: _ring_span(r))


def _ring_span(ring) -> float:
    lats = [p[0] for p in ring]
    lons = [p[1] for p in ring]
    return (max(lats) - min(lats)) * (max(lons) - min(lons))


def joined_line(name: str, g: Grid, level: float, tol: float | None = None):
    """The contour at `level` as one polyline where the tracer split it into
    several: marching squares breaks a line wherever it crosses the neatline,
    and the delta's 10 m contour comes back in two pieces that share an end."""
    return max(join_runs(sheet_lines(name, g, level, tol), 0.0), key=len)


def _near(p, q, tol: float = 5e-4) -> bool:
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def nearest_index(line, pt) -> int:
    return min(range(len(line)),
               key=lambda i: (line[i][0] - pt[0]) ** 2 + (line[i][1] - pt[1]) ** 2)


def _round(line, decimals: int = 4):
    return [[round(a, decimals), round(b, decimals)] for a, b in line]


# ── What each plate's relief layers are cut from ────────────────────────────
#
# Every entry names a contour level and a point the body must enclose, so the
# selection is reproducible rather than an index into a list that moves the
# next time the DEM is re-smoothed.

DEM_NOTE = ("Outline traced from SRTM elevation data (AWS Open Data Terrain "
            "Tiles, terrarium encoding) at about 30 m posting, smoothed and "
            "generalised for this sheet's scale. Modern terrain: ridges have "
            "not moved since the Bronze Age, and this is a survey of rock, "
            "not of the shoreline. The body is one step of this sheet's "
            "hypsometric ramp: it is filled in the tint its elevation earns "
            "and edged with a hairline contour, so height reads as colour "
            "rather than as texture.")

# One generic band layer per contour level carries every body at that level
# that no named layer above has claimed. Together the named bodies and the
# bands tile the sheet's relief, low to high, and the renderer paints each in
# the ramp tint its elevation earns.
BAND_NOTE = ("Hypsometric band: all ground on this sheet above {level} m that "
             "no separately named landform claims. Step {step} of {steps} in "
             "this sheet's elevation ramp, which runs from the lowland ground "
             "colour up to the summit tint; the ramp is keyed to THIS sheet's "
             "own relief range, as a physical map's always is, so a tint means "
             "the same height here and a different one on the other Troy "
             "plate. " + DEM_NOTE)

TROAD_RELIEF = [
    ("relief-troad-upland", 200, (39.75, 26.60), None,
     "The 200 m contour of the Asian mainland: one continuous upland from the "
     "Gulf of Adramyttium north to the Dardanelles and east to the Aesepus, "
     "with the Trojan plain the only real break in it. This is why the Troad "
     "reads as hill country with a plain let into its north-west corner. "
     + DEM_NOTE),
    ("relief-lesbos", 200, (39.11, 26.29), None,
     "The uplands of Lesbos, 'above, seat of Macar' and the southern bound of "
     "Priam's realm (Il. 24.544); Achilles sacked it (9.129). " + DEM_NOTE),
    ("relief-imbros", 200, (40.165, 25.80), "imbros",
     "The spine of 'rugged Imbros' (Il. 13.33), modern Gokceada, rising to "
     "about 670 m. Poseidon's stride from Samothrace passes 'midway between "
     "Tenedos and rugged Imbros' (13.33). " + DEM_NOTE),
    ("relief-chersonese", 200, (40.42, 26.48), None,
     "The spine of the Thracian Chersonese above the European shore of the "
     "Hellespont. Sestos stands on this coast opposite Abydos, the one "
     "European territory in the Trojan alliance (Il. 2.836). " + DEM_NOTE),
    ("relief-troad-west-highland", 400, (39.60, 26.30), None,
     "The highland of the south-western Troad, running west from Ida's foot "
     "toward Cape Lekton above the north shore of the Gulf of Adramyttium -- "
     "the ground Hera and Sleep cross when they come to Lekton, leave the sea "
     "and go on over the dry land to Ida (Il. 14.283-85). " + DEM_NOTE),
    # Anchor moved 2026-07-29 (the old (40.02, 26.65) sat at 405 m, four
    # metres inside its own contour, and fell outside the body as soon as the
    # grid was smoothed for the ramp). (40.00, 26.70) is at about 620 m and
    # stays well inside this body at every smoothing level tried.
    ("relief-ida-north-spurs", 400, (40.00, 26.70), None,
     "The broken country between Ida and the Trojan plain, through which the "
     "Scamander and the Simoeis come down: the 400 m core of the spurs that "
     "run north from the massif toward the Dardanelles. The old form-line "
     "register is gone from this layer -- the extent is contoured now, not "
     "sketched. " + DEM_NOTE),
    ("relief-adramyttion", 600, (39.35, 27.10), None,
     "The highland behind the Gulf of Adramyttium, on the far side of Ida from "
     "Troy: Thebe under Placus and the Cilician towns Achilles sacked, "
     "Andromache's country (Il. 6.395-97). Above 600 m it is a separate massif "
     "from Ida; the two join lower down. " + DEM_NOTE),
    ("relief-ida", 600, (39.6995, 26.8653), "ida",
     "Mount Ida, modern Kaz Dagi: 'many-fountained' Ida, source of the eight "
     "rivers of Il. 12.19-22, Zeus's grandstand from Book 8 onward, and the "
     "slopes Dardanus's people lived on before Ilios was built on the plain "
     "(20.218). Drawn on the 600 m contour, which is where the massif "
     "separates from the general upland of the Troad. " + DEM_NOTE),
    ("relief-samothrace", 600, (40.4525, 25.5967), "samothrace",
     "Mount Fengari, the central massif of Thracian Samos, over 1,600 m. "
     "Poseidon sits 'high on the topmost peak of wooded Thracian Samos, for "
     "from there all Ida was visible, and the city of Priam was visible, and "
     "the ships of the Achaeans' (Il. 13.12-14) -- and Ida genuinely is "
     "visible from that summit in clear weather, which makes it one of the "
     "poem's most defensible topographic claims. " + DEM_NOTE),
    ("relief-ida-800", 800, (39.6995, 26.8653), None,
     "Ida above 800 m: the core of the massif, running east-north-east from "
     "the summit ridge. " + DEM_NOTE),
    ("relief-ida-1200", 1200, (39.6995, 26.8653), None,
     "Ida above 1,200 m. Gargaron, Zeus's precinct and fragrant altar (Il. "
     "8.48), is traditionally the summit, which this DEM puts at 1,757 m at "
     "39.70 N, 26.87 E -- within 20 m of the published height of Kaz Dagi. "
     + DEM_NOTE),
]

PLAIN_RELIEF = [
    # These five are the landforms the sheet NAMES; every other body at every
    # level rides in the generic band layer beside them. The old threshold
    # comment here ("hachuring anything below 40 m paints the battlefield with
    # the same texture as the ridges") was a hachure problem and died with the
    # hachure: a ramp tint at 10 m and one at 20 m are two different colours,
    # so the flat delta can be drawn in full without swamping the ridges.
    ("relief-sigeion-ridge", 20, (39.9835, 26.1809), "sigeion",
     "The Sigeion ridge closing the plain on the west: a closed 20 m contour "
     "running from Kum Kale south past Yenikoy, crest at about 36 m, with the "
     "Kesik cut through it. The one landform on this sheet drawn from a "
     "contour below 40 m, because it is a real ridge standing out of flat "
     "ground rather than a slope. Sigeion is not named in the Iliad -- it is "
     "Strabonic geography, and the traditional western headland of the Achaean "
     "beach. Luce would put the Achaean camp on its lower western slopes. "
     + DEM_NOTE),
    ("relief-plain-south", 40, (39.88, 26.20), None,
     "The ground above 40 m closing the plain on the south, rising toward "
     "Balli Dag and the Ida foothills: the limit of the open plain in the "
     "direction the Scamander comes from. " + DEM_NOTE),
    ("relief-troy-ridge", 40, (40.0, 26.33), "troy",
     "The upland east of the plain, whose western toe is the spur Hisarlik "
     "stands on. The DEM is blunt about something the hand-drawn version hid: "
     "no contour isolates the Troy ridge, because it is a spur and not a hill "
     "-- the ground rises continuously eastward from the mound, 36 m at "
     "Hisarlik and 58 m a kilometre and a half east, so the mound itself sits "
     "just below the 40 m contour this body is drawn on. That is exactly why "
     "the city commands the plain to its west and south and nothing to its "
     "east. " + DEM_NOTE),
    ("relief-rhoiteion-ridge", 100, (40.01, 26.303), "rhoiteion",
     "The Rhoiteion ridge on the Cakal Tepe spur, closing the plain on the "
     "north-east and fronting the Dardanelles; the DEM puts the ground behind "
     "In Tepe at about 133 m. Rhoiteion is not named in the Iliad either; it "
     "is the traditional eastern headland of the Achaean beach, paired with "
     "Sigeion, and the tomb of Ajax was shown on its spur at In Tepe. "
     + DEM_NOTE),
    ("relief-plain-east-200", 200, (39.89, 26.36), None,
     "The hills above 200 m on the eastern rim of the sheet, where the plain "
     "gives out and the ground climbs toward Ida. " + DEM_NOTE),
]


# ── The Bronze Age shore, derived rather than drawn ─────────────────────────
#
# The ground between Hisarlik and the modern coast is infilled delta sediment
# -- the old marine embayment, filled by the Karamenderes and the Dumrek since
# the Bronze Age. That fill is flat and low, and it meets older ground at a
# clear break, so the ancient shore is well approximated by a low contour of
# the modern DEM. Which contour is an empirical question, answered against the
# published constraints in docs/TROAD-SOURCES.md section A:
#
#   1. maximum Holocene transgression reached c.10 km south of Hisarlik
#      (Kraft, Kayan and Erol 1980)
#   2. progradation had carried the coast west of Troia by c.4000 BP (Kayan)
#   3. the modern coast lies c.6 km north of the site
#   4. a 2 to 2.5 m relative sea-level fall in the Late Bronze Age left a
#      shallow lagoon behind a wide sandy barrier
#
# Measured on this DEM: the delta surface falls from about 11 m a kilometre
# north of Hisarlik to 5 m near the modern shore, and the modern shore sits
# 5 to 6 km north of the site (constraint 3, satisfied). The 10 m contour
# passes 1.2 km north of Hisarlik, which is where Kraft, Rapp, Kayan and Luce
# put the Late Bronze Age bay head; 8 m puts it 2.8 km north and 12 m only
# 0.7 km, both outside the published range. Hence 10 m.
#
# The 5 m contour runs east across the bay mouth at about 40.00 N between the
# Sigeion and Rhoiteion ridges -- low ground standing proud of the fill in
# exactly the position Kayan's sandy barrier occupies (constraint 4).

SHORE_LEVEL = 10.0
BARRIER_LEVEL = 5.0
SHORE_TOL = 0.0025          # ~275 m: a line whose own uncertainty is a
                            # kilometre has no business carrying 100 m wiggles
SHORE_WEST = (39.998, 26.192)     # the Sigeion ridge, at the bay mouth
SHORE_EAST = (40.0174, 26.321)    # the Rhoiteion spur, at the bay mouth
LAGOON_HEAD = (39.9582, 26.2062)  # the bay head, 1.2 km NNW of Hisarlik


SIGEION_RIDGE = (39.9835, 26.1809)   # the ridge whose east foot is the bay's west shore
LAGOON_WEST_N = (39.9975, 26.191)    # where that foot meets the barrier
LAGOON_WEST_S = (39.9584, 26.1946)   # and where it reaches the bay head


def _arc(ring: list, a_pt, b_pt, eastern: bool = True) -> list:
    """The arc of a closed ring between two points, taking the eastern side.
    Used for the bay's western shore, which is the east foot of the Sigeion
    ridge -- a real derived line, where closing the lagoon with a straight
    chord would have drawn a 4 km ruler-edge across the plain."""
    r = ring[:-1] if ring[0] == ring[-1] else ring
    a = nearest_index(r, a_pt)
    b = nearest_index(r, b_pt)
    fwd = r[a:b + 1] if a <= b else r[a:] + r[:b + 1]
    bwd = (r[b:a + 1] if b <= a else r[b:] + r[:a + 1])[::-1]
    key = (lambda arc: sum(p[1] for p in arc) / len(arc))
    return max((fwd, bwd), key=key) if eastern else min((fwd, bwd), key=key)


def bronze_geometry(g: Grid) -> dict:
    shore_line = joined_line("trojan-plain", g, SHORE_LEVEL)
    barrier_line = joined_line("trojan-plain", g, BARRIER_LEVEL)

    i0 = nearest_index(shore_line, SHORE_WEST)
    i1 = nearest_index(shore_line, SHORE_EAST)
    shore = douglas_peucker(shore_line[i0:i1 + 1], SHORE_TOL)

    j0 = nearest_index(barrier_line, SHORE_WEST)
    j1 = nearest_index(barrier_line, SHORE_EAST)
    barrier = douglas_peucker(barrier_line[j0:j1 + 1], SHORE_TOL)

    # The lagoon is the water the barrier held in: the east foot of the Sigeion
    # ridge on the west, the derived shore round the bay head and on to the
    # Rhoiteion spur, and the barrier closing it seaward. It stops at the bay
    # head rather than following the contour on south, because south of there
    # the same 10 m line bounds aggraded floodplain, not open water.
    ridge = body_containing("trojan-plain", g, 20, SIGEION_RIDGE)
    west = _arc(ridge, LAGOON_WEST_N, LAGOON_WEST_S)
    h = nearest_index(shore, LAGOON_HEAD)
    landward = west + shore[h:]
    lagoon = landward + barrier[::-1]

    return {
        "shore": _round(landward),
        "barrier": _round(barrier),
        "lagoon": _round(lagoon),
        "swamp": _round(swamp_geometry(g, lagoon)),
    }


# ── The wet delta ───────────────────────────────────────────────────────────
#
# The swamp Kayan puts over much of the delta plain, derived the way the shore
# was and no longer cut with a ruler. What it replaced (2026-07-29): a strip
# taken between the 10 m and 20 m contours and then FILTERED BY LATITUDE AND
# LONGITUDE (39.90 <= lat <= bay head, lon < 26.24), so three of the polygon's
# four sides were the filter rather than the ground -- the sharpest lines on a
# sheet whose whole subject is measured relief, and an artefact of how the data
# was cut presented as a landform.
#
# The derivation now is a contour band and a slope threshold, which is what
# aggraded floodplain IS: ground between the reconstructed shoreline (the 10 m
# contour, already calibrated against the published bay head -- see above) and
# one hypsometric step above it, flat enough not to be a ridge foot. Both
# numbers are principled rather than tuned to a shape: 15 m is a level the
# sheet's own ramp already draws, and 1.2 % separates the delta surface (which
# falls about 10 m over 5 km, 0.2 %) from the foot of the Sigeion ridge (36 m
# in well under a kilometre, 4 %). The lagoon is cut out of it, since that is
# open water on this reconstruction, and only the component connected to the
# bay head survives, so an unrelated flat patch elsewhere on the sheet cannot
# join the wetland by coincidence of height.
#
# The mask is then blurred and traced at its half-level rather than being
# converted cell by cell: a raster boundary at 29 m per cell drawn as a polygon
# is a staircase, and the blur is what makes the outline read as ground. The
# renderer softens it further -- the marsh draws with no outline at all -- for
# the reason stated on the layer itself: a wetland margin is indefinite, and a
# crisp edge round it claims a precision that does not exist.

SWAMP_LOW = SHORE_LEVEL       # the reconstructed shoreline is its seaward limit
SWAMP_HIGH = 15.0             # one step up the sheet's own hypsometric ramp
SWAMP_MAX_SLOPE = 0.012       # 1.2 %: floodplain, not the flank of a ridge
SWAMP_BLUR = 15               # box-blur passes on the mask before tracing
SWAMP_MIN_SPAN = 0.01         # degrees; drops slivers the blur leaves behind


def cell_metres(g: Grid, lat: float) -> float:
    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** g.z) * g.step


def slope_grid(g: Grid, lat: float) -> array:
    """Rise over run at every cell, by central differences."""
    step_m = cell_metres(g, lat)
    w, h = g.w, g.h
    out = array("f", bytes(4 * w * h))
    for j in range(h):
        jm = max(0, j - 1) * w
        jp = min(h - 1, j + 1) * w
        row = j * w
        for i in range(w):
            im = max(0, i - 1)
            ip = min(w - 1, i + 1)
            dx = (g.data[row + ip] - g.data[row + im]) / ((ip - im) * step_m)
            dy = (g.data[jp + i] - g.data[jm + i]) / (((jp - jm) // w) * step_m)
            out[row + i] = math.hypot(dx, dy)
    return out


def _largest_component(mask: bytearray, w: int, h: int, seed: tuple[int, int]) -> bytearray:
    out = bytearray(w * h)
    if not mask[seed[1] * w + seed[0]]:
        raise SystemExit("swamp: seed cell is not in the mask")
    out[seed[1] * w + seed[0]] = 1
    stack = [seed]
    while stack:
        i, j = stack.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < w and 0 <= b < h and mask[b * w + a] and not out[b * w + a]:
                out[b * w + a] = 1
                stack.append((a, b))
    return out


def swamp_geometry(g: Grid, lagoon: list) -> list[list[float]]:
    w, h = g.w, g.h
    slope = slope_grid(g, (SHEETS["trojan-plain"]["bbox"][0] + SHEETS["trojan-plain"]["bbox"][2]) / 2)
    lats = [p[0] for p in lagoon]
    lons = [p[1] for p in lagoon]

    mask = bytearray(w * h)
    for j in range(h):
        row = j * w
        for i in range(w):
            z = g.data[row + i]
            if not (SWAMP_LOW < z <= SWAMP_HIGH) or slope[row + i] > SWAMP_MAX_SLOPE:
                continue
            lat, lon = g.latlon(i, j)
            if (min(lats) <= lat <= max(lats) and min(lons) <= lon <= max(lons)
                    and _ring_contains(lagoon, (lat, lon))):
                continue
            mask[row + i] = 1

    # Seed: the first masked cell working south from the bay head, i.e. the
    # wet ground immediately behind the reconstructed shore.
    x, y = lonlat_to_px(LAGOON_HEAD[1], LAGOON_HEAD[0], g.z)
    si = int((x - g.x0) / g.step - 0.5)
    sj = int((y - g.y0) / g.step - 0.5)
    seed = None
    for dj in range(0, 60):
        for di in range(-30, 31):
            i, j = si + di, sj + dj
            if 0 <= i < w and 0 <= j < h and mask[j * w + i]:
                seed = (i, j)
                break
        if seed:
            break
    if seed is None:
        raise SystemExit("swamp: no masked cell within 60 cells south of the bay head")
    comp = _largest_component(mask, w, h, seed)
    cells = sum(comp)
    step_m = cell_metres(g, LAGOON_HEAD[0])
    print(f"  {'delta-swamp mask':<32} {cells:>7} cells, "
          f"{cells * step_m * step_m / 1e6:.1f} km2 at {step_m:.0f} m/cell")

    smooth = box_blur(Grid(g.z, g.x0, g.y0, w, h, g.step,
                           array("f", [float(v) for v in comp])), SWAMP_BLUR)
    rings = [r for r in clip_to_bbox(
        contours(smooth, 0.5, SHORE_TOL, 5, SWAMP_MIN_SPAN),
        SHEETS["trojan-plain"]["bbox"]) if len(r) >= 4]
    if not rings:
        raise SystemExit("swamp: the blurred mask traced no usable ring")
    return max(rings, key=len)


# ── Patching the plates ─────────────────────────────────────────────────────

PLATES_DIR = os.path.join(REPO, "apparatus", "plates")

BRONZE_NOTES = {
    "shore-bronze":
        "The landward shore of the Late Bronze Age embayment, DERIVED rather "
        "than drawn: the ground between Hisarlik and the modern coast is "
        "infilled delta sediment, so the old shore is closely approximated by "
        "a low contour of the modern DEM, where the flat fill meets ground "
        "that was already land. This line is the 10 m contour of SRTM (AWS "
        "Terrain Tiles), generalised to about 130 m, run from the Sigeion "
        "ridge round the bay head to the Rhoiteion spur. The 10 m level was "
        "chosen against the published constraints, not picked for looks: it "
        "passes 1.2 km north of Hisarlik, where Kraft, Rapp, Kayan and Luce "
        "put the bay head; the 8 m contour puts it 2.8 km north and the 12 m "
        "only 0.7 km, both outside the published range. The DEM independently "
        "confirms the other two: the modern shore is 5 to 6 km north of the "
        "site, and the delta surface falls from about 11 m a kilometre north "
        "of Hisarlik to 5 m at the coast. Approximate to on the order of a "
        "kilometre, and a reconstruction, not a survey: no published figure "
        "was traced. Two editorial cuts, both stated rather than hidden: the "
        "bay's western shore is taken from the 20 m contour of the Sigeion "
        "ridge, whose east foot is what the water stood against; and the line "
        "stops at the bay head, because south of there the 10 m contour bounds "
        "aggraded floodplain rather than open water. The contour does run on "
        "south -- that is the landward limit of the whole alluvial fill, not "
        "of the Late Bronze Age bay.",
    "barrier-bronze":
        "The wide sandy barrier that a relative sea-level fall of 2 to 2.5 m "
        "left across the mouth of the bay in the Late Bronze Age, closing the "
        "remaining water into a shallow lagoon. Derived on the same principle "
        "as the shore: the 5 m contour of the modern DEM, which runs east "
        "across the delta at about 40.00 N between the Sigeion and Rhoiteion "
        "ridges -- low ground standing proud of the fill in exactly the "
        "position Kayan's barrier occupies, and seaward of the derived shore "
        "everywhere along its length. Approximate to on the order of a "
        "kilometre. Not traced from any figure.",
    "lagoon-bronze":
        "The shallow lagoon of about 1200 BC: the water left between the "
        "prograding delta front and the sandy barrier after the Late Bronze "
        "Age sea-level fall. Its outline is the derived shore and the derived "
        "barrier joined, so it carries their uncertainty, on the order of a "
        "kilometre. It stops at the bay head 1.2 km north-north-west of "
        "Hisarlik: south of that the 10 m contour bounds floodplain, not "
        "water. Troy overlooks a wetland, a lagoon and a distant sea, not a "
        "deep-water bay.",
    "delta-swamp":
        "Swamp lay over much of the delta plain through the Late Bronze Age "
        "(Kayan). A WETLAND HAS NO BOUNDARY -- it grades from open water "
        "through reed and seasonal flood to dry ground, and it moves with the "
        "season and the year -- so this is drawn with no outline at all and "
        "fades out at its margin. That is the claim, not a decoration: the "
        "extent is indefinite and the drawing says so. What is measured is "
        "where the wet ground lay, derived from the same DEM as the shore: the "
        "flat aggraded fill immediately behind the reconstructed shoreline, "
        "between the 10 m contour that shoreline is cut from and 15 m, one "
        "step up this sheet's own hypsometric ramp, on ground falling at under "
        "1.2 per cent -- which separates the delta surface (about 10 m over "
        "5 km) from the foot of the Sigeion ridge (36 m in well under a "
        "kilometre). The lagoon is cut out of it, and only the ground "
        "continuous with the bay head is kept, so a flat patch elsewhere at "
        "the same height cannot join the wetland by coincidence. About "
        "15 square kilometres. It does not reach Troy or the dry plain the "
        "poem fights over, both of which stand above 20 m.",
}


# The land/water contract (docs/APPARATUS-SCHEMAS.md): a region only reads as
# water if it says which water it is. Without these the reconstructed bay
# renders as a dotted outline with beige ground inside it.
BRONZE_FILL = {"lagoon-bronze": "lagoon", "delta-swamp": "marsh"}

# The Bay of Troy is a body of water, not a line, and the renderer letters a
# line along a textPath: with the shore now hooking tightly round the bay head,
# its 50% point lands on the hook and "Bay of Troy" came out as a vertical
# scrunch of rotated glyphs. An area layer gets a centred label instead, so the
# gazetteer place moves from the shoreline to the lagoon it bounds.
BRONZE_PLACE = {"shore-bronze": None, "lagoon-bronze": "bay-of-troy"}


def _relief_layer(existing: dict | None, layer_id: str, place_id: str | None,
                  note: str, elevation: float, geometry: dict) -> dict:
    layer = dict(existing) if existing else {"id": layer_id, "kind": "relief"}
    layer.setdefault("id", layer_id)
    layer.setdefault("kind", "relief")
    if place_id:
        layer["placeId"] = place_id
    layer.setdefault("default", "on")
    # The form-line register said "sketched, not contoured". It is contoured now.
    layer.pop("shading", None)
    for f_ in ("rings", "polygon"):
        layer.pop(f_, None)
    layer["elevation"] = elevation
    layer.update(geometry)
    layer["note"] = note
    sources = [s for s in (existing or {}).get("sources", [])
               if "Terrain Tiles" not in s.get("cite", "")]
    layer["sources"] = sources + [dict(DEM_SOURCE)]
    # Key order: identity, geometry, prose.
    order = ["id", "kind", "placeId", "label", "default", "style", "width",
             "fill", "elevation", "rings", "path", "polygon", "baseline",
             "trace", "note", "sources"]
    return {k: layer[k] for k in order if k in layer} | {
        k: v for k, v in layer.items() if k not in order}


def _layer_vertices(layer: dict) -> int:
    if "rings" in layer:
        return sum(len(r) for r in layer["rings"])
    return len(layer.get("polygon", ()))


def relief_block(name: str, g: Grid, named: list, by_id: dict) -> list[dict]:
    """The sheet's whole relief stack, ascending: for every contour level, the
    named landforms cut from it plus one generic band layer carrying every
    other body at that level. Ascending order IS the paint order -- a higher
    band lies inside a lower one, so low must go down first."""
    levels = SHEETS[name]["levels"]
    out: list[dict] = []
    for step, level in enumerate(levels, start=1):
        bodies = sheet_bodies(name, g, level)
        claimed: list[tuple] = []
        taken: list[int] = []
        for layer_id, lv, pt, place_id, note in named:
            if lv != level:
                continue
            hits = [(k, r) for k, r in enumerate(bodies) if _ring_contains(r, pt)]
            if not hits:
                raise SystemExit(f"{name}: no {level} m body contains {pt} ({layer_id})")
            k, body = min(hits, key=lambda kr: _ring_span(kr[1]))
            taken.append(k)
            claimed.append((layer_id, place_id, note, body))
        rest = [r for k, r in enumerate(bodies) if k not in set(taken)]
        if rest:
            band_id = f"relief-band-{int(level):04d}"
            out.append(_relief_layer(
                by_id.get(band_id), band_id, None,
                BAND_NOTE.format(level=int(level), step=step, steps=len(levels)),
                level, {"rings": rest}))
        for layer_id, place_id, note, body in claimed:
            out.append(_relief_layer(by_id.get(layer_id), layer_id, place_id,
                                     note, level, {"polygon": body}))
    for layer in out:
        print(f"  {layer['id']:<32} {layer['elevation']:>5} m  "
              f"{_layer_vertices(layer):>5} vertices")
    return out


def _replace_block(layers: list, managed: list[str], new_layers: list,
                   after: str | None = None) -> list:
    """Swaps a set of layers for a new set, in place: the block lands where its
    first member was -- or, with `after`, immediately after the named layer --
    and every layer outside it keeps its exact position and content."""
    idx = [i for i, l in enumerate(layers) if l.get("id") in managed]
    keep = [l for i, l in enumerate(layers) if i not in set(idx)]
    if after is not None:
        at = next((i for i, l in enumerate(keep) if l.get("id") == after), -1) + 1
        if at == 0:
            raise SystemExit(f"anchor layer {after!r} not found")
    else:
        at = idx[0] if idx else len(layers)
    return keep[:at] + new_layers + keep[at:]


def patch_troad(g: Grid, gr: Grid) -> tuple[int, int]:
    path = os.path.join(PLATES_DIR, "troad.json")
    with open(path, encoding="utf-8") as f:
        plate = json.load(f)
    by_id = {l["id"]: l for l in plate["layers"]}
    new = relief_block("troad", gr, TROAD_RELIEF, by_id)
    managed = [l["id"] for l in plate["layers"] if l["id"].startswith("relief-")]
    managed += [l["id"] for l in new]
    # The relief stack sits above the coasts (whose `fill: "land"` lays the
    # lowland ground down) and below the rivers, which must stay on top of it.
    plate["layers"] = _replace_block(plate["layers"], managed, new,
                                     after="coast-tenedos")
    _write_plate(path, plate)
    return len(new), sum(_layer_vertices(l) for l in new)


def patch_plain(g: Grid, gr: Grid) -> tuple[int, int]:
    path = os.path.join(PLATES_DIR, "trojan-plain.json")
    with open(path, encoding="utf-8") as f:
        plate = json.load(f)
    by_id = {l["id"]: l for l in plate["layers"]}

    bronze = bronze_geometry(g)
    verts = 0
    for lid, field, geom in (("shore-bronze", "rings", [bronze["shore"]]),
                             ("barrier-bronze", "rings", [bronze["barrier"]]),
                             ("lagoon-bronze", "polygon", bronze["lagoon"]),
                             ("delta-swamp", "polygon", bronze["swamp"])):
        layer = by_id.get(lid)
        if layer is None:
            continue
        for f_ in ("rings", "polygon", "path"):
            layer.pop(f_, None)
        layer[field] = geom
        if lid in BRONZE_FILL:
            layer["fill"] = BRONZE_FILL[lid]
        if lid in BRONZE_PLACE:
            if BRONZE_PLACE[lid]:
                layer["placeId"] = BRONZE_PLACE[lid]
            else:
                layer.pop("placeId", None)
        layer["note"] = BRONZE_NOTES[lid]
        layer["sources"] = [s for s in layer.get("sources", [])
                            if "Terrain Tiles" not in s.get("cite", "")] + [dict(DEM_SOURCE)]
        n = len(geom[0]) if field == "rings" else len(geom)
        verts += n
        print(f"  {lid:<32} {'':>7}  {n:>4} vertices")

    new = relief_block("trojan-plain", gr, PLAIN_RELIEF, by_id)
    verts += sum(_layer_vertices(l) for l in new)
    managed = [l["id"] for l in plate["layers"] if l["id"].startswith("relief-")]
    managed += [l["id"] for l in new]
    # Terrain first, then the Bronze Age reconstruction, the coast and the
    # rivers on top of it. The old order put relief LAST, which was harmless
    # while relief was five isolated hachured knolls and fatal the moment it
    # became a ramp tiling the sheet: the 10 m band contains the whole
    # 10-to-20 m swamp belt, so a band drawn last paints the delta marsh -- the
    # plate's own argument -- out of existence.
    # `scamandrian-plain` moves with it, from over the relief to under it.
    # Its geometry is untouched and no longer draws anything (2026-07-29): it
    # is `fill: "none"` now, a lettering zone rather than a landform. It was an
    # eleven-vertex hand-drawn wash, fine as the only ground colour on the
    # sheet and a flat opaque blob with a ruler-straight diagonal edge once
    # there was contoured terrain under it -- and worse than merely ugly, since
    # at full opacity it painted the ramp's relief flat across the middle of
    # the plain. The ramp draws the ground; the region only ever had to say
    # where the name "SCAMANDRIAN PLAIN" goes.
    layers = [l for l in plate["layers"] if l["id"] != "scamandrian-plain"]
    wash = next(l for l in plate["layers"] if l["id"] == "scamandrian-plain")
    at = next(i for i, l in enumerate(layers) if l["id"] == "sea-modern") + 1
    plate["layers"] = _replace_block(layers[:at] + [wash] + layers[at:],
                                     managed, new, after="scamandrian-plain")
    _write_plate(path, plate)
    return len(new) + 4, verts


_NUM_ARRAY = re.compile(
    r"\[\s*\n\s*(-?\d[\d.eE+-]*(?:,\s*\n\s*-?\d[\d.eE+-]*)*)\s*\n\s*\]")


def _write_plate(path: str, plate: dict) -> None:
    """Writes the plate in the house style: two-space indent, but a purely
    numeric array (a bbox, a size, a coordinate pair) collapsed onto one line.
    Verified to round-trip both Troy plates byte for byte, so a patch touches
    only the layers it means to touch."""
    text = json.dumps(plate, indent=2, ensure_ascii=False)
    while True:
        collapsed = _NUM_ARRAY.sub(
            lambda m: "[" + ", ".join(v.strip() for v in m.group(1).split(",")) + "]",
            text)
        if collapsed == text:
            break
        text = collapsed
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def _probe(name: str, g: Grid, levels: list[float]) -> None:
    for lv in levels:
        rings = sheet_bodies(name, g, lv)
        rings.sort(key=lambda r: -len(r))
        print(f"== {name} {lv} m: {len(rings)} bodies, "
              f"{sum(len(r) for r in rings)} verts")
        for r in rings[:8]:
            lats = [p[0] for p in r]
            lons = [p[1] for p in r]
            print(f"    {len(r):>4}v [{min(lats):.3f},{min(lons):.3f}]-"
                  f"[{max(lats):.3f},{max(lons):.3f}] mean "
                  f"{_interior_above(r, g, lv)[0]:.0%} above")


def write_vendored(name: str, g: Grid, stats: dict) -> None:
    spec = SHEETS[name]
    levels = []
    for lv in spec["levels"]:
        lines = sheet_lines(name, g, lv)
        levels.append({"elevation_m": lv, "lines": [_round(ln) for ln in lines]})
        print(f"  {lv:>6} m: {len(lines):>3} lines, "
              f"{sum(len(ln) for ln in lines):>5} vertices")
    payload = {
        "sheet": name,
        "bbox": list(spec["bbox"]),
        "zoom": spec["zoom"],
        "source": "AWS Open Data Terrain Tiles (Tilezen elevation-tiles-prod), terrarium PNG; SRTM over the Troad",
        "attribution": "SRTM data courtesy of the U.S. Geological Survey",
        "derivation": {
            "blur_passes": spec["blur"],
            "decimate": spec["decimate"],
            "post_blur_passes": spec.get("post_blur", 0),
            "simplify_tolerance_deg": spec["tol_deg"],
            "sample_spacing_m": round(
                156543.03392 * math.cos(math.radians((spec["bbox"][0] + spec["bbox"][2]) / 2))
                / (2 ** spec["zoom"]) * spec["decimate"], 1),
        },
        "elevation_stats": stats,
        "levels": levels,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{name}-contours.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote {path}: {os.path.getsize(path) / 1024:.1f} KB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=DEFAULT_CACHE, help="tile cache directory")
    ap.add_argument("--sheet", action="append", choices=sorted(SHEETS))
    ap.add_argument("--stats", action="store_true", help="elevation report only")
    ap.add_argument("--probe", nargs="*", type=float, metavar="LEVEL",
                    help="report body/vertex counts at these levels and stop")
    ap.add_argument("--patch-plates", action="store_true",
                    help="also rewrite the relief geometry in apparatus/plates/")
    args = ap.parse_args()

    for name in (args.sheet or sorted(SHEETS)):
        g, stats = build_sheet(name, args.cache)
        if args.stats:
            continue
        if args.probe is not None:
            _probe(name, g, args.probe or SHEETS[name]["levels"])
            continue
        gr, post = relief_grid(name, g)
        stats["relief_grid"] = post
        write_vendored(name, gr, stats)
        if args.patch_plates:
            layers, verts = (patch_troad(g, gr) if name == "troad" else patch_plain(g, gr))
            print(f"[{name}] patched {layers} layers, {verts} vertices")


if __name__ == "__main__":
    main()
