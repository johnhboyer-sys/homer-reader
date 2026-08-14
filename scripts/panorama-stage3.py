#!/usr/bin/env python3
"""Stage 3 — THE WHOLE PLATE: "The Ships, the Bay, and Ilios".

The full 2400x1350 raised oblique from the settled Stage-1D camera, in the
Stage-2 register (flat fills, hairline contours, waterlines, the approximate
bronze shore drawn as a hairline against the modern coast's heavier survey
line, no texture), carrying what Stage 2 still owed: the
delta swamp with a faded margin, the neatline, the scale and the key.

THE GROUND IS COLOURED BY WHAT IT IS, NOT BY HOW HIGH IT IS (2026-08-14, and
see the GROUND COVER section below). The twelve hypsometric bands are gone.

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
import re
import subprocess
import time

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
# ── THE SAWTOOTH ALONG THE FRONT EDGE, and why it was in the mesh ────────
# A row of 37 px teeth ran across the foot of the plate wherever the ridge
# mask's edge met the near ground, and no amount of smoothing was ever going to
# cure it, because a smoother cannot invent a sample the mesh never took.
#
# RING_PX steps the rings by their separation ON FLAT GROUND. That is the right
# rule almost everywhere and it fails in one place: the near foreground is the
# BACK OF THE SIGEION RIDGE falling away from the viewpoint, and ground that
# drops away spreads the same ring step over far more screen than flat ground
# would. Measured, on the shipped frame: rings 30-36 m apart at 420-750 m land
# 5 px apart straight ahead, where the ground is nearly level, and 37 px apart
# out to the right, where the ridge back falls. Any boundary the mesh carries
# there -- a cover class, a tone region -- is quantised to a 37 px riser, and a
# mask edge that runs nearly PARALLEL to the rings then alternates rings every
# seven columns, which is a sawtooth by construction.
#
# So the near band is stepped on a finer screen rule. It is the same argument
# RING_MAX_M already makes from the other direction (the mesh must resolve the
# ground it is drawing); this one just measures the failure in pixels instead
# of metres. It costs 42 rings of the 150 and about 8% of the shipped SVG.
RING_PX_NEAR = 3.0
RING_NEAR_DETAIL = 1600.0
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
# leaves at about 19 km. The cap is the GRID'S OWN RESOLVING POWER, and it
# moved when the grid did: the panorama's field is now smoothed at 2+1 box
# passes (sigma 20.7 m at 14.65 m/px) rather than 10+2 (sigma 41.4 m), so
# nothing narrower than about 41 m survives in the data instead of 85 m, and
# the floor drops from 110 m to 45 m to match. See prep-terrain-contours.py's
# `panorama_blur` comment for why the blur went: measured over the whole
# sheet it was costing 1.14 m RMS of height and 13% of the slope, and the raw
# grid's power spectrum shows SRTM has neither landform nor noise below
# ~200 m, so there was nothing down there the blur was protecting anyone from.
#
# WHAT IT COSTS, measured 2026-08-14: 462 rings -> 523, 165,858 mesh nodes ->
# 187,757, and 626 -> 658 KB of SVG. It is that cheap because RING_MIN_PX
# binds first over most of the range -- a 45 m ring is sub-pixel past about
# 6 km -- so the finer floor buys rings exactly where the eye is, in the near
# and middle field, and nothing where it could not see them.
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
RING_MAX_M = 45.0

# The near floor on the mesh's own height stencil (Terrain.elev_smooth), in
# metres of ground. It is an ANTI-ALIAS for the sampler and nothing more now
# that the hypsometric bands it also served are gone, so the right size is
# half the finest ring: a stencil wider than the ring spacing is throwing
# away ground the mesh went to the trouble of sampling. The nine-point
# stencil's own sigma is 0.62 of its radius, so 22 m is sigma 13.6 m against
# the field's 20.7 -- it adds a fifth to the smoothing in quadrature where
# the old 35 m added a half. It was 35 m when the field was sigma 41 m and
# the rings 110 m apart; all three numbers moved together.
MESH_STENCIL_M = 22.0
RING_DETAIL_FAR = 19000.0
RING_MIN_PX = 1.0

# CONTOUR levels. They were also the boundaries of twelve hypsometric bands
# until the ground stopped being coloured by height (see GROUND COVER); now
# they are what they say on the tin -- the elevations the hairlines are cut at,
# and nothing else on the sheet depends on them.
LEVELS = [5, 10, 15, 20, 30, 45, 70, 110, 180, 300, 600]

# ── INDEX CONTOURS ───────────────────────────────────────────────────────
# The oldest weighting convention there is, and the only one that is a RULE
# rather than a thumb on the scale: every Nth isoline is drawn heavier, so the
# eye can count bands and read a slope without any line being chosen for what
# it happens to encircle. It applies across the sheet, by elevation alone.
#
# N = 3. The ladder is roughly geometric (ratio ~1.5), so every third level is
# a step of about 3.4x in elevation -- the even spacing in LOG height that
# "every fifth contour" is in linear height on a uniform ladder.
#
# The PHASE is set by the 10 m level, and not by anything on this sheet's
# subject: 10 m is the level the Bronze Age shoreline was calibrated against
# (TROAD-CARTOGRAPHY.md -- the 10 m contour passes 1.24 km north of Hisarlik
# where the reconstructed shore passes 1.22, against 2.8 km for the 8 m and
# 0.7 for the 12 m). Index lines therefore fall at 10, 30, 110 and 600 m.
#
# DECLARED, because it should not be enjoyed silently: a consequence of that
# phase is that the 30 m isoline -- the one that closes round the citadel --
# is an index line. It arrives by the rule, not for Troy, and the rule would
# have to be broken to keep it out.
CONTOUR_INDEX_EVERY = 3
CONTOUR_INDEX_PHASE = 1
INDEX_LEVELS = frozenset(
    k for k in range(len(LEVELS))
    if k % CONTOUR_INDEX_EVERY == CONTOUR_INDEX_PHASE)

# depth strata: painter order is by stratum, far first. Within a stratum the
# depth spread is small enough that a band union cannot mis-occlude.
STRATA_EDGES = [45000.0, 26000.0, 16000.0, 10500.0, 7000.0, 4800.0,
                3300.0, 2300.0, 1600.0, 1100.0, 750.0, 0.0]

# ── AERIAL PERSPECTIVE IS A LAW, NOT A TABLE (2026-08-14) ────────────────
# The haze was four hand-set numbers on four of the eleven strata --
# 0.20 / 0.13 / 0.09 / 0.05 -- and its colour was --page-bg. Both are now
# wrong for the same reason: distance is not a stylistic dose, it is
# extinction, and extinction is Beer-Lambert.
#
# The painter order does the integration for free and always did. Strata are
# drawn far to near, and the wash laid down before stratum s covers
# everything already painted -- that is, everything beyond it -- so the wash
# emitted at edge k is exactly the SLAB of air between edges[k] and
# edges[k+1], and a stratum ends up under the product of every slab in front
# of it. Transmittance therefore composites correctly with no extra work:
#
#     T(d) = prod over the slabs in front = exp(-d / HAZE_D)
#     a_k  = 1 - exp(-(edges[k] - edges[k+1]) / HAZE_D)
#
# So there is one dial, HAZE_D, the e-folding distance of the air; every
# stratum gets its own wash instead of four of them, which is also what
# takes the visible STEPS out of the distance. At 30 km the old table had
# reached 0.40 and this reaches 0.55, and the far mesh is meant to be nearly
# gone: it is 45 km of Anatolian afternoon.
HAZE_D = 34000.0
HAZE = {
    STRATA_EDGES[k]: 1.0 - math.exp(
        -(STRATA_EDGES[k] - STRATA_EDGES[k + 1]) / HAZE_D)
    for k in range(len(STRATA_EDGES) - 1)
}


def haze_at(dist_m: float) -> float:
    """Cumulative opacity of the air over ground `dist_m` away — the same
    law the strata integrate, for the things that are not strata: the water,
    which is one flat plane and takes its haze from a gradient in screen y,
    and Ida, which is beyond the mesh entirely."""
    return 1.0 - math.exp(-max(0.0, dist_m) / HAZE_D)

PLAIN_BBOX = (39.86, 40.05, 26.1, 26.38)


# ═══════════════════════════════════════════════════════════════════════════
# GROUND COVER — colour says what the ground IS, not how high it is
# ═══════════════════════════════════════════════════════════════════════════
# THE DEFECT. Hypsometric tint is a PLAN-VIEW device: it encodes height as
# colour because in plan you cannot see height. An oblique already shows height
# geometrically, so tinting by height says it twice, and the plate read as a
# flat map draped over terrain. Worse in perspective: quantised bands print as
# a stack of flat terraces -- "topographic strata aren't working here, troy
# looks like it's on a flat table" (John, on an 8x crop of Ilios) -- and once
# the sun arrived they fought the shading, two tonal systems on one surface,
# one stepped and one smooth, with the stepped one winning.
#
# THE ARCHITECTURE. Three channels, each saying one thing:
#     COLOUR  what the ground is        -- the classes below, categorical
#     TONE    where the light falls     -- slope shading + cast shadows,
#                                          continuous, no steps
#     HEIGHT  nothing in colour at all  -- it is in the geometry, and in the
#                                          contour hairlines if they are on
#
# THE CLASSES, and their evidence, come from docs/research/
# GROUND-COVER-TROJAN-PLAIN.md, which is this code's specification. Six classes
# were proposed there; three have a DEM-derivable rule and are drawn:
#
#   WET DELTA / SWAMP   reuse `delta-swamp` -- SRTM 10-15 m, slope < 1.2%,
#                       4-connected to the published bay head. INFERABLE
#                       (Kayan et al. 2003, 384, 389: "a broad deltaic swamp").
#                       Drawn as the blurred, outline-less wash this sheet
#                       already used, NOT as a mesh class: a wetland has no
#                       boundary (TROAD-CARTOGRAPHY.md, third pass, §3), and a
#                       lattice union would have given it a hard one.
#   DRY DELTA FAN       by ELIMINATION inside the `scamandrian-plain` sector:
#                       what is neither ridge nor wet. Kayan 2002, 1003 locates
#                       and describes the surface -- "a sand-covered and dusty
#                       plain... there is no need to look for a battlefield in
#                       the distance" -- but maps no boundary, so the boundary
#                       here is derived, never traced.
#   RIDGE SCRUB / BARE  reuse `relief-sigeion-ridge`, `relief-troy-ridge`,
#                       `relief-rhoiteion-ridge`. Their extents are already cut
#                       from the DEM; re-deriving thresholds would only invent
#                       a second, worse boundary. The vegetation itself is a
#                       stated Mediterranean-Aegean default for thin soil on
#                       exposed limestone, not a Troad finding -- the weakest
#                       claim on the sheet, and the key says so.
#
# TWO CLASSES ARE NOT DRAWN, and naming them is the point:
#
#   RIVERBANK THICKET   elm, willow, tamarisk over lotus, rush and galingale,
#                       Il. 21.350-52, explicitly "about the river's fair
#                       streams". POEM-ONLY, and the Bronze Age channels are
#                       not locatable at all ("with as much as 20 m of alluvium
#                       ... we cannot hope to locate the river channels of
#                       antiquity" -- Kraft, Rapp, Kayan and Luce 2003, 164),
#                       so there is no defensible extent and no defensible
#                       width. It is LETTERED IN THE KEY AND NOT BOUNDED, which
#                       is this project's standing answer when the honest
#                       options are "invent an edge" or "say nothing".
#   SAND BARRIER        a Bronze Age dune belt across the Scamander front is
#                       NOT KNOWABLE and is contradicted four times over (Kayan
#                       1997, 438; 2002, 1002; Kayan et al. 2003, 390; Kraft et
#                       al. 2003b, 164). No beach, dune or strand class exists
#                       in this file, and none may be built from the live
#                       `barrier-bronze` layer's footprint.
#
# A FOURTH FILL IS NOT A CLASS. Everything outside the plain sector and its
# three ridges -- the Troad hinterland, the far country under Ida -- carries
# NO ground-cover claim, because the specification makes none for it. It takes
# one quiet neutral fill and the key says "not classified". Painting it as
# scrub by extending the ridge default would be exactly the fabrication the
# whole exercise is against.
#
# WHERE WATER MEETS THE RULE. The specification's elimination clause also
# excludes water from the dry fan. Here that is discharged by PAINT ORDER
# rather than by the mask -- the sea, the lagoon and the swamp are painted
# over the ground, so no dry-fan claim survives under them -- which is the
# same device this sheet already uses to keep modern river channels out of the
# Bronze Age bay. A mask-based exclusion would have printed a neutral rim
# wherever the cell mask and the drawn waterline disagreed.
COVER_FAN = "fan"          # dry delta fan: the plain the poem fights over
COVER_RIDGE = "ridge"      # ridge scrub / bare slope
COVER_OPEN = "open"        # beyond the sector: no claim
# Painter order within a depth stratum. The classes tile the ground without
# overlap, so this decides nothing but which seam-stroke laps which.
COVER_ORDER = (COVER_OPEN, COVER_RIDGE, COVER_FAN)
COVER_TOKEN = {COVER_FAN: "--pp-cover-fan", COVER_RIDGE: "--pp-cover-ridge",
               COVER_OPEN: "--pp-cover-open"}
# The layers whose geometry is REUSED, never re-derived.
RIDGE_LAYERS = ("relief-sigeion-ridge", "relief-troy-ridge",
                "relief-rhoiteion-ridge")
PLAIN_LAYER = "scamandrian-plain"
SWAMP_LAYER = "delta-swamp"
# CONTOURS ARE THE LAST PIECE OF PLAN-MAP LANGUAGE LEFT ON THE SHEET, and
# whether they belong on an oblique is a real question, not a setting. Draped
# in perspective they read as form lines wrapping the ground, which is craft;
# they are also the one mark left that says "map" rather than "country", and
# with the hypsometric bands gone they are what the eye reads the near
# foreground by, since the back of the Sigeion ridge has nothing else on it.
#   "all"    every level: the full web. The most information, the most map.
#   "index"  10, 30, 110 and 600 m only -- the index rule's own lines. The
#            structural ones survive (the 30 m lobe closing round the citadel;
#            the 10 m the Bronze Age shore is calibrated on) and the web goes.
#   "none"   the panorama with no isolines at all.
#
# THE DEFAULT IS NOW "none" (2026-08-14). Two things changed under it. The
# hypsometric bands went, so nothing on the sheet reads height as colour and
# the isolines stopped being the key to a legend; and the sun arrived, so the
# near foreground the contours were kept for now has slope shading and cast
# shadows on it. What was left was the one mark that still says "plan map" on
# a plate whose whole argument is that it is a COUNTRY seen from a ridge, and
# it says it loudly: 0.75-1.5 px of ink meandering across every landform,
# redundant with the light that already models the same ground.
#
# THE RESERVATION WAS TESTED, NOT INHERITED. The previous lane kept "all"
# because with none Ilios "floats" at 8x -- nothing marked the bluff. It no
# longer holds, and the fix was not the contours: the citadel floated because
# it threw NO SHADOW while every hull and hut on the beach threw one (see
# city_shadow). With the shadow off its own walls the bluff reads at 8x with
# no isoline anywhere near it. All three modes stay on the flag.
CONTOURS = "none"
CONTOUR_MODES = ("all", "index", "none")
# ── smoothing, in low-pass passes (see soften) ───────────────────────────
# One idea, three strengths, because the three lines are three different
# claims. A CONTOUR is a measured line -- the bilinear crossing of the DEM --
# and only its cell-edge kinks are artefact, so it gets the lightest touch that
# takes the angles off. A TONE EDGE is where the quantiser fell and stands for
# nothing, so it can be softened until it reads as a wash. A COVER BOUNDARY is
# derived from a mask the mesh under-resolves, and its staircase risers are a
# whole ring tall in the near field, which needs the heaviest kernel on the
# sheet. Deviation is asserted against the mesh's own resolving power in
# test_panorama_relief.py -- a line smoothed off its ground is the one failure
# mode this device has.
CONTOUR_SOFT = 3
SHADE_SOFT_PASSES = 3
COVER_SOFT = 5
RIVER_SOFT = 2           # corner-cutting passes over the river CENTRELINE, in
                         # lat/lon, before it is draped (see rivers_svg)


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
#
# CURVE C IS A FAMILY, NOT A CONSTANT (2026-08-14). The near-ground rate
# C_A = ve(0) and the decay scale C_L are the two dials; the floor C_F is
# never a dial, it is SOLVED so that exaggerate(IDA_M) == IDA_M. Raising the
# near rate therefore lifts the plain, the bluff, the camp ridge and the
# headlands -- everything this sheet is about, all of it under 50 m -- and
# leaves the horizon where it is.
#
# The Ida constraint puts a HARD CEILING on the near rate, and it is worth
# stating because it is the reason this dial cannot simply be turned up:
# solving f = (I - A*K)/(I - K) with K = L*(1 - exp(-I/L)) gives f <= 0 once
# A >= I/K, and a non-positive floor is a non-monotonic curve. At L = 150 the
# ceiling is 11.83x; at L = 250 it is 7.10x; at L = 100, 17.74x. A longer
# taper spends more of Ida's budget low down and so allows LESS lift at the
# shore, which is the opposite of the intuition.
CURVE = "C"

C_A = 4.0             # ve(0): the exaggeration RATE at the shoreline.
C_L = 150.0           # decay scale: the excess over the floor halves at
                      # L*ln2 = 104 m, which is where the plain sheet's own
                      # p80 (107 m) puts the plain's edge and the ridges'
                      # start -- the taper follows the terrain's own break.
IDA_M = 1774.0        # published Kaz Dagi summit (panorama-profile.py:
                      # DEM 1757.4 measured, 1774 published). Curve C's floor
                      # is solved so exaggerate(IDA_M) == IDA_M.
C_F = 0.0             # solved by set_curve() below; never set by hand


def max_near_rate(scale: float = None) -> float:
    """The largest ve(0) for which curve C's solved floor stays positive --
    i.e. the largest near-ground rate compatible with Ida keeping its true
    height. Above it the curve inverts and must not ship."""
    s = C_L if scale is None else scale
    return IDA_M / (s * (1.0 - math.exp(-IDA_M / s)))


def set_curve(near_rate: float, scale: float) -> None:
    """Set curve C's two dials and re-solve the floor. Raises if the pair
    would put the floor at or below zero (a non-monotonic curve)."""
    global C_A, C_L, C_F
    k = scale * (1.0 - math.exp(-IDA_M / scale))
    f = (IDA_M - near_rate * k) / (IDA_M - k)
    if f <= 0.0:
        raise ValueError(
            f"ve(0)={near_rate:g} with scale {scale:g} solves to a floor of "
            f"{f:.4f}: the curve would invert. Ceiling is "
            f"{max_near_rate(scale):.2f}x at this scale.")
    C_A, C_L, C_F = float(near_rate), float(scale), f


set_curve(C_A, C_L)


def ve(e: float, curve: str | None = None) -> float:
    """The exaggeration RATE at real elevation `e` metres: d(apparent)/d(real).
    Strictly positive on every curve, which is what makes exaggerate()
    monotonic."""
    c = curve or CURVE
    if c == "C":
        return C_F + (C_A - C_F) * math.exp(-e / C_L)
    t = min(1.0, max(0.0, (e - 100.0) / 200.0))   # A and B share this rate law
    return 4.0 + t * (1.0 - 4.0)


def exaggerate(e: float, curve: str | None = None) -> float:
    """Apparent height (drawing metres) for a real elevation, = INT(0..e) ve."""
    c = curve or CURVE
    if c == "A":                       # legacy product form; DO NOT SHIP
        return e * ve(e, "A")
    if e <= 0.0:                       # the DEM dips a metre or so below zero
        return ve(0.0, c) * e          # extend at the sea-level rate
    if c == "C":
        return C_F * e + (C_A - C_F) * C_L * (1.0 - math.exp(-e / C_L))
    if e <= 100.0:                     # B, piecewise integral of the rate law
        return 4.0 * e
    if e <= 300.0:
        d = e - 100.0
        return 400.0 + 4.0 * d - 0.0075 * d * d
    return 900.0 + (e - 300.0)


def sun_disclosure() -> str:
    """The light, named. A lit plate that does not say where its sun is has
    turned a measurement into decoration."""
    if not SHADE_STEPS:
        return "No light source; relief carried by the hypsometric ramp alone."
    sh = "with cast shadows" if SHADOW else "slope shading only, no cast shadows"
    return ("Lit by the sun at bearing %.0f°, %.0f° above the horizon — %s, "
            "%s." % (LIGHT_AZ, LIGHT_ALT, SUN_NOTE, sh))


def disclosure(curve: str | None = None) -> str:
    """The cartouche's exaggeration line. It is GENERATED from the live dials,
    so the sheet cannot declare one rate and draw another."""
    c = curve or CURVE
    if c == "A":
        return ("Vertical exaggeration 4× at and under 100 m, tapering to 1× "
                "above 300 m; built heights TRUE.")
    if c == "B":
        return ("Vertical exaggeration 4× at and under 100 m, easing to 1× "
                "above 300 m — applied as a rate and integrated, so higher "
                "ground always draws higher. Built heights TRUE.")
    return ("Vertical exaggeration %.3g× at the shore, easing to %.2f× on the "
            "high ground — applied as a rate, so higher ground always draws "
            "higher. Built heights TRUE." % (C_A, C_F))


# ── slope shading ────────────────────────────────────────────────────────
# THE PLATE HAD NO LIGHT IN IT. Flat colour bands and hairline contours are a
# PLAN sheet's answer to relief, and on a plan they are the right one; on an
# OBLIQUE they remove the cue the eye actually reads height from, which is
# which face is lit and which is turned away. Correct geometry with no light
# reads as a paper map bent into perspective, and that is what this was.
#
# TROAD-CARTOGRAPHY.md's ban does not reach this, and the reasons matter:
#   - The general rule it states is about DISCRETE MARKS -- "every treatment
#     built out of discrete marks has a magnification at which it stops being
#     tone." That is an argument against hachures and stipple. Continuous tone
#     has no such magnification; this is the same drawing at every zoom.
#   - Its hillshade paragraph adds two more. The MULTISTABLE-INVERSION
#     objection is a plan-sheet objection: on a plan, nothing but the shading
#     says which way is up, so the reading can flip. Here perspective, the
#     horizon, the ships and the depth strata all fix the surface's
#     orientation before the shading is consulted, and it cannot flip.
#   - The other is the one that would really have bound us: "a shaded relief
#     is a raster, and this project's plates emit no colour that is not a
#     var() token... a baked PNG cannot be re-themed, and an SVG filter's
#     light source cannot be either." That is correct and is honoured, not
#     dodged: this shading is VECTOR, it is unioned lattice polygons like the
#     bands, and every tone it uses is --pp-shade or --pp-lit at a computed
#     opacity. Both themes re-key from the stylesheet exactly as before, and
#     there is no raster and no filter anywhere in it.
#
# LIGHT_AZ is the compass bearing the light COMES FROM; LIGHT_ALT its height
# above the horizon.
#
# WHY NORTH-WEST. It is the plan-sheet convention, and on this camera it is
# also the right light for the scene: the heading is 104°, so a light from
# 315° stands over the viewer's LEFT SHOULDER. Slopes facing the camera are
# lit and slopes falling away from it go dark, so every ridge shows a bright
# near flank and a dark far flank -- ground rising towards you, which is what
# it is. The two alternatives were rendered and are worse. From 14°
# (screen-left) the modelling is too faint to see. From 59° -- the frame's
# upper left, i.e. from BEYOND the scene -- the light is behind the subject:
# near flanks go dark and far flanks light, the plain reads mottled, and the
# multistable inversion the cartography doc warns about arrives by the back
# door. Perspective fixes the surface's orientation, but only if the light
# agrees with it.
#
# A REAL SUN, NOT A CARTOGRAPHER'S LAMP (2026-08-14). This plate is to become
# a lit scene, so its light is a SOLVED SOLAR POSITION for 39.9755 N and not a
# conventional upper-left wash. Every candidate below was computed from
#     sin(alt) = sin(phi) sin(dec) + cos(phi) cos(dec) cos(H)
#     cos(A)   = (sin(dec) - sin(alt) sin(phi)) / (cos(alt) cos(phi))
# and none of them is invented.
#
# THE CAMERA MAKES THIS HARDER THAN IT LOOKS, and the finding is worth stating
# because it contradicts the obvious guess. The heading is 104 deg, ESE. A
# summer AFTERNOON sun at this latitude sits at bearing 281-284 -- which is
# 177-180 deg round from the heading, i.e. DIRECTLY BEHIND THE VIEWER. Every
# shadow then falls straight away from the camera and hides behind the thing
# casting it: the flattest light on the list, and useless. The three suns that
# do rake are:
#
#   76.0 / 11.5   early August, 1 h after sunrise. The poem's own season and
#                 its own hour -- the fighting days open at dawn -- and 28 deg
#                 off the sightline, so shadows come towards the eye and are
#                 fully visible. Most three-dimensional plate of the set.
#                 Costs: near-foreground tone is blotchier than the afternoon
#                 suns, and Troy's own scarp reads softer.
#  260.2 / 11.4   equinox, 1 h before sunset. The most restrained. Lights
#                 Troy's west face, the face the camp looked at, but 156 deg
#                 round is still nearly behind the viewer and the citadel's
#                 shadow hides behind the citadel. Troy barely helped.
#  228.4 /  9.9   winter solstice, 3.5 h after noon.  SHIPPED (John,
#                 2026-08-14).  The best raking angle available at all -- 124
#                 deg off the sightline -- and the ONLY light in which Troy's
#                 bluff reads crisply, because the shadow off its scarp lies
#                 across the frame instead of pointing away down it. The
#                 seasonal match of 76/11.5 does not bind here: this plate
#                 depicts the SIEGE, a ten-year standing condition (ships
#                 drawn up, camp, wall and ditch), not one day's action, so
#                 the season is free and there is no reason to pay for a
#                 seasonally "correct" light with a flatter picture. The
#                 cartouche itself says only what it must -- bearing,
#                 altitude, "a low sun in the afternoon sky" -- and claims no
#                 date; the reasoning above is the log entry, not the label.
#
# Whichever ships, SUN_NOTE ships with it: --shade-az and --shade-alt REFUSE
# to move without --sun-note, because a plate that draws one sun and names
# another is worse than one that names none.
LIGHT_AZ = 228.4
LIGHT_ALT = 9.9
LIGHT_AZ_DEFAULT, LIGHT_ALT_DEFAULT = LIGHT_AZ, LIGHT_ALT
# ── THE TONE IS BUILT UP IN WASHES, NOT CUT INTO STEPS (2026-08-14) ──────
# The step count was pinned at 10 by a measurement that was true of the
# drawing as it then stood: at 14 the near foreground broke into a lattice of
# countable ovals -- fish scales -- and the SVG went 682 -> 776 KB to print
# them. Both halves of that failure come from ONE decision that was never the
# step count's fault: each tone level was drawn as the region where the light
# lands EXACTLY on that step, which makes every level an isolated island with
# two boundaries, and makes the area filter's rescue catastrophic -- a sliver
# dropped at level 7 loses SEVEN TENTHS of its tone and prints as a bright
# bead in the middle of a shadow.
#
# Superlevel sets do not have either property. Level k draws the region where
# the light is at or beyond step k -- {st >= k} -- so the regions NEST, and a
# cell at step 7 is covered by seven washes instead of one. Three things fall
# out at once:
#
#   1. WEIGHT GOES DOWN, not up. An exact-level region is bounded by the
#      contours at k AND k+1; a superlevel region is bounded by the contour
#      at k alone. Every boundary on the sheet was being drawn twice.
#   2. A DROPPED SLIVER COSTS ONE WASH. At 18 steps that is 3% of full tone
#      instead of 70%, so the fish scales have nothing to print with.
#   3. THE RAMP STOPS BEING LINEAR. n washes of alpha a composite to
#      1-(1-a)^n, which is optical density -- the curve a real wash builds,
#      and the curve film and eye both have. Tone compresses in the darks
#      exactly where it should.
#
# Per-wash alpha is solved, not chosen: a = 1 - (1-MAX)^(1/steps), so the
# deepest tone still lands on MAX however many washes it is built from.
#
# RE-MEASURED at 10 / 18 / 26 steps on the shipped frame: at 10 the wash
# banding is still countable on the bay-facing slope under Rhoiteion; at 18
# no band edge can be found anywhere at 1x and the gully system under the
# camp holds; at 26 nothing visible improves and the SVG gains 90 KB. 18.
SHADE_STEPS = 18         # quantisation; 0 turns slope shading off entirely
# ── THE SHADE COMES DOWN AND THE LIGHT GOES UP, and the reason is both
# physical and measured.
#
# PHYSICAL: the sun is at bearing 228 and the camera looks 104, so the light
# is over the reader's right shoulder and this is a FRONT-LIT scene. What a
# raking sun behind the viewer actually produces is bright sunward faces and
# shadows that mostly hide behind their own casters -- not deep shade across
# the near field. And a shadow now has sky in it (see SHADOW_AMBIENT), so the
# tonal budget no longer has to reach total darkness: flat ground in shadow
# sits at 0.61 of full tone and a vertical face in shadow at 0.81.
#
# THE CAP WAS NEVER PHYSICAL, IT WAS A MEASUREMENT ARTEFACT. This dial stood
# at 0.40 with a note recording that 0.50 "looked best" and had been backed
# down because it cost label contrast in a 16-28 px annulus round each label
# anchor. That annulus is not a label's background -- see HALO_W, where the
# whole argument and the re-measured numbers are. With the halo credited (and
# made translucent, so it dims the ground round a letter instead of deleting
# it) the labels stopped moving with the ground at all except one part in
# four, and the tone was free.
#
# MEASURED, on rendered pixels, halo credited, worst of the 44 labels on the
# sheet, at four settings of this dial:
#
#     shade / lit   light   dark
#     0.40 / 0.32    5.15   6.04
#     0.50 / 0.36    5.09   6.05
#     0.62 / 0.36    5.04   6.08
#     0.72 / 0.36    5.00   6.11
#
# The whole range moves the worst label by fifteen HUNDREDTHS of a ratio
# point, and in dark theme it moves the WRONG WAY -- up. That is the finding,
# and it is stronger than the one this pass went looking for: with the halo
# credited the tone is not trading against label contrast at all. (The worst
# label is THE SHIPS, lettered over the hulls, and a hull is not terrain, so
# the shade ramp never touches what it stands on.)
#
# So AA does not pick this number; the DRAWING does. 0.62 is where the bluff
# under Ilios finally carries the weight a 25 m scarp under a 10 degree sun
# ought to have while the deep shade still has landform inside it. 0.72 was
# rendered and looked at and is not visibly better at 1x, and it closes the
# shaded faces further, so the extra tenth buys nothing and costs modelling.
SHADE_MAX = 0.62         # peak opacity of --pp-shade on a slope turned away
LIT_MAX = 0.36           # peak opacity of --pp-lit on a slope facing the light

# ── THE TERMINATOR WAS THE AIRBRUSH ──────────────────────────────────────
# "Bolder, or sharper" (John, 2026-08-14). Tone alone is bolder; what makes a
# drawing SHARP is where the tone changes, and this sheet's light was linear
# in slope from the first step to the last, which spends most of its range on
# the middle -- exactly the gradient an airbrush lays down.
#
# The nested-wash ramp made it worse, and it is worth being precise about
# why. n washes of alpha a composite to 1-(1-a)^n, which is CONCAVE: the
# first washes do most of the work and the last ones almost none. Optical
# density is the right curve for a wash, but it means the deep end of the
# range -- 0.7 of full tone through 1.0 -- is nearly flat, so a face turned
# hard from the light and a face turned harder still print the same, and the
# shaded side of a ridge goes mushy exactly where it should be firmest.
#
# The fix is a gamma on the light BEFORE it is quantised, which is where the
# material gain already lives and for the same reason: shade_raw stays a pure
# function of slope and light. gamma < 1 pushes tone on fast near the
# terminator and then holds, so the lit/shaded boundary reads as a boundary
# and the interior of each side stays open.
#
# RENDERED AND LOOKED AT at 1.00 / 0.85 / 0.78 / 0.70. At 1.00 the far ridges
# are the smudges the complaint was about. At 0.70 every ridge has an edge and
# the plate is bolder than it has ever been, but the mid-distance masses go
# hard all the way round and start to read as cut paper laid on the plain --
# an edge is not the same thing as a silhouette. 0.78 is where the terminator
# is definite and the masses still turn.
SHADE_GAMMA = 0.78

# ── MATERIAL: THE GROUND CLASSES DO NOT TAKE LIGHT ALIKE ─────────────────
# One light field over four ground covers was drawing sand, scrub, limestone
# and waterlogged delta as though they were the same substance with different
# paint on. They are not, and the difference is not a matter of hue:
#
#   the dry fan is pale, dusty and very rough at grain scale, so it
#   backscatters and multiply-scatters hard. Its shadows fill in and its
#   modelling is SOFT -- this is why a sand dune photographs flat at midday
#   and only reads at all near sunset;
#   ridge scrub on thin soil over limestone is broken cover -- rock, bush and
#   bare pan in the same square metre -- so it takes tone HARDER than either
#   pure surface would;
#   ground beyond the sector carries no claim and takes the field as it is.
#
# The gain multiplies the light field, not the geometry: no elevation, no
# slope and no shadow moves, and shade_raw stays a pure function of slope and
# light (the test that pins that still passes, because this is applied over
# the field in shade_field, where the classification exists). What changes is
# how much tone a measured slope is worth on a given substance, which is a
# material property and belongs exactly here.
MATERIAL = {COVER_FAN: 0.76, COVER_OPEN: 1.0, COVER_RIDGE: 1.16}
# A tone region's edge is NOT a measured line -- it is where the quantisation
# happened to fall -- so it is low-passed before it is generalised, and the
# ORDER is the fix (see SHADE_SOFT_PASSES and the note in terrain_svg). The old
# dials generalised at 3.2 px FIRST, which kept every riser corner and threw
# away the treads, and then corner-cut the jagged result: that is where the
# scalloped tone edges came from.
# ── SHADE_SMOOTH WAS THE BIGGEST SMOOTHER ON THE SHEET, by a factor of four
# over the one everybody suspected. Its kernel is a 3x3 with the centre
# doubled, variance 0.6 cells per pass, so five passes is a Gaussian of sigma
# 1.73 MESH CELLS -- and a mesh cell is a ring apart in depth, which at the
# old 110 m floor was 190 m of ground. The DEM's own blur, the thing the
# "too soft and painterly" hunt started on, was sigma 41 m. The tone was
# being generalised over five times the ground the height field was.
#
# Two passes now, and the reason it can come down is that the defect it was
# hired for is being caught by the tools that actually fit it: the MEDIAN
# removes one-cell islands without moving an edge (see SHADE_MEDIAN), the
# area filter drops slivers, and the boundary low-pass takes the lattice out
# of the edges. Smoothing the field was doing none of those jobs well and was
# flattening the gullies to do them. Measured on the shipped frame at 5 / 3 /
# 2 / 1 passes: the ground under the camp is unmodelled at 5 and carries a
# readable gully-and-spur system at 2; at 1 the tone islands the median has
# to filter jump from 3,628 to 5,057 and the near foreground starts to bead.
SHADE_SMOOTH = 2         # box passes over the CONTINUOUS field, in mesh cells
SHADE_SIMPLIFY = 1.1     # px of Douglas-Peucker on a wash edge. It was 0.8
                         # while an edge was the seam between two tones seven
                         # tenths apart; a nested wash edge is one eighteenth
                         # of the tone, so it can be generalised harder, and
                         # that is what pays for nine more of them.
SHADE_MIN_AREA = 140.0   # px^2; below this a tone region is a sliver, not a
                         # slope, and it prints as a bead rather than as tone
# ── THE BLOTCHY FOREGROUND, and why smoothing alone never cured it ────────
# The near ground read as irregular smudges -- "stains rather than landform".
# The previous lane blurred the continuous field and dropped sub-90 px slivers
# and it helped and did not fix it, and the reason is that neither device can
# touch the defect's actual shape. Quantisation happens ON THE LATTICE, so a
# cell whose smoothed value lands a hair over a step boundary becomes a tone
# region ONE CELL BIG. Blurring the field beforehand cannot stop that -- it
# only moves where it happens -- and the area filter cannot catch it in the
# NEAR field, where a single cell is 200-400 px^2 and clears a 90 px^2 bar by
# a factor of four. Rounded, those one-cell regions print as ovals: at the
# foot of the frame they read as fish scales, and raising the step count makes
# it worse, because more steps means more boundaries for the lattice to show
# through.
#
# A MEDIAN OVER THE QUANTISED FIELD is the fix, and it is the right tool for
# a reason worth stating: a median is the filter that removes isolated values
# and one-cell filaments WITHOUT moving an edge, which is exactly the
# difference between this defect and the tone it is sitting in. A single cell
# out of step with all eight of its neighbours cannot survive one pass; a
# genuine slope, which is many cells wide, is untouched. It runs after
# quantisation, where the islands actually exist, and not before it, where
# they do not yet.
#
# MEASURED, on the shipped dials: 6 steps / 5 smoothing passes / 3 median
# passes / 140 px^2 removes the fish-scale beading from the near foreground
# outright and leaves the tone regions broad enough to read as gullies. SIX
# STEPS IS DELIBERATELY UNCHANGED -- the light itself is not this pass's to
# move, and raising the step count made the foreground WORSE for the reason
# above, which is worth knowing before anyone tries it again.
SHADE_MEDIAN = 3         # median passes over the QUANTISED field

# ── CAST SHADOWS ─────────────────────────────────────────────────────────
# Slope shading models a facet; it cannot throw anything. The long shadow off
# Troy's scarp -- the thing that actually makes a 25 m bluff read -- needs an
# OCCLUSION test: can this piece of ground see the sun?
#
# It is the renderer's own floating-horizon cull pointed somewhere else. The
# camera cull marches each screen column near-to-far keeping a running
# silhouette; this marches each SUN-ALIGNED column down-sun keeping a running
# ray height. Same algorithm, different origin -- and the sun is at infinity,
# so its natural lattice is a regular raster rotated to the solar azimuth
# rather than the camera's polar fan.
#
# It runs on the EXAGGERATED surface. Shadows have to belong to the ground as
# DRAWN or they will not sit on it.
#
# The mask becomes drawable geometry for free: the shadow depth joins the
# slope term in one illumination value, which the existing quantise-and-union
# path already turns into filled lattice polygons. No new geometry machinery.
SHADOW = True
SHADOW_STEP = 40.0       # raster pitch, m: the plain grid's own resolving
                         # power, which is now ~41 m (sigma 20.7) and was
                         # ~85 m (sigma 41) before the field stopped being
                         # smoothed for a contour tracer. Finer than the
                         # grid still buys nothing; this rule did not
                         # change, only the number it reads off.
SHADOW_REACH = 16000.0   # radius from the viewpoint, m. Beyond it the ground
                         # comes from the troad z11 sheet at 117 m samples,
                         # where a cast shadow would be fiction; that field
                         # keeps slope shading only.
SHADOW_SOFT_M = 5.0      # metres of ray clearance over which a shadow fades
                         # in, so a grazing edge is a penumbra, not a cut
# ── AND NO BOX BLUR ON TOP OF IT. The mask's raster is 40 m; one box pass
# over it spreads a shadow edge across 40-80 m of ground. The sun's disc is
# half a degree, so the true penumbra of a 25 m scarp at the tip of its own
# 140 m shadow is 1.3 m. The blur was three orders of magnitude of softness
# that nothing outdoors has, laid over the one boundary on this sheet that is
# genuinely a cut. SHADOW_SOFT_M already models the grazing edge, where the
# ray clears the ground by little and the shadow really does fade.
SHADOW_BLUR = 0          # box passes over the mask, in raster cells
# ── A SHADOW IS NOT A HOLE (2026-08-14) ──────────────────────────────────
# Ground that cannot see the sun was given illumination ZERO, which lands it
# at the bottom step whatever it is doing -- so every cast shadow on the
# plate was one flat black shape with no landform inside it, and the long
# shadow off Troy's scarp, the whole point of having cast shadows at all,
# fell across a gully system and erased it.
#
# Nothing outdoors is lit by the sun alone. The sky is a 2π source of its own
# and it is what fills a shadow; a surface tilted away from the zenith sees
# less of it, so the sky term is the surface's own SKY VIEW FACTOR, which for
# a plane is (1 + nz)/2 -- 1 on flat ground, 0.5 on a vertical face. That is
# the whole model and it costs one term:
#
#     illum = max(0, N.L) * sunlit + AMBIENT * (1 + nz) / 2
#
# and the datum flat ground is measured against gains the same ambient, so
# level ground in full sun still takes no wash at all.
#
# 0.11 is a defensible clear-afternoon diffuse fraction and it is also what
# the drawing wants: flat ground in shadow lands at 0.61 of full tone and a
# vertical face in shadow at 0.82, so a shadow now has a floor, a ceiling and
# everything between. The colour does the rest -- --pp-shade went cool
# because the light filling a shadow is the blue hemisphere, not the sun.
SHADOW_AMBIENT = 0.11
OBJ_SHADOW = True        # hulls and huts throw their own, at TRUE heights
LIGHT = (0.0, 0.0, 1.0)  # set by set_light()


SUN_H = (0.0, 0.0)       # down-sun horizontal unit vector; set by set_light()
# The solar solution the default light came from, named in the cartouche.
# It MUST be changed with the light -- a plate that draws one sun and names
# another is worse than one that names none.
SUN_NOTE = "a low sun in the afternoon sky"


def set_light(az_deg: float, alt_deg: float) -> None:
    """Unit vector toward the light, in (east, north, up), and the horizontal
    unit vector shadows travel along, which is its opposite."""
    global LIGHT_AZ, LIGHT_ALT, LIGHT, SUN_H
    LIGHT_AZ, LIGHT_ALT = float(az_deg), float(alt_deg)
    a, h = math.radians(LIGHT_AZ), math.radians(LIGHT_ALT)
    LIGHT = (math.sin(a) * math.cos(h), math.cos(a) * math.cos(h), math.sin(h))
    SUN_H = (-math.sin(a), -math.cos(a))


set_light(LIGHT_AZ, LIGHT_ALT)


class ShadowField:
    """Which ground can see the sun, over a sun-aligned raster.

    Axes: `a` runs DOWN-sun (the way shadows travel), `b` across it. One pass
    per across-sun column, keeping the running height of the sun ray -- the
    floating-horizon cull, run from the sun.

    `at(e, n)` returns visibility in [0, 1]: 1 in full sun, 0 in full shadow,
    and a bilinear blend at the penumbra."""

    def __init__(self, terr, az_deg, alt_deg, step=None, reach=None):
        step = SHADOW_STEP if step is None else step
        reach = SHADOW_REACH if reach is None else reach
        th = math.radians(az_deg)
        sx, sy = math.sin(th), math.cos(th)          # toward the sun
        self.ax, self.ay = -sx, -sy                  # down-sun
        self.bx, self.by = -sy, sx                   # across
        self.step = step
        self.m = math.tan(math.radians(alt_deg))     # ray fall per metre
        # a square in the rotated frame is enough: the reach is a radius
        self.half = reach
        n = int(2.0 * reach / step) + 1
        self.n = n
        lat0, lon0 = VIEWPOINT
        dlat = 1.0 / 111132.0
        dlon = 1.0 / (111320.0 * math.cos(math.radians(lat0)))
        # elevations, exaggerated, over the raster
        z = [[0.0] * n for _ in range(n)]
        for q in range(n):
            bq = -reach + q * step
            for p in range(n):
                ap = -reach + p * step
                e = ap * self.ax + bq * self.bx
                nn = ap * self.ay + bq * self.by
                z[q][p] = exaggerate(terr.elev(lat0 + nn * dlat, lon0 + e * dlon))
        # the sweep: one running ray height per across-sun column
        sh = [[0.0] * n for _ in range(n)]
        fall = self.m * step
        for q in range(n):
            row = z[q]
            out = sh[q]
            ray = -1e18
            for p in range(n):
                ray -= fall
                h = row[p]
                if h >= ray:
                    ray = h
                else:
                    out[p] = min(1.0, (ray - h) / SHADOW_SOFT_M)
        for _ in range(max(0, SHADOW_BLUR)):
            sh = _box_blur(sh, n)
        self.vis = [[1.0 - v for v in row] for row in sh]

    def at(self, e, nn):
        fp = (e * self.ax + nn * self.ay + self.half) / self.step
        fq = (e * self.bx + nn * self.by + self.half) / self.step
        if fp < 0 or fq < 0 or fp > self.n - 1.001 or fq > self.n - 1.001:
            return 1.0
        p0, q0 = int(fp), int(fq)
        tx, ty = fp - p0, fq - q0
        v = self.vis
        top = v[q0][p0] + (v[q0][p0 + 1] - v[q0][p0]) * tx
        bot = v[q0 + 1][p0] + (v[q0 + 1][p0 + 1] - v[q0 + 1][p0]) * tx
        return top + (bot - top) * ty


def median_lattice(q, passes):
    """Median-filter a quantised field over the (i, j) lattice.

    See SHADE_MEDIAN. Returns the filtered field and how many cells the FIRST
    pass moved, which is the island count: on a field that is already locally
    consistent a median moves nothing at all."""
    islands = 0
    for p in range(max(0, passes)):
        nxt = {}
        for (i, j), v in q.items():
            vals = [v]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = q.get((i + di, j + dj))
                if n is not None:
                    vals.append(n)
            vals.sort()
            m = vals[len(vals) // 2]
            if p == 0 and m != v:
                islands += 1
            nxt[(i, j)] = m
        q = nxt
    return q, islands


def _box_blur(g, n):
    out = [[0.0] * n for _ in range(n)]
    for q in range(n):
        row, o = g[q], out[q]
        for p in range(n):
            a = row[p - 1] if p else row[0]
            b = row[p + 1] if p + 1 < n else row[n - 1]
            o[p] = (a + row[p] * 2.0 + b) * 0.25
    fin = [[0.0] * n for _ in range(n)]
    for q in range(n):
        up = out[q - 1] if q else out[0]
        dn = out[q + 1] if q + 1 < n else out[n - 1]
        cu, fq = out[q], fin[q]
        for p in range(n):
            fq[p] = (up[p] + cu[p] * 2.0 + dn[p]) * 0.25
    return fin


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
        step = max(2.5, r * 0.004) if r < RING_NEAR_DETAIL else max(6.0, r * 0.008)
        want = RING_PX_NEAR if r < RING_NEAR_DETAIL else RING_PX
        nr = r + step
        while nr < RANGE_FAR and (y0 - flat_y(nr)) < want:
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
    def __init__(self, plain_grid, pitch=None):
        self.theta = math.radians(HEADING_DEG)
        self.e = -SETBACK * math.sin(self.theta)
        self.n = -SETBACK * math.cos(self.theta)
        self.z = ALT
        if pitch is not None:
            # a camera given its pitch and no DEM to read. The sky, the air
            # and the two water ramps are functions of the FRAME and not of
            # the ground under it, so they can be tested without loading
            # nine million elevation samples to find out where to point.
            self.pitch = pitch
        else:
            far_lat, far_lon = pp._dest_point(VIEWPOINT, HEADING_DEG, 9500.0)
            far_e, far_n = pp._flat_m((far_lat, far_lon), *VIEWPOINT)
            far_z = exaggerate(pp.bilinear_elev(plain_grid, far_lat, far_lon))
            view_z = exaggerate(pp.bilinear_elev(plain_grid, *VIEWPOINT))
            near_angle = math.atan2(ALT - view_z, SETBACK)
            far_angle = math.atan2(
                ALT - far_z, math.hypot(far_e - self.e, far_n - self.n))
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
        # The PANORAMA's field, not the contour product's: 2+1 box passes
        # (sigma 20.7 m) against the tracing chain's 10+2 (sigma 41.4 m).
        # A shaded surface's tone IS the grid's derivative, so generalising
        # the grid generalises the picture; a traced contour wants the
        # opposite. Measurements in prep-terrain-contours.py's `panorama_blur`
        # comment -- and the headline is that the old blur was cheap to lose
        # (1.14 m RMS of height, 13% of the slope) because SRTM has nothing
        # under ~200 m to give and no noise down there either.
        self.plain, _, _ = pp.load_panorama_grid()
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
        """Nine-point stencil at a radius that grows with range.

        HALF ITS REASON HAS EXPIRED. It was written for two: that a flat
        plateau straddling a hypsometric level printed as a rectilinear
        terrace, and that generalising far ground harder than near ground is
        what a draughtsman does. The first died with the hypsometric bands
        (2026-08-14, "colour says what the ground is, not how high it is") --
        there are no band edges left to terrace. The second still stands, and
        is why the stencil stays and why its radius still grows with range.
        What comes down is the NEAR FLOOR: see MESH_STENCIL_M."""
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


def poly_area(pts) -> float:
    """Signed shoelace area in square screen units."""
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def winding_sign(poly) -> float:
    """WHICH WAY IS IN. The polygon's own shoelace sign, which answers it
    locally everywhere — concavities, spits and all — where "toward the
    centroid" only answers it on a convex body."""
    return 1.0 if poly_area(poly) > 0 else -1.0


