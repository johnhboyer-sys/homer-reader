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
           ships as A RANK OF HULLS, fewer berths at two and a half times
           the ship, length and beam alike and declared in the key, with the
           huts behind them. (The huts sit at tier 1
           on purpose: without them the near third of the frame is bare
           ridge, and a fleet with no camp behind it reads as a mark rather
           than as an army's quarters.)
       t2  ~2-3x: the true fleet resolves under the rank -- every berth, five
           rows deep at a true 13 m pitch; the delta swamp,
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
     a light rim, not a light hull. The camp is now FOUR materials and each
     one carries the line that puts it there: pitch, the painted prow
     (κυανόπρῳρος, and μιλτοπάρῃοι for Odysseus's twelve), fir timber and
     cut reed. See the note above TOKENS.

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

# ── two plates, one script (John, 2026-09-02 14:47) ──────────────────────
# One camera cannot show the fleet on the Aegean flank and Troy across the
# bay at once. Default is plate A, the previous composition; B/B1/B2 look
# at the camp from over the sea. apply_plate_preset writes these.
PLATE = "A"
PLATE_FAMILY = "A"
DRAW_FLEET = False
DRAW_HUTS = False
PLATE_TITLE = "THE BAY AND ILIOS"
PLATE_SUBTITLE = (
    "the plain of Troy from above the Achaean camp, looking east-south-east")

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
# THAT IS 44% OF THE SHEET AND IT WAS RE-EXAMINED (2026-08-14), on the
# suspicion that the blank was a SCOPING artefact rather than an absence of
# evidence: the ridge-scrub default is graded INFERABLE from a regional
# analogue, and a regional analogue does not stop at a sector line. The
# suspicion is right about the CLASS and wrong about the FILL, and two things
# settle it.
#
#   1. THERE IS NO RULE TO CARRY OUTWARD. The specification does not derive
#      the ridges from a criterion; it reuses three existing polygons --
#      "this sheet's own relief-sigeion-ridge, relief-troy-ridge and
#      relief-rhoiteion-ridge layers already isolate exactly this ground by
#      elevation and slope. Reuse those polygons ... rather than re-deriving
#      elevation thresholds" (§2.4). Read the three layers and the sentence
#      turns out to be describing a coincidence, not a rule: they are cut at
#      the 20 m, 40 m and 100 m contours respectively, each chosen because it
#      was the contour that isolated THAT landform ("no contour isolates the
#      Troy ridge, because it is a spur and not a hill"). Three different
#      thresholds are not one criterion, and inventing the criterion they do
#      not share, in order to run it over the hinterland, would be deriving a
#      boundary the sources do not have -- which is the specific move every
#      class on this sheet is written to avoid.
#   2. THE 44% IS NOT ONE THING, AND THE POEM SAYS SO. Mount Ida lies inside
#      it, and the Iliad puts tall timber on Ida twice over: the Achaeans
#      climb κνημοὺς ... πολυπίδακος Ἴδης and cut δρῦς ὑψικόμους for the pyre
#      (23.117-19), and Sleep hides in an ἐλάτη περιμήκετος there (14.287).
#      Washing the whole hinterland in ridge scrub would assert maquis over
#      the one ground on this sheet the poem explicitly calls forest. The
#      blank is doing real work: it is the difference between "we have not
#      classified this" and "we have classified this wrongly, at scale".
#
# So the fill stays, the key now says WHY rather than only THAT, and the
# bareness it contributes is answered where it can honestly be answered --
# by putting on the ground the things that are attested to be on it. See the
# VEGETATION note.
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
COVER_DROWNED = "drowned"  # a gap between the two drawn shores, below the
                           # reconstruction's own cut (see SHORE_CUT_M)
# Painter order within a depth stratum. The classes tile the ground without
# overlap, so this decides nothing but which seam-stroke laps which.
COVER_ORDER = (COVER_OPEN, COVER_RIDGE, COVER_FAN, COVER_DROWNED)
COVER_TOKEN = {COVER_FAN: "--pp-cover-fan", COVER_RIDGE: "--pp-cover-ridge",
               COVER_OPEN: "--pp-cover-open", COVER_DROWNED: "--plate-lagoon"}
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
# ── the coastlines, and a defect this dial fixes ─────────────────────────
# THE SHORELINES ARE DEM STAIRCASES. `sea-modern` is contoured from the
# Copernicus GLO-30 water mask at 30 m posting and `lagoon-bronze` is cut
# from the same 30 m SRTM grid, so both rings step in 30 m risers -- their
# own note says so ("Contoured from the ocean class of the ... Water Body
# Mask at 30 m posting"). In plan that is invisible. In THIS camera it is
# not, because at the far left of the frame the Aegean shore runs nearly
# ALONG the line of sight, and a 30 m riser across the sightline projects to
# 8 px of lateral swing at 6 km while the run advances barely 2 px down the
# screen. Measured on the shipped frame at x 90-190, y 495-530: the outline
# reverses direction eleven times in twenty-two vertices, swinging x by 109,
# 174 and 197 screen px 605-621 while the DEPTH falls monotonically from
# 6477 m to 5573 m. The ring therefore crosses its own scanline three times
# instead of once, the nonzero fill rule cancels over the crossings, and two
# triangular slivers of `--pp-cover-open` ground print THROUGH the sea with
# `pp-coast` drawing the zigzag round them: John's "what's this?" at the left
# edge, and the same defect class cull() already documents for the mesh
# ("the nonzero fill rule CANCELS over the overlap and the page shows
# through"). chaikin's two passes inside water_path could not touch it --
# corner-cutting halves a staircase's corners, it does not remove a riser
# whose amplitude is the grid.
#
# THE LOW-PASS RUNS IN WORLD METRES, BEFORE THE PROJECTION, exactly as
# RIVER_SOFT does and for the same reason: the artefact is a property of the
# source grid, not of the camera, so it is removed at its own scale and the
# same amount everywhere, rather than by however much this particular oblique
# happens to magnify it. What comes out is asserted against the grid it was
# cut from -- the worst displacement is printed every run and pinned in
# test_panorama_relief.py at under one 30 m cell, which is the honest bound: a
# line smoothed off its own posting would be a line we no longer measured.
COAST_SOFT = 6
COAST_STEP_M = 30.0      # the source posting, so the filter sees one feature
                         # size all the way round the ring (see coast_ring)
# ── AND THE OTHER HALF OF THE LEFT-EDGE DEFECT, WHICH IS A DATA GAP ──────
# False-colouring the three layers at the artefact settled what it is, and it
# is not the fold this file's cull() documents. Between the modern sea and
# the reconstructed bay, at the bay's MOUTH, the two rings do not meet: they
# are independently derived -- sea-modern from the Copernicus 30 m water
# mask, lagoon-bronze flood-filled to the 10 m contour -- and at 39.99 N,
# 26.24 E a tongue of unclassified ground about 150 m long and 40 m across
# the neck is left standing between them, with the reconstruction's own
# boundary wrapping round it. That tongue is ground between the modern
# waterline and the 10 m contour, which is exactly the sediment the delta has
# gained since; the reconstruction says it was water, so the gap is a
# connectivity defect in the source polygon and not a landform.
#
# THE DATA IS NOT THIS FILE'S TO REPAIR. lagoon-bronze lives in
# apparatus/plates/trojan-plain.json and scripts/fix-lagoon-connectivity.py
# owns its flood fill; both are outside this lane. What IS this file's to
# decide is whether a plate may assert a landform NARROWER THAN THE INK IT IS
# DRAWN WITH -- the tongue's neck is under a pixel at 6 km, and the coast
# stroke, the approximate-shore hairline and two waterlines are laid across
# it four times over. It may not: that is ordinary cartographic
# generalisation, the same judgement SHADE_MIN_AREA already makes ("below
# this a tone region is a sliver, not a slope") and inset() already makes
# when it drops a concavity narrower than its own offset.
#
# THE CUT IS SURGICAL, not a blur. A closing (offset out, offset back) would
# have generalised the WHOLE ring to remove one notch. Instead the ring is
# searched for places where it returns within COAST_NECK_M of itself after
# running at least COAST_NECK_GAP samples, and the loop between them is
# spliced out. Everything else is left at the vertex it was at: the
# displacement this introduces is zero except across the neck it removes, and
# the count of cuts is printed every run so a silent one cannot happen. The
# Dardanelles is 1.3 km across at its narrowest here, twenty times the
# threshold, so nothing that is really a strait can be closed by it.
COAST_NECK_M = 60.0      # two cells of the source grid
COAST_NECK_GAP = 8       # samples; a neck must enclose at least 240 m of ring
# ── AND THE GAP ITSELF, WHICH THE DEM SETTLES ───────────────────────────
# The tongue survived the neck cut, so the DEM was asked what stands there.
# Forty-seven mesh nodes across it, at 7.0-7.5 km: the ground runs 0.0 to
# 4.6 m, most of it under 1 m, and the nodes at 0.7-2.6 m sit in NEITHER
# sea-modern NOR lagoon-bronze. That is decisive. lagoon-bronze is flood-
# filled to the 10 m contour (SHORE_LEVEL, prep-terrain-contours.py:1034),
# so ground at 1 m is ground the reconstruction itself says was water, and
# the only reason it is not inside the polygon is that the fill did not reach
# round the mouth. It is a hole in the source layer, not a bar across the
# bay -- and a plate that paints dry-fan colour on it is stating a landform
# the reconstruction denies.
#
# THE RULE THAT FILLS IT IS THE RECONSTRUCTION'S OWN, and nothing else. A
# visible cell is DROWNED when all three hold: it lies below the level the
# reconstructed shore is cut from; it is inside neither drawn water ring; and
# it is within DROWN_REACH_M of the drawn reconstructed shore. The third
# clause is the safety catch, and it is why this cannot quietly repaint the
# delta: the rule is only allowed to close gaps at the water's own edge, and
# the count of cells it takes is printed on every run and pinned in
# test_panorama_relief.py. It invents no coordinate -- every input is this
# sheet's own DEM and this sheet's own drawn rings.
SHORE_CUT_M = 10.0       # the contour lagoon-bronze was filled to
DROWN_REACH_M = 130.0    # how far from EACH drawn shore a gap may be closed
# BOTH SHORES, AND THAT CLAUSE IS THE WHOLE SAFETY CATCH. Requiring only
# "below the cut and near the reconstructed shore" is not a gap rule, it is a
# re-flooding rule, and it showed: the modern Scamander spit lies between the
# two waters at 2-8 m, so half of it went under the bay's wash and the plate
# grew a rash of blue blotches across ground the source polygon had
# deliberately left out. A GAP is where the two shores nearly touch and the
# ground is stranded between them, so the test is proximity to BOTH -- which
# the spit's interior fails, being a hundred and fifty metres wide.


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
SHADE_SIMPLIFY = 0.7     # px of Douglas-Peucker on a wash edge. It was 0.8
                         # while an edge was the seam between two tones seven
                         # tenths apart, then 1.1 once a nested wash edge
                         # carried only one eighteenth of the tone. It is back
                         # to the COVER's own 0.7 because of the stratum seam
                         # below: a wash edge that wanders 1.1 px away from the
                         # cover edge cut at the same range leaves a hole, and
                         # the hole is multiplied by however many washes are
                         # stacked there.
# ── THE PALE HAIRLINE ACROSS THE FOREGROUND (2026-08-14) ─────────────────
# "what's this line?" (John, on a crop of the near ridge): a fine, continuous,
# LIGHTER-than-its-ground line running diagonally across the foreground, and
# nothing on the sheet it could be. It is a DEPTH-STRATUM SEAM in the slope
# shading, and it was found by elimination, not by guessing:
#   --shade-max 0 --lit-max 0   the line goes. So it is in the washes.
#   --lit-max 0 alone           the line stays, unchanged. So it is --pp-shade.
#   --shade-min-area 0          no change. Not the sliver filter.
#   STRATA_EDGES moved 1600/1100/750 -> 1400/1000/700: the line VANISHES from
#                               its old position. So it is a stratum join.
#   --shade-steps 1             the line is still there at one wash, at 73% of
#                               the ground's own tone: the hole is about 0.3 px
#                               of a pixel's width, and it is EIGHTEEN NESTED
#                               WASHES all missing the same sliver that turns a
#                               sub-pixel gap into 26 levels of luminance.
# The mechanism: a stratum's ground cover is opaque and repaints the join, so
# the farther stratum's shading is erased under it; the nearer stratum's own
# wash, generalised on its own loop with its own tolerance, does not land on
# exactly the same line, and the sliver between them shows unshaded cover.
# The cover has always closed its own seams by stroking a band in its own fill
# (see terrain_svg); the washes were explicitly NOT stroked, on the reasoning
# that "a gap between two tones just reads as the tone between them" -- true
# WITHIN a stratum, where the neighbour tone is one step away, and false ACROSS
# one, where the neighbour is bare cover.
# So the washes now carry the same device, at a third of the width. It is a
# reduction and not a cure, and the honest reason is that two independently
# generalised polylines cannot be made to coincide: measured on the worst seam
# in the frame, +26 and +25 luminance became +1 and -4; on the next, +13 became
# +7 and -8. A wider stroke closes the gap and opens a DARK one in its place
# (at 0.7 the same seam reads -14), because the stroke then laps the far
# stratum's surviving wash and doubles it. 0.25 is where the two errors are
# smallest together.
SHADE_SEAM_W = 0.25      # px of own-tone stroke on a wash, to close the join
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


def cut_necks(ring, d=COAST_NECK_M, gap=COAST_NECK_GAP):
    """Splice out loops of a closed ring whose NECK is narrower than `d`.

    See COAST_NECK_M. Returns (ring, cuts). The scan is greedy and runs to a
    fixed point: cutting one neck can expose another, and a ring with none
    costs one O(n^2) sweep that finds nothing."""
    cuts = 0
    for _ in range(6):
        n = len(ring)
        if n < gap * 3:
            break
        found = None
        for i in range(n):
            xi, yi = ring[i]
            for k in range(gap, n - gap):
                j = (i + k) % n
                xj, yj = ring[j]
                if math.hypot(xi - xj, yi - yj) < d:
                    found = (i, k)
                    break
            if found:
                break
        if not found:
            break
        i, k = found
        # keep the LONGER of the two arcs the neck divides: a neck cuts a ring
        # into the body and the tongue, and the tongue is the short one
        keep = ([ring[(i + m) % n] for m in range(k, n + 1)] if k * 2 < n
                else [ring[(i + m) % n] for m in range(0, k + 1)])
        if len(keep) < 8:
            break
        ring = keep
        cuts += 1
    return ring, cuts


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


def object_shadow(cam, terr, lat, lon, bearing, silhouette, drape=False,
                  lift=0.0):
    """The shadow one built object throws on the ground.

    `silhouette` is [((u, v), height)] in the object's own frame: the points
    whose shadows bound the figure. Each contributes its foot and its shadow
    point, and the shadow is their convex hull -- exact for a convex solid,
    which a hull and a gabled hut both are.

    `lift` is the height of the object's UNDERSIDE, and it is the whole of
    the ships-on-props fix (SHIP_KEEL_H). A thing standing on the ground has
    lift 0 and its shadow starts at its own footprint, which is right for a
    hut and was wrong for a galley: shade hard against the outline all the
    way round is the one cue that reads as CONTACT, and it is what made the
    fleet look buried. A hull 0.9 m up on its ἕρματα casts from its keel, not
    from the sand, and at this plate's 9.9-degree sun that throws the near
    edge of the shade 5.2 m clear -- so daylight runs under every ship. The
    default reproduces the old behaviour exactly, since sun_offset(0) is
    (0, 0) and the foot is its own shadow.

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
    lx, ly = sun_offset(lift)
    for (u, v), h in silhouette:
        e = e0 + u * ux + v * vx
        n = n0 + u * uy + v * vy
        world.append((e + lx, n + ly))
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


# ── THE OVERVIEW'S RANK. Every number here is a DRAWING decision and the
# key declares it as one; none of them is a claim about the fleet. The true
# fleet — 13 m of lateral pitch, five rows 38 m apart, a 4.2 m beam — is
# untouched and is what the zoom shows. See camp() for why there are two.
#
# MEASURED, at the depth the ships are drawn at (about 2,600 m, 0.635 px per
# metre across the sight-line):
#
#     pitch   beam_k   ink   air   what it looks like at 1x
#     13 m      1.0    2.7    5.6   the rows behind fill the air: one band
#     26 m      1.8    4.7   11.8   a dotted line; ships too small to read
#     26 m      2.6    6.9    9.6   hull, air, hull — a fleet drawn up
#     26 m      3.4    9.0    7.5   the hulls touch again at the bends
# ── THE TRUE FLEET'S RANKS, προκρόσσας (14.35) ───────────────────────────
# 14.30-36 is exact about the SHAPE and silent about the spacing: the beach
# could not hold them all in one line -- οὐδὲ γὰρ οὐδ' εὐρύς περ ἐὼν
# ἐδυνήσατο πάσας / αἰγιαλὸς νῆας χαδέειν -- so they hauled them up
# προκρόσσας, in successive ranks, and filled the whole mouth of the shore
# between the headlands. Rows are the poem's; how many and how far apart are
# the drawing's, and both moved here.
#
# 5 ROWS AT 38 m WAS A TANGLE, and it was arithmetic, not taste. A galley is
# 24 m and her stem-post reaches 26.9, so 38 m of pitch leaves 11 m of clear
# sand between one row and the next. That is generous on the ground and
# nothing at all on the page: MEASURED at the camp's 2.4-2.6 km, ten metres
# of DEPTH projects to 0.5-1.2 px down this sight-line while ten metres
# ACROSS it projects to 4.0. The rows were therefore separated by about one
# pixel while each ship stood 2.5 px tall on her stem-post, so every row was
# drawn straight through the row in front. At 8x the fleet was hulls sitting
# inside one another.
#
# 3 rows at 74 m puts ~47 m of sand between ranks, which is 3-5 px of screen
# against the same 2.5 px of ship: the ranks now read as ranks receding, and
# what overlap remains is perspective doing its proper work rather than
# geometry failing. It costs count, and count is the one thing the key has
# always declared free ("filling the frontage in view and never the
# catalogue's count"). 3 x 74 = 222 m of camp depth, still well inside the
# 300 m at which the huts begin.
FLEET_ROWS = 3
FLEET_ROW_M = 74.0

# ── HOW BIG THE OVERVIEW DRAWS A SHIP, AND WHY IT IS DECLARED ────────────
# "are the ships rightly sized for scale? they read as ships now but they
# look frigging huge relative to everything else" (John). He is right that
# it was wrong; the mechanism is not the one it looks like, and the numbers
# matter enough to keep here, because they will be re-litigated.
#
# MEASURED, one berth mid-camp (2,500 m out, 300 m lateral, her bearing 14
# degrees off the heading), hull path extent on the sheet against a 7 m hut
# at the same spot:
#
#     enlargement   drawn as   hull px   hut px   ship:hut
#        x1.0 true     24 m       3.98     3.37     1.18
#        x1.5          36 m       6.04     3.37     1.79
#        x2.0          48 m       7.96     3.37     2.36
#        x2.5          60 m       9.94     3.37     2.95
#        x3.0          72 m      11.85     3.37     3.51
#      len x3.4 /
#      beam x2.0       82 m      12.70     3.37     3.77   <- what shipped
#
# THE TRUE RATIO OF THE THINGS THEMSELVES IS 3.43 (a 24 m galley against a
# 7 m hut), and the first row of that table is the finding: drawn at TRUE
# SIZE a ship comes out 1.18 hut-lengths, barely a third of the ratio she
# ought to have. She is seen end-on down the sight-line, where ten metres of
# DEPTH projects to 0.5-1.2 px against 4.0 px for ten metres ACROSS it, so
# true-scale drawing does not deliver true scale on this camera -- it
# shrinks a ship by about three and keeps a hut whole. That is why the
# previous lane needed an enlargement, and its 3.77 was not an order of
# magnitude out: it was the closest rung to the truth. What was wrong with
# it is that it stretched LENGTH x3.4 against BEAM x2.0, and a shape pulled
# 1.7x along one axis stops being a ship and becomes a quill -- which is
# what read as huge, since a long dark hook carries far more weight than its
# 12.7 px. Weight, not extent.
#
# So: x2.5, LENGTH AND BEAM TOGETHER. It is the smallest rung on which a
# hull still resolves as a hull, it lands at 2.95 -- under the true 3.43,
# erring modest -- and it is isotropic, so what it enlarges is a ship and
# not a feather. The stem-post's stroke comes down with it (see .pp-post-t1)
# because half the perceived bulk was in that stroke and none of it in the
# geometry.
#
# TRUE SIZE IS THE HONEST DEFAULT AND IT IS NOT AVAILABLE HERE; the plate
# says so in the key, in its own words and with the number. A convention the
# plate does not declare is one it may not draw.
FLEET_T1_PITCH_M = 32.0     # lateral pitch of the rank, opened with the beam
FLEET_T1_ROWS = 2           # of the true three. Two still reads as ranks
FLEET_T1_ROW_M = 170.0      # and 170 m keeps a row's prows well clear of the
                            # row in front's sterns at 2.5x drawn length
FLEET_T1_FIRST_M = 90.0     # the seaward row's stern, back from the waterline
# RE-MEASURED FOR PLATE B (2026-09-02 correction round). The table above was
# built end-on, down the old single-plate camera's sight-line, where a
# ship's 24 m LENGTH foreshortens to almost nothing and only enlargement
# could recover it. Plate B's camera looks down the beach instead of across
# it (see plate_presets()), so a hull is seen close to BROADSIDE and its
# length survives the projection on its own: measured at the fleet centroid
# (39.9452, 26.16527), true size (K=1.0) already drew 11.8 px against a
# 3.8 px hut at the FIRST correction round's camera -- 3.10x, close to the
# true 3.43.
#
# RE-MEASURED AGAIN for the FOURTH round's camera (plate_presets()'s own
# note -- the pivot moved off the whole zone's geometric centre to the main
# qualifying run's own midpoint, which is what actually fixed the fleet's
# frame coverage). Measured at that run's own hull station nearest the new
# pivot (camp-axis -3978 m; lat/lon 39.91965, 26.15652), K=1.0 already
# draws 38.4 px -- inside the 30-40 px composition target on its own, no
# real enlargement needed this time. K=1.02 (39.2 px) is used only to keep
# K strictly > 1.0, as the test suite requires (a regression gate against
# the original setback=0 bug's zero-hull renders, not a claim that 2% is a
# meaningful correction). THE RATIO TO THE HUT STILL DOES NOT TRACK THE
# TRUE 3.43 (a ~9x deviation was measured and left as a known gap in the
# third round's note, for the reason given there: the pitch foreshortens
# the hut's across-view roof span harder than the hull's along-view
# length). Isotropic still: see the note above on what an anisotropic K
# did to the shape.
FLEET_T1_BEAM_K = 1.02
FLEET_T1_LEN_K = 1.02
DRY_MARGIN_M = 14.0         # sand that must show between a forefoot and the
                            # water. About six pixels of beach at the camp's
                            # depth: enough that a reader can SEE she is
                            # hauled out, which is the claim Il. 1.485 makes.
FLEET_T1_STERN_H = 5.4      # the ἄφλαστον, in true metres above the beach
ODYSSEUS_TWELVE = 12        # δυώδεκα μιλτοπάρῃοι, Il. 2.637, and the number
                            # is the poem's own — the only count on this
                            # beach that IS a claim

# ── THE BEACH IS THE AEGEAN, NOT THE BAY (ruling 4, 2026-09-02) ──────────
# Kraft, Rapp, Kayan & Luce 2003 (after Luce 1998) put the camp on the
# outer (west) flank of the Sigeum ridge. The zone polygon's long axis
# bears 13.3°; seaward is perpendicular, west, 283.3°. The dossier has no
# published Bronze Age reconstruction of this outer coast, so the berth
# line is the modern Aegean shoreline (sea-modern).
CAMP_AXIS_DEG = 13.3
CAMP_SEAWARD_DEG = (CAMP_AXIS_DEG - 90.0) % 360.0   # 283.3, west
WALL_BEHIND_STERN_M = 60.0
DITCH_WEST_OF_WALL_M = 20.0
FLEET_FIRST_M = 66.0
KRAFT_2003_CITE = (
    "Kraft, John C., George Rapp, Ilhan Kayan, and John V. Luce. "
    '"Harbor Areas at Ancient Troy: Sedimentology and Geomorphology '
    'Complement Homer\'s Iliad." Geology 31, no. 2 (2003): 163-66.'
)


def camp_origin(camp_zone):
    return (sum(p[0] for p in camp_zone) / len(camp_zone),
            sum(p[1] for p in camp_zone) / len(camp_zone))


def camp_ll(origin, along, west):
    """Metres along the camp axis and west (seaward) of the centroid."""
    p = pp._dest_point(origin, CAMP_AXIS_DEG, along)
    return pp._dest_point(p, CAMP_SEAWARD_DEG, west)


def camp_axis_stations(camp_zone):
    """Central station and the two long-axis ends of the camp zone.

    Along-positive is 13.3° (slightly east of north), so max along is the
    northern endpoint and min along the southern."""
    origin = camp_origin(camp_zone)
    alongs = []
    ath = math.radians(CAMP_AXIS_DEG)
    for p in camp_zone:
        e, n = pp._flat_m(p, *origin)
        alongs.append(e * math.sin(ath) + n * math.cos(ath))
    a0, a1 = min(alongs), max(alongs)
    return {
        "origin": origin, "a0": a0, "a1": a1,
        "south": camp_ll(origin, a0, 0.0),
        "north": camp_ll(origin, a1, 0.0),
        "centre": camp_ll(origin, 0.5 * (a0 + a1), 0.0),
    }


def aegean_fleet(sea_poly, camp_zone, lagoon_poly=None, pitch=13.0, rows=None,
                 row_m=None, first_m=None, stagger=11.0):
    """Stern anchors on the Aegean beach: west of the camp zone, dry against
    sea-modern, ranks stepping landward (east). No camera, no DEM."""
    if rows is None:
        rows = FLEET_ROWS
    if row_m is None:
        row_m = FLEET_ROW_M
    if first_m is None:
        first_m = FLEET_FIRST_M
    origin = camp_origin(camp_zone)
    alongs = []
    ath = math.radians(CAMP_AXIS_DEG)
    for p in camp_zone:
        e, n = pp._flat_m(p, *origin)
        alongs.append(e * math.sin(ath) + n * math.cos(ath))
    a0, a1 = min(alongs), max(alongs)
    # shore samples stay on the true fleet's 13 m grid; berths may step wider
    lat_span = [x * 13.0 for x in range(int(math.floor(a0 / 13.0)),
                                        int(math.ceil(a1 / 13.0)) + 1)]

    def wet(f, along):
        lat, lon = camp_ll(origin, along, f)
        return point_in_poly_ll(lat, lon, sea_poly)

    def west_edge(along):
        lo = None
        f = -400.0
        while f < 2000.0:
            lat, lon = camp_ll(origin, along, f)
            if point_in_poly_ll(lat, lon, camp_zone):
                lo = f
            elif lo is not None and f > 0:
                break
            f += 25.0
        return lo

    def shore_at(along):
        edge = west_edge(along)
        if edge is None:
            return None
        lo = None
        f = edge
        while f < edge + 2500.0:
            if wet(f, along):
                if lo is None:
                    return None
                a, b = lo, f
                for _ in range(4):
                    mid = 0.5 * (a + b)
                    if wet(mid, along):
                        b = mid
                    else:
                        a = mid
                return a
            lo = f
            f += 25.0
        return None

    shore = {L: shore_at(L) for L in lat_span}

    def seaward(lateral):
        xs, ys = [], []
        for k in range(-5, 6):
            q = shore.get(round((lateral + k * 13.0) / 13.0) * 13.0)
            if q is not None:
                xs.append(k * 13.0)
                ys.append(q)
        if len(xs) < 4:
            return CAMP_SEAWARD_DEG
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 0:
            return CAMP_SEAWARD_DEG
        dfdl = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
        nf, nl = 1.0, -dfdl
        L = math.hypot(nf, nl)
        th_s = math.radians(CAMP_SEAWARD_DEG)
        th_a = math.radians(CAMP_AXIS_DEG)
        de = (nf * math.sin(th_s) + nl * math.sin(th_a)) / L
        dn = (nf * math.cos(th_s) + nl * math.cos(th_a)) / L
        return math.degrees(math.atan2(de, dn)) % 360.0

    berths = []
    for lateral in [x * pitch for x in
                    range(int(math.floor(a0 / pitch)),
                          int(math.ceil(a1 / pitch)) + 1)]:
        fs = shore.get(round(lateral / 13.0) * 13.0)
        if fs is None:
            fs = shore_at(lateral)
        if fs is None:
            continue
        bearing = seaward(round(lateral / 13.0) * 13.0)
        for row in range(rows):
            f = fs - first_m - row * row_m + (stagger if row % 2 else 0.0)
            if f < 60:
                continue
            lat, lon = camp_ll(origin, lateral, f)
            if point_in_poly_ll(lat, lon, camp_zone):
                continue
            if lagoon_poly and point_in_poly_ll(lat, lon, lagoon_poly):
                continue
            berths.append((lateral, row, f, lat, lon, bearing))

    along0 = 0.0
    fs0 = shore.get(0.0)
    if fs0 is None:
        sampled = [(abs(k), k, v) for k, v in shore.items() if v is not None]
        if sampled:
            _, along0, fs0 = min(sampled)
    wall_back = first_m + (rows - 1) * row_m + WALL_BEHIND_STERN_M
    ditch_back = wall_back - DITCH_WEST_OF_WALL_M
    wall = camp_ll(origin, along0, fs0 - wall_back) if fs0 is not None else origin
    ditch = camp_ll(origin, along0, fs0 - ditch_back) if fs0 is not None else origin
    return {
        "origin": origin, "shore": shore, "berths": berths,
        "wall": wall, "ditch": ditch, "along0": along0, "fs0": fs0,
        "wall_back": wall_back, "ditch_back": ditch_back,
        "a0": a0, "a1": a1,
    }

SHIP_STATIONS = [(0.00, 0.30), (0.14, 0.46), (0.34, 0.50), (0.60, 0.48),
                 (0.82, 0.36), (0.95, 0.18), (1.00, 0.06)]
SHIP_DECK_H = 2.4         # true, and true is the point (see built_h)
SHIP_POST_H = 6.4
SHIP_PROW_F = 0.62        # forward of this the bow is PAINTED, not pitched

# ── ἕρματα ΜΑΚΡΑ: THE SHIPS STAND ON PROPS, AND THE POEM SAYS SO TWICE ────
# "the ships look like they are buried in the sand at an angle" (John), and
# he was reading the drawing correctly: the hull's flank ran from the deck
# down to h=0, so its outline met the sand the whole way round and the
# object had no side. A thing with no visible side is a shape painted on
# the ground, never a thing standing on it -- which is exactly why the huts,
# with their 1.8 m walls, never had the problem.
#
# The poem does not merely permit the fix, it states it:
#
#   νῆα μὲν οἵ γε μέλαιναν ἐπ' ἠπείροιο ἔρυσσαν
#   ὑψοῦ ἐπὶ ψαμάθοις, ὑπὸ δ' ἕρματα μακρὰ τάνυσσαν    Il. 1.485-86
#
# They hauled the black ship up onto the land HIGH upon the sands, and
# stretched LONG PROPS beneath it. ὑψοῦ is doing real work in that line and
# ἕρματα are the timbers that hold it there. The second attestation settles
# what the standing condition is: to LAUNCH, you take the props out --
# ὑπὸ δ' ᾕρεον ἕρματα νηῶν (Il. 2.154), the men pulling them from under the
# ships when they think they are going home. A beached galley is on props;
# a galley off its props is a galley going to sea. (Il. 14.410 has ἔχματα
# νηῶν for the same office in a different word; ἕρμα elsewhere is an
# earring, 14.182 and Od. 18.297, or the "prop of a city" said of Sarpedon,
# 16.549, and of the suitors, Od. 23.121. The ship sense is 1.485 and 2.154.)
#
# So the hull's flank now runs from the GARBOARD to the gunwale -- 1.5 m of
# freeboard, which is a galley's true hull depth -- and under it there is
# 0.9 m of air with the props raking out to the sand. The deck stays at its
# true 2.4 m and the stem-post at 6.4: nothing is stretched to buy this. It
# is the same 2.4 m, divided honestly into the part that is hull and the
# part that is prop, where before the drawing had spent all of it on hull.
#
# THE SHADOW IS WHAT SELLS IT. At a 9.9-degree sun a keel 0.9 m up throws
# its shadow 5.2 m down-sun, so a band of LIT SAND runs under every hull.
# The old shadow was the convex hull of the deck outline's FEET and their
# shadow points, which put shade hard against the hull all the way round --
# the one cue that says "in contact with the ground". See object_shadow's
# `lift`.
SHIP_KEEL_H = 0.9         # ἕρματα μακρά: how far the props hold her up
SHIP_KEEL_V = 0.45        # the garboard, inboard of the gunwale: the flank
                          # between them is the freeboard that was missing
SHIP_PROP_F = (0.18, 0.48, 0.78)   # where the shores stand along her length
SHIP_PROP_V = 0.62        # and how far outboard their feet rake to. 0.62 is
                          # INSIDE the gunwale (1.0), and that is the whole
                          # of it: at 1.15 the shores raked out past her own
                          # silhouette and every galley at 8x had legs. A
                          # rank of them was a column of beetles -- a dark
                          # body, a pair of antennae, six legs. Kept under
                          # her, the same timbers read as what they are,
                          # props in the shadow of a hull standing off the
                          # sand. Nothing about the drawing changed except
                          # whether the feet show outside the hull.


def ship(cam, terr, lat, lon, bearing, length=24.0, beam=4.2,
         beam_k=1.0, len_k=1.0, post_cls="pp-post", prow_cls="pp-prow",
         stern_h=0.0, props=False):
    """One beached galley, prow toward the water — which is the poem's own
    order: the ships are hauled up and the wall goes in behind them, τεῖχος
    ἐπὶ πρύμνῃσιν ἔδειμαν, built at their STERNS (Il. 14.32). Five marks:
    the freeboard, the deck in plan, the painted bow, the stem-post, and the
    props she stands on (Il. 1.485-86 — see SHIP_KEEL_H).

    THE MAST IS ABSENT AND THAT IS THE POEM'S STATE, not an omission. A ship
    coming to her moorings lowers it into the crutch — ἱστὸν δ' ἱστοδόκῃ
    πέλασαν προτόνοισιν ὑφέντες (1.434) — and steps it again only to sail
    (1.480, ἱστὸν στήσαντ'). The upright here is the stem-post at its true
    6.4 m; the recorded finding is that stretching it by the terrain's 4x
    turned every beached galley into a ship under sail.

    THE BOW IS PAINTED. κυανόπρῳρος, dark-blue-prowed, is the standing
    formula (15.693 = 23.852 = 23.878); μιλτοπάρῃοι, vermilion-cheeked, is
    said of Odysseus's twelve and of no one else in the Iliad (2.637), which
    is why prow_cls is a parameter and not a constant — see camp().

    beam_k and len_k are the DRAWN CONVENTION and never the ship. At 1x a
    true 4.2 m beam is 2.7 px on this sheet and 465 of them integrate into a
    band with no air in it, so the overview draws fewer hulls larger. HEIGHTS
    ARE NEVER SCALED: deck and stem-post stay at 2.4 and 6.4 m at every tier,
    so a glyph and a hull throw the same true-length shadow."""
    g = terr.elev(lat, lon)
    th = math.radians(bearing)
    ux, uy = math.sin(th), math.cos(th)
    vx, vy = math.cos(th), -math.sin(th)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)

    def W3(u, v, h):
        return cam.project(e0 + u * ux + v * vx, n0 + u * uy + v * vy, built_h(h, g))

    top_r, top_l, side, fs = [], [], [], []
    for f, hb in SHIP_STATIONS:
        u, v = f * length * len_k, hb * beam * beam_k
        pr = W3(u, +v, SHIP_DECK_H)
        pl = W3(u, -v, SHIP_DECK_H)
        # THE GARBOARD, NOT THE GROUND. This point used to be (0.8v, 0.0) --
        # the flank ran to the sand, the outline closed on the beach, and the
        # hull read as buried. It is now the turn of the bilge at its true
        # height on the props, and the quad between it and the gunwale is the
        # freeboard the drawing never had. See SHIP_KEEL_H.
        pg = W3(u, +v * SHIP_KEEL_V, SHIP_KEEL_H)
        if pr and pl and pg:
            top_r.append((pr[0], pr[1]))
            top_l.append((pl[0], pl[1]))
            side.append((pg[0], pg[1]))
            fs.append(f)
    if len(top_r) < 5:
        return ""
    out = []
    # THE PROPS GO DOWN FIRST, so the hull's own fill closes over their heads
    # and they read as timbers disappearing under her, not as legs stuck on.
    # They are drawn only where they can be seen: at 1x, 0.9 m is a third of
    # a pixel and 465 sub-pixel ticks are not props, they are a smear along
    # the beach that darkens it. The true fleet carries them and the overview
    # rank does not — which is the same division the stern ornament already
    # keeps, in the other direction.
    if props:
        segs = []
        for f in SHIP_PROP_F:
            u, v = f * length * len_k, beam * beam_k
            hb = next((h for ff, h in SHIP_STATIONS if ff >= f), 0.3)
            a = W3(u, +v * hb * SHIP_KEEL_V, SHIP_KEEL_H)
            b = W3(u, +v * hb * SHIP_PROP_V, 0.0)
            if a and b:
                segs.append(f'M{n1(a[0])} {n1(a[1])}L{n1(b[0])} {n1(b[1])}')
        if segs:
            out.append(f'<path d="{"".join(segs)}" class="pp-erma"/>')
    out += [f'<path d="{rel_poly(top_r + list(reversed(side)))}" class="pp-hull-side"/>',
            f'<path d="{rel_poly(top_r + list(reversed(top_l)))}" class="pp-hull"/>']
    # The painted bow, laid over the pitch: BOTH faces of it forward of
    # SHIP_PROW_F, in one path with two subpaths. The deck alone put the
    # colour on a sliver that narrows to nothing at the stem and the flank
    # alone put it on a strip that is edge-on there, so either by itself came
    # out at 8x as a single blue nick. παρήϊον is a cheek: the bow has two of
    # them and a foredeck between.
    k = next((i for i, f in enumerate(fs) if f >= SHIP_PROW_F), None)
    if k is not None and len(fs) - k >= 2:
        out.append('<path d="%s%s" class="%s"/>'
                   % (rel_poly(top_r[k:] + list(reversed(top_l[k:]))),
                      rel_poly(top_r[k:] + list(reversed(side[k:]))),
                      prow_cls))
    # the stem-post rises FORWARD, over the water. Curving it back over its
    # own deck (tip at 0.90 of the length, base at 0.98) gave every hull at
    # 8x the profile of a bird's head, and a rank of them was a rank of geese.
    base = W3(length * len_k * 0.97, 0.0, SHIP_DECK_H)
    mid = W3(length * len_k * 1.05, 0.0, 4.4)
    tip = W3(length * len_k * 1.12, 0.0, SHIP_POST_H)
    if base and mid and tip:
        out.append(f'<path d="M{n1(base[0])} {n1(base[1])}'
                   f'Q{n1(mid[0])} {n1(mid[1])} {n1(tip[0])} {n1(tip[1])}" '
                   f'class="{post_cls}"/>')
    # THE STERN ORNAMENT, ἄφλαστον (Il. 15.717, the thing Hector gets his
    # hands on) with the ἄκρα κόρυμβα, the stern-tips he means to hack off
    # (9.241). It is drawn because of where the reader is standing: the fleet
    # points at the water and the camera looks at the water, so what faces the
    # eye is 457 STERNS, and the stem-post at the far end is behind its own
    # hull. A rank of little dark slats with a horn rising at the near end of
    # each is a beach with ships drawn up on it; the same rank without the
    # horns is a row of lumps, which is what it was.
    if stern_h > 0.0:
        b2 = W3(length * len_k * 0.03, 0.0, SHIP_DECK_H)
        m2 = W3(-length * len_k * 0.07, 0.0, stern_h * 0.62)
        t2 = W3(-length * len_k * 0.04, 0.0, stern_h)
        if b2 and m2 and t2:
            out.append(f'<path d="M{n1(b2[0])} {n1(b2[1])}'
                       f'Q{n1(m2[0])} {n1(m2[1])} {n1(t2[0])} {n1(t2[1])}" '
                       f'class="{post_cls}"/>')
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


# ═══════════════════════════════════════════════════════════════════════════
# VEGETATION -- the poem names its trees, and that is the only reason any of
# them are here
# ═══════════════════════════════════════════════════════════════════════════
# THE PROBLEM WAS SCALE, NOT DECORATION. "it does feel a bit small. no trees
# or vegetation. only the little huts for scale" (John). A tree is the best
# scale cue a landscape has, and this sheet had none, so the plain read as a
# tabletop -- and the featureless ground was never a rendering artefact:
# docs/research/PHOTOGRAPHS-OF-THE-TROAD.md §2.2 found the fill pass "only
# ever paints one of: sea, lagoon, an elevation-banded relief colour, or a
# contour hairline... the 'featureless dome' is not a rendering artifact, it
# is the literal absence of a data layer."
#
# THE RULE, AND IT IS THE WHOLE OF IT: every plant on this sheet traces to a
# line of the Iliad or to a ground-cover class the specification already
# states. Nothing is scattered for interest. The corpus was read for each one
# (build/dist/iliad, the pipeline's own text) and the line is carried in the
# key beside the mark, the same way the ground-cover swatches carry theirs.
#
#   THE OAK, φηγός -- a NAMED INDIVIDUAL at the Scaean Gate. Il. 6.237
#       Ἕκτωρ δ' ὡς Σκαιάς τε πύλας καὶ φηγὸν ἵκανεν, repeated verbatim at
#       9.354 and 11.170; it is Zeus's tree and big enough to lay a wounded
#       man under (5.693 εἷσαν ὑπ' αἰγιόχοιο Διὸς περικαλλέϊ φηγῷ) and to
#       lean on (21.549 φηγῷ κεκλιμένος); two gods meet beside it (7.22
#       ἀλλήλοισι δὲ τώ γε συναντέσθην παρὰ φηγῷ).
#   THE WILD FIG, ἐρινεός -- a NAMED INDIVIDUAL by the wall. Il. 22.145
#       παρὰ σκοπιὴν καὶ ἐρινεὸν ἠνεμόεντα, the windswept fig; Andromache
#       posts the host at it because there the city is most scalable (6.433
#       λαὸν δὲ στῆσον παρ' ἐρινεόν, ἔνθα μάλιστα / ἀμβατός ἐστι πόλις), and
#       the rout runs past it across mid-plain (11.167).
#   THE RIVERBANK THICKET -- Il. 21.350-52, what Hephaestus's fire takes
#       along the Scamander: καίοντο πτελέαι τε καὶ ἰτέαι ἠδὲ μυρῖκαι, /
#       καίετο δὲ λωτός τε ἰδὲ θρύον ἠδὲ κύπειρον, / τὰ περὶ καλὰ ῥέεθρα ἅλις
#       ποταμοῖο πεφύκει. The third line is a LOCATIVE and it is why this can
#       be drawn at all: the poem says this assemblage grows about the
#       river's streams, not over the plain. Tamarisk twice more, both times
#       at the water or as a way-mark (21.18 κεκλιμένον μυρίκῃσιν; 10.466-67
#       θῆκεν ἀνὰ μυρίκην ... συμμάρψας δόνακας μυρίκης τ' ἐριθηλέας ὄζους).
#   RIDGE SCRUB -- not the poem's, and the key has always said so: a stated
#       Mediterranean-Aegean default for thin soil on exposed limestone
#       (GROUND-COVER-TROJAN-PLAIN.md §2.4), already a colour on this sheet.
#       All that is new is that the class now has a MARK as well as a tint.
#
# WHY A THICKET MAY BE DRAWN WHEN ITS EXTENT IS UNKNOWABLE. The specification
# grades the riverbank thicket POEM-ONLY with no derivable extent, because
# "with as much as 20 m of alluvium on the southern Scamander floodplain, we
# cannot hope to locate the river channels of antiquity" (Kraft, Rapp, Kayan
# and Luce 2003, 164). That grading stands and is not being argued with. What
# has changed is only what it is being asked to license. THIS SHEET ALREADY
# DRAWS THE SCAMANDER AND THE SIMOEIS -- schematic, modern-survey lines,
# declared as such in the cartouche -- and a fringe drawn ALONG a course the
# plate has already committed to adds no locational claim the plate is not
# already making. It says what 21.352 says: wherever the river ran, this grew
# beside it. Draw the same flora anywhere else on the plain and it becomes a
# new claim; draw it on the drawn line and it inherits that line's own
# register exactly, which is what §2.3 asks for ("tie this class to the
# schematic river line as a schematic band"). The one thing §2.3 forbids is
# printing a metre value for the fringe's width, so BANK_OFFSET_M is captioned
# in the key as an artist's convention and no width is stated on the sheet.
#
#   IDA'S TIMBER -- A WOODED MOUNTAIN, and not a single tree. Il. 23.114-20:
#       the Achaeans climb κνημοὺς ... πολυπίδακος Ἴδης and cut δρῦς
#       ὑψικόμους for the pyre; 14.287 puts an ἐλάτη περιμήκετος there. The
#       previous pass lettered this and refused to draw it, because at 45-80 km
#       behind 0.73 of --pp-haze a 20 m oak is a tenth of a pixel and no source
#       gives a treeline altitude. Both facts are true and neither is an
#       argument against the thing the poem actually says. A FORESTED MOUNTAIN
#       DOES NOT READ AS TREES AT ANY RANGE; it reads as a darker, cooler,
#       greener mass. That is a claim about TONE, so it places nothing and
#       needs no treeline -- and the tan the mountain carried was asserting the
#       opposite of the text over the whole horizon of the plate. Drawn as
#       colour, in .pp-ida, and nothing is planted on it.
#
# WHAT IS NOT DRAWN, and each because the text will not carry it:
#   A REED BED ON THE WET DELTA. Il. 21.351 does name θρύον and κύπειρον, and
#       a mass of reeds at 8 km would be perfectly drawable as a tone where an
#       individual stem is not. The specification forbids it in so many words,
#       twice, and the forbidden thing is exactly the mark that was wanted:
#       §5.8 rules out "lotus/rush/galingale colour or texture spread broadcast
#       across the whole swamp rather than confined to the river's immediate
#       margin -- the poem locates this flora 'around the river's fair streams'
#       (21.352), not over the delta generally", and §5.2 rules out "reed
#       forests" as wetland dressing. 21.351 is the same sentence as 21.352:
#       the locative that licenses the thicket is the locative that denies the
#       delta. The one passage that puts anything growing on marsh ground --
#       Erichthonius's mares pasturing ἕλος κάτα, 20.221 -- is graded by §4 as
#       "poem-only, and non-locating", and it is a stronger argument than it
#       looks, because the marsh here is placed by the DEM and not by that
#       line; it is recorded for John's call and NOT drawn on this lane's own
#       authority. What the wet delta does gain is the thicket, at the pitch
#       21.352's own ἅλις asks for, wherever the drawn courses cross it.
#   TAMARISK SCATTERED ON THE PLAIN. 10.466-68 is one man tying one way-mark
#       at a spot the poem does not locate, and the specification's own
#       reading is that the three passages "support tamarisk as a common,
#       way-marking shrub of wet or riparian ground, not a claim about its
#       density or range beyond the water's edge." So tamarisk is drawn, in
#       the thicket where 21.350 puts it, and nowhere else.
#   ANYTHING ON THE DRY FAN. The fertility epithets (6.315 Τροίῃ ἐριβώλακι;
#       20.226 ζείδωρον ἄρουραν) qualify the class and give no pattern, and
#       GROUND-COVER-TROJAN-PLAIN.md §5.3 forbids drawing furrowed grainfields
#       or plot boundaries outright. The fan therefore stays a flat bright
#       tone, which is also what Imhof prescribes for flat ground and what the
#       drawn-landscape survey found the whole tradition doing.
VEG = True
# Heights are TRUE metres and go through built_h, exactly as the hulls, the
# huts and the tumuli do, so every one of these throws a true-length shadow
# under the same 9.9-degree sun. That is what puts a tree ON the ground
# instead of over it, and it is most of why the plate now reads at a size.
OAK_H, OAK_R = 15.0, 8.0        # a mature valonia oak; the poem gives no
FIG_H, FIG_R = 8.0, 6.0         # height, so these are a drawing convention,
BANK_TREE_H, BANK_TREE_R = 13.0, 6.0    # stated in the key -- the same kind
BANK_SHRUB_H, BANK_SHRUB_R = 4.2, 3.4   # of convention as the hull's 24 m
SCRUB_H = 1.4                   # maquis, and the tick self-extinguishes
                                # with distance because a true height must
BANK_OFFSET_M = 26.0            # AN ARTIST'S CONVENTION, NOT A MEASUREMENT
                                # (GROUND-COVER-TROJAN-PLAIN.md §2.3): the
                                # poem gives no width for the fringe and the
                                # key says the sheet is not claiming one.
BANK_STEP_M = 62.0              # clump pitch at the overview; halved at the
                                # zoom tiers, so the thicket GAINS members
                                # rather than being drawn bigger. It was 96,
                                # and the POEM is why it came down: 21.352 has
                                # this assemblage growing ἅλις, "in abundance",
                                # about the river's streams. ἅλις is a density
                                # word in the text's own voice and a fringe
                                # with 96 m between clumps was not drawing it.
                                # Pitch is not a locational claim -- the clumps
                                # stay on the same drawn course at the same
                                # captioned offset -- so this is the one place
                                # on the sheet where more marks say something
                                # the poem itself says.
SCRUB_PX2_ZOOM = 84.0           # screen px^2 of ridge per tuft where the
                                # cover is at full density. It is the ZOOM
                                # figure and there is no longer a tier-1 one,
                                # because at the overview the class is not
                                # drawn as tufts at all (see below). It was
                                # 120, which was the right figure while the
                                # cover was even; a STAND has to hold together
                                # when the reader walks into it, and thirteen
                                # bushes across a hundred metres is a thicket
                                # at 1x and a scatter at 8x.
SCRUB_REACH = 16000.0           # m; the same reach the cast shadows take
VEG_MIN_PX = 0.75               # below this a mark is smaller than the ink

# ── AT PLATE SCALE, COVER IS A MASS AND NOT A CROWD (2026-08-14) ──────────
# "those look like individual trees" ... "it looks like stubble on a man's
# chin" (John), and both verdicts are arithmetic before they are taste. The
# camera is 800 m up and Ilios is 7 km out; a canopy 8 m across subtends
# well under a pixel there, so ANYTHING THE READER CAN COUNT at 1x is drawing
# a thing that cannot be seen. The old pass drew the same tuft everywhere the
# class applied, at one tick per fixed unit of screen area, and a constant
# pitch is what the eye locks onto: find the pitch and the marks become
# countable by construction, however small each one is.
#
# So the class is drawn TWICE, and the two drawings are different marks and
# not the same mark at two sizes:
#   TIER 1-2, THE OVERVIEW -- a MASS. Adjacent dense cells are merged into one
#       outline by union_loops (interior edges cost nothing) and the outline
#       is scalloped, so what prints is a lobed patch of cover with a broken
#       edge and no countable member. Two nested thresholds give it an
#       interior: a broad skirt at SCRUB_MASS_MIN and a darker core at
#       SCRUB_CORE_MIN, which is a wood's own tonal structure -- open at the
#       margin, closed in the middle -- and is read off the density field
#       rather than invented.
#   TIER 3, ZOOMED -- the TUFTS, at SCRUB_PX2_ZOOM, in the same places. At 4x
#       and 8x a 1.4 m bush genuinely is resolvable, so the mass dissolving
#       into its parts is not a trick; it is what happens when you walk
#       closer. The tufts are keyed to the same density field, so they crowd
#       where the patch was dense and thin where it was open.
#
# AND THE DENSITY IS MEASURED, WHICH IS WHY THE PATCHINESS COSTS NO HONESTY.
# Maquis and garrigue on thin limestone are not evenly spread. They collect
# where water and soil collect and thin where neither does, and all three
# controls are already in this file's own DEM:
#   CURVATURE -- concave ground (gully heads, hollows) gathers soil and water;
#       convex ground (crests, spurs) sheds both. The lattice Laplacian,
#       normalised by the local relief so it means the same thing at 2 km and
#       at 14 km.
#   SLOPE -- steep faces shed soil. Taken from the RAW ground normal, not the
#       exaggerated one the shading uses: the shading models the geometry the
#       sheet shows, but soil creeps down the real hill.
#   ASPECT -- the strong Mediterranean control, and free here. Sun-facing
#       ground bakes; shaded ground holds moisture. The sun bears 228.4, so
#       the south-west faces are the dry ones, and the term is the ground
#       normal against the light's own horizontal -- the same vector the
#       shading takes. It scales with slope by construction, which is right:
#       flat ground has no aspect.
# The result is a factor on density, not on placement. No plant moves to
# ground it did not already have, no class changes, and the key says in so
# many words that the DENSITY is a drawing rule and not a survey.
#
# AND THE ANSWER IS COPSES, NOT A LAWN (John, 2026-08-14: "clusters of trees.
# like idk a small forest"). The first pass at this modulated a constant
# gently and got a slightly uneven constant, which is stubble with a wobble in
# it. Real maquis and garrigue on thin soil over limestone is not an even
# cover with variation; it is CLUMPED -- kermes and holm oak, wild olive,
# terebinth, standing at tree form in the gullies and the hollows where the
# thin soil and the winter water collect, and bare rock on the convex, the
# steep and the baked. So the weights below use the field's whole range: where
# all three controls favour cover the density reaches a coherent stand, and
# where all three refuse it the ground goes BARE, not thin. The bare rock is
# not the absence of the drawing; it is half of it, and it is what lets the
# stands read as stands.
#
# THIS DOES NOT MOVE THE HONESTY LINE and it is worth saying where the line
# is. The CLASS is unchanged -- the regional default for this ground, no
# survey, no line of the poem, exactly as the key has always said. What varies
# is DENSITY, and it varies with three numbers the DEM already holds. No copse
# is placed by hand and none is placed by a text.
# THE POEM CONSTRAINS THE SIZE, THOUGH, AND IS ALLOWED TO. Il. 23.114-20 sends
# the Achaeans twenty-odd kilometres up Ida's spurs with mules to cut δρῦς
# ὑψικόμους for Patroclus's pyre. Men do not haul beams that far past timber,
# so the ground in this frame carries NO WOOD WORTH FELLING -- and a stand of
# scrubby holm oak in a ravine is not one, which is exactly why it may be
# drawn. What may not be drawn is a canopy sheet over a whole ridge, which
# would be a forest and would contradict the pyre. The patches are therefore
# held to the size of a wood a reader would walk across, by SCRUB_PATCH_MAX.
SCRUB_W_CURV = 1.35             # weights on the three measured controls, and
SCRUB_W_SLOPE = 1.10            # they are set so the field SPANS its range:
SCRUB_W_ASPECT = 1.25           # a sheltered concave north-east hollow gets
                                # a closed stand, a baked convex spur gets
                                # nothing at all.
SCRUB_STENCIL_M = 130.0         # the radius, IN GROUND METRES, all three
                                # controls are measured over. It is a stand's
                                # own scale, and being a ground length it is
                                # the same everywhere -- which the mesh cell
                                # is emphatically not (20 m near, 300 m far,
                                # and wider across the view than along it at
                                # every range). Measured on the lattice, the
                                # field printed as horizontal streaks lying
                                # along the rings.
SCRUB_SLOPE_0 = 0.16            # sin(slope) below which slope costs nothing
SCRUB_SLOPE_K = 0.26            # and the scale it costs on above that
SCRUB_DENS_MAX = 1.90           # the field is clamped to [0, this]
SCRUB_BARE = 0.92               # below this the ground carries NO scrub, and
                                # it sits near the field's own middle on
                                # purpose: more than half this ground is
                                # limestone with nothing on it
SCRUB_MASS_MIN = 1.02           # the stand's skirt, and
SCRUB_CORE_MIN = 1.34           # its closed crown
SCRUB_SMOOTH = 1                # lattice passes over the density field: a
                                # patch has to span cells or it is a pitch
                                # again, at the lattice's own spacing -- but
                                # each pass also pulls the field toward its
                                # own mean, and a flat field is a pitch too
SCRUB_PATCH_PX2 = 26.0          # a merged loop under this many screen px^2
                                # is a speck and is dropped
SCRUB_PATCH_MAX = 34000.0       # and one over this many is a FOREST, which
                                # 23.114-20 does not allow on this ground:
                                # such a loop is drawn as the skirt only, so
                                # it stays a thin cover and never closes
SCRUB_COPSE_H = 5.0             # m, an artist's convention like the fringe's
                                # heights and stated in the key: what a stand
                                # of holm oak and terebinth throws its shadow
                                # from. The shadow is what makes a copse read
                                # as a thing standing on the hill rather than
                                # a stain laid on it.
SCRUB_TUFT_RANGE = 2300.0       # m. Beyond this a 1.4 m tuft is under the ink
                                # even at 8x (0.92 px at 1x here, 0.23 at
                                # 10 km), so beyond it the mass is not
                                # standing in for a crowd and does not step
                                # aside at the zoom tiers. It is a STRATA
                                # EDGE, so the boundary costs no new seam.
SCRUB_LOBE_PX = 3.1            # how far a scallop bulges off the merged
                                # outline. THE EDGE IS THE WHOLE MARK: in the
                                # drawn tradition a wood is recognised by its
                                # boundary, not by anything inside it.
BANK_MASS_LOBE = 0.55           # the fringe's scallop, as a fraction of the
                                # canopy's own screen height
BANK_MASS_MIN_PTS = 3           # a run shorter than this is not a fringe
IDA_FOLD_WIN = 9                # horizon columns each side that make up the
                                # local SUMMIT line the folds are measured
                                # from -- about a fifth of the mountain's
                                # frontage, which is a massif's own spacing of
                                # summits, not a peak's
IDA_FOLD_K = 2.6                # how far the dark band hangs below the
IDA_FOLD_MAX_PX = 26.0          # skyline per pixel of drop under that line,
                                # and its ceiling


def _rnd(*seed) -> float:
    """A deterministic value in [0, 1) from integer seeds -- FNV-1a, folded.

    Deterministic is the whole point and it is a zoom requirement, not a
    tidiness one. The tier-3 crowd must CONTAIN the tier-1 crowd: a reader
    zooming in should find more trees among the ones already there, not a
    different wood. Keying every jitter to the mark's own integer position
    gives that for free, and it also gives the plate the one thing a lattice
    cannot -- spacing that no system would have produced."""
    h = 0x811C9DC5
    for s in seed:
        h = (h ^ (int(s) & 0xFFFFFFFF)) & 0xFFFFFFFF
        h = (h * 0x01000193) & 0xFFFFFFFF
        h ^= h >> 13
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777216.0


def _crown_sil(r: float, h: float):
    """A crown's shadow silhouette: the canopy ring at its own height, plus
    the trunk's foot. Six points is exact enough for a body this round and it
    is what the tumulus already uses."""
    return ([((r * math.cos(a), r * math.sin(a)), h * 0.72)
             for a in (0.0, 1.05, 2.09, 3.14, 4.19, 5.24)]
            + [((0.0, 0.0), 0.0)])


def tree(cam, terr, lat, lon, h, r, seed=0, lean=0.0):
    """One tree at a true height, drawn with the fewest marks that still gain
    something at 8x: a trunk, a crown, and the crown's sunward lobe.

    The crown is sized from the PROJECTED trunk -- base and top are both
    projected and the screen height between them sets the radius -- so it
    carries the camera's real foreshortening instead of a 1/d formula, and it
    shrinks with depth the way the ground does. Nothing here is regenerated
    per tier: a named tree is an object, not a texture, and an object may
    simply be drawn larger when the reader comes closer."""
    g = terr.elev(lat, lon)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)
    base = cam.project(e0, n0, built_h(0.0, g))
    top = cam.project(e0, n0, built_h(h, g))
    if not base or not top:
        return ""
    hp = base[1] - top[1]
    if hp < VEG_MIN_PX:
        return ""
    rp = max(0.55, hp * (r / h))
    cy = base[1] - hp * 0.72
    cx = base[0] + lean * rp
    # a crown is not a circle: two lobes, the second offset by the tree's own
    # hash, which is the "one asymmetry no system would produce" the drawn-
    # landscape survey asks for. Both are var() fills; neither is a gradient.
    out = [f'<path class="pp-veg-trunk" d="M{n1(base[0])} {n1(base[1])}'
           f'L{n1(cx)} {n1(cy + rp * 0.35)}"/>',
           f'<ellipse class="pp-veg" cx="{n1(cx)}" cy="{n1(cy)}" '
           f'rx="{n1(rp)}" ry="{n1(rp * 0.80)}"/>']
    # FOUR LOBES, NOT ONE ELLIPSE, and the reason is the zoom tier. A single
    # ellipse is a lollipop at 8x however faithfully it is sized; a cluster
    # whose offsets come out of the tree's own hash has a broken silhouette
    # that goes on saying "crown" as it grows, and at 1x the four merge into
    # the same three-pixel dot the ellipse was. Nothing is regenerated: a
    # named tree is one object and may simply be drawn larger up close.
    for k, (fr, fs) in enumerate(((0.62, 0.70), (0.55, 0.62), (0.48, 0.55))):
        jx = (_rnd(seed, 11 + k) - 0.5) * rp * 1.15
        jy = (_rnd(seed, 23 + k) - 0.5) * rp * 0.55 - rp * 0.18
        out.append(f'<ellipse class="pp-veg" cx="{n1(cx + jx)}" '
                   f'cy="{n1(cy + jy)}" rx="{n1(rp * fr)}" '
                   f'ry="{n1(rp * fs)}"/>')
    # the lit face, on the sun's side, and only once it can be seen. SUN_H is
    # the DOWN-sun horizontal, so the light comes from -SUN_H.
    if rp >= 2.2:
        out.append(f'<ellipse class="pp-veg-lit" '
                   f'cx="{n1(cx - SUN_H[0] * rp * 0.38)}" '
                   f'cy="{n1(cy - rp * 0.30)}" rx="{n1(rp * 0.45)}" '
                   f'ry="{n1(rp * 0.34)}"/>')
    sd = object_shadow(cam, terr, lat, lon, 0.0, _crown_sil(r, h))
    return sd + "".join(out)


def thicket(cam, terr, lat, lon, h, r, seed):
    """One clump of the riverbank assemblage: a canopy silhouette, not a
    portrait of a tree.

    At the Scamander's 7-15 km a 13 m elm is one and a half pixels, so
    drawing individuals there would be drawing a stipple and calling it a
    wood. The tradition draws a wood as a scalloped edge -- Berann's forests
    are marks whose OUTLINE does the work -- so a clump is one path of three
    to five lobes across about fourteen metres of ground, at the true height
    of what stands in it, with its own true shadow."""
    g = terr.elev(lat, lon)
    e0, n0 = pp._flat_m((lat, lon), *VIEWPOINT)
    base = cam.project(e0, n0, built_h(0.0, g))
    top = cam.project(e0, n0, built_h(h, g))
    if not base or not top:
        return ""
    hp = base[1] - top[1]
    if hp < VEG_MIN_PX:
        return ""
    rp = max(0.6, hp * (r / h))
    n_lobe = 3 if rp < 2.5 else 5
    pts = []
    for k in range(n_lobe):
        f = (k + 0.5) / n_lobe
        x = base[0] + (f - 0.5) * 2.0 * rp
        lift = 0.62 + 0.38 * _rnd(seed, k)
        pts.append((x, base[1] - hp * lift - rp * 0.30, rp / n_lobe * 1.35))
    d = [f'M{n1(base[0] - rp)} {n1(base[1])}']
    for x, y, w in pts:
        d.append(f'Q{n1(x - w)} {n1(y)} {n1(x)} {n1(y)}'
                 f'Q{n1(x + w)} {n1(y)} {n1(x + w * 1.4)} {n1(base[1] - hp * 0.2)}')
    d.append(f'L{n1(base[0] + rp)} {n1(base[1])}Z')
    sd = object_shadow(cam, terr, lat, lon, 0.0, _crown_sil(r * 0.9, h))
    return sd + f'<path class="pp-veg" d="{"".join(d)}"/>'


def rel_scallop(pts, amp, seed=0, closed=True, sgn=1.0, fixed=None) -> str:
    """A polyline redrawn as a FOLIATE one: every segment becomes a quadratic
    whose control point is pushed off the segment's own normal by a hashed
    amount, so the boundary leaves and re-meets the straight line it was.

    This is the whole of the mass mark. A wood at plate scale is recognised by
    its OUTLINE -- Berann's forests, the Dufour sheets' timber, every drawn
    landscape that survived the century -- and a lattice union is a staircase,
    which reads as a region, not as cover. Amplitude is capped at a third of
    the segment so a long edge bulges rather than balloons, and MOST of the
    lobes go out while a few tuck in, which is what stops the boundary reading
    as a row of arcs. The offsets come out of _rnd, so the same patch scallops
    the same way every render.

    `fixed` replaces the segment's own normal with one direction for the whole
    chain -- what an open canopy edge wants, where the lobes belong on the sky
    side however the run happens to be running.

    Relative data, pen tracked at the rounded value written, exactly as
    rel_poly does it: a merged patch is a long loop and the file is the
    plate's second constraint after the eye."""
    if len(pts) < 2:
        return ""
    seq = list(zip(pts, pts[1:]))
    if closed:
        seq.append((pts[-1], pts[0]))
    px, py = round(pts[0][0], 1), round(pts[0][1], 1)
    out = [f"M{n1(px)} {n1(py)}"]
    for k, (a, b) in enumerate(seq):
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        if L < 0.2:
            continue
        f = amp * (-0.28 + 1.62 * _rnd(seed, k, 3)) * sgn
        f = max(-L * 0.32, min(f, L * 0.32))
        if fixed is None:
            ox, oy = -ey / L, ex / L
        else:
            ox, oy = fixed
        cx = (a[0] + b[0]) * 0.5 + ox * f
        cy = (a[1] + b[1]) * 0.5 + oy * f
        d1x, d1y = round(cx - px, 1), round(cy - py, 1)
        d2x, d2y = round(b[0] - px, 1), round(b[1] - py, 1)
        px, py = round(px + d2x, 1), round(py + d2y, 1)
        out.append(f"q{n1(d1x)} {n1(d1y)} {n1(d2x)} {n1(d2y)}")
    if len(out) < 2:
        return ""
    return "".join(out) + ("Z" if closed else "")


def bank_mass(pts, seed, lit=False) -> str:
    """The riverbank fringe as ONE canopy, not as a row of clumps.

    `pts` is a run of stations along the drawn course: (x, ground_y, canopy_y).
    The path runs out along a scalloped top edge and back along the ground, so
    what closes is a continuous ribbon with a lobed upper boundary -- the thing
    a fringe of elm and willow actually presents at 7-15 km, where the clumps
    it is made of are a pixel apart and cannot be told from each other.

    THE LOBE PITCH IS THE STATION PITCH, so the lobes OVERLAP: a scallop whose
    control point sits above the midpoint of a 4 px span never returns to the
    baseline between neighbours, and a boundary that never returns to its
    baseline has no countable member. That is the difference between this and
    the row of beads it replaces, and it is the only difference -- same
    course, same stations, same citation.

    `lit` draws the sunward crest instead: the same top edge lifted a little
    toward the light, which gives the mass an interior. A flat silhouette is a
    cut-out; a mass is lighter on the side the sun is on."""
    if len(pts) < BANK_MASS_MIN_PTS:
        return ""
    top = [(x, cy) for x, _, cy in pts]
    amp = max(0.5, sum(gy - cy for _, gy, cy in pts) / len(pts) * BANK_MASS_LOBE)
    if lit:
        k = -SUN_H[0] * amp * 0.9
        crest = [(x + k, y + amp * 0.30) for x, y in top]
        d = rel_scallop(crest, amp * 0.55, seed + 5, closed=False,
                        fixed=(0.0, -1.0))
        if not d:
            return ""
        return (f'<path class="pp-veg-crest" d="{d}" '
                f'stroke-width="{max(0.6, amp * 0.75):.1f}"/>')
    d = rel_scallop(top, amp, seed, closed=False, fixed=(0.0, -1.0))
    back = rel_poly([(x, gy) for x, gy, _ in reversed(pts)], close=False)
    if not d or not back:
        return ""
    return f'<path class="pp-veg" d="{d}L{back[1:]}Z"/>'


ROOFS =[(-0.62, 0.30, 8.0, 26), (-0.34, 0.46, 10.5, 30), (-0.02, 0.34, 9.0, 26),
         (0.28, 0.50, 12.5, 32), (0.58, 0.30, 8.5, 26), (-0.20, 0.10, 11.0, 30),
         (0.34, 0.06, 9.5, 26)]


def city(cam, terr, centre, radius=105.0, wall_h=6.0, tower_h=9.5):
    """Ilios on its spur, as a massing: one wall face, one crest, the great
    tower over the plain, a stepped skyline of roofs behind. At 1x this is a
    50 px mark; the DETAILED city is a separate artifact, and this plate does
    not pretend otherwise.

    IT THREW NO SHADOW, AND THAT IS WHY IT FLOATED. "Troy looks like it's
    floating" (John, on the 8x crop). Every one of the 465 hulls and 265 huts
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
# --pp-ida-wood and --pp-tumulus are NOT ground cover: neither is terrain the
# classification speaks for -- one is the mountain beyond the mesh, the other a
# built mound. The tumulus kept the exact value it had as relief-9 when the
# ramp was deleted. --pp-ida-mass, the bare tan Ida inherited from relief-12,
# is GONE: the poem calls that mountain forest twice over and the sheet now
# says so in the one register 66 km of air leaves open, which is hue (see
# .pp-ida). Nothing else on the plate used it.
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
#
# ── THE CAMP IS FOUR MATERIALS, AND THE POEM NAMES EVERY ONE ─────────────
# "a bit more color on the camps... like, not just black shapes" (John). It
# was two tokens for the whole beach -- a near-black hull and a terracotta
# roof borrowed off the citadel's masonry -- and the Achaean camp is not
# built of the same stuff as Ilios. What the Iliad actually gives:
#
#   PITCH, the hull.  νηυσὶ μελαίνῃσιν, the black ships, everywhere the
#       formula falls (9.235 = 11.824 = 12.107). --pp-hull / --pp-hull-side.
#       These stay the DARKEST fills on the beach in both themes; the plate
#       has the recorded bug where hulls keyed to --text went pale at night,
#       and test_the_black_ships_stay_the_darkest_thing_on_the_beach pins it.
#   DARK BLUE, the prow.  νηὸς κυανοπρῴροιο, Il. 15.693 = 23.852 = 23.878, a
#       standing formula. --pp-hull-prow, a lapis so dark it is only a prow
#       when you are close enough to be looking at one ship.
#   VERMILION, the cheek.  δυώδεκα μιλτοπάρῃοι, Il. 2.637 -- Odysseus's
#       twelve, and ONLY his twelve, which is why the red is a block in the
#       middle of the line and not a colour the fleet has. μίλτος is red
#       ochre. --pp-hull-cheek.
#   FIR AND CUT REED, the huts.  Il. 24.450-51: the Myrmidons built Achilles'
#       hut δοῦρ' ἐλάτης κέρσαντες, cutting fir timbers, and roofed it
#       λαχνήεντ' ὄροφον λειμωνόθεν ἀμήσαντες, with shaggy thatch mown from
#       the meadow. --pp-timber is cut fir, --pp-thatch is dry mown meadow.
#       Both are LIGHTER than the hulls on purpose: a camp of timber and
#       straw standing behind a fleet of pitch is the tonal fact the poem
#       states, and it is also what lets a reader tell the huts from the
#       ships at plate scale, which two near-black tokens never could.
TOKENS = {
    "light": """
  --page-bg:#E7E7E9; --text:#241827; --text-mid:#5B4C58;
  --scene-map-label-halo:#F8F7F3; --scene-map-coast:#565060;
  --plate-lagoon:#A8C3C6; --scene-map-sea:#71AEDC; --plate-contour:#5A4A32;
  --pp-shade:#181A2C; --pp-lit:#FFFAEB;
  --plate-masonry:#A87263; --plate-river:#1A4C6A;
  --pp-hull:#3A2C3C; --pp-hull-side:#1B1220; --pp-hull-edge:#140D18;
  --pp-hull-rim:#140D18;
  --pp-hull-prow:#2A4270; --pp-hull-cheek:#93331E;
  --pp-timber:#8E7150; --pp-thatch:#E0C892;
  --pp-cover-fan:#FAD391; --pp-cover-open:#E0CDBA; --pp-cover-ridge:#CDCD83;
  --pp-cover-wet:#94C472;
  --pp-veg:#46612E; --pp-veg-lit:#7C9945; --pp-veg-tick:#4E6B34;
  --pp-veg-mass:#7A8C5C;
  --pp-ida-wood:#617F4C; --pp-ida-fold:#465E36; --pp-tumulus:#CAB083;
  --pp-haze:#CBD9E4; --pp-sky-hi:#93B4D2; --pp-sky-lo:#E1DDD2;
  --pp-water-far:#DCE6EC; --pp-water-shoal:#CFE0D8;
""",
    "dark": """
  --page-bg:#181120; --text:#EDE6E8; --text-mid:#B7A9B4;
  --scene-map-label-halo:#17131C; --scene-map-coast:#8FA3AE;
  --plate-lagoon:#22363E; --scene-map-sea:#071C33; --plate-contour:#332818;
  --pp-shade:#03050E; --pp-lit:#F2E4C4;
  --plate-masonry:#A8846F; --plate-river:#123A4A;
  --pp-hull:#241C2A; --pp-hull-side:#120C16; --pp-hull-edge:#C3B49E;
  --pp-hull-rim:#38303A;
  --pp-hull-prow:#1F3059; --pp-hull-cheek:#5A1E11;
  --pp-timber:#4E3D28; --pp-thatch:#8A7248;
  --pp-cover-fan:#513B1F; --pp-cover-open:#493B30; --pp-cover-ridge:#3C3C1E;
  --pp-cover-wet:#233616;
  --pp-veg:#1C2A12; --pp-veg-lit:#3C5223; --pp-veg-tick:#93AE6A;
  --pp-veg-mass:#26331A;
  --pp-ida-wood:#2E4224; --pp-ida-fold:#1E2D17; --pp-tumulus:#7A6846;
  --pp-haze:#141B28; --pp-sky-hi:#0B1120; --pp-sky-lo:#242B3A;
  --pp-water-far:#1E3244; --pp-water-shoal:#1E3F45;
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
   air is about what it was, which is the right way round: the mountain is
   stated at full strength and the distance takes it down, rather than being
   pre-faded and then faded again.
   AND IDA IS WOODED. The mountain was --pp-ida-mass, a bare warm tan, which
   under 0.73 of air printed as a flat pale grey band across the whole
   horizon — and the poem says the opposite twice: the Achaeans climb
   κνημοὺς ... πολυπίδακος Ἴδης and cut δρῦς ὑψικόμους for the pyre
   (Il. 23.114-20), and Sleep hides on it in an ἐλάτη περιμήκετος (14.287).
   The old refusal to draw that was right about TREES and wrong about the
   MOUNTAIN: at 66 km a 20 m oak is a tenth of a pixel, but a forested
   mountain does not read as trees at any distance — it reads as a darker,
   cooler, greener mass, and that is a claim about tone, which needs no
   treeline and places nothing. So the fill is a forest token and the mass is
   asserted at 0.80 instead of 0.62, because what has to survive the air is
   now a HUE and not just a value. Nothing is planted on Ida; the key says so.
   Measured on the shipped frame, the mountain's green-minus-red goes from 5
   to 18 while its luminance drops about 8% — subtle, which is what 0.73 of
   air allows, and the right direction, which is what it never was. */
/* AND A FORESTED MASSIF IS NOT ONE TONE. It is darker in the folds, where the
   ground turns away and the timber stands deepest, and thinner toward the
   tops, where it is exposed and the rock comes through. The old fill said one
   flat colour across sixty kilometres of skyline, which is the same defect as
   the bare tan it replaced, only in the right hue.
   THE FOLDS ARE READ OFF THE SAMPLED SKYLINE and nothing else. Each column of
   the horizon already carries its own maximum-angle DEM sample; the running
   local maximum over a window of those samples is the SUMMIT line, and how
   far a column falls below it is exactly how deep a col or a re-entrant that
   column is. The dark wedge hangs below the skyline in proportion to that
   drop -- deepest at the saddles, nothing at all on the summits. It places no
   tree, it claims no treeline, and it is a function of the elevation data the
   mountain's own outline is already drawn from. */
.pp-ida{fill:var(--pp-ida-wood);fill-opacity:0.80;stroke:none}
.pp-ida-fold{fill:var(--pp-ida-fold);fill-opacity:0.62;stroke:none}
.pp-ida-crest{fill:none;stroke:var(--plate-contour);stroke-width:0.9;stroke-opacity:0.95}
/* ── TWO WATERS, TWO KINDS OF CLAIM ──────────────────────────────────────
   `sea-modern` is the Aegean and the Dardanelles as they stand now, contoured
   off the Copernicus GLO-30 water mask: a SURVEY. `lagoon-bronze` is the
   reconstructed Late Bronze Age embayment after Kraft, Kayan and Erol: a
   RECONSTRUCTION. They were within six points of value and a few of chroma,
   and a reader who cannot tell them apart cannot tell which coastline this
   sheet asserts as measured -- the same defect class as the barrier layer
   that came off the plate.
   THE PLATE ALREADY DECIDED THE MECHANISM and this only extends it to the
   fills. The reconstruction's SHORE draws at 0.7 px against the survey's
   1.1 px: "the difference between the two lines is how heavily they are
   asserted" (see pp-coast-approx). So the fills say it twice more, in the
   two registers a fill has:
     CHROMA. The surveyed sea keeps a saturated blue and gains some; the
     reconstruction is drained toward grey-blue. Value is left almost where
     it was, deliberately -- the bay is the plate's subject and is named in
     the title, and pushing it down the value scale to make a point about
     epistemics would have been a composition error. It reads as a
     provisional blue, not as a receding one.
     OPACITY. The survey is opaque; the reconstruction is a WASH, and that is
     not a graphic device but the literal claim: what lies under it on this
     base is the ground the reconstruction says was water, so the ground
     modulates it. delta-swamp is already drawn this way for the same reason,
     and lagoon-bronze is already DRAPED on that ground rather than floated
     on a sea level (see water_svg). At 0.87 the ground's tone comes through
     as a faint grain and the water still reads as one body.
   MEASURED ON RENDERED PIXELS, off the margin swatches, which is where each
   fill is seen unveiled. Out on the plate both waters lie under the same
   Fresnel and air ramps, and at the bay mouth those are 57% and 19% of the
   pixel, so they compress ANY token difference to about 1.1:1 -- that is
   physics, it is shared, and it is not a thing to tune around:
       sea vs bay        1.32:1 light, 1.37:1 dark, plus a chroma step the
                         ratio cannot see -- blue-minus-red is 107 on the sea
                         and 21 on the bay in light theme.
   AND THE LOAD-BEARING NUMBER IS NOT THAT ONE. Neither fill has ever carried
   the land/water boundary; the opaque coast line does, and WCAG 1.4.11 wants
   3:1 on it. Re-measured after this change, because moving a water token
   moves that number -- and the first sea token tried here FAILED it, at
   2.91:1, which is why the sea is #71AEDC and not the darker blue:
       coast ink on sea  3.24:1 light, 6.56:1 dark
       coast ink on bay  4.28:1 light, 4.77:1 dark
   The bay is LIGHTER than it was, which is why its line improved and why the
   fill boundary alone is now 1.05-1.27:1 against the ground classes where it
   was 1.45-1.69. Neither figure was ever load-bearing: both are far under
   3:1, which is the whole reason the hairline exists. */
.pp-sea{fill:var(--scene-map-sea)}
.pp-lagoon{fill:var(--plate-lagoon);fill-opacity:0.87}
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
/* THE SHIPS KEEP THEIR OWN RIM, and the reason is the oldest bug on this
   plate. --pp-hull-edge in dark theme is #C3B49E, a near-label cream, and it
   is right for the CITADEL, which is a pale stone mass on a dark hill. On a
   hull it inverts the one thing the epithet asks a drawing for: at 8x the
   fleet came out as bone-white canoes with cream posts, the LIGHTEST marks on
   the beach, and at 1x the rank read as a row of white ticks. --pp-hull-rim
   is the same near-black in daylight and a restrained slate at night -- above
   the beach it lies on, nowhere near the ink -- and the posts take the hull's
   own fill rather than any rim at all, because a post is a piece of the ship
   and not an outline of one. Pinned by
   test_the_black_ships_stay_the_darkest_thing_on_the_beach. */
.pp-hull{fill:var(--pp-hull);stroke:var(--pp-hull-rim);stroke-width:0.35;
  stroke-linejoin:round}
.pp-hull-side{fill:var(--pp-hull-side);stroke:none}
/* ἕρματα μακρά, the long props (Il. 1.485-86; pulled out again to launch at
   2.154). They take the hull's OWN side token and no rim, for the reason the
   posts do: a shore under a galley is a piece of the ship's berth, not an
   outline of anything, and giving it any lighter ink would put the lightest
   mark on the beach directly under the darkest fill on it. 0.3 against the
   post's 0.45 because a shore is thinner than a stem-post, and both are in
   user units, so both scale with the crop. */
.pp-erma{fill:none;stroke:var(--pp-hull-side);stroke-width:0.3;
  stroke-linecap:round}
/* 0.45, not 0.9. The tier-2 fleet is only ever LOOKED at from 2x up, and a
   stroke width is in user units, so 0.9 became a seven-pixel club at 8x --
   every galley a frying pan. A stem-post is about 0.3 m of worked timber,
   which is what 0.45 comes to on the 8x crop. The overview's post keeps its
   own weight below, because at 1x it is carrying the whole silhouette. */
.pp-post{fill:none;stroke:var(--pp-hull-side);stroke-width:0.45;stroke-linecap:round}
/* THE OVERVIEW'S HULL IS THE SAME SOLID, DRAWN BOLDER. Its stem-post and its
   stern ornament are the two marks on a 10 px glyph that have to survive at
   1x, so they take a heavier stroke -- and a ROUND cap, which is what a
   carved post end is; a butt cap at this weight chops the ἄφλαστον square.
   1.1, DOWN FROM 1.6: at 1.6 against a hull stretched 3.4x in length the
   post was half the mark's ink, and a near-black hook that heavy is what
   read as "frigging huge" on a glyph measuring 12.7 px. The geometry came
   down to x2.5 and the stroke comes down with it; the ἄφλαστον still tells
   a stern from a stem, which is all it is there to do. */
.pp-post-t1{fill:none;stroke:var(--pp-hull-side);stroke-width:1.1;
  stroke-linecap:round}
/* the painted bow. Two formulae, two colours, and which one a hull gets is
   decided by whose contingent it is beached in -- see ODYSSEUS_TWELVE. */
.pp-prow{fill:var(--pp-hull-prow);stroke:none}
.pp-prow-miltos{fill:var(--pp-hull-cheek);stroke:none}
/* fir wall, cut-reed roof (Il. 24.450-51). The roof was --plate-masonry,
   which is the CITADEL's stone: it made every hut a terracotta domino and
   said, in the one language a plate has, that Achilles slept in a stone
   house. The rim stays --pp-hull-edge, the sheet's one rim token. */
.pp-hut-wall{fill:var(--pp-timber);stroke:var(--pp-hull-rim);stroke-width:0.25;
  stroke-linejoin:round}
.pp-hut-roof{fill:var(--pp-thatch);stroke:var(--pp-hull-rim);stroke-width:0.3;
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
/* ── VEGETATION ──────────────────────────────────────────────────────────
   A CROWN IS A MASS AND TAKES THE MASS RULE: --pp-veg is darker than every
   ground class it can stand on, in BOTH themes, so the tonal rank cannot
   photo-negative between them. In dark theme that leaves the fill at 1.4:1
   against the ridge, which is exactly where the hulls already are (1.56:1)
   and is answered the same way -- --pp-hull-edge, the sheet's one rim token,
   dark on a light ground and restrained-light on a dark one. One convention
   for every standing thing on the plate, not a second one for trees.
   THE TICK IS NOT A MASS and does not get the mass rule. A 1 px tuft has no
   interior to hold a rank, and a --pp-veg tick measures 1.31:1 on the dark
   ridge -- invisible, which is not honesty, it is just a mark that failed to
   print. --pp-veg-tick therefore follows the RIM convention instead: green in
   both themes, dark on the light sheet and light on the dark one, 3.59:1 and
   4.44:1 against the ridge it sits on. The inversion is confined to hairline
   texture; nothing with an area inverts. */
.pp-veg{fill:var(--pp-veg);stroke:var(--pp-hull-edge);stroke-width:0.35;
  stroke-linejoin:round}
.pp-veg-lit{fill:var(--pp-veg-lit);stroke:none}
/* THE MASS MARKS, and they are washes, not fills. The patch lays cover over
   ground the sheet has already toned, shaded and banded, and an opaque fill
   would delete all of it and print a green shape -- which is the cut-out
   failure the fringe was already committing one clump at a time. At 0.36 the
   relief, the slope wash and the cover boundary all still read through, so
   what the reader sees is ground WITH scrub on it. The core is the same wash
   laid twice over the denser half of the field, so the interior carries two
   values and the margin one; nothing is a gradient and no filter is involved.
   AND IT HAS ITS OWN TOKEN, WHICH IS A LABEL FACT BEFORE IT IS A COLOUR ONE.
   --pp-veg is the CROWN colour: it is as dark as it is because a canopy seen
   against open ground is nearly a silhouette, which is right for a clump of
   elm on a riverbank a pixel and a half wide. Spread over whole hillsides at
   two coats it took the ground under SIGEION and THE SHIPS down with it, and
   a label's background is not this lane's to spend. --pp-veg-mass is a
   lighter green that still obeys the mass rule -- darker than every ground
   class it can stand on, in BOTH themes, so the tonal rank cannot
   photo-negative -- and carries the class by HUE and a moderate value step
   rather than by value alone. Colour is free; contrast is not.
   THE COPSE SHADOW is a CRESCENT and takes the even-odd rule to be one: the
   displaced outline with the outline itself cut back out of it, so only the
   strip that falls on open ground is painted. See scrub_mass_svg.
   THE CREST is the fringe's sunward face -- the one thing that keeps the
   ribbon from being a silhouette. It is a stroke and not a fill, because a
   canopy's lit side is an edge condition and the mark is one to three px. */
.pp-scrub-mass{fill:var(--pp-veg-mass);fill-opacity:0.34;stroke:none}
.pp-scrub-core{fill:var(--pp-veg);fill-opacity:0.46;stroke:none}
.pp-copse-shadow{fill:var(--pp-shade);fill-opacity:0.26;fill-rule:evenodd;
  stroke:none}
.pp-veg-crest{fill:none;stroke:var(--pp-veg-lit);stroke-linecap:round;
  stroke-linejoin:round;stroke-opacity:0.55}
.pp-veg-trunk{fill:none;stroke:var(--pp-hull-edge);stroke-width:0.7;
  stroke-linecap:round}
/* THE TUFT IS NOW A ZOOM MARK AND IS DRAWN LIKE ONE. It used to carry the
   class on its own at 1x, where 0.85 px was the least ink that would print;
   it is only ever seen at 4x and 8x now, where that same width is seven
   output pixels on a mark sixteen tall -- a club, not a bush. At 0.35, with
   the round cap off, the stems read as stems. */
.pp-scrub{fill:none;stroke:var(--pp-veg-tick);stroke-width:0.35;
  stroke-linejoin:round}
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
.pp-colophon{fill-opacity:0.85}
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
        self._rings: dict = {}           # layer id -> the DRAWN shore ring

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
        # ── the drowned-gap catch (see SHORE_CUT_M / DROWN_REACH_M). The
        # reconstructed shore's own vertices go into a coarse spatial hash so
        # the "near the drawn shore" clause costs nine bucket lookups per
        # cell instead of a thousand distances; without it this test would
        # have doubled the render.
        lag_ring = self.shore("lagoon-bronze")
        lag_mask = Mask(lag_ring)
        B = DROWN_REACH_M

        def _hash(ring):
            h: dict = {}
            for lat_, lon_ in ring:
                e_, n_ = pp._flat_m((lat_, lon_), vp_lat, vp_lon)
                h.setdefault((int(e_ // B), int(n_ // B)), []).append((e_, n_))
            return h

        def _near(h, ec, nc):
            bx, by = int(ec // B), int(nc // B)
            return any((ec - qe) ** 2 + (nc - qn) ** 2 < B * B
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                       for qe, qn in h.get((bx + dx, by + dy), ()))

        near_lag = _hash(lag_ring)
        near_sea = _hash(self.shore("sea-modern"))
        cov = {}
        tally = {COVER_FAN: 0, COVER_RIDGE: 0, COVER_OPEN: 0, COVER_DROWNED: 0}
        for (i, j) in self.visible:
            (e0, n0), (e1, n1) = self.wor[i][j], self.wor[i + 1][j]
            (e2, n2), (e3, n3) = self.wor[i + 1][j + 1], self.wor[i][j + 1]
            ec = (e0 + e1 + e2 + e3) * 0.25
            nc = (n0 + n1 + n2 + n3) * 0.25
            lat = vp_lat + nc * mlat
            lon = vp_lon + ec * mlon
            g = self.grid
            elev = (g[i][j][2] + g[i + 1][j][2]
                    + g[i + 1][j + 1][2] + g[i][j + 1][2]) * 0.25
            if elev < SHORE_CUT_M:
                hit = (_near(near_lag, ec, nc) and _near(near_sea, ec, nc))
                # NOT TESTED AGAINST THE SEA, and that is the last piece of
                # the left-edge defect. A cell inside the sea MASK can still
                # be outside the sea's DRAWN edge, because the drawn edge is
                # corner-cut and simplified; at this corner the source ring
                # swings twenty pixels a vertex, so the two disagree by
                # several cells and the disagreement printed as dry ground
                # between two waters. Testing only against the reconstruction
                # makes the rule paint bay-wash over anything below the cut
                # at the junction, and the sea's own fill lands on top of it
                # wherever the sea actually reaches -- so the only place the
                # wash is ever SEEN is the gap, which is what it is for. It
                # cannot spread inland either: lagoon-bronze is cut ON the
                # 10 m contour, so ground just outside it is at or above the
                # cut by construction and fails the first clause.
                if hit and not lag_mask.has(lat, lon):
                    cov[(i, j)] = COVER_DROWNED
                    tally[COVER_DROWNED] += 1
                    continue
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
                cls_ = self.cover[(i, j)]
                # A DROWNED CELL TAKES NO SLOPE SHADING. It stands in for
                # water, and water is flat: Imhof excludes cast shadow from
                # the relief system entirely and the bay itself carries none.
                # Left in the tone field the repair printed as a modelled dark
                # hollow exactly where the plate is asserting a smooth surface.
                st = 0 if cls_ == COVER_DROWNED else self.shade_q.get((i, j), 0)
                if st:
                    shade.setdefault(st, set()).add((i, j))
                interior.setdefault(cls_, set()).add((i, j))
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
                    # A DROWNED GAP IS ONE OR TWO CELLS WIDE and the cover
                    # low-pass is sized for a 37 px riser, so five passes over
                    # a sliver that thin collapse it onto its own centreline
                    # and the gap re-opens under the smoothing that was meant
                    # to tidy it. It gets one pass, and the seam-closing
                    # stroke every class carries is widened for it: this is a
                    # repair of a hole, so erring outward closes the hole and
                    # erring inward is the defect coming back.
                    d.append(rel_poly(chaikin(simplify(
                        soften(loop, 1 if c == COVER_DROWNED else COVER_SOFT),
                        0.7), 1)))
                if d:
                    # A hairline of page-bg used to show wherever a simplified
                    # union loop pulled away from its neighbour, or where one
                    # depth stratum met the next. Stroking a class in its OWN
                    # fill closes the seam for 0.3 px of expansion and no
                    # change to the drawing.
                    tok = f"var({COVER_TOKEN[c]})"
                    if c == COVER_DROWNED:
                        # painted as the RECONSTRUCTION paints itself -- the
                        # ground it would have had, under the bay's own wash
                        # at the bay's own opacity -- so a gap closed here is
                        # indistinguishable from the polygon that should have
                        # covered it, and no third colour appears on the sheet
                        base = f"var({COVER_TOKEN[COVER_OPEN]})"
                        out.append(f'<path class="pp-cover" fill="{base}" '
                                   f'stroke="{base}" stroke-width="5.0" '
                                   f'd="{"".join(d)}"/>')
                        out.append(f'<path class="pp-cover" fill="{tok}" '
                                   f'fill-opacity="0.87" stroke="{tok}" '
                                   f'stroke-opacity="0.87" stroke-width="5.0" '
                                   f'd="{"".join(d)}"/>')
                        continue
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
                    # STROKED IN ITS OWN TONE, at a third of the cover's
                    # width. It was not stroked at all, on the reasoning that
                    # "a gap between two tones just reads as the tone between
                    # them" -- which holds inside a stratum and fails across
                    # one, where the gap reads as bare cover and eighteen
                    # nested washes miss the same sliver at once. See
                    # SHADE_SEAM_W for the diagnosis and for why the width is
                    # 0.25 and not the cover's 0.7: a wider stroke laps the
                    # far stratum's surviving wash and prints a dark line
                    # instead of a pale one.
                    out.append(f'<path class="pp-shade" fill="{tone}" '
                               f'fill-opacity="{a:.4f}" stroke="{tone}" '
                               f'stroke-opacity="{a:.4f}" '
                               f'stroke-width="{SHADE_SEAM_W:g}" '
                               f'd="{"".join(d)}"/>')
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
        return ('<path d="%s" class="pp-ida"/>%s'
                '<path d="%s" class="pp-ida-crest"/>'
                % (rel_poly(poly), self.ida_folds(sky),
                   rel_poly(sky, close=False))), crest

    def ida_folds(self, sky) -> str:
        """The mountain's own folds, from the skyline the sheet already sampled.

        `sky` is one DEM-derived point per horizon column. The running maximum
        over a window of them is the SUMMIT line; a column's drop below it is
        how deep a saddle or a re-entrant stands there. The dark band hangs
        under the skyline in proportion to that drop -- deepest at the cols,
        nothing at all on the tops -- so it follows the elevation data rather
        than a taste for texture, and it plants nothing. See the .pp-ida-fold
        note in CSS."""
        n = len(sky)
        if n < IDA_FOLD_WIN * 2 + 2:
            return ""
        top = [min(q[1] for q in sky[max(0, i - IDA_FOLD_WIN):
                                     min(n, i + IDA_FOLD_WIN + 1)])
               for i in range(n)]
        low = [(x, y + min(IDA_FOLD_MAX_PX, (y - top[i]) * IDA_FOLD_K))
               for i, (x, y) in enumerate(sky)]
        if max(b[1] - a[1] for a, b in zip(sky, low)) < 1.0:
            return ""
        return ('<path d="%s" class="pp-ida-fold"/>'
                % rel_poly(sky + list(reversed(low))))

    # ── water ────────────────────────────────────────────────────────────
    def coast_ring(self, poly_latlon, label):
        """One water polygon's ring, with the source grid's 30 m staircase
        taken off it in WORLD METRES (see COAST_SOFT).

        Taubin's lambda/mu pair, which is the shrink-free low-pass this file
        already uses on cover boundaries and tone edges; a plain box or
        Laplacian pass would pull a closed ring in toward its own centre and
        that would move the shoreline in one direction, which is a bias and
        not a smoothing. The displacement is measured against the ORIGINAL
        ring, in metres, and reported.

        MEMOISED, and that matters for more than speed: the camp lays its
        ships against the shore, the rivers stop at it, and the fill and the
        coast line are drawn on it. All four must read the SAME ring, or the
        fleet beaches thirty metres off the water it is drawn against."""
        hit = self._rings.get(label)
        if hit is not None:
            return hit
        raw = [pp._flat_m(p, *VIEWPOINT) for p in poly_latlon]
        # DENSIFY FIRST, AND THAT IS NOT AN OPTIMISATION. A vertex low-pass
        # averages a point toward its NEIGHBOURS, so on a ring whose sampling
        # is uneven -- sea-modern runs 30 m risers round the headlands and
        # then straight for kilometres across the open Aegean -- a vertex
        # between two distant neighbours is dragged most of the way to the
        # chord between them. Measured before this line existed: worst move
        # 6339.7 m on sea-modern, which is not a smoothing, it is a different
        # coastline. Resampled at the source posting the filter sees one
        # feature size everywhere and the move falls to the grid's own scale.
        flat = []
        n_ = len(raw)
        for k in range(n_):
            a, b = raw[k], raw[(k + 1) % n_]
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            for s in range(max(1, int(seg / COAST_STEP_M))):
                t = s / max(1, int(seg / COAST_STEP_M))
                flat.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        soft = soften(flat, COAST_SOFT, closed=True)
        soft, cuts = cut_necks(soft)
        self.stats.setdefault("coast_necks", {})[label] = cuts
        # measured to the ORIGINAL POLYLINE, not to its vertices, for the
        # reason course() gives: a smoothed point sits mid-segment, and the
        # nearest vertex can be far away on a line the point never left
        worst = 0.0
        for cx, cy in soft:
            best = float("inf")
            for k in range(n_):
                x0, y0 = raw[k]
                x1, y1 = raw[(k + 1) % n_]
                ux, uy = x1 - x0, y1 - y0
                L2 = ux * ux + uy * uy
                t = 0.0 if L2 < 1e-9 else max(0.0, min(
                    1.0, ((cx - x0) * ux + (cy - y0) * uy) / L2))
                best = min(best, math.hypot(cx - x0 - t * ux, cy - y0 - t * uy))
            worst = max(worst, best)
        self.stats.setdefault("coast_dev_m", {})[label] = round(worst, 1)
        mlat = 1.0 / 111132.0
        mlon = 1.0 / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))
        ring = [(VIEWPOINT[0] + n * mlat, VIEWPOINT[1] + e * mlon)
                for e, n in soft]
        self._rings[label] = ring
        return ring

    def shore(self, label):
        """The drawn ring for one water body, by layer id."""
        return self.coast_ring(self.lay[label]["polygon"], label)

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
        # ONE CORNER-CUT, NOT TWO, now that coast_ring low-passes the ring in
        # world metres before it ever reaches here. Two on top of that pulled
        # the DRAWN edge well inside its own MASK -- and cover_field
        # classifies against the mask, so wherever the two disagreed the
        # ground kept a dry cover colour that the water fill no longer reached
        # to hide. That is what was left of the left-edge sliver after the
        # drowned-gap rule had done its work: not a misclassification, but a
        # drawn line that had walked away from the classification.
        return simplify(chaikin(scr, passes=1, closed=True), 0.6)

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
        sea = self.water_path(self.shore("sea-modern"), 0.0)
        lagoon = self.water_path(self.shore("lagoon-bronze"), drape=True)
        # the swamp keeps its raw ring: it is drawn with NO outline and a 9 px
        # blur, so a 30 m riser on it was never visible and taking one off
        # would be moving a line nobody can see.
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
        lagoon = self.shore("lagoon-bronze")
        sea = self.shore("sea-modern")

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
        # THE COURSES ARE KEPT so the thicket can be hung on the LINE THE
        # PLATE DREW rather than on the survey path it came from. That is the
        # whole licence for drawing bank flora at all (see the vegetation
        # note): a fringe along a drawn schematic course inherits that
        # course's register and makes no new claim. Recomputing it from the
        # raw path in vegetation_svg would have let the two drift apart.
        self.river_courses = []
        for run in dry_runs(self.lay["scamander"]["path"]):
            c = course(run)
            self.river_courses.append(("scamander", 1, c))
            out.append('<g>' + draped_ribbon(
                self.cam, self.terr, c, 17.0, "pp-river",
                taper=lambda t: 0.55 + 0.45 * t) + '</g>')
        for run in dry_runs(self.lay["simoeis"]["path"]):
            c = course(run)
            self.river_courses.append(("simoeis", 2, c))
            out.append('<g class="tm2">' + draped_ribbon(
                self.cam, self.terr, c, 11.0, "pp-river",
                taper=lambda t: 1.0 - 0.4 * t) + '</g>')
        # THE AIR IS OVER THE RIVERS TOO. The channels are drawn after every
        # haze rect the strata laid down, so the Scamander was arriving at
        # 8-14 km at the full strength of a mark two hundred metres away --
        # the one thing left in the middle distance that read as a map line
        # rather than as a thing seen. It takes the SAME gradient the bay
        # does, which is the same law the ground does; nothing about the
        # channel moves.
        return hazed("".join(p for p in out if "<path" in p))

    # ── vegetation ───────────────────────────────────────────────────────
    def _aired(self, marks, cls=""):
        """Group marks by the strata the terrain already integrates, and give
        each band the air's own transmittance.

        The terrain gets its haze from wash rects laid BETWEEN strata, which
        only reaches what was painted before them; anything drawn afterwards
        -- the rivers, the camp, and now this -- arrives at full strength
        however far away it is. rivers_svg answers that with hazed(), which
        re-emits every path under #pp-air; that device needs a FILLED path and
        would flood a stroked scrub tick with colour, and it doubles the
        element count, which on fifteen hundred ticks is not free. So the
        marks are bucketed by depth instead and each bucket carries the same
        exp(-d/HAZE_D) as a group opacity. It is the identical law read at the
        band's own range, and the approximation it makes -- fading a mark
        toward the ground beneath it rather than toward the haze token -- is
        invisible because the ground beneath it has itself already been
        hazed by exactly the same amount."""
        out = []
        edges = STRATA_EDGES
        for s in range(len(edges) - 1):
            far, near = edges[s], edges[s + 1]
            band = [m for d, m in marks if near <= d < far]
            if not band:
                continue
            t = math.exp(-((far + near) * 0.5) / HAZE_D)
            g = f'<g class="{cls}" opacity="{t:.3f}">' if cls else \
                f'<g opacity="{t:.3f}">'
            out.append(g + "".join(band) + "</g>")
        return "".join(out)

    def cover_centre(self, cls, near, far):
        """The screen point to letter a ground-cover class at: the median of
        the visible cells of that class inside a depth band.

        THE MEDIAN AND NOT THE CENTROID, because a class on this sheet is
        rarely one blob -- the dry fan has a lobe west of the citadel and a
        much larger sheet east of the camp -- and a centroid of two lobes
        lands between them, on ground that is not the class at all. The band
        is what chooses WHICH stretch gets the name: the fan is lettered where
        the fighting is, between the camp and the city, and not out at the
        mesh's edge where it is four pixels tall.

        This is region lettering in the sense TROAD-CARTOGRAPHY.md means: an
        unbounded tract gets letterspaced caps laid across it, no pin and no
        outline, because a pin would claim a point and an outline a boundary,
        and the class has neither."""
        pts = [(self.grid[i][j][0], self.grid[i][j][1])
               for (i, j) in self.visible
               if self.cover.get((i, j)) == cls
               and near <= self.grid[i][j][3] < far]
        if len(pts) < 40:
            return None
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        return xs[len(xs) // 2], ys[len(ys) // 2]

    def scrub_cover(self):
        """How much cover each ridge cell carries, in [0, SCRUB_DENS_MAX], as
        a function of curvature, slope and aspect -- see the note over
        SCRUB_W_CURV. One number per cell, and it drives BOTH drawings of the
        class: which ground the merged patch covers at the overview, and how
        many tufts stand on it once the reader is close enough to see tufts.

        A CONSTANT DENSITY IS WHAT MADE THE CLASS READ AS STUBBLE. One mark
        per fixed unit of area is a pitch, the eye finds a pitch immediately,
        and once it has found one the marks are countable however small they
        are. The fix is not fewer marks or smaller ones; it is to stop the
        pitch existing, and the terrain will do that for nothing, because real
        maquis IS patchy and the DEM already knows where.

        THE STENCIL IS IN GROUND METRES, NOT IN LATTICE CELLS, and the first
        attempt at this proves why it has to be. Read off the mesh's own
        neighbours, all three controls are measured over a cell -- twenty
        metres under the reader's feet and three hundred at the far crests,
        and wider across the view than along it at every range. The field that
        came out was banded the way the lattice is banded, and it printed as
        horizontal streaks lying along the rings: a drawing of the mesh, not
        of the hill. Sampled instead at a fixed SCRUB_STENCIL_M in east and
        north, the field is isotropic and has ONE scale everywhere, which is
        also the scale of the thing being drawn -- a stand of trees a couple
        of hundred metres across."""
        g, terr = self.grid, self.terr
        cells = [ij for ij in self.visible
                 if self.cover.get(ij) == COVER_RIDGE
                 and g[ij[0]][ij[1]][3] <= SCRUB_REACH]
        a = math.radians(LIGHT_AZ)
        lx, ly = math.sin(a), math.cos(a)
        mlat = 1.0 / 111132.0
        mlon = 1.0 / (111320.0 * math.cos(math.radians(VIEWPOINT[0])))

        dens = {}
        for (i, j) in cells:
            (e0, n0), (e1, n1_) = self.wor[i][j], self.wor[i + 1][j]
            (e2, n2), (e3, n3) = self.wor[i + 1][j + 1], self.wor[i][j + 1]
            ec, nc = (e0 + e1 + e2 + e3) * 0.25, (n0 + n1_ + n2 + n3) * 0.25
            # AND THE STENCIL CANNOT BE FINER THAN THE LATTICE IT IS READ ON.
            # Sampled at a flat 130 m the far field aliased: the columns are
            # 24 m apart at 10 km and the rings 250, so the field came out
            # correlated across the view and noisy along it, which is a
            # horizontal streak by construction. Widening it to the ring's own
            # spacing where the ring is wider is the ordinary anti-aliasing
            # rule -- the drawing simply generalises with distance, which is
            # what a draughtsman does anyway and what elev_smooth already does
            # for the mesh itself.
            R = max(SCRUB_STENCIL_M, math.hypot(e3 - e0, n3 - n0) * 0.9)
            el = lambda de, dn: terr.elev_smooth(
                VIEWPOINT[0] + (nc + dn) * mlat,
                VIEWPOINT[1] + (ec + de) * mlon, R * 0.5)
            zc = el(0.0, 0.0)
            zE, zW, zN, zS = el(R, 0), el(-R, 0), el(0, R), el(0, -R)
            # the Laplacian at the stencil's own scale, normalised by the
            # local relief so a hollow means the same thing on a 20 m spur and
            # on a 200 m ridge. Positive is CONCAVE: a gully head, a hollow,
            # ground that gathers the winter water and what soil there is.
            relief = max(zc, zE, zW, zN, zS) - min(zc, zE, zW, zN, zS)
            curv = math.tanh(2.4 * ((zE + zW + zN + zS) * 0.25 - zc)
                             / (relief + 0.5))
            gx, gy = (zE - zW) / (2 * R), (zN - zS) / (2 * R)
            den = math.sqrt(1.0 + gx * gx + gy * gy)
            sn = math.hypot(gx, gy) / den
            steep = min(1.0, max(0.0, (sn - SCRUB_SLOPE_0) / SCRUB_SLOPE_K))
            # >0 where the face is turned toward the light's own bearing,
            # which at 228.4 deg is the baked south-west side
            face = math.tanh((-gx * lx - gy * ly) / den / 0.30)
            dens[(i, j)] = (1.0 + SCRUB_W_CURV * curv
                            - SCRUB_W_SLOPE * steep - SCRUB_W_ASPECT * face)
        # A PATCH HAS TO SPAN CELLS. Unsmoothed, the field alternates at the
        # lattice's own spacing and the drawing is back to a pitch, only a
        # coarser one; two passes make the runs a few cells long, which is a
        # patch of cover a couple of hundred metres across.
        for _ in range(max(0, SCRUB_SMOOTH)):
            nxt = {}
            for (i, j), v in dens.items():
                tot, wt = v * 2.0, 2.0
                for q in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if q in dens:
                        tot += dens[q]
                        wt += 1.0
                nxt[(i, j)] = tot / wt
            dens = nxt
        out = {}
        for ij, v in dens.items():
            v = min(SCRUB_DENS_MAX, v)
            # and the BARE GROUND, which is the half of patchiness that the
            # weights alone will not give: without a floor the field only
            # thins, and thin-everywhere is still a pitch
            out[ij] = v if v >= SCRUB_BARE else 0.0
        if out:
            self.stats["scrub_dens_mean"] = round(
                sum(out.values()) / len(out), 3)
            self.stats["scrub_bare_frac"] = round(
                sum(1 for v in out.values() if v == 0.0) / len(out), 3)
        return out

    def scrub_mass_svg(self, dens):
        """The overview drawing of the ridge cover: merged patches, scalloped.

        union_loops drops every interior edge, so a run of dense cells costs
        its perimeter and not its area -- which is why the mass is CHEAPER
        than the crowd it replaces and not dearer. Two thresholds are laid
        one over the other, so the interior carries two values and the margin
        one: a wood is open at its edge and closed in the middle, and that is
        read off the density field rather than invented.

        Built per depth stratum, which does two jobs: each patch takes the
        air at its own range, exactly as every other mark on the sheet does,
        and no single patch can merge across the whole ridge from the
        foreground to the far crests.

        Two returns, and the split is the LEVEL OF DETAIL rule read honestly.
        Inside SCRUB_TUFT_RANGE a 1.4 m bush is over the ink at 1x, so there
        the mass is the overview's drawing of a thing the zoom will draw as
        tufts, and it steps aside at tier 3. Beyond it the tuft is a fifth of
        a pixel at 1x and still under the ink at 8x, so there is no crowd for
        the mass to stand in for and it stays on at every tier -- the same
        argument the sheet already makes for Ida, where a forested mountain is
        a tone at any range because a tree there is a tenth of a pixel. The
        boundary is a stratum edge, so it costs no seam the plate did not
        already have."""
        grid = self.grid
        corner = lambda i, j: (grid[i][j][0], grid[i][j][1])
        near_m, far_m, n_loop, n_big = [], [], 0, 0
        edges = STRATA_EDGES
        for s in range(len(edges) - 1):
            far, near = edges[s], edges[s + 1]
            band = {ij: v for ij, v in dens.items()
                    if near <= grid[ij[0]][ij[1]][3] < far}
            if not band:
                continue
            out = near_m if near < SCRUB_TUFT_RANGE else far_m
            sx, sy = self.copse_shadow_px(band)
            for lvl, (thr, cls) in enumerate(
                    ((SCRUB_MASS_MIN, "pp-scrub-mass"),
                     (SCRUB_CORE_MIN, "pp-scrub-core"))):
                cells = {ij for ij, v in band.items() if v >= thr}
                if not cells:
                    continue
                for lp in union_loops(cells, corner):
                    # A LONE CELL IS A SPECK, NOT A STAND. Small islands were
                    # the countability defect coming back one size up: three
                    # far cells union into a rounded blob the eye picks off
                    # immediately.
                    a = abs(poly_area(lp))
                    if a < SCRUB_PATCH_PX2:
                        continue
                    lp = simplify(lp, 1.1, closed=True)
                    if len(lp) < 7:
                        continue
                    # THE STAIRCASE HAS TO GO FIRST. A union loop is the
                    # lattice's own right angles, and in the near field a cell
                    # is forty pixels across, so a 3 px scallop laid over that
                    # draws a staircase with a frill on it. Taubin's
                    # shrink-free low-pass -- the pass the cover boundaries
                    # and the tone edges already take -- rounds the steps out,
                    # and the lobe then has something to be a lobe on.
                    # ... and the low-pass leaves a great many near-collinear
                    # points behind it. They are not information -- the
                    # tolerance is well under the sheet's own 1.1 px hairline
                    # -- and on a hundred merged loops they are most of the
                    # file.
                    lp = simplify(soften(lp, 3, closed=True), 0.9, closed=True)
                    if len(lp) < 7:
                        continue
                    seg = sum(math.hypot(q[0] - p_[0], q[1] - p_[1])
                              for p_, q in zip(lp, lp[1:])) / max(1, len(lp) - 1)
                    # AND THE LOBE SCALES WITH THE STAND. A fixed amplitude is
                    # a fixed pitch, which is the same defect one level up:
                    # a near copse wants big crowns and a far one small ones,
                    # exactly as its trees do.
                    amp = min(15.0, max(SCRUB_LOBE_PX, seg * 0.42))
                    # OUTWARD: for a loop of positive shoelace the segment's
                    # own left normal points INTO the body, and a wood's
                    # crowns bulge off it, not into it
                    d = rel_scallop(lp, amp, seed=n_loop + lvl * 7919,
                                    closed=True, sgn=-winding_sign(lp))
                    if not d:
                        continue
                    if a > SCRUB_PATCH_MAX:
                        # a sheet this size would be a FOREST, and the pyre of
                        # Il. 23.114-20 says there is none here: it keeps the
                        # thin skirt and is refused the closed crown
                        if lvl:
                            continue
                        n_big += 1
                    n_loop += 1
                    if not lvl and (sx or sy):
                        # THE STAND STANDS ON THE HILL. One true-length
                        # shadow per copse, the same rule as every built thing
                        # on the sheet -- SCRUB_COPSE_H down-sun at the
                        # stratum's own range -- and the cheapest mark that
                        # stops a patch reading as a stain.
                        #
                        # A CRESCENT, NOT A DUPLICATE. The whole silhouette
                        # displaced is what object_shadow draws for a hut,
                        # and it is wrong for a body the size of a wood:
                        # nearly all of that shadow falls on the wood itself,
                        # and only the strip beyond the down-sun edge lands on
                        # open ground. Drawn as a duplicate at 0.30 over a
                        # near ridge carrying stands at every turn, the
                        # overlaps stacked and took the ground under SIGEION
                        # and THE SHIPS to almost black -- a label's
                        # background spent on a shadow that is not there. The
                        # displaced outline and the outline itself in ONE path
                        # under the even-odd rule leave exactly the strip.
                        sd = rel_scallop([(q[0] + sx, q[1] + sy) for q in lp],
                                         amp, seed=n_loop + lvl * 7919,
                                         closed=True, sgn=-winding_sign(lp))
                        out.append(((far + near) * 0.5,
                                    f'<path class="pp-copse-shadow" '
                                    f'd="{sd}{d}"/>'))
                    out.append(((far + near) * 0.5,
                                f'<path class="{cls}" d="{d}"/>'))
        self.stats["scrub_forest_skirts"] = n_big
        self.stats["scrub_mass_loops"] = n_loop
        return near_m, far_m

    def copse_shadow_px(self, band):
        """How far down-sun a SCRUB_COPSE_H stand throws its shadow, in screen
        pixels, at one stratum's own range.

        One sample per band, taken at a cell that is actually in it: the
        offset is a few pixels and its variation across a stratum is well
        under one, so a per-loop solve would cost a projection each and print
        the identical drawing. The RULE is the one every built thing on this
        sheet obeys -- a true height at the true solar altitude, through
        sun_offset -- and only the sampling is coarse."""
        if not band or not OBJ_SHADOW or LIGHT_ALT <= 0.5:
            return (0.0, 0.0)
        i, j = min(band)
        e, n = self.wor[i][j]
        g = self.grid[i][j][2]
        p0 = self.cam.project(e, n, built_h(0.05, g))
        dx, dy = sun_offset(SCRUB_COPSE_H)
        p1 = self.cam.project(e + dx, n + dy, built_h(0.05, g))
        if not p0 or not p1:
            return (0.0, 0.0)
        return (p1[0] - p0[0], p1[1] - p0[1])

    def vegetation_svg(self):
        """Everything that grows on this sheet. See the VEGETATION note above
        the primitives for what each class is and which line of the poem puts
        it there; this method is only the placement.

        Painted after the water and the rivers and before the camp, which is
        depth order for these marks: the thicket is at 6-15 km, the ridge
        scrub runs from under the reader's feet to the mesh's edge, and the
        fleet is nearer than either.

        EVERY CLASS IS DRAWN TWICE AND THE TWO DRAWINGS ARE DIFFERENT MARKS.
        At the overview the fringe is one lobed ribbon and the cover is one
        merged patch, because at 800 m up and 7 km out an 8 m canopy is under
        a pixel and anything countable is drawing what cannot be seen. At the
        zoom tier the same ground carries the clumps and the tufts, because at
        4x and 8x they genuinely are resolvable. Nothing is scaled between the
        two; each is generated for its own tier."""
        if not VEG:
            return ""
        cam, terr = self.cam, self.terr
        marks_t1: list = []      # the mass, at the overview
        marks_t3: list = []      # its members, once the reader has come closer
        n_bank = n_scrub = n_run = 0

        # ── the riverbank thicket, along the drawn courses ───────────────
        # THE CLUMPS ALTERNATE BANKS. At the overview they are not drawn as
        # clumps at all: the stations are collected into runs and each run
        # closes as ONE ribbon whose upper edge is a chain of overlapping
        # scallops -- the lobe pitch is the station pitch, so the boundary
        # never returns to its baseline between neighbours and has no member
        # to count. The tall-over-low alternation of 21.350-51 is what breaks
        # that edge up: elm at 13 m and tamarisk at 4 m give the silhouette
        # its own rise and fall, at true heights, with no mark added.
        for name, tier, course in getattr(self, "river_courses", []):
            if len(course) < 4:
                continue
            step = BANK_STEP_M * 0.5
            flat = [pp._flat_m(p, *VIEWPOINT) for p in course]
            run = 0.0
            k = 0
            band: list = []      # the current run: (x, ground_y, canopy_y)
            foot: list = []      # and its ground and down-sun shadow feet
            b_dep = None

            def close_run():
                nonlocal band, foot, b_dep, n_run
                if len(band) >= BANK_MASS_MIN_PTS and b_dep is not None:
                    sd = ""
                    if OBJ_SHADOW and len(foot) >= BANK_MASS_MIN_PTS:
                        ring = [q[0] for q in foot] + [q[1] for q in
                                                       reversed(foot)]
                        sd = ('<path class="pp-objshadow" d="%s"/>'
                              % rel_poly(ring))
                    sd_seed = n_run * 17 + 3
                    body = bank_mass(band, seed=sd_seed)
                    if body:
                        n_run += 1
                        marks_t1.append((b_dep, sd + body
                                         + bank_mass(band, seed=sd_seed,
                                                     lit=True)))
                band, foot, b_dep = [], [], None

            for a, b in zip(flat, flat[1:]):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if seg < 1e-6:
                    continue
                tx, ty = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
                while run < seg:
                    f = run / seg
                    k += 1
                    side = 1.0 if k % 2 else -1.0
                    jit = 0.55 + 0.9 * _rnd(k, int(a[0]), int(a[1]))
                    off = BANK_OFFSET_M * jit * side
                    # the CLUMP takes its bank; the MASS takes the course. The
                    # alternation is right for the clumps and wrong for the
                    # ribbon: at 26 m it is two pixels here, and two pixels
                    # flipped at every station is a sawtooth -- a pitch, and
                    # therefore countable, which is the whole defect. On the
                    # course line the same run has only the rise and fall of
                    # what stands in it, which is what a fringe looks like.
                    ce, cn = a[0] + tx * run, a[1] + ty * run
                    e = ce - ty * off
                    n = cn + tx * off
                    lat = VIEWPOINT[0] + n / 111132.0
                    lon = (VIEWPOINT[1] + e
                           / (111320.0 * math.cos(math.radians(VIEWPOINT[0]))))
                    # tall over low, as 21.350-51 has it: elm, willow and
                    # tamarisk over lotus, rush and galingale. The herb layer
                    # is under a tenth of a pixel at these ranges and is
                    # lettered in the key instead of drawn.
                    tall = _rnd(k, 7, int(e)) < 0.58
                    h, r = ((BANK_TREE_H, BANK_TREE_R) if tall
                            else (BANK_SHRUB_H, BANK_SHRUB_R))
                    sv = thicket(cam, terr, lat, lon, h, r, seed=k * 31 + tier)
                    run += step
                    clat = VIEWPOINT[0] + cn / 111132.0
                    clon = (VIEWPOINT[1] + ce
                            / (111320.0 * math.cos(math.radians(VIEWPOINT[0]))))
                    gz = terr.elev(clat, clon)
                    p = cam.project(ce, cn, built_h(0.0, gz))
                    pt = cam.project(ce, cn, built_h(h, gz))
                    ok = (sv and p and pt
                          and -BLEED < p[0] < W + BLEED
                          and -BLEED < p[1] < H + BLEED)
                    if not ok:
                        close_run()
                        continue
                    n_bank += 1
                    marks_t3.append((p[2], sv))
                    # a run breaks at a stratum edge, so each ribbon takes the
                    # air at its own range, and at a jump in screen position,
                    # which is where the course has left the frame and come
                    # back or crossed a ridge
                    dep = next(s for s in range(len(STRATA_EDGES) - 1)
                               if STRATA_EDGES[s + 1] <= p[2] < STRATA_EDGES[s])
                    if b_dep is not None and (dep != b_dep or (
                            band and math.hypot(p[0] - band[-1][0],
                                                p[1] - band[-1][1]) > 34.0)):
                        close_run()
                    b_dep = dep
                    band.append((p[0], p[1], pt[1]))
                    dx, dy = sun_offset(h)
                    ps = cam.project(ce + dx, cn + dy, built_h(0.05, gz))
                    if ps:
                        foot.append(((p[0], p[1]), (ps[0], ps[1])))
                run -= seg
            close_run()
        # the ribbons carry a stratum INDEX; _aired wants a range
        marks_t1 = [((STRATA_EDGES[s] + STRATA_EDGES[s + 1]) * 0.5, m)
                    for s, m in marks_t1]

        # ── ridge scrub ─────────────────────────────────────────────────
        # DENSITY IS HELD IN SCREEN AREA, NOT IN GROUND AREA, which is the
        # hachure discipline: the marks keep a constant apparent spacing and
        # so the ridge reads as one texture from the foreground to the far
        # crests instead of as a lattice going to mush. It also makes the
        # class self-extinguishing where it should be -- the tick's height is
        # TRUE, so 1.4 m of maquis falls under the ink at about 3 km and the
        # far ridges simply stop carrying scrub, exactly as slope hachures
        # vanish on flat ground by construction.
        #
        # AND IT IS NOW MODULATED BY THE GROUND ITSELF (see scrub_cover): the
        # constant that used to sit here was a pitch, and a pitch is what the
        # eye counts. Curvature, slope and aspect say where maquis thickens
        # and where the limestone shows through, all three off the DEM, so the
        # patchiness is measured and the class still covers exactly the ground
        # it covered before.
        dens = self.scrub_cover()
        near_m, far_m = self.scrub_mass_svg(dens)
        marks_t1 += near_m
        grid = self.grid
        for (i, j) in self.visible:
            if self.cover.get((i, j)) != COVER_RIDGE:
                continue
            dv = dens.get((i, j), 0.0)
            if dv <= 0.0:
                continue
            a0, a1 = grid[i][j], grid[i + 1][j]
            b1, b0 = grid[i + 1][j + 1], grid[i][j + 1]
            if a0[3] > SCRUB_REACH:
                continue
            quad = [(a0[0], a0[1]), (a1[0], a1[1]), (b1[0], b1[1]), (b0[0], b0[1])]
            area = abs(poly_area(quad))
            if area < 2.0:
                continue
            (e0, n0), (e1, n1_) = self.wor[i][j], self.wor[i + 1][j]
            (e2, n2), (e3, n3) = self.wor[i + 1][j + 1], self.wor[i][j + 1]
            want = area / SCRUB_PX2_ZOOM * dv
            n_tick = int(want) + (1 if _rnd(i, j, 3) < (want % 1.0) else 0)
            for t in range(min(n_tick, 14)):
                u, v = _rnd(i, j, t, 5), _rnd(i, j, t, 9)
                e = (e0 * (1 - u) + e1 * u) * (1 - v) + (e3 * (1 - u) + e2 * u) * v
                n = (n0 * (1 - u) + n1_ * u) * (1 - v) + (n3 * (1 - u) + n2 * u) * v
                lat = VIEWPOINT[0] + n / 111132.0
                lon = (VIEWPOINT[1] + e
                       / (111320.0 * math.cos(math.radians(VIEWPOINT[0]))))
                g_ = terr.elev(lat, lon)
                pb = cam.project(e, n, built_h(0.0, g_))
                pt = cam.project(e, n, built_h(SCRUB_H, g_))
                if not pb or not pt:
                    continue
                hp = pb[1] - pt[1]
                if hp < VEG_MIN_PX:
                    continue
                w_ = hp * 0.75
                # four stems from one foot, and the fourth is what the mark
                # gained when it stopped having to carry the class at 1x: at
                # 8x a three-stroke tuft is a fork, a four-stroke one is a
                # bush. The lean of each is the mark's own hash, so no two
                # stand the same way.
                jx = (_rnd(i, j, t, 21) - 0.5) * w_ * 0.5
                d = (f'M{n1(pb[0] - w_)} {n1(pb[1] - hp * 0.9)}'
                     f'L{n1(pb[0])} {n1(pb[1])}'
                     f'L{n1(pb[0] + w_)} {n1(pb[1] - hp * 0.85)}'
                     f'M{n1(pb[0])} {n1(pb[1])}L{n1(pb[0] + w_ * 0.15)} '
                     f'{n1(pb[1] - hp)}'
                     f'M{n1(pb[0])} {n1(pb[1])}L{n1(pb[0] - w_ * 0.45 + jx)} '
                     f'{n1(pb[1] - hp * 0.62)}')
                n_scrub += 1
                marks_t3.append((a0[3], f'<path class="pp-scrub" d="{d}"/>'))

        self.stats["veg_bank"] = n_bank
        self.stats["veg_bank_runs"] = n_run
        self.stats["veg_scrub"] = n_scrub
        return (self._aired(far_m)
                + self._aired(marks_t1, "t1-only")
                + self._aired(marks_t3, "tm3"))

    # ── the camp ─────────────────────────────────────────────────────────
    def camp(self):
        """Ships hauled up in rows, prows to the water; huts on the ridge
        behind; the wall and its ditch inland of both. Every position is
        conjectural, laid against the measured shoreline: the poem is exact
        about the camp's SHAPE (14.31-36, rows because one row would not fit
        between the headlands) and silent about its ground.

        THE FLEET IS DRAWN TWICE, and this is the whole of the ships fix.
        The plate is NAMED for the ships and they were the weakest thing on
        it: hulls at a true 13 m pitch, ranks deep, are 2.7 px of beam each
        with the rows behind filling every gap, so at 1x they integrate
        into one dark body — and the tier-1 mark was worse than that, a
        SOLID BAND with a zigzag top edge, which is a fence. A reader had to
        ask outright whether it was ships or a wall.

        THREE THINGS THE FIRST PASS AT IT GOT WRONG, all in the same corner
        and all now answered above where their numbers live: the hulls had
        no freeboard and read as buried (SHIP_KEEL_H); the clearance test
        asked only whether a berth's STERN stood on dry sand, so the
        overview's long glyphs put their forefeet in the bay (afloat); and
        the enlargement was anisotropic, which made a quill of a ship
        (FLEET_T1_LEN_K).

        The vegetation lane's defect was the inverse of this one and so is
        the fix. Plants read as countable individuals and had to be merged
        into mass; the ships had merged into mass and had to be given back
        their identity. What makes a hull read as a hull is AIR either side
        of it, and air at 1x can only be bought with count.

        So the overview draws a RANK: fewer stations, two rows instead of
        three, each hull at FLEET_T1_LEN_K times its size — Pope's plate of
        1716 and the whole tradition after it draw the beached fleet as one
        glyph repeated at a pitch, never as individuated hulls, and that is
        why his reads at plate scale and ours did not
        (docs/research/DEPICTIONS-OF-TROY.md, "Concrete, implementable
        lessons", 1). It is not a claim and it does not become one: the key
        has always declared the ships "hulls in ranks with the huts behind,
        filling the frontage in view and never the catalogue's count", and
        that sentence covers the drawn NUMBER and not the drawn SIZE, which
        is why the key now states the enlargement and its factor outright.
        At 4x and 8x the tier-1 rank switches off and the true fleet — 13 m
        pitch, three ranks, 4.2 m beam, every hull true — is underneath."""
        cam, terr = self.cam, self.terr
        sea_poly = self.shore("sea-modern")
        camp_zone = self.lay["achaean-camp-zone"]["polygon"]
        layout = aegean_fleet(sea_poly, camp_zone, self.shore("lagoon-bronze"))
        origin = layout["origin"]
        th = math.radians(CAMP_SEAWARD_DEG)

        def wet(f, lateral):
            lat, lon = camp_ll(origin, lateral, f)
            return point_in_poly_ll(lat, lon, sea_poly)

        def shore_forward(lateral):
            """How far west the beach runs on this station, REFINED to about
            a metre. It used to return the last dry 25 m step, and the 25 m
            staircase was invisible in everything that consumed it except the
            one thing that differentiates it: the prow bearing below took the
            slope over a 26 m baseline, so a single step of the staircase was
            a 44-degree swing, and adjacent ships in the same rank pointed
            44 degrees apart. At a 2.7 px hull nobody could see it. At the
            overview's glyph it was the whole defect — a rank that looked
            like a heap.

            Walk starts at the camp zone's west edge, not at the camera:
            the beach is the Aegean, ~700 m west of the ridge-crest zone."""
            q = layout["shore"].get(round(lateral / 13.0) * 13.0)
            if q is not None:
                return q
            lo = None
            f = -400.0
            started = False
            while f < 4000.0:
                lat, lon = camp_ll(origin, lateral, f)
                in_zone = point_in_poly_ll(lat, lon, camp_zone)
                if in_zone:
                    started = True
                if started and wet(f, lateral):
                    if lo is None:
                        return None
                    a, b = lo, f
                    for _ in range(4):           # 25 m -> ~1.5 m
                        mid = 0.5 * (a + b)
                        if wet(mid, lateral):
                            b = mid
                        else:
                            a = mid
                    return a
                if started or in_zone:
                    lo = f
                f += 25.0
            return None

        def near_camp(lat, lon, margin_m=380.0):
            """The zone polygon is the ridge crest/plateau, 13-24 m up; the
            beach sits ~700 m west of its west edge down the scarp. A 380 m
            vertex blob never reaches that sand, so the gate also accepts a
            point from which an eastward walk hits the zone (the zone's own
            west apron). Widening the blob would have admitted the bay side
            too; measuring from the west edge does not."""
            if point_in_poly_ll(lat, lon, camp_zone):
                return True
            for plat, plon in camp_zone:
                if math.hypot(*pp._flat_m((plat, plon), lat, lon)) < margin_m:
                    return True
            landward = (CAMP_SEAWARD_DEG + 180.0) % 360.0
            d = 25.0
            while d <= 1000.0:
                plat, plon = pp._dest_point((lat, lon), landward, d)
                if point_in_poly_ll(plat, plon, camp_zone):
                    return True
                d += 25.0
            return False

        def ll(f, lateral):
            return camp_ll(origin, lateral, f)

        # ROWS, at the poem's own reason for them: the beach could not hold
        # the fleet in one line (14.31-36) -- οὐδὲ γὰρ οὐδ' εὐρύς περ ἐὼν
        # ἐδυνήσατο πάσας / αἰγιαλὸς νῆας χαδέειν -- so they hauled them up
        # προκρόσσας, in ranks (14.35). 13 m of lateral pitch on a 4.2 m beam
        # is roomy; how DEEP the ranks go is FLEET_ROWS, and why it is three
        # and not five is worked out there.
        ships, ship_px, hulls_drawn, depths = [], [], 0, []
        ships_t1: list = []
        obj_sh: list = []           # the hulls', which are tier 2 and up
        obj_sh_t1: list = []        # the overview rank's
        hut_sh: list = []           # the huts', which are on at EVERY tier,
                                    # because the huts are

        # The silhouette that throws: the deck's outline at its true 2.4 m
        # with the stem-post's 6.4 m tip.
        #
        # THE OVERVIEW'S GLYPH THROWS THE TRUE SHIP'S SHADOW, not its own.
        # Drawn at the glyph's 82 m by 8.4 m the shadow came out BIGGER than
        # the hull and squarer, and eighty grey slabs with a ship on each is
        # a rank of pallets. It is also the more honest division of labour:
        # the shadow says where a ship stands and how big it is, the glyph
        # says what it is, and only one of those two jobs needs a convention.
        HULL_SIL = ([((f * 24.0, s * hb * 4.2), SHIP_DECK_H)
                     for f, hb in ((0.0, 0.30), (0.34, 0.50),
                                   (0.82, 0.36), (1.0, 0.06))
                     for s in (1, -1)]
                    + [((24.0 * 1.12, 0.0), SHIP_POST_H)])
        HUT_SIL = [((-2.5, -3.5), 1.8), ((-2.5, 3.5), 1.8),
                   ((2.5, -3.5), 1.8), ((2.5, 3.5), 1.8),
                   ((0.0, -3.5), 3.2), ((0.0, 3.5), 3.2)]
        lat_span = [x * 13.0 for x in range(
            int(math.floor(layout["a0"] / 13.0)),
            int(math.ceil(layout["a1"] / 13.0)) + 1)]
        shore = layout["shore"]

        def seaward(lateral):
            """The bearing a hull's prow takes: the OUTWARD NORMAL OF THE
            SHORE at this point on the beach, not a constant. Every ship laid
            on the camera's own heading pointed straight away from the eye
            wherever the coast turned, and a beached galley seen exactly
            end-on is a dark blob, not a ship.

            THE SLOPE IS TAKEN OVER 130 m, not over 26. A shoreline sampled
            off a reconstructed polygon has metre-scale wobble in it that is
            not coastline, it is the polygon's own vertex spacing; over a
            26 m baseline that wobble IS the derivative, and the ranks came
            out fanned. 130 m is about five true berths — the scale at which
            a beach really does turn — and it is what makes a rank read as
            προκρόσσας (14.35) rather than as wreckage."""
            xs, ys = [], []
            for k in range(-5, 6):
                q = shore.get(round((lateral + k * 13.0) / 13.0) * 13.0)
                if q is not None:
                    xs.append(k * 13.0)
                    ys.append(q)
            if len(xs) < 4:
                return CAMP_SEAWARD_DEG
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            den = sum((x - mx) ** 2 for x in xs)
            if den <= 0:
                return CAMP_SEAWARD_DEG
            dfdl = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
            nf, nl = 1.0, -dfdl
            L = math.hypot(nf, nl)
            th_s = math.radians(CAMP_SEAWARD_DEG)
            th_a = math.radians(CAMP_AXIS_DEG)
            de = (nf * math.sin(th_s) + nl * math.sin(th_a)) / L
            dn = (nf * math.cos(th_s) + nl * math.cos(th_a)) / L
            return math.degrees(math.atan2(de, dn)) % 360.0

        def dry_at(lateral):
            """The waterline on this line of the beach, from the cache where
            the cache has it. Berths are laid at whatever pitch they ask for
            and the cache is on the true fleet's 13 m, so a tier-1 prow can
            reach a lateral nobody has sampled."""
            q = shore.get(round(lateral / 13.0) * 13.0)
            return q if q is not None else shore_forward(lateral)

        def afloat(f, lateral, bearing, reach_m):
            """Whether any part of a hull berthed here would be in the water.

            THE CLEARANCE IS TESTED AGAINST THE FOREFOOT, NOT THE ANCHOR, and
            that distinction is the whole bug. A berth's anchor is her STERN;
            she then runs `reach_m` forward along her own bearing, which is
            the shore normal and not the camera's heading, so she both
            advances toward the water and slides ALONG the beach to a lateral
            whose waterline is somewhere else entirely. The old test asked
            only whether the stern stood on dry sand. At the true fleet's
            26.9 m reach that was harmless; at the overview rank's 91.4 m it
            put the seaward row's forefoot 1.4 m PAST the waterline on flat
            frontage and much further wherever the coast turned, so hulls sat
            half in the bay — a fleet half-launched, which is the exact
            opposite of ships hauled up ὑψοῦ ἐπὶ ψαμάθοις and shored for ten
            years (1.485-86).

            Three points are asked, because a bow is not a needle: the stem
            and both forward quarters."""
            b = math.radians(bearing)
            for u, v in ((reach_m, 0.0),
                         (reach_m * 0.80, +reach_m * 0.055),
                         (reach_m * 0.80, -reach_m * 0.055)):
                de = u * math.sin(b) + v * math.cos(b)
                dn = u * math.cos(b) - v * math.sin(b)
                ft = f + de * math.sin(th) + dn * math.cos(th)
                lt = lateral + de * math.cos(th) - dn * math.sin(th)
                fs = dry_at(lt)
                if fs is None or ft > fs - DRY_MARGIN_M:
                    return True
            return False

        def berths(pitch, rows, row_m, first_m=66.0, stagger=11.0,
                   reach_m=0.0):
            """Every place on the beach a hull can stand, collected BEFORE
            anything is drawn. The order matters: Odysseus's twelve are the
            twelve nearest the middle of the line (8.222-23, ἐν μεσσάτῳ),
            and the middle of the line is not known until the whole line
            is."""
            out = []
            # the camp zone's own long axis, sampled at whatever pitch asks.
            #
            # STATION ACCEPTANCE IS BY THE SHORE WALK ALONE, not by
            # near_camp's polygon-vertex blob (ruling 4 diagnosis,
            # 2026-09-02): the zone polygon is the RIDGE LANDFORM's own
            # outline (apparatus/plates/trojan-plain.json note on
            # achaean-camp-zone), 600-900 m wide station to station because
            # it is a real hill, not a thin crest line -- so a berth's
            # near_camp() eastward walk (capped at 1000 m) missed it at
            # ~1/4 of stations for no reason connected to whether the berth
            # is a sane place to put a ship. The shore walk already answers
            # the only question that matters -- is this station's waterline
            # within reach of the axis at all -- so a bare distance check on
            # fs replaces it.
            for lateral in [x * pitch for x in
                            range(int(math.floor(layout["a0"] / pitch)),
                                  int(math.ceil(layout["a1"] / pitch)) + 1)]:
                fs = shore.get(round(lateral / 13.0) * 13.0)
                if fs is None:
                    fs = shore_forward(lateral)
                if fs is None or fs > 1500.0:
                    continue
                bearing = seaward(round(lateral / 13.0) * 13.0)
                for row in range(rows):
                    f = fs - first_m - row * row_m + (stagger if row % 2 else 0.0)
                    if f < 60:
                        continue
                    lat, lon = ll(f, lateral)
                    if point_in_poly_ll(lat, lon, camp_zone):
                        continue
                    if point_in_poly_ll(lat, lon, self.shore("lagoon-bronze")):
                        continue
                    if terr.elev(lat, lon) > 16.0:
                        continue
                    if afloat(f, lateral, bearing, reach_m):
                        continue
                    sp = cam.project_ll(lat, lon, built_h(SHIP_DECK_H,
                                                          terr.elev(lat, lon)))
                    if not sp or not (-BLEED < sp[0] < W + BLEED
                                      and -BLEED < sp[1] < H + BLEED):
                        continue
                    out.append((lateral, row, f, lat, lon, bearing, sp))
            return out

        def miltos(berth_list, n):
            """ODYSSEUS'S TWELVE, and only his twelve. δυώδεκα μιλτοπάρῃοι
            (2.637) is said of his contingent alone in the Iliad, and his
            ship is ἐν μεσσάτῳ, in the very middle, because from there he
            can be heard both ways down the line — to Ajax's huts at the one
            end and Achilles' at the other (8.222-26). So the vermilion is a
            BLOCK in the middle of the fleet, which is the poem's own
            statement about where Odysseus is, drawn in the one language a
            plate has. Everything else keeps the general formula's dark-blue
            prow.

            n is twelve on the true fleet. On the overview's rank it is
            twelve scaled by the rank's own count, for the same reason every
            other number there is scaled: the rank draws a sixth of the
            berths, so twelve of them would be a sixth of the fleet in
            vermilion and the plate would be saying something false about how
            much of the line is Odysseus's."""
            if not berth_list or n < 1:
                return set()
            lats = sorted(q[0] for q in berth_list)
            med = lats[len(lats) // 2]
            order = sorted(range(len(berth_list)),
                           key=lambda i: (abs(berth_list[i][0] - med),
                                          berth_list[i][1]))
            return set(order[:n])

        red = set()
        if DRAW_FLEET:
            true_berths = berths(13.0, FLEET_ROWS, FLEET_ROW_M,
                                 first_m=FLEET_FIRST_M, reach_m=24.0)
            red = miltos(true_berths, ODYSSEUS_TWELVE)
            for i, (lateral, row, f, lat, lon, bearing, sp) in enumerate(true_berths):
                sh = ship(cam, terr, lat, lon, bearing, props=True,
                          prow_cls="pp-prow-miltos" if i in red else "pp-prow")
                if sh:
                    ships.append(sh)
                    sd = object_shadow(cam, terr, lat, lon, bearing, HULL_SIL,
                                       lift=SHIP_KEEL_H)
                    if sd:
                        obj_sh.append(sd)
                    hulls_drawn += 1
                    ship_px.append((sp[0], sp[1], lateral, f, lat, lon))
                    depths.append(sp[2])

            # ── and the same beach, at the overview's own count and size ──
            t1_berths = berths(FLEET_T1_PITCH_M, FLEET_T1_ROWS, FLEET_T1_ROW_M,
                               first_m=FLEET_T1_FIRST_M,
                               stagger=FLEET_T1_PITCH_M * 0.5,
                               reach_m=24.0 * FLEET_T1_LEN_K)
            red_t1 = miltos(t1_berths, max(1, round(
                ODYSSEUS_TWELVE * len(t1_berths) / max(1, len(true_berths)))))
            for i, (lateral, row, f, lat, lon, bearing, sp) in enumerate(t1_berths):
                sh = ship(cam, terr, lat, lon, bearing,
                          beam_k=FLEET_T1_BEAM_K, len_k=FLEET_T1_LEN_K,
                          post_cls="pp-post-t1", stern_h=FLEET_T1_STERN_H,
                          prow_cls="pp-prow-miltos" if i in red_t1 else "pp-prow")
                if sh:
                    ships_t1.append(sh)
                    sd = object_shadow(cam, terr, lat, lon, bearing, HULL_SIL,
                                       lift=SHIP_KEEL_H)
                    if sd:
                        obj_sh_t1.append(sd)
        else:
            true_berths = []

        huts = []
        hut_lls = []
        # HUTS BEHIND THE SHIPS, not across the whole 9 km zone. The zone
        # polygon is the ridge landform's own outline (diagnosis, ruling 4,
        # 2026-09-02) and the true fleet only stands where the beach is wide
        # enough for it -- most of the 9 km has none. Sampling every 34 m of
        # the zone regardless painted huts the length of the ridge, on the
        # plateau far from any ship, which is the dense mid-ground field the
        # camp() docstring's own convention never asked for. Huts are drawn
        # only over the along-span the true fleet actually occupies (with a
        # margin so a hut can sit behind the end berths), and only where the
        # projection lands in frame -- the same test the ships already pass.
        span = true_berths if true_berths else layout["berths"]
        hut_laterals = ([q[0] for q in span] if span
                        else [x * 34.0 for x in range(
                            int(math.floor(layout["a0"] / 34.0)),
                            int(math.ceil(layout["a1"] / 34.0)) + 1)])
        hut_lo = min(hut_laterals) - 100.0
        hut_hi = max(hut_laterals) + 100.0
        for lateral in [x * 34.0 for x in range(
                int(math.floor(hut_lo / 34.0)),
                int(math.ceil(hut_hi / 34.0)) + 1)]:
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
                sp = cam.project_ll(lat, lon, built_h(3.2, terr.elev(lat, lon)))
                if not sp or not (-BLEED < sp[0] < W + BLEED
                                  and -BLEED < sp[1] < H + BLEED):
                    continue
                hut_lls.append((lat, lon))
                if not DRAW_HUTS:
                    continue
                hb = seaward(round(lateral / 13.0) * 13.0) + (17 if row % 2 else -11)
                hh = hut(cam, terr, lat, lon, hb)
                if hh:
                    huts.append(hh)
                    sd = object_shadow(cam, terr, lat, lon, hb, HUT_SIL)
                    if sd:
                        hut_sh.append(sd)

        # THE SERRATED MASS IS GONE, and its removal is the fix, not a side
        # effect of it. It was one filled polygon per stretch of beach with a
        # zigzag along the seaward edge — the note that built it argued the
        # prows in the zigzag would say "ships" rather than "a dark band",
        # and on the page they said fence. A solid has no air in it, and air
        # between the hulls is the only thing that makes a hull a hull. What
        # stands here now is the rank built above: individual glyphs, at the
        # overview's own count and size, with the beach showing between them.

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
        wall_back = layout["wall_back"]
        ditch_back = layout["ditch_back"]
        for nth, lateral in enumerate([x * 34.0 for x in range(
                int(math.floor(layout["a0"] / 34.0)),
                int(math.ceil(layout["a1"] / 34.0)) + 1)]):
            fs = shore_forward(lateral)
            if fs is None:
                continue
            lat, lon = ll(fs - wall_back, lateral)
            if not near_camp(lat, lon, 300.0):
                continue
            g = terr.elev(lat, lon)
            crest = 4.6 + (3.4 if nth % 4 == 0 else 0.0)
            a = cam.project_ll(lat, lon, built_h(0.0, g))
            b = cam.project_ll(lat, lon, built_h(crest, g))
            latd, lond = ll(fs - ditch_back, lateral)
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
        self.stats["hulls_t1"] = len(ships_t1)
        self.stats["hulls_miltos"] = len(red)
        self.stats["huts"] = len(huts)
        self.stats["ship_depth"] = round(sum(depths) / len(depths), 1) if depths else 2600.0
        self.stats["beach_frontage_m"] = round(
            (max(q[2] for q in ship_px) - min(q[2] for q in ship_px)) if ship_px else 0.0)
        self.stats["obj_shadows"] = len(obj_sh) + len(obj_sh_t1) + len(hut_sh)
        geo = layout["berths"]
        if geo:
            clat = sum(q[3] for q in geo) / len(geo)
            clon = sum(q[4] for q in geo) / len(geo)
            self.stats["fleet_centroid"] = [round(clat, 5), round(clon, 5)]
            spc = cam.project_ll(clat, clon, built_h(0.0, terr.elev(clat, clon)))
            if spc:
                self.stats["fleet_centroid_screen"] = [
                    round(spc[0], 1), round(spc[1], 1), round(spc[2], 1)]
        if hut_lls:
            hlat = sum(q[0] for q in hut_lls) / len(hut_lls)
            hlon = sum(q[1] for q in hut_lls) / len(hut_lls)
            self.stats["hut_centroid"] = [round(hlat, 5), round(hlon, 5)]
            sph = cam.project_ll(hlat, hlon, built_h(3.2, terr.elev(hlat, hlon)))
            if sph:
                self.stats["hut_centroid_screen"] = [
                    round(sph[0], 1), round(sph[1], 1), round(sph[2], 1)]
        self.stats["wall_at"] = [round(layout["wall"][0], 5),
                                 round(layout["wall"][1], 5)]
        self.stats["ditch_at"] = [round(layout["ditch"][0], 5),
                                  round(layout["ditch"][1], 5)]
        return (ships, ships_t1, huts, wall_svg, ditch_svg, ship_px,
                obj_sh, obj_sh_t1, hut_sh)

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
        wet = self.shore("lagoon-bronze")
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
            aegean_fleet(self.shore("sea-modern"),
                         self.lay["achaean-camp-zone"]["polygon"],
                         self.shore("lagoon-bronze"))["wall"], 4.6, "line",
            "On the Aegean (outer) flank of the Sigeum ridge, 60 m landward "
            "of the rearmost sterns, after Kraft, Rapp, Kayan and Luce 2003; "
            "the beach uses the modern coastline, no Bronze Age reconstruction "
            "of the outer coast being published in our sources.")
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


# ── THE NOTES HAD NO MEASURE, AND THAT IS WHY THEY READ AS A SLAB ────────
# "legend is too busy" (John, 2026-08-15). Measured before anything was
# touched: the margin sets about 3,500 characters, and 1,930 of them were
# five <text> elements running the full 2,276 px between the margins. SVG
# text does not wrap, so each note WAS one physical line -- about 380
# characters of it, against print's 45-75 and this project's own rule for
# every other block on the sheet. Five of those stacked at 11.5 px is a grey
# slab across the foot of the plate, and a slab has no entry point: there is
# nowhere for the eye to start, so the whole block reads as one texture and
# none of it gets read.
#
# The fix is a MEASURE, not a cut. Every sentence down there is a claim that
# a test pins -- the citations, the measured/conjectural split, the
# never-an-invented-coordinate rule, the repair of the drowned gap, DRAFT --
# and the handoff's own warning is the right one: cutting a gloss thoughtlessly
# makes the plate assert silently. So the text stays and the TYPESETTING
# changes: wrapped to a real measure, set in columns, each column under its own
# heading so the block has four entry points instead of none.
#
# 4.4 px per character is measured off the shipped frame, not assumed: note 1
# is 486 characters and runs 62 -> ~2200 px, note 2 is 382 and runs to ~1712.
# It is only used to CHOOSE the wrap width; nothing downstream depends on the
# glyph advance being right, because a column that comes out narrow is still
# a column.
NOTE_CH_PX = 4.4


def wrap(text: str, width_px: float, ch=NOTE_CH_PX) -> list[str]:
    """Greedy word wrap to a width in PIXELS. Deterministic, no hyphenation:
    a word longer than the measure gets its own line rather than being cut,
    because every over-long token on this sheet is a Greek phrase or a
    citation and neither may be broken."""
    n = max(1, int(width_px / ch))
    out, line = [], ""
    for word in text.split():
        cand = word if not line else line + " " + word
        if len(cand) <= n or not line:
            line = cand
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


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
     "sand-covered, dusty, firm — lettered THE BATTLEFIELD after Kayan 2002, "
     "his reading of the surface, not the poem’s name"),
    (COVER_RIDGE, "RIDGE SCRUB, BARE SLOPE",
     "thin soil on limestone — a regional default, not a survey"),
    ("wet", "WET DELTA, SWAMP",
     "waterlogged delta behind the bay (Kayan 2003) — no edge"),
    (COVER_OPEN, "GROUND BEYOND THE PLAIN",
     "not classified — the three ridges are cut at 20, 40 and 100 m, so there "
     "is no one rule to carry outward"),
)
COVER_KEY_UNDRAWN = (
    "Not drawn: the thicket’s WIDTH — the channels lie under 20 m of alluvium, so the "
    "fringe follows the drawn course at an artist’s width, never a measured one. Ida’s "
    "timber as TREES (Il. 23.114–20; 14.287) — at 66 km one is a tenth of a pixel, so "
    "the mountain is coloured wooded and nothing is planted on it. Reeds over the wet "
    "delta — 21.351 names rush and galingale, 21.352 sites them at the river. Nothing "
    "on the dry fan — the epithets (6.315; 20.226) call it good soil, and no pattern."
)
# ── THE TWO WATERS, AND WHY THE KEY HAD LOST THEM ────────────────────────
# When the legend was rewritten from a twelve-step elevation ramp to four
# ground-cover entries, the old "Open sea" and "Lagoon and shallow water"
# rows went with it -- and the plate draws two water bodies that are two
# different KINDS OF CLAIM. A reader who cannot tell which coastline is
# surveyed and which is reconstructed cannot read the sheet. They are back,
# each carrying its evidence in the same breath as its swatch, exactly as the
# ground-cover rows do.
WATER_KEY = (
    ("sea", "OPEN SEA",
     "the Aegean and the Dardanelles as they stand — surveyed (Copernicus GLO-30)"),
    ("lagoon", "THE BAY OF TROY, RECONSTRUCTED",
     "the Late Bronze Age embayment (Kraft, Kayan and Erol 1980; Kayan) — a wash, "
     "and a lighter line"),
)
# ── AND THE MARKS. Everything below is drawn on the plate and, until now,
# explained nowhere: a reader could count 465 hulls and think we were making
# a claim about the fleet. Every line here is a CONVENTION being declared,
# which is the only kind of thing a key can honestly say about a mark whose
# position is conjectural.
DRAWN_MARKS = (
    "Marks, each a declared convention: ships as hulls in ranks with the huts behind, "
    "filling the frontage in view and never the catalogue’s count; the wall and its "
    "ditch one line each at the camp’s inland edge (Il. 7.436–441; 14.30–36); the "
    "ships beach on the Sigeum ridge’s Aegean flank, modern coast standing in "
    "(Kraft et al. 2003); a "
    "tumulus a low shadowed mound; the wagon-road one line from the gate onto the "
    "plain (22.146), an open ring at each waypoint in the poem’s own order."
)
# ── THE CAMP IS BUILT OF FOUR THINGS AND THE POEM NAMES ALL FOUR. Same rule
# as VEG_KEY: the mark carries the line that puts it there, in the same
# breath as the mark. It was two near-black tokens and a roof borrowed off
# the citadel's masonry, which is neither honest nor legible.
CAMP_KEY = (
    ("THE SHIPS", "pitch, νῆες μέλαιναι — Il. 9.235 = 11.824 = 12.107; dark-blue prows, "
     "κυανόπρῳρος — 15.693; vermilion on Odysseus’ twelve alone, μιλτοπάρῃοι — 2.637, "
     "a block ἐν μεσσάτῳ — 8.222–26. Beached on the Aegean outer flank of the "
     "Sigeum ridge; modern coast, no Bronze Age outer-coast reconstruction in "
     "our sources"),
    ("ON PROPS", "hauled out ὑψοῦ ἐπὶ ψαμάθοις, high on the sands, and shored "
     "on ἕρματα μακρά — Il. 1.485–86; to launch, the props come out — 2.154. "
     "Sterns landward — 14.32. The props draw from 2× up"),
    ("THE HUTS", "fir timber and cut reed — δοῦρ’ ἐλάτης κέρσαντες, λαχνήεντ’ ὄροφον "
     "λειμωνόθεν ἀμήσαντες, Il. 24.450–51"),
)
# Plate A looks inland: the fleet is behind the camera. Same three headings
# so the key's shape holds; the gloss points at the companion plate.
PLATE_A_CAMP_KEY = (
    ("THE SHIPS", "lie behind the viewer on the Aegean shore, on the companion plate"),
    ("ON PROPS", "with the ships, behind the viewer, on the companion plate"),
    ("THE HUTS", "with the ships, behind the viewer, on the companion plate"),
)
PLATE_A_MARKS = (
    "Marks: the wall and its ditch one line each at the camp’s inland edge "
    "(Il. 7.436–441; 14.30–36), where they fall in this frame. The ships and "
    "huts lie behind the viewer on the Aegean shore, on the companion plate."
)
MARGIN_DROPPED = []           # names furniture() dropped on plate B for space
# ── VEGETATION, and the four things on this sheet that grow. Each carries
# the line of the poem that puts it there in the same breath as its mark,
# which is the ground-cover key's own rule applied to the layer that was
# missing from it.
VEG_KEY = (
    ("THE OAK", "φηγός — Il. 6.237 = 9.354 = 11.170, at the Scaean Gate"),
    ("THE WILD FIG", "ἐρινεός — Il. 22.145, ἠνεμόεντα, “windswept”"),
    ("RIVERBANK THICKET", "elm, willow, tamarisk over lotus, rush, galingale "
     "— Il. 21.350–52, growing ἅλις, “in abundance”, which is why it is drawn "
     "as thick as it is; one canopy here, its clumps when you come closer"),
    ("IDA’S TIMBER", "δρῦς ὑψίκομοι, ἐλάτη — Il. 23.114–20; 14.287 — coloured "
     "as a wooded mass, darker in the folds of its own sampled skyline; no "
     "tree drawn on it, no treeline claimed"),
    ("RIDGE SCRUB", "no line of the poem — the regional default above, now "
     "given a mark as well as a tint. Its DENSITY follows the ground’s "
     "curvature, slope and aspect: a drawing rule, not a survey"),
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
VEG_ROW = 12.5           # leading for the key's own small face. It was 14
                         # for four vegetation rows; Ida's timber is a fifth,
                         # and the margin is 300 px and FIXED -- it is the
                         # crop, and the crop is not this lane's to move -- so
                         # the row is paid for out of the leading rather than
                         # out of the sheet.
NOTE_ROW = 11.5          # and the same again for THE CAMP's two rows. The
                         # disclosure block is five lines of a 10 px face, so
                         # a 12.5 px step was a display leading on running
                         # text; 11.5 is still 1.15 em and it buys the rows.
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
               f'text-anchor="middle">{esc(PLATE_TITLE)}</text>')
    out.append(f'<text class="pp-l-note" x="{W / 2}" y="{m + 64}" '
               f'text-anchor="middle">{esc(PLATE_SUBTITLE)}</text>')

    bx = 62.0                      # the margin's own left edge
    rx = W - 62.0                  # and its right
    sx0 = 1300.0                   # where the scale column starts
    y0 = PIC_BOT + 16.0            # first baseline in the margin. It was 38,
                                   # which put 54 px of white between the
                                   # neatline and the first word: the most
                                   # expensive whitespace on the sheet, and
                                   # what THE CAMP's rows are paid for with.

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

    kw, kh, row, col = 30.0, 16.0, 32.0, 600.0
    ky0 = y0 + 22.0
    camp_key = list(PLATE_A_CAMP_KEY if PLATE_FAMILY == "A" else CAMP_KEY)
    veg_key = list(VEG_KEY)
    drawn_marks = PLATE_A_MARKS if PLATE_FAMILY == "A" else DRAWN_MARKS
    dropped = []
    gut = 20.0
    ncol = 5
    colw = ((rx - bx) - gut * (ncol - 1)) / ncol
    note_cols_trial = (
        ("NOT DRAWN", COVER_KEY_UNDRAWN),
        ("THE MARKS", drawn_marks),
        ("THE DRAWING", disclosure() + " " + sun_disclosure()
         + " Height is in the geometry and the light"
         + {"all": ", and in the contour hairlines.",
            "index": ", and in the index contours at 10, 30, 110 and 600 m.",
            "none": " alone; no contours are drawn."}[CONTOURS]),
        ("MEASURED, AND CONJECTURAL",
         "Measured: terrain, coastlines, rivers, Hisarlık, Callicolone, Sigeion, "
         "Rhoiteion. Conjectural: the ships, the huts, the wall and ditch, and every "
         "waypoint of the poem — each placed by a stated rule, never at an invented "
         "coordinate. The ridges are this sheet's own DEM outlines, the wet delta its "
         "10–15 m slope-under-1.2% mask, the dry fan what the plain sector has left."),
        ("THE TWO WATERS",
         "The bay is the reconstructed Late Bronze Age embayment (Kraft, Kayan and Erol "
         "1980; Kayan): a wash over the ground it is draped on, inside a hairline, "
         "against the modern coastline's opaque fill and heavier survey line — they "
         "differ in weight because they differ in kind. Where the two shores leave "
         "ground stranded between them below that 10 m contour, the wash closes the "
         "gap by the reconstruction's own rule. DRAFT."),
    )
    nline = max(len(wrap(b, colw)) for _, b in note_cols_trial)
    ty_trial = H - NEAT_M - (nline - 1) * NOTE_ROW - 13.0
    sub_trial = ky0 + 2 * row + 10.0
    camp_y_trial = sub_trial + 10.0 + (len(WATER_KEY) - 1) * 22.0 + kh + 14.0
    key_bot_trial = max(sub_trial + 18.0 + len(veg_key) * VEG_ROW,
                        camp_y_trial + 12.0 + (len(camp_key) - 1) * NOTE_ROW)
    if PLATE_FAMILY == "B" and ty_trial < key_bot_trial + 16.0:
        plain_veg = {"THE OAK", "THE WILD FIG", "RIVERBANK THICKET", "IDA'S TIMBER"}
        dropped = [n for n, _ in veg_key if n in plain_veg]
        veg_key = [(n, g) for n, g in veg_key if n not in plain_veg]
        key_bot_trial = max(sub_trial + 18.0 + len(veg_key) * VEG_ROW,
                            camp_y_trial + 12.0 + (len(camp_key) - 1) * NOTE_ROW)
        if ty_trial < key_bot_trial + 16.0:
            dropped.append("NOT DRAWN")
            note_cols_trial = tuple(c for c in note_cols_trial if c[0] != "NOT DRAWN")
            ncol = len(note_cols_trial)
            colw = ((rx - bx) - gut * (ncol - 1)) / ncol
    globals()["MARGIN_DROPPED"] = dropped
    if dropped:
        print("  ! plate B margin dropped: " + ", ".join(dropped))
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
    # ── the two sub-blocks the legend rewrite had dropped: what GROWS, and
    # WHICH WATER IS WHICH. They sit under their own columns at a smaller
    # step than the swatch rows, because each is one line and not two.
    sub = ky0 + 2 * row + 10.0
    out.append(f'<text class="pp-l-region" x="{n1(bx)}" y="{n1(sub)}">'
               f'VEGETATION</text>')
    out.append(f'<text class="pp-l-note" x="{n1(bx + 196)}" y="{n1(sub)}" '
               f'fill-opacity="0.85">every plant traces to a line of the poem '
               f'or to a class above</text>')
    for i, (name, gloss) in enumerate(veg_key):
        yy = sub + 18.0 + i * VEG_ROW
        out.append(f'<text class="pp-l-note" x="{n1(bx)}" y="{n1(yy)}" '
                   f'letter-spacing="0.9">{esc(name)}</text>')
        out.append(f'<text class="pp-l-note" x="{n1(bx + 168)}" y="{n1(yy)}" '
                   f'fill-opacity="0.85">{esc(gloss)}</text>')

    out.append(f'<text class="pp-l-region" x="{n1(sx0)}" y="{n1(sub)}">'
               f'WATER</text>')
    out.append(f'<text class="pp-l-note" x="{n1(sx0 + 112)}" y="{n1(sub)}" '
               f'fill-opacity="0.85">two bodies, two kinds of claim</text>')
    for i, (cls, name, gloss) in enumerate(WATER_KEY):
        sy_ = sub + 10.0 + i * 22.0
        # THE SWATCH IS DRAWN THE WAY THE PLATE DRAWS IT, wash and all, so the
        # key cannot promise a water the sheet never prints: the survey is
        # opaque on page, the reconstruction is its wash over the GROUND it is
        # draped on, which is what a reader sees on the sheet.
        out.append(f'<rect class="pp-key-sw" x="{n1(sx0)}" y="{n1(sy_)}" '
                   f'width="{n1(kw)}" height="{n1(kh)}" fill="var('
                   + ('--pp-cover-open' if cls == "lagoon" else '--scene-map-sea')
                   + ')"/>')
        if cls == "lagoon":
            out.append(f'<rect x="{n1(sx0)}" y="{n1(sy_)}" width="{n1(kw)}" '
                       f'height="{n1(kh)}" fill="var(--plate-lagoon)" '
                       f'fill-opacity="0.87"/>')
        out.append(f'<text class="pp-l-note" x="{n1(sx0 + kw + 9)}" '
                   f'y="{n1(sy_ + 11)}" letter-spacing="0.9">{esc(name)}</text>')
        out.append(f'<text class="pp-l-note" x="{n1(sx0 + kw + 268)}" '
                   f'y="{n1(sy_ + 11)}" fill-opacity="0.85">{esc(gloss)}</text>')

    # ── THE CAMP, under the water it is drawn up beside. The plate is named
    # for the ships and until now the key said nothing about what they are
    # made of; the hulls were one near-black token and the huts wore the
    # citadel's masonry. Same rule as VEGETATION and GROUND COVER: the mark
    # carries the line that puts it there, in the same breath as the mark.
    # THE CAMP has to clear WATER's second SWATCH, not its baseline: the
    # swatch runs 16 px below the row's own top, and a 15.5 px display face
    # reaches ~11 px above its baseline. Tightening this to 53 put the
    # heading straight through THE BAY OF TROY's swatch — caught on the
    # render, which is the only place it shows.
    camp_y = sub + 10.0 + (len(WATER_KEY) - 1) * 22.0 + kh + 14.0
    out.append(f'<text class="pp-l-region" x="{n1(sx0)}" y="{n1(camp_y)}">'
               f'THE CAMP</text>')
    if PLATE_FAMILY == "A":
        camp_gloss = ("the ships lie behind the viewer on the Aegean shore, "
                      "on the companion plate")
    else:
        camp_gloss = (
            "four materials, and the poem names all "
            "four; at 1× the hulls are fewer than the beach holds and "
            f"×{FLEET_T1_LEN_K:g} oversize, length and beam alike — seen "
            "broadside, she reads near true size. True from 2× up")
    out.append(f'<text class="pp-l-note" x="{n1(sx0 + 148)}" y="{n1(camp_y)}" '
               f'fill-opacity="0.85">{esc(camp_gloss)}</text>')
    for i, (name, gloss) in enumerate(camp_key):
        # NOTE_ROW, not VEG_ROW: these are note rows with no swatch beside
        # them, which is what NOTE_ROW was cut for in the first place, and
        # ON PROPS is a third row that has to come out of the leading. The
        # margin is 300 px and FIXED — it is the crop, and the crop is not
        # this lane's to move.
        yy = camp_y + 12.0 + i * NOTE_ROW
        out.append(f'<text class="pp-l-note" x="{n1(sx0)}" y="{n1(yy)}" '
                   f'letter-spacing="0.9">{esc(name)}</text>')
        out.append(f'<text class="pp-l-note" x="{n1(sx0 + 148)}" y="{n1(yy)}" '
                   f'fill-opacity="0.85">{esc(gloss)}</text>')

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

    # ── the notes, set to a measure and in columns (2026-08-15) ──────────
    # NOTHING HERE WAS CUT. Every sentence below is a claim a test pins --
    # the citations, the measured/conjectural split, the
    # never-an-invented-coordinate rule, the repair of the drowned gap, how
    # the reconstruction is drawn, DRAFT -- and the standing warning is the
    # right one: a gloss cut thoughtlessly makes the plate assert silently.
    # What changed is the TYPESETTING (see wrap()): five 380-character lines
    # running the full width became five columns at a ~90-character measure,
    # each under its own heading. The block goes from a slab with no entry
    # point to a colophon with five, and it gets SHORTER, because a wrapped
    # column packs the same text into a quarter of the width.
    #
    # THE BLOCK BREAK IS NOW BIGGER THAN THE LINE STEP, which is what a block
    # break is for and what the old 8.0 was not: the leading inside these
    # blocks is NOTE_ROW's 11.5, so 8.0 separated two blocks by LESS than it
    # separated two lines of one, and the notes read as a sixth row of THE
    # CAMP. (The comment that set it claimed "8.0 still is" bigger. It is not,
    # and the arithmetic was never done.)
    note_cols = note_cols_trial
    # THE BLOCK IS ANCHORED TO THE FOOT OF THE SHEET, NOT TO THE KEY ABOVE
    # IT, and that is what stops this defect coming back. Set from the top,
    # the notes ran off the bottom edge whenever a row was added above them:
    # the shipped sheet had its last baseline at y=1341 of 1350 — 9 px of air
    # under a 10 px face with descenders, where the neatline holds 16. Set
    # from the BOTTOM, the last line lands on the neatline's own inset by
    # construction, and it is the SPACE ABOVE the block that runs short
    # instead — which shows as a collision on the render rather than as ink
    # printing off the sheet.
    ncol = len(note_cols)
    colw = ((rx - bx) - gut * (ncol - 1)) / ncol
    nline = max(len(wrap(b, colw)) for _, b in note_cols)
    ty = H - NEAT_M - (nline - 1) * NOTE_ROW - 13.0
    key_bot = max(sub + 18.0 + len(veg_key) * VEG_ROW,
                  camp_y + 12.0 + (len(camp_key) - 1) * NOTE_ROW)
    if ty < key_bot + 16.0:
        print(f"  ! margin: the notes want y={ty:.0f} and the key runs to "
              f"{key_bot:.0f} — {key_bot + 16.0 - ty:.0f} px short")
    out.append(f'<path class="pp-neat-i" d="M{n1(bx)} {n1(ty - 10)}'
               f'H{n1(rx)}" stroke-opacity="0.5"/>')
    for i, (head, body) in enumerate(note_cols):
        cx = bx + i * (colw + gut)
        out.append(f'<text class="pp-l-note pp-colophon-h" x="{n1(cx)}" '
                   f'y="{n1(ty)}" letter-spacing="0.9">{esc(head)}</text>')
        for j, line in enumerate(wrap(body, colw)):
            out.append(f'<text class="pp-l-note pp-colophon" x="{n1(cx)}" '
                       f'y="{n1(ty + 13.0 + j * NOTE_ROW)}">{esc(line)}</text>')
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
    # vegetation goes down after the water and the rivers it grows beside,
    # and before the fleet, which is nearer than any of it
    body.append(P.vegetation_svg())

    wps = P.waypoints()
    (ships, ships_t1, huts, wall_svg, ditch_svg, ship_px,
     obj_sh, obj_sh_t1, hut_sh) = P.camp()

    # wall and ditch, then huts, then ships: inland to seaward is also far to
    # near in this camera, so painter order is depth order.
    body.append(f'<g class="tm2">{wall_svg}{ditch_svg}</g>')
    # the camp's own shadows go down on the beach BEFORE what throws them: a
    # true-length shadow under every hull and every hut is most of what makes
    # the camp read as objects standing on ground rather than marks on paper.
    # THE HUTS' SHADOWS ARE ON AT EVERY TIER, because the huts are. They were
    # in the tier-2 group with the hulls', so at 1x the whole camp behind the
    # fleet floated — and it floated hardest after the huts stopped being
    # near-black boxes and became pale timber and straw on pale ground.
    body.append('<g>' + "".join(hut_sh) + "</g>")
    body.append('<g class="tm2">' + "".join(obj_sh) + "</g>")
    body.append('<g class="t1-only">' + "".join(obj_sh_t1) + "</g>")
    body.append('<g>' + "".join(h for h in huts if h) + "</g>")
    body.append('<g class="tm2">' + "".join(s for s in ships if s) + "</g>")
    body.append('<g class="t1-only">' + "".join(s for s in ships_t1 if s) + "</g>")

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
            elif w["id"] == "fig-tree":
                # THE POEM'S TWO NAMED TREES ARE DRAWN AS TREES. Both were
                # open circles -- the same ring the lookout and the springs
                # get -- which is the right mark for a place and the wrong one
                # for a thing that stands up out of the ground and has a name.
                # ἐρινεὸν ἠνεμόεντα (22.145), the WINDSWEPT fig: the epithet
                # says it stands exposed, so the crown leans, which is the one
                # thing about its appearance the poem actually gives us.
                marks.append(f'<g class="{tcls(tier)}">'
                             + tree(cam, terr, lat, lon, FIG_H, FIG_R,
                                    seed=71, lean=0.30) + '</g>')
            else:
                marks.append(f'<g class="{tcls(tier)}"><circle class="pp-mark" cx="{n1(x)}" '
                             f'cy="{n1(y)}" r="{n1(r)}"/></g>')
            if w["id"] == "scaean-gate":
                # THE GATE KEEPS ITS RING AND THE OAK STANDS BESIDE IT. They
                # are one formulaic pair -- Σκαιάς τε πύλας καὶ φηγόν, 6.237 =
                # 9.354 = 11.170 -- and the label has always named both, but
                # one ring could only ever draw one of them. The oak is set
                # 45 m out along the road, which is a drawing convention and
                # not a position: what the poem fixes is that they are
                # adjacent (9.354 measures Hector's furthest sally as "only as
                # far as the Scaean gates and the oak").
                olat, olon = off_road(w["at"], pp.TROY, -45.0)
                marks.append(f'<g class="{tcls(tier)}">'
                             + tree(cam, terr, olat, olon, OAK_H, OAK_R,
                                    seed=13) + '</g>')

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

    # ── tier 1 — what a reader needs in order to know where they are ──────
    # THE BATTLEFIELD WAS IN THE LEGEND AND NOT ON THE GROUND. The key has
    # always said "dry delta fan -- the battlefield (Kayan 2002)", so the sheet
    # knew the one thing about that surface that matters to a reader of the
    # Iliad and said it in a swatch caption. It is lettered on the fan itself
    # now, in the region manner, and the register is Kayan's: he makes the
    # correlation in his own voice ("Characteristics of the surface recall
    # Homer's descriptions of the battlefield: a sand-covered and dusty plain
    # ... there is no need to look for a battlefield in the distance", Kayan
    # 2002, 1003), which is why the key entry names him rather than a line of
    # the poem. It is not the poem's own name for the ground.
    # PLAIN-SIDE LABEL, PLATE A ONLY. The dry fan is the Scamandrian plain's
    # own ground -- beyond the ridge from plate B's camera (ruling 4: Ilios,
    # and everything on its side of the crest, is not visible from the
    # camp). Plate B can still show a sliver of this cover class at the
    # extreme edge of a wide-angle mesh without the ridge fully occluding
    # it; the label naming it "the battlefield" belongs with plate A's view
    # of the plain, never with B's shore.
    fanc = P.cover_centre(COVER_FAN, 2500.0, 5000.0) if PLATE_FAMILY == "A" else None
    if fanc:
        # nudged clear of the bay's own hairline, which the median's left end
        # was sitting on: region lettering may cross ground, never a drawn line
        L.append(f'<g><text class="plate-label pp-l-region" '
                 f'x="{n1(fanc[0] + 40.0)}" y="{n1(fanc[1])}" '
                 f'text-anchor="middle">THE BATTLEFIELD</text></g>')
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

    # THE NAMED GEOGRAPHY OF THE PICTURE, all of it measured, all of it
    # already drawn, and until now all of it waiting for a 2x zoom. Tier 1
    # carries what ORIENTS: the two rivers, the two headlands the camp's own
    # ends are named against ("Ajax's ships, the end toward Rhoiteion" is a
    # tier-3 label anchored on a headland the overview did not name), the
    # city, the bay, the mountain, the fleet, and the ground they fought over.
    # Tier 2 keeps the poem's fine waypoints and everything conjectural in
    # position -- the ford, Callicolone, the Achaean wall, the throsmos -- so
    # the split is now "what is here" against "what happened here".
    put("simoeis", 8, -8, "pp-l-water", 1)
    put("rhoiteion", 0, -14, "pp-l-region", 1, "middle")
    put("sigeion", 0, -14, "pp-l-region", 1, "middle")

    # tier 2
    put("ford-of-the-scamander", 10, -10, "pp-l-site", 2, text="the ford of the Scamander")
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
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size={w},{h}", f"--screenshot={png_path}", svg_path],
                       check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"  ! chrome failed for {png_path}: {e}")
        return False
    return True


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
    def add_subject(pid, name, greek, cite, rule, at, scr, show_tiers):
        if not at:
            return
        scr = scr or [W / 2.0, PIC_BOT * 0.6, 2000.0]
        x, y, d = scr[0], scr[1], scr[2]
        chars = max(len(name), 12)
        lw = chars * 7.2
        x0 = min(x - 40, x - lw * 0.5) - 60
        x1 = max(x + 40, x + lw * 0.5) + 60
        y0 = min(y - 46, y - 24) - 40
        y1 = max(y + 46, y + 16) + 40
        min_w, min_h = 1150.0, 647.0
        bw, bh = max(x1 - x0, min_w), max(y1 - y0, min_h)
        zoom = min(W / bw, PIC_BOT / bh)
        zoom = max(1.6, min(4.0, zoom))
        rows.append({
            "id": pid,
            "name": name,
            "greek": greek,
            "tier": 1,
            "positionBasis": "conjectural",
            "citation": cite,
            "tradition": None,
            "rule": rule,
            "at": [round(at[0], 5), round(at[1], 5)],
            "frame": {"x": x, "y": y, "depthM": d},
            "camera": {"cx": round((x0 + x1) / 2, 1),
                       "cy": round((y0 + y1) / 2, 1),
                       "zoom": round(zoom, 2)},
            "showTiers": show_tiers,
        })

    add_subject(
        "ships", "the ships", "νῆες",
        "Il. 14.30-36; 8.222-26",
        "Fleet centroid on the Aegean (outer) flank of the Sigeum ridge.",
        plate_stats.get("fleet_centroid"),
        plate_stats.get("fleet_centroid_screen"),
        [1, 2])
    add_subject(
        "huts", "the huts", "κλισίαι",
        "Il. 24.450-51",
        "Hut centroid on the Aegean (outer) flank, inland of the sterns.",
        plate_stats.get("hut_centroid"),
        plate_stats.get("hut_centroid_screen"),
        [1])
    if PLATE_FAMILY == "A":
        rows = [r for r in rows if r["id"] not in ("ships", "huts")]
    elif PLATE_FAMILY == "B":
        keep = {"ships", "achaean-wall", "sigeion", "bay-of-troy", "huts"}
        rows = [r for r in rows if r["id"] in keep]
    return {
        "id": ("panorama-bay-ilios" if PLATE_FAMILY == "A"
               else "panorama-ships-aegean"),
        "title": ("The Bay and Ilios" if PLATE_FAMILY == "A"
                  else "The Ships on the Aegean Shore"),
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


def _parse_latlon(s):
    parts = s.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected LAT,LON")
    return (float(parts[0].strip()), float(parts[1].strip()))


def output_stem(plate, kind, tag=""):
    return f"stage3-{plate}-{kind}{tag}"


def _camp_zone_polygon():
    path = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")
    with open(path) as f:
        for layer in json.load(f)["layers"]:
            if layer["id"] == "achaean-camp-zone":
                return layer["polygon"]
    raise KeyError("achaean-camp-zone")


_PRESETS = None


def plate_presets():
    """Named cameras, computed from the camp zone.

    B WAS SPECIFIED WITH setback=0, WHICH IS A BUG, NOT A CHOICE. Camera's
    near-pitch is atan2(alt - view_z, setback): at setback 0 that is
    atan2(alt, 0) = 90 degrees, straight down, which is why the first B1/B2
    rendered nothing in frame (0 hulls). A camera needs BOTH a viewpoint (the
    near-field aim point the pitch is measured to) and a nonzero setback (how
    far behind it the camera sits) — see Camera.__init__.

    THE SURVIVING B (2026-09-02 correction round) points down the beach, not
    across it. Two candidates that pointed roughly perpendicular to the shore
    — straight in from the sea at the camp's own latitude — put the fleet at
    the same depth as the old single-plate calibration (~2.5 km) but with
    Ilios inside the 72-degree cone (unwanted: ruling 4 says Ilios is not
    visible from the camp) or, at a shallower pitch, spread the whole 9 km
    frontage across the frame so thin the hulls read as dots. Pointed instead
    from off the CENTRE station toward the SOUTH station — down the shore's
    own line — Ilios's bearing sits ~75-90 degrees off the camera's heading,
    well outside the half-cone, by AZIMUTH rather than by hoping the ridge
    occludes it at whatever altitude was last tried; and because the camera
    sits abreast of the fleet's own middle rather than off one end looking
    down the whole length, the fleet centroid lands at ~2.8 km, close to the
    old calibration, with the beach crossing the frame on a diagonal.

    THIRD ROUND (2026-09-02, composition fix): the 2,000 m/alt 300/pitch
    7.3-degree camera above rendered two-thirds sky and sea with the land a
    thin strip and the fleet a scatter of specks -- not a framing bug, a
    camera too far and too shallow for a picture that wants the ridge crest
    in the TOP QUARTER and the waterline near the BOTTOM. A scratch solver
    (sweeping distance off the beach, altitude, setback, heading and hfov,
    scoring the projected y of a real ridge-crest sample against the camp
    zone's own DEM, the waterline at the fleet's central station, the
    fleet's frame-width span and Ilios's azimuth) landed on 900 m/alt
    280/setback 750/hfov 56/heading 160 -- crest and waterline both fell
    where asked, but a real Plate.camp() render of it showed the true fleet
    crammed into the right third of the frame (screen x 1690-2472 of 2400).

    FOURTH ROUND, same day, same solver corrected: the third round's fleet
    coverage was measured against aegean_fleet()'s RAW berth list, which
    spans the whole ~9.3 km camp axis with no elevation test. The real
    berths() closure inside camp() also drops any station whose front berth
    sits above 16 m, and that turns out to fragment the beach hard -- the
    only long CONTIGUOUS run of qualifying frontage is ~1.1 km near the
    SOUTH end of the axis (camp-axis metres -4537 to -3419; everything else
    is scraps under 160 m). ax["centre"], the geometric middle of the whole
    9.3 km zone, is nowhere near that run, which is why the third round's
    camera -- aimed from off the zone's centre -- only ever caught the run's
    near edge. The fourth round re-solves from a new pivot, this run's OWN
    midpoint (camp-axis -3978 m), re-run with the real elevation-filtered
    berth set standing in for the drawn fleet: 900 m off that pivot, alt
    160, setback 500, hfov 52, heading a literal 152 degrees (partway
    between abreast-of-pivot and the run's own south end, the same
    trade-off the earlier rounds made, re-solved at the new station). Crest
    lands at y~308, waterline at y~919 of the 1050 px picture, the fleet
    spanning the FULL frame width edge to edge (confirmed against a real
    camp() call: hull screen x -87 to 2281), 97 true hulls and 100 huts
    drawn, huts on the ridge slope in frame. Pitch ~8.8 degrees. Ilios's
    azimuth clears the half-cone by 65 degrees, far more margin than
    strictly needed -- spent on a narrower hfov (bigger hulls) rather than
    banked."""
    global _PRESETS
    if _PRESETS is not None:
        return _PRESETS
    ax = camp_axis_stations(_camp_zone_polygon())
    # the main run's own midpoint (see the docstring above), NOT the whole
    # zone's geometric centre -- that is where the qualifying beach actually
    # is, camp-axis metres, not degrees.
    fleet_pivot = camp_ll(ax["origin"], -3978.0, 0.0)
    vp_b = ll_along(fleet_pivot, CAMP_SEAWARD_DEG, 900.0)
    b_title = "THE SHIPS ON THE AEGEAN SHORE"
    b_sub = ("the Achaean camp from over the sea, looking east; "
             "Ilios lies beyond the ridge, out of sight")
    a = {
        "viewpoint": (39.9755, 26.1785),
        "heading": 104.0, "hfov": 72.0, "alt": 800.0,
        "setback": 1500.0, "range_near": 420.0,
        "family": "A",
        "title": "THE BAY AND ILIOS",
        "subtitle": ("the plain of Troy from above the Achaean camp, "
                     "looking east-south-east"),
        "draw_fleet": False, "draw_huts": False,
    }
    b = {
        "viewpoint": vp_b,
        "heading": 152.0,
        "hfov": 52.0, "alt": 160.0, "setback": 500.0, "range_near": 150.0,
        "family": "B", "title": b_title, "subtitle": b_sub,
        "draw_fleet": True, "draw_huts": True,
    }
    _PRESETS = {"A": a, "B": b}
    return _PRESETS


def apply_plate_preset(name):
    """Named camera+content preset. Apply before apply_camera_args so
    explicit camera flags still override."""
    p = plate_presets()[name]
    g = globals()
    g["VIEWPOINT"] = tuple(p["viewpoint"])
    g["HEADING_DEG"] = float(p["heading"])
    g["ALT"] = float(p["alt"])
    g["SETBACK"] = float(p["setback"])
    g["RANGE_NEAR"] = float(p["range_near"])
    g["HFOV_DEG"] = float(p["hfov"])
    g["FOCAL"] = (W / 2.0) / math.tan(math.radians(g["HFOV_DEG"]) / 2.0)
    g["PLATE"] = name
    g["PLATE_FAMILY"] = p["family"]
    g["PLATE_TITLE"] = p["title"]
    g["PLATE_SUBTITLE"] = p["subtitle"]
    g["DRAW_FLEET"] = p["draw_fleet"]
    g["DRAW_HUTS"] = p["draw_huts"]


def build_arg_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(REPO, "build", "panorama"))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--plate", choices=("A", "B"), default="A",
                    help="named camera+content preset; "
                         "camera flags override the preset")
    ap.add_argument("--viewpoint", type=_parse_latlon, default=None,
                    metavar="LAT,LON",
                    help="camera look-at, default %.4f,%.4f"
                         % (VIEWPOINT[0], VIEWPOINT[1]))
    ap.add_argument("--heading", type=float, default=None, metavar="DEG",
                    help="compass heading, default %g" % HEADING_DEG)
    ap.add_argument("--alt", type=float, default=None, metavar="M",
                    help="camera height in metres, default %g" % ALT)
    ap.add_argument("--setback", type=float, default=None, metavar="M",
                    help="camera setback behind the viewpoint, default %g" % SETBACK)
    ap.add_argument("--range-near", type=float, default=None, metavar="M",
                    help="near edge of the drawn mesh, default %g" % RANGE_NEAR)
    ap.add_argument("--hfov", type=float, default=None, metavar="DEG",
                    help="horizontal field of view, default %g" % HFOV_DEG)
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
    return ap


def apply_camera_args(args):
    """Module constants Camera, ring_ranges and project_ll read. Apply
    before any of those run."""
    g = globals()
    if args.viewpoint is not None:
        g["VIEWPOINT"] = args.viewpoint
    if args.heading is not None:
        g["HEADING_DEG"] = float(args.heading)
    if args.alt is not None:
        g["ALT"] = float(args.alt)
    if args.setback is not None:
        g["SETBACK"] = float(args.setback)
    if args.range_near is not None:
        g["RANGE_NEAR"] = float(args.range_near)
    if args.hfov is not None:
        g["HFOV_DEG"] = float(args.hfov)
    g["FOCAL"] = (W / 2.0) / math.tan(math.radians(g["HFOV_DEG"]) / 2.0)


def main():
    ap = build_arg_parser()
    args = ap.parse_args()
    apply_plate_preset(args.plate)
    apply_camera_args(args)
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
    print(f"plate {args.plate} family {PLATE_FAMILY} title {PLATE_TITLE!r}")
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

    prom = troy_prominence(terr, cam) if PLATE_FAMILY == "A" else {}
    if prom:
        print("Ilios: " + " ".join(f"{k}={v}" for k, v in prom.items()))
    print(f"camera viewpoint {VIEWPOINT[0]:.4f},{VIEWPOINT[1]:.4f} "
          f"heading {HEADING_DEG:g} alt {ALT:g} setback {SETBACK:g} "
          f"range-near {RANGE_NEAR:g} hfov {HFOV_DEG:g}")
    print(f"pitch {math.degrees(cam.pitch):.2f} deg down; focal {FOCAL:.1f}")
    inner, wps, P = build(terr, cam, plate_json)
    def _xy(lat, lon):
        p = cam.project_ll(lat, lon, built_h(0.0, terr.elev(lat, lon)))
        return (round(p[0], 1), round(p[1], 1)) if p else None
    fc = P.stats.get("fleet_centroid")
    hc = P.stats.get("hut_centroid")
    wall_ll = P.stats.get("wall_at")
    print("screen xy: fleet=%s huts=%s wall=%s ridge=%s troy=%s ida=%s" % (
        _xy(*fc) if fc else None,
        _xy(*hc) if hc else None,
        _xy(*wall_ll) if wall_ll else None,
        _xy(*pp.SIGEION),
        _xy(*pp.TROY),
        _xy(*pp.IDA_SUMMIT)))
    if wall_ll:
        e, n = pp._flat_m(tuple(wall_ll), *VIEWPOINT)
        cam_e = -SETBACK * math.sin(math.radians(HEADING_DEG))
        cam_n = -SETBACK * math.cos(math.radians(HEADING_DEG))
        wr = math.hypot(e - cam_e, n - cam_n)
        print(f"wall range {wr:.0f} m  RANGE_NEAR {RANGE_NEAR:g}  "
              f"{'behind RANGE_NEAR' if wr < RANGE_NEAR else 'in mesh'}")
    if MARGIN_DROPPED:
        print("margin dropped: " + ", ".join(MARGIN_DROPPED))
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
    print(f"hulls {P.stats['hulls']} ({P.stats['hulls_miltos']} vermilion), "
          f"overview rank {P.stats['hulls_t1']}, huts {P.stats['huts']}, "
          f"thicket clumps {P.stats.get('veg_bank', 0)} in "
          f"{P.stats.get('veg_bank_runs', 0)} fringe runs, scrub tufts "
          f"{P.stats.get('veg_scrub', 0)} under "
          f"{P.stats.get('scrub_mass_loops', 0)} merged patches "
          f"(density mean {P.stats.get('scrub_dens_mean', 0):.2f}, "
          f"{100 * P.stats.get('scrub_bare_frac', 0):.0f}% of the ridge bare)")
    nk = P.stats.get("coast_necks", {})
    print("coastline low-pass worst move: " + ", ".join(
        f"{k} {v:g} m ({nk.get(k, 0)} neck cut)"
        for k, v in sorted(P.stats.get("coast_dev_m", {}).items()))
          + f" (source grid 30 m; COAST_SOFT={COAST_SOFT}, "
            f"neck<{COAST_NECK_M:g} m)")

    tgt = camera_targets(wps, dict(P.stats))
    tgt["camera"]["pitchDegDown"] = round(math.degrees(cam.pitch), 2)
    tgt["stats"]["ilios"] = prom
    tp = os.path.join(args.out_dir, output_stem(args.plate, "camera-targets", tag) + ".json")
    with open(tp, "w") as f:
        json.dump(tgt, f, ensure_ascii=False, indent=2)
    print(f"camera targets -> {tp} ({len(tgt['targets'])} rows)")

    if args.variant:
        # the comparison set: full plate both themes, the 8x Ilios crop both
        # themes, the camp zoom in light. Nothing else -- these renders exist
        # to be put side by side, not to ship.
        by_id = {t["id"]: t for t in tgt["targets"]}
        ic = by_id["ilios"]["camera"] if "ilios" in by_id else None
        for theme in ("light", "dark"):
            sfx = "" if theme == "light" else "-dark"
            svg = os.path.join(args.out_dir, output_stem(args.plate, "full", tag) + f"{sfx}.svg")
            w, h = emit(theme, inner, 0, 0, W, H, 1.0, svg, tier=1)
            shoot(svg, os.path.join(args.out_dir, output_stem(args.plate, "full", tag) + f"{sfx}.png"), w, h)
            print(f"[{theme}] full 1x {os.path.getsize(svg) / 1024:.0f} KB")
            if ic is None:
                continue
            cw, ch = W / 8.0, H / 8.0
            s2 = os.path.join(args.out_dir, output_stem(args.plate, "zoom8-troy", tag) + f"{sfx}.svg")
            w2, h2 = emit(theme, inner, ic["cx"] - cw / 2, ic["cy"] - ch / 2,
                          cw, ch, 8.0, s2, tier=3, descale=8.0)
            shoot(s2, os.path.join(args.out_dir,
                                   output_stem(args.plate, "zoom8-troy", tag) + f"{sfx}.png"), w2, h2)
        cw, ch = W / 4.0, H / 4.0
        s3 = os.path.join(args.out_dir, output_stem(args.plate, "zoom-camp", tag) + ".svg")
        w3, h3 = emit("light", inner, 1250.0 - cw / 2, 665.0 - ch / 2, cw, ch,
                      4.0, s3, tier=3, descale=4.0)
        shoot(s3, os.path.join(args.out_dir, output_stem(args.plate, "zoom-camp", tag) + ".png"), w3, h3)
        print("variant set done")
        return

    themes = ("light",) if args.quick else ("light", "dark")
    for theme in themes:
        sfx = "" if theme == "light" else "-dark"
        svg = os.path.join(args.out_dir, output_stem(args.plate, "full", tag) + f"{sfx}.svg")
        w, h = emit(theme, inner, 0, 0, W, H, 1.0, svg, tier=1)
        shoot(svg, os.path.join(args.out_dir, output_stem(args.plate, "full", tag) + f"{sfx}.png"), w, h)
        sz = os.path.getsize(svg)
        print(f"[{theme}] full 1x  {sz / 1024:.0f} KB ({sz} bytes) -> {w}x{h}")
        if args.quick:
            break
        # The 4x crops are taken from the CAMERA-TARGET TABLE where the table
        # has a row for them, so the renders John looks at are the frames the
        # Chart Room would actually serve.
        by_id = {t["id"]: t for t in tgt["targets"]}
        cams = {"camp": (1250.0, 665.0)}
        if "ilios" in by_id:
            cams["troy"] = (by_id["ilios"]["camera"]["cx"], by_id["ilios"]["camera"]["cy"])
        for name, (cx, cy) in cams.items():
            cw, ch = W / 4.0, H / 4.0
            s2 = os.path.join(args.out_dir, output_stem(args.plate, f"zoom-{name}", tag) + f"{sfx}.svg")
            w2, h2 = emit(theme, inner, cx - cw / 2, cy - ch / 2, cw, ch, 4.0, s2,
                          tier=3, descale=4.0)
            shoot(s2, os.path.join(args.out_dir, output_stem(args.plate, f"zoom-{name}", tag) + f"{sfx}.png"), w2, h2)
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
        s2t = os.path.join(args.out_dir, output_stem(args.plate, "full-tier2", tag) + f"{sfx}.svg")
        w2t, h2t = emit(theme, inner, 0, 0, W, H, 1.0, s2t, tier=2)
        shoot(s2t, os.path.join(args.out_dir, output_stem(args.plate, "full-tier2", tag) + f"{sfx}.png"), w2t, h2t)
        ph = PIC_BOT
        pw = ph * (390.0 / 780.0)
        s3 = os.path.join(args.out_dir, output_stem(args.plate, "mobile-portrait", tag) + f"{sfx}.svg")
        w3, h3 = emit(theme, inner, 1376 - pw / 2, 0, pw, ph, 780.0 / ph, s3,
                      tier=1, descale=780.0 / ph, furn=False,
                      caption=PLATE_TITLE)
        shoot(s3, os.path.join(args.out_dir, output_stem(args.plate, "mobile-portrait", tag) + f"{sfx}.png"), w3, h3)
    print("done")


if __name__ == "__main__":
    main()
