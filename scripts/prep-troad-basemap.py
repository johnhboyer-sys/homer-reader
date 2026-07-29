#!/usr/bin/env python3
"""Build the coastlines, islands and rivers of the two Troad map plates from
real survey data.

WHY THIS EXISTS. `apparatus/plates/trojan-plain.json` and `troad.json` used to
carry hand-typed coordinate arrays -- 5 to 17 vertices a feature. Hand-typed
coordinates cannot make a map: ten times as many of them is a smoother blob,
not the Troad. This script replaces that geometry with measurements. Nothing
it emits is authored by hand; every vertex comes from one of the two sources
below, generalised for the sheet it is drawn on.

SOURCES AND LICENCES
--------------------

1. COASTLINE AND ISLANDS -- Copernicus DEM GLO-30 Water Body Mask, from the
   AWS Open Data registry, no credentials:
       https://copernicus-dem-30m.s3.amazonaws.com/
   The WBM is the auxiliary raster shipped with each 1x1 degree DEM tile:
   0 no water, 1 ocean, 2 lake, 3 river. Its ocean/land boundary is a 30 m
   survey of the coastline, two orders of magnitude finer than the 1:50m
   Natural Earth vectors this repo already vendors (which carry three
   vertices inside the Trojan-plain sheet, and cannot draw it at all).

   Licence: the ESA/Airbus "Copernicus DEM Instrument Data" terms grant a
   free, worldwide, non-exclusive, royalty-free, perpetual right to use,
   reproduce, modify and distribute, CONDITIONAL ON the attribution notice
   reproduced in `sources/copernicus-dem/README.md`. It is NOT share-alike.

2. RIVERS -- OpenStreetMap, via the Overpass API. There is no comparable
   public-domain source for a river CENTRELINE at this scale: Natural Earth
   1:10m has no watercourse anywhere inside the Troad sheet (checked), and
   the Copernicus water mask classes the Karamenderes as river for only a
   few hundred pixels of its lowest reach.

   Licence: ODbL 1.0. Attribution ("(c) OpenStreetMap contributors") is
   required, AND the share-alike clause applies to a Derivative Database --
   which the vendored file under `sources/openstreetmap/` and the river
   geometry inside the plate JSONs both are. See that directory's README for
   the obligations in full; they are a decision for the project owner, not
   for this script.

DEPENDENCIES. numpy and Pillow beyond the standard library, and deliberately
so: the Copernicus rasters are tiled float32/uint8 GeoTIFFs and the standard
library has no TIFF decoder. Neither package is a runtime dependency of the
site or of `homer_pipeline` -- this is a manual vendoring script whose OUTPUT
is committed, run by hand when the base geometry needs rebuilding, exactly
like `scripts/prep-naturalearth-coastline.py`.

OUTPUT
------
  sources/copernicus-dem/trojan-plain-coastline.json
  sources/copernicus-dem/trojan-plain-sea.json
  sources/copernicus-dem/troad-coastline.json
  sources/openstreetmap/trojan-plain-rivers.json
  sources/openstreetmap/troad-rivers.json

each `{ "source", "sourceUrl", "license", "derivation", "bbox", "features" }`
where a feature is `{ "id", "name", "points": [[lat, lon], ...] }` in this
project's coordinate order (not GeoJSON's `[lon, lat]`), rounded to 5 decimals
(~1 m -- finer than any of this data claims, but a rounding that never costs a
visible vertex).

With `--update-plates` the same geometry is written into the coast, island and
river layers of the two plate files. Layer ids never change (the renderer
resolves features by id) and no other layer is touched: the relief and Bronze
Age reconstruction layers belong to a different lane.

Usage:
    python3 scripts/prep-troad-basemap.py                    # emit sources
    python3 scripts/prep-troad-basemap.py --update-plates    # and rewrite plates
"""
from __future__ import annotations

import argparse
import json
import math
import os
import ssl
import unicodedata
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# The python.org macOS framework build ships no root certificates unless
# "Install Certificates.command" has been run, so urllib's default context
# fails on every https fetch here. certifi's bundle is used when it is
# importable, and the default context otherwise.
try:  # pragma: no cover - environment dependent
    import certifi

    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    SSL_CTX = ssl.create_default_context()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEM_DIR = os.path.join(ROOT, "sources", "copernicus-dem")
OSM_DIR = os.path.join(ROOT, "sources", "openstreetmap")
PLATE_DIR = os.path.join(ROOT, "apparatus", "plates")

DEM30_BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

DEM_LICENSE = (
    "Copernicus DEM GLO-30. (c) DLR e.V. 2010-2014 and (c) Airbus Defence and "
    "Space GmbH 2014-2018 provided under COPERNICUS by the European Union and "
    "ESA; all rights reserved. Free worldwide licence to use, reproduce, "
    "modify and distribute, conditional on this attribution. Not share-alike."
)
OSM_LICENSE = (
    "(c) OpenStreetMap contributors, ODbL 1.0 "
    "(https://opendatacommons.org/licenses/odbl/1-0/). Attribution required; "
    "share-alike applies to derivative databases."
)

# ── The two sheets ────────────────────────────────────────────────────────
# bbox is [minLat, minLon, maxLat, maxLon] -- the plates' own convention.
PLAIN_BBOX = (39.86, 26.10, 40.05, 26.38)
TROAD_BBOX = (38.95, 25.35, 40.60, 27.50)

# Douglas-Peucker tolerance in degrees, set to about half a pixel at each
# plate's own render size -- the plain draws 0.19 deg of latitude into 779 px
# (1 px = 0.000244 deg), the Troad 1.65 deg into 839 px (1 px = 0.00197 deg).
# Generalising to the sheet is correct cartography; keeping vertices finer
# than half a pixel only adds bytes no reader can see.
PLAIN_TOL = 0.00012
TROAD_TOL = 0.00100

# Rings smaller than this (square degrees) are specks at the sheet's scale.
PLAIN_MIN_AREA = 2.0e-7   # ~2.5 ha
TROAD_MIN_AREA = 8.0e-6   # ~80 ha

