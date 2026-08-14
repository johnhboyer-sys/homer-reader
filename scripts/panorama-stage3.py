#!/usr/bin/env python3
"""Stage 3 — THE WHOLE PLATE: "The Ships, the Bay, and Ilios".

The full 2400x1350 raised oblique from the settled Stage-1D camera, in the
Stage-2 register (hypsometric bands with true-isoline edges, hairline
contours, waterlines, the dashed approximate bronze shore, flat fills, no
texture), carrying what Stage 2 still owed: the delta swamp with a faded
margin, the neatline, the scale and the hypsometric key.

WHAT IS NEW HERE, against Stage 2
  1. THE PLATE IS NAVIGABLE, and that changes what "legible" means. Stage 2
     measured Ilios at 50 px and judged it illegible. That was the wrong bar:
     1x is an overview, and detail arrives on zoom -- at 4x the hulls are
     ~64 px and Ilios ~200 px. So the wide oblique stands.
  2. LEVEL OF DETAIL, in content as well as in labels. Three tiers, carried
     as CSS classes on the shipping SVG so a panel can switch them:
       t1  the overview: Ilios, Scamander, the bay, Ida, and the camp -- the
           ships as ONE SERRATED MASS with the huts behind it. (The huts sit
           at tier 1 on purpose: without them the near third of the frame is
           bare ridge, and a mass of ships with no camp behind it reads as a
           mark rather than as an army's quarters.)
       t2  ~2-3x: individual hulls resolve out of the mass; the delta swamp,
           the Simoeis, the ford, both headlands, Callicolone, the Achaean
           wall and its ditch, the throsmos
       t3  ~4x+: the wagon-road and everything strung along it -- the Scaean
           Gate and the oak, the lookout, the fig tree, the two springs, the
           tomb of Ilos, Batieia, the wall of Heracles -- and the camp
           sectors by holder (Ajax's end, Odysseus in the middle with the
           assembly, Achilles' end), each end named by MEASURING it against
           the two headlands, never by left/right in the frame
     Labels carry class `plate-label`, which is what PlatePanel's existing
     descale hook wraps, so type never magnifies with zoom.
  3. WEIGHT. Stage 2 spent 2.26 MB on a third of the frame. Three things fix
     that and none of them changes the drawing:
       - FLOATING-HORIZON CULL. The mesh is a single-valued height field seen
         from above, so marching each screen column from near to far and
         keeping the running silhouette tells you exactly which cells are
         hidden. Roughly two cells in five never had to be emitted.
       - LATTICE UNION. Cells whose four corners share a band are unioned per
         depth stratum by boundary extraction, so a blob of 900 same-band
         cells costs its perimeter (~120 points), not 3600. Only the cells a
         hypsometric level actually crosses are emitted individually, and
         those are the ones carrying the isoline, which is the whole point of
         the register.
       - RELATIVE PATH DATA, emitted against the ALREADY-ROUNDED pen position
         so rounding error cannot accumulate along a long loop.
  4. THE SHIPS HAVE THEIR OWN TOKENS. Stage 2 keyed hulls to --text, which
     inverts: Homer's black ships went pale in dark theme. They now carry
     --pp-hull / --pp-hull-side / --pp-hull-edge, dark in BOTH themes, with
     the edge token doing the separating -- a dark hull on dark ground needs
     a light rim, not a light hull.

POSITIONS. Terrain, coastlines, the rivers, Hisarlik, Callicolone, Sigeion
and Rhoiteion are measured. Everything the poem leaves unplaced -- the ford,
the oak, the fig tree, the lookout, the springs, the tomb of Ilos, the
wagon-road, the Achaean wall and ditch, the throsmos, Batieia, the wall of
Heracles, every hull and hut -- is emitted with positionBasis "conjectural"
and its Iliad citation IN THE DATA. No coordinate is invented: each
conjectural waypoint is placed by a stated rule against measured ground, and
the rule travels with it in the camera-target table.

VERTICAL EXAGGERATION is a RATE that is INTEGRATED, not a multiplier that is
applied (see ve/exaggerate below: the multiplier form inverted, drawing a
300 m ridge shorter than a 100 m hill). Built heights are TRUE (Stage 2's
finding: a 4x stem-post reads as a mast). Disclosed on the plate.

Usage
  python3 scripts/panorama-stage3.py               # both themes, all renders
  python3 scripts/panorama-stage3.py --quick       # light theme, 1x only
  python3 scripts/panorama-stage3.py --curve B     # a different height curve
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

# ── mesh. Columns are UNIFORM IN SCREEN X (so azimuth density follows the
# tangent, which is what keeps far-edge cells the same size as centre cells);
# rings are stepped to a target screen-y separation on flat ground. ──────
COL_PX = 7.2
RING_PX = 8.2
RANGE_NEAR, RANGE_FAR = 420.0, 45000.0
BLEED = 90.0                      # screen units of mesh outside the frame

# ── ring spacing has a GROUND floor as well as a screen one ──────────────
# RING_PX alone sets ring spacing from screen separation ON FLAT GROUND, and
# that rule under-resolves the TERRAIN at range: 8.2 flat pixels is 17 m of
# ground at 1 km and 332 m at 7 km. Any landform narrower than the local ring
# spacing is not smoothed, it is never sampled -- the mesh draws a straight
# ramp between the two rings that straddle it.
#
# That is what was flattening Ilios. Hisarlik's bluff climbs 24 m over about
# 250 m of ground, and at Troy's 7.0 km the rings sat 332 m apart, so the
# citadel fell inside a single cell and drew at 29.7 m instead of its measured
# 34.6 m -- one hypsometric band low, with the 30 m isoline that ought to ring
# the citadel missing. The DEM was never the problem: 10+2 box-blur passes
# cost the mound 1.4 m of 25 (prep-terrain-contours.py SHEETS['trojan-plain']).
# The mesh was.
#
# So rings are also capped in METRES over the range where the plate's own
# subject lies -- the extent of the trojan-plain z13 sheet, which the sightline
# leaves at about 19 km. 110 m is the grid's own resolving power: 12 box-blur
# passes at 14.65 m/px is a Gaussian of sigma 41 m, so nothing narrower than
# ~85 m survives in the data and a finer mesh would only resample the blur.
# THIS IS NOT A FIX FOR TROY. It is a floor on the whole near-and-middle
# field, and it lifts every landform of that scale: Callicolone (150 -> 191 m
# of 209 measured), Rhoiteion, Kesik Tepe, the Sigeion bluff's own edge.
# Beyond 19 km the ground comes from the troad z11 sheet, whose 117 m samples
# have nothing finer to give, and the flat-ground rule takes over again.
#
# The metre cap gets a floor of its own the other way, and it is about the
# raster, not about the ground: left alone the cap drives rings to 0.4 screen
# pixels apart at 15 km, which emits cells the sheet cannot show. RING_MIN_PX
# stops at one pixel. It costs Callicolone its last 4% (191 m drawn against
# 209 measured) and saves 46 KB of the shipped SVG.
RING_MAX_M = 110.0
RING_DETAIL_FAR = 19000.0
RING_MIN_PX = 1.0

LEVELS = [5, 10, 15, 20, 30, 45, 70, 110, 180, 300, 600]  # 11 levels, 12 bands

# depth strata: painter order is by stratum, far first. Within a stratum the
# depth spread is small enough that a band union cannot mis-occlude.
STRATA_EDGES = [45000.0, 26000.0, 16000.0, 10500.0, 7000.0, 4800.0,
                3300.0, 2300.0, 1600.0, 1100.0, 750.0, 0.0]
# haze applied on crossing INTO the stratum whose far edge is the key
HAZE = {26000.0: 0.20, 10500.0: 0.13, 4800.0: 0.09, 2300.0: 0.05}

PLAIN_BBOX = (39.86, 40.05, 26.1, 26.38)


# ── vertical exaggeration ────────────────────────────────────────────────
# ve() IS A RATE, NOT A MULTIPLIER. It is d(apparent)/d(real), and apparent
# height is its INTEGRAL from sea level -- not the product e * ve(e).
#
# The product form was NON-MONOTONIC and drew high ground low. With the
# 4x-to-1x taper as a multiplier, apparent(e) = 5.5e - 0.015e^2: it peaks at
# e = 183.3 m (504.2 apparent) and falls away after, so
#       100 m -> 400      183 m -> 504      267 m -> 400      300 m -> 300
# and a 300 m ridge printed SHORTER than a 100 m hill. About a fifth of the
# plain sheet's ground (p80 = 107 m, p90 = 190 m) sat inside that inverting
# band, which is exactly the middle-distance ridge line the plate's skyline
# is made of. A decreasing multiplier applied to a rising input need not
# produce a rising product, and here it did not.
#
# The integral cannot invert: apparent(e) = INT(0..e) ve(t) dt is strictly
# increasing wherever ve > 0, whatever shape the taper takes. That is the
# whole fix, and it is why ve() is now documented as a rate.
#
# THREE CURVES, because the integral changes the composition and that is
# John's call, not the draughtsman's (--curve):
#   A  the legacy product form. NON-MONOTONIC; kept only so the baseline
#      render is reproducible. Delete once a curve is chosen.
#   B  the integral of the SAME rate law A used (4x to 1x over 100-300 m,
#      1x above). Near ground is bit-identical to A; every ridge above
#      183 m rises, and the lift is a flat +600 m once the rate reaches 1x.
#   C  the integral of an exponential taper -- 4x at the shore, decaying
#      with a 150 m scale to a floor set so that MOUNT IDA KEEPS ITS PRESENT
#      APPARENT HEIGHT. Near ground reads as now, the ridges are put in true
#      order, and the horizon does not move.
CURVE = "C"

C_L = 150.0           # decay scale: the excess over the floor halves at
                      # L*ln2 = 104 m, which is where the plain sheet's own
                      # p80 (107 m) puts the plain's edge and the ridges'
                      # start -- the taper follows the terrain's own break.
IDA_M = 1774.0        # published Kaz Dagi summit (panorama-profile.py:
                      # DEM 1757.4 measured, 1774 published). Curve C's floor
                      # is solved so exaggerate(IDA_M) == IDA_M.
_C_K = C_L * (1.0 - math.exp(-IDA_M / C_L))
C_F = (IDA_M - 4.0 * _C_K) / (IDA_M - _C_K)      # ~0.7229


def ve(e: float, curve: str | None = None) -> float:
    """The exaggeration RATE at real elevation `e` metres: d(apparent)/d(real).
    Strictly positive on every curve, which is what makes exaggerate()
    monotonic."""
    c = curve or CURVE
    if c == "C":
        return C_F + (4.0 - C_F) * math.exp(-e / C_L)
    t = min(1.0, max(0.0, (e - 100.0) / 200.0))   # A and B share this rate law
    return 4.0 + t * (1.0 - 4.0)


def exaggerate(e: float, curve: str | None = None) -> float:
    """Apparent height (drawing metres) for a real elevation, = INT(0..e) ve."""
    c = curve or CURVE
    if c == "A":                       # legacy product form; DO NOT SHIP
        return e * ve(e, "A")
    if e <= 0.0:                       # the DEM dips a metre or so below zero
        return 4.0 * e                 # extend at the sea-level rate
    if c == "C":
        return C_F * e + (4.0 - C_F) * C_L * (1.0 - math.exp(-e / C_L))
    if e <= 100.0:                     # B, piecewise integral of the rate law
        return 4.0 * e
    if e <= 300.0:
        d = e - 100.0
        return 400.0 + 4.0 * d - 0.0075 * d * d
    return 900.0 + (e - 300.0)


DISCLOSURE = {
    "A": "Vertical exaggeration 4× at and under 100 m, tapering to 1× above "
         "300 m; built heights TRUE.",
    "B": "Vertical exaggeration 4× at and under 100 m, easing to 1× above "
         "300 m — applied as a rate and integrated, so higher ground always "
         "draws higher. Built heights TRUE.",
    "C": "Vertical exaggeration 4× at the shore, easing to %.2f× on the high "
         "ground — applied as a rate and integrated, so higher ground always "
         "draws higher and Mount Ida keeps its true height. Built heights "
         "TRUE." % C_F,
}


def ring_ranges(flat_y) -> list[float]:
    """The mesh's radial sampling, near to far. `flat_y(r)` is the screen y of
    flat ground at range r; it is the only thing the rule needs from the
    camera, which is what makes the rule testable without a DEM.

    Rings are stepped to RING_PX of screen separation ON FLAT GROUND, then
    held to RING_MAX_M of ground inside RING_DETAIL_FAR and to RING_MIN_PX of
    screen everywhere. See the comment on RING_MAX_M for why the screen rule
    alone is not enough."""
    rngs, r = [RANGE_NEAR], RANGE_NEAR
    y0 = flat_y(r)
    while r < RANGE_FAR:
        step = max(6.0, r * 0.008)
        nr = r + step
        while nr < RANGE_FAR and (y0 - flat_y(nr)) < RING_PX:
            nr += step
        cap = r + RING_MAX_M if r < RING_DETAIL_FAR else RANGE_FAR
        rc = min(nr, RANGE_FAR, cap)
        while rc < nr and (y0 - flat_y(rc)) < RING_MIN_PX:
            rc += step
        r = min(rc, nr, RANGE_FAR)
        y0 = flat_y(r)
        rngs.append(r)
    return rngs


def built_h(metres: float, ground_elev: float) -> float:
    """A TRUE built height on top of the exaggerated ground (Stage 2's
    finding: stretching a 6.4 m stem-post by the terrain's 4x turned every
    beached galley into a ship under mast)."""
    return exaggerate(ground_elev) + metres


# ═══════════════════════════════════════════════════════════════════════════
# camera / terrain  (Stage 2's, unchanged)
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
        self.right = (math.cos(self.theta), -math.sin(self.theta), 0.0)
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


class Terrain:
    def __init__(self):
        self.plain, _, _ = pp.load_plain_grid()
        self.troad, _ = ptc.build_sheet("troad", pp.CACHE)
        self._cache: dict = {}

    def elev(self, lat, lon):
        a, b, c, d = PLAIN_BBOX
        if a <= lat <= b and c <= lon <= d:
            return pp.bilinear_elev(self.plain, lat, lon)
        if 38.95 <= lat <= 40.6 and 25.35 <= lon <= 27.5:
            return pp.bilinear_elev(self.troad, lat, lon)
        return 0.0

    def elev_smooth(self, lat, lon, radius_m):
        """Nine-point stencil at a radius that grows with range: the DEM is
        quantised, and a flat plateau straddling a hypsometric level prints as
        a rectilinear terrace. Generalising far ground harder than near ground
        is also just what a draughtsman does."""
        if radius_m <= 0:
            return self.elev(lat, lon)
        dlat = radius_m / 111132.0
        dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
        tot = self.elev(lat, lon) * 2.0
        wsum = 2.0
        for dx, dy, w in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                          (0.7, 0.7, 0.7), (-0.7, 0.7, 0.7), (0.7, -0.7, 0.7),
                          (-0.7, -0.7, 0.7)):
            tot += self.elev(lat + dy * dlat, lon + dx * dlon) * w
            wsum += w
        return tot / wsum


def band_of(elev: float) -> int:
    for i, lv in enumerate(LEVELS):
        if elev < lv:
            return i
    return len(LEVELS)


# ═══════════════════════════════════════════════════════════════════════════
# path emission: relative data against the already-rounded pen
# ═══════════════════════════════════════════════════════════════════════════
def n1(v: float) -> str:
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0.") and len(s) > 2:
        s = s[1:]
    elif s.startswith("-0.") and len(s) > 3:
        s = "-" + s[2:]
    return s


def rel_poly(pts, close=True) -> str:
    """Relative path data. The pen position is tracked as the ROUNDED value
    actually written, so error cannot accumulate along a long loop."""
    if not pts:
        return ""
    px, py = round(pts[0][0], 1), round(pts[0][1], 1)
    out = [f"M{n1(px)} {n1(py)}"]
    body = []
    for x, y in pts[1:]:
        dx, dy = round(x - px, 1), round(y - py, 1)
        if dx == 0 and dy == 0:
            continue
        px, py = round(px + dx, 1), round(py + dy, 1)
        sy = n1(dy)
        body.append(f"{n1(dx)}{'' if sy.startswith('-') else ' '}{sy}")
    if not body:
        return ""
    out.append("l" + "".join(
        s if s.startswith("-") else (" " + s) for s in body).lstrip())
    return "".join(out) + ("Z" if close else "")


def rel_seg(a, b) -> str:
    ax, ay = round(a[0], 1), round(a[1], 1)
    dx, dy = round(b[0] - ax, 1), round(b[1] - ay, 1)
    sy = n1(dy)
    return f"M{n1(ax)} {n1(ay)}l{n1(dx)}{'' if sy.startswith('-') else ' '}{sy}"


def simplify(pts, tol=0.7, closed=True):
    """Ramer-Douglas-Peucker. A lattice union loop is a staircase and a
    densified-then-smoothed shoreline carries points a tenth of a pixel apart;
    neither is information, and both are most of the file. Tolerance is well
    under the 1.1 px hairline the plate strokes with, so the drawing does not
    change -- only its cost."""
    if len(pts) < 4:
        return pts
    ring = pts + [pts[0]] if closed else pts
    keep = [False] * len(ring)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        ax, ay = ring[a]
        bx, by = ring[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        worst, wi = -1.0, -1
        for k in range(a + 1, b):
            px_, py_ = ring[k]
            if L < 1e-9:
                dd = math.hypot(px_ - ax, py_ - ay)
            else:
                dd = abs(dy * px_ - dx * py_ + bx * ay - by * ax) / L
            if dd > worst:
                worst, wi = dd, k
        if worst > tol:
            keep[wi] = True
            stack.append((a, wi))
            stack.append((wi, b))
    out = [ring[k] for k in range(len(ring)) if keep[k]]
    if closed:
        out = out[:-1]
    return out if len(out) >= (3 if closed else 2) else pts


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
    out_p = []
    n = len(poly)
    for i in range(n):
        p0, e0 = poly[i], evals[i]
        p1, e1 = poly[(i + 1) % n], evals[(i + 1) % n]
        if e0 <= level:
            out_p.append(p0)
        if (e0 <= level) != (e1 <= level) and e1 != e0:
            t = (level - e0) / (e1 - e0)
            out_p.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
    return out_p


def clip_above(poly, evals, level):
    out_p = []
    n = len(poly)
    for i in range(n):
        p0, e0 = poly[i], evals[i]
        p1, e1 = poly[(i + 1) % n], evals[(i + 1) % n]
        if e0 >= level:
            out_p.append(p0)
        if (e0 >= level) != (e1 >= level) and e1 != e0:
            t = (level - e0) / (e1 - e0)
            out_p.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
    return out_p


def clip_to_depth(pts_world, cam):
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
# lattice union: boundary loops of a set of cells on an (i, j) lattice
# ═══════════════════════════════════════════════════════════════════════════
def union_loops(cells, corner):
    """`cells` is a set of (i, j); `corner(i, j)` returns the screen point of
    lattice node (i, j). A cell (i,j) has corners (i,j) (i+1,j) (i+1,j+1)
    (i,j+1). Returns a list of closed screen-space loops covering exactly the
    union of those cells -- interior edges are dropped, so a solid blob costs
    its perimeter."""
    # Directed boundary edges, wound so the interior is consistently on one
    # side. A node starts TWO of them wherever two cells of the set meet only
    # at a corner, so the map has to hold a LIST: keeping one target per node
    # loses the other, the chain closes early, and the result is a small
    # unpainted notch in the middle of a solid band.
    edges: dict = {}

    def push(a, b):
        edges.setdefault(a, []).append(b)

    for (i, j) in cells:
        if (i, j - 1) not in cells:
            push((i, j), (i + 1, j))
        if (i + 1, j) not in cells:
            push((i + 1, j), (i + 1, j + 1))
        if (i, j + 1) not in cells:
            push((i + 1, j + 1), (i, j + 1))
        if (i - 1, j) not in cells:
            push((i, j + 1), (i, j))

    def take(node):
        tgt = edges[node].pop()
        if not edges[node]:
            del edges[node]
        return tgt

    loops = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        node = take(start)
        while node != start and node in edges:
            loop.append(node)
            node = take(node)
        if len(loop) >= 3:
            loops.append([corner(*nd) for nd in loop])
    return loops


# ═══════════════════════════════════════════════════════════════════════════
# built content
# ═══════════════════════════════════════════════════════════════════════════
def ship(cam, terr, lat, lon, bearing, length=24.0, beam=4.2):
    """One beached galley, prow toward the water. Deck in plan, the visible
    side along one edge, the stem-post standing clear: three marks, which at
    17 px is the honest limit."""
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)
    vx, vy = math.cos(th), -math.sin(th)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)

    def W3(u, v, h):
        return cam.project(e0 + u * ux + v * vx, n0 + u * uy + v * vy, built_h(h, g))

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
    out = [f'<path d="{rel_poly(top_r + list(reversed(side)))}" class="pp-hull-side"/>',
           f'<path d="{rel_poly(top_r + list(reversed(top_l)))}" class="pp-hull"/>']
    base = W3(length * 0.98, 0.0, deck_h)
    mid = W3(length * 1.02, 0.0, 4.2)
    tip = W3(length * 0.90, 0.0, 6.4)
    if base and mid and tip:
        out.append(f'<path d="M{n1(base[0])} {n1(base[1])}'
                   f'Q{n1(mid[0])} {n1(mid[1])} {n1(tip[0])} {n1(tip[1])}" class="pp-post"/>')
    return "".join(out)


def hut(cam, terr, lat, lon, bearing, w=7.0, d=5.0, wall=1.8, ridge=3.2):
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)
    vx, vy = math.cos(th), -math.sin(th)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)

    def W3(u, v, h):
        return cam.project(e0 + u * ux + v * vx, n0 + u * uy + v * vy, built_h(h, g))

    fl, fr = W3(-d / 2, -w / 2, 0), W3(-d / 2, w / 2, 0)
    el_, er = W3(-d / 2, -w / 2, wall), W3(-d / 2, w / 2, wall)
    rl, rr = W3(0, -w / 2, ridge), W3(0, w / 2, ridge)
    ol, orr = W3(-d / 2 - 0.6, -w / 2 - 0.6, wall), W3(-d / 2 - 0.6, w / 2 + 0.6, wall)
    if any(p is None for p in (fl, fr, el_, er, rl, rr, ol, orr)):
        return ""
    P = lambda p: (p[0], p[1])
    return (f'<path d="{rel_poly([P(fl), P(fr), P(er), P(el_)])}" class="pp-hut-wall"/>'
            f'<path d="{rel_poly([P(ol), P(orr), P(rr), P(rl)])}" class="pp-hut-roof"/>')


def city(cam, terr, centre, radius=105.0, wall_h=6.0, tower_h=9.5):
    """Ilios on its spur, as a massing: one wall face, one crest, the great
    tower over the plain, a stepped skyline of roofs behind. At 1x this is a
    50 px mark; the DETAILED city is a separate artifact, and this plate does
    not pretend otherwise."""
    lat0, lon0 = centre
    g = terr.elev(lat0, lon0)
    mlat = 1.0 / 111132.0
    mlon = 1.0 / (111320.0 * math.cos(math.radians(lat0)))

    def at(dx, dy, h):
        return cam.project_ll(lat0 + dy * mlat, lon0 + dx * mlon, built_h(h, g))

    def ring(f, h, n=64):
        out = []
        for k in range(n):
            a = 2 * math.pi * k / n
            p = at(radius * f * math.cos(a), radius * f * 0.86 * math.sin(a), h)
            if p:
                out.append((p[0], p[1]))
        return out

    base, top = ring(1.0, 0.0), ring(1.0, wall_h)
    if len(base) < 32 or len(top) < 32:
        return ""
    out = []
    for fx, fy, hh, wd in [
            (-0.62, 0.30, 8.0, 26), (-0.34, 0.46, 10.5, 30), (-0.02, 0.34, 9.0, 26),
            (0.28, 0.50, 12.5, 32), (0.58, 0.30, 8.5, 26), (-0.20, 0.10, 11.0, 30),
            (0.34, 0.06, 9.5, 26)]:
        cxm, cym = radius * fx, radius * fy
        eaves = hh * 0.62
        a = at(cxm - wd / 2, cym, eaves)
        b = at(cxm + wd / 2, cym, eaves)
        rg = at(cxm, cym, hh)
        c_ = at(cxm + wd / 2, cym, 0.0)
        d2 = at(cxm - wd / 2, cym, 0.0)
        if a and b and rg and c_ and d2:
            out.append('<path d="%s" class="pp-roof"/>' % rel_poly(
                [(d2[0], d2[1]), (c_[0], c_[1]), (b[0], b[1]), (rg[0], rg[1]), (a[0], a[1])]))
    n = len(base)
    ix_min = min(range(n), key=lambda k: top[k][0])
    ix_max = max(range(n), key=lambda k: top[k][0])
    arc_a = [k % n for k in range(ix_min, ix_min + ((ix_max - ix_min) % n) + 1)]
    arc_b = [k % n for k in range(ix_max, ix_max + ((ix_min - ix_max) % n) + 1)]
    near = arc_a if (sum(top[k][1] for k in arc_a) / len(arc_a)
                     > sum(top[k][1] for k in arc_b) / len(arc_b)) else arc_b
    out.append('<path d="%s" class="pp-wall"/>' % rel_poly(
        [top[k] for k in near] + [base[k] for k in reversed(near)]))
    out.append('<path d="%s" class="pp-wall-crest"/>' % rel_poly(top))
    gt = []
    for h in (tower_h * 1.6, 0.0):
        row = [at(-radius * 1.04, -9.0, h), at(-radius * 1.04, 9.0, h)]
        if any(p is None for p in row):
            gt = []
            break
        gt.append([(p[0], p[1]) for p in row])
    if gt:
        out.append('<path d="%s" class="pp-tower"/>' % rel_poly(gt[0] + list(reversed(gt[1]))))
    return "".join(out)


def draped_ribbon(cam, terr, latlons, half_w_m, cls, z_off=0.0, taper=None):
    """A line feature draped on the terrain and drawn as a POLYGON of true
    width -- a river 40 m across cannot be a constant stroke over a 40 km
    depth range."""
    left, right = [], []
    n = len(latlons)
    for k, (lat, lon) in enumerate(latlons):
        if k == 0:
            b = pp._bearing_deg(latlons[0], latlons[1])
        elif k == n - 1:
            b = pp._bearing_deg(latlons[n - 2], latlons[n - 1])
        else:
            b = pp._bearing_deg(latlons[k - 1], latlons[k + 1])
        th = math.radians(b + 90.0)
        hw = half_w_m * (taper(k / max(1, n - 1)) if taper else 1.0)
        dlat = hw * math.cos(th) / 111132.0
        dlon = hw * math.sin(th) / (111320.0 * math.cos(math.radians(lat)))
        z = built_h(z_off, terr.elev(lat, lon))
        pl = cam.project_ll(lat + dlat, lon + dlon, z)
        pr = cam.project_ll(lat - dlat, lon - dlon, z)
        if pl and pr:
            left.append((pl[0], pl[1]))
            right.append((pr[0], pr[1]))
    if len(left) < 3:
        return ""
    return f'<path d="{rel_poly(left + list(reversed(right)))}" class="{cls}"/>'


# ═══════════════════════════════════════════════════════════════════════════
# tokens + CSS
# ═══════════════════════════════════════════════════════════════════════════
TOKENS = {
    "light": """
  --page-bg:#E7E7E9; --text:#241827; --text-mid:#5B4C58;
  --scene-map-label-halo:#F8F7F3; --scene-map-coast:#565060;
  --plate-lagoon:#87AEB8; --scene-map-sea:#9BBFD6; --plate-contour:#5A4A32;
  --plate-masonry:#A87263; --plate-river:#1A4C6A; --plate-marsh:#C7D3A5;
  --pp-hull:#3A2C3C; --pp-hull-side:#1B1220; --pp-hull-edge:#140D18;
  --plate-relief-1:#EDEEDF; --plate-relief-2:#E8E8CF; --plate-relief-3:#E4E2C0;
  --plate-relief-4:#E1DAB3; --plate-relief-5:#DED3A7; --plate-relief-6:#DACB9E;
  --plate-relief-7:#D5C296; --plate-relief-8:#D0B98C; --plate-relief-9:#CAB083;
  --plate-relief-10:#C2A679; --plate-relief-11:#B99C6F; --plate-relief-12:#AF9164;
