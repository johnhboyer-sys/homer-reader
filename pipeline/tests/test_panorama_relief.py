"""The panorama's vertical-exaggeration curve must never invert.

`scripts/panorama-stage3.py` once computed apparent height as `e * ve(e)` with
a decreasing `ve`. The product of a rising input and a falling multiplier need
not rise, and it did not: apparent height peaked at 183.3 m real and fell away
after, so a 300 m ridge drew shorter than a 100 m hill and about a fifth of the
plain sheet's ground sat inside the inverting band. The fix treats `ve` as a
RATE and integrates it, which cannot invert while the rate stays positive.

These tests hold that line: they assert the legacy form really did invert (so
the bug is documented, not merely gone), and that every shippable curve is
strictly increasing over the plate's whole range, sea level to Mount Ida.
"""
from __future__ import annotations

import importlib.util
import math
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE3 = os.path.join(REPO, "scripts", "panorama-stage3.py")

SHIPPABLE = ("B", "C")          # "A" is the legacy product form, kept only so
                                # the baseline render stays reproducible
IDA_M = 1774.0                  # published Kaz Dagi summit


@pytest.fixture(scope="module")
def s3():
    if not os.path.exists(STAGE3):
        pytest.skip(f"panorama stage 3 script not present at {STAGE3}")
    spec = importlib.util.spec_from_file_location("panorama_stage3", STAGE3)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_legacy_product_form_inverts(s3):
    """The bug, reproduced. Remove this test only with curve A itself."""
    ex = lambda e: s3.exaggerate(e, "A")
    assert ex(100.0) == pytest.approx(400.0, abs=0.5)
    assert ex(183.0) == pytest.approx(504.2, abs=0.5)
    assert ex(267.0) == pytest.approx(399.2, abs=0.5)
    assert ex(300.0) == pytest.approx(300.0, abs=0.5)
    # a 300 m ridge drawn shorter than a 100 m hill: the defect itself
    assert ex(300.0) < ex(100.0)


@pytest.mark.parametrize("curve", SHIPPABLE)
def test_apparent_height_is_strictly_increasing(s3, curve):
    """Dense sweep of the plate's whole range at 0.25 m, sea level to Ida."""
    step = 0.25
    prev_e = 0.0
    prev_a = s3.exaggerate(prev_e, curve)
    n = int(round((IDA_M + 50.0) / step))
    for i in range(1, n + 1):
        e = i * step
        a = s3.exaggerate(e, curve)
        assert a > prev_a, (
            f"curve {curve} inverts: {prev_e:.2f} m -> {prev_a:.4f} apparent, "
            f"{e:.2f} m -> {a:.4f}"
        )
        prev_e, prev_a = e, a


@pytest.mark.parametrize("curve", SHIPPABLE)
def test_rate_is_positive_everywhere(s3, curve):
    """Monotonicity of the integral follows from a positive rate."""
    for i in range(0, int(IDA_M) + 51):
        assert s3.ve(float(i), curve) > 0.0, f"curve {curve} rate <= 0 at {i} m"


@pytest.mark.parametrize("curve", SHIPPABLE)
def test_sea_level_is_the_datum(s3, curve):
    """The sea plane is drawn at a flat 0 and the bay and swamp drape on the
    exaggerated ground; if the curve moved 0, their junction would step."""
    assert s3.exaggerate(0.0, curve) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("curve", SHIPPABLE)
def test_shoreline_still_reads_at_about_four_times(s3, curve):
    """The exaggeration exists so the beach and the plain read at all. The
    near ground is where that is spent, and it must not be spent elsewhere."""
    assert s3.exaggerate(10.0, curve) == pytest.approx(40.0, rel=0.06)
    assert s3.ve(0.0, curve) == pytest.approx(4.0, abs=1e-9)


def test_curve_c_keeps_ida_at_its_true_height(s3):
    assert s3.exaggerate(IDA_M, "C") == pytest.approx(IDA_M, abs=0.5)


