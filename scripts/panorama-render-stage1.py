#!/usr/bin/env python3
"""Stage-1 checkpoint render: a BARE terrain silhouette for "The Plain of
Troy from the Achaean Camp" panorama. See docs/PANORAMA-RESUME.md.

Input: build/panorama/sightline-fan.json (written by
`panorama-profile.py --fan`) -- a real DEM fan, never hand-authored.

For each bearing this script takes the OCCLUSION-AWARE horizon: the sample
along that ray with the greatest apparent (angular) elevation as seen from
the viewpoint, atan2(elev - viewpoint_elev, dist). That is what an eye (or a
camera) actually sees -- a nearer lower rise can hide a farther higher one,
and vice versa; picking the literal max metres would ignore that.

No PIL/matplotlib in pipeline/.venv (stdlib + numpy only, per this
project's dependency rule) -- pixels are composed with numpy, written as a
binary PPM, and converted to PNG with macOS's built-in `sips` (a system
tool, not a project dependency).

Usage:
  python3 scripts/panorama-render-stage1.py
"""
from __future__ import annotations

import json
import math
import os
import subprocess

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAN_PATH = os.path.join(REPO, "build", "panorama", "sightline-fan.json")
OUT_PPM = os.path.join(REPO, "build", "panorama", "stage1-terrain.ppm")
OUT_PNG = os.path.join(REPO, "panorama-stage1-terrain.png")

# ── canvas ───────────────────────────────────────────────────────────────
W, H = 2400, 1000
MARGIN_L = 90
MARGIN_R = 40
MARGIN_T = 40
MARGIN_B = 40
PLOT_W = W - MARGIN_L - MARGIN_R
PLOT_H = H - MARGIN_T - MARGIN_B

FOV_DEG = 75.0  # rendered field of view (brief: "roughly 60-90 deg")

SKY = (238, 238, 235)
GROUND = (58, 56, 52)
LINE = (20, 19, 18)
GRID = (150, 148, 143)
TEXT = (40, 39, 37)


# ── tiny 3x5 bitmap font (digits, m, deg, minus, dot) for axis labels only
# -- content labels (place names) are explicitly out of scope for stage 1;
# this is just the "simple vertical scale" the brief asks for. ────────────
FONT = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "-": ["000", "000", "111", "000", "000"],
    ".": ["000", "000", "000", "000", "010"],
    "m": ["000", "111", "111", "101", "101"],
    "k": ["100", "101", "110", "101", "101"],
    "d": ["001", "001", "111", "101", "111"],
    "e": ["000", "111", "111", "100", "111"],
    "g": ["000", "111", "101", "111", "001"],
    " ": ["000", "000", "000", "000", "000"],
}