""",
    "dark": """
  --page-bg:#181120; --text:#EDE6E8; --text-mid:#B7A9B4;
  --scene-map-label-halo:#17131C; --scene-map-coast:#8FA3AE;
  --plate-lagoon:#0A2430; --scene-map-sea:#0A1C2A; --plate-contour:#C2B189;
  --plate-masonry:#A8846F; --plate-river:#B4DAEF; --plate-marsh:#46503A;
  --pp-hull:#241C2A; --pp-hull-side:#120C16; --pp-hull-edge:#C3B49E;
  --plate-relief-1:#4A4136; --plate-relief-2:#51473A; --plate-relief-3:#584D3D;
  --plate-relief-4:#5F523F; --plate-relief-5:#655740; --plate-relief-6:#6B5C42;
  --plate-relief-7:#706043; --plate-relief-8:#766444; --plate-relief-9:#7A6846;
  --plate-relief-10:#7E6C48; --plate-relief-11:#836F49; --plate-relief-12:#86734B;
""",
}

CSS = """
.pp-band{stroke:none}
.pp-contour{fill:none;stroke:var(--plate-contour);stroke-width:0.6;stroke-opacity:0.6;
  stroke-linecap:round}
.pp-ida{fill:var(--plate-relief-12);fill-opacity:0.22;stroke:none}
.pp-ida-crest{fill:none;stroke:var(--plate-contour);stroke-width:0.8;stroke-opacity:0.5}
.pp-sea{fill:var(--scene-map-sea)}
.pp-lagoon{fill:var(--plate-lagoon)}
.pp-marsh{fill:var(--plate-marsh);fill-opacity:0.55;stroke:none}
.pp-coast{fill:none;stroke:var(--scene-map-coast);stroke-width:1.1}
.pp-coast-approx{fill:none;stroke:var(--scene-map-coast);stroke-width:1.1;
  stroke-dasharray:4.5 3;stroke-linecap:round}