@pytest.mark.parametrize("curve", SHIPPABLE)
def test_built_heights_stay_true(s3, curve):
    """A 6.4 m stem-post is 6.4 m on top of whatever the ground does — the
    defect this plate already fixed once (a 4x stem-post reads as a mast)."""
    saved = s3.CURVE
    try:
        s3.CURVE = curve
        for ground in (0.0, 5.0, 12.5, 40.0, 100.0, 183.0, 300.0, 661.0):
            for h in (0.0, 2.4, 6.4, 9.0):
                assert s3.built_h(h, ground) - s3.exaggerate(ground) == \
                    pytest.approx(h, abs=1e-9)
    finally:
        s3.CURVE = saved


def test_shipped_default_is_not_the_legacy_curve(s3):
    assert s3.CURVE in SHIPPABLE


# ── the mesh must resolve the ground, not just the screen ─────────────────
# Ilios drew at plain level because the mesh's RINGS, stepped to a screen
# separation on FLAT ground, sat 332 m apart at Troy's 7.0 km. Hisarlik's
# bluff climbs 24 m over about 250 m, so the citadel fell inside one cell and
# the mesh drew a ramp: 29.7 m instead of the 34.6 m the DEM carries, one
# hypsometric band low. The blur was never the cause -- prep-terrain-contours'
# 10+2 box passes cost the mound 1.4 m of 25.


def _flat_y_of(cam_alt=800.0, focal=1651.7, horizon=380.0):
    """A stand-in for the camera's flat-ground projection: screen y falls
    towards a horizon as 1/range, which is the only shape the ring rule
    depends on."""
    return lambda r: horizon + focal * cam_alt / max(r, 1.0)


def test_rings_resolve_the_ground_inside_the_plain_sheet(s3):
    """Inside the plain sheet a ring may not outrun RING_MAX_M -- except
    where the raster floor bites first, which is the stated trade."""
    fy = _flat_y_of()
    rngs = s3.ring_ranges(fy)
    for a, b in zip(rngs, rngs[1:]):
        if a >= s3.RING_DETAIL_FAR:
            continue
        if fy(a) - fy(a + s3.RING_MAX_M) < s3.RING_MIN_PX:
            continue                       # a capped ring would be sub-pixel
        assert b - a <= s3.RING_MAX_M + 1e-6, (
            f"ring spacing {b - a:.1f} m at {a:.0f} m outruns the DEM")


def test_the_citadel_gets_more_than_one_ring(s3):
    """The bug in one number. Hisarlik's bluff is about 250 m of ground at
    7 km; a single cell across it is what drew Ilios at plain level."""
    rngs = s3.ring_ranges(_flat_y_of())
    near = [b - a for a, b in zip(rngs, rngs[1:]) if 6000.0 <= a <= 8000.0]
    assert max(near) <= 125.0, (
        f"worst ring spacing at Troy's range is {max(near):.0f} m")


def test_the_screen_rule_alone_would_not_have(s3):
    """The defect, reproduced: with RING_MAX_M off, the flat-ground screen
    rule puts rings hundreds of metres apart across the whole plain."""
    saved = s3.RING_DETAIL_FAR
    try:
        s3.RING_DETAIL_FAR = 0.0
        rngs = s3.ring_ranges(_flat_y_of())
        worst = max(b - a for a, b in zip(rngs, rngs[1:])
                    if a < 8000.0)
        assert worst > 250.0, (
            "expected the unaided screen rule to under-resolve the plain; "
            f"worst spacing inside 8 km was only {worst:.0f} m")
    finally:
        s3.RING_DETAIL_FAR = saved


def test_rings_are_increasing_and_span_the_plate(s3):
    rngs = s3.ring_ranges(_flat_y_of())
    assert rngs[0] == s3.RANGE_NEAR
    assert rngs[-1] == s3.RANGE_FAR
    assert all(b > a for a, b in zip(rngs, rngs[1:]))


def test_rings_never_close_below_a_raster_pixel(s3):
    fy = _flat_y_of()
    rngs = s3.ring_ranges(fy)
    for a, b in zip(rngs, rngs[1:]):
        if b < s3.RANGE_FAR:
            assert fy(a) - fy(b) >= s3.RING_MIN_PX - 1e-6


