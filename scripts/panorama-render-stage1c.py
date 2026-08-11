#!/usr/bin/env python3
"""Stage-1C: terrain + water render of the raised-oblique bird's-eye of the
Trojan plain, from the settled Stage-1B camera (alt 800 m, setback 1500 m
along the reverse Sigeion->Troy bearing, hfov 55 deg, pitch bisecting
near/far). See docs/PANORAMA-RESUME.md for lane background; the camera
itself is DONE and unchanged here (imported by re-deriving it from the same
pp.SIGEION/pp.TROY control points panorama-render-stage1b.py uses).

Two things this stage does that Stage 1B did not:
  1. Vertical exaggeration raised 1.75x -> 4x (John's ruling: the plain is
     genuinely almost flat -- Troy's mound is 36 m and the ridge behind it
     58 m across six km, seen from 800 m up -- so push the exaggeration
     hard and let the built content carry the rest). VE is a disclosed
     factor (printed below), for the plate's margin.
  2. The checkerboard (debug texture) is replaced with the engraved
     line-and-tint register the map plates already use: flat hypsometric
     tone bands (shared/styles/global.css --plate-relief-1..12), hairline
     contours between them (--plate-contour), and real water -- the
     reconstructed Bronze Age bay (apparatus/plates/trojan-plain.json's
     lagoon-bronze polygon, --plate-lagoon) over the modern open sea
     (sea-modern polygon, --scene-map-sea) -- plus the Scamander and
     Simoeis courses (sources/openstreetmap/trojan-plain-rivers.json,
     --plate-river), clipped at the reconstructed shore per each river
     layer's own note (the surveyed course runs on to the modern mouth;
     with the Bronze Age bay shown, what's drawn stops at the bay it
     entered in 1200 BC).

No city, no buildings, no labels, no camp, no ships -- terrain and water
only, per the Stage-1C brief. The ten Stage-1B diagnostic waypoint dots are
kept so the on-screen separation result stays visible; nothing else.

Renders BOTH themes (light/dark), each a real independent colour set pulled
from shared/styles/global.css's tokens -- not one image with a CSS filter --
because "does the dark variant hold up" is exactly the thing being tested.

No PIL/matplotlib in pipeline/.venv (stdlib + numpy only) -- pixels are
composed with numpy, written as a binary PPM, converted to PNG with macOS's
`sips`, exactly as the Stage 1/1B scripts do.

Usage:
  python3 scripts/panorama-render-stage1c.py
    -> writes panorama-stage1c-terrain.png (light) and
       panorama-stage1c-terrain-dark.png (dark) at the repo root.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "panorama_profile", os.path.join(REPO, "scripts", "panorama-profile.py")
)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)  # type: ignore[union-attr]

# ── canvas ───────────────────────────────────────────────────────────────
W, H = 2400, 1350  # 16:9

# ── camera (settled Stage-1B geometry -- John approved 2026-08; do not
# change): alt 800 m, setback 1500 m, hfov 55 deg, true perspective, pitch
# bisecting the near-field and Troy angles. ──────────────────────────────
ALT = 800.0
SETBACK = 1500.0
HFOV_DEG = 55.0

# vertical exaggeration -- disclosed factor, reported on stdout below for
# the plate's margin caption. Raised from Stage 1B's 1.75x on John's
# ruling (2026-08-10/11): the DEM read as a dead flat plane at 1.75x
# because the plain genuinely is that flat at this remove; push it hard.
VE = 4.0

RAMP_STEPS = 12  # matches shared/lib/plate.ts RELIEF_RAMP_STEPS

# terrain sampling grid, in metres along (forward = bearing to Troy,
# right = perpendicular) axes from the viewpoint -- unchanged from Stage 1B
FORWARD_RANGE = (-900.0, 7200.0)
LATERAL_RANGE = (-3200.0, 3200.0)
GRID_STEP = 160.0

NEAR_CLIP = 5.0  # metres; points/quads closer than this to the camera plane are dropped


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ── theme palettes, pulled from shared/styles/global.css (see this
# script's docstring for the token names; every value below is copy-typed
# from that file, not invented) ────────────────────────────────────────
THEMES = {
    "light": dict(
        sky=_hex("#E7E7E9"),  # --page-bg (light); no dedicated sky token exists
        ramp=[_hex(c) for c in [
            "#EDEEDF", "#E8E8CF", "#E4E2C0", "#E1DAB3", "#DED3A7", "#DACB9E",
            "#D5C296", "#D0B98C", "#CAB083", "#C2A679", "#B99C6F", "#AF9164",
        ]],  # --plate-relief-1..12 (light)
        contour=_hex("#5A4A32"),   # --plate-contour (light)
        coast=_hex("#565060"),     # --scene-map-coast (light)
        lagoon=_hex("#87AEB8"),    # --plate-lagoon (light)
        sea=_hex("#9BBFD6"),       # --scene-map-sea (light)
        river=_hex("#1A4C6A"),     # --plate-river (light)
        dot_outline=(25, 24, 22),      # ~ --text (light, #241827)
        dot_viewpoint=(45, 85, 165),   # ~ --accent-ish blue, unchanged from Stage 1B
        dot_troy=(175, 35, 30),        # ~ --error (light, #b22323)
        dot_shore=(30, 120, 118),
        dot_waypoint=(205, 120, 20),
    ),
    "dark": dict(
        sky=_hex("#181120"),  # --page-bg (dark)
        ramp=[_hex(c) for c in [
            "#4A4136", "#51473A", "#584D3D", "#5F523F", "#655740", "#6B5C42",
            "#706043", "#766444", "#7A6846", "#7E6C48", "#836F49", "#86734B",
        ]],  # --plate-relief-1..12 (dark)
        contour=_hex("#C2B189"),   # --plate-contour (dark)
        coast=_hex("#8FA3AE"),     # --scene-map-coast (dark)
        lagoon=_hex("#0A2430"),    # --plate-lagoon (dark)
        sea=_hex("#0A1C2A"),       # --scene-map-sea (dark)
        river=_hex("#B4DAEF"),     # --plate-river (dark)
        dot_outline=(237, 230, 232),   # ~ --text (dark, #EDE6E8)
        dot_viewpoint=(130, 170, 235),
        dot_troy=(230, 95, 85),
        dot_shore=(90, 190, 185),
        dot_waypoint=(235, 170, 80),
    ),
}


# ── data loaders (READ-ONLY; apparatus/plates/trojan-plain.json and
# sources/openstreetmap/trojan-plain-rivers.json are not touched) ───────
def _load_trojan_plain_layers():
    path = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")
    with open(path) as f:
        d = json.load(f)
    return {l["id"]: l for l in d["layers"]}


def _load_rivers():
    path = os.path.join(REPO, "sources", "openstreetmap", "trojan-plain-rivers.json")
    with open(path) as f:
        d = json.load(f)
    return {f["id"]: f["points"] for f in d["features"]}


def points_in_polygon(lat_arr: np.ndarray, lon_arr: np.ndarray, poly_latlon) -> np.ndarray:
    """Vectorised ray-casting point-in-polygon. poly_latlon: list of [lat,lon].
    Planar (lon=x, lat=y) -- valid at this sheet's ~24 km scale, same posture
    as panorama-profile.py's own _flat_m."""
    poly = np.asarray(poly_latlon, dtype=np.float64)
    x = lon_arr
    y = lat_arr
    n = poly.shape[0]
    inside = np.zeros(x.shape, dtype=bool)
    xj, yj = poly[-1, 1], poly[-1, 0]
    for i in range(n):
        xi, yi = poly[i, 1], poly[i, 0]
        denom = yj - yi
        denom = denom if denom != 0 else 1e-15
        cond = (yi > y) != (yj > y)
        xint = (xj - xi) * (y - yi) / denom + xi
        inside ^= cond & (x < xint)
        xj, yj = xi, yi
    return inside