.pp-waterline{fill:none;stroke:var(--scene-map-coast);stroke-width:0.6;stroke-opacity:0.45}
.pp-river{fill:var(--plate-river);stroke:none}
.pp-hull{fill:var(--pp-hull);stroke:var(--pp-hull-edge);stroke-width:0.35;
  stroke-linejoin:round}
.pp-hull-side{fill:var(--pp-hull-side);stroke:none}
.pp-post{fill:none;stroke:var(--pp-hull-edge);stroke-width:0.9;stroke-linecap:round}
.pp-ship-mass{fill:var(--pp-hull);stroke:var(--pp-hull-edge);stroke-width:0.7;
  stroke-linejoin:round}
.pp-hut-wall{fill:var(--pp-hull-side);stroke:none}
.pp-hut-roof{fill:var(--plate-masonry);stroke:var(--pp-hull-edge);stroke-width:0.3;
  stroke-linejoin:round}
.pp-wall{fill:var(--plate-masonry);stroke:var(--text);stroke-width:0.5;stroke-linejoin:round}
.pp-wall-crest{fill:none;stroke:var(--text);stroke-width:0.8}
.pp-tower{fill:var(--plate-masonry);stroke:var(--text);stroke-width:0.5;stroke-linejoin:round}
.pp-roof{fill:var(--text-mid);stroke:var(--text);stroke-width:0.4;stroke-linejoin:round}
/* A built work, not terrain: keyed to the relief ramp it was a shade of the
   ground it stands on in both themes and read as one more contour. */
.pp-rampart{fill:var(--plate-masonry);stroke:var(--text-mid);stroke-width:0.5;
  stroke-linejoin:round}
.pp-ditch{fill:none;stroke:var(--text-mid);stroke-width:1.0;stroke-opacity:0.55;
  stroke-dasharray:6 4}
.pp-road{fill:none;stroke:var(--text-mid);stroke-width:1.2;stroke-opacity:0.55;
  stroke-dasharray:9 5;stroke-linecap:round}
.pp-mark{fill:none;stroke:var(--text-mid);stroke-width:1.1}
.pp-mark-f{fill:var(--text-mid);stroke:none}
.pp-tumulus{fill:var(--plate-relief-9);fill-opacity:0.9;stroke:var(--text-mid);
  stroke-width:0.6}
.pp-leader{fill:none;stroke:var(--text-mid);stroke-width:0.8;stroke-opacity:0.75}
.pp-neat-o{fill:none;stroke:var(--text);stroke-width:2.2}
.pp-neat-i{fill:none;stroke:var(--text);stroke-width:0.7}
.pp-key-sw{stroke:var(--text-mid);stroke-width:0.4}
text{font-family:var(--font-ui,Optima,Seravek,"Gill Sans","Gill Sans MT",sans-serif);
  paint-order:stroke;stroke:var(--scene-map-label-halo);stroke-width:3.2;
  stroke-linejoin:round}