# ── back-face cull ────────────────────────────────────────────────────────
# Where the ground falls away behind a crest the mesh quad folds over in
# screen space. It is occluded, and it winds the other way, so the band
# union's nonzero fill CANCELS over the overlap and the page shows through.


def _plate_with(grid, azs, rngs):
    p = object.__new__(_PLATE[0])
    p.grid, p.azs, p.rngs, p.stats = grid, azs, rngs, {}
    return p


_PLATE = [None]


def test_back_facing_cells_are_culled(s3):
    _PLATE[0] = s3.Plate
    # two columns, three rings. Ring 0 -> 1 rises to a crest (front-facing);
    # ring 1 -> 2 falls away behind it, so that quad folds.
    #            (x,        y,    elev, range)
    g = [[(0.0, 500.0, 10.0, 1000.0), (0.0, 460.0, 100.0, 1200.0), (0.0, 480.0, 40.0, 1400.0)],
         [(40.0, 500.0, 10.0, 1000.0), (40.0, 460.0, 100.0, 1200.0), (40.0, 480.0, 40.0, 1400.0)]]
    p = _plate_with(g, [0.0, 1.0], [1000.0, 1200.0, 1400.0])
    p.cull()
    assert (0, 0) in p.visible, "the front face of the crest must be drawn"
    assert (0, 1) not in p.visible, "the folded back face must not be"


# ═══════════════════════════════════════════════════════════════════════════
# curve C is a FAMILY: the near-ground rate is a dial, the floor never is
# ═══════════════════════════════════════════════════════════════════════════
# `ve(0)` was 4.0 and hard-coded. It is now set by set_curve(near, scale),
# which SOLVES the floor so exaggerate(IDA_M) == IDA_M. That constraint puts a
# hard ceiling on the near rate: past it the floor goes non-positive and the
# curve inverts, which is the defect the tests above exist to prevent.


@pytest.fixture
def restore_curve(s3):
    saved = (s3.C_A, s3.C_L)
    yield
    s3.set_curve(*saved)


@pytest.mark.parametrize("near", [4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 11.5])
def test_every_shippable_near_rate_stays_monotonic(s3, restore_curve, near):
    s3.set_curve(near, 150.0)
    prev = s3.exaggerate(0.0, "C")
    e = 0.0
    while e < IDA_M + 50.0:
        e += 0.25
        a = s3.exaggerate(e, "C")
        assert a > prev, f"ve(0)={near} inverts at {e:.2f} m"
        prev = a


@pytest.mark.parametrize("near", [4.0, 6.0, 8.0, 10.0, 11.5])
def test_ida_keeps_its_true_height_at_every_near_rate(s3, restore_curve, near):
    """The whole point of the family: turning the near dial must not move the
    horizon."""
    s3.set_curve(near, 150.0)
    assert s3.exaggerate(IDA_M, "C") == pytest.approx(IDA_M, abs=0.5)
    assert s3.ve(0.0, "C") == pytest.approx(near, abs=1e-9)


def test_the_near_rate_has_a_ceiling_and_the_ceiling_is_enforced(s3, restore_curve):
    """Past the ceiling the solved floor is non-positive, so the rate can go
    to zero or negative and apparent height can stop rising. set_curve must
    refuse rather than emit a curve that inverts."""
    ceil = s3.max_near_rate(150.0)
    assert 11.5 < ceil < 12.5
    s3.set_curve(ceil - 0.05, 150.0)
    assert s3.C_F > 0.0
    with pytest.raises(ValueError):
        s3.set_curve(ceil + 0.5, 150.0)


def test_a_longer_taper_lowers_the_ceiling(s3):
    """Counter-intuitive and worth pinning: a longer decay scale spends more
    of Ida's budget low down, so it permits LESS lift at the shore."""
    assert s3.max_near_rate(100.0) > s3.max_near_rate(150.0) > s3.max_near_rate(250.0)


def test_the_cartouche_cannot_declare_a_rate_it_does_not_draw(s3, restore_curve):
    """The disclosure is generated from the live dials. A plate saying 4x
    while drawing 8x discredits everything else on the sheet."""
    for near in (4.0, 6.0, 8.0):
        s3.set_curve(near, 150.0)
        assert ("%.3g×" % near) in s3.disclosure("C")
        assert ("%.2f×" % s3.C_F) in s3.disclosure("C")


