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
import re

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
    declination -23.44 (winter solstice), 3.5 h after noon."""
    alt, az = _solar(39.9755, -23.44, 53.0)
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


# ═══════════════════════════════════════════════════════════════════════════
# dark theme is a different light, not an inverted one
# ═══════════════════════════════════════════════════════════════════════════
# 2026-08-14: --plate-river inverted between themes -- a pale ice-blue ribbon
# at night, the brightest thing on the plate -- and --plate-contour did too, a
# pale gold web fighting the labels. Both are physical ground (water, and the
# isolines of the terrain itself), not ink, so the relationship that must
# hold is: each stays DARKER than every relief band it is drawn over, in BOTH
# themes. Ink tokens (--text, --text-mid, --scene-map-coast) are exempt --
# they are supposed to swap dark-on-light for light-on-dark, the same as a
# page of type does, and that is not the bug.
def _parse_tokens(css_vars: str) -> dict[str, tuple[int, int, int]]:
    out = {}
    for name, hexval in re.findall(r"--([\w-]+):\s*#([0-9A-Fa-f]{6})", css_vars):
        out[name] = tuple(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
    return out


def _srgb_to_linear(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _luminance(rgb):
    r, g, b = rgb
    return (0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g)
            + 0.0722 * _srgb_to_linear(b))


def _mix(fg, bg, a):
    return tuple(a * fg[i] + (1 - a) * bg[i] for i in range(3))


def _ground_values(s3, theme):
    """Every colour the READER sees as ground, per theme: the three opaque
    cover fills, the wet delta as it is actually composited (its wash over the
    fan beneath it), and the two non-cover terrain marks."""
    t = _parse_tokens(s3.TOKENS[theme])
    out = {n: t[n] for n in
           ("pp-cover-fan", "pp-cover-ridge", "pp-cover-open",
            "pp-ida-mass", "pp-tumulus")}
    out["pp-cover-wet*"] = _mix(t["pp-cover-wet"], t["pp-cover-fan"],
                                s3.COVER_WASH_OP)
    return out


def test_river_stays_darker_than_every_ground_colour_in_both_themes(s3):
    """Water is darker than the land it crosses, in daylight AND at night.
    A river keyed to a value that inverts is the glowing-ribbon bug; this
    pins the fix so it cannot come back. Inherited by the ground-cover
    tokens when the twelve-step relief ramp was deleted."""
    for theme in ("light", "dark"):
        river_l = _luminance(_parse_tokens(s3.TOKENS[theme])["plate-river"])
        for name, rgb in _ground_values(s3, theme).items():
            assert river_l < _luminance(rgb), (
                f"{theme}: river (L={river_l:.3f}) is not darker than "
                f"{name} (L={_luminance(rgb):.3f})")


def test_contour_stays_darker_than_every_ground_colour_in_both_themes(s3):
    """Same rule for the isolines: an engraved contour reads as a quiet
    subordinate line by staying darker than its ground in both themes, not
    by inverting to the ink convention and outshining the labels."""
    for theme in ("light", "dark"):
        contour_l = _luminance(_parse_tokens(s3.TOKENS[theme])["plate-contour"])
        for name, rgb in _ground_values(s3, theme).items():
            assert contour_l < _luminance(rgb), (
                f"{theme}: contour (L={contour_l:.3f}) is not darker than "
                f"{name} (L={_luminance(rgb):.3f})")


def test_the_cover_classes_keep_their_order_in_both_themes(s3):
    """DARK THEME IS A DIFFERENT LIGHT, NOT AN INVERTED ONE, applied to the
    ground itself. Dry sand is the brightest ground and wet delta the
    darkest, in daylight and at night alike; if the rank flipped, the plate
    would be telling two different stories about the same ground."""
    order = ["pp-cover-fan", "pp-cover-open", "pp-cover-ridge", "pp-cover-wet*"]
    for theme in ("light", "dark"):
        g = _ground_values(s3, theme)
        lums = [_luminance(g[n]) for n in order]
        assert lums == sorted(lums, reverse=True), (
            f"{theme}: cover order is not fan > open > ridge > wet: "
            + ", ".join(f"{n}={l:.4f}" for n, l in zip(order, lums)))


def test_the_ground_is_no_longer_a_tonal_ramp(s3):
    """The terraces were a LUMINANCE problem. Twelve hypsometric bands spanned
    2.50x in light, so every band edge was a step in the light and a stack of
    them read as flat tables. Ground-cover classes are separated by hue, and
    the whole set must stay inside a spread narrow enough that a class
    boundary cannot read as a step."""
    for theme in ("light", "dark"):
        lums = [_luminance(v) for v in _ground_values(s3, theme).values()
                if v is not None]
        cover = [_luminance(v) for k, v in _ground_values(s3, theme).items()
                 if k.startswith("pp-cover")]
        assert max(cover) / min(cover) < 1.45, (
            f"{theme}: cover luminance spread {max(cover)/min(cover):.2f}x "
            "is wide enough to read as a tonal ramp")


def test_labels_keep_wcag_aa_on_every_ground_colour(s3):
    """Measured, not eyeballed, and on the DIMMEST tier of type on the sheet.
    Small text needs 4.5:1; the labels also carry a halo, but the halo is a
    stroke and the contrast has to hold without leaning on it."""
    for theme in ("light", "dark"):
        ink = _luminance(_parse_tokens(s3.TOKENS[theme])["text-mid"])
        for name, rgb in _ground_values(s3, theme).items():
            if name in ("pp-ida-mass", "pp-tumulus"):
                continue          # marks, not label ground
            g = _luminance(rgb)
            hi, lo = max(ink, g), min(ink, g)
            ratio = (hi + 0.05) / (lo + 0.05)
            assert ratio >= 4.5, (
                f"{theme}: --text-mid on {name} is {ratio:.2f}:1, under AA")


def test_contour_and_river_stay_subordinate_to_label_ink(s3):
    """'Never compete with labels' (John, 2026-08-14), machine-checked: in
    both themes the river and the contour must read as less salient than
    the labels' own --text-mid ink -- the dimmest tier of type on the sheet
    -- so neither can out-shine what the plate is actually saying."""
    for theme in ("light", "dark"):
        tokens = _parse_tokens(s3.TOKENS[theme])
        text_mid_l = _luminance(tokens["text-mid"])
        for name in ("plate-river", "plate-contour"):
            assert _luminance(tokens[name]) < text_mid_l, (
                f"{theme}: {name} is not subordinate to --text-mid")


def test_city_architecture_no_longer_keyed_to_inverting_ink(s3):
    """The recorded ship bug (elements keyed to --text invert to white in
    dark theme) had a second, unfixed instance: Ilios's wall, crest, tower
    and roofs used --text/--text-mid directly and rang the citadel in
    label-white at night. They now take the rim token the hulls already
    use. Pinned so a future edit cannot quietly key them back to --text."""
    css = s3.CSS
    for cls in ("pp-wall", "pp-wall-crest", "pp-tower", "pp-roof"):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", css)
        assert m, f"{cls} not found in CSS"
        block = m.group(1)
        assert "stroke:var(--pp-hull-edge)" in block, (
            f"{cls} stroke is not keyed to --pp-hull-edge: {block}")
        assert "var(--text)" not in block and "var(--text-mid)" not in block, (
            f"{cls} is still keyed to an inverting ink token: {block}")


# ═══════════════════════════════════════════════════════════════════════════
# ground cover: colour says what the ground IS, not how high it is
# ═══════════════════════════════════════════════════════════════════════════
# 2026-08-14. The plate coloured the ground by elevation -- twelve hypsometric
# bands with a metres key -- which is a PLAN-VIEW device on an oblique that
# already shows height geometrically, and which printed as a stack of flat
# terraces ("troy looks like it's on a flat table"). Colour now carries the
# ground-cover classes of docs/research/GROUND-COVER-TROJAN-PLAIN.md; tone
# carries the light; height carries itself.


def test_the_hypsometric_ramp_is_gone(s3):
    """The bug, in its own terms: no relief-ramp token may survive, and no
    fill may be keyed to one."""
    for theme in ("light", "dark"):
        assert "plate-relief" not in s3.TOKENS[theme]
    assert "plate-relief" not in s3.CSS
    assert not hasattr(s3, "COVER_TOKEN_RELIEF")


def test_no_colour_on_the_plate_is_anything_but_a_var_token(s3):
    """TROAD-CARTOGRAPHY.md's standing rule, and half the reason hillshade
    was refused: a baked colour cannot be re-themed, so both themes and both
    contrast requirements are satisfied by the stylesheet or not at all."""
    lit = re.findall(r"(?:fill|stroke)\s*[:=]\s*[\"']?(#[0-9A-Fa-f]{3,8}|"
                     r"rgba?\([^)]*\)|hsla?\([^)]*\))", s3.CSS)
    assert lit == [], f"literal colours in CSS: {lit}"
    for c, tok in s3.COVER_TOKEN.items():
        assert tok.startswith("--"), f"{c} is not a CSS custom property"
        for theme in ("light", "dark"):
            assert tok + ":" in s3.TOKENS[theme], (
                f"{tok} has no {theme} value")


def test_every_cover_class_has_a_token_in_both_themes(s3):
    for theme in ("light", "dark"):
        t = _parse_tokens(s3.TOKENS[theme])
        for name in ("pp-cover-fan", "pp-cover-ridge", "pp-cover-open",
                     "pp-cover-wet"):
            assert name in t, f"{theme} is missing --{name}"


def test_the_masks_are_the_plate_s_own_layers_never_re_derived(s3):
    """§2.1 and §2.4 of the specification: the wet delta and the ridges
    already exist on this sheet, cut from the DEM. Re-deriving thresholds
    here would invent a second, worse boundary for the same ground."""
    assert s3.RIDGE_LAYERS == ("relief-sigeion-ridge", "relief-troy-ridge",
                               "relief-rhoiteion-ridge")
    assert s3.PLAIN_LAYER == "scamandrian-plain"
    assert s3.SWAMP_LAYER == "delta-swamp"
    plate = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")
    if not os.path.exists(plate):
        pytest.skip("plate JSON not present")
    import json
    ids = {l["id"] for l in json.load(open(plate))["layers"]}
    for layer in s3.RIDGE_LAYERS + (s3.PLAIN_LAYER, s3.SWAMP_LAYER):
        assert layer in ids, f"{layer} is not a layer on this plate"


def test_no_sand_barrier_or_beach_class_exists(s3):
    """§2.5: a Bronze Age barrier on the Scamander front is NOT KNOWABLE and
    is contradicted four times over. It may not re-enter as ground cover,
    and `barrier-bronze`'s footprint may not be used as a mask."""
    src = open(s3.__file__ if hasattr(s3, "__file__") else STAGE3).read() \
        if False else open(STAGE3).read()
    for forbidden in ("COVER_BARRIER", "COVER_BEACH", "COVER_DUNE",
                      "pp-cover-barrier", "pp-cover-beach", "pp-cover-dune"):
        assert forbidden not in src, f"{forbidden} is a forbidden class"
    assert "barrier-bronze" not in s3.COVER_TOKEN.values()
    body = src.split("def cover_field", 1)[1].split("def terrain_svg", 1)[0]
    assert "barrier" not in body, (
        "the classifier reads barrier-bronze; §2.5 forbids it")