# Anchors: one or more points known to lie ON each landmass, used to decide
# which contoured land body belongs to which plate layer. Gazetteer-grade
# points, not invented ones -- a summit, a cape, a town site.
TROAD_LAND_ANCHORS = {
    # Asia Minor: Ida's summit, the Troad interior, the Adramyttian hinterland,
    # and the Asian side of the Dardanelles behind Abydos.
    "coast-asia": [(39.70, 26.92), (39.60, 26.45), (39.35, 26.90), (40.25, 26.62)],
    # The Thracian Chersonese, well back from the strait so the 1.3 km narrows
    # can never flip the test to the Asian side.
    "coast-chersonese": [(40.30, 26.42), (40.50, 26.70), (40.13, 26.28)],
    # Lesbos, Samothrace, Imbros.
    "coast-islands": [(39.15, 26.30), (40.45, 25.53), (40.17, 25.85)],
    # Tenedos / Bozcaada.
    "coast-tenedos": [(39.82, 26.04)],
}
PLAIN_LAND_ANCHORS = {"coast-modern": [(39.95, 26.30)]}

# Which OSM watercourse feeds which plate layer. Matching is on a
# diacritic-folded substring of the OSM `name` tag, so "Karamenderes Nehri"
# and "Karamenderes Cayi" both hit.
PLAIN_RIVERS = {
    "scamander": ("karamenderes",),
    "simoeis": ("dombrik", "dumrek"),
}
TROAD_RIVERS = {
    "river-scamander": ("karamenderes",),
    "river-granikos": ("biga cayi",),
    "river-aisepos": ("gonen cayi",),
    "river-satnioeis": ("tuzla cayi",),
}

# ── What the sheet says about itself ──────────────────────────────────────
# The layer notes live here, not only in the JSON, so that the claim a layer
# makes about its own provenance is rewritten by the same run that rewrites
# its geometry. A note that outlives the data it describes is how a map
# starts lying.
NOTES = {
    "trojan-plain": {
        "sea-modern": (
            "The MODERN sea: the Aegean off the Sigeion shore and the mouth of the "
            "Dardanelles, as they stand now. Contoured from the ocean class of the "
            "Copernicus DEM GLO-30 Water Body Mask at 30 m posting and filled, so that "
            "the Bronze Age water drawn over it -- the embayment, the lagoon, the "
            "swamp -- is read against a real sea rather than against blank parchment. "
            "This is not the sea of 1200 BC: at that date the water reached far further "
            "south, over ground the Scamander has since filled in. Drawn first, under "
            "every other layer, because it is the sheet's water and not a feature on it."
        ),
        "coast-modern": (
            "The modern coast, and the only surveyed waterline on this sheet: the Aegean "
            "shore south to Besik Bay, the mouth of the Karamenderes, Kum Kale, and the "
            "Dardanelles shore running east past the Rhoiteion spur. Every vertex is a "
            "measurement -- the ocean class of the Copernicus DEM GLO-30 Water Body Mask, "
            "30 m posting, contoured at the land/water boundary and generalised to about "
            "half a pixel at this plate's size. It is drawn ON by default because the "
            "reconstruction above it has to be read against something surveyed: the ground "
            "between this line and the Bronze Age shore is delta the Scamander has laid "
            "down since. This layer carried fifteen hand-typed vertices before 2026-07-28."
        ),
        "scamander": (
            "Scamander, called Xanthus by the gods (Il. 20.74); the modern Karamenderes. "
            "The line is the MODERN channel, from OpenStreetMap, chained out of the ways "
            "OSM splits a river into and generalised to the sheet: the meanders are "
            "surveyed, not drawn. Its Bronze Age bed is not this line and is not drawn -- "
            "the channel then lay west of today's, in water that is now land, and no "
            "publication gives a coordinate for it. Read this as the river's valley, which "
            "has not moved, rather than as its 1200 BC course, which has."
        ),
        "simoeis": (
            "The Simoeis, coming down from the north-east along the far side of the ridge "
            "Hisarlik stands on; 'between the streams of Simoeis and Xanthus' is where the "
            "fighting runs (Il. 6.4). The equation with the modern Dumrek Su is a Strabonic "
            "tradition that Leaf, Cook and Luce all accept, not an excavated fact, and the "
            "gazetteer holds the river at that tier. The line is the modern Dumrek from "
            "OpenStreetMap, carried west as far as the channel is mapped: it stops about a "
            "kilometre short of the Karamenderes, which is where the survey stops, not "
            "where the river does. Homer's confluence of the two (5.774) is deliberately "
            "not marked -- both channels have shifted and the whole delta has prograded, so "
            "its Bronze Age position cannot be fixed."
        ),
    },
    "troad": {
        "coast-asia": (
            "The Asian shore: north from the coast facing Lesbos, round the head of the "
            "Gulf of Adramyttium, west along the southern Troad to Cape Lekton, north past "
            "Besik Bay and the mouth of the Scamander to Kum Kale, then north-east up the "
            "Dardanelles past Abydos and out towards the Marmara. From the ocean class of "
            "the Copernicus DEM GLO-30 Water Body Mask at 30 m posting, generalised to "
            "about half a pixel at this sheet's scale (a pixel here is roughly 220 m). "
            "Cape Lekton, the Adramyttian head and the Dardanelles narrows are all in the "
            "data: nothing on this line is hand-placed. It replaces a 1:50m Natural Earth "
            "generalisation whose vertices fell about 12 km apart and which flattened Cape "
            "Lekton away entirely."
        ),
        "coast-chersonese": (
            "The Thracian Chersonese, the European shore of the Hellespont, from the "
            "Marmara end down to the cape opposite Kum Kale and back up its Aegean side. "
            "Sestos stands on this shore opposite Abydos and is the only European territory "
            "in the Trojan alliance (Il. 2.836). Same source and generalisation as the "
            "Asian shore. The ring is open at the top edge because the peninsula's neck "
            "runs off the sheet."
        ),
        "coast-islands": (
            "Lesbos, rugged Imbros, Thracian Samos, the eastern end of Lemnos, and every "
            "smaller island the water mask resolves inside the sheet, each as its own ring. "
            "Lesbos is 'above, seat of Macar', the northern bound of Priam's realm "
            "(Il. 24.544); Poseidon strides from the topmost peak of Samothrace, from which "
            "Ida, Priam's city and the Achaean ships are all visible (13.11-14); Imbros is "
            "'rugged' on that same route (13.33). From the same 30 m water mask as the two "
            "mainland shores. The Natural Earth 1:50m vectors this layer used to carry gave "
            "Samothrace five vertices and Imbros six -- polygons, not coasts."
        ),
        "coast-tenedos": (
            "Tenedos, modern Bozcaada, off the mouth of Besik Bay: under Apollo's "
            "protection (Il. 1.38), sacked by Achilles (11.625), and the waypoint for "
            "Poseidon striding from Samothrace 'midway between Tenedos and rugged Imbros' "
            "(13.33). Its position is why the Besik Bay harbour case matters: any ship "
            "coming to Troy from the south passes it. From the 30 m water mask, which -- "
            "unlike Natural Earth's 1:50m land layer, that omits the island altogether -- "
            "resolves its bays."
        ),
        "river-scamander": (
            "Scamander, called Xanthus by the gods (Il. 20.74), from its head on Ida's "
            "north-western flank down to the Dardanelles: the river that organises the "
            "whole Troad. The modern Karamenderes, from OpenStreetMap. At this scale the "
            "Bronze Age shoreline correction is smaller than the line weight, so the modern "
            "mouth is drawn; the detail plate (trojan-plain) carries the reconstruction."
        ),
        "river-granikos": (
            "The Granicus, one of the eight Idaean rivers Poseidon and Apollo turn against "
            "the Achaean wall (Il. 12.21); later famous as the site of Alexander's first "
            "victory in Asia. Its identification with the Biga Cayi is standard since "
            "antiquity -- a tradition, not an excavated fact. Course from OpenStreetMap."
        ),
        "river-aisepos": (
            "The Aesepus, modern Gonen Cayi, and the eastern limit of Trojan-allied "
            "territory: Pandarus's Zeleians 'drink the dark water of Aesepus' (Il. 2.825), "
            "and it is another of the eight Idaean rivers (12.21). Course from "
            "OpenStreetMap, drawn from the mouth to the east neatline; the upper course "
            "lies off this sheet."
        ),
        "river-satnioeis": (
            "The Satnioeis: 'the banks of fair-flowing Satnioeis' (Il. 6.34), where Satnios "
            "was born to a nymph and a herdsman by its waters (14.445), and below which "
            "'steep Pedasus' stands (21.87). Drawn as the modern Tuzla Cayi, running west "
            "along the southern Troad to the Aegean opposite Lesbos -- a traditional "
            "identification resting on Strabo's account of the river's course, not an "
            "excavated fact, and the gazetteer holds the place at that tier. Course from "
            "OpenStreetMap."
        ),
    },
}