def build_scene(gr, viewpoint, bearing_deg):
    """Regular grid of (lat, lon, elev) over the plain, in forward/lateral
    metres from the viewpoint. Returns elev[i][j] (NaN where outside the
    trojan-plain bbox) and the coordinate arrays, plus lat/lon grids so
    water classification can run against the plate's own polygons."""
    theta = math.radians(bearing_deg)
    fwd = (math.sin(theta), math.cos(theta))
    right = (math.sin(theta + math.pi / 2), math.cos(theta + math.pi / 2))
    lat0 = math.radians(viewpoint[0])

    f0, f1 = FORWARD_RANGE
    r0, r1 = LATERAL_RANGE
    fs = np.arange(f0, f1 + GRID_STEP / 2, GRID_STEP)
    rs = np.arange(r0, r1 + GRID_STEP / 2, GRID_STEP)

    elev = np.full((len(fs), len(rs)), np.nan, dtype=np.float64)
    east = np.zeros_like(elev)
    north = np.zeros_like(elev)
    lat_g = np.full_like(elev, np.nan)
    lon_g = np.full_like(elev, np.nan)
    for i, f in enumerate(fs):
        for j, r in enumerate(rs):
            e = f * fwd[0] + r * right[0]
            n = f * fwd[1] + r * right[1]
            east[i, j] = e
            north[i, j] = n
            lat = viewpoint[0] + n / 111132.0
            lon = viewpoint[1] + e / (111320.0 * math.cos(lat0))
            lat_g[i, j] = lat
            lon_g[i, j] = lon
            if 39.86 <= lat <= 40.05 and 26.1 <= lon <= 26.38:
                elev[i, j] = pp.bilinear_elev(gr, lat, lon)
    return fs, rs, east, north, elev, lat_g, lon_g