def test_the_riverbank_thicket_is_lettered_and_never_bounded(s3):
    """§2.3: the flora is the best-attested thing the poem says about this
    ground AND has no defensible extent, because the channels it grew along
    are unlocatable. It must appear in the key and nowhere in the geometry."""
    assert any("RIVERBANK THICKET" in s for s in [s3.COVER_KEY_UNDRAWN])
    assert "21.350" in s3.COVER_KEY_UNDRAWN
    assert "not bounded" in s3.COVER_KEY_UNDRAWN
    assert "thicket" not in str(s3.COVER_TOKEN)
    assert all(c != "thicket" for c in s3.COVER_ORDER)


def test_the_key_names_the_classes_and_no_longer_names_metres(s3):
    """The key WAS the instruction to read colour as height. It is now four
    ground-cover entries and carries no elevation numbers at all."""
    src = open(STAGE3).read()
    assert "ELEVATION, METRES" not in src
    assert "GROUND COVER" in src
    named = {c for c, _, _ in s3.COVER_KEY}
    assert named == set(s3.COVER_ORDER) | {"wet"}
    for _, name, gloss in s3.COVER_KEY:
        assert name and gloss, "every key entry states its evidence"
    # the weakest class says so, and the unclassified one says that
    joined = " ".join(g for _, _, g in s3.COVER_KEY)
    assert "default" in joined and "not classified" in joined


