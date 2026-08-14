#!/usr/bin/env python3
"""Stage-1B checkpoint render: a RAISED OBLIQUE bird's-eye of the plain of
Troy from behind the Achaean camp -- supersedes the eye-level Stage 1
(panorama-render-stage1.py). See docs/PANORAMA-RESUME.md and the Stage 1B
brief (worktree scratch).

Why raised oblique, not eye level: at eye level the whole plain compresses
into ~1 deg near the horizon (Troy subtends 0.19 deg at 5.76 km; the ridge
5-6 km behind it subtends up to 0.49 deg and dominates the skyline) -- no
room to place waypoint labels. Raising the camera a few hundred metres and
pulling it back opens the plain into a real 2-D surface on screen.

Reuses panorama-profile.py's DEM reading (load_plain_grid / bilinear_elev /
the flat-metre and bearing helpers) by importing it as a module -- this
script does no independent tile/DEM I/O. Samples a REGULAR GRID over the
plain (not a bearing fan) and projects it as a surface, because the point
of this stage is to see the ground open out, which a 1-D fan cannot show.

No PIL/matplotlib in pipeline/.venv (stdlib + numpy only) -- pixels are
composed with numpy, written as a binary PPM, converted to PNG with macOS's
`sips`, exactly as panorama-render-stage1.py does.

Usage:
  python3 scripts/panorama-render-stage1b.py --alt 500 --setback 900 --out panorama-stage1b-oblique.png
  python3 scripts/panorama-render-stage1b.py --all-tests   # renders the 3 combos tried for the brief
"""
from __future__ import annotations

import argparse
import importlib.util
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

SKY = (234, 233, 227)
GROUND_A = (211, 202, 183)
GROUND_B = (200, 191, 172)
DOT_OUTLINE = (25, 24, 22)
DOT_VIEWPOINT = (45, 85, 165)
DOT_TROY = (175, 35, 30)
DOT_SHORE = (30, 120, 118)
DOT_WAYPOINT = (205, 120, 20)

# vertical exaggeration -- disclosed factor (brief: 1.5-2x, standard
# panorama practice, applied uniformly to the whole scene's z axis so the
# camera/target geometry stays self-consistent)
VE = 1.75

# terrain sampling grid, in metres along (forward = bearing to Troy,
# right = perpendicular) axes from the viewpoint
FORWARD_RANGE = (-900.0, 7200.0)
LATERAL_RANGE = (-3200.0, 3200.0)
GRID_STEP = 160.0

NEAR_CLIP = 5.0  # metres; points/quads closer than this to the camera plane are dropped


def _coastline_points():
    import json
    path = os.path.join(REPO, "sources", "copernicus-dem", "trojan-plain-coastline.json")
    with open(path) as f:
        d = json.load(f)
    pts = []
    for feat in d["features"]:
        if feat["id"] == "coast-modern":
            pts.extend(feat["points"])
    return pts


def build_scene(gr, viewpoint, bearing_deg):
    """Regular grid of (lat, lon, elev) over the plain, in forward/lateral
    metres from the viewpoint. Returns elev[i][j] (None where outside the
    trojan-plain bbox) and the coordinate arrays."""
    theta = math.radians(bearing_deg)
    fwd = (math.sin(theta), math.cos(theta))         # (east, north) per metre forward
    right = (math.sin(theta + math.pi / 2), math.cos(theta + math.pi / 2))
    lat0 = math.radians(viewpoint[0])

    f0, f1 = FORWARD_RANGE
    r0, r1 = LATERAL_RANGE
    fs = np.arange(f0, f1 + GRID_STEP / 2, GRID_STEP)
    rs = np.arange(r0, r1 + GRID_STEP / 2, GRID_STEP)

    elev = np.full((len(fs), len(rs)), np.nan, dtype=np.float64)
    east = np.zeros_like(elev)
    north = np.zeros_like(elev)
    for i, f in enumerate(fs):
        for j, r in enumerate(rs):
            e = f * fwd[0] + r * right[0]
            n = f * fwd[1] + r * right[1]
            east[i, j] = e
            north[i, j] = n
            lat = viewpoint[0] + n / 111132.0
            lon = viewpoint[1] + e / (111320.0 * math.cos(lat0))
            if 39.86 <= lat <= 40.05 and 26.1 <= lon <= 26.38:
                elev[i, j] = pp.bilinear_elev(gr, lat, lon)
    return fs, rs, east, north, elev


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


def draw_dot(img, x, y, r, color):
    if not (0 <= x < W and 0 <= y < H):
        return
    xi, yi = int(round(x)), int(round(y))
    for dy in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            if dx * dx + dy * dy <= (r + 1) ** 2:
                yy, xx = yi + dy, xi + dx
                if 0 <= xx < W and 0 <= yy < H:
                    d2 = dx * dx + dy * dy
                    img[yy, xx] = color if d2 <= r * r else DOT_OUTLINE


