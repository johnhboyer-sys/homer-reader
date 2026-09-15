#!/usr/bin/env python3
"""Stage-1D: terrain + water render of the raised-oblique bird's-eye of the
Trojan plain, from the SETTLED camera the Opus vantage lane produced (John's
brief, 2026-08-10/11). Not eye-level -- a raised oblique, same family as
Stage 1B/1C, but every camera number below is new: independently placed
viewpoint, wider hfov, wider grid, finer step, and a vertical-exaggeration
taper instead of a flat multiplier. See docs/PANORAMA-RESUME.md for lane
background.

Camera (given, not re-derived):
  viewpoint   39.9755 N, 26.1785 E (DEM 37.6 m) -- on the ridge crest, inside
              achaean-camp-zone
  heading     104.0 deg compass (Troy +7.7 deg right of centre, Rhoiteion
              -33.8 deg, both confirmed by direct bearing computation below)
  hfov        72 deg (vfov ~= 44.6 deg at 16:9)
  altitude    800 m (world-z, unscaled -- see VE note)
  setback     1500 m, on the reverse heading from the viewpoint
  pitch       bisects the near-field angle (down to the viewpoint's own
              ground) and the far-field angle (down to the ground straight
              ahead at FORWARD_RANGE's far edge, 9500 m out) -- generalises
              Stage 1C's "bisect near/Troy" now that Troy sits off-axis
  VE          4.0 for elevations <=100 m, tapering linearly to 1.0 at 300 m,
              1.0 above. Applied per-vertex (elev -> elev * ve(elev)).
              Camera altitude (800) and Ida's real elevation are NOT
              multiplied by ve() -- see the "world-z convention" note below.
  grid        FORWARD (-1500, 9500) m, LATERAL +-5800 m, step 60 m

World-z convention (unchanged from Stage 1C, made explicit here because VE is
no longer a single constant): sea level is z=0 in every part of this scene.
Near/low terrain (<=100 m real) is scaled up by VE so the near-flat plain
reads as relief; genuinely high or far things -- the camera's own altitude,
and Mount Ida beyond 300 m real -- sit in the SAME z-axis at their real
(VE=1) height. That is exactly what the taper formalises: ve(elev) -> 1.0
above 300 m, so Ida's horizon (all sampled >>300 m) and the camera (ALT=800,
used directly as world-z, never multiplied by any ve()) are already
consistent with the taper's own limit, not a special case bolted on.

Two defects this stage fixes that Stage 1C did not:
  1. THE SKY-RIVERS BUG (reported fixed in 1C's own draw_river docstring;
     measured still present in panorama-stage1c-terrain.png -- two blue
     lines cross the upper frame). Root cause, found by measuring the river
     source data: Scamander's polyline runs to 14.7 km forward of the
     viewpoint and Simoeis's to 13.1 km; 1C's draw_river only broke a
     segment when a point fell outside the trojan-plain DEM's ~24 km bbox,
     not outside the RENDERED grid (1C's own FORWARD_RANGE topped out at
     7.2 km). Points 7-15 km out still got a real elevation and a real
     camera projection -- perspective just does not guarantee "far and
     off-axis" lands off-SCREEN, and for these points it did not, producing
     two long connected chords across the sky where the far reaches of both
     rivers happened to project. Fix: draw_river now breaks the line
     wherever a point's OWN (forward, lateral) coordinates fall outside this
     stage's FORWARD_RANGE/LATERAL_RANGE, the same box the terrain grid
     itself is built on -- not just the DEM's much larger source bbox.
  2. Ida (68.7 km out) is real terrain nobody can grid at 60 m resolution
     over that distance. Drawn separately: a fan of bearings around the
     true bearing to Ida (117.6 deg absolute, +13.6 deg off heading) sampled
     against the TROAD sheet (zoom 11, ~183 m/px, covers Ida — trojan-plain's
     own grid does not reach that far east), at VE 1.0 (real elevation, no
     exaggeration -- see the world-z note), giving a real horizon silhouette
     rather than a hand-drawn bump. Projected with the SAME camera used for
     the near scene (real ALT, same forward/right/up/focal), so it sits at
     its true angular position; painted first, so nearer terrain correctly
     occludes it.

No city, no buildings, no camp, no ships, no labels -- terrain and water
only. The ten Stage-1B/1C diagnostic waypoint dots are kept.

Renders BOTH themes (light/dark) from shared/styles/global.css tokens.
No PIL/matplotlib in pipeline/.venv -- pixels composed with numpy, written as
a binary PPM, converted with macOS's `sips`.

Usage:
  python3 scripts/panorama-render-stage1d.py
    -> writes panorama-stage1d-terrain.png (light) and
       panorama-stage1d-terrain-dark.png (dark) at the repo root.
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
ptc = pp.ptc  # prep-terrain-contours.py, already loaded as a module by pp

# ── canvas ───────────────────────────────────────────────────────────────
W, H = 2400, 1350  # 16:9

# ── camera (settled by the Opus vantage lane; John: "use it exactly; do not
# re-derive") ───────────────────────────────────────────────────────────
VIEWPOINT = (39.9755, 26.1785)
HEADING_DEG = 104.0
HFOV_DEG = 72.0
ALT = 800.0
SETBACK = 1500.0

FORWARD_RANGE = (-1500.0, 9500.0)
LATERAL_RANGE = (-5800.0, 5800.0)
GRID_STEP = 60.0

NEAR_CLIP = 5.0  # metres

RAMP_STEPS = 12  # matches shared/lib/plate.ts RELIEF_RAMP_STEPS


def ve(elev):
    """Vertical-exaggeration factor: 4.0 at/under 100 m real, tapering
    linearly to 1.0 at 300 m, 1.0 above. Works on scalars and numpy arrays."""
    e = np.asarray(elev, dtype=np.float64)
    t = np.clip((e - 100.0) / 200.0, 0.0, 1.0)
    factor = 4.0 + t * (1.0 - 4.0)
    return factor if isinstance(elev, np.ndarray) else float(factor)


def exaggerate(elev):
    """elev * ve(elev), the world-z terrain uses."""
    e = np.asarray(elev, dtype=np.float64)
    out = e * ve(e)
    return out if isinstance(elev, np.ndarray) else float(out)


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ── theme palettes, copy-typed from shared/styles/global.css (unchanged
# from Stage 1C) plus a distance tone for Ida's silhouette, derived the same
# way: a step further along each theme's own relief ramp / sky tone rather
# than an invented colour, so the far ridge reads as "more of this sheet's
# own atmosphere," not a foreign asset. ──────────────────────────────────
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
        # Ida: a pale, low-contrast tint -- mostly sky, with a little of this
        # theme's OWN darkest relief band mixed in (not the contour token:
        # tried first at 78/22 with contour, and in the dark theme that
        # blends toward a bright warm tan against a near-black sky, reading
        # as a lit panel rather than a hazy silhouette -- the ramp's own
        # first band is closer in value to sky in both themes by
        # construction). 88/12 keeps it legible without competing with the
        # near relief ramp; the hairline crest carries the actual shape.
        distance=tuple(int(0.88 * a + 0.12 * b) for a, b in zip(_hex("#E7E7E9"), _hex("#AF9164"))),
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
        distance=tuple(int(0.88 * a + 0.12 * b) for a, b in zip(_hex("#181120"), _hex("#86734B"))),
        dot_outline=(237, 230, 232),   # ~ --text (dark, #EDE6E8)
        dot_viewpoint=(130, 170, 235),
        dot_troy=(230, 95, 85),
        dot_shore=(90, 190, 185),
        dot_waypoint=(235, 170, 80),
    ),
}


# ── data loaders (READ-ONLY) ────────────────────────────────────────────
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
    """Vectorised ray-casting point-in-polygon. poly_latlon: list of [lat,lon]."""
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


def build_scene(gr, viewpoint, heading_deg):
    theta = math.radians(heading_deg)
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
    """pts_world: Nx3 array of (east, north, world_z). Returns (px, py, depth)."""
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


def fill_quad_over_sky(img, pts, color, sky_color):
    """Like fill_quad, but only overwrites pixels still exactly the sky
    colour. Used for Ida's silhouette, which is painted AFTER the terrain
    (not before, see the render() note by its call site): the true empty
    sky at any given column is then already known -- whatever the terrain
    quads did not touch -- so this follows the near ridge's own irregular
    skyline exactly, by construction, rather than guessing a fixed offset
    or extent (the "floating rectangle" the first cut of this produced)."""
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(H - 1, int(math.ceil(max(ys))))
    n = len(pts)
    sky = np.array(sky_color, dtype=np.uint8)
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
                row = img[y, xa:xb + 1]
                mask = np.all(row == sky, axis=-1)
                row[mask] = color


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


def waypoint_targets():
    """Unchanged offsets from Stage 1B/1C: ~10 diagnostic points spread
    across the plain, mixing on-axis and off-axis so separation is visible.
    All fit comfortably inside this stage's wider FORWARD_RANGE."""
    return [
        (600, 0), (1600, 0), (2600, 0), (3600, 0), (4600, 0),
        (1100, 700), (2100, -700), (3100, 700), (4100, -700), (5100, 700),
    ]