def test_the_contour_switch_has_three_settings_and_none_means_none(s3):
    assert s3.CONTOUR_MODES == ("all", "index", "none")
    assert s3.CONTOURS in s3.CONTOUR_MODES


def test_cover_classification_is_priority_ordered(s3):
    """Ridge beats plain-sector, and anything in neither carries no claim.
    Driven through the real classifier with two square masks, so the test
    exercises the code and not a restatement of it."""
    lat0, lon0 = s3.VIEWPOINT
    mlon = 111320.0 * math.cos(math.radians(lat0))
    box = lambda la, lo, d: [[la - d, lo - d], [la - d, lo + d],
                             [la + d, lo + d], [la + d, lo - d]]
    # the ridge lies wholly inside the plain sector, so their overlap is the
    # case the priority rule exists for
    P = object.__new__(s3.Plate)
    P.lay = {"relief-sigeion-ridge": {"polygon": box(lat0, lon0, 0.004)},
             "relief-troy-ridge": {"polygon": box(lat0 + 9, lon0, 0.001)},
             "relief-rhoiteion-ridge": {"polygon": box(lat0 + 9.5, lon0, 0.001)},
             "scamandrian-plain": {"polygon": box(lat0, lon0, 0.02)}}
    P.stats = {}

    def cover_at(dlon_deg):
        """One cell whose four corners all sit at the same offset, so the
        cell centre is exactly that offset."""
        e = dlon_deg * mlon
        P.wor = [[(e, 0.0), (e, 0.0)], [(e, 0.0), (e, 0.0)]]
        P.visible = {(0, 0)}
        P.cover_field()
        return P.cover[(0, 0)]

    assert cover_at(0.0) == s3.COVER_RIDGE, "ridge must beat the sector"
    assert cover_at(0.01) == s3.COVER_FAN, "the sector's remainder is the fan"
    assert cover_at(0.5) == s3.COVER_OPEN, (
        "ground outside every mask carries no claim")
    assert P.stats["cover_cells"][s3.COVER_OPEN] == 1


