#!/usr/bin/env python3
"""Stage 2 — ONE FRAGMENT of "The Ships, the Bay, and Ilios".

A vertical slice through the raised-oblique plate, 800 units wide by the full
1350-unit frame height, taken from the settled Stage-1D camera. It exists to
answer one question and then stop: does engraved line-and-tint reach the bar
for this subject, at 1x and at 3.5x?

WHAT IS NEW HERE, against Stage 1D
  1. The artifact is SVG, not pixels. Every colour is a var() token; the
     prototype inlines the two themes' token blocks so a headless browser can
     rasterise it, but the geometry is the shipping geometry.
  2. POLAR MESH, from the camera's own ground point: bearings x ranges rather
     than a rectangular forward/lateral grid. Two consequences that matter --
     screen-space sample density is uniform by construction (a rectangular
     grid over-samples the foreground and under-samples the far ground), and
     painter order is exact by construction (draw rings far to near; no depth
     sort, no overlap).
  3. BAND EDGES ARE TRUE ISOLINES. Stage 1D coloured each grid quad flat, so
     every hypsometric boundary was a 60 m staircase. Here a quad spanning two
     bands is split along the interpolated level, so the boundary is the
     isoline itself. The staircase is gone, not smoothed.
  4. THE COAST IS A VECTOR, NOT A CLASSIFICATION. Stage 1D decided sea/land
     per grid quad -- the single biggest source of the "just shapes" look.
     Here the terrain is drawn as land everywhere and the reconstructed water
     bodies are projected as polygons and painted over it, exactly as the map
     plates do. Any sliver of pale low band left showing at the margin reads
     as beach, which is what it is.
  5. THE HORIZON IS REAL, AND THAT IS WHAT FIXES IDA. The grey rectangle in
     the sky was never an Ida bug: Stage 1D's ground stopped at 9.5 km, which
     in this camera is 160 px BELOW the true horizon, and Ida's silhouette
     fill dropped into that gap of open sky with vertical edges where its
     bearing fan ended. The ground now runs to 45 km (plain DEM inside its
     bbox, Troad DEM beyond), so it reaches the horizon and there is no gap to
     fall into.
  6. ATMOSPHERIC PERSPECTIVE, four strata deep, for the price of three
     rectangles: because painter order is exact, a --page-bg rectangle at low
     opacity laid over the canvas between distance strata hazes everything
     already drawn and nothing yet to come. Cumulative, correct, and
     expressible as one token.

WHAT IS DELIBERATELY NOT HERE (fragment scope)
  delta-swamp (its margin has to fade, and a fade wants its own decision);
  the neatline, legend, scale and hypsometric key; Tier 2/3 labels; the
  Scamander and Simoeis; anything west of the strip.

VERTICAL EXAGGERATION is Stage 1D's, unchanged: 4.0x at or under 100 m real,
tapering to 1.0x at 300 m. It is applied to BUILT HEIGHTS TOO -- hulls,
stem-posts, hut roofs, walls and towers -- because a ship drawn at true height
against a landscape stretched 4x would read as a squashed ship, not as
honesty. Disclosed in the report; must be disclosed on the plate.

POSITIONS. Terrain, coastlines and Hisarlik are measured. Every ship, hut,
wall and roof is positionBasis "conjectural": the poem's own logic (ships
hauled up in rows, prows to the water, huts behind them on the ridge) laid
against measured ground. No coordinate is invented for anything the poem
leaves unplaced.

Usage
  python3 scripts/panorama-stage2-fragment.py            # both themes, 1x + 3.5x crop
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "panorama_profile", os.path.join(REPO, "scripts", "panorama-profile.py")
)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)  # type: ignore[union-attr]
ptc = pp.ptc

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ── frame + camera (Stage 1D's, not re-derived) ──────────────────────────
W, H = 2400, 1350
VIEWPOINT = (39.9755, 26.1785)
HEADING_DEG = 104.0
HFOV_DEG = 72.0
ALT = 800.0
SETBACK = 1500.0
NEAR_CLIP = 5.0
FOCAL = (W / 2.0) / math.tan(math.radians(HFOV_DEG) / 2.0)

# ── the fragment: a vertical slice of the frame ──────────────────────────
FRAG_X0, FRAG_W = 1000.0, 800.0

# ── mesh ─────────────────────────────────────────────────────────────────
AZ_MIN, AZ_MAX, AZ_STEP = -16.0, 30.0, 0.16      # degrees off the heading
RANGE_NEAR, RANGE_FAR, RANGE_RATIO = 650.0, 45000.0, 1.030

# ── hypsometric ladder. Six of the twelve bands sit under 45 m, the same
# reasoning the trojan-plain sheet uses: the subject is a shore and a plain
# 20-40 m above the sea, not a mountain range. ───────────────────────────
LEVELS = [5, 10, 15, 20, 30, 45, 70, 110, 180, 300, 600]  # 11 levels, 12 bands

# ── atmospheric strata: (max range, haze opacity applied AFTER that stratum)
STRATA = [(45000.0, 0.20), (30000.0, 0.15), (12000.0, 0.09), (5000.0, 0.0)]

PLAIN_BBOX = (39.86, 40.05, 26.1, 26.38)


def ve(e: float) -> float:
    t = min(1.0, max(0.0, (e - 100.0) / 200.0))
    return 4.0 + t * (1.0 - 4.0)


def exaggerate(e: float) -> float:
    return e * ve(e)


def built_h(metres: float, ground_elev: float) -> float:
    """A built height, TRUE, on top of the exaggerated ground.

    The first cut stretched built heights by the terrain's own 4x, reasoning
    that a true-height ship against a 4x landscape would read as squashed.
    Rendered, that argument is simply wrong: a 6.4 m stem-post became 25.6 m
    and stood 17 px proud of the hull, so every beached galley grew a mast and
    the whole fleet read as riding at anchor in the bay behind it. The ground
    is the exaggerated thing; the ships are the subject, and the subject stays
    true. Disclosed on the plate: terrain z x4, built heights x1.""" 
    return exaggerate(ground_elev) + metres


# ═══════════════════════════════════════════════════════════════════════════
# camera
# ═══════════════════════════════════════════════════════════════════════════
class Camera:
    def __init__(self, plain_grid):
        self.theta = math.radians(HEADING_DEG)
        self.e = -SETBACK * math.sin(self.theta)
        self.n = -SETBACK * math.cos(self.theta)
        self.z = ALT
        far_lat, far_lon = pp._dest_point(VIEWPOINT, HEADING_DEG, 9500.0)
        far_e, far_n = pp._flat_m((far_lat, far_lon), *VIEWPOINT)
        far_z = exaggerate(pp.bilinear_elev(plain_grid, far_lat, far_lon))
        view_z = exaggerate(pp.bilinear_elev(plain_grid, *VIEWPOINT))
        near_angle = math.atan2(ALT - view_z, SETBACK)
        far_angle = math.atan2(ALT - far_z, math.hypot(far_e - self.e, far_n - self.n))
        self.pitch = (near_angle + far_angle) / 2.0
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        self.fwd = (math.sin(self.theta) * cp, math.cos(self.theta) * cp, -sp)
        # right = fwd x world_up, normalised; horizontal by construction
        self.right = (math.cos(self.theta), -math.sin(self.theta), 0.0)
        # up = right x fwd
        self.up = (
            self.right[1] * self.fwd[2] - self.right[2] * self.fwd[1],
            self.right[2] * self.fwd[0] - self.right[0] * self.fwd[2],
            self.right[0] * self.fwd[1] - self.right[1] * self.fwd[0],
        )

    def project(self, e, n, z):
        rx, ry, rz = e - self.e, n - self.n, z - self.z
        d = rx * self.fwd[0] + ry * self.fwd[1] + rz * self.fwd[2]
        if d <= NEAR_CLIP:
            return None
        xc = rx * self.right[0] + ry * self.right[1] + rz * self.right[2]
        yc = rx * self.up[0] + ry * self.up[1] + rz * self.up[2]
        return (W / 2.0 + FOCAL * xc / d, H / 2.0 - FOCAL * yc / d, d)

    def project_ll(self, lat, lon, z):
        e, n = pp._flat_m((lat, lon), *VIEWPOINT)
        return self.project(e, n, z)


# ═══════════════════════════════════════════════════════════════════════════
# terrain sampling: plain DEM inside its bbox, Troad DEM beyond
# ═══════════════════════════════════════════════════════════════════════════
class Terrain:
    def __init__(self):
        self.plain, _, _ = pp.load_plain_grid()
        self.troad, _ = ptc.build_sheet("troad", pp.CACHE)

    def elev(self, lat, lon):
        a, b, c, d = PLAIN_BBOX
        if a <= lat <= b and c <= lon <= d:
            return pp.bilinear_elev(self.plain, lat, lon)
        if 38.95 <= lat <= 40.6 and 25.35 <= lon <= 27.5:
            return pp.bilinear_elev(self.troad, lat, lon)
        return 0.0

    def elev_smooth(self, lat, lon, radius_m):
        """Elevation generalised over `radius_m`. The DEM is quantised (1 m
        terrarium steps, then decimated), which leaves flat plateaus 40-70 m
        across; where one of those straddles a hypsometric level it prints as
        a rectilinear terrace with axis-aligned edges -- the paper-model look
        the first cut of this fragment had all through its middle distance.
        Averaging a nine-point stencil at a radius that GROWS WITH RANGE also
        does the right cartographic thing: far ground is generalised more than
        near ground, which is what a draughtsman does anyway."""
        if radius_m <= 0:
            return self.elev(lat, lon)
        dlat = radius_m / 111132.0
        dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
        tot = self.elev(lat, lon) * 2.0
        wsum = 2.0
        for dx, dy, w in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                          (0.7, 0.7, 0.7), (-0.7, 0.7, 0.7), (0.7, -0.7, 0.7), (-0.7, -0.7, 0.7)):
            tot += self.elev(lat + dy * dlat, lon + dx * dlon) * w
            wsum += w
        return tot / wsum


def band_of(elev: float) -> int:
    for i, lv in enumerate(LEVELS):
        if elev < lv:
            return i
    return len(LEVELS)


# ═══════════════════════════════════════════════════════════════════════════
# geometry helpers
# ═══════════════════════════════════════════════════════════════════════════
def f2(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def path_of(pts) -> str:
    return "M" + "L".join(f"{f2(x)} {f2(y)}" for x, y in pts) + "Z"


def chaikin(pts, passes=2, closed=True):
    for _ in range(passes):
        out = []
        n = len(pts)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            out.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
            out.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        if not closed:
            out = [pts[0]] + out + [pts[-1]]
        pts = out
    return pts


def clip_below(poly, evals, level):
    """Sutherland-Hodgman: the part of `poly` where the scalar is <= level.
    Returns (points, scalars). Used to split a mesh quad along an isoline."""
    out_p, out_e = [], []
    n = len(poly)
    for i in range(n):
        p0, e0 = poly[i], evals[i]
        p1, e1 = poly[(i + 1) % n], evals[(i + 1) % n]
        in0, in1 = e0 <= level, e1 <= level
        if in0:
            out_p.append(p0)
            out_e.append(e0)
        if in0 != in1 and e1 != e0:
            t = (level - e0) / (e1 - e0)
            out_p.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
            out_e.append(level)
    return out_p, out_e


def clip_above(poly, evals, level):
    out_p, out_e = [], []
    n = len(poly)
    for i in range(n):
        p0, e0 = poly[i], evals[i]
        p1, e1 = poly[(i + 1) % n], evals[(i + 1) % n]
        in0, in1 = e0 >= level, e1 >= level
        if in0:
            out_p.append(p0)
            out_e.append(e0)
        if in0 != in1 and e1 != e0:
            t = (level - e0) / (e1 - e0)
            out_p.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
            out_e.append(level)
    return out_p, out_e


def clip_to_depth(pts_world, cam):
    """Clip a world-space polygon against the camera's near plane, so a body
    of water that extends behind the camera can still be projected."""
    def depth(p):
        return ((p[0] - cam.e) * cam.fwd[0] + (p[1] - cam.n) * cam.fwd[1]
                + (p[2] - cam.z) * cam.fwd[2])
    out = []
    n = len(pts_world)
    for i in range(n):
        p0, p1 = pts_world[i], pts_world[(i + 1) % n]
        d0, d1 = depth(p0), depth(p1)
        if d0 >= NEAR_CLIP:
            out.append(p0)
        if (d0 >= NEAR_CLIP) != (d1 >= NEAR_CLIP):
            t = (NEAR_CLIP - d0) / (d1 - d0)
            out.append(tuple(p0[k] + t * (p1[k] - p0[k]) for k in range(3)))
    return out


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    xj, yj = poly[-1]
    for i in range(n):
        xi, yi = poly[i]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi
            if x < xint:
                inside = not inside
        xj, yj = xi, yi
    return inside


def point_in_poly_ll(lat, lon, poly_latlon):
    return point_in_poly(lon, lat, [(p[1], p[0]) for p in poly_latlon])


# ═══════════════════════════════════════════════════════════════════════════
# drawing: the built content
# ═══════════════════════════════════════════════════════════════════════════
def ship(cam, terr, lat, lon, bearing, length=24.0, beam=4.2):
    """One beached galley, prow toward the water on `bearing`. Drawn as a
    hull solid plus stem and stern posts -- three shapes, no ornament. Every
    mark is a part of a ship; nothing here stands for tone."""
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)          # along the keel, toward the sea
    vx, vy = math.cos(th), -math.sin(th)         # across the beam
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)

    def W3(u, v, h):
        return cam.project(e0 + u * ux + v * vx, n0 + u * uy + v * vy,
                           built_h(h, g))

    # Seen from 800 m up and 2.4 km back, a beached galley is 17 px long and
    # 3 px in the beam, and the ground is 19 deg below the eye -- so what the
    # reader can actually be shown is the DECK in plan, a long leaf, with the
    # side just visible along one edge and the stem-post standing clear of it.
    # Three marks. A stern-post, oar-ports and strakes were all drawn in the
    # first cut and all of them, at this range, are sub-pixel: marks standing
    # for tone, which is the rule this project retired hachures over.
    stations = [(0.00, 0.30), (0.14, 0.46), (0.34, 0.50), (0.60, 0.48),
                (0.82, 0.36), (0.95, 0.18), (1.00, 0.06)]
    deck_h = 2.4
    top_r, top_l, side = [], [], []
    for f, hb in stations:
        u, v = f * length, hb * beam
        pr = W3(u, +v, deck_h)
        pl = W3(u, -v, deck_h)
        pg = W3(u, +v * 0.8, 0.0)
        if pr and pl and pg:
            top_r.append((pr[0], pr[1]))
            top_l.append((pl[0], pl[1]))
            side.append((pg[0], pg[1]))
    if len(top_r) < 5:
        return ""
    out = [f'<path d="{path_of(top_r + list(reversed(side)))}" class="pp-hull-side"/>',
           f'<path d="{path_of(top_r + list(reversed(top_l)))}" class="pp-hull"/>']
    base = W3(length * 0.98, 0.0, deck_h)
    mid = W3(length * 1.02, 0.0, 4.2)
    tip = W3(length * 0.90, 0.0, 6.4)
    if base and mid and tip:
        out.append(f'<path d="M{f2(base[0])} {f2(base[1])}'
                   f'Q{f2(mid[0])} {f2(mid[1])} {f2(tip[0])} {f2(tip[1])}" class="pp-post"/>')
    return "".join(out)


def hut(cam, terr, lat, lon, bearing, w=7.0, d=5.0, wall=1.8, ridge=3.2):
    """A klisie: low walls, a pitched roof. Two shapes."""
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)
    vx, vy = math.cos(th), -math.sin(th)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)

    def W3(u, v, h):
        return cam.project(e0 + u * ux + v * vx, n0 + u * uy + v * vy, built_h(h, g))

    # Two marks: the wall the reader can see (the near face, toward the
    # camera) and the roof plane above it. The first cut chained base and eave
    # corners into one ring and printed an L.
    fl = W3(-d / 2, -w / 2, 0)
    fr = W3(-d / 2, w / 2, 0)
    el_ = W3(-d / 2, -w / 2, wall)
    er = W3(-d / 2, w / 2, wall)
    bl = W3(d / 2, -w / 2, wall)
    br = W3(d / 2, w / 2, wall)
    rl = W3(0, -w / 2, ridge)
    rr = W3(0, w / 2, ridge)
    if any(p is None for p in (fl, fr, el_, er, bl, br, rl, rr)):
        return ""
    ol = W3(-d / 2 - 0.6, -w / 2 - 0.6, wall)
    orr = W3(-d / 2 - 0.6, w / 2 + 0.6, wall)
    if any(p is None for p in (ol, orr)):
        return ""
    P = lambda p: (p[0], p[1])
    face = [P(fl), P(fr), P(er), P(el_)]
    # the roof plane, eaves overhanging the wall on the near side: at five or
    # six pixels a hut gets two marks, and the overhang is what makes the
    # upper one read as a roof rather than as a second storey.
    roof_near = [P(ol), P(orr), P(rr), P(rl)]
    return (f'<path d="{path_of(face)}" class="pp-hut-wall"/>'
            f'<path d="{path_of(roof_near)}" class="pp-hut-roof"/>')


def city(cam, terr, centre, radius=105.0, wall_h=6.0, tower_h=9.5, n_towers=9):
    """Ilios on its spur: a walled citadel, towers standing above the curtain,
    the great tower and the gate turned to the plain, and roofs behind. The
    footprint is the Troy VI citadel's own order of size; the wall's line and
    every roof are conjectural. No masonry course is drawn -- at this range a
    course would be half a pixel, which is the definition of a mark standing
    for tone."""
    lat0, lon0 = centre
    g = terr.elev(lat0, lon0)
    mlat = 1.0 / 111132.0
    mlon = 1.0 / (111320.0 * math.cos(math.radians(lat0)))

    def at(dx, dy, h):
        return cam.project_ll(lat0 + dy * mlat, lon0 + dx * mlon, built_h(h, g))

    # the curtain: an oval, slightly flattened, with the long axis NE-SW
    def ring(f, h, n=64):
        out = []
        for k in range(n):
            a = 2 * math.pi * k / n
            dx = radius * f * math.cos(a)
            dy = radius * f * 0.86 * math.sin(a)
            p = at(dx, dy, h)
            if p:
                out.append((p[0], p[1]))
        return out

    base, top = ring(1.0, 0.0), ring(1.0, wall_h)
    if len(base) < 32 or len(top) < 32:
        return ""
    out = []
    # ── roofs, drawn first so the curtain stands in front of them: a stepped
    # skyline of gables across the citadel. Seven of them at 26 m each is six
    # pixels apiece here, which is the honest limit of what can be drawn.
    for k, (fx, fy, hh, wd) in enumerate([
            (-0.62, 0.30, 8.0, 26), (-0.34, 0.46, 10.5, 30), (-0.02, 0.34, 9.0, 26),
            (0.28, 0.50, 12.5, 32), (0.58, 0.30, 8.5, 26), (-0.20, 0.10, 11.0, 30),
            (0.34, 0.06, 9.5, 26)]):
        cxm, cym = radius * fx, radius * fy
        eaves = hh * 0.62
        a = at(cxm - wd / 2, cym, eaves)
        b = at(cxm + wd / 2, cym, eaves)
        rg = at(cxm, cym, hh)
        c_ = at(cxm + wd / 2, cym, 0.0)
        d2 = at(cxm - wd / 2, cym, 0.0)
        if a and b and rg and c_ and d2:
            poly = [(d2[0], d2[1]), (c_[0], c_[1]), (b[0], b[1]), (rg[0], rg[1]), (a[0], a[1])]
            out.append(f'<path d="{path_of(poly)}" class="pp-roof"/>')
    # The curtain: only the arc whose OUTER FACE the camera can see is filled
    # base-to-crest. Filling the whole ring, as the first cut did, wraps a band
    # right round the oval and prints a barrel -- or, with towers added at true
    # scale (3 px wide, 9 px tall), a wooden pen. At this range the honest
    # drawing is a massing: one wall face, one crest, one great tower.
    n = len(base)
    ix_min = min(range(n), key=lambda k: top[k][0])
    ix_max = max(range(n), key=lambda k: top[k][0])
    arc_a = [k % n for k in range(ix_min, ix_min + ((ix_max - ix_min) % n) + 1)]
    arc_b = [k % n for k in range(ix_max, ix_max + ((ix_min - ix_max) % n) + 1)]
    near = arc_a if (sum(top[k][1] for k in arc_a) / len(arc_a)
                     > sum(top[k][1] for k in arc_b) / len(arc_b)) else arc_b
    wall_poly = [top[k] for k in near] + [base[k] for k in reversed(near)]
    out.append(f'<path d="{path_of(wall_poly)}" class="pp-wall"/>')
    out.append('<path d="M' + "L".join(f"{f2(x)} {f2(y)}" for x, y in top) + 'Z" class="pp-wall-crest"/>')

    # The great tower, on the west face, over the plain and facing the camp.
    # 18 m across and half again the curtain's height: the one piece of the
    # circuit big enough to draw as a separate thing rather than a nick.
    gt = []
    for h in (tower_h * 1.6, 0.0):
        row = [at(-radius * 1.04, -9.0, h), at(-radius * 1.04, 9.0, h)]
        if any(p is None for p in row):
            gt = []
            break
        gt.append([(p[0], p[1]) for p in row])
    if gt:
        out.append(f'<path d="{path_of(gt[0] + list(reversed(gt[1])))}" class="pp-tower"/>')
    return "".join(out)


# ═══════════════════════════════════════════════════════════════════════════
# the sheet
# ═══════════════════════════════════════════════════════════════════════════
TOKENS = {
    "light": """
  --page-bg:#E7E7E9; --text:#241827; --text-mid:#5B4C58;
  --scene-map-label-halo:#F8F7F3; --scene-map-coast:#565060;
  --plate-lagoon:#87AEB8; --scene-map-sea:#9BBFD6; --plate-contour:#5A4A32;
  --plate-masonry:#A87263; --plate-river:#1A4C6A;
  --plate-relief-1:#EDEEDF; --plate-relief-2:#E8E8CF; --plate-relief-3:#E4E2C0;
  --plate-relief-4:#E1DAB3; --plate-relief-5:#DED3A7; --plate-relief-6:#DACB9E;
  --plate-relief-7:#D5C296; --plate-relief-8:#D0B98C; --plate-relief-9:#CAB083;
  --plate-relief-10:#C2A679; --plate-relief-11:#B99C6F; --plate-relief-12:#AF9164;