# A layer this script owns that a plate does not yet carry. Geometry is filled
# from the data like any other; everything else is declared here.
NEW_LAYERS = {
    "trojan-plain": [
        {
            # First in the list, so every other layer draws over it: this is
            # the sheet's water, not a feature on it.
            "after": None,
            "layer": {
                "id": "sea-modern",
                "kind": "region",
                "fill": "sea",
                "default": "on",
                "polygon": [],
            },
        }
    ],
    "troad": [
        {
            "after": "river-aisepos",
            "layer": {
                "id": "river-satnioeis",
                "kind": "river",
                "placeId": "satnioeis",
                "default": "on",
                "width": 1.5,
                "path": [],
                "sources": [
                    {"cite": "Strabo, Geography 13.1.",
                     "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"},
                    {"cite": "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."},
                ],
            },
        }
    ]
}

# Per-layer citations. A coast layer that still cited Natural Earth after
# being redrawn from a 30 m water mask would be a false claim about its own
# provenance, so these are rewritten with the geometry.
DEM_CITE = {
    "cite": ("Copernicus DEM GLO-30, Water Body Mask. (c) DLR e.V. 2010-2014 and "
             "(c) Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS "
             "by the European Union and ESA."),
    "url": "https://copernicus-dem-30m.s3.amazonaws.com/",
}
OSM_CITE = {
    "cite": "OpenStreetMap contributors, waterway data, ODbL 1.0.",
    "url": "https://www.openstreetmap.org/copyright",
}
LAYER_SOURCES = {
    "sea-modern": [DEM_CITE],
    "coast-modern": [DEM_CITE],
    "coast-asia": [DEM_CITE, {"cite": "Pleiades: Lekton.", "url": "https://pleiades.stoa.org/places/550691"}],
    "coast-chersonese": [DEM_CITE],
    "coast-islands": [DEM_CITE],
    "coast-tenedos": [DEM_CITE, {"cite": "Pleiades: Tenedos.", "url": "https://pleiades.stoa.org/places/550912"}],
    "scamander": [OSM_CITE, {"cite": "Pleiades: Scamander.", "url": "https://pleiades.stoa.org/places/550871"}],
    "simoeis": [OSM_CITE,
                {"cite": "Strabo, Geography 13.1.",
                 "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"},
                {"cite": "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."}],
    "river-scamander": [OSM_CITE, {"cite": "Pleiades: Scamander.", "url": "https://pleiades.stoa.org/places/550871"}],
    "river-granikos": [OSM_CITE,
                       {"cite": "Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014."}],
    "river-aisepos": [OSM_CITE, {"cite": "Pleiades: Aesepus.", "url": "https://pleiades.stoa.org/places/511141"}],
    "river-satnioeis": [OSM_CITE,
                        {"cite": "Strabo, Geography 13.1.",
                         "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"},
                        {"cite": "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."}],
}