def test_a_cover_class_is_never_split_at_an_isoline(s3):
    """A ground-cover boundary is not an isoline, so no cell is clipped
    against one. The band-fragment machinery that did that is gone, and the
    contour hairlines are extracted on their own."""
    src = open(STAGE3).read()
    assert "def clip_below" not in src and "def clip_above" not in src
    assert "_interp_elev" not in src
    body = src.split("def terrain_svg", 1)[1].split("def shade_field", 1)[0]
    assert "frag" not in body, "fill fragments are band machinery"


def test_the_shade_median_removes_islands_without_moving_an_edge(s3):
    """The blotchy foreground: one-cell tone islands round into countable
    ovals. A median kills an isolated cell in one pass and leaves a straight
    edge between two broad regions exactly where it was."""
    # a 7x7 quantised field: left half at -3, right half at 0, one island
    q = {(i, j): (-3 if i < 3 else 0) for i in range(7) for j in range(7)}
    q[(1, 1)] = 5
    out, islands = s3.median_lattice(q, 1)
    assert out[(1, 1)] == -3, "the one-cell island survived the median"
    assert islands >= 1, "the island was not counted"
    # and the edge between the two regions has not moved
    for j in range(1, 6):
        assert out[(2, j)] == -3 and out[(3, j)] == 0, (
            "the median moved the boundary between two broad regions")
    # a field with no islands is a fixed point
    clean = {(i, j): (-3 if i < 3 else 0) for i in range(7) for j in range(7)}
    same, none = s3.median_lattice(clean, 3)
    assert same == clean and none == 0


def test_the_shade_dials_are_the_ones_that_were_measured(s3):
    """SIX WAS RIGHT WHILE THE EDGES WERE RAW, AND IS NOT RIGHT NOW.

    The old finding -- "raising the step count made the near foreground worse,
    more step boundaries for the lattice to show through" -- was true of a
    lattice that showed through. Two things changed under it: the near band is
    stepped on a finer screen rule (RING_PX_NEAR), and every tone edge is
    low-passed before it is generalised, so a step boundary is no longer a
    place the lattice can print. Re-measured on the shipped frame at 6 / 10 /
    14 steps: at 6 the near foreground is nearly unmodelled -- the gully
    system under the camp does not read at all; at 14 it breaks into pale
    filaments and countable marks, which is the old defect arriving on
    schedule; at 10 the gullies read and no filament appears. SVG weight
    525 / 606 / 680 KB for the same three.

    The dial is not free and this test is the record of what it cost to move.
    """
    assert s3.SHADE_STEPS == 10
    assert s3.SHADE_MEDIAN >= 1 and s3.SHADE_SMOOTH >= 3
    assert s3.SHADE_SOFT_PASSES >= 1, (
        "more steps is only safe while the tone edges are low-passed")