def test_built_heights_stay_true_at_every_near_rate(s3, restore_curve):
    saved = s3.CURVE
    try:
        s3.CURVE = "C"
        for near in (4.0, 6.0, 8.0, 11.0):
            s3.set_curve(near, 150.0)
            for ground in (0.0, 5.0, 12.5, 40.0, 100.0, 300.0, 661.0):
                for h in (0.0, 2.4, 6.4, 9.0):
                    assert s3.built_h(h, ground) - s3.exaggerate(ground) == \
                        pytest.approx(h, abs=1e-9)
    finally:
        s3.CURVE = saved


# ═══════════════════════════════════════════════════════════════════════════
# index contours: a rule across the sheet, never a weight chosen for a place
# ═══════════════════════════════════════════════════════════════════════════
def test_index_contours_are_every_third_level(s3):
    assert sorted(s3.INDEX_LEVELS) == [1, 4, 7, 10]
    assert [s3.LEVELS[k] for k in sorted(s3.INDEX_LEVELS)] == [10, 30, 110, 600]


def test_index_weight_is_heavier_than_the_intermediate(s3):
    assert s3.CONTOUR_INDEX_W > s3.CONTOUR_W > 0.6
    css = s3.contour_css()
    assert ".pp-contour-index{" in css and ".pp-contour{" in css
    assert f"stroke-width:{s3.CONTOUR_INDEX_W:g}" in css


# ═══════════════════════════════════════════════════════════════════════════
# the light: a solved sun, and shadows that are the cull run from it
# ═══════════════════════════════════════════════════════════════════════════
def _solar(lat_deg, dec_deg, H_deg):
    phi, d, H = (math.radians(x) for x in (lat_deg, dec_deg, H_deg))
    alt = math.asin(math.sin(phi) * math.sin(d)
                    + math.cos(phi) * math.cos(d) * math.cos(H))
    ca = ((math.sin(d) - math.sin(alt) * math.sin(phi))
          / (math.cos(alt) * math.cos(phi)))
    A = math.degrees(math.acos(max(-1.0, min(1.0, ca))))
    return math.degrees(alt), (360.0 - A if H_deg > 0 else A)


def test_the_shipped_sun_is_a_real_solar_position(s3):
    """No faked sun. The default must be reachable at 39.9755 N -- here at
    declination +18 (early August), an hour after sunrise."""
    alt, az = _solar(39.9755, 18.0, -90.0)
    assert alt == pytest.approx(s3.LIGHT_ALT, abs=0.6)
    assert az == pytest.approx(s3.LIGHT_AZ, abs=0.6)


def test_the_light_vector_matches_its_bearing_and_altitude(s3):
    for az, alt in ((76.0, 11.5), (228.4, 9.9), (260.2, 11.4)):
        s3.set_light(az, alt)
        lx, ly, lz = s3.LIGHT
        assert math.hypot(math.hypot(lx, ly), lz) == pytest.approx(1.0, abs=1e-12)
        assert math.degrees(math.atan2(lx, ly)) % 360 == pytest.approx(az, abs=1e-9)
        assert math.degrees(math.asin(lz)) == pytest.approx(alt, abs=1e-9)
        # shadows travel the opposite way along the ground
        assert s3.SUN_H[0] == pytest.approx(-lx / math.cos(math.radians(alt)), abs=1e-12)
    s3.set_light(s3.LIGHT_AZ_DEFAULT, s3.LIGHT_ALT_DEFAULT)


def test_shadow_length_is_the_true_height_over_tan_altitude(s3):
    """Built heights are true, so their shadows are true lengths. A 6.4 m
    stem-post at 11.5 deg throws 31.4 m and not whatever looks good."""
    s3.set_light(76.0, 11.5)
    for h in (2.4, 3.2, 6.4, 25.0):
        dx, dy = s3.sun_offset(h)
        assert math.hypot(dx, dy) == pytest.approx(
            h / math.tan(math.radians(11.5)), rel=1e-9)
    assert s3.sun_offset(0.0) == (0.0, 0.0)
    s3.set_light(s3.LIGHT_AZ_DEFAULT, s3.LIGHT_ALT_DEFAULT)