.pp-l-region{font-size:15.5px;letter-spacing:2.48px;fill:var(--text-mid)}
.pp-l-settlement{font-size:15px;font-weight:600;fill:var(--text)}
.pp-l-water{font-size:12.5px;font-style:italic;letter-spacing:0.5px;fill:var(--text-mid)}
.pp-l-site{font-size:11.5px;fill:var(--text)}
.pp-l-note{font-size:10px;fill:var(--text-mid);stroke-width:2.4}
.pp-l-title{font-size:22px;letter-spacing:3.2px;fill:var(--text)}
"""

# The three level-of-detail tiers. Content and labels are both tiered; a
# panel turns them on by zoom. Static renders set the same switch.
TIER_CSS = {
    1: ".tm2,.tm3{display:none}",
    2: ".tm3{display:none}",
    3: ".t1-only{display:none}",
}


# ═══════════════════════════════════════════════════════════════════════════
# the plate
# ═══════════════════════════════════════════════════════════════════════════
class Plate:
    def __init__(self, terr, cam, plate_json):
        self.terr = terr
        self.cam = cam
        self.lay = {l["id"]: l for l in plate_json["layers"]}
        self.targets: list = []          # camera-target table rows
        self.stats: dict = {}

    # ── mesh ─────────────────────────────────────────────────────────────
    def mesh(self):
        cam, terr = self.cam, self.terr
        # columns uniform in screen x
        azs = []
        x = -BLEED
        while x <= W + BLEED:
            azs.append(math.degrees(math.atan((x - W / 2.0) / FOCAL)))
            x += COL_PX
        # rings: see ring_ranges / RING_MAX_M
        def flat_y(r):
            p = cam.project(cam.e + r * math.sin(cam.theta),
                            cam.n + r * math.cos(cam.theta), 0.0)
            return p[1] if p else -1e9
        rngs = ring_ranges(flat_y)
        self.azs, self.rngs = azs, rngs

        grid = [[None] * len(rngs) for _ in azs]
        for i, az in enumerate(azs):
            th = math.radians(HEADING_DEG + az)
            s, c = math.sin(th), math.cos(th)
            for j, rr in enumerate(rngs):
                e = cam.e + rr * s
                n = cam.n + rr * c
                lat = VIEWPOINT[0] + n / 111132.0
                lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
                el = terr.elev_smooth(lat, lon, max(35.0, rr * 0.006))
                p = cam.project(e, n, exaggerate(el))
                grid[i][j] = None if p is None else (p[0], p[1], el, rr)
        self.grid = grid

    def cull(self):
        """Floating horizon. The mesh is a single-valued height field seen
        from above, so marching each screen column near-to-far and keeping the
        running silhouette says exactly which cells are hidden."""
        grid, azs, rngs = self.grid, self.azs, self.rngs
        hor = [1e9] * len(azs)
        visible = set()
        tested = 0
        for j in range(len(rngs) - 1):
            for i in range(len(azs) - 1):
                a0, a1 = grid[i][j], grid[i + 1][j]
                b0, b1 = grid[i][j + 1], grid[i + 1][j + 1]
                if a0 is None or a1 is None or b0 is None or b1 is None:
                    continue
                ys = (a0[1], a1[1], b0[1], b1[1])
                xs = (a0[0], a1[0], b0[0], b1[0])
                tested += 1
                if max(xs) < -BLEED or min(xs) > W + BLEED:
                    continue
                if min(ys) > H + BLEED:
                    continue
                # BACK-FACE CULL. Where the ground falls away behind a crest
                # the quad FOLDS OVER in screen space: its far edge projects
                # above its near edge, and what it would paint is the back of
                # the slope, which the eye cannot see -- the crest in front of
                # it is the visible surface there. Two reasons to drop it and
                # neither is taste. It is occluded; and it winds the opposite
                # way, so when the band union merges it with the front-facing
                # ground beside it the nonzero fill rule CANCELS over the
                # overlap and the page shows through. That is where the pale
                # lens-shaped slivers along the middle-distance crests came
                # from. Denser rings make folds commoner -- adding the ring
                # floor above took the defect from 204 stray pixels to 1206 --
                # but it was always there, and dropping these cells also takes
                # 8% off the shipped SVG.
                if ((a0[0] * a1[1] - a1[0] * a0[1])
                        + (a1[0] * b1[1] - b1[0] * a1[1])
                        + (b1[0] * b0[1] - b0[0] * b1[1])
                        + (b0[0] * a0[1] - a0[0] * b0[1])) > 0.0:
                    continue
                # `hor` covers rings STRICTLY NEARER than this cell. Folding
                # the cell's own far edge (ring j+1) into the silhouette
                # before testing over-culls by one ring, which printed as
                # white notches scattered through the middle distance.
                lim = max(hor[i], hor[i + 1])
                if min(ys) < lim + 2.0:
                    visible.add((i, j))
            for i in range(len(azs)):
                g = grid[i][j]
                if g is not None and g[1] < hor[i]:
                    hor[i] = g[1]
        self.visible = visible
        self.stats["cells_tested"] = tested
        self.stats["cells_visible"] = len(visible)

    def terrain_svg(self):
        grid, azs, rngs = self.grid, self.azs, self.rngs
        corner = lambda i, j: (grid[i][j][0], grid[i][j][1])
        out = []
        edges = STRATA_EDGES
        for s in range(len(edges) - 1):
            far, near = edges[s], edges[s + 1]
            if far in HAZE and s > 0:
                out.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                           f'fill="var(--page-bg)" fill-opacity="{HAZE[far]}"/>')
            interior: dict = {}
            frag: dict = {}
            cont = []
            for (i, j) in self.visible:
                rr = grid[i][j][3]
                if not (near * 0.965 <= rr < far):
                    continue
                a0, a1 = grid[i][j], grid[i + 1][j]
                b1, b0 = grid[i + 1][j + 1], grid[i][j + 1]
                quad = [(a0[0], a0[1]), (a1[0], a1[1]), (b1[0], b1[1]), (b0[0], b0[1])]
                evs = [a0[2], a1[2], b1[2], b0[2]]
                k0, k1 = band_of(min(evs)), band_of(max(evs))
                if k0 == k1:
                    interior.setdefault(k0, set()).add((i, j))
                    continue
                if k1 == k0 + 1:
                    lv = LEVELS[k0]
                    lo = clip_below(quad, evs, lv)
                    hi = clip_above(quad, evs, lv)
                    if len(lo) >= 3:
                        frag.setdefault(k0, []).append(rel_poly(lo))
                    if len(hi) >= 3:
                        frag.setdefault(k1, []).append(rel_poly(hi))
                    seg = []
                    for m in range(4):
                        e0, e1 = evs[m], evs[(m + 1) % 4]
                        if (e0 - lv) * (e1 - lv) < 0:
                            t = (lv - e0) / (e1 - e0)
                            p0, p1 = quad[m], quad[(m + 1) % 4]
                            seg.append((p0[0] + t * (p1[0] - p0[0]),
                                        p0[1] + t * (p1[1] - p0[1])))
                    if len(seg) == 2:
                        cont.append(rel_seg(*seg))
                else:
                    # three or more bands in one cell: a cliff. Split at every
                    # level it crosses so the ramp stays a ramp.
                    for k in range(k0, k1 + 1):
                        lo_lv = LEVELS[k - 1] if k > 0 else -1e9
                        hi_lv = LEVELS[k] if k < len(LEVELS) else 1e9
                        part = clip_above(quad, evs, lo_lv) if k > 0 else quad
                        if len(part) < 3:
                            continue
                        if k < len(LEVELS):
                            pev = []
                            for px_, py_ in part:
                                pev.append(self._interp_elev(quad, evs, px_, py_))
                            part = clip_below(part, pev, hi_lv)
                        if len(part) >= 3:
                            frag.setdefault(k, []).append(rel_poly(part))
            for k in sorted(set(list(interior) + list(frag))):
                d = []
                for loop in union_loops(interior.get(k, set()), corner):
                    d.append(rel_poly(simplify(loop, 0.6)))
                d.extend(frag.get(k, []))
                if d:
                    # A hairline of page-bg used to show wherever a
                    # simplified union loop pulled away from the fragment
                    # polygons beside it, or where one depth stratum met the
                    # next. Stroking a band in its OWN fill closes the seam
                    # for 0.3 px of expansion and no change to the drawing.
                    out.append(f'<path class="pp-band" fill="var(--plate-relief-{k + 1})" '
                               f'stroke="var(--plate-relief-{k + 1})" stroke-width="0.7" '
                               f'd="{"".join(d)}"/>')
            if cont:
                out.append(f'<path class="pp-contour" d="{"".join(cont)}"/>')
        return "".join(out)

    @staticmethod
    def _interp_elev(quad, evs, x, y):
        """Inverse-distance elevation at a point inside the cell -- only used
        for the rare three-band cell, where exactness buys nothing."""
        num = den = 0.0
        for (qx, qy), e in zip(quad, evs):
            w = 1.0 / (max(1e-6, (qx - x) ** 2 + (qy - y) ** 2))
            num += w * e
            den += w
        return num / den

    # ── Ida beyond the mesh ──────────────────────────────────────────────
    def ida_svg(self):
        cam, terr = self.cam, self.terr
        sky = []
        x = -BLEED
        while x <= W + BLEED:
            az = math.degrees(math.atan((x - W / 2.0) / FOCAL))
            bearing = HEADING_DEG + az
            best_angle, best = -9e9, None
            d = 46000.0
            while d < 100000.0:
                lat, lon = pp._dest_point(VIEWPOINT, bearing, d)
                if 38.95 <= lat <= 40.6 and 25.35 <= lon <= 27.5:
                    # THE SKYLINE IS IN THE SAME HEIGHT SPACE AS THE MESH.
                    # It used to be drawn at RAW elevation, which happened to
                    # match only because the legacy curve was flat 1x above
                    # 300 m and every skyline sample here is over 373 m. Any
                    # curve with lift up high would have stepped the mesh's
                    # far edge above the horizon behind it.
                    z = exaggerate(terr.elev(lat, lon))
                    e, n = pp._flat_m((lat, lon), *VIEWPOINT)
                    ang = math.atan2(z - cam.z, math.hypot(e - cam.e, n - cam.n))
                    if ang > best_angle:
                        best_angle, best = ang, (e, n, z)
                d += 500.0
            if best:
                p = cam.project(*best)
                if p:
                    sky.append((p[0], p[1]))
            x += COL_PX * 3
        if len(sky) < 4:
            return "", None
        sky.sort(key=lambda q: q[0])
        poly = sky + [(sky[-1][0], float(H) + 40), (sky[0][0], float(H) + 40)]
        crest = min(sky, key=lambda q: q[1])
        return ('<path d="%s" class="pp-ida"/><path d="%s" class="pp-ida-crest"/>'
                % (rel_poly(poly), rel_poly(sky, close=False))), crest

    # ── water ────────────────────────────────────────────────────────────
    def water_path(self, poly_latlon, z=0.0, drape=False):
        cam, terr = self.cam, self.terr
        dense = []
        n_ = len(poly_latlon)
        for k in range(n_):
            a = poly_latlon[k]
            b = poly_latlon[(k + 1) % n_]
            seg = math.hypot(*pp._flat_m(b, a[0], a[1]))
            steps = max(1, int(seg / 45.0))
            for s in range(steps):
                t = s / steps
                dense.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        world = []
        for lat, lon in dense:
            e, n = pp._flat_m((lat, lon), *VIEWPOINT)
            world.append((e, n, built_h(0.0, terr.elev(lat, lon)) if drape else z))
        scr = []
        for wpt in clip_to_depth(world, cam):
            p = cam.project(*wpt)
            if p:
                scr.append((p[0], p[1]))
        if len(scr) < 4:
            return None
        return simplify(chaikin(scr, passes=2, closed=True), 0.6)

    def water_svg(self):
        out = []
        # A WATER LAYER IS DRAWN AT THE ELEVATION OF THE GROUND IT WAS DERIVED
        # FROM. sea-modern is the modern coastline on a modern DEM, so its own
        # ground is 0 and a flat 0 plane is both the datum and the drape.
        #
        # lagoon-bronze is not. It was flood-filled from DEM cells at or below
        # the 10 m contour (fix-lagoon-connectivity.py; SHORE_LEVEL in
        # prep-terrain-contours.py:1034), and that 10 m is a HORIZONTAL device
        # -- the contour that puts the bay head 1.2 km NNW of Hisarlik, where
        # Kraft, Rapp, Kayan and Luce put it -- standing in for the sediment
        # the plain has gained since. It is not a paleo sea level. The Late
        # Bronze Age relative sea level here is about 2 m BELOW present
        # (Kayan et al. 2003, 383 fig. 2, after Kayan 1991, the minimum at
        # ~3300 BP carrying the "Trojan War" label; and 379, "a relative fall
        # in sea level of about 2 m in the Bronze Age").
        #
        # So it was drawn at exaggerate(10.0) = a flat 40 apparent metres.
        # Measured over the polygon's 140 vertices, that is right where the
        # outline follows the contour (120 of 140 sit at 8-12 m; median
        # displacement from the ground 0.5 px) and wrong where it meets the
        # sea (13 vertices under 2 m; up to 35 px), which is precisely the
        # junction where a raised plane reads as a lake perched above the
        # Aegean and covers the modern water behind it.
        #
        # Dropping it to a flat 0 fixes the mouth and breaks the head: median
        # displacement 14.8 px, up to 32.7 px, pulling the reconstructed
        # shoreline off the contour it was traced from. Draping is right at
        # both ends, costs nothing, and asserts no sea level at all -- it
        # shades the ground the reconstruction says was under water, which on
        # a modern DEM carrying Holocene fill is the only claim the base can
        # actually support. delta-swamp already does this, for this reason.
        sea = self.water_path(self.lay["sea-modern"]["polygon"], 0.0)
        lagoon = self.water_path(self.lay["lagoon-bronze"]["polygon"], drape=True)
        swamp = self.water_path(self.lay["delta-swamp"]["polygon"], drape=True)
        if sea:
            out.append(f'<path d="{rel_poly(sea)}" class="pp-sea"/>')
            out.append(f'<path d="{rel_poly(sea)}" class="pp-coast"/>')
        if lagoon:
            out.append(f'<path d="{rel_poly(lagoon)}" class="pp-lagoon"/>')
            gaps, d = [], 3.2
            for _ in range(2):
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
                keep = []
                for i in range(len(off)):
                    ax, ay, tx, ty = off[i]
                    bx, by, _, _ = off[(i + 1) % len(off)]
                    if (bx - ax) * tx + (by - ay) * ty >= 0:
                        keep.append((ax, ay))
                if len(keep) > 8:
                    out.append(f'<path d="{rel_poly(keep)}" class="pp-waterline"/>')
            out.append(f'<path d="{rel_poly(lagoon)}" class="pp-coast-approx"/>')
        # THE SWAMP HAS NO EDGE. A wetland grades from open water through reed
        # and seasonal flood to dry ground and moves with the year, so it is
        # drawn with no outline at all and blurred out at its margin -- the
        # same argument, and the same treatment, the geographic sheet already
        # uses for delta-swamp.
        if swamp:
            out.append(f'<g class="tm2"><path d="{rel_poly(swamp)}" class="pp-marsh" '
                       f'filter="url(#pp-soft)"/></g>')
        return "".join(out)

    def rivers_svg(self):
        """A river is drawn on LAND ONLY. The channels are the modern survey;
        the bay is the Bronze Age reconstruction, and running a modern channel
        across a reconstructed lagoon mixes the two registers in one mark --
        which printed as a dark line wandering over open water."""
        lagoon = self.lay["lagoon-bronze"]["polygon"]
        sea = self.lay["sea-modern"]["polygon"]

        def dry_runs(path):
            runs, cur = [], []
            for lat, lon in path:
                if point_in_poly_ll(lat, lon, lagoon) or point_in_poly_ll(lat, lon, sea):
                    if len(cur) > 2:
                        runs.append(cur)
                    cur = []
                else:
                    cur.append((lat, lon))
            if len(cur) > 2:
                runs.append(cur)
            return runs

        out = []
        n_sc = len(self.lay["scamander"]["path"])
        for run in dry_runs(self.lay["scamander"]["path"]):
            out.append('<g>' + draped_ribbon(
                self.cam, self.terr, run, 17.0, "pp-river",
                taper=lambda t: 0.55 + 0.45 * t) + '</g>')
        for run in dry_runs(self.lay["simoeis"]["path"]):
            out.append('<g class="tm2">' + draped_ribbon(
                self.cam, self.terr, run, 11.0, "pp-river",
                taper=lambda t: 1.0 - 0.4 * t) + '</g>')
        _ = n_sc
        return "".join(p for p in out if "<path" in p)

    # ── the camp ─────────────────────────────────────────────────────────
    def camp(self):
        """Ships hauled up in rows, prows to the water; huts on the ridge
        behind; the wall and its ditch inland of both. Every position is
        conjectural, laid against the measured shoreline: the poem is exact
        about the camp's SHAPE (14.31-36, rows because one row would not fit
        between the headlands) and silent about its ground."""
        cam, terr = self.cam, self.terr
        lagoon_poly = self.lay["lagoon-bronze"]["polygon"]
        camp_zone = self.lay["achaean-camp-zone"]["polygon"]
        th = math.radians(HEADING_DEG)

        def shore_forward(lateral):
            lo = None
            f = 100.0
            while f < 5200.0:
                e = f * math.sin(th) + lateral * math.cos(th)
                n = f * math.cos(th) - lateral * math.sin(th)
                lat = VIEWPOINT[0] + n / 111132.0
                lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
                if point_in_poly_ll(lat, lon, lagoon_poly):
                    return lo
                lo = f
                f += 25.0
            return None

        def near_camp(lat, lon, margin_m=380.0):
            if point_in_poly_ll(lat, lon, camp_zone):
                return True
            for plat, plon in camp_zone:
                if math.hypot(*pp._flat_m((plat, plon), lat, lon)) < margin_m:
                    return True
            return False

        def ll(f, lateral):
            e = f * math.sin(th) + lateral * math.cos(th)
            n = f * math.cos(th) - lateral * math.sin(th)
            return (VIEWPOINT[0] + n / 111132.0,
                    VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0]))))

        # ROWS, at the poem's own reason for them: the beach could not hold
        # the fleet in one line (14.31-36). 13 m of lateral pitch on a 4.2 m
        # beam is roomy; five ranks is what the frontage in view then carries.
        ships, ship_px, hulls_drawn, depths = [], [], 0, []
        lat_span = [x * 13.0 for x in range(-70, 150)]
        shore = {L: shore_forward(L) for L in lat_span}

        def seaward(lateral):
            """The bearing a hull's prow takes: the OUTWARD NORMAL OF THE
            SHORE at this point on the beach, not a constant. Every ship laid
            on the camera's own heading pointed straight away from the eye
            wherever the coast turned, and a beached galley seen exactly
            end-on is a dark blob, not a ship."""
            a = shore.get(lateral - 13.0)
            b = shore.get(lateral + 13.0)
            if a is None or b is None:
                return HEADING_DEG
            dfdl = (b - a) / 26.0
            nf, nl = 1.0, -dfdl
            L = math.hypot(nf, nl)
            de = (nf * math.sin(th) + nl * math.cos(th)) / L
            dn = (nf * math.cos(th) - nl * math.sin(th)) / L
            return math.degrees(math.atan2(de, dn))

        for lateral in lat_span:
            fs = shore[lateral]
            if fs is None:
                continue
            bearing = seaward(lateral)
            for row in range(5):
                f = fs - 66.0 - row * 38.0 + (11.0 if row % 2 else 0.0)
                if f < 60:
                    continue
                lat, lon = ll(f, lateral)
                if terr.elev(lat, lon) > 16.0 or not near_camp(lat, lon):
                    continue
                sp = cam.project_ll(lat, lon, built_h(2.4, terr.elev(lat, lon)))
                if not sp or not (-BLEED < sp[0] < W + BLEED and -BLEED < sp[1] < H + BLEED):
                    continue
                sh = ship(cam, terr, lat, lon, bearing)
                if sh:
                    ships.append(sh)
                    hulls_drawn += 1
                    ship_px.append((sp[0], sp[1], lateral, f, lat, lon))
                    depths.append(sp[2])
        huts = []
        for lateral in [x * 34.0 for x in range(-26, 58)]:
            fs = shore_forward(lateral)
            if fs is None:
                continue
            for row in range(6):
                f = fs - 300.0 - row * 52.0
                if f < 40:
                    continue
                lat, lon = ll(f, lateral)
                if not near_camp(lat, lon, 260.0):
                    continue
                hh = hut(cam, terr, lat, lon, seaward(round(lateral / 13.0) * 13.0)
                         + (17 if row % 2 else -11))
                if hh:
                    huts.append(hh)

        # THE MASS, for tier 1: the same fleet, drawn as one body with a
        # serrated seaward edge, because at 1x 1,100 outlines is a smudge and
        # a smudge is a mark standing for tone.
        # THE ORDER ALONG THE BEACH IS `lateral`, NOT SCREEN X. The shoreline
        # curves through this camera, so chaining the rows by x threaded the
        # band back and forth across the bay and printed a black snake over
        # open water. The beach parameter is monotone by construction.
        mass = ""
        if ship_px:
            front: dict = {}
            back: dict = {}
            for q in ship_px:
                key = round(q[2] / 13.0)
                if key not in front or q[3] > front[key][3]:
                    front[key] = q
                if key not in back or q[3] < back[key][3]:
                    back[key] = q
            keys = sorted(front)
            # split at any gap in the beach parameter: two stretches of beach
            # separated by ground the ships are not on must not be joined.
            runs, cur = [], [keys[0]]
            for k in keys[1:]:
                if k - cur[-1] <= 2:
                    cur.append(k)
                else:
                    runs.append(cur)
                    cur = [k]
            runs.append(cur)
            parts = []
            for run in runs:
                if len(run) < 6:
                    continue
                # a serrated seaward edge: at 1x the prows are what says
                # "ships" rather than "a dark band".
                # The band follows the SEAWARD ROW only, at a modest depth.
                # Running it back to the landward row made it as deep as the
                # camp really is and printed a slab; the huts behind carry the
                # camp's depth, and the ships carry its line.
                top, bot = [], []
                for n_, k in enumerate(run):
                    x, y = front[k][0], front[k][1]
                    top.append((x, y - (6.5 if n_ % 2 else 2.0)))
                    bot.append((x, y + 8.0))
                parts.append(rel_poly(simplify(top + list(reversed(bot)), 0.5)))
            if parts:
                mass = '<path class="pp-ship-mass" d="%s"/>' % "".join(parts)

        # THE ACHAEAN WALL AND ITS DITCH (7.436-441), inland of the huts:
        # a rampart with the ditch beyond it, toward the plain. Conjectural;
        # the poem provides for its own erasure, which is why nothing of it
        # has ever been found.
        # "a great wall, and towers on it, high, a defence for the ships and
        # for themselves; and in it they made gates well fitted, that there
        # might be a way through for chariots" (7.436-439). Drawn without the
        # towers it was a uniform band the width of the frame and read as a
        # road; the towers are what make it a wall. Their SPACING is drawn,
        # their number is not a claim.
        wall_pts, ditch_pts = [], []
        for nth, lateral in enumerate([x * 34.0 for x in range(-22, 52)]):
            fs = shore_forward(lateral)
            if fs is None:
                continue
            lat, lon = ll(fs - 640.0, lateral)
            if not near_camp(lat, lon, 300.0):
                continue
            g = terr.elev(lat, lon)
            crest = 4.6 + (3.4 if nth % 4 == 0 else 0.0)
            a = cam.project_ll(lat, lon, built_h(0.0, g))
            b = cam.project_ll(lat, lon, built_h(crest, g))
            latd, lond = ll(fs - 760.0, lateral)
            c = cam.project_ll(latd, lond, built_h(0.0, terr.elev(latd, lond)))
            if a and b:
                wall_pts.append(((a[0], a[1]), (b[0], b[1])))
            if c:
                ditch_pts.append((c[0], c[1]))
        wall_svg = ""
        if len(wall_pts) > 4:
            wall_pts.sort(key=lambda q: q[0][0])
            wall_svg = ('<path class="pp-rampart" d="%s"/>'
                        % rel_poly([p[1] for p in wall_pts]
                                   + [p[0] for p in reversed(wall_pts)]))
            self.stats["wall_mid"] = list(wall_pts[len(wall_pts) // 4][1])
        ditch_svg = ""
        if len(ditch_pts) > 4:
            ditch_pts.sort(key=lambda q: q[0])
            ditch_svg = '<path class="pp-ditch" d="%s"/>' % rel_poly(ditch_pts, close=False)

        self.stats["hulls"] = hulls_drawn
        self.stats["huts"] = len(huts)
        self.stats["ship_depth"] = round(sum(depths) / len(depths), 1) if depths else 2600.0
        self.stats["beach_frontage_m"] = round(
            (max(q[2] for q in ship_px) - min(q[2] for q in ship_px)) if ship_px else 0.0)
        return ships, huts, mass, wall_svg, ditch_svg, ship_px

    # ── the poem's waypoints, placed by rule ─────────────────────────────
    def waypoints(self):
        """Every entry here is `conjectural` unless it names measured ground.
        The RULE is recorded with each one; the rule is the honesty, not a
        hedge in the note."""
        cam, terr = self.cam, self.terr
        troy = pp.TROY
        sc = self.lay["scamander"]["path"]
        # THE WAGON-ROAD RUNS ONTO THE PLAIN, NOT AT THE CAMP. Laid straight
        # from Ilios to the camp it crossed the reconstructed embayment, and
        # printed the poem's oak, fig tree, springs, tomb and ford as marks
        # floating on open water -- a fabricated route, which is the one thing
        # this plate may not do. What the poem actually says is πεδίοιο: the
        # road goes out from under the wall onto the PLAIN (22.145-147), and
        # the plain on this reconstruction is the Scamandrian ground south of
        # the city. The road is therefore laid from the west face of Ilios
        # toward the centroid of the drawn scamandrian-plain region, and the
        # ford is where it first meets the drawn channel. Every point of it is
        # dry ground on the plate's own geometry.
        plain = self.lay["scamandrian-plain"]["polygon"]
        plain_c = (sum(q[0] for q in plain) / len(plain),
                   sum(q[1] for q in plain) / len(plain))

        def road_pt(t):
            return (troy[0] + t * (plain_c[0] - troy[0]),
                    troy[1] + t * (plain_c[1] - troy[1]))

        # ford: the road's crossing of the drawn channel
        ford_t, ford = None, None
        for k in range(len(sc) - 1):
            a, b = sc[k], sc[k + 1]
            for m in range(60):
                t = 0.10 + m * 0.015
                p = road_pt(t)
                # distance from p to segment ab, in metres
                ae, an = pp._flat_m(a, *p)
                be, bn = pp._flat_m(b, *p)
                vx, vy = be - ae, bn - an
                L2 = vx * vx + vy * vy or 1e-9
                u = max(0.0, min(1.0, -(ae * vx + an * vy) / L2))
                dx, dy = ae + u * vx, an + u * vy
                if math.hypot(dx, dy) < 120.0 and (ford_t is None or t < ford_t):
                    ford_t, ford = t, p
        if ford is None:
            ford_t, ford = 0.72, road_pt(0.72)
        # a guard, not a hope: if any point of the road as laid falls in water,
        # the rule has failed and the plate must not draw it.
        wet = self.lay["lagoon-bronze"]["polygon"]
        for m in range(41):
            q = road_pt(m * ford_t / 40.0)
            if point_in_poly_ll(q[0], q[1], wet):
                raise SystemExit("wagon-road crosses the reconstructed bay — "
                                 "the placement rule is wrong, not the drawing")

        WP = []

        def add(pid, name, greek, tier, basis, cite, latlon, h=0.0, kind="site",
                rule="", tradition=""):
            WP.append(dict(id=pid, name=name, greek=greek, tier=tier,
                           positionBasis=basis, citation=cite, at=latlon,
                           height=h, kind=kind, rule=rule, tradition=tradition))

        add("ilios", "Ilios", "Ἴλιος", 1, "measured",
            "Il. 3.145-153; 6.386; 22.97", troy, 15.0, "settlement",
            "Hisarlık, apparatus/places.json 'troy'.")
        add("scamander", "Scamander", "Σκάμανδρος / Ξάνθος", 1, "measured",
            "Il. 6.4; 14.433; 21.1-2", (39.9295, 26.2445), 0.0, "water",
            "On the drawn (modern) channel, OSM. The Bronze Age bed is not "
            "this line and is not drawn.")
        add("bay-of-troy", "the bay of Troy", "", 1, "reconstructed",
            "Kraft, Kayan and Erol 1980; Kayan 1995", (39.9880, 26.2060), 0.0, "water",
            "The reconstructed Late Bronze Age embayment (lagoon-bronze).")
        add("ida", "MOUNT IDA", "Ἴδη", 1, "measured",
            "Il. 8.47-48; 14.283-285", pp.IDA_SUMMIT, 0.0, "region",
            "Kaz Dağı summit; skyline sampled from the Troad DEM.")

        add("simoeis", "Simoeis", "Σιμόεις", 2, "traditional",
            "Il. 5.774; 6.4", (39.9720, 26.2900), 0.0, "water",
            "On the drawn channel.", "Equation with the Dümrek Su, following "
            "Strabo 13.1; accepted by Leaf, Cook and Luce.")
        add("ford-of-the-scamander", "the ford", "πόρος ποταμοῖο", 2, "conjectural",
            "Il. 14.433 = 21.1-2 = 24.692-693", ford, 0.0, "site",
            "Where the wagon-road, laid from Ilios toward the camp, meets the "
            "drawn channel. The crossing is named by a repeated formula; its "
            "ground is unrecoverable — the delta has prograded past it.")
        add("rhoiteion", "RHOITEION", "Ῥοίτειον", 2, "measured",
            "Il. 14.31-36 (a beach between two headlands; the headlands are "
            "not named in the poem)", pp.RHOITEION, 0.0, "region",
            "Baba Kale spur, apparatus/places.json 'rhoiteion'.")
        add("sigeion", "SIGEION", "Σίγειον", 2, "measured",
            "Il. 14.31-36 (as above)", pp.SIGEION, 0.0, "region",
            "apparatus/places.json 'sigeion'.")
        add("callicolone", "Callicolone", "Καλλικολώνη", 2, "traditional",
            "Il. 20.53; 20.151", (39.9565, 26.3395), 0.0, "site",
            "Kara Tepe, the surveyed peak 8.5 km east of Troy (207 m).",
            "Spratt/Forchhammer identification, editorial ruling 2026-07-30.")
        add("achaean-wall", "the wall of the Achaeans", "τεῖχος", 2, "conjectural",
            "Il. 7.436-441; 12.17-24; 14.30-36",
            ll_along(VIEWPOINT, HEADING_DEG, 1500.0), 4.6, "line",
            "Laid parallel to the drawn shoreline, on the landward side of "
            "the huts — the poem's own order is sea, ships in ranks, then the "
            "wall at the camp's inland edge with the ditch beyond it "
            "(14.30-36; 7.440-441). Note the tension this plate does not "
            "hide: on the Late Bronze Age reconstruction the water the ships "
            "face is the embayment, and the plain the wall was built against "
            "lies round its head.")
        add("throsmos", "the rising ground of the plain", "θρωσμὸς πεδίοιο", 2,
            "conjectural", "Il. 10.160; 11.56; 20.3", road_pt(0.40), 0.0, "region",
            "On the plain between the ford and the city, where the Trojans "
            "bivouac and form up.")
        add("delta-swamp", "marsh and wet delta", "", 2, "reconstructed",
            "Kayan 1995; 2002", (39.9700, 26.2470), 0.0, "region",
            "Margin indefinite by construction — drawn with no outline.")

        add("scaean-gate", "the Scaean Gate and the oak", "Σκαιαὶ πύλαι / φηγός",
            3, "conjectural", "Il. 3.145; 6.237 = 9.354 = 11.170; 5.693; 7.60",
            road_pt(0.035), 6.0, "site",
            "At the west face of the circuit, where the wagon-road leaves it. "
            "No agreed candidate at Hisarlık; the gate and the oak are one "
            "formulaic pair and are drawn as one mark.")
        add("lookout-skopie", "the lookout", "σκοπιή", 3, "conjectural",
            "Il. 22.145", road_pt(0.11), 0.0, "site",
            "First of the three things the chase passes on the wagon-road.")
        add("fig-tree", "the wild fig tree", "ἐρινεός", 3, "conjectural",
            "Il. 6.433; 11.167; 22.145", road_pt(0.17), 0.0, "site",
            "Second on the chase-route, 'always out from under the wall'.")
        add("two-springs-of-scamander", "the two springs", "κρουνὼ καλλιρρόω", 3,
            "conjectural", "Il. 22.147-152", road_pt(0.25), 0.0, "site",
            "Third on the chase-route: one warm, steaming; one cold as hail.")
        add("tomb-of-ilos", "the tomb of Ilus", "σῆμα Ἴλου", 3, "conjectural",
            "Il. 10.415; 11.166-167; 11.371-372; 24.349", road_pt(0.60), 5.0, "tumulus",
            "Out on the plain between the ford and the fig tree: the rout at "
            "11.166-170 runs past the tomb, over mid-plain, past the fig, to "
            "the city, and that order is the only fix there is.")
        add("wagon-road", "the wagon-road", "ἀμαξιτός", 3, "conjectural",
            "Il. 22.146", road_pt(0.42), 0.0, "line",
            "The single organizing line of the plain, from the Scaean Gate "
            "past the lookout, the fig tree and the springs.")
        add("batieia", "Batieia", "Βατίεια", 3, "conjectural",
            "Il. 2.811-815", off_road(road_pt(0.30), troy, 620.0), 7.0, "tumulus",
            "'Before the city, out in the plain, standing clear, with a way "
            "round it on either side' — off the road, on the city side.")
        add("wall-of-heracles", "the wall of Heracles", "τεῖχος Ἡρακλῆος", 3,
            "conjectural", "Il. 20.145-148", off_road(road_pt(0.72), troy, -780.0),
            6.0, "site",
            "The pro-Greek gods' seat, Callicolone's opposite number across "
            "the divine grandstand; on the plain between the camp and the "
            "city. A mythical place, on the map with confidence.")
        self.road_t = (0.0, ford_t)
        self.road_pt = road_pt
        return [w for w in WP if w["id"] != "_ford_t"]


def ll_along(origin, bearing_deg, dist_m):
    return pp._dest_point(origin, bearing_deg, dist_m)


def off_road(p, troy, offset_m):
    """A point `offset_m` to one side of the road at p (positive = north of
    the road's own line)."""
    b = pp._bearing_deg(troy, p)
    return pp._dest_point(p, b + 90.0, offset_m)


# ═══════════════════════════════════════════════════════════════════════════
# labels
# ═══════════════════════════════════════════════════════════════════════════
def tcls(tier):
    """Tier classes are CUMULATIVE: tm2 means "from tier 2 up". A class per
    exact tier ("t2 t3") reads as two selectors and a tier-2 stylesheet that
    hides .t3 hides it, which silently blanked the huts at 2x."""
    return "" if tier <= 1 else f"tm{tier}"


def label(cls, x, y, text, tier, anchor="start", greek=""):
    t = f' class="plate-label {cls}"' if cls else ' class="plate-label"'
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    g = (f'<tspan class="pp-l-note" dx="6">{greek}</tspan>' if greek else "")
    return (f'<g class="{tcls(tier)}">'
            f'<text{t} x="{n1(x)}" y="{n1(y)}"{a}>{text}{g}</text></g>')


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ═══════════════════════════════════════════════════════════════════════════
# furniture: neatline, scale, hypsometric key, disclosure
# ═══════════════════════════════════════════════════════════════════════════
def furniture(cam, terr, ship_depth, troy_depth):
    out = []
    m = 16.0
    out.append(f'<rect x="{m}" y="{m}" width="{W - 2 * m}" height="{H - 2 * m}" '
               f'class="pp-neat-o"/>')
    out.append(f'<rect x="{m + 6}" y="{m + 6}" width="{W - 2 * m - 12}" '
               f'height="{H - 2 * m - 12}" class="pp-neat-i"/>')
    out.append(f'<text class="pp-l-title" x="{W / 2}" y="{m + 44}" '
               f'text-anchor="middle">THE SHIPS, THE BAY, AND ILIOS</text>')
    out.append(f'<text class="pp-l-note" x="{W / 2}" y="{m + 64}" '
               f'text-anchor="middle">the plain of Troy from the Achaean camp, '
               f'looking east-south-east</text>')

    # ── THE CARTOUCHE, IN THE DEAD FOREGROUND. The bottom third of a raised
    # oblique from a ridge is the back of the ridge: real ground with nothing
    # on it. Printed cartography has always answered that with the furniture,
    # and it is the honest answer here too — the key, the scale and the
    # disclosures make the empty quarter deliberate instead of unused.
    bx, by = 62.0, H - 258.0
    out.append(f'<path class="pp-neat-i" d="M{n1(bx)} {n1(by - 26)}h520" '
               f'stroke-opacity="0.5"/>')
    out.append(f'<text class="pp-l-region" x="{n1(bx)}" y="{n1(by - 34)}">'
               f'ELEVATION, METRES</text>')

    kw, kh = 42.0, 20.0
    for i in range(12):
        out.append(f'<rect class="pp-key-sw" x="{n1(bx + i * kw)}" y="{n1(by)}" '
                   f'width="{n1(kw)}" height="{n1(kh)}" '
                   f'fill="var(--plate-relief-{i + 1})"/>')
    out.append(f'<text class="pp-l-note" x="{n1(bx)}" y="{n1(by + kh + 13)}">0</text>')
    for i, lv in enumerate(LEVELS):
        out.append(f'<text class="pp-l-note" x="{n1(bx + (i + 1) * kw)}" '
                   f'y="{n1(by + kh + 13)}" text-anchor="middle">{lv}</text>')

    # scale. On an oblique there is no one scale, so the bar is given at two
    # depths and says which.
    sy = by + kh + 62
    out.append(f'<text class="pp-l-region" x="{n1(bx)}" y="{n1(sy - 12)}">'
               f'SCALE — VARIES WITH DEPTH</text>')
    for k, (d, lbl) in enumerate(((ship_depth, "1 km at the ships"),
                                  (troy_depth, "1 km at Ilios"))):
        px = FOCAL * 1000.0 / d
        yy = sy + k * 24
        out.append(f'<path class="pp-neat-i" d="M{n1(bx)} {n1(yy)}h{n1(px)}'
                   f'M{n1(bx)} {n1(yy - 4)}v8M{n1(bx + px)} {n1(yy - 4)}v8" '
                   f'stroke-width="1.1"/>')
        out.append(f'<text class="pp-l-note" x="{n1(bx + px + 9)}" y="{n1(yy + 3.5)}">'
                   f'{lbl}</text>')

    # ── the disclosures, which are part of the plate, not of the report
    ty = H - 60
    for line in (
        DISCLOSURE[CURVE],
        "Terrain, coastlines, rivers, Hisarlık, Callicolone, Sigeion and Rhoiteion are "
        "measured. Ships, huts, the wall and ditch, and every waypoint of the poem are "
        "conjectural — each placed by a stated rule, never at an invented coordinate.",
        "The bay is the reconstructed Late Bronze Age embayment (Kraft, Kayan and Erol "
        "1980; Kayan), its shore approximate and drawn dashed. DRAFT.",
    ):
        out.append(f'<text class="pp-l-note" x="{n1(bx)}" y="{n1(ty)}">{esc(line)}</text>')
        ty += 15
    return "".join(out)


# ═══════════════════════════════════════════════════════════════════════════
# assembly
# ═══════════════════════════════════════════════════════════════════════════
DEFS = ('<defs><filter id="pp-soft" x="-25%" y="-25%" width="150%" height="150%">'
        '<feGaussianBlur stdDeviation="9"/></filter>'
        f'<clipPath id="pp-frame"><rect x="23" y="23" width="{W - 46}" '
        f'height="{H - 46}"/></clipPath></defs>')


def build(terr, cam, plate_json):
    P = Plate(terr, cam, plate_json)
    P.mesh()
    P.cull()
    body = ['<g clip-path="url(#pp-frame)">']
    # THE SKY IS NOT THE PAGE. Left as bare --page-bg it sat within a shade of
    # --plate-relief-1, and every patch of delta under 5 m in the far plain
    # read as a hole punched through the plate rather than as low wet ground.
    # A wash of the coast ink over the page separates them, and gives the top
    # fifth of the frame something to be.
    body.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                f'fill="var(--scene-map-coast)" fill-opacity="0.1"/>')
    ida, ida_crest = P.ida_svg()
    body.append(ida)
    body.append(P.terrain_svg())
    body.append(P.water_svg())
    body.append(P.rivers_svg())

    wps = P.waypoints()
    ships, huts, mass, wall_svg, ditch_svg, ship_px = P.camp()

    # wall and ditch, then huts, then ships: inland to seaward is also far to
    # near in this camera, so painter order is depth order.
    body.append(f'<g class="tm2">{wall_svg}{ditch_svg}</g>')
    body.append('<g>' + "".join(h for h in huts if h) + "</g>")
    body.append('<g class="tm2">' + "".join(s for s in ships if s) + "</g>")
    body.append('<g class="t1-only">' + mass + "</g>")

    # the wagon-road, and the marks for the poem's waypoints
    road = []
    _, ford_t = P.road_t
    for m in range(41):
        lat, lon = P.road_pt(m * ford_t / 40.0)
        p = cam.project_ll(lat, lon, built_h(0.6, terr.elev(lat, lon)))
        if p:
            road.append((p[0], p[1]))
    if len(road) > 3:
        body.append('<g class="tm3"><path class="pp-road" d="%s"/></g>'
                    % rel_poly(road, close=False))

    marks, labels = [], []
    anchors: dict = {}
    for w in wps:
        lat, lon = w["at"]
        p = cam.project_ll(lat, lon, built_h(w["height"], terr.elev(lat, lon)))
        if not p:
            continue
        x, y, d = p
        anchors[w["id"]] = (x, y, d)
        w["_screen"] = [round(x, 1), round(y, 1), round(d, 1)]
        tier = w["tier"]
        if w["kind"] in ("site", "tumulus") and w["id"] != "ilios":
            r = max(2.4, FOCAL * 9.0 / d)
            if w["kind"] == "tumulus":
                marks.append(f'<g class="{tcls(tier)}"><path class="pp-tumulus" '
                             f'd="M{n1(x - r * 1.6)} {n1(y)}a{n1(r * 1.6)} {n1(r * 1.1)} 0 0 1 '
                             f'{n1(r * 3.2)} 0Z"/></g>')
            else:
                marks.append(f'<g class="{tcls(tier)}"><circle class="pp-mark" cx="{n1(x)}" '
                             f'cy="{n1(y)}" r="{n1(r)}"/></g>')

    if "wall_mid" in P.stats and "achaean-wall" in anchors:
        anchors["achaean-wall"] = (P.stats["wall_mid"][0], P.stats["wall_mid"][1],
                                   anchors["achaean-wall"][2])
    body.append("".join(marks))
    body.append(city(cam, terr, pp.TROY))

    # ── labels, by tier. Depth banding does the decluttering: tier 1 sits in
    # three different depth zones by construction, and tiers 2 and 3 only
    # appear once there is room for them.
    L = []
    A = anchors

    def put(pid, dx, dy, cls, tier, anchor="start", text=None, greek=""):
        if pid not in A:
            return
        x, y, _ = A[pid]
        w = next(v for v in wps if v["id"] == pid)
        txt = esc(text if text is not None else w["name"])
        L.append(f'<g class="{tcls(tier)}"><text class="plate-label {cls}" '
                 f'x="{n1(x + dx)}" y="{n1(y + dy)}"'
                 + (f' text-anchor="{anchor}"' if anchor != "start" else "")
                 + f'>{txt}'
                 + (f'<tspan class="pp-l-note" dx="7">{esc(greek)}</tspan>' if greek else "")
                 + '</text></g>')
        w["_label"] = [round(A[pid][0] + dx, 1), round(A[pid][1] + dy, 1)]

    # tier 1 — six marks and no more
    if "ilios" in A:
        x, y, _ = A["ilios"]
        L.append(f'<g><path class="pp-leader" d="M{n1(x + 5)} {n1(y - 7)}'
                 f'L{n1(x + 34)} {n1(y - 40)}"/></g>')
    put("ilios", 38, -44, "pp-l-settlement", 1)
    put("bay-of-troy", 0, 0, "pp-l-water", 1, "middle", text="the bay of Troy")
    put("scamander", 8, -8, "pp-l-water", 1, text="Scamander")
    if ida_crest:
        L.append(f'<g><text class="plate-label pp-l-region" '
                 f'x="{n1(ida_crest[0])}" y="{n1(ida_crest[1] - 16)}" '
                 f'text-anchor="middle">MOUNT IDA</text></g>')
    if ship_px:
        ends = sorted(ship_px, key=lambda q: q[2])
        mid = ends[len(ends) // 2]
        L.append(f'<g><text class="plate-label pp-l-region" x="{n1(mid[0])}" '
                 f'y="{n1(mid[1] + 34)}" text-anchor="middle">THE SHIPS</text></g>')
        # The camp by holder (Il. 8.222-226; 11.5-9): Ajax at the end toward
        # Rhoiteion, Achilles at the end toward Sigeion, Odysseus in the
        # middle with the place of assembly. WHICH end is which is decided by
        # measuring each end against the two headlands, never by left/right
        # in the frame (ruling 2a).
        def nearer(q, target):
            return math.hypot(*pp._flat_m((q[4], q[5]), *target))
        a, b = ends[0], ends[-1]
        if nearer(a, pp.RHOITEION) < nearer(b, pp.RHOITEION):
            ajax_end, ach_end = a, b
        else:
            ajax_end, ach_end = b, a
        for q, txt in ((ajax_end, "Ajax’s ships, the end toward Rhoiteion"),
                       (ach_end, "Achilles’ ships, the end toward Sigeion")):
            side = "start" if q[0] < W / 2 else "end"
            L.append(f'<g class="tm3"><text class="plate-label pp-l-site" x="{n1(q[0])}" '
                     f'y="{n1(q[1] + 22)}" text-anchor="{side}">{esc(txt)}</text></g>')
        L.append(f'<g class="tm3"><text class="plate-label pp-l-site" x="{n1(mid[0])}" '
                 f'y="{n1(mid[1] + 52)}" text-anchor="middle">'
                 f'Odysseus’ ships and the place of assembly</text></g>')

    # tier 2
    put("simoeis", 8, -8, "pp-l-water", 2)
    put("ford-of-the-scamander", 10, -10, "pp-l-site", 2, text="the ford of the Scamander")
    put("rhoiteion", 0, -14, "pp-l-region", 2, "middle")
    put("sigeion", 0, -14, "pp-l-region", 2, "middle")
    put("callicolone", 10, -12, "pp-l-site", 2, greek="Καλλικολώνη")
    put("achaean-wall", 0, 22, "pp-l-site", 2, "middle",
        text="the wall of the Achaeans, and the ditch")
    put("throsmos", 0, 30, "pp-l-site", 2, "middle",
        text="the rising ground of the plain", greek="θρωσμὸς πεδίοιο")
    put("delta-swamp", 0, 0, "pp-l-region", 2, "middle", text="MARSH AND WET DELTA")

    # tier 3
    put("scaean-gate", 0, -30, "pp-l-site", 3, "middle", text="the Scaean Gate and the oak")
    put("lookout-skopie", 0, 22, "pp-l-site", 3, "middle", text="the lookout")
    put("fig-tree", 0, -16, "pp-l-site", 3, "middle", text="the wild fig tree", greek="ἐρινεός")
    put("two-springs-of-scamander", 0, 22, "pp-l-site", 3, "middle", text="the two springs")
    put("tomb-of-ilos", 0, -18, "pp-l-site", 3, "middle", text="the tomb of Ilus")
    put("wagon-road", 12, 22, "pp-l-site", 3, text="the wagon-road", greek="ἀμαξιτός")
    put("batieia", 0, -16, "pp-l-site", 3, "middle", text="Batieia")
    put("wall-of-heracles", -10, -10, "pp-l-site", 3, "end", text="the wall of Heracles")

    body.append("".join(L))
    body.append("</g>")

    troy_d = A.get("ilios", (0, 0, 5500))[2]
    body.append('<g class="pp-furn">'
                + furniture(cam, terr, P.stats.get("ship_depth", 2600.0), troy_d)
                + '</g>')
    return "".join(body), wps, P


def emit(theme, inner, vx, vy, vw, vh, scale, out_svg, tier=3, descale=1.0,
         furn=True, caption=None):
    px_w, px_h = int(round(vw * scale)), int(round(vh * scale))
    # LABELS DO NOT MAGNIFY. The shipping SVG carries class `plate-label`,
    # which PlatePanel's existing hook wraps and counter-transforms; a static
    # render at k× emulates it with one CSS rule so what John looks at is what
    # the panel will do.
    ds = "" if descale == 1.0 else (
        f'.plate-label{{font-size:inherit}}'
    )
    tier_css = TIER_CSS[tier]
    scale_css = ""
    if descale != 1.0:
        k = 1.0 / descale
        scale_css = (f'.pp-l-region{{font-size:{15.5 * k:.2f}px;'
                     f'letter-spacing:{2.48 * k:.2f}px}}'
                     f'.pp-l-settlement{{font-size:{15 * k:.2f}px}}'
                     f'.pp-l-water{{font-size:{12.5 * k:.2f}px}}'
                     f'.pp-l-site{{font-size:{11.5 * k:.2f}px}}'
                     f'text{{stroke-width:{3.2 * k:.2f}}}'
                     f'.pp-l-note{{font-size:{10 * k:.2f}px;stroke-width:{2.4 * k:.2f}}}')
    furn_css = "" if furn else ".pp-furn{display:none}"
    cap = ""
    if caption:
        k = 1.0 / max(scale, 1e-6)
        cap = (f'<text class="pp-l-region" x="{n1(vx + vw / 2)}" '
               f'y="{n1(vy + 34 * k)}" text-anchor="middle" '
               f'font-size="{15.5 * k:.2f}px" letter-spacing="{2.48 * k:.2f}px" '
               f'stroke-width="{3.2 * k:.2f}">{esc(caption)}</text>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{px_w}" height="{px_h}" '
        f'viewBox="{n1(vx)} {n1(vy)} {n1(vw)} {n1(vh)}">'
        f'<style>svg{{{TOKENS[theme]}}}{CSS}{tier_css}{ds}{scale_css}{furn_css}</style>'
        f'{DEFS}'
        f'<rect x="{n1(vx)}" y="{n1(vy)}" width="{n1(vw)}" height="{n1(vh)}" '
        f'fill="var(--page-bg)"/>'
        f'{inner}{cap}</svg>'
    )
    with open(out_svg, "w") as f:
        f.write(svg)
    return px_w, px_h


def shoot(svg_path, png_path, w, h):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--screenshot={png_path}", svg_path],
                   check=True, capture_output=True)