# ═══════════════════════════════════════════════════════════════════════════
# the low-pass: every lattice-derived line gets the curve the coastline had
# ═══════════════════════════════════════════════════════════════════════════
# docs/TROAD-CARTOGRAPHY.md, third pass: "every measured line is now drawn as a
# curve, not just relief" -- facets assert a precision the data does not have.
# The coastline obeyed it and nothing else on the sheet did: the contours were
# emitted as DISCONNECTED per-cell segments (nothing to smooth), the rivers as
# raw survey facets, the tone and cover boundaries as lattice staircases.


def test_a_straight_run_is_a_fixed_point_of_the_low_pass(s3):
    """Why a neighbour average and not more corner-cutting: it must leave a
    stratum seam and a neatline edge exactly where they are."""
    line = [(float(x), 100.0) for x in range(0, 200, 10)]
    out = s3.soften(line, 6, closed=False)
    for a, b in zip(line, out):
        assert abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6


def test_the_low_pass_kills_a_one_ring_riser_and_chaikin_does_not(s3):
    """The measured defect: a 37 px riser in the near-field cover boundary.
    Corner-cutting converges to a quadratic B-spline and leaves about half of
    it standing however many passes it is given; a repeated neighbour average
    keeps attenuating. This is the whole argument for soften() over chaikin()."""
    step = [(float(x), 0.0) for x in range(0, 60, 6)]
    step += [(60.0, 37.0)]
    step += [(float(x), 37.0) for x in range(66, 126, 6)]
    amp = lambda p: max(y for _, y in p) - min(y for _, y in p)
    # WHAT IS MEASURED IS THE SLOPE OF THE JOIN, not the rise per segment:
    # corner-cutting inserts points ON the riser, so its segments get short
    # while the knee stays exactly as steep. That is the defect.
    def steepest(p):
        return max(abs(b[1] - a[1]) / max(1e-6, abs(b[0] - a[0]))
                   for a, b in zip(p, p[1:]))
    assert steepest(step) > 6.0
    ch = s3.chaikin(s3.chaikin(step, 4, closed=False), 4, closed=False)
    sf = s3.soften(step, 8, closed=False)
    assert steepest(sf) < steepest(ch) * 0.5, (
        f"low-pass slope {steepest(sf):.2f} is not beating corner-cutting "
        f"{steepest(ch):.2f} on a one-ring riser")
    assert steepest(sf) < 2.5, "the riser is still a step, not a ramp"
    assert amp(sf) > 30.0, "the low-pass moved the boundary, not just the step"


def test_the_low_pass_does_not_shrink_a_small_tone_island(s3):
    """Plain Laplacian smoothing pulls a closed loop toward its centroid on
    every pass and a five-cell tone region would vanish. Taubin's +lam/-mu
    alternation is why the loop keeps its area."""
    import math as _m
    ring = [(20 * _m.cos(2 * _m.pi * k / 12), 20 * _m.sin(2 * _m.pi * k / 12))
            for k in range(12)]
    out = s3.soften(ring, 8)
    r0 = sum(_m.hypot(*p) for p in ring) / len(ring)
    r1 = sum(_m.hypot(*p) for p in out) / len(out)
    assert r1 > 0.9 * r0, f"the loop shrank from {r0:.1f} to {r1:.1f}"


def test_contours_are_chained_into_lines_before_they_are_drawn(s3):
    """They were a soup of two-point facets: 'just a bunch of straight lines
    forming sharp angles' (John). Chaining is on the LATTICE EDGE each crossing
    sits on, not on the coordinate -- the same crossing computed from either of
    the two cells that share an edge differs in the last bit of the float."""
    # a four-cell run of a level crossing left to right
    segs = []
    for i in range(4):
        a = (((i, 0), (i, 1)), (float(i), 0.5))
        b = (((i + 1, 0), (i + 1, 1)), (float(i + 1), 0.5))
        segs.append((a, b))
    lines = s3.chain_segments(segs)
    assert len(lines) == 1, f"{len(lines)} lines from one continuous contour"
    pts, shut = lines[0]
    assert not shut and len(pts) == 5
    assert [p[0] for p in pts] == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_a_closed_contour_chains_as_a_closed_ring(s3):
    ring_nodes = [(0, 0), (1, 0), (1, 1), (0, 1)]
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    segs = [((ring_nodes[k], pts[k]),
             (ring_nodes[(k + 1) % 4], pts[(k + 1) % 4])) for k in range(4)]
    lines = s3.chain_segments(segs)
    assert len(lines) == 1
    out, shut = lines[0]
    assert shut and len(out) == 4


