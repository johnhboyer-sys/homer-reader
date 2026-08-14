#!/usr/bin/env python3
"""Sample a real DEM sightline for "The Plain of Troy from the Achaean Camp"
panorama — the checkpoint step of the panorama lane (see the brief in
docs/, and CLAUDE.md's "an accurate drawing of the wrong thing" / "a map
with no map under it" failure-mode entries: geography must come from real
data, never be hand-authored).

Reuses the grid-building machinery in prep-terrain-contours.py (tile decode,
mosaic, box-blur) by importing it as a module — adds no new dependency and
no new tile fetch: the trojan-plain z13 tiles are already cached under
build/terrain-tiles/ from that script's own prior run. This script is
READ-ONLY on that cache and on sources/terrain-tiles/; it writes only under
build/panorama/ (gitignored working directory) in this worktree.

Usage:
  python3 scripts/panorama-profile.py --verify      # control-point check
  python3 scripts/panorama-profile.py --profile      # sightline elevation profile -> build/panorama/sightline-profile.json
  python3 scripts/panorama-profile.py --fan          # 60 deg fan of bearings, for the horizon silhouette
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "build", "terrain-tiles")
OUT_DIR = os.path.join(REPO, "build", "panorama")

# ── Load prep-terrain-contours.py as a module (hyphenated filename, so
# regular `import` cannot name it) ──────────────────────────────────────────
_spec = importlib.util.spec_from_file_location(
    "prep_terrain_contours", os.path.join(REPO, "scripts", "prep-terrain-contours.py")
)
ptc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ptc)  # type: ignore[union-attr]


# ── Control points (measured/published, per sources/terrain-tiles/README.md
# and docs/TROY-MAPS-TODO.md) ───────────────────────────────────────────────
TROY = (39.957, 26.239)          # apparatus/places.json "troy"
SIGEION = (39.9835, 26.1809)     # apparatus/places.json "sigeion"; also
                                  # prep-terrain-contours.py's SIGEION_RIDGE
RHOITEION = (40.01, 26.303)      # apparatus/places.json "rhoiteion"
IDA_SUMMIT = (39.6995, 26.8653)  # prep-terrain-contours.py relief-ida anchor;
                                  # measured 1757.4 m there, published 1774 m


def _flat_m(p, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """[lat, lon] -> flat metres (east, north) from an origin. Equirectangular,
    matching prep-terrain-contours.py's own `_flat_m` convention — the sheet is
    ~24 km across, so a spherical formula would be false precision."""
    lat0 = math.radians(origin_lat)
    return (
        (p[1] - origin_lon) * 111320.0 * math.cos(lat0),
        (p[0] - origin_lat) * 111132.0,
    )


def _bearing_deg(a, b) -> float:
    """Compass bearing (0=N, 90=E) from point a to point b, flat-earth."""
    dx, dy = _flat_m(b, a[0], a[1])
    return math.degrees(math.atan2(dx, dy)) % 360.0


def _dest_point(origin, bearing_deg: float, dist_m: float) -> tuple[float, float]:
    """Point `dist_m` from `origin` along compass `bearing_deg`, flat-earth."""
    lat0 = math.radians(origin[0])
    theta = math.radians(bearing_deg)
    dx = dist_m * math.sin(theta)
    dy = dist_m * math.cos(theta)
    dlat = dy / 111132.0
    dlon = dx / (111320.0 * math.cos(lat0))
    return (origin[0] + dlat, origin[1] + dlon)


def bilinear_elev(g, lat: float, lon: float) -> float:
    """Bilinearly interpolated elevation at (lat, lon) on grid `g`. Inverts
    Grid.latlon's cell-centre formula (same inversion prep-terrain-contours.py's
    `_grid_elev` uses, but interpolated rather than nearest-cell — a sightline
    profile benefits from the smoother read)."""
    x, y = ptc.lonlat_to_px(lon, lat, g.z)
    fi = (x - g.x0) / g.step - 0.5
    fj = (y - g.y0) / g.step - 0.5
    i0 = max(0, min(g.w - 2, int(math.floor(fi))))
    j0 = max(0, min(g.h - 2, int(math.floor(fj))))
    tx = min(1.0, max(0.0, fi - i0))
    ty = min(1.0, max(0.0, fj - j0))
    a = g.at(i0, j0)
    b = g.at(i0 + 1, j0)
    c = g.at(i0, j0 + 1)
    d = g.at(i0 + 1, j0 + 1)
    top = a + (b - a) * tx
    bot = c + (d - c) * tx
    return top + (bot - top) * ty


def load_plain_grid():
    """The trojan-plain relief grid (post-blur), matching the smoothing the
    vendored sources/terrain-tiles/trojan-plain-contours.json and the
    README's own "elevation sanity check" table were measured on."""
    g, stats = ptc.build_sheet("trojan-plain", CACHE)
    gr, relief_stats = ptc.relief_grid("trojan-plain", g)
    return gr, stats, relief_stats


