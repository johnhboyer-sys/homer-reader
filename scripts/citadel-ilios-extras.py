#!/usr/bin/env python3
# Generates the citadel panels' mound top, scrub and the poem's two trees from Dörpfeld's circuit (the plate itself) and the SRTM terrain tiles.
"""Scrub on the steep open slopes of the Ilios window, the poem's two trees,
and the mound top under the Pergamos circuit. Prints a JSON list of layers.
Usage (from the repo root):
  python3 scripts/citadel-ilios-extras.py . > /tmp/extras.json
  python3 scripts/splice-plate-layers.py apparatus/plates/trojan-plain-schematic.json /tmp/extras.json --before wagon-road"""
import importlib.util, json, math, os, sys
from array import array

REPO = sys.argv[1]
spec = importlib.util.spec_from_file_location("ptc", f"{REPO}/scripts/prep-terrain-contours.py")
ptc = importlib.util.module_from_spec(spec); spec.loader.exec_module(ptc)
plate = json.load(open(f"{REPO}/apparatus/plates/trojan-plain-schematic.json"))
L = {l["id"]: l for l in plate["layers"]}
places = {p["id"]: p for p in json.load(open(f"{REPO}/apparatus/places.json"))["places"]}

ILIOS = (39.95162, 26.23381, 39.96117, 26.24419)
M_LAT = 111320.0
M_LON = 111320.0 * math.cos(math.radians(39.957))

def chaikin(ring, n=2):
    """Corner-cutting: rounds the cell-sized steps a traced grid leaves."""
    for _ in range(n):
        out = []
        for a, b in zip(ring, ring[1:] + ring[:1]):
            out.append([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]])
            out.append([0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]])
        ring = out
    return ring

def to_m(p):  # local metres, x east, y north
    return ((p[1] - 26.239) * M_LON, (p[0] - 39.957) * M_LAT)
def to_ll(x, y):
    return [round(39.957 + y / M_LAT, 6), round(26.239 + x / M_LON, 6)]

def hull(pts):
    pts = sorted(set(pts))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def verts(l):
    for k in ("polygon", "trace", "path"):
        for p in l.get(k) or []: yield p
    for r in l.get("rings") or []:
        for p in r: yield p

# ── The mound top: the hull of the Troy VI circuit, surveyed and restored ──
circuit_ids = ["citadel-circuit-west", "citadel-circuit-south", "citadel-circuit-southeast-east",
               "citadel-circuit-northeast", "citadel-circuit-restored"]
circ = [to_m(p) for i in circuit_ids for p in verts(L[i])]
# The mound's edge is the circuit's OUTER face, not its convex hull (a hull
# bridges the recesses between towers with straight lines that stand off the
# wall). Rasterise the circuit at 0.5 m -- masonry polygons filled, the
# restored stretch as a band of its drawn width -- close the gaps between
# pieces, fill the inside, and trace the outline.
RES = 0.5
xs = [p[0] for p in circ]; ys = [p[1] for p in circ]
ox, oy = min(xs) - 20, min(ys) - 20
W = int((max(xs) - ox + 20) / RES); H = int((max(ys) - oy + 20) / RES)
grid = bytearray(W * H)
def paint_poly(poly):
    for j in range(H):
        y = oy + (j + 0.5) * RES
        cuts = []
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if (y1 > y) != (y2 > y): cuts.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        cuts.sort()
        for a, b in zip(cuts[::2], cuts[1::2]):
            for i in range(max(0, int((a - ox) / RES)), min(W, int((b - ox) / RES) + 1)): grid[j * W + i] = 1
def paint_disc(cx, cy, r):
    for j in range(max(0, int((cy - r - oy) / RES)), min(H, int((cy + r - oy) / RES) + 1)):
        for i in range(max(0, int((cx - r - ox) / RES)), min(W, int((cx + r - ox) / RES) + 1)):
            if (ox + (i + .5) * RES - cx) ** 2 + (oy + (j + .5) * RES - cy) ** 2 <= r * r: grid[j * W + i] = 1
for i in circuit_ids[:-1]:
    paint_poly([to_m(p) for p in L[i]["polygon"]])
tr = [to_m(p) for p in L["citadel-circuit-restored"]["trace"]]
for (x1, y1), (x2, y2) in zip(tr, tr[1:]):
    n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.5))
    for k in range(n + 1): paint_disc(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n, 2.5)
def morph(g, r, val):
    out = bytearray(g)
    k = int(r / RES)
    offs = [(di, dj) for di in range(-k, k + 1) for dj in range(-k, k + 1) if di * di + dj * dj <= k * k]
    for j in range(H):
        for i in range(W):
            if g[j * W + i] == val: continue
            for di, dj in offs:
                ii, jj = i + di, j + dj
                if 0 <= ii < W and 0 <= jj < H and g[jj * W + ii] == val:
                    out[j * W + i] = val; break
    return out
grid = morph(grid, 6.0, 1)          # close gaps between wall pieces...
grid = morph(grid, 6.0, 0)          # ...and give the width back
# flood the outside from the frame; everything not reached is the mound
outside = bytearray(W * H); stack = [(0, 0)]
while stack:
    i, j = stack.pop()
    if not (0 <= i < W and 0 <= j < H) or outside[j * W + i] or grid[j * W + i]: continue
    outside[j * W + i] = 1
    stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
from array import array as _arr
mg = _arr("f", [0.0 if outside[k] else 1.0 for k in range(W * H)])
class G: pass
gg = G(); gg.w, gg.h, gg.data = W, H, mg
gg.at = lambda i, j: mg[j * W + i]
lines = ptc.trace_contour(gg, 0.5)
ring = max(lines, key=len)
pts = [(ox + (fi + 0.5) * RES, oy + (fj + 0.5) * RES) for fi, fj in ring]
pts = ptc.douglas_peucker([list(p) for p in pts], 0.4)
mound = [to_ll(x, y) for x, y in pts[:-1]]