# Sentences in the plate-level notes that the redraw makes false. Applied as
# exact replacements so a concurrent edit elsewhere in the note survives.
NOTE_FIXES = {
    "trojan-plain": [
        ("NOTHING ON THIS PLATE IS TRACED from any published figure: see the shore "
         "layer's note for how the line was derived from stated measurements.",
         "The BASE of this sheet is survey: the modern coast is contoured from the "
         "Copernicus DEM's 30 m water mask, and the rivers are OpenStreetMap's mapped "
         "channels, so the reconstruction has something measured to be read against. "
         "The Bronze Age reconstruction drawn over that base is NOT TRACED from any "
         "published figure -- see the shore layer's note for how its line was derived "
         "from stated measurements."),
    ],
    "troad": [
        ("and the Scamander, Granicus and Aesepus.",
         "and the Scamander, Satnioeis, Granicus and Aesepus."),
        ("Lemnos, the Achaeans' rear base, lies west of this sheet and is not drawn "
         "rather than drawn as a sliver.",
         "Lemnos, the Achaeans' rear base, lies mostly west of this sheet; the eastern "
         "end that falls inside the neatline is drawn."),
        ("Island outlines are Natural Earth 1:50m, which is public domain but coarse at "
         "this scale and omits Tenedos entirely, so Tenedos is hand-drawn; see the layer "
         "notes.",
         "Every coastline here -- both mainland shores, all the islands, Tenedos -- is "
         "contoured from the ocean class of the Copernicus DEM's 30 m Water Body Mask "
         "and generalised to about half a pixel at this scale; the rivers are "
         "OpenStreetMap's mapped channels. See the layer notes."),
    ],
}

# Plate-level source entries for the two datasets this script draws from.
PLATE_SOURCES = [
    {
        "cite": ("Copernicus DEM GLO-30 (30 m global digital surface model), Water Body "
                 "Mask. (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH "
                 "2014-2018, provided under COPERNICUS by the European Union and ESA. "
                 "Coastlines and islands on this sheet are contoured from it."),
        "url": "https://copernicus-dem-30m.s3.amazonaws.com/",
    },
    {
        "cite": ("OpenStreetMap contributors. River courses on this sheet are taken from "
                 "OSM waterway data, ODbL 1.0."),
        "url": "https://www.openstreetmap.org/copyright",
    },
]


# ── Copernicus tiles ──────────────────────────────────────────────────────

def tile_name(lat: int, lon: int) -> str:
    return f"N{lat:02d}_00_E{lon:03d}_00"


def fetch_wbm(lat: int, lon: int, cache: str) -> np.ndarray:
    os.makedirs(cache, exist_ok=True)
    t = tile_name(lat, lon)
    path = os.path.join(cache, f"WBM_{t}.tif")
    if not os.path.exists(path):
        url = f"{DEM30_BUCKET}/Copernicus_DSM_COG_10_{t}_DEM/AUXFILES/Copernicus_DSM_COG_10_{t}_WBM.tif"
        print(f"  fetching {url}")
        with urllib.request.urlopen(url, timeout=300, context=SSL_CTX) as resp, open(path, "wb") as f:
            f.write(resp.read())
    return np.array(Image.open(path))


def wbm_mosaic(bbox, cache):
    """Assemble the 1x1 degree WBM tiles covering bbox.

    Copernicus tiles are pixel-is-point: row 0 of tile Nxx sits at latitude
    xx+1 exactly and row n-1 at xx + 1/n, so stacking a northern tile on a
    southern one gives a gapless, duplicate-free grid at 1/n degree spacing.
    """
    la0, lo0, la1, lo1 = bbox
    lats = list(range(int(math.ceil(la1)) - 1, int(math.floor(la0)) - 1, -1))
    lons = list(range(int(math.floor(lo0)), int(math.ceil(lo1))))
    rows, n = [], None
    for la in lats:
        cols = []
        for lo in lons:
            arr = fetch_wbm(la, lo, cache)
            n = arr.shape[0]
            cols.append(arr)
        rows.append(np.hstack(cols))
    return np.vstack(rows), float(lats[0] + 1), float(lons[0]), 1.0 / n


def window(grid, lat_top, lon_left, step, bbox, pad):
    """Crop to bbox + pad. The pad matters: a landmass cut by the neatline
    contours as an OPEN line, and an open line cannot be tested for what it
    contains. Contour the padded window, identify bodies, then clip."""
    la0, lo0, la1, lo1 = bbox
    r0 = max(0, int(math.floor((lat_top - (la1 + pad)) / step)))
    r1 = min(grid.shape[0], int(math.ceil((lat_top - (la0 - pad)) / step)))
    c0 = max(0, int(math.floor(((lo0 - pad) - lon_left) / step)))
    c1 = min(grid.shape[1], int(math.ceil(((lo1 + pad) - lon_left) / step)))
    return grid[r0:r1, c0:c1], lat_top - r0 * step, lon_left + c0 * step


# ── Marching squares ──────────────────────────────────────────────────────

def marching_squares(grid: np.ndarray, level: float):
    """Contour `grid` at `level`; polylines in (row, col) index space."""
    g = grid.astype(np.float64)
    above = g >= level

    def interp(v0, v1):
        d = v1 - v0
        return 0.5 if d == 0 else min(1.0, max(0.0, (level - v0) / d))

    tl, tr = above[:-1, :-1], above[:-1, 1:]
    br, bl = above[1:, 1:], above[1:, :-1]
    code = ((tl.astype(np.uint8) << 3) | (tr.astype(np.uint8) << 2)
            | (br.astype(np.uint8) << 1) | bl.astype(np.uint8))
    rows, cols = np.nonzero((code > 0) & (code < 15))
    segs = []
    for r, c in zip(rows.tolist(), cols.tolist()):
        v_tl, v_tr, v_br, v_bl = g[r, c], g[r, c + 1], g[r + 1, c + 1], g[r + 1, c]
        top = (r, c + interp(v_tl, v_tr))
        right = (r + interp(v_tr, v_br), c + 1)
        bottom = (r + 1, c + interp(v_bl, v_br))
        left = (r + interp(v_tl, v_bl), c)
        k = int(code[r, c])
        if k in (1, 14):
            segs.append((left, bottom))
        elif k in (2, 13):
            segs.append((bottom, right))
        elif k in (3, 12):
            segs.append((left, right))
        elif k in (4, 11):
            segs.append((top, right))
        elif k in (6, 9):
            segs.append((top, bottom))
        elif k in (7, 8):
            segs.append((left, top))
        elif k == 5:
            segs.append((left, top))
            segs.append((bottom, right))
        elif k == 10:
            segs.append((top, right))
            segs.append((left, bottom))
    return stitch(segs)