def project(camera, forward, right_v, up_v, focal, pts_world):
    """pts_world: Nx3 array of (east, north, elev*VE). Returns (px, py, depth)."""
    rel = pts_world - camera
    depth = rel @ forward
    xc = rel @ right_v
    yc = rel @ up_v
    with np.errstate(divide="ignore", invalid="ignore"):
        px = W / 2.0 + focal * (xc / depth)
        py = H / 2.0 - focal * (yc / depth)
    return px, py, depth


def fill_quad(img, pts, color):
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(H - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1_ = pts[i]
            x2, y2_ = pts[(i + 1) % n]
            if y1_ == y2_:
                continue
            if (y >= y1_ and y < y2_) or (y >= y2_ and y < y1_):
                t = (y - y1_) / (y2_ - y1_)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(round(xs[k])))
            xb = min(W - 1, int(round(xs[k + 1])))
            if xb >= xa:
                img[y, xa:xb + 1] = color


def draw_line(img, x0, y0, x1, y1, color, width=1, alpha=1.0):
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
        return
    length = max(abs(x1 - x0), abs(y1 - y0))
    steps = max(1, int(length))
    xs = np.linspace(x0, x1, steps + 1)
    ys = np.linspace(y0, y1, steps + 1)
    r = width // 2
    col = np.array(color, dtype=np.float32)
    for x, y in zip(xs, ys):
        xi, yi = int(round(x)), int(round(y))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                xx, yy = xi + dx, yi + dy
                if 0 <= xx < W and 0 <= yy < H:
                    if alpha >= 1.0:
                        img[yy, xx] = color
                    else:
                        img[yy, xx] = (
                            img[yy, xx].astype(np.float32) * (1 - alpha) + col * alpha
                        ).astype(np.uint8)


def draw_dot(img, x, y, r, color, outline):
    if not (0 <= x < W and 0 <= y < H):
        return
    xi, yi = int(round(x)), int(round(y))
    for dy in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            if dx * dx + dy * dy <= (r + 1) ** 2:
                yy, xx = yi + dy, xi + dx
                if 0 <= xx < W and 0 <= yy < H:
                    d2 = dx * dx + dy * dy
                    img[yy, xx] = color if d2 <= r * r else outline


def waypoint_targets(bearing_deg):
    """Unchanged from Stage 1B: ~10 diagnostic points spread across the
    plain between camp and Troy, mixing on-axis and off-axis so 2-D
    separation is visible."""
    return [
        (600, 0), (1600, 0), (2600, 0), (3600, 0), (4600, 0),
        (1100, 700), (2100, -700), (3100, 700), (4100, -700), (5100, 700),
    ]