def inset(poly, sgn, dist):
    """One inward offset of a closed screen polygon. `dist` is either px or a
    callable (x, y) -> px, so an offset can hold a constant width IN GROUND
    and shrink with distance the way the ground it measures does.

    Segments that invert — where the offset has swallowed a concavity
    narrower than itself — are dropped rather than folded back."""
    n = len(poly)
    off = []
    for i in range(n):
        x0, y0 = poly[(i - 1) % n]
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        tx, ty = x2 - x0, y2 - y0
        L = math.hypot(tx, ty) or 1e-9
        nx, ny = sgn * -ty / L, sgn * tx / L
        w = dist(x1, y1) if callable(dist) else dist
        off.append((x1 + nx * w, y1 + ny * w, tx / L, ty / L))
    keep = []
    for i in range(len(off)):
        ax, ay, tx, ty = off[i]
        bx, by, _, _ = off[(i + 1) % len(off)]
        if (bx - ax) * tx + (by - ay) * ty >= 0:
            keep.append((ax, ay))
    return keep


def hazed(svg: str) -> str:
    """Lay the air over marks that are painted after the strata have already
    laid theirs down. The gradient is #pp-air — the same Beer-Lambert law,
    read off the z=0 plane by screen y — so a mark drawn out of depth order
    still recedes with everything at its distance."""
    return svg + "".join(f'<path d="{d}" fill="url(#pp-air)"/>'
                         for d in re.findall(r'\sd="([^"]+)"', svg))