def stitch(segs, tol=1e-6):
    """Join segments end to end into polylines (and closed rings)."""
    from collections import defaultdict

    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))

    adj = defaultdict(list)
    for i, (a, b) in enumerate(segs):
        adj[key(a)].append(i)
        adj[key(b)].append(i)
    used = [False] * len(segs)
    lines = []
    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        a, b = segs[i]
        line = [a, b]
        for _ in (0, 1):
            while True:
                end = line[-1]
                nxt = None
                for j in adj.get(key(end), ()):
                    if used[j]:
                        continue
                    pa, pb = segs[j]
                    if key(pa) == key(end):
                        nxt = (j, pb)
                        break
                    if key(pb) == key(end):
                        nxt = (j, pa)
                        break
                if nxt is None:
                    break
                j, p = nxt
                used[j] = True
                line.append(p)
                if key(p) == key(line[0]):
                    break
            line.reverse()
        lines.append(line)
    return lines


# ── Geometry ──────────────────────────────────────────────────────────────

def to_latlon(line, lat_top, lon_left, step):
    return [(lat_top - r * step, lon_left + c * step) for r, c in line]


def rdp(points, eps):
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        ay, ax = points[i]
        by, bx = points[j]
        dy, dx = by - ay, bx - ax
        norm = math.hypot(dy, dx)
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            py, px = points[k]
            d = (math.hypot(py - ay, px - ax) if norm == 0
                 else abs(dx * (ay - py) - dy * (ax - px)) / norm)
            if d > best:
                best, bi = d, k
        if best > eps:
            keep[bi] = True
            stack.append((i, bi))
            stack.append((bi, j))
    return [p for p, k in zip(points, keep) if k]