def test_the_shadow_sweep_puts_ground_behind_a_ridge_in_shadow(s3):
    """The cull, run from the sun. A wall of ground must shadow what lies
    down-sun of it and nothing up-sun of it."""
    class _Terr:
        """A 40 m step running across the light, at the origin."""
        def elev(self, lat, lon):
            e = (lon - 26.1785) * (111320.0 * math.cos(math.radians(39.9755)))
            return 40.0 if 0.0 <= e <= 200.0 else 0.0

    saved = s3.CURVE
    try:
        s3.CURVE = "B"                      # 4x flat under 100 m: 40 -> 160
        sf = s3.ShadowField(_Terr(), 270.0, 11.5, step=25.0, reach=2000.0)
    finally:
        s3.CURVE = saved
    # light from due west, so shadows run east. 160 apparent metres at 11.5
    # deg reaches 786 m east of the step's east face.
    assert sf.at(500.0, 0.0) < 0.35, "ground just east of the step must be dark"
    assert sf.at(-500.0, 0.0) > 0.95, "ground west of it -- up-sun -- must be lit"
    assert sf.at(1600.0, 0.0) > 0.95, "beyond the shadow's reach must be lit"


def test_shadow_visibility_is_bounded_and_defaults_lit_outside_the_raster(s3):
    class _Flat:
        def elev(self, lat, lon):
            return 0.0
    sf = s3.ShadowField(_Flat(), 76.0, 11.5, step=200.0, reach=1000.0)
    assert sf.at(0.0, 0.0) == pytest.approx(1.0, abs=1e-9)
    assert sf.at(9e5, 9e5) == 1.0          # off the raster: no claim, full sun
    for row in sf.vis:
        for v in row:
            assert 0.0 <= v <= 1.0


def test_shading_is_a_function_of_slope_and_light_only(s3):
    """No location-dependent effects. Two identical cells at different places
    must take the same tone."""
    s3.set_light(76.0, 11.5)
    P = object.__new__(s3.Plate)
    P.shadow = None
    # a cell tilted the same way at two different positions 5 km apart
    def cell(off_e, off_n):
        P.grid = [[(0, 0, 0.0, 1e3), (0, 0, 10.0, 1e3)],
                  [(0, 0, 0.0, 1e3), (0, 0, 10.0, 1e3)]]
        P.wor = [[(off_e, off_n), (off_e, off_n + 100.0)],
                 [(off_e + 100.0, off_n), (off_e + 100.0, off_n + 100.0)]]
        return P.shade_raw(0, 0)
    assert cell(0.0, 0.0) == pytest.approx(cell(5000.0, -3000.0), abs=1e-12)
    s3.set_light(s3.LIGHT_AZ_DEFAULT, s3.LIGHT_ALT_DEFAULT)


def test_flat_ground_in_full_sun_takes_no_wash(s3):
    """The hypsometric ramp is left to say what it says; only slopes and
    shadows are modelled."""
    s3.set_light(76.0, 11.5)
    P = object.__new__(s3.Plate)
    P.shadow = None
    P.grid = [[(0, 0, 12.0, 1e3), (0, 0, 12.0, 1e3)],
              [(0, 0, 12.0, 1e3), (0, 0, 12.0, 1e3)]]
    P.wor = [[(0.0, 0.0), (0.0, 100.0)], [(100.0, 0.0), (100.0, 100.0)]]
    assert P.shade_raw(0, 0) == pytest.approx(0.0, abs=1e-12)
    s3.set_light(s3.LIGHT_AZ_DEFAULT, s3.LIGHT_ALT_DEFAULT)


def test_the_cartouche_names_the_sun_it_draws(s3):
    line = s3.sun_disclosure()
    assert "%.0f°" % s3.LIGHT_AZ in line
    assert "%.0f°" % s3.LIGHT_ALT in line
    assert s3.SUN_NOTE in line