# ── Scrub: steep cells of the DEM, clear of the built city ──
g = ptc.build_grid(15, (ILIOS[0] - 0.001, ILIOS[1] - 0.001, ILIOS[2] + 0.001, ILIOS[3] + 0.001), os.path.join(REPO, "build", "terrain-tiles"), verbose=False)
g = ptc.box_blur(g, 4)
slope = ptc.slope_grid(g, 39.957)
built = [to_m(p) for p in verts(L["ilios-lower-city"])] + circ
bh = hull(built)
def inside(poly, x, y):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
def dist_poly(poly, x, y):
    best = 1e9
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return best
THRESH = 0.09     # rise over run: the scarps, not the plateau
CLEAR = 25.0      # metres kept clear of the city's outer edge
mask = array("f", [0.0] * (g.w * g.h))
for j in range(g.h):
    for i in range(g.w):
        la, lo = g.latlon(i, j)
        x, y = to_m((la, lo))
        if slope[j * g.w + i] < THRESH: continue
        if inside(bh, x, y) or dist_poly(bh, x, y) < CLEAR: continue
        mask[j * g.w + i] = 1.0
mg = ptc.Grid(g.z, g.x0, g.y0, g.w, g.h, g.step, ptc.box_blur(ptc.Grid(g.z, g.x0, g.y0, g.w, g.h, g.step, mask), 2).data)
# pad with a zero moat so every ring closes
w, h = mg.w + 2, mg.h + 2
pd = array("f", [0.0] * (w * h))
for j in range(mg.h):
    for i in range(mg.w):
        pd[(j + 1) * w + i + 1] = mg.at(i, j)
pg = ptc.Grid(mg.z, mg.x0 - 1, mg.y0 - 1, w, h, mg.step, pd)
rings = []
for line in ptc.join_runs([[list(pg.latlon(fi, fj)) for fi, fj in l] for l in ptc.trace_contour(pg, 0.5)], 0.0):
    if line[0] != line[-1] or len(line) < 6: continue
    simp = ptc.douglas_peucker(line, 0.00003)
    xs = [to_m(p) for p in simp]
    a = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(xs, xs[1:] + xs[:1]))) / 2
    if a < 1500: continue  # specks under ~40 m square
    rings.append([[round(p[0], 6), round(p[1], 6)] for p in chaikin([list(q) for q in simp[:-1]], 3)])
rings.sort(key=lambda r: -len(r))
print(f"scrub: {len(rings)} rings", file=sys.stderr)

def circle(c, r_m, n=9):
    x, y = to_m(c)
    return [to_ll(x + r_m * math.cos(2 * math.pi * k / n), y + r_m * math.sin(2 * math.pi * k / n)) for k in range(n)]

GROUND_SRC = L["relief-band-0030"]["sources"]
out = [
    {
        "id": "pergamos-mound-top",
        "kind": "relief",
        "elevation": 30,
        "insetOf": ["citadel-city-panel", "citadel-inset-panel"],
        "insetOnly": True,
        "polygon": mound,
        "note": ("The top of the citadel mound, inside the Troy VI circuit: above 30 m (the elevation data puts the "
                 "inside of the circuit at 36–38 m). Drawn as the hull of Dörpfeld's surveyed circuit and its "
                 "restoration rather than from the 30 m contour itself, because at this scale the smoothed 30 m "
                 "grid runs the contour inside the north-west wall, where the citadel stands at the edge of a scarp."),
        "sources": GROUND_SRC,
    },
    {
        "id": "ilios-scrub",
        "kind": "region",
        "style": "scrub",
        "fill": "none",
        "insetOf": ["citadel-inset-panel"],
        "insetOnly": True,
        "spacingM": 9,
        "polygon": rings[0],
        "rings": rings[1:],
        "note": ("Scrub on the steep open slopes below the citadel and the city: ground where the elevation data "
                 "falls more than about 1 m in 11, clear of the walls and the built city. No pollen core or plant "
                 "survey covers Bronze Age Troy; thin soil on exposed slopes at this latitude defaults to low scrub "
                 "or bare rock, and that default, not a finding, is what is drawn. The poem names no growth on the "
                 "slopes. See docs/research/GROUND-COVER-TROJAN-PLAIN.md §2.4."),
        "sources": GROUND_SRC,
    },
]
for pid, tid, r, note in [
    ("oak-of-zeus", "ilios-tree-oak", 15,
     "The oak of Zeus (φηγός), at the Scaean gates (Il. 6.237, 9.354, 11.170). Drawn as a single tree at "
     "the oak's place on this sheet; the poem gives its place by the gate and nothing of its size."),
    ("fig-tree", "ilios-tree-fig", 11,
     "The wild fig (ἐρινεός), by the wall where it is most open to assault (Il. 6.433–34, 22.145); the fig at 11.167 is another, out in the mid-plain. Drawn "
     "as a single tree at the fig's place on this sheet; the poem gives nothing of its size."),
]:
    c = places[pid]["plateAnchors"]["trojan-plain-schematic"]
    out.append({
        "id": tid, "kind": "region", "style": "tree", "fill": "none",
        "insetOf": ["citadel-inset-panel"], "insetOnly": True,
        "certainty": "speculative",
        "polygon": circle(c, r),
        "note": note,
        "sources": L["citadel-poem-house-of-priam"]["sources"][:1],
    })
json.dump(out, sys.stdout, ensure_ascii=False)