def waypoint_targets(bearing_deg):
    """~10 diagnostic points spread across the plain between camp and Troy,
    roughly 1 km spacing, mixing on-axis and off-axis so 2-D separation is
    visible, not just along-track."""
    return [
        (600, 0), (1600, 0), (2600, 0), (3600, 0), (4600, 0),
        (1100, 700), (2100, -700), (3100, 700), (4100, -700), (5100, 700),
    ]


def render(alt: float, setback: float, hfov_deg: float, out_path: str, verbose: bool = True):
    gr, stats, relief_stats = pp.load_plain_grid()
    viewpoint = pp.SIGEION
    bearing = pp._bearing_deg(pp.SIGEION, pp.TROY)
    theta = math.radians(bearing)
    fwd_hat = np.array([math.sin(theta), math.cos(theta), 0.0])

    fs, rs, east, north, elev = build_scene(gr, viewpoint, bearing)

    # camera: `setback` metres behind the viewpoint along the reverse
    # bearing, at absolute altitude `alt` (metres, sea-level frame -- not
    # itself vertically exaggerated; it is an artistic placement, not a
    # measured terrain height)
    cam_e = -setback * math.sin(theta)
    cam_n = -setback * math.cos(theta)
    camera = np.array([cam_e, cam_n, alt])

    troy_e, troy_n = pp._flat_m(pp.TROY, viewpoint[0], viewpoint[1])
    troy_elev = pp.bilinear_elev(gr, *pp.TROY)
    target = np.array([troy_e, troy_n, troy_elev * VE])

    # Pitch: boresighting straight at Troy gives too shallow a downward
    # tilt to also fit the near foreground (the camp, directly below and
    # behind the camera) in frame -- Troy sits only ~4 deg below horizontal
    # from a few-hundred-metre camera at this range, while the ground under
    # the camera itself sits 20-30 deg below. Bisect the two so both the
    # near field and Hisarlik land inside the vertical FOV; the heading
    # (bearing) stays exactly on the Sigeion-Troy axis either way.
    view_z = pp.bilinear_elev(gr, *viewpoint) * VE
    troy_horiz = math.hypot(troy_e - cam_e, troy_n - cam_n)
    near_angle = math.atan2(alt - view_z, setback)       # rad, positive = down
    far_angle = math.atan2(alt - target[2], troy_horiz)  # rad, positive = down
    pitch = (near_angle + far_angle) / 2.0

    forward = np.array([math.sin(theta) * math.cos(pitch),
                         math.cos(theta) * math.cos(pitch),
                         -math.sin(pitch)])
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0])
    right_v = np.cross(forward, world_up)
    right_v = right_v / np.linalg.norm(right_v)
    up_v = np.cross(right_v, forward)

    focal = (W / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)

    img = np.empty((H, W, 3), dtype=np.uint8)
    img[:, :] = SKY

    # build world points and project the whole grid at once
    ni, nj = elev.shape
    world = np.stack([east, north, elev * VE], axis=-1)  # ni x nj x 3
    flat_world = world.reshape(-1, 3)
    px, py, depth = project(camera, forward, right_v, up_v, focal, flat_world)
    px = px.reshape(ni, nj)
    py = py.reshape(ni, nj)
    depth = depth.reshape(ni, nj)
    valid = ~np.isnan(elev)

    quads = []
    for i in range(ni - 1):
        for j in range(nj - 1):
            if not (valid[i, j] and valid[i + 1, j] and valid[i + 1, j + 1] and valid[i, j + 1]):
                continue
            d = (depth[i, j], depth[i + 1, j], depth[i + 1, j + 1], depth[i, j + 1])
            if min(d) <= NEAR_CLIP:
                continue
            pts = [(px[i, j], py[i, j]), (px[i + 1, j], py[i + 1, j]),
                   (px[i + 1, j + 1], py[i + 1, j + 1]), (px[i, j + 1], py[i, j + 1])]
            avg_depth = sum(d) / 4.0
            color = GROUND_A if (i + j) % 2 == 0 else GROUND_B
            quads.append((avg_depth, pts, color))

    quads.sort(key=lambda q: -q[0])  # far first, near last (painter's algorithm)
    for _, pts, color in quads:
        fill_quad(img, pts, color)

    # ── diagnostic dots ──────────────────────────────────────────────────
    dot_report = []

    def project_one(lat, lon, elev_m, label, color, radius):
        e, n = pp._flat_m((lat, lon), viewpoint[0], viewpoint[1])
        wp = np.array([e, n, elev_m * VE])
        x, y, d = project(camera, forward, right_v, up_v, focal, wp.reshape(1, 3))
        x, y, d = float(x[0]), float(y[0]), float(d[0])
        onscreen = d > NEAR_CLIP and 0 <= x < W and 0 <= y < H
        if onscreen:
            draw_dot(img, x, y, radius, color)
        dot_report.append((label, lat, lon, round(elev_m, 1), round(x, 1), round(y, 1), onscreen))
        return x, y, onscreen

    project_one(viewpoint[0], viewpoint[1], pp.bilinear_elev(gr, *viewpoint), "viewpoint", DOT_VIEWPOINT, 8)
    project_one(pp.TROY[0], pp.TROY[1], troy_elev, "hisarlik", DOT_TROY, 8)

    coast = _coastline_points()
    # nearest coastline point to the viewpoint, and nearest to a point 3 km
    # along-bearing (representative of the shore flanking the plain)
    mid = pp._dest_point(viewpoint, bearing, 3000.0)

    def nearest(pt):
        best, bd = None, None
        for c in coast:
            dx, dy = pp._flat_m(c, pt[0], pt[1])
            dd = dx * dx + dy * dy
            if bd is None or dd < bd:
                bd, best = dd, c
        return best

    for label, anchor in (("shore_near_camp", viewpoint), ("shore_mid_bay", mid)):
        c = nearest(anchor)
        e2, n2 = pp._flat_m(c, viewpoint[0], viewpoint[1])
        lat_c, lon_c = c
        elev_c = 0.0  # coastline == sea level by construction
        if 39.86 <= lat_c <= 40.05 and 26.1 <= lon_c <= 26.38:
            elev_c = max(0.0, pp.bilinear_elev(gr, lat_c, lon_c))
        project_one(lat_c, lon_c, elev_c, label, DOT_SHORE, 7)

    waypoint_px = []
    for k, (f, r) in enumerate(waypoint_targets(bearing)):
        e = f * math.sin(theta) + r * math.sin(theta + math.pi / 2)
        n = f * math.cos(theta) + r * math.cos(theta + math.pi / 2)
        lat = viewpoint[0] + n / 111132.0
        lon = viewpoint[1] + e / (111320.0 * math.cos(math.radians(viewpoint[0])))
        wev = pp.bilinear_elev(gr, lat, lon) if (39.86 <= lat <= 40.05 and 26.1 <= lon <= 26.38) else 0.0
        x, y, onscreen = project_one(lat, lon, wev, f"waypoint_{k}", DOT_WAYPOINT, 6)
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

    # minimum pairwise pixel separation among on-screen waypoint dots
    min_sep = None
    for i in range(len(waypoint_px)):
        for j in range(i + 1, len(waypoint_px)):
            dx = waypoint_px[i][0] - waypoint_px[j][0]
            dy = waypoint_px[i][1] - waypoint_px[j][1]
            dist = math.hypot(dx, dy)
            if min_sep is None or dist < min_sep:
                min_sep = dist

    vfov_deg = 2 * math.degrees(math.atan((H / 2.0) / focal))
    if verbose:
        print(f"wrote {out_path}  (alt={alt} m, setback={setback} m, hfov={hfov_deg} deg, "
              f"vfov={vfov_deg:.1f} deg, VE={VE}x)")
        print(f"bearing {bearing:.2f} deg, viewpoint elev {pp.bilinear_elev(gr, *viewpoint):.1f} m, "
              f"Troy elev {troy_elev:.1f} m, dist {np.linalg.norm(target[:2]-camera[:2]):.0f} m (camera-to-Troy, xy)")
        print(f"pitch {math.degrees(pitch):.1f} deg down; near-field angle "
              f"{math.degrees(near_angle):.1f} deg down, Troy angle {math.degrees(far_angle):.1f} deg down "
              f"(need half-vfov >= {(math.degrees(near_angle)-math.degrees(far_angle))/2:.1f} deg)")
        print(f"quads drawn: {len(quads)} / {(ni-1)*(nj-1)} grid cells")
        print(f"on-screen waypoints: {len(waypoint_px)} / 10, min pairwise pixel separation: "
              f"{min_sep:.1f} px" if min_sep is not None else "n/a")
        for label, lat, lon, e, x, y, onscreen in dot_report:
            print(f"  {label:16s} lat={lat:.5f} lon={lon:.5f} elev={e:6.1f}m -> px=({x:7.1f},{y:7.1f}) "
                  f"{'ON' if onscreen else 'OFF'}-screen")
    return min_sep, len(waypoint_px)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alt", type=float, default=500.0)
    ap.add_argument("--setback", type=float, default=900.0)
    ap.add_argument("--hfov", type=float, default=60.0)
    ap.add_argument("--out", default=os.path.join(REPO, "panorama-stage1b-oblique.png"))
    ap.add_argument("--all-tests", action="store_true",
                     help="render the 3 combos tried for the brief into build/panorama/")
    args = ap.parse_args()

    if args.all_tests:
        combos = [
            ("A", 300.0, 500.0, 60.0),
            ("B", 500.0, 900.0, 60.0),
            ("C", 800.0, 1500.0, 55.0),
        ]
        for name, alt, setback, hfov in combos:
            out = os.path.join(REPO, "build", "panorama", f"stage1b-test-{name}.png")
            print(f"\n=== combo {name}: alt={alt} setback={setback} hfov={hfov} ===")
            render(alt, setback, hfov, out)
    else:
        render(args.alt, args.setback, args.hfov, args.out)


if __name__ == "__main__":
    main()