def draw_text(img: np.ndarray, x: int, y: int, s: str, color, scale: int = 3):
    """Blit `s` (top-left at x,y) using the 3x5 font, each cell `scale` px."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    y0 = y + row * scale
                    x0 = cx + col * scale
                    img[y0:y0 + scale, x0:x0 + scale] = color
        cx += 4 * scale  # 3 cols + 1 spacer


def main():
    with open(FAN_PATH) as f:
        d = json.load(f)
    viewpoint = d["viewpoint"]
    ve = viewpoint["elev_m"]
    cb = d["centre_bearing_deg"]
    raw_span = d["span_deg"]
    n_bearings_raw = len(d["fan"])
    step_deg = (2 * raw_span) / (n_bearings_raw - 1)

    half_fov = FOV_DEG / 2.0
    rows = []
    for entry in d["fan"]:
        b = entry["bearing_deg"]
        delta = ((b - cb + 180) % 360) - 180
        if abs(delta) > half_fov:
            continue
        best = None
        for s in entry["profile"]:
            ang = math.degrees(math.atan2(s["elev_m"] - ve, s["dist_m"]))
            if best is None or ang > best[0]:
                best = (ang, s["dist_m"], s["elev_m"])
        rows.append({"bearing": b, "delta": delta, "angle_deg": best[0],
                     "dist_m": best[1], "elev_m": best[2]})

    if len(rows) < 2:
        raise SystemExit(f"only {len(rows)} bearings fell inside +/-{half_fov} deg "
                          f"of centre {cb} -- fan span too narrow, aborting rather "
                          f"than hand-drawing a horizon")

    rows.sort(key=lambda r: r["delta"])
    angles = [r["angle_deg"] for r in rows]
    deltas = [r["delta"] for r in rows]
    at_ceiling = sum(1 for r in rows if r["dist_m"] >= 11940)

    ang_min, ang_max = min(angles), max(angles)
    pad = (ang_max - ang_min) * 0.25 or 0.1
    y_top_deg = ang_max + pad      # sky headroom
    y_bot_deg = ang_min - pad * 3  # ground shown filled below horizon anyway

    def deg_to_py(a: float) -> int:
        t = (y_top_deg - a) / (y_top_deg - y_bot_deg)
        return int(round(MARGIN_T + t * PLOT_H))

    def delta_to_px(dl: float) -> int:
        t = (dl + half_fov) / (2 * half_fov)
        return int(round(MARGIN_L + t * PLOT_W))

    # interpolate the horizon at every pixel column from the sampled bearings
    xs_sample = [delta_to_px(dl) for dl in deltas]
    horizon_px = np.interp(np.arange(W), xs_sample, [deg_to_py(a) for a in angles],
                            left=deg_to_py(angles[0]), right=deg_to_py(angles[-1]))

    img = np.empty((H, W, 3), dtype=np.uint8)
    img[:, :] = SKY
    # fill/horizon confined to the plot area only -- the sample-derived
    # curve does not extend into the axis-label margins, so nothing should
    # be drawn there (an earlier pass let np.interp's edge extrapolation
    # bleed a stray dark block behind the margin labels; fixed by clipping
    # the loop range).
    for x in range(MARGIN_L, W - MARGIN_R):
        yh = int(round(horizon_px[x]))
        yh = max(0, min(H - 1, yh))
        img[yh:H, x] = GROUND
    for x in range(MARGIN_L, W - MARGIN_R):
        yh = int(round(horizon_px[x]))
        img[max(0, yh - 1):yh + 1, x] = LINE

    # ── vertical scale: elevation gridlines, calibrated at Troy's own
    # sightline distance (5.76 km) for legibility -- an approximation
    # stated plainly, not a claim that every point on the curve sits at
    # that distance. Plus the exact eye-level (0 deg) line, no distance
    # approximation needed. Collect all label rows first and push apart
    # any that would collide (e.g. "40m" lands 0.047 deg from 0 deg at
    # this reference distance -- a coincidence of round numbers, not
    # geography -- so its label sits pixels away from "0deg" unless
    # separated). ────────────────────────────────────────────────────────
    ref_dist = 5760.0
    labels = [(deg_to_py(0.0), "0deg", True)]
    for elev_m in (0, 20, 40, 60, 80, 100, 120, 140):
        ang = math.degrees(math.atan2(elev_m - ve, ref_dist))
        if not (y_bot_deg <= ang <= y_top_deg):
            continue
        labels.append((deg_to_py(ang), f"{elev_m}m", False))

    # gridlines drawn at their true (uncollided) positions -- only the TEXT
    # is pushed apart, so the lines stay honest and only the labels move.
    for py, text, is_eye in labels:
        color = LINE if is_eye else GRID
        img[py:py + 1, MARGIN_L - 14:W - MARGIN_R] = color

    min_gap = 18  # px, >= glyph height (5*3=15) + breathing room
    labels.sort(key=lambda t: t[0])
    placed = []
    for py, text, is_eye in labels:
        ty = py - 8
        if placed and ty - placed[-1] < min_gap:
            ty = placed[-1] + min_gap
        placed.append(ty)
        draw_text(img, 10, ty, text, TEXT, scale=3)

    # frame
    img[MARGIN_T, MARGIN_L:W - MARGIN_R] = LINE
    img[H - MARGIN_B, MARGIN_L:W - MARGIN_R] = LINE
    img[MARGIN_T:H - MARGIN_B, MARGIN_L] = LINE
    img[MARGIN_T:H - MARGIN_B, W - MARGIN_R] = LINE

    os.makedirs(os.path.dirname(OUT_PPM), exist_ok=True)
    with open(OUT_PPM, "wb") as f:
        f.write(f"P6\n{W} {H}\n255\n".encode())
        f.write(img.tobytes())
    subprocess.run(["sips", "-s", "format", "png", OUT_PPM, "--out", OUT_PNG],
                    check=True, capture_output=True)

    print(f"wrote {OUT_PNG} ({W}x{H})")
    print(f"viewpoint: lat={viewpoint['lat']} lon={viewpoint['lon']} elev={ve} m")
    print(f"centre bearing {cb:.2f} deg, rendered FOV {FOV_DEG:.0f} deg "
          f"(sampled fan span {raw_span*2:.0f} deg, step {step_deg:.2f} deg, "
          f"{len(rows)} bearings used)")
    print(f"angle range shown: {ang_min:.3f} to {ang_max:.3f} deg "
          f"(~{y_bot_deg:.3f} to {y_top_deg:.3f} deg incl. padding)")
    print(f"bearings at the 12 km sampling ceiling: {at_ceiling} / {len(rows)}")
    for r in rows:
        flag = " CEILING" if r["dist_m"] >= 11940 else ""
        print(f"  bearing {r['bearing']:7.2f} (delta {r['delta']:+6.2f})  "
              f"angle {r['angle_deg']:+6.3f} deg  dist {r['dist_m']:6.0f} m  "
              f"elev {r['elev_m']:6.1f} m{flag}")


if __name__ == "__main__":
    main()