def plane_scale(cam):
    """r -> screen px per ground metre measured ALONG the line of sight on
    the z=0 plane. Differentiated from the camera by projecting two points
    either side of r, so it carries the real pitch and setback and not a
    small-angle formula."""
    s, c = math.sin(cam.theta), math.cos(cam.theta)

    def at(r):
        r = max(150.0, r)
        a = cam.project(cam.e + s * r * 0.995, cam.n + c * r * 0.995, 0.0)
        b = cam.project(cam.e + s * r * 1.005, cam.n + c * r * 1.005, 0.0)
        if not a or not b:
            return 0.0
        return abs(a[1] - b[1]) / (r * 0.01)
    return at


def plane_depth(cam, n=72):
    """y -> range on the z=0 plane, as a lookup. The inverse of the mapping
    plane_ramp uses, and exact for the same reason: image y on a horizontal
    plane is a function of axial depth alone."""
    tab = []
    for k in range(n + 1):
        r = 90.0 * (90000.0 / 90.0) ** (k / n)
        p = cam.project(cam.e + math.sin(cam.theta) * r,
                        cam.n + math.cos(cam.theta) * r, 0.0)
        if p:
            tab.append((p[1], r))
    tab.sort()

    def at(y):
        if y <= tab[0][0]:
            return tab[0][1]
        if y >= tab[-1][0]:
            return tab[-1][1]
        lo, hi = 0, len(tab) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if tab[mid][0] <= y:
                lo = mid
            else:
                hi = mid
        y0, r0 = tab[lo]
        y1, r1 = tab[hi]
        t = (y - y0) / (y1 - y0 or 1e-9)
        return r0 + t * (r1 - r0)
    return at


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


# ── the low-pass, and why corner-cutting was never going to do it ────────
# EVERY LINE ON THIS SHEET THAT COMES OFF THE MESH IS A STAIRCASE. A union
# boundary walks lattice edges; a marching-squares contour turns at every cell
# it crosses; a tone region's edge is where the quantiser happened to fall.
# TROAD-CARTOGRAPHY.md's third pass settled the principle for the coastline --
# "every measured line is now drawn as a curve, not just relief", and a facet
# asserts a precision the data does not have -- and the coastline got chaikin()
# and nothing else on the sheet did.
#
# CHAIKIN ALONE IS NOT ENOUGH, and the reason is worth stating because it cost
# a pass to find. Corner-cutting converges to the quadratic B-spline of its
# control polygon: it rounds a riser and then STOPS, whatever the pass count,
# leaving about half the step standing. That is fine for a shoreline whose
# facets are a pixel or two. It is useless against the near-foreground cover
# boundary, whose risers are ONE RING TALL -- 37 px on the shipped frame,
# measured -- because half of 37 px is still a sawtooth.
#
# A REPEATED NEIGHBOUR AVERAGE is the filter that actually fits the defect. It
# is a true low-pass: a one-vertex spike dies outright, a straight run is a
# FIXED POINT (which is what keeps a stratum seam and the neatline edge exactly
# where they were), and the pass count buys real attenuation instead of
# converging. The +lam/-mu alternation is Taubin's: plain Laplacian smoothing
# shrinks a closed loop toward its centroid a little on every pass, and a
# five-cell tone island would have shrunk into nothing.
SOFT_LAM = 0.55
SOFT_MU = -0.58


def soften(pts, passes=2, closed=True):
    """Taubin low-pass along a polyline. Endpoints of an OPEN line are pinned
    -- they are where the geometry was cut, not where the ground turns, which
    is the same exemption the cartography doc gives the neatline."""
    if passes <= 0 or len(pts) < (4 if closed else 3):
        return pts
    for p in range(2 * passes):
        w = SOFT_LAM if p % 2 == 0 else SOFT_MU
        n = len(pts)
        out = []
        for i in range(n):
            if not closed and (i == 0 or i == n - 1):
                out.append(pts[i])
                continue
            (ax, ay) = pts[(i - 1) % n]
            (bx, by) = pts[i]
            (cx, cy) = pts[(i + 1) % n]
            out.append((bx + w * ((ax + cx) * 0.5 - bx),
                        by + w * ((ay + cy) * 0.5 - by)))
        pts = out
    return pts


def max_deviation(a, b):
    """How far the low-pass moved the line, worst vertex, in the line's own
    units. soften() is index-preserving -- vertex i of the curve is vertex i of
    the polyline, moved -- so the honest measure is the pairwise displacement
    and not a nearest-point search, which would flatter the result by sliding
    along the curve. The simplify() that follows is bounded by its own
    tolerance and adds at most that.

    THE GATE: a smoothed line that no longer follows the ground it was cut from
    is a worse drawing than the facets it replaced."""
    return max((math.hypot(p[0] - q[0], p[1] - q[1])
                for p, q in zip(a, b)), default=0.0)


def chain_segments(segs):
    """Marching-squares segments -> polylines.

    THE CONTOURS WERE NEVER LINES. Each cell that a level crossed emitted its
    own two-point `M…l…`, so a hairline was a soup of disconnected facets:
    nothing to smooth, sharp angles at every cell edge, and the corner of one
    facet meeting the corner of the next is exactly what "just a bunch of
    straight lines forming sharp angles" describes.

    `segs` is [((key_a, pt_a), (key_b, pt_b))], where the key is the LATTICE
    EDGE the crossing sits on -- the pair of nodes it lies between. Chaining on
    the edge identity rather than on the coordinate is exact: the same crossing
    computed from either of the two cells that share the edge differs in the
    last bit of the float, and a coordinate-keyed chain drops those joins.

    Returns [(points, closed)].
    """
    adj: dict = {}
    for idx, (a, b) in enumerate(segs):
        adj.setdefault(a[0], []).append(idx)
        adj.setdefault(b[0], []).append(idx)
    used = [False] * len(segs)
    # Open ends first: starting a walk in the middle of an open line would cut
    # it in two and leave a corner the smoothing then pins.
    order = [k for k, v in adj.items() if len(v) == 1] + list(adj)
    lines = []
    for k0 in order:
        for idx in adj.get(k0, ()):
            if used[idx]:
                continue
            k, i = k0, idx
            a, b = segs[i]
            line = [a[1] if a[0] == k else b[1]]
            while True:
                used[i] = True
                a, b = segs[i]
                nk, npt = (b[0], b[1]) if a[0] == k else (a[0], a[1])
                line.append(npt)
                nxt = next((j for j in adj.get(nk, ()) if not used[j]), None)
                if nxt is None:
                    break
                k, i = nk, nxt
            if len(line) < 2:
                continue
            shut = (nk == k0 and len(line) > 3)
            lines.append((line[:-1] if shut else line, shut))
    return lines


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