def test_the_smoothing_is_tuned_per_line_type(s3):
    """Three different claims, three strengths. A contour is a measured line
    and takes the lightest touch; a tone edge stands for nothing and can be
    softened until it reads as a wash; a cover boundary has a whole ring of
    quantisation in it and needs the heaviest kernel on the sheet."""
    assert s3.CONTOUR_SOFT < s3.COVER_SOFT
    assert s3.SHADE_SOFT_PASSES <= s3.COVER_SOFT
    assert s3.CONTOUR_SOFT >= 1 and s3.RIVER_SOFT >= 1


def test_the_near_band_is_stepped_on_a_finer_screen_rule(s3):
    """The sawtooth was in the MESH, not in the drawing. RING_PX steps rings by
    their separation on FLAT ground, and the near foreground is the back of the
    Sigeion ridge falling away, which spreads the same step over far more
    screen. A smoother cannot invent a sample the mesh never took."""
    assert s3.RING_PX_NEAR < s3.RING_PX
    rngs = s3.ring_ranges(lambda r: 1000.0 - 900.0 * r / (r + 4000.0))
    near = [b - a for a, b in zip(rngs, rngs[1:]) if b < s3.RING_NEAR_DETAIL]
    far = [b - a for a, b in zip(rngs, rngs[1:])
           if s3.RING_NEAR_DETAIL < a < 6000.0]
    assert near and far
    assert max(near) < min(far), (
        "the near band is not sampled more finely than the band beyond it")


# ═══════════════════════════════════════════════════════════════════════════
# Ilios stands on the ground: the citadel's own shadow
# ═══════════════════════════════════════════════════════════════════════════


def test_the_citadel_throws_a_shadow_like_everything_else_that_stands(s3):
    """'Troy looks like it's floating' (John). 459 hulls and 270 huts were each
    pinned to the beach by a true-length shadow; the citadel -- the biggest
    built thing in the frame -- was excluded and read as a sticker."""
    src = open(STAGE3).read()
    body = src.split("def city(", 1)[1].split("\ndef draped_ribbon", 1)[0]
    assert "object_shadow(" in body, "the city still throws nothing"
    assert "drape=True" in body, (
        "a 90 m shadow off a spur cannot be laid flat at the centre's height")
    # and it takes the roofs, whose ridges out-throw the wall
    assert "ROOFS" in body


def test_the_citadel_shadow_is_the_true_height_over_tan_altitude(s3):
    """Same rule as the hulls: no fudge factor for the big object."""
    s3.set_light(s3.LIGHT_AZ_DEFAULT, 9.9)
    for h in (6.0, 15.2):
        dx, dy = s3.sun_offset(h)
        assert abs(math.hypot(dx, dy)
                   - h / math.tan(math.radians(9.9))) < 1e-6


def test_the_wall_takes_a_lit_face_and_a_shaded_face(s3):
    """A flat ellipse ring in perspective reads as a plan-view oval however
    well it is grounded. Both washes are the terrain's own tokens, so the
    citadel is lit by the same sun as the ground it stands on."""
    for cls, tok in (("pp-wall-lit", "var(--pp-lit)"),
                     ("pp-wall-shade", "var(--pp-shade)")):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", s3.CSS)
        assert m, f"{cls} is not in the stylesheet"
        assert f"fill:{tok}" in m.group(1)


def test_the_rampart_and_the_barrows_throw_too(s3):
    """Anything standing on the ground that does not cast reads as pasted on.
    The rampart is drawn as ONE shadow band rather than 74 hulls, because the
    wall is continuous and hulling each station would print the seams."""
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    assert "wall_ground" in camp and "pp-objshadow" in camp
    build = src.split("def build(", 1)[1].split("def emit(", 1)[0]
    assert "object_shadow(" in build, "the tumuli still throw nothing"


def test_the_rampart_keeps_its_towers(s3):
    """Every fourth station stands 3.4 m higher and those spikes ARE the towers
    (Il. 7.436-439). A low-pass would file them off, so the rampart is the one
    line on the sheet that is deliberately not softened."""
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    ramp = camp.split("pp-rampart", 1)[1][:400]
    assert "soften(" not in ramp.split("wall_pts")[0]