def ring_area(points):
    a = 0.0
    n = len(points)
    for i in range(n):
        y0, x0 = points[i]
        y1, x1 = points[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return abs(a / 2.0)


def contains(ring, pt) -> bool:
    y, x = pt
    inside = False
    n = len(ring)
    for i in range(n):
        y0, x0 = ring[i]
        y1, x1 = ring[(i + 1) % n]
        if (x0 > x) != (x1 > x):
            if y0 + (y1 - y0) * (x - x0) / (x1 - x0) > y:
                inside = not inside
    return inside


def clip_polyline(line, bbox):
    """Cut a polyline to the bbox, keeping the inside pieces as separate open
    polylines. A coast or a river is stroked, never filled, so it must not be
    closed along the neatline -- that would draw the sheet's own edge as land.
    """
    la0, lo0, la1, lo1 = bbox

    def cut(a, b):  # Liang-Barsky
        t0, t1 = 0.0, 1.0
        dy, dx = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dy, a[0] - la0), (dy, la1 - a[0]),
                     (-dx, a[1] - lo0), (dx, lo1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
                continue
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return None
        return ((a[0] + dy * t0, a[1] + dx * t0), (a[0] + dy * t1, a[1] + dx * t1))

    out, cur = [], []
    for i in range(len(line) - 1):
        seg = cut(line[i], line[i + 1])
        if seg is None:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            continue
        s, e = seg
        if cur and abs(cur[-1][0] - s[0]) < 1e-12 and abs(cur[-1][1] - s[1]) < 1e-12:
            cur.append(e)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = [s, e]
    if len(cur) > 1:
        out.append(cur)
    return out


def dedupe(points):
    out = []
    for p in points:
        if not out or (abs(p[0] - out[-1][0]) > 1e-12 or abs(p[1] - out[-1][1]) > 1e-12):
            out.append(p)
    return out


def rnd(points, nd=5):
    return [[round(p[0], nd), round(p[1], nd)] for p in points]


# ── Coast extraction ──────────────────────────────────────────────────────

def clip_polygon(ring, bbox):
    """Sutherland-Hodgman -- for a FILLED body, where closing along the
    neatline is correct. The plate renderer strokes a coast ring open and
    fills it closed from the same points, and its 1.2 px outer neatline is
    drawn last, over the sheet edge: a closing edge that runs along the bbox
    is covered by the frame, so a filled coast can be clipped as a polygon
    without a false shoreline appearing along the neatline."""
    la0, lo0, la1, lo1 = bbox

    def clip_edge(points, keep, cross):
        if not points:
            return []
        out = []
        prev = points[-1]
        prev_in = keep(prev)
        for cur in points:
            cur_in = keep(cur)
            if cur_in:
                if not prev_in:
                    out.append(cross(prev, cur))
                out.append(cur)
            elif prev_in:
                out.append(cross(prev, cur))
            prev, prev_in = cur, cur_in
        return out

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    pts = list(ring)
    pts = clip_edge(pts, lambda p: p[0] >= la0,
                    lambda a, b: lerp(a, b, (la0 - a[0]) / (b[0] - a[0])) if b[0] != a[0] else a)
    pts = clip_edge(pts, lambda p: p[0] <= la1,
                    lambda a, b: lerp(a, b, (la1 - a[0]) / (b[0] - a[0])) if b[0] != a[0] else a)
    pts = clip_edge(pts, lambda p: p[1] >= lo0,
                    lambda a, b: lerp(a, b, (lo0 - a[1]) / (b[1] - a[1])) if b[1] != a[1] else a)
    pts = clip_edge(pts, lambda p: p[1] <= lo1,
                    lambda a, b: lerp(a, b, (lo1 - a[1]) / (b[1] - a[1])) if b[1] != a[1] else a)
    return pts


def land_bodies(bbox, cache, pad, want="land"):
    """Closed rings, one per landmass, from the Copernicus water mask.

    The mask is contoured as LAND (anything the WBM does not call ocean) over
    a padded window whose outermost frame is forced to sea. Forcing the frame
    is what makes every body come back CLOSED, even the ones that run off the
    sheet -- and a closed ring is the only thing a point-in-polygon test can
    be run against, which is how each body finds its plate layer. The
    artificial closing edges sit outside the real bbox and are clipped away.
    """
    wbm, lat_top, lon_left, step = wbm_mosaic(bbox, cache)
    w, lt, ll = window(wbm, lat_top, lon_left, step, bbox, pad=pad)
    land = (w == 1).astype(np.float64) if want == "ocean" else (w != 1).astype(np.float64)
    land[0, :] = land[-1, :] = land[:, 0] = land[:, -1] = 0.0
    rings = []
    for ln in marching_squares(land, 0.5):
        pts = to_latlon(ln, lt, ll, step)
        if len(pts) < 4:
            continue
        rings.append(pts)
    return rings


def clip_body(ring, bbox, tol, closed):
    """One landmass, cut to the sheet: as closed polygons when the layer's
    rings are filled (the `fill` contract in docs/APPARATUS-SCHEMAS.md), as
    open polylines when they are pure linework."""
    if closed:
        cp = dedupe(rdp(clip_polygon(ring, bbox), tol))
        return [cp] if len(cp) >= 3 else []
    out = []
    for piece in clip_polyline(ring, bbox):
        simp = dedupe(rdp(piece, tol))
        if len(simp) >= 2:
            out.append(simp)
    return out


def assign_coast(bodies, anchors, bbox, tol, min_area, closed=False):
    """Point-in-polygon each landmass against the layer anchors, then clip."""
    out = {k: [] for k in anchors}
    unassigned = []
    for ring in bodies:
        layer = None
        for name, pts in anchors.items():
            if any(contains(ring, p) for p in pts):
                layer = name
                break
        if layer is None:
            if ring_area(ring) < min_area:
                continue
            unassigned.append(ring)
            continue
        out[layer].extend(clip_body(ring, bbox, tol, closed))
    return out, unassigned


# ── Rivers (OpenStreetMap / Overpass) ─────────────────────────────────────

def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("ı", "i").replace("İ", "i").lower()


def overpass(bbox, cache, tag: str, named_only: bool, pad: float = 0.0):
    os.makedirs(cache, exist_ok=True)
    la0, lo0, la1, lo1 = bbox
    la0, lo0, la1, lo1 = la0 - pad, lo0 - pad, la1 + pad, lo1 + pad
    path = os.path.join(cache, f"osm_{tag}.json")
    if not os.path.exists(path):
        name_filter = '["name"]' if named_only else ""
        q = ('[out:json][timeout:280];('
             f'way["waterway"~"^(river|stream)$"]{name_filter}({la0},{lo0},{la1},{lo1});'
             ');out geom;')
        print(f"  querying Overpass for {tag}")
        data = urllib.parse.urlencode({"data": q}).encode()
        # Overpass answers 406 to a request with no User-Agent.
        req = urllib.request.Request(
            OVERPASS_URL, data=data,
            headers={"User-Agent": "homer-reader/prep-troad-basemap (github.com/johnhboyer-sys/homer-reader)"})
        with urllib.request.urlopen(req, timeout=300, context=SSL_CTX) as resp, \
                open(path, "wb") as f:
            f.write(resp.read())
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def join_ways(ways, primary=None):
    """Join OSM ways sharing an endpoint into continuous courses.

    OSM splits a river into dozens of ways at every bridge, boundary and
    landuse edge; a plate wants one line. Ways are chained on coincident
    endpoints. At a junction the chain follows a `primary` way (one whose
    name matched the river we are after) in preference to an unnamed one, so
    that an unnamed connector can carry the course across a gap in the name
    tagging without an unnamed tributary being able to hijack it.
    """
    primary = primary or set()
    segs, is_primary = [], []
    for i, w in enumerate(ways):
        pts = [(p["lat"], p["lon"]) for p in w.get("geometry", [])]
        if len(pts) > 1:
            segs.append(pts)
            is_primary.append(i in primary)

    def key(p):
        return (round(p[0], 7), round(p[1], 7))

    from collections import defaultdict
    ends = defaultdict(list)
    for i, s in enumerate(segs):
        ends[key(s[0])].append(i)
        ends[key(s[-1])].append(i)
    used = [False] * len(segs)
    chains = []
    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        chain = list(segs[i])
        for _ in (0, 1):
            while True:
                cands = []
                for j in ends.get(key(chain[-1]), ()):
                    if used[j]:
                        continue
                    s = segs[j]
                    if key(s[0]) == key(chain[-1]):
                        cands.append((not is_primary[j], j, s[1:]))
                    elif key(s[-1]) == key(chain[-1]):
                        cands.append((not is_primary[j], j, list(reversed(s))[1:]))
                if not cands:
                    break
                cands.sort(key=lambda t: (t[0], -len(t[2])))
                _, j, tail = cands[0]
                used[j] = True
                chain.extend(tail)
            chain.reverse()
        chains.append(chain)
    chains.sort(key=len, reverse=True)
    return chains


def rivers(bbox, cache, tag, selectors, tol, named_only=True, pad=0.0):
    """One continuous course per plate layer, from OSM waterways.

    With `named_only=False` the query also returns UNNAMED waterway ways, and
    each course is chained through them: OSM's name tagging on the Dumrek Su
    stops after 7 km, and without the unnamed connectors the Simoeis would be
    drawn as a stub floating in the middle of the sheet. The chain kept for a
    layer is the one carrying the most vertices that came from a NAMED,
    matching way, so an unnamed tributary can never become the river.
    """
    data = overpass(bbox, cache, tag, named_only, pad)
    ways = [e for e in data["elements"] if e.get("type") == "way"]
    out = {}
    for layer, needles in selectors.items():
        matched = [w for w in ways
                   if any(n in fold(w.get("tags", {}).get("name", "")) for n in needles)]
        if not matched:
            print(f"  WARNING: no OSM watercourse matched {needles} for {layer}")
            out[layer] = []
            continue
        if named_only:
            pool = matched
        else:
            pool = matched + [w for w in ways if not w.get("tags", {}).get("name")]
        primary = {i for i, w in enumerate(pool) if w in matched}
        named_pts = {(round(p["lat"], 7), round(p["lon"], 7))
                     for w in matched for p in w.get("geometry", [])}
        chains = join_ways(pool, primary)
        best, best_score = None, -1
        for c in chains:
            score = sum(1 for p in c if (round(p[0], 7), round(p[1], 7)) in named_pts)
            if score > best_score or (score == best_score and best and len(c) > len(best)):
                best, best_score = c, score
        pieces = clip_polyline(best or [], bbox)
        pieces.sort(key=len, reverse=True)
        out[layer] = dedupe(rdp(pieces[0], tol)) if pieces else []
    return out


# ── Emit ──────────────────────────────────────────────────────────────────

def write_json(directory, name, payload):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
        f.write("\n")
    n = sum(len(feat["points"]) for feat in payload["features"])
    print(f"  wrote {name}: {len(payload['features'])} features, {n} vertices, "
          f"{os.path.getsize(path) / 1024:.0f} KB")


def coast_payload(bbox, assigned, derivation):
    feats = []
    for layer, rings in assigned.items():
        for i, r in enumerate(rings):
            feats.append({"id": layer, "name": f"{layer}#{i}", "points": rnd(r)})
    return {
        "source": "Copernicus DEM GLO-30 Water Body Mask (AWS Open Data)",
        "sourceUrl": DEM30_BUCKET + "/",
        "license": DEM_LICENSE,
        "derivation": derivation,
        "bbox": list(bbox),
        "features": feats,
    }


def river_payload(bbox, courses, derivation):
    return {
        "source": "OpenStreetMap, via the Overpass API",
        "sourceUrl": "https://www.openstreetmap.org/",
        "license": OSM_LICENSE,
        "derivation": derivation,
        "bbox": list(bbox),
        "features": [{"id": k, "name": k, "points": rnd(v)} for k, v in courses.items() if v],
    }


# ── Plate rewriting ───────────────────────────────────────────────────────

def load_plate(pid):
    with open(os.path.join(PLATE_DIR, f"{pid}.json"), "r", encoding="utf-8") as f:
        return json.load(f)


#: `[lat, lon]` on one line. json.dump(indent=2) puts each number on its own
#: line, which turns a coastline into thousands of unreadable diff lines; the
#: plate files have always kept a coordinate pair together, and a geometry
#: rewrite must not also be a reformat.
_NUM = r"-?\d+(?:\.\d+)?"
_PAIR_RE = __import__("re").compile(
    r"\[\s*\n\s*(" + _NUM + r")(?:,\s*\n\s*(" + _NUM + r")){1,3}\s*\n\s*\]")


def _collapse(m):
    return "[" + ", ".join(__import__("re").findall(_NUM, m.group(0))) + "]"


def save_plate(pid, doc):
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    while True:
        text, n = _PAIR_RE.subn(_collapse, text)
        if not n:
            break
    with open(os.path.join(PLATE_DIR, f"{pid}.json"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


def set_layer(doc, pid, layer_id, field, value):
    """Write one layer's geometry, and the note that describes its source.

    Only these two fields, and only on the layers this script owns: another
    lane owns the relief and Bronze Age reconstruction layers in the same two
    files, so nothing else here is allowed to touch them.
    """
    for layer in doc["layers"]:
        if layer.get("id") == layer_id:
            layer[field] = value
            note = NOTES.get(pid, {}).get(layer_id)
            if note:
                layer["note"] = note
            srcs = LAYER_SOURCES.get(layer_id)
            if srcs:
                layer["sources"] = json.loads(json.dumps(srcs))
            return True
    print(f"  WARNING: {pid} has no layer {layer_id!r}")
    return False


def ensure_layers(doc, pid):
    """Insert any layer this script owns that the plate does not yet carry."""
    have = {l.get("id") for l in doc["layers"]}
    for spec in NEW_LAYERS.get(pid, []):
        if spec["layer"]["id"] in have:
            continue
        layer = json.loads(json.dumps(spec["layer"]))
        if spec["after"] is None:
            doc["layers"].insert(0, layer)
        else:
            idx = next((i for i, l in enumerate(doc["layers"])
                        if l.get("id") == spec["after"]), len(doc["layers"]) - 1)
            doc["layers"].insert(idx + 1, layer)
        print(f"  added layer {layer['id']} to {pid}")


def ensure_sources(doc, pid):
    """Add the plate-level citation for each dataset drawn on the sheet, drop
    the Natural Earth citation nothing on the sheet rests on any more, and
    correct the sentences of the plate note the redraw makes false."""
    srcs = [s for s in doc.get("sources", []) if "naturalearthdata.com" not in (s.get("url") or "")]
    have = {s.get("url") for s in srcs}
    for src in PLATE_SOURCES:
        if src["url"] not in have:
            srcs.append(json.loads(json.dumps(src)))
    doc["sources"] = srcs
    note = doc.get("note")
    if isinstance(note, str):
        for old, new in NOTE_FIXES.get(pid, []):
            if old in note:
                note = note.replace(old, new)
            elif new not in note:
                print(f"  WARNING: {pid} note has no sentence to fix: {old[:48]}...")
        doc["note"] = note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(ROOT, "build", "basemap-cache"))
    ap.add_argument("--update-plates", action="store_true")
    args = ap.parse_args()

    print("Trojan plain sheet:")
    plain_bodies = land_bodies(PLAIN_BBOX, args.cache, pad=0.03)
    plain_coast, plain_extra = assign_coast(plain_bodies, PLAIN_LAND_ANCHORS,
                                            PLAIN_BBOX, PLAIN_TOL, PLAIN_MIN_AREA)
    for ring in plain_extra:  # islets: real land, same layer, drawn not dropped
        for piece in clip_polyline(ring, PLAIN_BBOX):
            simp = dedupe(rdp(piece, PLAIN_TOL))
            if len(simp) >= 3:
                plain_coast["coast-modern"].append(simp)
    write_json(DEM_DIR, "trojan-plain-coastline.json", coast_payload(
        PLAIN_BBOX, plain_coast,
        "Land (Water Body Mask != ocean) contoured by marching squares at the "
        "land/ocean boundary over a window padded 0.03 deg beyond the sheet, "
        "sorted onto plate layers by point-in-polygon against gazetteer-grade "
        "anchors, clipped to the sheet as open polylines and generalised by "
        f"Douglas-Peucker at {PLAIN_TOL} deg -- about half a pixel at this "
        "plate's render size."))

    # The plain is a mostly-dry sheet, so its ground stays land and its water
    # is drawn as bodies over it (docs/APPARATUS-SCHEMAS.md). The Bronze Age
    # lagoon is another lane's; this is the MODERN sea, closed and filled, so
    # the reconstruction has a real Aegean to sit beside instead of parchment.
    plain_sea = []
    for ring in land_bodies(PLAIN_BBOX, args.cache, pad=0.03, want="ocean"):
        if ring_area(ring) >= PLAIN_MIN_AREA:
            plain_sea.extend(clip_body(ring, PLAIN_BBOX, PLAIN_TOL, True))
    plain_sea.sort(key=len, reverse=True)
    plain_sea = plain_sea[:1]  # the Aegean/Dardanelles body; inland ponds are not sea
    write_json(DEM_DIR, "trojan-plain-sea.json", coast_payload(
        PLAIN_BBOX, {"sea-modern": plain_sea},
        "Ocean class (1) of the same water mask, contoured over the padded "
        "window with its frame forced to land so the body closes, clipped to "
        "the sheet as a polygon and generalised at "
        f"{PLAIN_TOL} deg. The modern sea, not the Bronze Age one."))

    plain_rivers = rivers(PLAIN_BBOX, args.cache, "plain-all", PLAIN_RIVERS, PLAIN_TOL,
                          named_only=False, pad=0.04)
    write_json(OSM_DIR, "trojan-plain-rivers.json", river_payload(
        PLAIN_BBOX, plain_rivers,
        "Named waterways from OSM, ways chained on coincident endpoints into "
        "one course per river, clipped to the sheet and generalised by "
        f"Douglas-Peucker at {PLAIN_TOL} deg."))

    print("Troad sheet:")
    # The Troad is a marine sheet: `ground: "sea"` under everything, and each
    # landmass a CLOSED ring filled `land` over it (docs/APPARATUS-SCHEMAS.md,
    # the ground + fill contract). Closed is why the strait reads as a strait.
    troad_bodies = land_bodies(TROAD_BBOX, args.cache, pad=0.05)
    troad_coast, troad_extra = assign_coast(troad_bodies, TROAD_LAND_ANCHORS, TROAD_BBOX,
                                            TROAD_TOL, TROAD_MIN_AREA, closed=True)
    for ring in troad_extra:  # unnamed islands: draw them with the rest
        troad_coast["coast-islands"].extend(clip_body(ring, TROAD_BBOX, TROAD_TOL, True))
    write_json(DEM_DIR, "troad-coastline.json", coast_payload(
        TROAD_BBOX, troad_coast,
        "Land (Water Body Mask != ocean) contoured at the land/ocean boundary "
        "over a window padded 0.05 deg beyond the sheet, sorted onto plate "
        "layers by point-in-polygon against gazetteer-grade anchors, clipped "
        "to the sheet as open polylines and generalised by Douglas-Peucker at "
        f"{TROAD_TOL} deg -- about half a pixel at this plate's render size."))

    troad_rivers = rivers(TROAD_BBOX, args.cache, "troad", TROAD_RIVERS, TROAD_TOL)
    write_json(OSM_DIR, "troad-rivers.json", river_payload(
        TROAD_BBOX, troad_rivers,
        "Named waterways from OSM, ways chained on coincident endpoints into "
        "one course per river, clipped to the sheet and generalised by "
        f"Douglas-Peucker at {TROAD_TOL} deg."))

    if args.update_plates:
        update_plates(plain_coast, plain_sea, plain_rivers, troad_coast, troad_rivers)


def update_plates(plain_coast, plain_sea, plain_rivers, troad_coast, troad_rivers):
    print("Rewriting plates:")
    doc = load_plate("trojan-plain")
    ensure_layers(doc, "trojan-plain")
    ensure_sources(doc, "trojan-plain")
    set_layer(doc, "trojan-plain", "coast-modern", "rings",
              [rnd(r) for r in plain_coast["coast-modern"]])
    # The modern coast is the only surveyed waterline on the sheet, so the
    # reconstruction has something measured to be read against: on, not off.
    for layer in doc["layers"]:
        if layer.get("id") == "coast-modern":
            layer["default"] = "on"
    set_layer(doc, "trojan-plain", "sea-modern", "polygon",
              rnd(plain_sea[0]) if plain_sea else [])
    for layer_id, pts in plain_rivers.items():
        if pts:
            set_layer(doc, "trojan-plain", layer_id, "path", rnd(pts))
    save_plate("trojan-plain", doc)
    print("  trojan-plain.json")

    doc = load_plate("troad")
    ensure_layers(doc, "troad")
    ensure_sources(doc, "troad")
    # A marine sheet: sea under everything, landmasses filled over it.
    doc["ground"] = "sea"
    for layer_id, rings in troad_coast.items():
        set_layer(doc, "troad", layer_id, "rings", [rnd(r) for r in rings])
        for layer in doc["layers"]:
            if layer.get("id") == layer_id:
                layer["fill"] = "land"
    for layer_id, pts in troad_rivers.items():
        if pts:
            set_layer(doc, "troad", layer_id, "path", rnd(pts))
    save_plate("troad", doc)
    print("  troad.json")


if __name__ == "__main__":
    main()