class Mask:
    """A lat/lon polygon with a bounding box, tested once per visible mesh
    cell -- some sixty thousand times per mask. The box is the whole
    optimisation and it earns its keep: most of this plate's mesh lies outside
    every mask, and a box test rejects those in four comparisons."""

    __slots__ = ("poly", "lat0", "lat1", "lon0", "lon1")

    def __init__(self, poly_latlon):
        self.poly = [(p[1], p[0]) for p in poly_latlon]      # (lon, lat)
        lats = [p[0] for p in poly_latlon]
        lons = [p[1] for p in poly_latlon]
        self.lat0, self.lat1 = min(lats), max(lats)
        self.lon0, self.lon1 = min(lons), max(lons)

    def has(self, lat, lon):
        if not (self.lat0 <= lat <= self.lat1
                and self.lon0 <= lon <= self.lon1):
            return False
        return point_in_poly(lon, lat, self.poly)


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
def _hull2d(pts):
    """Convex hull, monotone chain. Small inputs only -- 8 to 20 points."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        h: list = []
        for p in ps:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h

    lo = half(pts)
    up = half(list(reversed(pts)))
    return lo[:-1] + up[:-1]


def sun_offset(h: float) -> tuple[float, float]:
    """How far down-sun a point `h` metres up throws its shadow, in metres of
    ground. A TRUE height gives a true length -- the same discipline built_h()
    keeps for the objects themselves."""
    if LIGHT_ALT <= 0.5:
        return (0.0, 0.0)
    L = h / math.tan(math.radians(LIGHT_ALT))
    return (SUN_H[0] * L, SUN_H[1] * L)


def object_shadow(cam, terr, lat, lon, bearing, silhouette, drape=False):
    """The shadow one built object throws on the ground.

    `silhouette` is [((u, v), height)] in the object's own frame: the points
    whose shadows bound the figure. Each contributes its foot and its shadow
    point, and the shadow is their convex hull -- exact for a convex solid,
    which a hull and a gabled hut both are.

    It is laid FLAT on the ground under the object, not draped down-slope: at
    the camp's 2-3 km a hull's shadow is 11 m long and the beach falls less
    than a metre across it. `drape` lifts that simplification for objects big
    enough to need it -- Ilios's shadow is 90 m long and runs off the edge of
    the spur, where a flat lay would have floated 20 m above the ground."""
    if not OBJ_SHADOW or LIGHT_ALT <= 0.5:
        return ""
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)
    vx, vy = math.cos(th), -math.sin(th)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)
    world = []
    for (u, v), h in silhouette:
        e = e0 + u * ux + v * vx
        n = n0 + u * uy + v * vy
        world.append((e, n))
        dx, dy = sun_offset(h)
        world.append((e + dx, n + dy))
    mlat = 1.0 / 111132.0
    mlon = 1.0 / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
    scr = []
    for e, n in _hull2d(world):
        gz = terr.elev(VIEWPOINT[0] + n * mlat,
                       VIEWPOINT[1] + e * mlon) if drape else g
        p = cam.project(e, n, built_h(0.05, gz))
        if p:
            scr.append((p[0], p[1]))
    if len(scr) < 3:
        return ""
    return f'<path d="{rel_poly(scr)}" class="pp-objshadow"/>'


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


ROOFS = [(-0.62, 0.30, 8.0, 26), (-0.34, 0.46, 10.5, 30), (-0.02, 0.34, 9.0, 26),
         (0.28, 0.50, 12.5, 32), (0.58, 0.30, 8.5, 26), (-0.20, 0.10, 11.0, 30),
         (0.34, 0.06, 9.5, 26)]


def city(cam, terr, centre, radius=105.0, wall_h=6.0, tower_h=9.5):
    """Ilios on its spur, as a massing: one wall face, one crest, the great
    tower over the plain, a stepped skyline of roofs behind. At 1x this is a
    50 px mark; the DETAILED city is a separate artifact, and this plate does
    not pretend otherwise.

    IT THREW NO SHADOW, AND THAT IS WHY IT FLOATED. "Troy looks like it's
    floating" (John, on the 8x crop). Every one of the 459 hulls and 270 huts
    on the beach is pinned to the ground by a true-length shadow of its own;
    the citadel -- the biggest built thing in the frame and the one the plate
    is named for -- was excluded from that pass and read as a sticker laid on
    the surface. Nothing about the ground under it was wrong; there was simply
    no mark tying it down.

    It is the same machinery, at the same true heights, with two differences
    the size forces. The shadow is DRAPED, not laid flat: at 9.9 deg the wall
    throws 34 m and the great tower 87, which runs off the edge of the spur,
    and a flat lay would have floated the far end of it 20 m over the plain.
    And it takes the ROOFS into its silhouette as well as the wall ring,
    because a 12.5 m ridge inside a 6 m wall throws 72 m and reaches well past
    the wall's own shadow -- the citadel's shadow is longer than the citadel.

    THE WALL IS ALSO MODELLED NOW. A flat ellipse ring in perspective reads as
    a plan-view oval however well it is grounded; a low raking sun gives it a
    sunward face and a far face, which is the same cue the huts have had all
    along and is what makes it a thing standing on a spur."""
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
    # ── the shadow, first, so everything else stands on it ───────────────
    sil = [((radius * 0.86 * math.sin(2 * math.pi * k / 20),
             radius * math.cos(2 * math.pi * k / 20)), wall_h)
           for k in range(20)]
    sil += [((-9.0, -radius * 1.04), tower_h * 1.6),
            ((9.0, -radius * 1.04), tower_h * 1.6)]
    sil += [((radius * fy, radius * fx), hh) for fx, fy, hh, _ in ROOFS]
    out = [object_shadow(cam, terr, lat0, lon0, 0.0, sil, drape=True)]
    for fx, fy, hh, wd in ROOFS:
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
    # THE SUNWARD FACE AND THE FAR FACE. The wall's outward normal at ring
    # index k, for the ellipse it is drawn on, is (cos/a, sin/b) in (east,
    # north); dotted with the horizontal direction of the light it says which
    # stretch of the drawn face the sun is on. The washes are the terrain's own
    # --pp-lit and --pp-shade at the terrain's own peak opacities, so the
    # citadel is lit by the same sun as the ground it stands on and re-keys
    # with the theme like everything else.
    n_ = len(top)
    sunward = (math.sin(math.radians(LIGHT_AZ)), math.cos(math.radians(LIGHT_AZ)))
    face = []
    for k in near:
        a = 2 * math.pi * k / n_
        nx, ny = math.cos(a) / radius, math.sin(a) / (radius * 0.86)
        face.append(nx * sunward[0] + ny * sunward[1] > 0.0)
    run = 0
    while run < len(near) and SHADE_STEPS:
        end = run
        while end + 1 < len(near) and face[end + 1] == face[run]:
            end += 1
        arc = near[run:end + 2]           # one index of overlap closes the seam
        if len(arc) > 1:
            cls = "pp-wall-lit" if face[run] else "pp-wall-shade"
            op = LIT_MAX if face[run] else SHADE_MAX
            out.append('<path class="%s" fill-opacity="%.3f" d="%s"/>' % (
                cls, op, rel_poly([top[k] for k in arc]
                                  + [base[k] for k in reversed(arc)])))
        run = end + 1
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
# DARK THEME IS A DIFFERENT LIGHT, NOT AN INVERTED ONE (2026-08-14). --text
# and --text-mid are ink -- they are SUPPOSED to swap from dark-on-light to
# light-on-dark, the same as a page of type does. --plate-river and
# --plate-contour are not ink; they are the water and the isolines of actual
# ground, and ground does not swap which parts of it are darker just because
# the sun went down. --plate-river inverted anyway (a pale ice-blue ribbon,
# the brightest thing on the plate) and so did --plate-contour (a pale gold
# web fighting the labels for attention). Both are now their own dark-theme
# values, chosen to stay DARKER than every relief band they cross in that
# theme, exactly as they are in daylight -- water reads as water, contours
# read as a quiet line, in both themes.
#
# THE GROUND-COVER TOKENS INHERIT THAT RULE, and it is what fixes the terraces.
# The twelve-step relief ramp spanned 2.50x in luminance, so every band edge
# was a tonal step and in perspective a stack of them read as flat tables. The
# four cover values span 1.24x in light and 1.32x in dark: they are separated
# by HUE, not by value, so a class boundary is a change of ground and not a
# step in the light. The rank order is identical in both themes -- dry fan
# brightest, then unclassified ground, then ridge, then the wet delta darkest,
# which is also the order they take in life -- because dark theme is a
# different light, not an inverted one.
#
# WARMTH IS BOUGHT IN CHROMA, NOT IN VALUE (2026-08-14). Killing the terraces
# left the plate sage-and-cream where the Troad is sand and ochre, and the
# obvious repair -- open the value range back up -- is the one move that is not
# available, for a reason worth writing down: --text-mid must hold 4.5:1 on
# every class, which in light theme puts a FLOOR of L=0.539 under all four, and
# the spread test puts a ceiling of 1.45x over them. Between a floor and a
# ceiling there is no room to be warmer by being darker.
#
# There is a great deal of room to be warmer by being MORE SATURATED, and that
# is free -- "this is digital, not print. color is free" (John). Every class
# keeps the luminance its constraints allow and roughly doubles its chroma:
# 0.19 -> 0.32 on the fan, 0.10 -> 0.19 on unclassified ground, 0.14 -> 0.24 on
# the ridge, 0.17 -> 0.29 on the wet delta, with dark theme moved further still
# because its ink is looser. The hues are what the classes are: warm sand at
# 41 deg for the dusty fan, a quieter buff at 32 for the ground that carries no
# claim, olive at 54 for scrub on limestone, and 92 for the green delta.
#
# --pp-cover-wet is the wash's own token, painted at 0.55 over the fan beneath
# it; the composite is what the reader sees and what the key swatch draws, and
# it is the composite the contrast tests measure.
#
# --pp-ida-mass and --pp-tumulus are NOT ground cover. They kept the exact
# values they had as relief-12 and relief-9 when the ramp was deleted, because
# neither is terrain the classification speaks for: one is the mountain beyond
# the mesh, the other a built mound.
# ── AIR, SKY AND WATER (2026-08-14, the realism pass) ────────────────────
# Five new families, and every one of them is a physical quantity the plate
# was drawing as a constant.
#
# --pp-haze is what distance is made of. It was --page-bg, a NEUTRAL grey,
# which makes the far plain recede toward paper rather than toward air.
# Aerial perspective is Rayleigh scattering: the extinguished light is
# replaced by scattered SKYLIGHT, which is blue, so the distance goes cool
# and pale, not grey and pale. The token is therefore a pale cool blue in
# daylight -- and in dark theme a DARK cool blue, because a night landscape
# fades toward the dark sky behind it, not toward a light one. That is also
# what keeps the labels legal: the far ground moves AWAY from the ink in
# both themes, never toward it.
#
# --pp-sky-hi / --pp-sky-lo are the two ends of the sky. A real sky under a
# low sun is dark and saturated at the zenith and pale and warm at the
# horizon, because the horizon is five to ten air masses of forward-scattered
# light. --pp-sky-lo is deliberately CLOSE to --pp-haze: the horizon sky and
# the colour distance resolves to must agree, or the far ground floats
# instead of dissolving.
#
# --pp-water-far is the far bay. Water at grazing incidence is a mirror
# (Fresnel: ~2% reflectance looking straight down, >50% at 10 deg), so the
# far water shows the SKY and the near water shows its own body colour.
# --plate-lagoon and --scene-map-sea keep their measured values and stay the
# NEAR end of that ramp, because the lagoon/land fill pair is a pinned
# contrast fact (see test_the_marks_this_pass_moved_clear_wcag_1_4_11).
#
# --pp-shade GOES COOL. It was #2A1E10, a warm brown-black, which is the one
# thing an outdoor shadow is not: the sun is warm and everything it does not
# reach is lit by the blue hemisphere instead. Warm light, cool shadow is the
# oldest observation in landscape painting and it is also just the spectrum.
# The value barely moves (L 0.0146 -> 0.0111 in light, 0.0023 -> 0.0016 in
# dark), so every ordering the tests pin is untouched.
TOKENS = {
    "light": """
  --page-bg:#E7E7E9; --text:#241827; --text-mid:#5B4C58;
  --scene-map-label-halo:#F8F7F3; --scene-map-coast:#565060;
  --plate-lagoon:#87AEB8; --scene-map-sea:#9BBFD6; --plate-contour:#5A4A32;
  --pp-shade:#181A2C; --pp-lit:#FFFAEB;
  --plate-masonry:#A87263; --plate-river:#1A4C6A;
  --pp-hull:#3A2C3C; --pp-hull-side:#1B1220; --pp-hull-edge:#140D18;
  --pp-cover-fan:#FAD391; --pp-cover-open:#E0CDBA; --pp-cover-ridge:#CDCD83;
  --pp-cover-wet:#94C472;
  --pp-ida-mass:#AF9164; --pp-tumulus:#CAB083;
  --pp-haze:#CBD9E4; --pp-sky-hi:#93B4D2; --pp-sky-lo:#E1DDD2;
  --pp-water-far:#DCE6EC; --pp-water-shoal:#CFE0D8;
""",
    "dark": """
  --page-bg:#181120; --text:#EDE6E8; --text-mid:#B7A9B4;
  --scene-map-label-halo:#17131C; --scene-map-coast:#8FA3AE;
  --plate-lagoon:#0A2430; --scene-map-sea:#0A1C2A; --plate-contour:#332818;
  --pp-shade:#03050E; --pp-lit:#F2E4C4;
  --plate-masonry:#A8846F; --plate-river:#123A4A;
  --pp-hull:#241C2A; --pp-hull-side:#120C16; --pp-hull-edge:#C3B49E;
  --pp-cover-fan:#513B1F; --pp-cover-open:#493B30; --pp-cover-ridge:#3C3C1E;
  --pp-cover-wet:#233616;
  --pp-ida-mass:#86734B; --pp-tumulus:#7A6846;
  --pp-haze:#141B28; --pp-sky-hi:#0B1120; --pp-sky-lo:#242B3A;
  --pp-water-far:#1E3244; --pp-water-shoal:#15343C;
""",
}
COVER_WASH_OP = 0.55        # the wet delta's wash over the fan beneath it

# ── the shoal (see water_svg). Widths are METRES OF GROUND out from the
# waterline, painted OUTERMOST FIRST so the three bands stack: full strength
# at the shore, two thirds of it at 110 m, a third at 260 m, gone at 560.
SHOAL_BANDS = (560.0, 260.0, 110.0)
SHOAL_OP = (0.10, 0.11, 0.13)
SHOAL_PX_MAX = 80.0         # a near-field clamp, and it is the near field
                            # that needs one: the plane's scale goes as
                            # 1/r^2 and runs away under the reader's feet


def _shoal_px(px_per_m: float, ground_m: float) -> float:
    """Ground metres, measured AWAY FROM THE VIEWER on the water plane, in
    screen px.

    Which scale to use is the whole question and the first answer was wrong.
    A metre ACROSS the line of sight projects to FOCAL/r px; a metre ALONG it
    projects to about FOCAL*h/r^2 — sixty times smaller at eight kilometres,
    because that is what an oblique does to a horizontal plane. Using the
    across-sight scale left the far shore of the bay with a band fifty pixels
    wide, which is the "widest where the water is farthest" failure this was
    written to avoid, arriving by a different door. A shoal band is measured
    PERPENDICULAR TO ITS SHORE, and on a bay seen from above one end that is
    mostly the receding direction, so the along-sight scale is both the
    honest choice and the conservative one. It is computed from the camera
    itself (plane_scale), never from a formula fitted here."""
    return min(SHOAL_PX_MAX, ground_m * px_per_m)

CSS = """
.pp-cover{stroke:none}
.pp-shade{stroke-linejoin:round}
/* IDA IS DRAWN BEFORE THE AIR, so it takes all of it: the mountain sits at
   45-80 km and the strata lay 0.73 of --pp-haze over it before anything else
   is painted. At 0.22 it disappeared outright once the haze became a law
   instead of a table. The mass is asserted harder so that what SURVIVES the
   air is about what it was — 0.62 x 0.27 = 0.17 — which is the right way
   round: the mountain is stated at full strength and the distance takes it
   down, rather than being pre-faded and then faded again. */
.pp-ida{fill:var(--pp-ida-mass);fill-opacity:0.62;stroke:none}
.pp-ida-crest{fill:none;stroke:var(--plate-contour);stroke-width:0.9;stroke-opacity:0.95}
.pp-sea{fill:var(--scene-map-sea)}
.pp-lagoon{fill:var(--plate-lagoon)}
.pp-marsh{fill:var(--pp-cover-wet);fill-opacity:0.55;stroke:none}
.pp-coast{fill:none;stroke:var(--scene-map-coast);stroke-width:1.1}
/* THE RECONSTRUCTED SHORE IS A HAIRLINE, NOT A DASH -- and NOT nothing.
   It was drawn dashed and the dash ran all the way round the bay, which made
   it the dottiest mark on the sheet. The obvious repair is the one
   docs/TROAD-CARTOGRAPHY.md prescribes for an indefinite margin: NO BOUNDARY
   at all, lettered and not outlined, as delta-swamp already is in water_svg.
   IT IS NOT AVAILABLE HERE, and the reason is measured. WCAG 1.4.11 wants
   3:1 on a graphical boundary, and the fill boundary alone gives
   1.69:1 / 1.56:1 / 1.45:1 in light and 1.54 / 1.48 / 1.41 in dark, lagoon
   against fan, unclassified ground and ridge. The same doc says it in
   words -- "a wash may not be relied on for contrast" -- and answers itself
   with an opaque hairline. So the wetland rule cannot cross to a shoreline
   whose two sides are a value pair this close.
   --scene-map-coast at full opacity DOES carry it: 3.24:1 on the lagoon in
   light, 6.13 in dark, and 4.0-5.5 on every land class in both. Full opacity
   is not a choice either -- 3.24 in light theme has no headroom to give away.
   What is left free is WEIGHT, and weight is the oldest certainty convention
   there is and one this sheet already runs on (see CONTOUR_INDEX_EVERY). The
   reconstruction draws at 0.7 px against the surveyed modern coastline's
   1.1 px solid, so the difference between the two lines is how heavily they
   are asserted. The claim itself is in the cartouche, in words. */