""",
    "dark": """
  --page-bg:#181120; --text:#EDE6E8; --text-mid:#B7A9B4;
  --scene-map-label-halo:#17131C; --scene-map-coast:#8FA3AE;
  --plate-lagoon:#0A2430; --scene-map-sea:#0A1C2A; --plate-contour:#C2B189;
  --plate-masonry:#A8846F; --plate-river:#B4DAEF;
  --plate-relief-1:#4A4136; --plate-relief-2:#51473A; --plate-relief-3:#584D3D;
  --plate-relief-4:#5F523F; --plate-relief-5:#655740; --plate-relief-6:#6B5C42;
  --plate-relief-7:#706043; --plate-relief-8:#766444; --plate-relief-9:#7A6846;
  --plate-relief-10:#7E6C48; --plate-relief-11:#836F49; --plate-relief-12:#86734B;
""",
}

CSS = """
.pp-band{stroke:none}
.pp-contour{fill:none;stroke:var(--plate-contour);stroke-width:0.6;stroke-opacity:0.62;
  stroke-linecap:round}
.pp-ida{fill:var(--plate-relief-12);fill-opacity:0.13;stroke:none}
.pp-ida-crest{fill:none;stroke:var(--plate-contour);stroke-width:0.7;stroke-opacity:0.35}
.pp-sea{fill:var(--scene-map-sea)}
.pp-lagoon{fill:var(--plate-lagoon)}
.pp-coast{fill:none;stroke:var(--scene-map-coast);stroke-width:1.1}
.pp-coast-approx{fill:none;stroke:var(--scene-map-coast);stroke-width:1.1;
  stroke-dasharray:4.5 3;stroke-linecap:round}