# ── Ida horizon silhouette (real DEM, VE 1.0, sampled against the troad
# sheet since Ida sits far outside the trojan-plain bbox) ─────────────────
def build_ida_silhouette(camera, forward, right_v, up_v, focal, viewpoint):
    """A fan of bearings around the true bearing to Ida, each sampled out to
    85 km on the troad DEM (z11, ~183 m/px after its own blur+decimate --
    plenty for a silhouette 66+ km out) for the elevation ANGLE of its
    highest point (the horizon test: nearer high ground can occlude a
    farther peak, so the skyline is the running max of angle-with-distance,
    not the terrain height at a fixed range). Returns a list of (px, py) in
    screen space, one per bearing, real (VE=1) elevation throughout."""
    troad_grid, _ = ptc.build_sheet("troad", pp.CACHE)
    bearing_to_ida = pp._bearing_deg(viewpoint, pp.IDA_SUMMIT)
    # +-9 deg (the first cut) never left the summit's own shoulder -- angle
    # was still 0.3-0.4 deg at both edges (measured), so the silhouette cut
    # off in two vertical walls instead of tapering, which is what actually
    # produced the "floating rectangle" look, not the painting order. +-22
    # deg is wide enough to reach negative (below-horizon) angle on both
    # sides (measured: -0.14 deg at -25, -0.21 deg at +20), so the ridge
    # comes down to meet the true horizon at both ends instead of stopping
    # mid-slope.
    span = 22.0
    n_bearings = 89
    distances = np.arange(15_000.0, 95_000.0, 300.0)

    cam_e, cam_n, cam_z = camera
    pts = []
    for k in range(n_bearings):
        bearing = bearing_to_ida - span + (2 * span * k / (n_bearings - 1))
        theta = math.radians(bearing)
        best_angle = -1e9
        best_world = None
        for d in distances:
            lat, lon = pp._dest_point(viewpoint, bearing, d)
            if not (38.95 <= lat <= 40.6 and 25.35 <= lon <= 27.5):
                continue
            elev = pp.bilinear_elev(troad_grid, lat, lon)
            e, n = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
            angle = math.atan2(elev - cam_z, math.hypot(e - cam_e, n - cam_n))
            if angle > best_angle:
                best_angle = angle
                best_world = (e, n, elev)
        if best_world is not None:
            pts.append(best_world)

    if not pts:
        return []
    arr = np.array(pts)
    px, py, depth = project(camera, forward, right_v, up_v, focal, arr)
    out = [(float(x), float(y)) for x, y, d in zip(px, py, depth) if d > NEAR_CLIP]
    return out