.pp-coast-approx{fill:none;stroke:var(--scene-map-coast);stroke-width:0.7;
  stroke-linejoin:round}
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
/* Ilios's wall, crest, tower and roofs are a BUILT MASS on the skyline, the
   same kind of thing a hull is, and they had the hull bug: keyed to --text,
   a 50 px ring of pure label-white appeared round the citadel in dark theme.
   They take the same fix the hulls already have -- --pp-hull-edge, dark rim
   on light ground, restrained rim on dark ground -- instead of re-deriving a
   third rim token for one more built shape. */
.pp-wall{fill:var(--plate-masonry);stroke:var(--pp-hull-edge);stroke-width:0.5;
  stroke-linejoin:round}
.pp-wall-crest{fill:none;stroke:var(--pp-hull-edge);stroke-width:0.8}
/* the citadel's own sunward and far faces: the terrain's tones, on masonry */
.pp-wall-lit{fill:var(--pp-lit);stroke:none}
.pp-wall-shade{fill:var(--pp-shade);stroke:none}
.pp-tower{fill:var(--plate-masonry);stroke:var(--pp-hull-edge);stroke-width:0.5;
  stroke-linejoin:round}
.pp-roof{fill:var(--plate-masonry);stroke:var(--pp-hull-edge);stroke-width:0.4;
  stroke-linejoin:round}
/* A built work, not terrain: keyed to the relief ramp it was a shade of the
   ground it stands on in both themes and read as one more contour. */
.pp-rampart{fill:var(--plate-masonry);stroke:var(--text-mid);stroke-width:0.5;
  stroke-linejoin:round}
/* The ditch and the road were dashed too, and neither dash was carrying what
   the shore's was. Both are CONJECTURAL positions, and that claim is already
   made in words on the plate ("the wall and ditch, and every waypoint of the
   poem are conjectural — each placed by a stated rule, never at an invented
   coordinate") and in the data, where every waypoint ships its
   positionBasis. A dash cannot say "conjectural" twice, and it was saying it
   in the one register the eye reads as texture. So both go solid and quiet:
   a fine low-opacity line states the shape without claiming a survey, which
   is the same trade the cartouche already makes. The road keeps its open
   waypoint circles, which are what actually mark the places; the line
   between them only says these lie in this order along the ground.
   OPACITY GOES UP, NOT DOWN, and that is a defect fixed rather than a taste.
   Both marks were at 0.55, which put --text-mid over the ground classes at
   2.19-2.33:1 in light and 2.47-2.62:1 in dark -- under WCAG 1.4.11's 3:1 in
   BOTH themes, and under it before this pass touched them. 3:1 needs 0.74 in
   light and 0.68 in dark, so 0.75 clears both with a little to spare and
   measures 3.06-3.40:1 light, 3.33-3.57:1 dark. The marks stay quiet by being
   THIN (0.9 px, the road down from 1.2), which costs no contrast, instead of
   by being faint, which costs nothing else. */
.pp-ditch{fill:none;stroke:var(--text-mid);stroke-width:0.9;stroke-opacity:0.75}
.pp-road{fill:none;stroke:var(--text-mid);stroke-width:0.9;stroke-opacity:0.75;
  stroke-linecap:round}
.pp-mark{fill:none;stroke:var(--text-mid);stroke-width:1.1}
.pp-mark-f{fill:var(--text-mid);stroke:none}
.pp-tumulus{fill:var(--pp-tumulus);fill-opacity:0.9;stroke:var(--text-mid);
  stroke-width:0.6}