def cmd_verify(args):
    gr, stats, relief_stats = load_plain_grid()
    checks = [
        ("Hisarlik (Troy)", TROY, 36.1, "measured 36.1 m, README table; mound c.38 m"),
        ("Sigeion ridge crest", SIGEION, 36.0, "measured 36.0 m, README table; Cook \"30-40 m\""),
    ]
    print(f"grid: {gr.w}x{gr.h} @ z{gr.z}, step {gr.step}")
    print(f"relief_stats: {relief_stats}")
    for label, pt, published, note in checks:
        elev = bilinear_elev(gr, *pt)
        print(f"{label:28s} {pt}  sampled={elev:6.1f} m   published/README={published:6.1f} m   ({note})")

    # "ground rising to 58 m about 1.5 km east of it [Hisarlık]" (brief control
    # point) — scan a small fan east of Troy at ~1.5 km and report the max.
    print()
    print("scan ~1.5 km east of Troy (bearings 60-120 deg) for the 58 m control point:")
    best = None
    for bearing in range(60, 121, 5):
        for dist in (1200, 1350, 1500, 1650, 1800):
            pt = _dest_point(TROY, bearing, dist)
            if not (39.86 <= pt[0] <= 40.05 and 26.1 <= pt[1] <= 26.38):
                continue
            elev = bilinear_elev(gr, *pt)
            if best is None or elev > best[0]:
                best = (elev, bearing, dist, pt)
    if best:
        elev, bearing, dist, pt = best
        print(f"  max found: {elev:.1f} m at bearing {bearing} deg, {dist} m, {pt}")
    else:
        print("  no in-bbox samples")

    # Ida is far outside the trojan-plain bbox; report bearing/distance from
    # Sigeion so the panorama script can place it on the horizon without
    # fabricating a coordinate for the intervening ground.
    print()
    bda = _bearing_deg(SIGEION, IDA_SUMMIT)
    dxa, dya = _flat_m(IDA_SUMMIT, SIGEION[0], SIGEION[1])
    dist_ida = math.hypot(dxa, dya)
    print(f"Ida summit from Sigeion: bearing {bda:.1f} deg, distance {dist_ida/1000:.1f} km "
          f"(outside trojan-plain bbox; troad-contours.json z11 measured 1757.4 m there)")
    bdt = _bearing_deg(SIGEION, TROY)
    dxt, dyt = _flat_m(TROY, SIGEION[0], SIGEION[1])
    dist_troy = math.hypot(dxt, dyt)
    print(f"Troy from Sigeion:      bearing {bdt:.1f} deg, distance {dist_troy/1000:.2f} km")
    bdr = _bearing_deg(SIGEION, RHOITEION)
    print(f"Rhoiteion from Sigeion: bearing {bdr:.1f} deg")