def draw_ida(img, T, silhouette_px):
    """Fills the silhouette down to the bottom of the frame, but ONLY over
    pixels still exactly the sky colour (fill_quad_over_sky) -- which is why
    this is called AFTER the terrain quads are painted, not before. A first
    cut drew Ida first and extended its fill a fixed 80 px below its own
    line; wherever the near ridge's true skyline sat higher than that in
    screen space, the gap between the two showed as a flat-bottomed
    rectangle floating in open sky -- an artifact of the guessed offset, not
    of the geometry. Painting Ida second and clipping to "still sky" finds
    the real gap by construction, whatever its shape, with nothing left to
    guess. Restrained otherwise: one flat tint, one hairline -- the same
    engraved-tint register as the rest of the sheet, not a separate asset."""
    if len(silhouette_px) < 2:
        return
    pts = sorted(silhouette_px, key=lambda p: p[0])
    poly = pts + [(pts[-1][0], float(H)), (pts[0][0], float(H))]
    fill_quad_over_sky(img, poly, T["distance"], T["sky"])
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        draw_line(img, x0, y0, x1, y1, T["contour"], width=1, alpha=0.6)


def render(theme_name: str, out_path: str, verbose: bool = True):
    T = THEMES[theme_name]
    layers = _load_trojan_plain_layers()
    rivers = _load_rivers()
    lagoon_poly = layers["lagoon-bronze"]["polygon"]
    sea_poly = layers["sea-modern"]["polygon"]
    shore_bronze_pts = [p for ring in layers["shore-bronze"]["rings"] for p in ring]

    gr, stats, relief_stats = pp.load_plain_grid()
    viewpoint = VIEWPOINT
    heading = HEADING_DEG
    theta = math.radians(heading)

    fs, rs, east, north, elev, lat_g, lon_g = build_scene(gr, viewpoint, heading)

    # camera
    cam_e = -SETBACK * math.sin(theta)
    cam_n = -SETBACK * math.cos(theta)
    camera = np.array([cam_e, cam_n, ALT])

    # far target: straight ahead at FORWARD_RANGE's far edge -- generalises
    # Stage 1C's "bisect near/Troy" pitch now that Troy sits +7.7 deg off
    # the boresight rather than defining it.
    far_lat, far_lon = pp._dest_point(viewpoint, heading, FORWARD_RANGE[1])
    far_e, far_n = pp._flat_m((far_lat, far_lon), viewpoint[0], viewpoint[1])
    far_elev = pp.bilinear_elev(gr, far_lat, far_lon) if (39.86 <= far_lat <= 40.05 and 26.1 <= far_lon <= 26.38) else 0.0
    far_z = exaggerate(far_elev)

    view_elev = pp.bilinear_elev(gr, *viewpoint)
    view_z = exaggerate(view_elev)
    far_horiz = math.hypot(far_e - cam_e, far_n - cam_n)
    near_angle = math.atan2(ALT - view_z, SETBACK)
    far_angle = math.atan2(ALT - far_z, far_horiz)
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

    # Ida's screen position is independent of the terrain fill and can be
    # computed any time; the PAINT happens later (see the comment at that
    # call site) -- after the terrain quads, not before, so it can clip to
    # whatever sky the near ridge actually left open.
    ida_px = build_ida_silhouette(camera, forward, right_v, up_v, focal, viewpoint)

    # ── water classification (unchanged posture from Stage 1C) ──────────
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

    land_mask = valid & (water == 0)
    land_elevs = elev[land_mask]
    if land_elevs.size > 0:
        emin, emax = float(np.min(land_elevs)), float(np.max(land_elevs))
    else:
        emin, emax = 0.0, 1.0
    erange = max(emax - emin, 1e-6)

    world = np.stack([east, north, exaggerate(elev)], axis=-1)
    flat_world = world.reshape(-1, 3)
    px, py, depth = project(camera, forward, right_v, up_v, focal, flat_world)
    px = px.reshape(ni, nj)
    py = py.reshape(ni, nj)
    depth = depth.reshape(ni, nj)

    quads = []
    band_grid = np.full((ni - 1, nj - 1), -1, dtype=np.int16)
    class_grid = np.full((ni - 1, nj - 1), -1, dtype=np.int8)

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

    quads.sort(key=lambda q: -q[0])
    for _, pts, color in quads:
        fill_quad(img, pts, color)

    # Ida, now that the terrain has painted the real skyline: see the note
    # on draw_ida for why painting order matters here.
    draw_ida(img, T, ida_px)

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

    # contour hairlines: true isolines, RAMP_STEPS-1 thresholds
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

    # ── rivers: FIX (see module docstring #1) -- a segment now breaks not
    # only outside the DEM bbox but outside THIS RENDER'S OWN
    # FORWARD_RANGE/LATERAL_RANGE, so a point off the rendered ground can
    # never be chained into a chord across the sky. ─────────────────────
    f0, f1 = FORWARD_RANGE
    r0, r1 = LATERAL_RANGE

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
                prev = None
                continue
            e, n = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
            f = e * math.sin(theta) + n * math.cos(theta)
            r = e * math.sin(theta + math.pi / 2) + n * math.cos(theta + math.pi / 2)
            if not (f0 <= f <= f1 and r0 <= r <= r1):
                # off the rendered ground -- break rather than chain a
                # chord across the sky (the fix: see module docstring).
                prev = None
                continue
            elevv = pp.bilinear_elev(gr, lat, lon)
            wp = np.array([[e, n, exaggerate(elevv)]])
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

    # ── diagnostic dots ──────────────────────────────────────────────────
    dot_report = []

    def project_one(lat, lon, elev_m, label, color, radius):
        e, n = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
        wp = np.array([e, n, exaggerate(elev_m)])
        x, y, d = project(camera, forward, right_v, up_v, focal, wp.reshape(1, 3))
        x, y, d = float(x[0]), float(y[0]), float(d[0])
        onscreen = d > NEAR_CLIP and 0 <= x < W and 0 <= y < H
        if onscreen:
            draw_dot(img, x, y, radius, color, T["dot_outline"])
        dot_report.append((label, lat, lon, round(elev_m, 1), round(x, 1), round(y, 1), onscreen))
        return x, y, onscreen

    troy_elev = pp.bilinear_elev(gr, *pp.TROY)
    project_one(viewpoint[0], viewpoint[1], view_elev, "viewpoint", T["dot_viewpoint"], 8)
    project_one(pp.TROY[0], pp.TROY[1], troy_elev, "hisarlik", T["dot_troy"], 8)

    mid = pp._dest_point(viewpoint, heading, 3000.0)

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
    for k, (f, r) in enumerate(waypoint_targets()):
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
        bearing_troy = pp._bearing_deg(viewpoint, pp.TROY)
        bearing_rhoiteion = pp._bearing_deg(viewpoint, pp.RHOITEION)
        print(f"[{theme_name}] wrote {out_path}  (alt={ALT} m, setback={SETBACK} m, "
              f"hfov={HFOV_DEG} deg, heading={HEADING_DEG} deg, pitch={math.degrees(pitch):.1f} deg down)")
        print(f"  VE: 4.0x <=100m real, tapering to 1.0x at 300m [DISCLOSE]")
        print(f"  Troy relative bearing: {(bearing_troy - HEADING_DEG + 180) % 360 - 180:+.1f} deg   "
              f"Rhoiteion relative bearing: {(bearing_rhoiteion - HEADING_DEG + 180) % 360 - 180:+.1f} deg")
        print(f"  land elevation range in frame (band basis): {emin:.1f}-{emax:.1f} m "
              f"({RAMP_STEPS} bands, {erange/RAMP_STEPS:.2f} m/band)")
        print(f"  quads: {len(quads)}; ida silhouette points: {len(ida_px)}; "
              f"on-screen waypoints: {len(waypoint_px)}/10, min pairwise separation: "
              f"{min_sep:.1f} px" if min_sep is not None else "  n/a")
        for label, lat, lon, e, x, y, onscreen in dot_report:
            print(f"  {label:16s} lat={lat:.5f} lon={lon:.5f} elev={e:6.1f}m -> px=({x:7.1f},{y:7.1f}) "
                  f"{'ON' if onscreen else 'OFF'}-screen")
    return min_sep, len(waypoint_px)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-light", default=os.path.join(REPO, "panorama-stage1d-terrain.png"))
    ap.add_argument("--out-dark", default=os.path.join(REPO, "panorama-stage1d-terrain-dark.png"))
    args = ap.parse_args()
    render("light", args.out_light)
    print()
    render("dark", args.out_dark)


if __name__ == "__main__":
    main()