.pp-leader{fill:none;stroke:var(--text-mid);stroke-width:0.8;stroke-opacity:0.75}
.pp-neat-o{fill:none;stroke:var(--text);stroke-width:2.2}
.pp-neat-i{fill:none;stroke:var(--text);stroke-width:0.7}
.pp-key-sw{stroke:var(--text-mid);stroke-width:0.4}
.pp-l-region{font-size:15.5px;letter-spacing:2.48px;fill:var(--text-mid)}
.pp-l-settlement{font-size:15px;font-weight:600;fill:var(--text)}
.pp-l-water{font-size:12.5px;font-style:italic;letter-spacing:0.5px;fill:var(--text-mid)}
.pp-l-site{font-size:11.5px;fill:var(--text)}
.pp-l-note{font-size:10px;fill:var(--text-mid)}
.pp-l-title{font-size:22px;letter-spacing:3.2px;fill:var(--text)}
"""

# ── THE HALO IS THE LABEL'S BACKGROUND, AND SAYING SO IS WHAT LET THE TONE
# OFF ITS LEASH (2026-08-14) ─────────────────────────────────────────────
# The sheet was pale on purpose. SHADE_MAX sat at 0.40 with a note saying
# 0.50 "looked best" and had been backed down because it cost label contrast
# -- so the ground was being kept light to protect the lettering standing on
# it, which is the wrong thing to trade and, it turns out, was not even the
# trade being made.
#
# WHAT WAS ACTUALLY CAPPING THE TONE WAS THE MEASUREMENT. The numbers in the
# old SHADE_MAX note were taken from "the median ground in a 16-28 px annulus"
# round each label's anchor. A 16-28 px ring is not a label's background: it
# is the terrain a quarter of an inch away, on the far side of a halo the
# sheet has always drawn. Re-measured on rendered pixels with that halo
# credited, EVERY label on the plate came out at 7.48:1 (--text-mid) and
# 15.86:1 (--text) in light -- because the halo was OPAQUE, so the composite
# under the lettering was the halo token exactly and had nothing to do with
# the ground at all. The three labels the old note reports as "already
# failing" (SIGEION, GROUND COVER, THE SHIPS, at 3.30-3.42) fail only under
# the annulus, and only against ground they never touch.
#
# So the fix is the one the sister geographic plates shipped the same morning
# (shared/lib/plate.ts, RELIEF_HALO_WIDTH / RELIEF_HALO_OPACITY): let the
# label carry its own background, and MEASURE THAT. The opacity is the whole
# craft of it. An opaque knockout reads as its own shape -- a white worm
# round every word, and the bolder the ground gets the more it shows -- while
# at 0.72 the stroke DIMS the terrain round the letterforms instead of
# deleting it: the tone edges and the cover boundaries still run through the
# halo, and the label still sits on a background it brought with it.
#
# WHAT IT COSTS AND WHAT IT BUYS, both stated, because one number goes down.
# An opaque halo scores 7.48:1 on every --text-mid label in light and 8.15 in
# dark REGARDLESS OF THE GROUND, since the composite under the letterform is
# then the halo token and nothing else. Translucent, the composite is 0.72
# halo over whatever is there, so it moves with the ground -- and the worst
# label on the sheet measures 5.04:1 light, 6.08:1 dark, 4.75:1 on the 4x camp
# crop. Lower than 7.48, clear of AA everywhere, and it is the number that
# means something: it is what a reader compares.
#
# Measured across the dial, worst label, so the trade is on the record:
#
#     opacity   light   dark   camp 4x
#     0.72       5.04   6.08     4.75
#     0.78       5.51   6.54     5.27
#     0.82       5.84   6.85     5.63
#     0.86       6.18   7.16     6.02
#     1.00       7.48   8.15     7.48
#
# 0.72 because it is what the sister geographic plates ship: one atlas, one
# halo, and a reader moving between a plan sheet and this one should not meet
# two different treatments of the same lettering. Raise it here if the margin
# is ever wanted -- the cost is that the knockout starts to show.
#
# And the floor rose where it actually mattered. The three labels the old note
# reports as failing had NO honest measurement at all: 3.30-3.42 against
# ground a quarter-inch away. Measured against what they sit on, SIGEION is
# 5.31, THE SHIPS 5.04, and GROUND COVER has left the picture entirely for the
# margin, where it letters on page.
HALO_W = 2.6             # px of knockout on the display type
HALO_W_NOTE = 2.2        # the 10 px note face wants proportionally less
HALO_OP = 0.72           # dims the ground round a letter; never punches it out


def label_css() -> str:
    return (
        'text{font-family:var(--font-ui,Optima,Seravek,"Gill Sans",'
        '"Gill Sans MT",sans-serif);paint-order:stroke;'
        'stroke:var(--scene-map-label-halo);'
        f'stroke-width:{HALO_W:g};stroke-opacity:{HALO_OP:g};'
        'stroke-linejoin:round}'
        f'.pp-l-note{{stroke-width:{HALO_W_NOTE:g}}}'
    )

# ── contour ink ──────────────────────────────────────────────────────────
# Generated, not literal, because the weights are what this pass is testing.
# The old values were 0.6 px at 0.6 opacity for every isoline on the sheet:
# on tan ground that is a whisper, and the landforms the contours carry --
# the closed lobe round the citadel above all -- were in the drawing and
# invisible. Index lines (see INDEX_LEVELS) take the heavier weight.
CONTOUR_W = 0.75
CONTOUR_OP = 0.80
CONTOUR_INDEX_W = 1.5
CONTOUR_INDEX_OP = 0.95
OBJ_SHADOW_OP = 0.3


def contour_css() -> str:
    return (
        f".pp-objshadow{{fill:var(--pp-shade);"
        f"fill-opacity:{OBJ_SHADOW_OP:g};stroke:none}}"
        f".pp-contour{{fill:none;stroke:var(--plate-contour);"
        f"stroke-width:{CONTOUR_W:g};stroke-opacity:{CONTOUR_OP:g};"
        f"stroke-linecap:round}}"
        f".pp-contour-index{{fill:none;stroke:var(--plate-contour);"
        f"stroke-width:{CONTOUR_INDEX_W:g};stroke-opacity:{CONTOUR_INDEX_OP:g};"
        f"stroke-linecap:round;stroke-linejoin:round}}"
    )


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
        self.shadow = None               # the ShadowField; set by shade_field
        self.shade_q: dict = {}
        self.cover: dict = {}            # (i, j) -> ground-cover class

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
        # the ground positions in metres, kept because the slope shading needs
        # a surface normal and the screen point cannot give it one
        wor = [[(0.0, 0.0)] * len(rngs) for _ in azs]
        for i, az in enumerate(azs):
            th = math.radians(HEADING_DEG + az)
            s, c = math.sin(th), math.cos(th)
            for j, rr in enumerate(rngs):
                e = cam.e + rr * s
                n = cam.n + rr * c
                wor[i][j] = (e, n)
                lat = VIEWPOINT[0] + n / 111132.0
                lon = VIEWPOINT[1] + e / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
                el = terr.elev_smooth(lat, lon, max(MESH_STENCIL_M, rr * 0.006))
                p = cam.project(e, n, exaggerate(el))
                grid[i][j] = None if p is None else (p[0], p[1], el, rr)
        self.grid = grid
        self.wor = wor

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

    # ── ground cover ─────────────────────────────────────────────────────
    def cover_field(self):
        """Classify every visible mesh cell by what the ground IS.

        One class per cell, taken at the cell's CENTRE, and no cell is ever
        split: a ground-cover boundary is not an isoline, so there is nothing
        to clip a cell against. (The hypsometric bands did split cells, at the
        level they crossed -- that machinery went with them, and the contour
        hairlines are now extracted on their own.)

        The masks are the plate's own layers, reused verbatim. Priority runs
        most specific first, which is also most defensible first: the ridges
        are cut from the DEM, the plain sector is a lettering polygon, and
        anything in neither carries no claim at all. The wet delta is not here
        -- it is a wash painted over this, because a wetland has no boundary.
        """
        ridge = [Mask(self.lay[k]["polygon"]) for k in RIDGE_LAYERS]
        plain = Mask(self.lay[PLAIN_LAYER]["polygon"])
        vp_lat, vp_lon = VIEWPOINT
        mlat = 1.0 / 111132.0
        mlon = 1.0 / (111320.0 * math.cos(math.radians(vp_lat)))
        cov = {}
        tally = {COVER_FAN: 0, COVER_RIDGE: 0, COVER_OPEN: 0}
        for (i, j) in self.visible:
            (e0, n0), (e1, n1) = self.wor[i][j], self.wor[i + 1][j]
            (e2, n2), (e3, n3) = self.wor[i + 1][j + 1], self.wor[i][j + 1]
            lat = vp_lat + (n0 + n1 + n2 + n3) * 0.25 * mlat
            lon = vp_lon + (e0 + e1 + e2 + e3) * 0.25 * mlon
            if any(m.has(lat, lon) for m in ridge):
                c = COVER_RIDGE
            elif plain.has(lat, lon):
                c = COVER_FAN
            else:
                c = COVER_OPEN
            cov[(i, j)] = c
            tally[c] += 1
        self.cover = cov
        self.stats["cover_cells"] = tally

    def terrain_svg(self):
        grid, azs, rngs = self.grid, self.azs, self.rngs
        corner = lambda i, j: (grid[i][j][0], grid[i][j][1])
        out = []
        edges = STRATA_EDGES
        for s in range(len(edges) - 1):
            far, near = edges[s], edges[s + 1]
            if far in HAZE and s > 0:
                out.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                           f'fill="var(--pp-haze)" '
                           f'fill-opacity="{HAZE[far]:.4f}"/>')
            interior: dict = {}
            cont: dict = {}
            shade: dict = {}
            for (i, j) in self.visible:
                rr = grid[i][j][3]
                if not (near * 0.965 <= rr < far):
                    continue
                st = self.shade_q.get((i, j), 0)
                if st:
                    shade.setdefault(st, set()).add((i, j))
                interior.setdefault(self.cover[(i, j)], set()).add((i, j))
                if CONTOURS == "none":
                    continue
                # THE HAIRLINES ARE NOW EXTRACTED ON THEIR OWN. While the ground
                # was tinted by height the isolines fell out of the fill as the
                # seam between two bands; nothing colours by height any more, so
                # a contour is cut here directly -- the segment where the cell's
                # bilinear surface crosses a level. Every level a cell crosses
                # gets its line, which is one line more than the old code drew
                # on a cliff cell (it fell into the three-band branch and emitted
                # fills only).
                a0, a1 = grid[i][j], grid[i + 1][j]
                b1, b0 = grid[i + 1][j + 1], grid[i][j + 1]
                evs = [a0[2], a1[2], b1[2], b0[2]]
                k0, k1 = band_of(min(evs)), band_of(max(evs))
                if k0 == k1:
                    continue
                quad = [(a0[0], a0[1]), (a1[0], a1[1]),
                        (b1[0], b1[1]), (b0[0], b0[1])]
                # the lattice edge each quad edge IS, so the crossings chain
                nodes = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                for k in range(k0, k1):
                    if CONTOURS == "index" and k not in INDEX_LEVELS:
                        continue
                    lv = LEVELS[k]
                    seg = []
                    for m in range(4):
                        e0, e1 = evs[m], evs[(m + 1) % 4]
                        if (e0 - lv) * (e1 - lv) < 0:
                            t = (lv - e0) / (e1 - e0)
                            p0, p1 = quad[m], quad[(m + 1) % 4]
                            na, nb = nodes[m], nodes[(m + 1) % 4]
                            seg.append(((na, nb) if na < nb else (nb, na),
                                        (p0[0] + t * (p1[0] - p0[0]),
                                         p0[1] + t * (p1[1] - p0[1]))))
                    if len(seg) == 2:
                        cont.setdefault(k, []).append(tuple(seg))
            for c in COVER_ORDER:
                cells = interior.get(c)
                if not cells:
                    continue
                d = []
                for loop in union_loops(cells, corner):
                    # THE SAWTOOTH ALONG THE FRONT EDGE lives here. In the
                    # near field a ring is 37 px of screen and the ridge
                    # mask's own edge runs nearly PARALLEL to the rings, so
                    # classifying by cell centre put the boundary a whole ring
                    # out every seven columns: a row of 37 px teeth across the
                    # foot of the plate, the first thing the eye found. The
                    # low-pass is sized for exactly that riser.
                    d.append(rel_poly(chaikin(simplify(
                        soften(loop, COVER_SOFT), 0.7), 1)))
                if d:
                    # A hairline of page-bg used to show wherever a simplified
                    # union loop pulled away from its neighbour, or where one
                    # depth stratum met the next. Stroking a class in its OWN
                    # fill closes the seam for 0.3 px of expansion and no
                    # change to the drawing.
                    tok = f"var({COVER_TOKEN[c]})"
                    out.append(f'<path class="pp-cover" fill="{tok}" '
                               f'stroke="{tok}" stroke-width="0.7" '
                               f'd="{"".join(d)}"/>')
            # SHADING sits between the cover and the contours: it models the
            # surface the cover colours, and the hairlines stay on top of both.
            #
            # NESTED WASHES, not cut steps -- see SHADE_STEPS for why. Level k
            # is the region where the light has reached step k or beyond, so
            # the regions contain one another and the tone is however many
            # washes a cell lies under.
            for sgn, tone, mx in ((-1, "var(--pp-shade)", SHADE_MAX),
                                  (1, "var(--pp-lit)", LIT_MAX)):
                if not mx:
                    continue
                a = 1.0 - (1.0 - mx) ** (1.0 / SHADE_STEPS)
                acc: set = set()
                for k in range(SHADE_STEPS, 0, -1):
                    acc |= shade.get(sgn * k, set())
                    if not acc:
                        continue
                    d = []
                    for loop in union_loops(acc, corner):
                        if abs(poly_area(loop)) < SHADE_MIN_AREA:
                            continue      # a sliver, not a slope
                        # SOFTEN FIRST, GENERALISE AFTER, and the order is
                        # the whole fix. Douglas-Peucker on a raw staircase
                        # keeps every riser corner (a 7 px step clears a
                        # 3.2 px band by a factor of two) and throws away the
                        # treads that made it read as a diagonal, so what
                        # arrived at chaikin() was a jagged polyline with
                        # SHARPER angles than the lattice had -- and
                        # corner-cutting scalloped those instead of curing
                        # them. Low-pass the lattice loop while it is still
                        # dense and regular, then generalise the curve that
                        # comes out. The tolerance can be looser than it was
                        # because a wash edge now carries 1/18 of the tone,
                        # not 7/10 of it.
                        d.append(rel_poly(chaikin(simplify(
                            soften(loop, SHADE_SOFT_PASSES),
                            SHADE_SIMPLIFY), 1)))
                    if not d:
                        continue
                    # NOT stroked, unlike the bands. A wash needs no
                    # seam-closing -- a gap between two tones just reads as
                    # the tone between them -- and a stroke doubles the width
                    # of any thin region, which is what printed the pale
                    # filaments at 8x.
                    out.append(f'<path class="pp-shade" fill="{tone}" '
                               f'fill-opacity="{a:.4f}" d="{"".join(d)}"/>')
            for k in sorted(cont):
                cls = "pp-contour-index" if k in INDEX_LEVELS else "pp-contour"
                d = []
                for line, shut in chain_segments(cont[k]):
                    curve = soften(line, CONTOUR_SOFT, closed=shut)
                    self.stats["contour_dev_px"] = max(
                        self.stats.get("contour_dev_px", 0.0),
                        max_deviation(curve, line))
                    sm = simplify(curve, 0.5, closed=shut)
                    if len(sm) < 2:
                        continue
                    d.append(rel_poly(sm, close=shut))
                if d:
                    out.append(f'<path class="{cls}" d="{"".join(d)}"/>')
        return "".join(out)

    # ── slope shading ────────────────────────────────────────────────────
    def shade_field(self):
        """Quantise the light over every visible cell, ONCE, with a smoothing
        pass first.

        The smoothing is why this is a field and not a per-cell call. Raw
        per-cell normals speckle: a single cell whose normal differs from its
        neighbours' becomes a one-cell tone island, and a one-cell island
        draws as a filament. At 8x those filaments printed as pale threads
        across the plain -- continuous tone resolving into countable marks,
        which is the one thing the cartography doc's general rule really does
        forbid. A 3x3 box over the LATTICE (not over the ground) removes them
        at the source, and it generalises TONE, not terrain: no elevation, no
        contour and no band moves."""
        self.shadow = None
        if not SHADE_STEPS:
            self.shade_q = {}
            return
        if SHADOW:
            t0 = time.time()
            self.shadow = ShadowField(self.terr, LIGHT_AZ, LIGHT_ALT)
            self.stats["shadow_raster"] = self.shadow.n
            self.stats["shadow_secs"] = round(time.time() - t0, 1)
        raw = {ij: self.shade_raw(*ij) for ij in self.visible}
        # ── THE SMOOTHER WAS EATING THE SHADOW EDGE, and a shadow edge is the
        # one edge on this sheet that is genuinely hard. The sun's disc is
        # half a degree, so the penumbra of a 25 m scarp at its own shadow's
        # tip is about 1.3 m of ground -- a fifth of a mesh cell. Everything
        # softer than that in the drawing was put there by the drawing.
        #
        # The box pass above exists for a real defect (speckled normals, see
        # the docstring), and it is the right tool for that; it is simply the
        # wrong tool to run ACROSS a discontinuity. So it is made edge-aware:
        # a cell averages only with neighbours that agree with it about
        # whether they can see the sun. Inside a shadow the filter is exactly
        # what it was; at the boundary it stops, and the boundary survives at
        # the lattice's own resolution instead of being smeared over two mesh
        # cells, which in the near field is 400 m of ground.
        lit = ({ij: (1.0 if self.sunlit_at(*ij) > 0.5 else 0.0)
                for ij in raw} if self.shadow is not None else None)
        for _ in range(max(1, SHADE_SMOOTH)):
            nxt = {}
            for (i, j), v in raw.items():
                tot, wsum = v * 2.0, 2.0
                s0 = None if lit is None else lit[(i, j)]
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    ij2 = (i + di, j + dj)
                    n = raw.get(ij2)
                    if n is None or (s0 is not None and lit[ij2] != s0):
                        continue
                    tot += n
                    wsum += 1.0
                nxt[(i, j)] = tot / wsum
            raw = nxt
        q: dict = {}
        for ij, v in raw.items():
            # MATERIAL GAIN. The light field is one thing; what a substance
            # does with it is another (see MATERIAL). It multiplies here,
            # after the field has been smoothed and before it is quantised,
            # so shade_raw stays a pure function of slope and light and the
            # gain lands where the ground classification actually exists.
            v *= MATERIAL.get(self.cover.get(ij), 1.0)
            # TERMINATOR GAMMA, and it belongs beside the material gain for
            # the same reason: shade_raw stays a pure function of slope and
            # light, and this is a statement about how the sheet DRAWS that
            # light. See SHADE_GAMMA. Sign-preserving, so lit and shaded are
            # steepened alike and flat ground still takes nothing.
            if SHADE_GAMMA != 1.0 and v:
                v = math.copysign(abs(v) ** SHADE_GAMMA, v)
            st = int(round(v * SHADE_STEPS))
            q[ij] = max(-SHADE_STEPS, min(SHADE_STEPS, st))
        q, islands = median_lattice(q, SHADE_MEDIAN)
        self.shade_q = q
        self.stats["shaded_cells"] = sum(1 for v in q.values() if v)
        self.stats["shade_islands_filtered"] = islands

    def sunlit_at(self, i, j):
        """The cast-shadow visibility at one cell's centre, on its own — the
        same number shade_raw folds into the light, read separately so the
        smoother can be told where not to cross. No shadow field, all lit."""
        if self.shadow is None:
            return 1.0
        w = self.wor
        (e00, n00), (e10, n10) = w[i][j], w[i + 1][j]
        (e11, n11), (e01, n01) = w[i + 1][j + 1], w[i][j + 1]
        return self.shadow.at((e00 + e10 + e11 + e01) * 0.25,
                              (n00 + n10 + n11 + n01) * 0.25)

    def shade_raw(self, i, j):
        """The continuous light at one mesh cell, in [-1, 1]: negative for a
        slope turned away from the light and positive for one facing it, zero
        on ground lying flat to it.

        The normal is taken from the DRAWN surface (exaggerated z), not the
        real one, because the shading has to model the geometry the sheet
        actually shows. It is a function of the cell's own slope and aspect
        and of one global light vector -- of nothing else, and above all not
        of where the cell is.

        Flat ground is the datum: N.L there is sin(altitude), and the tone is
        the DEPARTURE from it, so level ground in full sun takes no wash at
        all and the hypsometric ramp is left to say what it says.

        CAST SHADOW enters as a factor on the same quantity. A cell that
        cannot see the sun has illumination 0 however it is tilted, which
        lands it at the bottom step -- so the slope term and the occlusion
        term are ONE number and need no second drawing pass."""
        g, w = self.grid, self.wor
        a0, a1 = g[i][j], g[i + 1][j]
        b1, b0 = g[i + 1][j + 1], g[i][j + 1]
        (e00, n00), (e10, n10) = w[i][j], w[i + 1][j]
        (e11, n11), (e01, n01) = w[i + 1][j + 1], w[i][j + 1]
        z00, z10 = exaggerate(a0[2]), exaggerate(a1[2])
        z11, z01 = exaggerate(b1[2]), exaggerate(b0[2])
        # normal from the cell's two diagonals
        ux, uy, uz = e11 - e00, n11 - n00, z11 - z00
        vx, vy, vz = e01 - e10, n01 - n10, z01 - z10
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        if nz < 0.0:
            nx, ny, nz = -nx, -ny, -nz
        m = math.sqrt(nx * nx + ny * ny + nz * nz)
        if m < 1e-9:
            return 0
        lam = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / m
        sunlit = 1.0
        if self.shadow is not None:
            ec = (e00 + e10 + e11 + e01) * 0.25
            nc = (n00 + n10 + n11 + n01) * 0.25
            sunlit = self.shadow.at(ec, nc)
        # the sky is the second source, and a shadow is where it is the only
        # one; the surface's own sky view factor is (1 + nz)/2 (see
        # SHADOW_AMBIENT)
        illum = max(0.0, lam) * sunlit + SHADOW_AMBIENT * 0.5 * (1.0 + nz / m)
        flat = LIGHT[2] + SHADOW_AMBIENT
        d = illum - flat
        return d / (1.0 - flat) if d > 0 else d / flat

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
        # a per-column maximum is a ragged silhouette by construction; the
        # mountain behind the mesh is the one line on the sheet with no
        # measured vertices at all
        sky = soften(sky, 2, closed=False)
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
        # ── WHAT MAKES IT WATER AND NOT A BLUE SHAPE ─────────────────────
        # Both bodies were flat fills, which is why the far arm of the bay
        # twenty kilometres out sat at exactly the saturation of the water
        # under the reader's feet. Water is not a colour, it is a surface,
        # and two measured things happen to it across that distance:
        #
        #   1. FRESNEL. Reflectance runs from about 2% looking straight down
        #      to over 80% at eight degrees above the horizontal, so the near
        #      bay shows its body colour and the far bay is a mirror of the
        #      sky. That is the #pp-water-sky ramp, and it is Schlick's curve
        #      on the camera height and the range, with nothing chosen.
        #   2. AIR. The same Beer-Lambert extinction the land strata already
        #      integrate — which the water was getting none of, because
        #      water_svg paints after terrain_svg and after every haze rect.
        #      That is #pp-air.
        #
        # Both go on UNDER the shoreline strokes. The fills may recede; the
        # lines that carry the land/water boundary are a cartographic
        # assertion and keep their measured contrast at every distance.
        def _air(d):
            return (f'<path d="{d}" fill="url(#pp-water-sky)"/>'
                    f'<path d="{d}" fill="url(#pp-air)"/>')

        # ── THE SHOAL, and why it is not a bathymetric claim ─────────────
        # A body of water is never the same colour at its edge as in its
        # middle, because at its edge you are looking at the bottom. The bay
        # of Troy is the extreme case: Kayan's cores have it silting up
        # through the Bronze Age, a shallow embayment over a sand and mud
        # floor, and a metre of clear water over pale sand is paler and
        # greener than four metres of the same water. This is the single
        # thing that stops a flat fill reading as a coloured shape.
        #
        # IT STATES NO DEPTH ANYWHERE. What it says is only "water shallows
        # at a shore", which is true of every shore there has ever been; it
        # carries no isobath, no soundings and no coordinate. The band holds
        # a constant width IN GROUND (see SHOAL_M) rather than in pixels, so
        # it narrows with distance exactly as the ground does — a fixed pixel
        # margin would have been widest where the water is farthest away,
        # which is the one thing that would have made it a claim about
        # something other than perspective.
        #
        # It goes PALER, never darker, which is both what a sand floor does
        # and what the label ink needs: "the bay of Troy" sits on this water.
        # IT IS A CLIPPED STROKE, NOT AN OFFSET RING, and that is a defect
        # fixed rather than a preference. Offsetting a closed polygon inward
        # by seventy pixels across a bay this concave inverts whole runs of
        # it; dropping the inverted runs -- which is what the waterlines' own
        # filter does, correctly, at four pixels -- closes the ring with long
        # straight CHORDS, and the first render put two of them clean across
        # the middle of the bay. A stroke centred on the shoreline and
        # clipped to the water cannot do that: it has no topology of its own
        # to lose. The clip also takes away the half of the stroke that would
        # otherwise have fallen on the beach.
        depth_at = plane_depth(self.cam)
        scale_at = plane_scale(self.cam)

        def shoal(poly, gid):
            # THE WIDTH IS IN GROUND, so the shore is cut into runs of
            # roughly equal range and each run strokes at its own width. One
            # width for the whole shore would have been widest where the
            # water is farthest, which is the one thing that would have made
            # this a claim about something other than perspective.
            # A RUN ENDS WHEN THE BAND'S WIDTH HAS MOVED BY ONE PIXEL. The
            # first cut was a sixth of an octave, which stepped the width
            # twenty pixels at a time on a band a hundred wide, and every one
            # of those steps printed a straight-edged wedge into the bay. A
            # one-pixel step cannot be seen; the only cost is more pieces.
            runs, cur, dep, last = [], [], [], None
            for (x, y) in poly:
                k = scale_at(depth_at(y))
                b = round(_shoal_px(k, SHOAL_BANDS[0]))
                if last is not None and b != last and len(cur) > 1:
                    cur.append((x, y))          # share a vertex: no gap
                    runs.append((sum(dep) / len(dep), cur))
                    cur, dep = [cur[-2]], [k]
                cur.append((x, y))
                dep.append(k)
                last = b
            if len(cur) > 1 and dep:
                runs.append((sum(dep) / len(dep), cur))
            # EACH BAND IS ONE GROUP AT ONE OPACITY, and that is the third
            # defect this one wash has produced. Runs of different width have
            # to be separate <path> elements, and two translucent paths that
            # overlap composite TWICE: where the shore turned, the wedge
            # where a hundred-and-sixty-pixel stroke met its neighbour went
            # to double strength, and the near bay filled with a faint quilt
            # of straight-edged patches. Group opacity is the fix and it is
            # exact: SVG flattens a group before applying its opacity, so
            # every run of one band composites once however they overlap.
            svg = [f'<defs><clipPath id="{gid}">'
                   f'<path d="{rel_poly(poly)}"/></clipPath></defs>'
                   f'<g clip-path="url(#{gid})" fill="none" '
                   f'stroke="var(--pp-water-shoal)" stroke-linecap="butt" '
                   f'stroke-linejoin="round">']
            for m, op in zip(SHOAL_BANDS, SHOAL_OP):   # outermost band first
                band, d, w0 = [], [], None
                for k, run in runs:
                    w = round(2.0 * _shoal_px(k, m), 1)
                    if w < 1.2:
                        continue
                    if w != w0 and d:
                        band.append(f'<path d="{"".join(d)}" '
                                    f'stroke-width="{w0:g}"/>')
                        d = []
                    d.append(rel_poly(run, close=False))
                    w0 = w
                if d:
                    band.append(f'<path d="{"".join(d)}" '
                                f'stroke-width="{w0:g}"/>')
                if band:
                    svg.append(f'<g opacity="{op:.3f}">'
                               + "".join(band) + '</g>')
            svg.append('</g>')
            return "".join(svg)

        if sea:
            out.append(f'<path d="{rel_poly(sea)}" class="pp-sea"/>')
            out.append(shoal(sea, "pp-shoal-sea"))
            out.append(_air(rel_poly(sea)))
            out.append(f'<path d="{rel_poly(sea)}" class="pp-coast"/>')
        if lagoon:
            out.append(f'<path d="{rel_poly(lagoon)}" class="pp-lagoon"/>')
            out.append(shoal(lagoon, "pp-shoal-lagoon"))
            out.append(_air(rel_poly(lagoon)))
            # THE WATERLINES. Two hairlines stepped in from the shore, the
            # oldest convention on any sea chart. Their offset is in PIXELS
            # and stays so: they are a drawn mark, not a measured margin, and
            # they must not thin below the raster in the distance.
            sgn = winding_sign(lagoon)
            acc = 0.0
            for gap in (3.2, 4.16):
                acc += gap
                keep = inset(lagoon, sgn, acc)
                if len(keep) > 8:
                    out.append(f'<path d="{rel_poly(keep)}" class="pp-waterline"/>')
            out.append(f'<path d="{rel_poly(lagoon)}" class="pp-coast-approx"/>')
        # THE SWAMP HAS NO EDGE. A wetland grades from open water through reed
        # and seasonal flood to dry ground and moves with the year, so it is
        # drawn with no outline at all and blurred out at its margin -- the
        # same argument, and the same treatment, the geographic sheet already
        # uses for delta-swamp.
        #
        # IT IS NOW A GROUND-COVER CLASS, and that promoted it out of tier 2.
        # As an annotation it could wait for the 2x zoom; as one of the three
        # classes on this sheet with a derivable rule it belongs in the
        # overview, or the overview shows a delta with no wet ground on it.
        # It stays a wash rather than a mesh class for the reason above: the
        # lattice would have given it the hard boundary the layer's own note
        # says it does not have. What it washes over is the dry fan, so the
        # composite is the wet delta's colour and the blur is the gradation
        # between the two -- which is the only edge either of them really has.
        if swamp:
            out.append(f'<path d="{rel_poly(swamp)}" class="pp-marsh" '
                       f'filter="url(#pp-soft)"/>')
        return "".join(out)

    def rivers_svg(self):
        """A river is drawn on LAND ONLY. The channels are the modern survey;
        the bay is the Bronze Age reconstruction, and running a modern channel
        across a reconstructed lagoon mixes the two registers in one mark --
        which printed as a dark line wandering over open water."""
        lagoon = self.lay["lagoon-bronze"]["polygon"]
        sea = self.lay["sea-modern"]["polygon"]

        def wet(p):
            return (point_in_poly_ll(p[0], p[1], lagoon)
                    or point_in_poly_ll(p[0], p[1], sea))

        # ── A RIVER THAT STOPS SHORT OF THE WATER ────────────────────────
        # The Scamander ran down the sand spit and ended in mid-ground, a
        # blunt stub with beach on every side. The channel data was never the
        # problem: apparatus/plates/trojan-plain.json's `scamander` path has
        # 170 vertices and 43 of them lie INSIDE lagoon-bronze, so the survey
        # line reaches the reconstructed bay and crosses it. What ended short
        # was the DRAWING -- the run was cut at the last vertex outside the
        # water, and this path carries a vertex every 122 m (625 m at worst),
        # so the mouth was left up to a whole segment inland. Measured on the
        # shipped frame: the Scamander's last drawn vertex sat 37 m from the
        # lagoon boundary and the Simoeis's 40 m.
        #
        # So the run ends where the measured line CROSSES the reconstructed
        # shore, found by bisection on the straddling segment. Nothing is
        # invented: the route is the survey's own, and all that changes is
        # where along it the ribbon stops. It stops AT the waterline and not
        # past it, because water_svg paints before rivers_svg and a channel
        # drawn over the bay is the register mixing the docstring forbids.
        def waterline(dry, w, iters=20):
            for _ in range(iters):
                mid = ((dry[0] + w[0]) / 2.0, (dry[1] + w[1]) / 2.0)
                if wet(mid):
                    w = mid
                else:
                    dry = mid
            return w

        def dry_runs(path):
            runs, cur, prev = [], [], None
            for p in path:
                p = (p[0], p[1])
                if wet(p):
                    if len(cur) > 2:
                        cur.append(waterline(cur[-1], p))
                        runs.append(cur)
                    cur = []
                else:
                    if not cur and prev is not None and wet(prev):
                        cur.append(waterline(p, prev))
                    cur.append(p)
                prev = p
            if len(cur) > 2:
                runs.append(cur)
            return runs

        # A RIVER IS A MEASURED LINE AND IT WAS DRAWN AS FACETS. The survey
        # path carries a vertex every 122 m (median; 625 m at worst), which at
        # the Scamander's 7-12 km is a 17-28 px straight run, and the plate
        # printed the channel as a zigzag of them meeting at sharp corners --
        # "just a bunch of straight lines forming sharp angles". The
        # cartography doc's third pass settled this for the coastline and the
        # rivers never got it.
        #
        # SMOOTHED IN LAT/LON, NOT ON SCREEN, and with the coastline's own
        # device. Corner-cutting is the honest smoother for a surveyed line:
        # every point it emits lies ON a segment of the original, so the curve
        # cannot leave the polyline's own corridor, and the worst displacement
        # is a quarter of the shorter adjacent segment. Doing it in the world
        # and re-draping afterwards is what keeps the channel in its valley --
        # smoothing the two screen edges instead would have let the ribbon
        # climb out of the ground it was cut for.
        def course(path):
            curve = chaikin(path, passes=RIVER_SOFT, closed=False)
            # measured to the POLYLINE, not to its vertices: a corner-cut point
            # sits mid-segment, and on a 625 m segment the nearest vertex is
            # 300 m away while the line it is on is 0 m away
            flat = [pp._flat_m(p, *VIEWPOINT) for p in path]
            worst = 0.0
            for c in curve:
                cx, cy = pp._flat_m(c, *VIEWPOINT)
                best = float("inf")
                for (x0, y0), (x1, y1) in zip(flat, flat[1:]):
                    ux, uy = x1 - x0, y1 - y0
                    L2 = ux * ux + uy * uy
                    t = 0.0 if L2 < 1e-9 else max(0.0, min(
                        1.0, ((cx - x0) * ux + (cy - y0) * uy) / L2))
                    best = min(best, math.hypot(cx - x0 - t * ux,
                                                cy - y0 - t * uy))
                worst = max(worst, best)
            self.stats["river_dev_m"] = max(
                self.stats.get("river_dev_m", 0.0), worst)
            dense = []
            for a, b in zip(curve, curve[1:]):
                steps = max(1, int(math.hypot(*pp._flat_m(b, *a)) / 40.0))
                for s in range(steps):
                    t = s / steps
                    dense.append((a[0] + t * (b[0] - a[0]),
                                  a[1] + t * (b[1] - a[1])))
            dense.append(curve[-1])
            return dense

        out = []
        for run in dry_runs(self.lay["scamander"]["path"]):
            out.append('<g>' + draped_ribbon(
                self.cam, self.terr, course(run), 17.0, "pp-river",
                taper=lambda t: 0.55 + 0.45 * t) + '</g>')
        for run in dry_runs(self.lay["simoeis"]["path"]):
            out.append('<g class="tm2">' + draped_ribbon(
                self.cam, self.terr, course(run), 11.0, "pp-river",
                taper=lambda t: 1.0 - 0.4 * t) + '</g>')
        # THE AIR IS OVER THE RIVERS TOO. The channels are drawn after every
        # haze rect the strata laid down, so the Scamander was arriving at
        # 8-14 km at the full strength of a mark two hundred metres away --
        # the one thing left in the middle distance that read as a map line
        # rather than as a thing seen. It takes the SAME gradient the bay
        # does, which is the same law the ground does; nothing about the
        # channel moves.
        return hazed("".join(p for p in out if "<path" in p))

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
        obj_sh: list = []
        # the silhouettes that throw: a hull's deck at its true 2.4 m with the
        # stem-post's 6.4 m tip, and a hut's eaves at 1.8 with its ridge at
        # 3.2. Every height here is the one the object is drawn at.
        HULL_SIL = ([((f * 24.0, s * hb * 4.2), 2.4)
                     for f, hb in ((0.0, 0.30), (0.34, 0.50), (0.82, 0.36), (1.0, 0.06))
                     for s in (1, -1)] + [((24.0 * 0.90, 0.0), 6.4)])
        HUT_SIL = [((-2.5, -3.5), 1.8), ((-2.5, 3.5), 1.8),
                   ((2.5, -3.5), 1.8), ((2.5, 3.5), 1.8),
                   ((0.0, -3.5), 3.2), ((0.0, 3.5), 3.2)]
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
                    sd = object_shadow(cam, terr, lat, lon, bearing, HULL_SIL)
                    if sd:
                        obj_sh.append(sd)
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
                hb = seaward(round(lateral / 13.0) * 13.0) + (17 if row % 2 else -11)
                hh = hut(cam, terr, lat, lon, hb)
                if hh:
                    huts.append(hh)
                    sd = object_shadow(cam, terr, lat, lon, hb, HUT_SIL)
                    if sd:
                        obj_sh.append(sd)

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
        wall_pts, ditch_pts, wall_ground = [], [], []
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
                wall_ground.append((a[0], lat, lon, crest))
            if c:
                ditch_pts.append((c[0], c[1]))
        wall_svg = ""
        if len(wall_pts) > 4:
            wall_pts.sort(key=lambda q: q[0][0])
            # THE RAMPART THREW NOTHING EITHER, and a 4.6 m bank standing on
            # open ground with no shadow is the citadel's defect at a smaller
            # scale. It is drawn as ONE band rather than 74 object shadows:
            # the wall is continuous, so its shadow is, and hulling each
            # station separately would have printed the seams between them.
            wall_shadow = ""
            if OBJ_SHADOW and LIGHT_ALT > 0.5 and len(wall_ground) > 4:
                wall_ground.sort(key=lambda q: q[0])
                foot, cast = [], []
                for _, wlat, wlon, crest in wall_ground:
                    e, n = pp._flat_m((wlat, wlon), *VIEWPOINT)
                    dx, dy = sun_offset(crest)
                    gz = terr.elev(wlat, wlon)
                    a_ = cam.project(e, n, built_h(0.05, gz))
                    b_ = cam.project(e + dx, n + dy, built_h(0.05, gz))
                    if a_ and b_:
                        foot.append((a_[0], a_[1]))
                        cast.append((b_[0], b_[1]))
                if len(foot) > 4:
                    wall_shadow = ('<path class="pp-objshadow" d="%s"/>'
                                   % rel_poly(cast + list(reversed(foot))))
            wall_svg = (wall_shadow + '<path class="pp-rampart" d="%s"/>'
                        % rel_poly([p[1] for p in wall_pts]
                                   + [p[0] for p in reversed(wall_pts)]))
            self.stats["wall_mid"] = list(wall_pts[len(wall_pts) // 4][1])
        ditch_svg = ""
        if len(ditch_pts) > 4:
            ditch_pts.sort(key=lambda q: q[0])
            # the RAMPART is deliberately not softened: every fourth station
            # stands 3.4 m higher and those spikes are its towers (7.436-439),
            # which a low-pass would file off. The ditch has no such content.
            ditch_svg = '<path class="pp-ditch" d="%s"/>' % rel_poly(
                soften(ditch_pts, 2, closed=False), close=False)

        self.stats["hulls"] = hulls_drawn
        self.stats["huts"] = len(huts)
        self.stats["ship_depth"] = round(sum(depths) / len(depths), 1) if depths else 2600.0
        self.stats["beach_frontage_m"] = round(
            (max(q[2] for q in ship_px) - min(q[2] for q in ship_px)) if ship_px else 0.0)
        self.stats["obj_shadows"] = len(obj_sh)
        return ships, huts, mass, wall_svg, ditch_svg, ship_px, obj_sh

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
# furniture: neatline, scale, ground-cover key, disclosure
# ═══════════════════════════════════════════════════════════════════════════
# THE KEY IS THE ARGUMENT IN MINIATURE. It used to be a twelve-step ramp
# under a heading naming elevation in metres -- the plan-view apparatus that
# told the reader to read colour as height. It is now four ground-cover entries
# and no numbers at all, because the plate no longer makes a claim a number
# could answer. Each entry carries its evidence in the same breath as its
# swatch: whose finding it is, or that it is a default, or that it is nothing.
#
# THE FIFTH ENTRY HAS NO SWATCH, and that is the entry doing the most work.
# The riverbank thicket is the best-attested flora on this plain -- a named
# assemblage, sited in the poem's own words -- and it is unmappable, because
# the channels it grew along are under twenty metres of alluvium. So it is
# lettered and not bounded. A key that only lists what could be drawn would
# have quietly deleted the strongest thing the poem says about this ground.
COVER_KEY = (
    (COVER_FAN, "DRY DELTA FAN",
     "sand-covered, dusty, firm — the battlefield (Kayan 2002)"),
    (COVER_RIDGE, "RIDGE SCRUB, BARE SLOPE",
     "thin soil on limestone — a regional default, not a survey"),
    ("wet", "WET DELTA, SWAMP",
     "waterlogged delta behind the bay (Kayan 2003) — no edge"),
    (COVER_OPEN, "GROUND BEYOND THE PLAIN",
     "outside the sector and its ridges — not classified"),
)
COVER_KEY_UNDRAWN = (
    "RIVERBANK THICKET — elm, willow, tamarisk over lotus, rush and galingale "
    "(Il. 21.350–52): lettered, not bounded. Its channels lie under 20 m of "
    "alluvium and cannot be located."
)
# ── THE FURNITURE COMES OFF THE PICTURE (2026-08-14) ─────────────────────
# "the legends are unhelpful and obscure too much of the images" (John). The
# key, the two scale bars and the four-line cartouche were laid ON the map
# face, over the bottom-left quarter of the frame. The note that put them
# there argued the ground under them was dead — "the back of the ridge: real
# ground with nothing on it" — and it was RIGHT about the ground and wrong
# about the answer. Print's answer to a plate with dead foreground is not to
# letter over it. It is to CROP IT OFF and set the furniture in a margin
# below the neatline, where nothing it says can cover anything the plate
# draws. Which is the honest arrangement as well as the conventional one: a
# key that overlaps the map is making a claim about the ground it covers,
# namely that the ground does not matter.
#
# So the sheet is now a picture and a margin. The picture keeps its camera,
# its projection and its width exactly; what it loses is 300 px of empty near
# foreground at the foot, which takes the panorama from 16:9 to about 2.2:1 —
# a panorama's own proportion, and a closer crop on the thing the plate is
# of. The margin holds everything that is apparatus rather than picture.
BAND_H = 300.0           # the margin below the neatline, in px
NEAT_M = 16.0            # neatline inset from the sheet edge
PIC_BOT = H - BAND_H     # the picture's own bottom edge


def furniture(cam, terr, ship_depth, troy_depth):
    out = []
    m = NEAT_M
    # Double neatline, per docs/TROAD-CARTOGRAPHY.md — 1.2/0.4 px, 3 px apart
    # at the doc's own sheet size, doubled here because this sheet is drawn at
    # 2400 px for a 1200 px column.
    out.append(f'<rect x="{m}" y="{m}" width="{W - 2 * m}" '
               f'height="{PIC_BOT - 2 * m}" class="pp-neat-o"/>')
    out.append(f'<rect x="{m + 6}" y="{m + 6}" width="{W - 2 * m - 12}" '
               f'height="{PIC_BOT - 2 * m - 12}" class="pp-neat-i"/>')
    out.append(f'<text class="pp-l-title" x="{W / 2}" y="{m + 44}" '
               f'text-anchor="middle">THE SHIPS, THE BAY, AND ILIOS</text>')
    out.append(f'<text class="pp-l-note" x="{W / 2}" y="{m + 64}" '
               f'text-anchor="middle">the plain of Troy from the Achaean camp, '
               f'looking east-south-east</text>')

    bx = 62.0                      # the margin's own left edge
    rx = W - 62.0                  # and its right
    sx0 = 1300.0                   # where the scale column starts
    y0 = PIC_BOT + 38.0            # first baseline in the margin

    # ── the key. Every entry still carries its evidence in the same breath as
    # its swatch — that is the honesty mechanism and it is not negotiable —
    # but the heading now carries the sentence the cartouche used to spend a
    # whole line on, which is where it belonged: it is what the key MEANS.
    out.append(f'<text class="pp-l-region" x="{n1(bx)}" y="{n1(y0)}">'
               f'GROUND COVER</text>')
    out.append(f'<text class="pp-l-note" x="{n1(bx + 214)}" y="{n1(y0)}" '
               f'fill-opacity="0.85">colour says what the ground is, '
               f'not how high it is</text>')
    out.append(f'<text class="pp-l-region" x="{n1(sx0)}" y="{n1(y0)}">'
               f'SCALE</text>')
    out.append(f'<text class="pp-l-note" x="{n1(sx0 + 92)}" y="{n1(y0)}" '
               f'fill-opacity="0.85">an oblique has no one scale; '
               f'these are along the sight-line</text>')
    out.append(f'<path class="pp-neat-i" d="M{n1(bx)} {n1(y0 + 9)}'
               f'H{n1(sx0 - 40)}M{n1(sx0)} {n1(y0 + 9)}H{n1(rx)}" '
               f'stroke-opacity="0.5"/>')

    kw, kh, row, col = 30.0, 16.0, 36.0, 600.0
    ky0 = y0 + 32.0
    for i, (cls, name, gloss) in enumerate(COVER_KEY):
        sx = bx + (i % 2) * col
        sy_ = ky0 + (i // 2) * row
        # the wet delta's swatch is what the reader actually sees: the wash at
        # its own opacity over the fan it lies on, drawn the same way here as
        # on the plate, so the key cannot promise a colour the sheet never
        # prints. (The matte the swatches used to carry is gone with the move:
        # it existed because the key floated on ground that was itself one of
        # these classes. In the margin every swatch is already on page.)
        base = COVER_TOKEN.get(cls, COVER_TOKEN[COVER_FAN])
        out.append(f'<rect class="pp-key-sw" x="{n1(sx)}" y="{n1(sy_)}" '
                   f'width="{n1(kw)}" height="{n1(kh)}" fill="var({base})"/>')
        if cls == "wet":
            out.append(f'<rect x="{n1(sx)}" y="{n1(sy_)}" width="{n1(kw)}" '
                       f'height="{n1(kh)}" fill="var(--pp-cover-wet)" '
                       f'fill-opacity="{COVER_WASH_OP:g}"/>')
        out.append(f'<text class="pp-l-note" x="{n1(sx + kw + 9)}" '
                   f'y="{n1(sy_ + 7)}" letter-spacing="0.9">{esc(name)}</text>')
        out.append(f'<text class="pp-l-note" x="{n1(sx + kw + 9)}" '
                   f'y="{n1(sy_ + 20)}" fill-opacity="0.85">{esc(gloss)}</text>')
    out.append(f'<text class="pp-l-note" x="{n1(bx)}" y="{n1(ky0 + 2 * row + 8)}">'
               f'{esc(COVER_KEY_UNDRAWN)}</text>')

    # the two bars, at the two depths the plate is mostly about
    for k, (d, lbl) in enumerate(((ship_depth, "1 km at the ships"),
                                  (troy_depth, "1 km at Ilios"))):
        px = FOCAL * 1000.0 / d
        yy = ky0 + 9.0 + k * 32.0
        out.append(f'<path class="pp-neat-i" d="M{n1(sx0)} {n1(yy)}h{n1(px)}'
                   f'M{n1(sx0)} {n1(yy - 4)}v8M{n1(sx0 + px)} {n1(yy - 4)}v8" '
                   f'stroke-width="1.1"/>')
        out.append(f'<text class="pp-l-note" x="{n1(sx0 + px + 9)}" '
                   f'y="{n1(yy + 3.5)}">{lbl}</text>')

    # ── the disclosures, cut from five lines to three. Nothing that was a
    # CLAIM has gone: every citation, the measured/conjectural split, the
    # never-an-invented-coordinate rule, how the reconstruction is drawn and
    # the DRAFT stamp are all still here. What went was the prose around
    # them, and one whole line that was explaining the key, which the key now
    # says itself.
    ty = ky0 + 2 * row + 44.0
    for line in (
        disclosure() + " " + sun_disclosure(),
        "Measured: terrain, coastlines, rivers, Hisarlık, Callicolone, Sigeion, "
        "Rhoiteion. Conjectural: the ships, the huts, the wall and ditch, and every "
        "waypoint of the poem — each placed by a stated rule, never at an invented "
        "coordinate. The ridges are this sheet's own DEM outlines, the wet delta its "
        "10–15 m slope-under-1.2% mask, the dry fan what the plain sector has left.",
        "The bay is the reconstructed Late Bronze Age embayment (Kraft, Kayan and Erol "
        "1980; Kayan); its shore is approximate, drawn as a hairline against the modern "
        "coastline's heavier survey line. Height is in the geometry and the light"
        + {"all": ", and in the contour hairlines.",
           "index": ", and in the index contours at 10, 30, 110 and 600 m.",
           "none": " alone; no contours are drawn."}[CONTOURS]
        + " DRAFT.",
    ):
        out.append(f'<text class="pp-l-note" x="{n1(bx)}" y="{n1(ty)}">{esc(line)}</text>')
        ty += 18
    return "".join(out)


# ═══════════════════════════════════════════════════════════════════════════
# assembly
# ═══════════════════════════════════════════════════════════════════════════
DEFS = ''          # set by build(): three of the four gradients need the camera


# ── GRADIENTS, AND THE ONE TRICK THAT KEEPS THEM RE-THEMABLE ─────────────
# Every colour on this plate is a var() token and a gradient does not change
# that, but it does constrain HOW: two tokens cannot be interpolated between,
# because the interpolation would have to happen at authoring time and would
# bake a literal. So no ramp here ever interpolates colour. Each ramp is ONE
# token whose stop-OPACITY varies, laid over a flat rect or fill of a second
# token. Opacity is a number, not a colour; the compositing is the browser's,
# in the reader's own theme, and swapping the two tokens re-themes the whole
# ramp. That is the same discipline the haze rects have always used, written
# as a gradient instead of as a stack.
SKY_GAMMA = 2.4    # how tightly the pale band hugs the horizon: brightness
                   # near the horizon rises as the air mass does, not linearly


def horizon_y(cam) -> float:
    """Screen y of the true horizon — where the z=0 plane goes to infinity.
    Everything about the sky is measured from it, so it is projected, never
    guessed at."""
    p = cam.project(math.sin(cam.theta) * 1e7, math.cos(cam.theta) * 1e7, 0.0)
    return p[1]


def plane_ramp(cam, alpha_of_range, n=44, r0=150.0, r1=70000.0):
    """Gradient stops over the z=0 plane, keyed by screen y.

    A pinhole camera with no roll maps a horizontal plane so that image y is
    a function of AXIAL DEPTH ALONE — lateral offset moves only the `right`
    component, which y does not see. So one vertical gradient over the bay
    is not an approximation of depth: on the sea plane it IS depth, exactly.
    The stops are projected from real ranges, and the alpha at each is
    whatever law the caller passes."""
    hy = horizon_y(cam)
    stops = []
    for k in range(n + 1):
        r = r0 * (r1 / r0) ** (k / n)
        e = cam.e + math.sin(cam.theta) * r
        nn = cam.n + math.cos(cam.theta) * r
        p = cam.project(e, nn, 0.0)
        if not p:
            continue
        stops.append((max(hy, p[1]) / H, alpha_of_range(r)))
    stops.sort()
    out, last = [], -1.0
    for off, a in stops:
        off = min(1.0, max(0.0, off))
        if off <= last:
            continue
        out.append((off, a))
        last = off
    return out


def _ramp(gid, token, stops):
    s = "".join(f'<stop offset="{o:.4f}" stop-color="var({token})" '
                f'stop-opacity="{a:.4f}"/>' for o, a in stops)
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="{H}" '
            f'gradientUnits="userSpaceOnUse">{s}</linearGradient>')


def make_defs(cam) -> str:
    hy = horizon_y(cam)
    # THE SKY. Flat --pp-sky-hi under a --pp-sky-lo ramp that goes from
    # nothing at the zenith to solid at the horizon. The exponent is the air
    # mass: looking up you see one atmosphere and the sky is its own dark
    # blue; looking level you see forty, and forty atmospheres of
    # forward-scattered light is the pale warm band every landscape has along
    # its horizon. Below the horizon the ramp holds at solid, so the holes
    # the far delta punches through the mesh read as distance and not as page.
    sky = []
    n = 12
    for k in range(n + 1):
        y = hy * k / n
        sky.append((y / H, (k / n) ** SKY_GAMMA))
    sky.append((1.0, 1.0))

    # THE BAY TAKES THE SKY, and it is Fresnel that says how much. Schlick's
    # approximation with water's R0 = 0.02: looking down at 70 degrees off
    # the vertical the bay shows a fifth sky and four fifths its own body
    # colour; at the far arm, eight degrees off the horizontal, it is five
    # sixths mirror. That single curve is the whole difference between a flat
    # blue shape and water, and none of it is invented — it is the camera
    # height, the range, and one constant.
    def fresnel(r):
        c = cam.z / math.hypot(cam.z, r)
        return min(1.0, 0.02 + 0.98 * (1.0 - c) ** 5)

    return (
        '<defs><filter id="pp-soft" x="-25%" y="-25%" width="150%" height="150%">'
        '<feGaussianBlur stdDeviation="9"/></filter>'
        + _ramp("pp-sky", "--pp-sky-lo", sky)
        + _ramp("pp-water-sky", "--pp-water-far",
                plane_ramp(cam, fresnel))
        + _ramp("pp-air", "--pp-haze",
                plane_ramp(cam, lambda r: haze_at(math.hypot(r, cam.z))))
        + f'<clipPath id="pp-frame"><rect x="23" y="23" width="{W - 46}" '
        f'height="{PIC_BOT - 46}"/></clipPath></defs>')


def build(terr, cam, plate_json):
    globals()["DEFS"] = make_defs(cam)
    P = Plate(terr, cam, plate_json)
    P.mesh()
    P.cull()
    P.cover_field()
    P.shade_field()
    body = ['<g clip-path="url(#pp-frame)">']
    # THE SKY IS NOT THE PAGE, and it is not a flat strip either. Left as bare
    # --page-bg it sat within a shade of the palest relief band, and every
    # patch of delta under 5 m in the far plain read as a hole punched through
    # the plate; a flat wash of coast ink over the page fixed that and left the
    # top fifth of the frame with nothing to be. It is now a graduated sky
    # (see make_defs) — dark and cool at the zenith, pale and warm along the
    # horizon, which is what forty air masses of forward-scattered light does
    # under a low sun.
    body.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                f'fill="var(--pp-sky-hi)"/>')
    body.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                f'fill="url(#pp-sky)"/>')
    ida, ida_crest = P.ida_svg()
    body.append(ida)
    body.append(P.terrain_svg())
    body.append(P.water_svg())
    body.append(P.rivers_svg())

    wps = P.waypoints()
    ships, huts, mass, wall_svg, ditch_svg, ship_px, obj_sh = P.camp()

    # wall and ditch, then huts, then ships: inland to seaward is also far to
    # near in this camera, so painter order is depth order.
    body.append(f'<g class="tm2">{wall_svg}{ditch_svg}</g>')
    # the fleet's own shadows go down on the beach BEFORE the fleet: 459 hulls
    # and 270 huts each throwing a true-length shadow is most of what makes
    # the camp read as objects standing on ground rather than marks on paper.
    body.append('<g class="tm2">' + "".join(obj_sh) + "</g>")
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
        # draped on a real DEM at 41 stations, so its kinks are the terrain's
        # sampling and not the road's course, which is conjectural anyway
        body.append('<g class="tm3"><path class="pp-road" d="%s"/></g>'
                    % rel_poly(soften(road, 2, closed=False), close=False))

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
                # A BARROW IS A BUILT MOUND and it stood on the plain casting
                # nothing, which is the citadel's defect in miniature. Its
                # shadow is the hull of a 14 m footprint and the shadow of its
                # own summit -- a cone's shadow, exactly, and the same call the
                # hulls and huts make.
                sil = [((14.0 * math.cos(a), 14.0 * math.sin(a)), 0.0)
                       for a in (0.0, 1.05, 2.09, 3.14, 4.19, 5.24)]
                sil.append(((0.0, 0.0), w["height"]))
                sd = object_shadow(cam, terr, lat, lon, 0.0, sil)
                marks.append(f'<g class="{tcls(tier)}">{sd}<path class="pp-tumulus" '
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
                     f'text{{stroke-width:{HALO_W * k:.2f}}}'
                     f'.pp-l-note{{font-size:{10 * k:.2f}px;'
                     f'stroke-width:{HALO_W_NOTE * k:.2f}}}')
    furn_css = "" if furn else ".pp-furn{display:none}"
    cap = ""
    if caption:
        k = 1.0 / max(scale, 1e-6)
        cap = (f'<text class="pp-l-region" x="{n1(vx + vw / 2)}" '
               f'y="{n1(vy + 34 * k)}" text-anchor="middle" '
               f'font-size="{15.5 * k:.2f}px" letter-spacing="{2.48 * k:.2f}px" '
               f'stroke-width="{HALO_W * k:.2f}">{esc(caption)}</text>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{px_w}" height="{px_h}" '
        f'viewBox="{n1(vx)} {n1(vy)} {n1(vw)} {n1(vh)}">'
        f'<style>svg{{{TOKENS[theme]}}}{CSS}{label_css()}{contour_css()}'
        f'{tier_css}{ds}{scale_css}{furn_css}</style>'
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
        # against the PICTURE, not the sheet: the margin below the neatline is
        # apparatus, and a postcard that frames it is framing the legend
        zoom = min(W / bw, PIC_BOT / bh)
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
        # w/h is the SVG's own box; pictureH is where the neatline closes and
        # the margin begins, which is the bound every crop has to respect
        "frame": {"w": W, "h": H, "pictureH": round(PIC_BOT)},
        "camera": {
            "viewpoint": list(VIEWPOINT), "headingDeg": HEADING_DEG,
            "hfovDeg": HFOV_DEG, "altM": ALT, "setbackM": SETBACK,
            "pitchDegDown": None,
            "verticalExaggerationCurve": CURVE,
            "verticalExaggerationNearRate": round(C_A, 4),
            "verticalExaggerationScaleM": round(C_L, 2),
            "verticalExaggerationFloor": round(C_F, 4),
            "verticalExaggeration": disclosure(),
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


def troy_prominence(terr, cam):
    """Ilios's apparent prominence in PIXELS at 1x: how far the drawn citadel
    top stands above the drawn plain around it, measured on the screen.

    The base is the 10th percentile of the ground in an annulus 700-1400 m out
    from Hisarlik, which is the plain the mound stands on; the top is the
    highest DEM sample within 250 m of it. Both are pushed through the live
    exaggeration curve and projected at the mound's own position, so the
    number is the drawing's, not the terrain's."""
    lat0, lon0 = pp.TROY
    dlat = 1.0 / 111132.0
    dlon = 1.0 / (111320.0 * math.cos(math.radians(lat0)))
    top = terr.elev(lat0, lon0)
    ring = []
    for a in range(0, 360, 5):
        th = math.radians(a)
        for r in (250.0,):
            e = terr.elev(lat0 + r * math.cos(th) * dlat,
                          lon0 + r * math.sin(th) * dlon)
            top = max(top, e)
        for r in (700.0, 900.0, 1100.0, 1400.0):
            ring.append(terr.elev(lat0 + r * math.cos(th) * dlat,
                                  lon0 + r * math.sin(th) * dlon))
    ring.sort()
    base = ring[int(0.10 * len(ring))]
    e, n = pp._flat_m((lat0, lon0), *VIEWPOINT)
    pt = cam.project(e, n, exaggerate(top))
    pb = cam.project(e, n, exaggerate(base))
    px = (pb[1] - pt[1]) if (pt and pb) else float("nan")
    return {"topM": round(top, 2), "baseM": round(base, 2),
            "reliefM": round(top - base, 2),
            "apparentM": round(exaggerate(top) - exaggerate(base), 2),
            "prominencePx": round(px, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(REPO, "build", "panorama"))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--curve", choices=("A", "B", "C"), default=CURVE,
                    help="vertical-exaggeration curve (see ve/exaggerate)")
    ap.add_argument("--ve-near", type=float, default=C_A,
                    help="curve C's ve(0): the exaggeration rate at the shore")
    ap.add_argument("--ve-scale", type=float, default=C_L,
                    help="curve C's decay scale in metres")
    ap.add_argument("--contour-w", type=float, default=CONTOUR_W)
    ap.add_argument("--contour-op", type=float, default=CONTOUR_OP)
    ap.add_argument("--contour-index-w", type=float, default=CONTOUR_INDEX_W)
    ap.add_argument("--contour-index-op", type=float, default=CONTOUR_INDEX_OP)
    ap.add_argument("--contours", choices=CONTOUR_MODES, default=CONTOURS,
                    help="all levels, the index levels only, or none — the "
                         "last piece of plan-map language on the sheet")
    ap.add_argument("--shade-az", type=float, default=LIGHT_AZ,
                    help="compass bearing the light comes FROM")
    ap.add_argument("--shade-alt", type=float, default=LIGHT_ALT)
    ap.add_argument("--sun-note", default=None,
                    help="the solar solution named in the cartouche; "
                         "REQUIRED whenever --shade-az/--shade-alt move")
    ap.add_argument("--ring-max", type=float, default=RING_MAX_M,
                    help="ground floor on ring spacing inside the plain "
                         "sheet, in metres (see RING_MAX_M)")
    ap.add_argument("--shade-smooth", type=int, default=SHADE_SMOOTH,
                    help="box passes over the CONTINUOUS light field, in "
                         "mesh cells (see SHADE_SMOOTH)")
    ap.add_argument("--shade-steps", type=int, default=SHADE_STEPS,
                    help="0 turns slope shading off")
    ap.add_argument("--shade-max", type=float, default=SHADE_MAX)
    ap.add_argument("--lit-max", type=float, default=LIT_MAX)
    ap.add_argument("--shade-gamma", type=float, default=SHADE_GAMMA,
                    help="terminator sharpness; <1 is sharper "
                         "(see SHADE_GAMMA)")
    ap.add_argument("--shade-min-area", type=float, default=SHADE_MIN_AREA)
    ap.add_argument("--no-shadow", action="store_true",
                    help="slope shading only -- no cast shadows")
    ap.add_argument("--no-obj-shadow", action="store_true")
    ap.add_argument("--shadow-step", type=float, default=SHADOW_STEP)
    ap.add_argument("--shadow-reach", type=float, default=SHADOW_REACH)
    ap.add_argument("--obj-shadow-op", type=float, default=0.3)
    ap.add_argument("--tag", default="",
                    help="suffix for every output name, so variants coexist")
    ap.add_argument("--variant", action="store_true",
                    help="the comparison render set: full plate in both "
                         "themes, the 8x Ilios crop in both, the camp zoom")
    args = ap.parse_args()
    globals()["CURVE"] = args.curve
    set_curve(args.ve_near, args.ve_scale)
    set_light(args.shade_az, args.shade_alt)
    if args.sun_note:
        globals()["SUN_NOTE"] = args.sun_note
    elif (abs(args.shade_az - LIGHT_AZ_DEFAULT) > 0.01
          or abs(args.shade_alt - LIGHT_ALT_DEFAULT) > 0.01):
        ap.error("--shade-az/--shade-alt moved without --sun-note: the "
                 "cartouche would name a sun the plate does not draw")
    globals().update(
        CONTOUR_W=args.contour_w, CONTOUR_OP=args.contour_op,
        CONTOUR_INDEX_W=args.contour_index_w,
        CONTOUR_INDEX_OP=args.contour_index_op,
        RING_MAX_M=args.ring_max, SHADE_SMOOTH=max(1, args.shade_smooth),
        SHADE_STEPS=max(0, args.shade_steps), SHADE_MAX=args.shade_max,
        LIT_MAX=args.lit_max, SHADE_GAMMA=args.shade_gamma,
        SHADE_MIN_AREA=args.shade_min_area,
        SHADOW=not args.no_shadow, OBJ_SHADOW=not args.no_obj_shadow,
        SHADOW_STEP=args.shadow_step, SHADOW_REACH=args.shadow_reach,
        OBJ_SHADOW_OP=args.obj_shadow_op, CONTOURS=args.contours)
    tag = args.tag
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"curve {args.curve} ve(0)={C_A:g} scale={C_L:g} floor={C_F:.4f} "
          f"(ceiling {max_near_rate():.2f}x): " + " ".join(
              f"{e:g}->{exaggerate(float(e)):.0f}"
              for e in (10, 25, 100, 300, 800, 1774)))
    print(f"sun az {LIGHT_AZ:g} alt {LIGHT_ALT:g} (shadow x{1.0 / max(1e-6, math.tan(math.radians(LIGHT_ALT))):.1f} "
          f"height), cast shadows {SHADOW}, object shadows {OBJ_SHADOW}")
    print(f"ring floor {RING_MAX_M:g} m inside {RING_DETAIL_FAR:g} m")
    print(f"{SHADE_STEPS} steps, shade<={SHADE_MAX:g} lit<={LIT_MAX:g}, "
          f"{SHADE_SMOOTH} smoothing + {SHADE_MEDIAN} median passes; contours "
          + ("OFF" if CONTOURS == "none" else
             f"{CONTOURS}: {CONTOUR_W:g}/{CONTOUR_OP:g}, index "
             f"{CONTOUR_INDEX_W:g}/{CONTOUR_INDEX_OP:g} at "
             f"{[LEVELS[k] for k in sorted(INDEX_LEVELS)]} m"))

    terr = Terrain()
    cam = Camera(terr.plain)
    with open(os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")) as f:
        plate_json = json.load(f)

    prom = troy_prominence(terr, cam)
    print("Ilios: " + " ".join(f"{k}={v}" for k, v in prom.items()))
    print(f"pitch {math.degrees(cam.pitch):.2f} deg down; focal {FOCAL:.1f}")
    inner, wps, P = build(terr, cam, plate_json)
    if "shadow_raster" in P.stats:
        n_ = P.stats["shadow_raster"]
        print(f"shadow raster {n_}x{n_} = {n_ * n_} samples in "
              f"{P.stats['shadow_secs']}s; {P.stats.get('shaded_cells', 0)} "
              f"toned cells, {P.stats.get('obj_shadows', 0)} object shadows, "
              f"{P.stats.get('shade_islands_filtered', 0)} tone islands "
              f"filtered by the median")
    print(f"smoothing: cover {COVER_SOFT} / tone {SHADE_SOFT_PASSES} / contour "
          f"{CONTOUR_SOFT} low-pass passes; worst contour move "
          f"{P.stats.get('contour_dev_px', 0.0):.2f} px, worst river move "
          f"{P.stats.get('river_dev_m', 0.0):.0f} m")
    cc = P.stats.get("cover_cells", {})
    print("ground cover: " + ", ".join(
        f"{k} {v} ({100 * v / max(1, sum(cc.values())):.0f}%)"
        for k, v in sorted(cc.items(), key=lambda kv: -kv[1])))
    print(f"mesh {len(P.azs)}x{len(P.rngs)} = {len(P.azs) * len(P.rngs)} nodes; "
          f"cells tested {P.stats['cells_tested']}, visible "
          f"{P.stats['cells_visible']} "
          f"({100 * P.stats['cells_visible'] / max(1, P.stats['cells_tested']):.0f}%)")
    print(f"hulls {P.stats['hulls']}, huts {P.stats['huts']}")

    tgt = camera_targets(wps, dict(P.stats))
    tgt["camera"]["pitchDegDown"] = round(math.degrees(cam.pitch), 2)
    tgt["stats"]["ilios"] = prom
    tp = os.path.join(args.out_dir, f"stage3-camera-targets{tag}.json")
    with open(tp, "w") as f:
        json.dump(tgt, f, ensure_ascii=False, indent=2)
    print(f"camera targets -> {tp} ({len(tgt['targets'])} rows)")

    if args.variant:
        # the comparison set: full plate both themes, the 8x Ilios crop both
        # themes, the camp zoom in light. Nothing else -- these renders exist
        # to be put side by side, not to ship.
        by_id = {t["id"]: t for t in tgt["targets"]}
        ic = by_id["ilios"]["camera"]
        for theme in ("light", "dark"):
            sfx = "" if theme == "light" else "-dark"
            svg = os.path.join(args.out_dir, f"stage3-full{tag}{sfx}.svg")
            w, h = emit(theme, inner, 0, 0, W, H, 1.0, svg, tier=1)
            shoot(svg, os.path.join(args.out_dir, f"stage3-full{tag}{sfx}.png"), w, h)
            print(f"[{theme}] full 1x {os.path.getsize(svg) / 1024:.0f} KB")
            cw, ch = W / 8.0, H / 8.0
            s2 = os.path.join(args.out_dir, f"stage3-zoom8-troy{tag}{sfx}.svg")
            w2, h2 = emit(theme, inner, ic["cx"] - cw / 2, ic["cy"] - ch / 2,
                          cw, ch, 8.0, s2, tier=3, descale=8.0)
            shoot(s2, os.path.join(args.out_dir,
                                   f"stage3-zoom8-troy{tag}{sfx}.png"), w2, h2)
        cw, ch = W / 4.0, H / 4.0
        s3 = os.path.join(args.out_dir, f"stage3-zoom-camp{tag}.svg")
        w3, h3 = emit("light", inner, 1250.0 - cw / 2, 665.0 - ch / 2, cw, ch,
                      4.0, s3, tier=3, descale=4.0)
        shoot(s3, os.path.join(args.out_dir, f"stage3-zoom-camp{tag}.png"), w3, h3)
        print("variant set done")
        return

    themes = ("light",) if args.quick else ("light", "dark")
    for theme in themes:
        sfx = "" if theme == "light" else "-dark"
        svg = os.path.join(args.out_dir, f"stage3-full{tag}{sfx}.svg")
        w, h = emit(theme, inner, 0, 0, W, H, 1.0, svg, tier=1)
        shoot(svg, os.path.join(args.out_dir, f"stage3-full{tag}{sfx}.png"), w, h)
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
            s2 = os.path.join(args.out_dir, f"stage3-zoom-{name}{tag}{sfx}.svg")
            w2, h2 = emit(theme, inner, cx - cw / 2, cy - ch / 2, cw, ch, 4.0, s2,
                          tier=3, descale=4.0)
            shoot(s2, os.path.join(args.out_dir, f"stage3-zoom-{name}{tag}{sfx}.png"), w2, h2)
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
        s2t = os.path.join(args.out_dir, f"stage3-full-tier2{tag}{sfx}.svg")
        w2t, h2t = emit(theme, inner, 0, 0, W, H, 1.0, s2t, tier=2)
        shoot(s2t, os.path.join(args.out_dir, f"stage3-full-tier2{tag}{sfx}.png"), w2t, h2t)
        ph = PIC_BOT
        pw = ph * (390.0 / 780.0)
        s3 = os.path.join(args.out_dir, f"stage3-mobile-portrait{tag}{sfx}.svg")
        w3, h3 = emit(theme, inner, 1376 - pw / 2, 0, pw, ph, 780.0 / ph, s3,
                      tier=1, descale=780.0 / ph, furn=False,
                      caption="THE SHIPS, THE BAY, AND ILIOS")
        shoot(s3, os.path.join(args.out_dir, f"stage3-mobile-portrait{tag}{sfx}.png"), w3, h3)
    print("done")


if __name__ == "__main__":
    main()