.pp-waterline{fill:none;stroke:var(--scene-map-coast);stroke-width:0.6;stroke-opacity:0.45}
.pp-hull{fill:var(--text-mid);stroke:var(--text);stroke-width:0.35;stroke-linejoin:round}
.pp-hull-side{fill:var(--text);stroke:none}
.pp-post{fill:none;stroke:var(--text);stroke-width:0.9;stroke-linecap:round}
.pp-hut-wall{fill:var(--text-mid);stroke:none}
.pp-hut-roof{fill:var(--plate-masonry);stroke:var(--text);stroke-width:0.3;
  stroke-linejoin:round}
.pp-wall{fill:var(--plate-masonry);stroke:var(--text);stroke-width:0.5;
  stroke-linejoin:round}
.pp-wall-crest{fill:none;stroke:var(--text);stroke-width:0.8}
.pp-tower{fill:var(--plate-masonry);stroke:var(--text);stroke-width:0.5;
  stroke-linejoin:round}
.pp-roof{fill:var(--text-mid);stroke:var(--text);stroke-width:0.4;stroke-linejoin:round}
.pp-leader{fill:none;stroke:var(--text-mid);stroke-width:0.8;stroke-opacity:0.75}
text{font-family:var(--font-ui,Optima,Seravek,"Gill Sans","Gill Sans MT",sans-serif);
  paint-order:stroke;stroke:var(--scene-map-label-halo);stroke-width:3.2;
  stroke-linejoin:round}