def cmd_profile(args):
    """Sample the primary sightline: Sigeion (viewpoint) -> Troy -> beyond,
    every `step` metres out to `max_dist` metres, plus a spread of off-axis
    bearings for a proper horizon (not a single line)."""
    gr, stats, relief_stats = load_plain_grid()
    viewpoint = SIGEION
    bearing = _bearing_deg(SIGEION, TROY)
    step = 50.0
    max_dist = 6500.0

    samples = []
    d = 0.0
    while d <= max_dist:
        pt = _dest_point(viewpoint, bearing, d)
        elev = bilinear_elev(gr, *pt) if (39.86 <= pt[0] <= 40.05 and 26.1 <= pt[1] <= 26.38) else None
        samples.append({"dist_m": round(d, 1), "lat": round(pt[0], 5), "lon": round(pt[1], 5),
                         "elev_m": round(elev, 2) if elev is not None else None})
        d += step

    viewpoint_elev = bilinear_elev(gr, *viewpoint)
    out = {
        "sheet": "trojan-plain",
        "source": "AWS Open Data Terrain Tiles (Tilezen elevation-tiles-prod), terrarium PNG; SRTM over the Troad",
        "attribution": "SRTM data courtesy of the U.S. Geological Survey",
        "viewpoint": {"lat": viewpoint[0], "lon": viewpoint[1], "elev_m": round(viewpoint_elev, 2),
                       "note": "Sigeum ridge, the attested Achaean-camp zone per ruling 2e-iv "
                                "(Kraft, Rapp, Kayan & Luce 2003, after Luce 1998)."},
        "bearing_deg": round(bearing, 2),
        "step_m": step,
        "samples": samples,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "sightline-profile.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path} ({len(samples)} samples, bearing {bearing:.1f} deg, "
          f"viewpoint elev {viewpoint_elev:.1f} m)")


def cmd_fan(args):
    """A fan of parallel sightlines across a spread of bearings, for the
    horizon silhouette (ridge line as seen from the viewpoint, not just the
    single Troy bearing)."""
    gr, stats, relief_stats = load_plain_grid()
    viewpoint = SIGEION
    centre_bearing = _bearing_deg(SIGEION, TROY)
    span = 50.0  # degrees either side
    n_bearings = 41
    step = 60.0
    # 6000 m clipped several off-Troy bearings at the sampling ceiling (max
    # angle found exactly at d=6000 with a rising trend) -- extended to stay
    # inside the trojan-plain bbox (Sigeion sits ~13.7 km from the south edge,
    # ~17 km from the east edge) while giving those rays room to crest.
    max_dist = 12000.0

    fan = []
    for k in range(n_bearings):
        bearing = centre_bearing - span + (2 * span * k / (n_bearings - 1))
        profile = []
        d = step
        while d <= max_dist:
            pt = _dest_point(viewpoint, bearing, d)
            if not (39.86 <= pt[0] <= 40.05 and 26.1 <= pt[1] <= 26.38):
                d += step
                continue
            elev = bilinear_elev(gr, *pt)
            profile.append({"dist_m": round(d, 1), "elev_m": round(elev, 2)})
            d += step
        fan.append({"bearing_deg": round(bearing, 2), "profile": profile})

    viewpoint_elev = bilinear_elev(gr, *viewpoint)
    out = {
        "sheet": "trojan-plain",
        "viewpoint": {"lat": viewpoint[0], "lon": viewpoint[1], "elev_m": round(viewpoint_elev, 2)},
        "centre_bearing_deg": round(centre_bearing, 2),
        "span_deg": span,
        "fan": fan,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "sightline-fan.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path} ({len(fan)} bearings x up to {int(max_dist/step)} samples)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--profile", action="store_true")
    p.add_argument("--fan", action="store_true")
    args = p.parse_args()
    if args.verify:
        cmd_verify(args)
    if args.profile:
        cmd_profile(args)
    if args.fan:
        cmd_fan(args)
    if not (args.verify or args.profile or args.fan):
        p.print_help()


if __name__ == "__main__":
    main()