# ═══════════════════════════════════════════════════════════════════════════
# camera-target table
# ═══════════════════════════════════════════════════════════════════════════
LABEL_EM = {"pp-l-region": 15.5, "pp-l-settlement": 15.0, "pp-l-water": 12.5,
            "pp-l-site": 11.5}


def camera_targets(wps, plate_stats):
    """The data the Chart Room consumes. Each row frames ONE subject with its
    own label box inside the frame with margin, which is the defect list's
    items 2 and 4 answered in data: nothing slices, and a frame names only its
    own subject."""
    rows = []
    for w in wps:
        scr = w.get("_screen")
        if not scr:
            continue
        x, y, d = scr
        lab = w.get("_label", [x, y])
        # the box that must survive the crop: subject + its label + margin
        chars = max(len(w["name"]), 12)
        lw = chars * 7.2
        x0 = min(x - 40, lab[0] - lw * 0.5) - 60
        x1 = max(x + 40, lab[0] + lw * 0.5) + 60
        y0 = min(y - 46, lab[1] - 24) - 40
        y1 = max(y + 46, lab[1] + 16) + 40
        # A POSTCARD IS NOT A MACRO. Fitting the box alone drove every frame
        # to the cap and reproduced the Chart Room's own defect from the other
        # side: a 5.5x crop of a site mark shows the mark and no country.
        # Each kind therefore declares the MINIMUM extent its frame must
        # carry, and the fit only tightens from there.
        min_w, min_h = {"region": (1150.0, 647.0), "water": (1000.0, 563.0),
                        "line": (820.0, 461.0), "settlement": (560.0, 315.0),
                        "tumulus": (520.0, 293.0)}.get(w["kind"], (520.0, 293.0))
        bw, bh = max(x1 - x0, min_w), max(y1 - y0, min_h)
        zoom = min(W / bw, H / bh)
        zoom = max(1.6, min(4.0, zoom))
        rows.append({
            "id": w["id"],
            "name": w["name"],
            "greek": w["greek"],
            "tier": w["tier"],
            "positionBasis": w["positionBasis"],
            "citation": w["citation"],
            "tradition": w["tradition"] or None,
            "rule": w["rule"],
            "at": [round(w["at"][0], 5), round(w["at"][1], 5)],
            "frame": {"x": x, "y": y, "depthM": d},
            "camera": {"cx": round((x0 + x1) / 2, 1),
                       "cy": round((y0 + y1) / 2, 1),
                       "zoom": round(zoom, 2)},
            "showTiers": list(range(1, w["tier"] + 1)),
        })
    return {
        "id": "panorama-ships-bay-ilios",
        "title": "The Ships, the Bay, and Ilios",
        "status": "draft",
        "frame": {"w": W, "h": H},
        "camera": {
            "viewpoint": list(VIEWPOINT), "headingDeg": HEADING_DEG,
            "hfovDeg": HFOV_DEG, "altM": ALT, "setbackM": SETBACK,
            "pitchDegDown": None,
            "verticalExaggerationCurve": CURVE,
            "verticalExaggeration": DISCLOSURE[CURVE],
        },
        "note": (
            "Camera targets for the Chart Room 'postcard' frames. Each row is "
            "sized round its own subject AND its label box, so no crop slices a "
            "label; showTiers says which level-of-detail tiers a frame turns on, "
            "so a frame pins only its own subject. Labels carry class "
            "plate-label and must be counter-scaled (pp-label-descale) — type "
            "never magnifies. A locator inset showing this rectangle against the "
            "full frame is the caller's job."),
        "stats": plate_stats,
        "targets": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(REPO, "build", "panorama"))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--curve", choices=("A", "B", "C"), default=CURVE,
                    help="vertical-exaggeration curve (see ve/exaggerate)")
    args = ap.parse_args()
    globals()["CURVE"] = args.curve
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"curve {args.curve}: " + " ".join(
        f"{e:g}->{exaggerate(float(e)):.0f}" for e in (10, 100, 300, 800, 1774)))

    terr = Terrain()
    cam = Camera(terr.plain)
    with open(os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")) as f:
        plate_json = json.load(f)

    print(f"pitch {math.degrees(cam.pitch):.2f} deg down; focal {FOCAL:.1f}")
    inner, wps, P = build(terr, cam, plate_json)
    print(f"mesh {len(P.azs)}x{len(P.rngs)} = {len(P.azs) * len(P.rngs)} nodes; "
          f"cells tested {P.stats['cells_tested']}, visible "
          f"{P.stats['cells_visible']} "
          f"({100 * P.stats['cells_visible'] / max(1, P.stats['cells_tested']):.0f}%)")
    print(f"hulls {P.stats['hulls']}, huts {P.stats['huts']}")

    tgt = camera_targets(wps, dict(P.stats))
    tgt["camera"]["pitchDegDown"] = round(math.degrees(cam.pitch), 2)
    tp = os.path.join(args.out_dir, "stage3-camera-targets.json")
    with open(tp, "w") as f:
        json.dump(tgt, f, ensure_ascii=False, indent=2)
    print(f"camera targets -> {tp} ({len(tgt['targets'])} rows)")

    themes = ("light",) if args.quick else ("light", "dark")
    for theme in themes:
        sfx = "" if theme == "light" else "-dark"
        svg = os.path.join(args.out_dir, f"stage3-full{sfx}.svg")
        w, h = emit(theme, inner, 0, 0, W, H, 1.0, svg, tier=1)
        shoot(svg, os.path.join(args.out_dir, f"stage3-full{sfx}.png"), w, h)
        sz = os.path.getsize(svg)
        print(f"[{theme}] full 1x  {sz / 1024:.0f} KB ({sz} bytes) -> {w}x{h}")
        if args.quick:
            break
        # The 4x crops are taken from the CAMERA-TARGET TABLE where the table
        # has a row for them, so the renders John looks at are the frames the
        # Chart Room would actually serve.
        by_id = {t["id"]: t for t in tgt["targets"]}
        cams = {"troy": (by_id["ilios"]["camera"]["cx"], by_id["ilios"]["camera"]["cy"]),
                "camp": (1250.0, 665.0)}
        for name, (cx, cy) in cams.items():
            cw, ch = W / 4.0, H / 4.0
            s2 = os.path.join(args.out_dir, f"stage3-zoom-{name}{sfx}.svg")
            w2, h2 = emit(theme, inner, cx - cw / 2, cy - ch / 2, cw, ch, 4.0, s2,
                          tier=3, descale=4.0)
            shoot(s2, os.path.join(args.out_dir, f"stage3-zoom-{name}{sfx}.png"), w2, h2)
        # mobile portrait: the crop frames the SIGHTLINE, not the panorama --
        # camp, bay, city, Ida in depth order. What portrait gives up is the
        # flanks: the headlands and the swamp.
        # PORTRAIT FRAMES THE SIGHTLINE, NOT THE PANORAMA. A 72-degree
        # landscape oblique cannot show its whole self on a phone, and the
        # thing worth keeping is the DEPTH AXIS -- camp, ships, bay, city,
        # Ida, in the order the poem's action crosses them. The crop is
        # therefore a full-height column on Ilios's own bearing. What it gives
        # up is the flanks: the headlands, the swamp, the Scamander's course,
        # and the cartouche, which is re-laid as a caption. Tier 1 only:
        # tier-2 labels are anchored across the full width and a portrait crop
        # slices them, which is defect 2 on the Chart Room list.
        # a tier-2 full frame as well: it is the state the swamp, the wall,
        # the ditch, the Simoeis and the headland labels first appear in, and
        # nothing else renders them.
        s2t = os.path.join(args.out_dir, f"stage3-full-tier2{sfx}.svg")
        w2t, h2t = emit(theme, inner, 0, 0, W, H, 1.0, s2t, tier=2)
        shoot(s2t, os.path.join(args.out_dir, f"stage3-full-tier2{sfx}.png"), w2t, h2t)
        pw = H * (390.0 / 780.0)
        s3 = os.path.join(args.out_dir, f"stage3-mobile-portrait{sfx}.svg")
        w3, h3 = emit(theme, inner, 1376 - pw / 2, 0, pw, H, 780.0 / H, s3,
                      tier=1, descale=780.0 / H, furn=False,
                      caption="THE SHIPS, THE BAY, AND ILIOS")
        shoot(s3, os.path.join(args.out_dir, f"stage3-mobile-portrait{sfx}.png"), w3, h3)
    print("done")


if __name__ == "__main__":
    main()