.pp-l-region{font-size:15.5px;letter-spacing:2.48px;fill:var(--text-mid)}
.pp-l-settlement{font-size:15px;font-weight:600;fill:var(--text)}
.pp-l-water{font-size:12.5px;font-style:italic;letter-spacing:0.5px;fill:var(--text-mid)}
"""


def build(theme: str, terr: Terrain, cam: Camera, plate) -> str:
    lay = {l["id"]: l for l in plate["layers"]}
    body = []

    # ── Ida: real Troad DEM skyline, painted first so the near ground
    # occludes it. It is 66 km out; the mesh stops at 45 km, so it is the only
    # thing between the mesh's far edge and the true horizon.
    ida_bearing = pp._bearing_deg(VIEWPOINT, pp.IDA_SUMMIT)
    sky = []
    b = AZ_MIN
    while b <= AZ_MAX + 1e-9:
        bearing = HEADING_DEG + b
        best_angle, best = -9e9, None
        d = 46000.0
        while d < 100000.0:
            lat, lon = pp._dest_point(VIEWPOINT, bearing, d)
            if 38.95 <= lat <= 40.6 and 25.35 <= lon <= 27.5:
                el = terr.elev(lat, lon)
                e, n = pp._flat_m((lat, lon), *VIEWPOINT)
                ang = math.atan2(el - cam.z, math.hypot(e - cam.e, n - cam.n))
                if ang > best_angle:
                    best_angle, best = ang, (e, n, el)
            d += 400.0
        if best:
            p = cam.project(*best)
            if p:
                sky.append((p[0], p[1]))
        b += 0.5
    if len(sky) > 3:
        sky.sort(key=lambda q: q[0])
        poly = sky + [(sky[-1][0], float(H) + 40), (sky[0][0], float(H) + 40)]
        body.append(f'<path d="{path_of(poly)}" class="pp-ida"/>')
        body.append('<path d="M' + "L".join(f"{f2(x)} {f2(y)}" for x, y in sky) + '" class="pp-ida-crest"/>')

    # ── polar mesh, far ring to near ring ────────────────────────────────
    azs = []
    a = AZ_MIN
    while a <= AZ_MAX + 1e-9:
        azs.append(a)
        a += AZ_STEP
    rngs = []
    r = RANGE_NEAR
    while r < RANGE_FAR:
        rngs.append(r)
        r *= RANGE_RATIO
    rngs.append(RANGE_FAR)

    # sample once: elevation + screen point on the (bearing, range) lattice
    grid = [[None] * len(rngs) for _ in azs]
    for i, az in enumerate(azs):
        bearing = HEADING_DEG + az
        th = math.radians(bearing)
        for j, rr in enumerate(rngs):
            e = cam.e + rr * math.sin(th)
            n = cam.n + rr * math.cos(th)
            lat = VIEWPOINT[0] + n / 111132.0
            lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
            el = terr.elev_smooth(lat, lon, max(40.0, rr * 0.006))
            p = cam.project(e, n, exaggerate(el))
            grid[i][j] = None if p is None else (p[0], p[1], el)

    # Rings are emitted far to near, one <path> per band per ring, so painter
    # order is exactly depth order -- a ridge occludes the ground behind it by
    # construction, with no depth sort anywhere. HAZE_CUTS are crossed on the
    # way in: a --page-bg rectangle laid down at that moment dims everything
    # already drawn and nothing still to come, which is atmospheric
    # perspective for the price of one rectangle per stratum.
    haze_cuts = [(30000.0, 0.20), (12000.0, 0.15), (5000.0, 0.09)]
    hz = 0
    for j in range(len(rngs) - 2, -1, -1):
        rr = rngs[j]
        while hz < len(haze_cuts) and rr < haze_cuts[hz][0]:
            body.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                        f'fill="var(--page-bg)" fill-opacity="{haze_cuts[hz][1]}"/>')
            hz += 1
        band_paths = {}
        contour_d = []
        for i in range(len(azs) - 1):
            a0, a1 = grid[i][j], grid[i + 1][j]
            b0, b1 = grid[i][j + 1], grid[i + 1][j + 1]
            if a0 is None or a1 is None or b0 is None or b1 is None:
                continue
            xs = [a0[0], a1[0], b1[0], b0[0]]
            ys = [a0[1], a1[1], b1[1], b0[1]]
            if max(xs) < FRAG_X0 - 20 or min(xs) > FRAG_X0 + FRAG_W + 20:
                continue
            if max(ys) < -20 or min(ys) > H + 20:
                continue
            quad = [(a0[0], a0[1]), (a1[0], a1[1]), (b1[0], b1[1]), (b0[0], b0[1])]
            evs = [a0[2], a1[2], b1[2], b0[2]]
            k0, k1 = band_of(min(evs)), band_of(max(evs))
            if k0 == k1:
                band_paths.setdefault(k0, []).append(path_of(quad))
            elif k1 == k0 + 1:
                lv = LEVELS[k0]
                lo_p, _ = clip_below(quad, evs, lv)
                hi_p, _ = clip_above(quad, evs, lv)
                if len(lo_p) >= 3:
                    band_paths.setdefault(k0, []).append(path_of(lo_p))
                if len(hi_p) >= 3:
                    band_paths.setdefault(k1, []).append(path_of(hi_p))
                # the isoline itself, drawn once, as the shared edge
                seg = []
                for m in range(4):
                    e0, e1 = evs[m], evs[(m + 1) % 4]
                    if (e0 - lv) * (e1 - lv) < 0:
                        t = (lv - e0) / (e1 - e0)
                        p0, p1 = quad[m], quad[(m + 1) % 4]
                        seg.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
                if len(seg) == 2:
                    contour_d.append(f"M{f2(seg[0][0])} {f2(seg[0][1])}L{f2(seg[1][0])} {f2(seg[1][1])}")
            else:
                kk = band_of(sum(evs) / 4.0)
                band_paths.setdefault(kk, []).append(path_of(quad))
        for k in sorted(band_paths):
            body.append(f'<path class="pp-band" fill="var(--plate-relief-{k + 1})" '
                        f'd="{"".join(band_paths[k])}"/>')
        if contour_d:
            body.append(f'<path class="pp-contour" d="{"".join(contour_d)}"/>')

    # ── water: projected reconstruction polygons over the terrain ────────
    def water_path(poly_latlon, z=0.0):
        # Densify before smoothing. Chaikin cuts corners, and on a polygon
        # whose vertices are 100 m apart -- 70 px near the camp -- it moved the
        # drawn shore up to 17 px off the measured one, which is how the first
        # cut beached its whole fleet in open water. Subdividing to 20 m first
        # keeps the smoothing to a rounding of the line rather than a
        # displacement of it.
        dense = []
        n_ = len(poly_latlon)
        for k in range(n_):
            a = poly_latlon[k]
            b = poly_latlon[(k + 1) % n_]
            seg = math.hypot(*pp._flat_m(b, a[0], a[1]))
            steps = max(1, int(seg / 20.0))
            for s in range(steps):
                t = s / steps
                dense.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        world = []
        for lat, lon in dense:
            e, n = pp._flat_m((lat, lon), *VIEWPOINT)
            world.append((e, n, z))
        clipped = clip_to_depth(world, cam)
        scr = []
        for wpt in clipped:
            p = cam.project(*wpt)
            if p:
                scr.append((p[0], p[1]))
        if len(scr) < 4:
            return None
        return chaikin(scr, passes=2, closed=True)

    # THE WATER SURFACE SITS AT THE LEVEL IT WAS CUT FROM. sea-modern is the
    # sea as it stands, so z=0. The bronze embayment is the 10 m contour of the
    # MODERN DEM standing in for the Late Bronze Age waterline (see the
    # lagoon-bronze and shore-bronze notes), so its surface is 10 m in this
    # scene's terms -- 40 m once the 4x exaggeration is applied. Drawn at z=0
    # it sank 27 px below the beach it is supposed to meet, and every ship
    # hauled up on that beach appeared to float in open water. This is the
    # whole of that defect: not the ships' placement, the water's level.
    sea = water_path(lay["sea-modern"]["polygon"], 0.0)
    lagoon = water_path(lay["lagoon-bronze"]["polygon"], exaggerate(10.0))
    if sea:
        body.append(f'<path d="{path_of(sea)}" class="pp-sea"/>')
        body.append(f'<path d="{path_of(sea)}" class="pp-coast"/>')
    if lagoon:
        body.append(f'<path d="{path_of(lagoon)}" class="pp-lagoon"/>')
        # waterlines: Huffman's growing gaps (x1.3), inside the water only
        gaps, d = [], 3.0
        for _ in range(3):
            gaps.append(d)
            d *= 1.3
        cx = sum(p[0] for p in lagoon) / len(lagoon)
        cy = sum(p[1] for p in lagoon) / len(lagoon)
        acc = 0.0
        for gap in gaps:
            acc += gap
            off = []
            n = len(lagoon)
            for i in range(n):
                x0, y0 = lagoon[(i - 1) % n]
                x1, y1 = lagoon[i]
                x2, y2 = lagoon[(i + 1) % n]
                tx, ty = x2 - x0, y2 - y0
                L = math.hypot(tx, ty) or 1e-9
                nx, ny = -ty / L, tx / L
                if (nx * (cx - x1) + ny * (cy - y1)) < 0:
                    nx, ny = -nx, -ny
                off.append((x1 + nx * acc, y1 + ny * acc, tx / L, ty / L))
            # A naive normal offset folds back on itself inside a tight
            # concavity, and the fold prints as a bow-tie on the water. Drop
            # any vertex whose offset segment now runs against the original
            # tangent -- the standard cheap de-looping, and enough at gaps
            # this small.
            keep = []
            for i in range(len(off)):
                ax, ay, tx, ty = off[i]
                bx, by, _, _ = off[(i + 1) % len(off)]
                if (bx - ax) * tx + (by - ay) * ty >= 0:
                    keep.append((ax, ay))
            if len(keep) > 8:
                body.append(f'<path d="{path_of(keep)}" class="pp-waterline"/>')
        body.append(f'<path d="{path_of(lagoon)}" class="pp-coast-approx"/>')

    # ── the camp: ships on the beach, huts on the ridge behind ───────────
    lagoon_poly = lay["lagoon-bronze"]["polygon"]
    camp_zone = lay["achaean-camp-zone"]["polygon"]

    def shore_forward(lateral):
        """March out along the heading at this lateral offset and return the
        forward distance at which the ground becomes water. Data-driven: no
        ship is placed at a guessed coordinate, only against the measured
        shoreline."""
        th = math.radians(HEADING_DEG)
        lo, hi = None, None
        f = 100.0
        while f < 4500.0:
            e = f * math.sin(th) + lateral * math.cos(th)
            n = f * math.cos(th) - lateral * math.sin(th)
            lat = VIEWPOINT[0] + n / 111132.0
            lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
            if point_in_poly_ll(lat, lon, lagoon_poly):
                hi = f
                break
            lo = f
            f += 25.0
        return lo if hi is not None else None

    def near_camp(lat, lon, margin_m=380.0):
        """Inside the attributed camp zone, or within `margin_m` of it. The
        zone traces the LANDFORM the camp is set against (see the layer's own
        note), not the camp's extent, so a strict inside-test put every ship
        off the beach: the beach is a couple of hundred metres seaward of the
        ridge outline. The margin is the ridge-to-water frontage, not a claim
        about where any ship lay."""
        if point_in_poly_ll(lat, lon, camp_zone):
            return True
        for plat, plon in camp_zone:
            if math.hypot(*pp._flat_m((plat, plon), lat, lon)) < margin_m:
                return True
        return False

    ships, huts, ship_px = [], [], []
    th = math.radians(HEADING_DEG)
    for lateral in [x * 26.0 for x in range(-30, 65)]:
        fs = shore_forward(lateral)
        if fs is None:
            continue
        for row in range(2):
            # the anchor is the STERN and the hull runs 24 m seaward of it,
            # so a 34 m setback beached the bow in open water.
            f = fs - 66.0 - row * 42.0 + (13.0 if row % 2 else 0.0)
            if f < 60:
                continue
            e = f * math.sin(th) + lateral * math.cos(th)
            n = f * math.cos(th) - lateral * math.sin(th)
            lat = VIEWPOINT[0] + n / 111132.0
            lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
            if terr.elev(lat, lon) > 16.0 or not near_camp(lat, lon):
                continue
            sh = ship(cam, terr, lat, lon, HEADING_DEG)
            if sh:
                ships.append(sh)
                sp = cam.project_ll(lat, lon, built_h(2.4, terr.elev(lat, lon)))
                if sp:
                    ship_px.append((sp[0], sp[1]))
    for lateral in [x * 44.0 for x in range(-18, 38)]:
        fs = shore_forward(lateral)
        if fs is None:
            continue
        for row in range(5):
            f = fs - 190.0 - row * 58.0
            if f < 40:
                continue
            e = f * math.sin(th) + lateral * math.cos(th)
            n = f * math.cos(th) - lateral * math.sin(th)
            lat = VIEWPOINT[0] + n / 111132.0
            lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
            if not near_camp(lat, lon, 260.0):
                continue
            huts.append(hut(cam, terr, lat, lon, HEADING_DEG + (17 if row % 2 else -11)))
    body.append("".join(h for h in huts if h))
    body.append("".join(s for s in ships if s))

    # ── Ilios ────────────────────────────────────────────────────────────
    body.append(city(cam, terr, pp.TROY))

    # ── labels ───────────────────────────────────────────────────────────
    tp = cam.project_ll(pp.TROY[0], pp.TROY[1], built_h(9.5, terr.elev(*pp.TROY)))
    if tp:
        lx, ly = tp[0] + 30, tp[1] - 34
        body.append(f'<path d="M{f2(tp[0] + 4)} {f2(tp[1] - 6)}L{f2(lx - 4)} {f2(ly + 4)}" class="pp-leader"/>')
        body.append(f'<text class="pp-l-settlement" x="{f2(lx)}" y="{f2(ly)}">Ilios</text>')
    bp = cam.project_ll(39.9880, 26.2060, 0.0)
    if bp:
        body.append(f'<text class="pp-l-water" x="{f2(bp[0])}" y="{f2(bp[1])}" text-anchor="middle">the bay of Troy</text>')
    if ship_px:
        inside = [q for q in ship_px if FRAG_X0 + 90 < q[0] < FRAG_X0 + FRAG_W - 90] or ship_px
        lx = sum(q[0] for q in inside) / len(inside)
        ly = max(q[1] for q in inside) + 46
        body.append(f'<text class="pp-l-region" x="{f2(lx)}" y="{f2(ly)}" text-anchor="middle">THE SHIPS</text>')
    return "".join(body)


def emit(theme, inner, vx, vy, vw, vh, scale, out_svg):
    px_w, px_h = int(round(vw * scale)), int(round(vh * scale))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{px_w}" height="{px_h}" '
        f'viewBox="{f2(vx)} {f2(vy)} {f2(vw)} {f2(vh)}">'
        f'<style>svg{{{TOKENS[theme]}}}{CSS}</style>'
        f'<rect x="{f2(vx)}" y="{f2(vy)}" width="{f2(vw)}" height="{f2(vh)}" fill="var(--page-bg)"/>'
        f'{inner}</svg>'
    )
    with open(out_svg, "w") as f:
        f.write(svg)
    return px_w, px_h


def shoot(svg_path, png_path, w, h):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--screenshot={png_path}", svg_path],
                   check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(REPO, "build", "panorama"))
    ap.add_argument("--crop", nargs=4, type=float, default=[1180, 380, 300, 220],
                    help="x y w h of the 3.5x detail crop, in frame units")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    terr = Terrain()
    cam = Camera(terr.plain)
    with open(os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")) as f:
        plate = json.load(f)

    print(f"pitch {math.degrees(cam.pitch):.2f} deg down; focal {FOCAL:.1f}; "
          f"horizon y={H / 2 - FOCAL * math.tan(-cam.pitch) * -1:.0f}")
    for theme in ("light", "dark"):
        inner = build(theme, terr, cam, plate)
        suffix = "" if theme == "light" else "-dark"
        svg = os.path.join(args.out_dir, f"stage2-fragment{suffix}.svg")
        w, h = emit(theme, inner, FRAG_X0, 0, FRAG_W, H, 1.0, svg)
        shoot(svg, os.path.join(args.out_dir, f"stage2-fragment{suffix}.png"), w, h)
        for name, (cx, cy, cw, ch) in (("ilios", tuple(args.crop)),
                                       ("camp", (1250.0, 700.0, 300.0, 220.0))):
            svg2 = os.path.join(args.out_dir, f"stage2-{name}-3x5{suffix}.svg")
            w2, h2 = emit(theme, inner, cx, cy, cw, ch, 3.5, svg2)
            shoot(svg2, os.path.join(args.out_dir, f"stage2-{name}-3x5{suffix}.png"), w2, h2)
        print(f"[{theme}] {os.path.getsize(svg) / 1024:.0f} KB svg -> {w}x{h}, plus 3.5x crops")


if __name__ == "__main__":
    main()