def render(theme_name: str, out_path: str, verbose: bool = True):
    T = THEMES[theme_name]
    layers = _load_trojan_plain_layers()
    rivers = _load_rivers()
    lagoon_poly = layers["lagoon-bronze"]["polygon"]
    sea_poly = layers["sea-modern"]["polygon"]
    shore_bronze_pts = [p for ring in layers["shore-bronze"]["rings"] for p in ring]

    gr, stats, relief_stats = pp.load_plain_grid()
    viewpoint = pp.SIGEION
    bearing = pp._bearing_deg(pp.SIGEION, pp.TROY)
    theta = math.radians(bearing)

    fs, rs, east, north, elev, lat_g, lon_g = build_scene(gr, viewpoint, bearing)

    # camera: unchanged Stage-1B placement
    cam_e = -SETBACK * math.sin(theta)
    cam_n = -SETBACK * math.cos(theta)
    camera = np.array([cam_e, cam_n, ALT])

    troy_e, troy_n = pp._flat_m(pp.TROY, viewpoint[0], viewpoint[1])
    troy_elev = pp.bilinear_elev(gr, *pp.TROY)
    target = np.array([troy_e, troy_n, troy_elev * VE])

    view_z = pp.bilinear_elev(gr, *viewpoint) * VE
    troy_horiz = math.hypot(troy_e - cam_e, troy_n - cam_n)
    near_angle = math.atan2(ALT - view_z, SETBACK)
    far_angle = math.atan2(ALT - target[2], troy_horiz)
    pitch = (near_angle + far_angle) / 2.0

    forward = np.array([math.sin(theta) * math.cos(pitch),
                         math.cos(theta) * math.cos(pitch),
                         -math.sin(pitch)])
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0])
    right_v = np.cross(forward, world_up)
    right_v = right_v / np.linalg.norm(right_v)
    up_v = np.cross(right_v, forward)

    focal = (W / 2.0) / math.tan(math.radians(HFOV_DEG) / 2.0)

    img = np.empty((H, W, 3), dtype=np.uint8)
    img[:, :] = T["sky"]

    # ── water classification, per vertex: 0=land, 1=lagoon (Bronze Age
    # bay), 2=sea (modern open sea, drawn as the base the reconstruction
    # sits over -- exactly the layering apparatus/plates/trojan-plain.json's
    # own sea-modern note specifies: "Drawn first, under every other
    # layer"). Priority: lagoon over sea over land. ────────────────────
    valid = ~np.isnan(elev)
    ni, nj = elev.shape
    water = np.full((ni, nj), -1, dtype=np.int8)
    flat_lat = lat_g[valid]
    flat_lon = lon_g[valid]
    in_lagoon = points_in_polygon(flat_lat, flat_lon, lagoon_poly)
    in_sea = points_in_polygon(flat_lat, flat_lon, sea_poly)
    w_flat = np.zeros(flat_lat.shape, dtype=np.int8)
    w_flat[in_sea] = 2
    w_flat[in_lagoon] = 1
    water[valid] = w_flat

    # ── hypsometric band range: land cells only, so the ~2 km sliver of
    # near-zero bay/sea elevations doesn't compress the plain's real
    # (small) relief into one or two bands. ─────────────────────────────
    land_mask = valid & (water == 0)
    land_elevs = elev[land_mask]
    if land_elevs.size > 0:
        emin, emax = float(np.min(land_elevs)), float(np.max(land_elevs))
    else:
        emin, emax = 0.0, 1.0
    erange = max(emax - emin, 1e-6)

    world = np.stack([east, north, elev * VE], axis=-1)
    flat_world = world.reshape(-1, 3)
    px, py, depth = project(camera, forward, right_v, up_v, focal, flat_world)
    px = px.reshape(ni, nj)
    py = py.reshape(ni, nj)
    depth = depth.reshape(ni, nj)

    # ── per-quad classification: land band (1..12, continuous elevation
    # threshold over the land-only range -- matches plate.ts's rank-over-
    # the-sheet's-own-elevations posture, adapted for a continuous DEM
    # instead of a short discrete level list) or water class. ──────────
    quads = []
    edges = []  # (x0,y0,x1,y1,color) contour/coast hairlines
    band_grid = np.full((ni - 1, nj - 1), -1, dtype=np.int16)   # -1 = water or invalid
    class_grid = np.full((ni - 1, nj - 1), -1, dtype=np.int8)   # 0 land, 1 lagoon, 2 sea, -1 invalid

    for i in range(ni - 1):
        for j in range(nj - 1):
            if not (valid[i, j] and valid[i + 1, j] and valid[i + 1, j + 1] and valid[i, j + 1]):
                continue
            d = (depth[i, j], depth[i + 1, j], depth[i + 1, j + 1], depth[i, j + 1])
            if min(d) <= NEAR_CLIP:
                continue
            wv = (water[i, j], water[i + 1, j], water[i + 1, j + 1], water[i, j + 1])
            n_water = sum(1 for v in wv if v >= 1)
            if n_water >= 2:
                cls = 1 if 1 in wv else 2
                color = T["lagoon"] if cls == 1 else T["sea"]
                band_grid[i, j] = -1
            else:
                cls = 0
                qelev = (elev[i, j] + elev[i + 1, j] + elev[i + 1, j + 1] + elev[i, j + 1]) / 4.0
                rank = min(0.999999, max(0.0, (qelev - emin) / erange))
                band = 1 + int(rank * RAMP_STEPS)
                band = min(RAMP_STEPS, max(1, band))
                color = T["ramp"][band - 1]
                band_grid[i, j] = band
            class_grid[i, j] = cls

            pts = [(px[i, j], py[i, j]), (px[i + 1, j], py[i + 1, j]),
                   (px[i + 1, j + 1], py[i + 1, j + 1]), (px[i, j + 1], py[i, j + 1])]
            avg_depth = sum(d) / 4.0
            quads.append((avg_depth, pts, color))

    quads.sort(key=lambda q: -q[0])  # far first, near last (painter's algorithm)
    for _, pts, color in quads:
        fill_quad(img, pts, color)

    # ── hairlines: coast between land and water (or lagoon and sea),
    # walked quad-to-quad (a clean binary classification, so a shared-edge
    # comparison is the right test). ─────────────────────────────────────
    def coast_edge(ci, cj):
        c0, c1 = class_grid[ci], class_grid[cj]
        if c0 < 0 or c1 < 0 or c0 == c1:
            return None
        return T["coast"], 1.0

    for i in range(ni - 2):
        for j in range(nj - 1):
            res = coast_edge((i, j), (i + 1, j))
            if res:
                color, alpha = res
                x0, y0 = px[i + 1, j], py[i + 1, j]
                x1, y1 = px[i + 1, j + 1], py[i + 1, j + 1]
                if depth[i + 1, j] > NEAR_CLIP and depth[i + 1, j + 1] > NEAR_CLIP:
                    draw_line(img, x0, y0, x1, y1, color, width=1, alpha=alpha)
    for i in range(ni - 1):
        for j in range(nj - 2):
            res = coast_edge((i, j), (i, j + 1))
            if res:
                color, alpha = res
                x0, y0 = px[i, j + 1], py[i, j + 1]
                x1, y1 = px[i + 1, j + 1], py[i + 1, j + 1]
                if depth[i, j + 1] > NEAR_CLIP and depth[i + 1, j + 1] > NEAR_CLIP:
                    draw_line(img, x0, y0, x1, y1, color, width=1, alpha=alpha)

    # ── contour hairlines: true isolines (simplified marching squares —
    # no saddle disambiguation, which this register doesn't need), traced
    # at the RAMP_STEPS-1 elevation thresholds that separate the
    # hypsometric bands. This replaced a first attempt that drew a
    # hairline on every quad-to-quad boundary where the discrete band
    # differed: on the steep spur/ridge near Hisarlik that fired on
    # almost every cell edge in BOTH grid directions and rendered as a
    # dense diagonal cross-hatch (a shaded mesh, exactly what "flat tone
    # bands... not a shaded mesh" rules out) rather than lines that
    # follow the slope. A true isoline crosses each quad at most once,
    # so on steep ground it naturally produces closely spaced near-
    # parallel lines -- correct contour-map behaviour -- instead of a
    # mesh, and on the near-flat plain it produces widely spaced lines. */
    levels = [emin + k * (erange / RAMP_STEPS) for k in range(1, RAMP_STEPS)]
    for i in range(ni - 1):
        for j in range(nj - 1):
            if class_grid[i, j] != 0:
                continue
            d4 = (depth[i, j], depth[i + 1, j], depth[i + 1, j + 1], depth[i, j + 1])
            if min(d4) <= NEAR_CLIP:
                continue
            es = (elev[i, j], elev[i + 1, j], elev[i + 1, j + 1], elev[i, j + 1])
            ps = ((px[i, j], py[i, j]), (px[i + 1, j], py[i + 1, j]),
                  (px[i + 1, j + 1], py[i + 1, j + 1]), (px[i, j + 1], py[i, j + 1]))
            for level in levels:
                if level < min(es) or level > max(es):
                    continue
                crossings = []
                for a in range(4):
                    b = (a + 1) % 4
                    ea, eb = es[a], es[b]
                    if (ea - level) * (eb - level) > 0:
                        continue
                    if ea == eb:
                        continue
                    t = min(1.0, max(0.0, (level - ea) / (eb - ea)))
                    xa, ya = ps[a]
                    xb, yb = ps[b]
                    crossings.append((xa + t * (xb - xa), ya + t * (yb - ya)))
                if len(crossings) >= 2:
                    (x0, y0), (x1, y1) = crossings[0], crossings[1]
                    draw_line(img, x0, y0, x1, y1, T["contour"], width=1, alpha=0.55)

    # ── rivers: Scamander and Simoeis, clipped where they enter the
    # reconstructed Bronze Age bay (each layer's own note in
    # trojan-plain.json: with the bay shown, the surveyed course -- which
    # continues to the modern mouth -- is not drawn past the point where
    # the ground it crosses was open water in 1200 BC). ─────────────────
    def draw_river(points_latlon, color):
        lat_arr = np.array([p[0] for p in points_latlon])
        lon_arr = np.array([p[1] for p in points_latlon])
        in_lag = points_in_polygon(lat_arr, lon_arr, lagoon_poly)
        prev = None
        for k, (lat, lon) in enumerate(points_latlon):
            if in_lag[k]:
                prev = None
                continue
            if not (39.86 <= lat <= 40.05 and 26.1 <= lon <= 26.38):
                # outside the DEM bbox -- no real elevation to sample, and
                # this stage's whole point is data-derived terrain, so
                # break the line here rather than fabricate elev=0 and
                # draw a long, wrong segment across the frame (this is
                # what produced two stray lines cutting across the sky in
                # the first draft of this render).
                prev = None
                continue
            e = pp.bilinear_elev(gr, lat, lon)
            ee, nn = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
            wp = np.array([[ee, nn, e * VE]])
            xarr, yarr, darr = project(camera, forward, right_v, up_v, focal, wp)
            x, y, d = float(xarr[0]), float(yarr[0]), float(darr[0])
            if d <= NEAR_CLIP:
                prev = None
                continue
            if prev is not None:
                draw_line(img, prev[0], prev[1], x, y, color, width=3)
            prev = (x, y)

    draw_river(rivers["scamander"], T["river"])
    draw_river(rivers["simoeis"], T["river"])

    # ── diagnostic dots (Stage 1B waypoints, kept) ──────────────────────
    dot_report = []

    def project_one(lat, lon, elev_m, label, color, radius):
        e, n = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
        wp = np.array([e, n, elev_m * VE])
        x, y, d = project(camera, forward, right_v, up_v, focal, wp.reshape(1, 3))
        x, y, d = float(x[0]), float(y[0]), float(d[0])
        onscreen = d > NEAR_CLIP and 0 <= x < W and 0 <= y < H
        if onscreen:
            draw_dot(img, x, y, radius, color, T["dot_outline"])
        dot_report.append((label, lat, lon, round(elev_m, 1), round(x, 1), round(y, 1), onscreen))
        return x, y, onscreen

    project_one(viewpoint[0], viewpoint[1], pp.bilinear_elev(gr, *viewpoint), "viewpoint", T["dot_viewpoint"], 8)
    project_one(pp.TROY[0], pp.TROY[1], troy_elev, "hisarlik", T["dot_troy"], 8)

    # shore reference dots now sourced from the Bronze Age shore (not the
    # modern coastline) -- consistent with the water this stage draws
    mid = pp._dest_point(viewpoint, bearing, 3000.0)

    def nearest(pt, pts):
        best, bd = None, None
        for c in pts:
            dx, dy = pp._flat_m(c, pt[0], pt[1])
            dd = dx * dx + dy * dy
            if bd is None or dd < bd:
                bd, best = dd, c
        return best

    for label, anchor in (("shore_near_camp", viewpoint), ("shore_mid_bay", mid)):
        c = nearest(anchor, shore_bronze_pts)
        lat_c, lon_c = c
        elev_c = 0.0
        if 39.86 <= lat_c <= 40.05 and 26.1 <= lon_c <= 26.38:
            elev_c = max(0.0, pp.bilinear_elev(gr, lat_c, lon_c))
        project_one(lat_c, lon_c, elev_c, label, T["dot_shore"], 7)

    waypoint_px = []
    for k, (f, r) in enumerate(waypoint_targets(bearing)):
        e = f * math.sin(theta) + r * math.sin(theta + math.pi / 2)
        n = f * math.cos(theta) + r * math.cos(theta + math.pi / 2)
        lat = viewpoint[0] + n / 111132.0
        lon = viewpoint[1] + e / (111320.0 * math.cos(math.radians(viewpoint[0])))
        wev = pp.bilinear_elev(gr, lat, lon) if (39.86 <= lat <= 40.05 and 26.1 <= lon <= 26.38) else 0.0
        x, y, onscreen = project_one(lat, lon, wev, f"waypoint_{k}", T["dot_waypoint"], 6)
        if onscreen:
            waypoint_px.append((x, y))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    ppm_path = out_path.rsplit(".", 1)[0] + ".ppm"
    with open(ppm_path, "wb") as f:
        f.write(f"P6\n{W} {H}\n255\n".encode())
        f.write(img.tobytes())
    subprocess.run(["sips", "-s", "format", "png", ppm_path, "--out", out_path],
                    check=True, capture_output=True)
    os.remove(ppm_path)

    min_sep = None
    for i in range(len(waypoint_px)):
        for j in range(i + 1, len(waypoint_px)):
            dx = waypoint_px[i][0] - waypoint_px[j][0]
            dy = waypoint_px[i][1] - waypoint_px[j][1]
            dist = math.hypot(dx, dy)
            if min_sep is None or dist < min_sep:
                min_sep = dist

    if verbose:
        print(f"[{theme_name}] wrote {out_path}  (alt={ALT} m, setback={SETBACK} m, "
              f"hfov={HFOV_DEG} deg, VE={VE}x [DISCLOSE])")
        print(f"  land elevation range in frame (band basis): {emin:.1f}-{emax:.1f} m "
              f"({RAMP_STEPS} bands, {erange/RAMP_STEPS:.2f} m/band)")
        print(f"  quads: {len(quads)}; on-screen waypoints: {len(waypoint_px)}/10, "
              f"min pairwise separation: {min_sep:.1f} px" if min_sep is not None else "  n/a")
        for label, lat, lon, e, x, y, onscreen in dot_report:
            print(f"  {label:16s} lat={lat:.5f} lon={lon:.5f} elev={e:6.1f}m -> px=({x:7.1f},{y:7.1f}) "
                  f"{'ON' if onscreen else 'OFF'}-screen")
    return min_sep, len(waypoint_px)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-light", default=os.path.join(REPO, "panorama-stage1c-terrain.png"))
    ap.add_argument("--out-dark", default=os.path.join(REPO, "panorama-stage1c-terrain-dark.png"))
    args = ap.parse_args()
    render("light", args.out_light)
    print()
    render("dark", args.out_dark)


if __name__ == "__main__":
    main()
