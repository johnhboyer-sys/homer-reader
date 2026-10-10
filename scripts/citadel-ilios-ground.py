#!/usr/bin/env python3
# Generates the citadel panels' elevation bands (ilios-ground-*) from the SRTM terrain tiles (AWS Terrain Tiles, terrarium).
"""The Ilios window's own ground: elevation bands traced at the citadel
panels' scale from the same SRTM terrain tiles the sheet's face is cut from,
at the face's own contour levels (so a band means the same tint in a panel as
on the face). Prints a JSON list of layers on stdout.

Usage (from the repo root, Node-free; tiles are fetched once into build/terrain-tiles):
  python3 scripts/citadel-ilios-ground.py . > /tmp/ground.json
  python3 scripts/splice-plate-layers.py apparatus/plates/trojan-plain-schematic.json /tmp/ground.json --before wagon-road
"""
import importlib.util, json, math, os, sys
from array import array

REPO = sys.argv[1]
spec = importlib.util.spec_from_file_location("ptc", f"{REPO}/scripts/prep-terrain-contours.py")
ptc = importlib.util.module_from_spec(spec); spec.loader.exec_module(ptc)

ILIOS = (39.95162, 26.23381, 39.96117, 26.24419)   # citadel-inset-panel insetBBox
PAD = 0.0025                                         # ~250 m beyond the window
LEVELS = [10, 15, 20, 25, 30, 40]                    # the face's levels at Troy
Z = 15
BLUR = 4
TOL = 0.00003                                        # ~3 m simplification

PLATE = json.load(open(os.path.join(REPO, "apparatus", "plates", "trojan-plain-schematic.json")))
FACE_SOURCES = next(l for l in PLATE["layers"] if l["id"] == "relief-band-0030")["sources"]

bbox = (ILIOS[0] - PAD, ILIOS[1] - PAD, ILIOS[2] + PAD, ILIOS[3] + PAD)
g = ptc.build_grid(Z, bbox, os.path.join(REPO, "build", "terrain-tiles"), verbose=False)
g = ptc.box_blur(g, BLUR)
# A one-cell moat far below every level, so every contour closes inside the
# grid; the renderer's window clip trims what runs past the panel.
w, h = g.w + 2, g.h + 2
data = array("f", [-1000.0] * (w * h))
for j in range(g.h):
    for i in range(g.w):
        data[(j + 1) * w + i + 1] = g.at(i, j)
padded = ptc.Grid(g.z, g.x0 - 1, g.y0 - 1, w, h, g.step, data)

def chaikin(ring, n=2):
    """Corner-cutting: rounds the cell-sized steps a traced grid leaves."""
    for _ in range(n):
        out = []
        for a, b in zip(ring, ring[1:] + ring[:1]):
            out.append([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]])
            out.append([0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]])
        ring = out
    return ring

def signed_area(r):
    return sum(a[1] * b[0] - b[1] * a[0] for a, b in zip(r, r[1:] + r[:1])) / 2

layers = []
for level in LEVELS:
    rings = []
    for line in ptc.join_runs([[list(padded.latlon(fi, fj)) for fi, fj in l] for l in ptc.trace_contour(padded, level)], 0.0):
        if line[0] != line[-1] or len(line) < 4:
            continue
        simp = ptc.douglas_peucker(line, TOL)
        if len({tuple(p) for p in simp}) < 3:
            continue
        rings.append([[round(a, 6), round(b, 6)] for a, b in chaikin([list(p) for p in simp[:-1]])])
    # Orientation: a body (higher ground inside) and a basin (lower inside)
    # must wind opposite ways for the band's nonzero fill to leave the basin
    # open. Decide by sampling the grid just inside each ring's first edge.
    out = []
    for r in rings:
        frac, _ = ptc._interior_above(r + [r[0]], padded, level)
        body = frac >= 0.5
        a = signed_area(r)
        if (a > 0) != body:
            r = r[::-1]
        out.append(r)
    if not out:
        continue
    layers.append({
        "id": f"ilios-ground-{level:04d}",
        "kind": "relief",
        "elevation": level,
        "insetOf": ["citadel-inset-panel", "citadel-city-panel"],
        "insetOnly": True,
        "rings": out,
        "note": (f"Ground above {level} m inside the two citadel panels, traced from the same SRTM "
                 f"terrain tiles as the sheet's own relief (zoom {Z}, {BLUR} blur passes) at the "
                 f"sheet's own contour levels, so its tint means what the face's does. The modern "
                 f"surface: the excavated mound, and a plain that has since built up over its Bronze "
                 f"Age surface (RESEARCH-PALEOGEOGRAPHY.md, the Kraft–Kayan sections)."),
        # The face's own terrain citation, so the two can never disagree.
        "sources": FACE_SOURCES,
    })
    print(f"level {level}: {len(out)} rings, {sum(len(r) for r in out)} vertices", file=sys.stderr)
json.dump(layers, sys.stdout, ensure_ascii=False)
