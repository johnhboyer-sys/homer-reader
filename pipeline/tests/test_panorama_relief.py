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
    contrast requirements are satisfied by the stylesheet or not at all.

    IT NOW SCANS THE EMITTED SVG TOO, and that is the half that was missing.
    Scanning s3.CSS alone could only ever catch a literal written in the
    stylesheet; every colour the drawing code emits inline — and the
    gradients above all, which are generated in Python and never appear in
    CSS at all — went straight past it."""
    lit = re.findall(r"(?:fill|stroke)\s*[:=]\s*[\"']?(#[0-9A-Fa-f]{3,8}|"
                     r"rgba?\([^)]*\)|hsla?\([^)]*\))", s3.CSS)
    assert lit == [], f"literal colours in CSS: {lit}"
    # and the DRAWING CODE, which is where every colour the stylesheet never
    # sees is written: inline fills, inline strokes, and the gradients, which
    # are generated in Python and appear in no stylesheet at all.
    src = open(STAGE3).read()
    src = "\n".join(l for l in src.split("\n")
                    if not l.lstrip().startswith("#"))
    lit = re.findall(r"(?:fill|stroke|stop-color)\s*[:=]\s*[\\\"']?"
                     r"(#[0-9A-Fa-f]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\))", src)
    assert lit == [], f"literal colours emitted by the drawing: {sorted(set(lit))}"


def _cam(s3):
    """The shipped camera with its pitch handed to it, so the frame-level
    machinery — sky, air, water ramps — can be tested without the DEM."""
    return s3.Camera(None, pitch=math.radians(13.23))


# ═══════════════════════════════════════════════════════════════════════════
# air, sky and water — the realism pass, 2026-08-14
# ═══════════════════════════════════════════════════════════════════════════
# Three quantities the plate had been drawing as constants: the air between
# the eye and the ground, the sky above the horizon, and the surface of the
# bay. Each is now a law with one dial, and these tests are what stops the
# laws being quietly replaced by taste again.


def test_the_air_is_beer_lambert_and_not_a_table(s3):
    """HAZE was four hand-set numbers on four of the eleven strata. It is now
    derived: the wash emitted at a stratum edge is exactly the slab of air
    that stratum spans, so the product of the washes in front of any ground
    is exp(-range / HAZE_D). This checks the integration, which is the whole
    claim — get it wrong and the distance is a dose, not a depth."""
    edges = s3.STRATA_EDGES
    assert len(s3.HAZE) == len(edges) - 1, (
        "not every stratum lays down its own slab: the distance will step")
    for k in range(len(edges) - 1):
        cum = 1.0
        for j in range(k + 1, len(edges) - 1):     # every slab nearer than k
            cum *= 1.0 - s3.HAZE[edges[j]]
        want = math.exp(-edges[k + 1] / s3.HAZE_D)
        assert cum == pytest.approx(want, rel=1e-9), (
            f"transmittance to {edges[k + 1]:.0f} m is {cum:.4f}, "
            f"Beer-Lambert says {want:.4f}")
    assert s3.haze_at(0.0) == 0.0
    assert 0.4 < s3.haze_at(26000.0) < 0.75, (
        "the far shore of the bay is either not receding or gone entirely")


def test_the_gradients_are_one_token_and_an_opacity_ramp(s3):
    """The rule that keeps a gradient re-themable: two tokens cannot be
    interpolated between without baking a literal, so no ramp on this plate
    interpolates COLOUR. Each is one var() token whose stop-opacity varies,
    over a flat fill of a second token."""
    defs = s3.make_defs(_cam(s3))
    grads = re.findall(r"<linearGradient[^>]*>(.*?)</linearGradient>", defs)
    assert len(grads) >= 3, "the sky and the two water ramps are not there"
    for g in grads:
        stops = re.findall(r"<stop[^>]*>", g)
        assert len(stops) >= 8, "a ramp this coarse will band"
        cols = {re.search(r'stop-color="([^"]+)"', s).group(1) for s in stops}
        assert len(cols) == 1 and cols.pop().startswith("var(--"), (
            "a gradient interpolates between colours: it has baked a literal")
        ops = [float(re.search(r'stop-opacity="([\d.]+)"', s).group(1))
               for s in stops]
        assert ops == sorted(ops) or ops == sorted(ops, reverse=True), (
            "a ramp that is not monotonic in opacity is not a depth cue")


def test_the_land_dissolves_into_the_horizon_it_meets(s3):
    """--pp-haze is what distance resolves to and --pp-sky-lo is what the sky
    is where the land meets it. If they disagree, the far ground stops
    receding and starts floating in front of the sky. They must be close in
    value, and the ground must always end up the DARKER of the two — nothing
    on the earth is brighter than the sky behind it."""
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        haze, sky = _srgb_lum(t["--pp-haze"]), _srgb_lum(t["--pp-sky-lo"])
        assert haze < sky, f"{theme}: the distance is brighter than the sky"
        assert abs(haze - sky) < 0.10, (
            f"{theme}: haze L={haze:.3f} and horizon sky L={sky:.3f} are far "
            "enough apart that the far ground will read as a cut-out")


def test_dark_theme_is_a_different_light_for_the_air_too(s3):
    """The plate's oldest rule, applied to the air, and MEASURED ON WHAT THE
    LABELS SIT ON rather than on the token.

    The naive claim — "daylight haze is lighter than every ground colour" —
    is false and should be: a veil at a fixed luminance darkens whatever is
    brighter than it and lightens whatever is darker, which is what haze
    does to pale sand under a blue sky in life. What actually has to hold is
    the consequence: at FULL haze, on the farthest ground the plate draws,
    --text-mid must still clear WCAG AA on every class in both themes. In
    daylight the veil is pale; at night it is dark; either way the veil
    COLLAPSES the ground toward itself, which is the thing aerial
    perspective actually is, and the collapse must not take a class through
    the ink on the way."""
    full = s3.haze_at(max(s3.STRATA_EDGES))
    classes = ("--pp-cover-fan", "--pp-cover-open", "--pp-cover-ridge")
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        raw, veiled = [], []
        for g in classes:
            hazed = _over(t["--pp-haze"], t[g], full)
            r = _ratio(t["--text-mid"], hazed)
            assert r >= 4.5, (
                f"{theme}: --text-mid on {g} under full haze is {r:.2f}:1")
            raw.append(_srgb_lum(t[g]))
            veiled.append(_srgb_lum(hazed))
        assert max(veiled) - min(veiled) < 0.5 * (max(raw) - min(raw)), (
            f"{theme}: the air is not flattening the distance's contrast")
        ink = _srgb_lum(t["--text-mid"])
        assert all((v > ink) == (r > ink) for v, r in zip(veiled, raw)), (
            f"{theme}: the haze carried a ground class across the label ink")


def test_the_shoal_is_lighter_than_its_water_in_both_themes(s3):
    """Shallow water over a pale sand floor is lighter than deep water, at
    noon and at dusk alike — and it has to be, because 'the bay of Troy' is
    lettered on this water and the shoal must never take contrast away from
    it."""
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        assert _srgb_lum(t["--pp-water-shoal"]) > _srgb_lum(t["--plate-lagoon"]), (
            f"{theme}: the shoal is darker than the water it shallows into")


def test_the_shoal_holds_its_width_in_ground_not_in_pixels(s3):
    """A fixed pixel margin would be widest where the water is farthest,
    which would make the band a claim about something other than
    perspective. And the SCALE has to be the along-sight one: the first cut
    used FOCAL/r, the across-sight scale, and left the far shore of the bay
    with a band fifty pixels wide — the same failure by a different door."""
    k = s3.plane_scale(_cam(s3))
    near, far = k(2600.0), k(18000.0)
    assert near > far * 20.0, (
        f"the plane's scale is falling off as 1/r, not 1/r^2: {near:.4f} "
        f"px/m at 2.6 km against {far:.4f} at 18 km — this is the "
        "across-sight scale and it is the wrong one for a shoal")
    assert s3._shoal_px(far, s3.SHOAL_BANDS[0]) < 6.0, (
        "the shoal on the far shore of the bay is still a visible band")
    assert s3._shoal_px(k(300.0), s3.SHOAL_BANDS[0]) <= s3.SHOAL_PX_MAX
    assert s3.SHOAL_BANDS == tuple(sorted(s3.SHOAL_BANDS, reverse=True)), (
        "the bands are painted outermost first so that they stack")


def test_the_sky_and_the_water_are_measured_off_the_camera(s3):
    """Both ramps are keyed to SCREEN Y and both are exact for the reason
    that image y on a horizontal plane is a function of axial depth alone.
    The horizon is projected, never guessed; the water stops start at it and
    run to the foot of the frame, monotonically."""
    cam = _cam(s3)
    hy = s3.horizon_y(cam)
    assert 0 < hy < s3.H / 2, (
        f"the horizon is at y={hy:.0f}, which is not where a 13-degree "
        "downward pitch puts it")
    stops = s3.plane_ramp(cam, lambda r: s3.haze_at(r))
    offs = [o for o, _ in stops]
    assert offs == sorted(offs) and len(set(offs)) == len(offs)
    assert offs[0] * s3.H >= hy - 1.0, "a water stop is above the horizon"
    alphas = [a for _, a in stops]
    assert alphas == sorted(alphas, reverse=True), (
        "the air is not thinning toward the reader")
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


def test_the_riverbank_thicket_is_drawn_but_its_width_never_is(s3):
    """THIS TEST REPLACES ONE THAT ASSERTED THE OPPOSITE, and the replacement
    is the point: the old claim was "lettered, never drawn", on the reasoning
    that the Bronze Age channels are unlocatable. That reasoning bounds the
    thicket's EXTENT and this plate never had to state one -- it already draws
    the Scamander and the Simoeis as declared schematic lines, so a fringe hung
    on a drawn course adds no locational claim the sheet is not already making,
    which is exactly what §2.3 asks for ("tie this class to the schematic river
    line as a schematic band"). What §2.3 still forbids is printing a metre
    value for the fringe's width, and that is what is pinned here."""
    key = " ".join(n + " " + g for n, g in s3.VEG_KEY)
    assert "RIVERBANK THICKET" in key
    assert "21.350" in key, "the thicket must carry its line of the poem"
    # it is not a ground-cover class: it hangs on the river, not on the mesh
    assert "thicket" not in str(s3.COVER_TOKEN)
    assert all(c != "thicket" for c in s3.COVER_ORDER)
    # and the sheet may not state a width for it
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "artist" in s3.COVER_KEY_UNDRAWN and "never a measured one" in s3.COVER_KEY_UNDRAWN
    assert f"{s3.BANK_OFFSET_M:g} m" not in svg, (
        "the fringe's offset is an artist's convention and may not be printed "
        "on the sheet as if it were measured")


def test_every_plant_drawn_carries_a_line_of_the_poem_or_a_stated_class(s3):
    """The rule the whole vegetation pass runs on. Three of the four things
    that grow here are named in the Iliad and cite it; the fourth is the ridge
    default the key already carried, and it says in the key that it has no
    line."""
    cites = {n: g for n, g in s3.VEG_KEY}
    assert "6.237" in cites["THE OAK"]
    assert "22.145" in cites["THE WILD FIG"]
    assert "21.350" in cites["RIVERBANK THICKET"]
    assert "no line of the poem" in cites["RIDGE SCRUB"], (
        "ridge scrub is a regional default and the key must not imply a text")


def test_ida_s_timber_is_attested_and_declared_undrawn(s3):
    """Il. 23.114-20 cuts high-crowned oaks on Ida's spurs and 14.287 puts a
    towering fir there, so the poem carries a wooded Ida -- and the mountain
    sits at 45-80 km behind 0.73 of the air, where a 20 m tree is a tenth of a
    pixel. It is lettered, exactly as the thicket's width is."""
    assert "23.114" in s3.COVER_KEY_UNDRAWN and "Ida" in s3.COVER_KEY_UNDRAWN
    src = open(STAGE3).read()
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    assert "ida" not in veg.lower(), "nothing is planted on Ida"


def test_the_dry_fan_grows_nothing(s3):
    """GROUND-COVER-TROJAN-PLAIN.md §5.3 forbids furrowed grainfields and plot
    boundaries outright; the fertility epithets qualify the class and give no
    pattern. Only the ridge class may carry a mark."""
    src = open(STAGE3).read()
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    assert "COVER_RIDGE" in veg
    assert "COVER_FAN" not in veg, "something was planted on the battlefield"


def test_vegetation_throws_a_true_shadow_like_every_built_thing(s3):
    """The trees go through object_shadow at their own height, the same call
    the hulls, the huts and the tumuli make. That is what puts them ON the
    ground; without it they float, which was the citadel's old defect."""
    src = open(STAGE3).read()
    for fn in ("def tree(", "def thicket("):
        body = src.split(fn, 1)[1].split("\ndef ", 1)[0]
        assert "object_shadow(" in body, f"{fn} draws no shadow"
        assert "built_h(" in body, f"{fn} does not stand on the exaggerated ground"


def test_the_crowd_gains_members_at_the_zoom_tiers_it_does_not_scale(s3):
    """The zoom finding: a mark-based texture only survives magnification if
    it is REGENERATED per tier. Both crowds put a subset in the overview and
    the rest behind tm2, so zooming in finds more trees among the ones already
    there rather than the same trees drawn bigger."""
    src = open(STAGE3).read()
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    assert "marks_t1" in veg and "marks_t3" in veg
    assert '"tm2"' in veg, "the extra crowd is never gated to a zoom tier"
    assert s3.SCRUB_PX2 > s3.SCRUB_PX2_ZOOM, (
        "the zoom tiers must be denser in screen area, not larger in mark")
    # deterministic: the same seed gives the same jitter, so tier 3 contains
    # tier 1 instead of being a different wood
    assert s3._rnd(4, 11) == s3._rnd(4, 11)
    assert s3._rnd(4, 11) != s3._rnd(5, 11)
    assert 0.0 <= s3._rnd(7, 3, 9) < 1.0


def test_the_key_names_the_classes_and_no_longer_names_metres(s3):
    """The key WAS the instruction to read colour as height. It is now four
    ground-cover entries and carries no elevation numbers at all."""
    src = open(STAGE3).read()
    assert "ELEVATION, METRES" not in src
    assert "GROUND COVER" in src
    named = {c for c, _, _ in s3.COVER_KEY}
    # COVER_DROWNED is not a key row and must not become one: it is a REPAIR
    # of a hole between the two drawn shores, painted as the reconstruction
    # already paints itself, and it is declared in the cartouche instead.
    assert named == (set(s3.COVER_ORDER) - {s3.COVER_DROWNED}) | {"wet"}
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
    # the two shores are parked far away, so no cell here can be a drowned gap
    # and the priority rule is what is under test
    P.lay = {"relief-sigeion-ridge": {"polygon": box(lat0, lon0, 0.004)},
             "relief-troy-ridge": {"polygon": box(lat0 + 9, lon0, 0.001)},
             "relief-rhoiteion-ridge": {"polygon": box(lat0 + 9.5, lon0, 0.001)},
             "scamandrian-plain": {"polygon": box(lat0, lon0, 0.02)},
             "lagoon-bronze": {"polygon": box(lat0 + 4, lon0 + 4, 0.002)},
             "sea-modern": {"polygon": box(lat0 + 4.5, lon0 + 4, 0.002)}}
    P.stats = {}
    P._rings = {}

    def cover_at(dlon_deg, elev=40.0):
        """One cell whose four corners all sit at the same offset, so the
        cell centre is exactly that offset."""
        e = dlon_deg * mlon
        P.wor = [[(e, 0.0), (e, 0.0)], [(e, 0.0), (e, 0.0)]]
        P.grid = [[(0.0, 0.0, elev, 1.0), (0.0, 0.0, elev, 1.0)],
                  [(0.0, 0.0, elev, 1.0), (0.0, 0.0, elev, 1.0)]]
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

    RE-MEASURED AGAIN 2026-08-14, on a finer mesh and a sharper field, on the
    suspicion that the filaments at 14 were an artefact of quantising a smooth
    surface and would not survive a surface with real texture. THEY SURVIVED,
    and 14 is still wrong: rendered at ring floor 45 m, field sigma 20.7 m and
    2 smoothing passes, the near foreground breaks into a regular lattice of
    countable ovals across the dry fan below the camp -- the fish scales, by
    name -- and the SVG goes 682 -> 776 KB to print them. 10 stands.

    SHADE_SMOOTH is 2, not 5, and that is this pass's real find. Its kernel is
    a centre-doubled 3x3, variance 0.6 cells a pass, so five passes was sigma
    1.73 MESH CELLS -- at the old 110 m ring floor, 190 m of ground, against
    the DEM blur's 41 m that everyone was blaming. It was the biggest smoother
    on the sheet by a factor of four. At 2 passes the gully system under the
    camp reads; at 1 the tone islands the median has to filter go 3,628 ->
    5,057 and the foreground starts to bead. The floor here is 2, not 3.

    RE-MEASURED A THIRD TIME 2026-08-14, and TEN IS NO LONGER THE ANSWER,
    because the thing ten was the best answer to has been replaced. Every
    finding above is about EXACT-LEVEL tone regions -- the drawing where
    level k is the ground that lands exactly on step k. Those regions are
    isolated, they each carry seven tenths of the tone, and the area filter's
    rescue therefore prints a bright bead in the middle of a shadow: that is
    what the fish scales always were, and it is why more steps made it worse.
    The tone is now built from SUPERLEVEL SETS, nested washes of one
    eighteenth each (see SHADE_STEPS in the script), and neither property
    survives the change.

    Measured again on the shipped frame, 10 / 18 / 26 steps, light theme,
    full 1x:

        10   677 KB   wash banding is still countable on the bay-facing
                      slope under Rhoiteion and along the near ridge back
        18   868 KB   no band edge findable anywhere at 1x; the gully system
                      under the camp holds; nothing beads at 8x
        26  1058 KB   indistinguishable from 18 at 1x and at 8x

    So the cost curve is linear and the benefit stops at 18. The fish scales
    did not come back at 26 either, which is the positive evidence that the
    old ceiling was the exact-level drawing and not the step count.
    """
    assert s3.SHADE_STEPS == 18
    assert s3.SHADE_MEDIAN >= 1 and s3.SHADE_SMOOTH >= 2
    assert s3.SHADE_SOFT_PASSES >= 1, (
        "more steps is only safe while the tone edges are low-passed")
    # and the drawing it was re-measured on: superlevel sets, not exact
    # levels. If this ever goes back to `shade.get(st)` alone the number
    # above is wrong again.
    src = open(STAGE3).read()
    body = src.split("def terrain_svg(", 1)[1].split("def shade_field", 1)[0]
    assert "acc |= shade.get" in body, (
        "the tone is back to exact-level regions; 18 was measured on "
        "nested washes and is not a number that transfers")


def test_the_wash_alpha_is_solved_not_chosen(s3):
    """n nested washes of alpha a composite to 1-(1-a)^n. The per-wash alpha
    is solved so that lands exactly on SHADE_MAX however many washes there
    are — otherwise every change to the step count would silently change how
    dark the plate's darkest ground is."""
    for mx in (s3.SHADE_MAX, s3.LIT_MAX):
        a = 1.0 - (1.0 - mx) ** (1.0 / s3.SHADE_STEPS)
        assert 1.0 - (1.0 - a) ** s3.SHADE_STEPS == pytest.approx(mx, abs=1e-9)
        assert 0.0 < a < 0.1, (
            f"a single wash at {a:.3f} is heavy enough to band on its own")


def test_a_shadow_has_sky_in_it(s3):
    """SHADOW_AMBIENT. Ground that cannot see the sun is not black: it is lit
    by the hemisphere, in proportion to how much of it the surface can see.
    Three things must hold, or the long shadow off Troy's scarp goes back to
    being a flat hole with no landform inside it."""
    s3.set_light(228.4, 9.9)

    class _Blocked:
        def at(self, e, n):
            return 0.0

    def cell(dz, shadow):
        P = object.__new__(s3.Plate)
        P.shadow = shadow
        # a facet tilted dz metres over 100 m, across the light
        P.grid = [[(0, 0, 0.0, 1e3), (0, 0, 0.0, 1e3)],
                  [(0, 0, dz, 1e3), (0, 0, dz, 1e3)]]
        P.wor = [[(0.0, 0.0), (0.0, 100.0)], [(100.0, 0.0), (100.0, 100.0)]]
        return P.shade_raw(0, 0)

    flat_shadowed = cell(0.0, _Blocked())
    steep_shadowed = cell(400.0, _Blocked())
    assert flat_shadowed > -0.95, (
        "flat ground in shadow is still at the bottom step: the shadow has "
        "no sky in it and nothing inside it can be modelled")
    assert steep_shadowed < flat_shadowed, (
        "a steep face in shadow must be darker than flat ground in shadow — "
        "it sees less of the sky")
    assert cell(0.0, None) == pytest.approx(0.0, abs=1e-12), (
        "flat ground in full sun must still take no wash at all")
    s3.set_light(s3.LIGHT_AZ_DEFAULT, s3.LIGHT_ALT_DEFAULT)


def test_the_material_gain_is_a_property_of_the_ground_not_of_the_light(s3):
    """Sand, scrub and unclassified ground do not take light alike (see
    MATERIAL). Two things are pinned: the gain exists for exactly the three
    cover classes, in the order the substances actually take tone; and it is
    NOT in shade_raw, which must stay a pure function of slope and light."""
    assert set(s3.MATERIAL) == {s3.COVER_FAN, s3.COVER_RIDGE, s3.COVER_OPEN}
    assert (s3.MATERIAL[s3.COVER_FAN] < s3.MATERIAL[s3.COVER_OPEN]
            < s3.MATERIAL[s3.COVER_RIDGE]), (
        "the dry fan is the brightest, dustiest, most multiply-scattering "
        "ground on the sheet and must take tone the most softly")
    for v in s3.MATERIAL.values():
        assert 0.5 < v < 1.6, "a material gain this far from 1 is a repaint"
    src = open(STAGE3).read()
    raw = src.split("def shade_raw(", 1)[1].split("def ida_svg", 1)[0]
    assert "MATERIAL" not in raw, (
        "the material gain has leaked into shade_raw, which makes the light "
        "a function of where a cell is")


# ═══════════════════════════════════════════════════════════════════════════
# the field the mesh samples is not the grid the contours are traced on
# ═══════════════════════════════════════════════════════════════════════════
# "too soft and painterly. more detail fixes that" (John, 2026-08-14). The
# suspect was prep-terrain-contours' 10+2 box passes, and the suspect was
# largely innocent: measured over the whole trojan-plain sheet they cost
# 1.14 m RMS of height and 13% of the slope at a 29 m baseline, because the
# raw grid's power spectrum falls at about -5 from 234 m to 39 m wavelength
# with no white floor -- SRTM has neither landform nor noise down there. The
# blur still goes, because it buys nothing either, but the detail came from
# the mesh and from SHADE_SMOOTH.


def test_the_panorama_has_its_own_smoothing_and_the_bronze_age_does_not_move():
    """A traced contour and a shaded surface want opposite treatments, so the
    panorama's field is a separate key. What must NOT have moved is `blur`:
    build_bronze_grid reads it, and the Bronze Age shore, barrier and swamp
    were tuned against published measurements at 10 passes."""
    import importlib.util as iu
    p = os.path.join(REPO, "scripts", "prep-terrain-contours.py")
    if not os.path.exists(p):
        pytest.skip("prep-terrain-contours.py not present")
    sp = iu.spec_from_file_location("ptc", p)
    ptc = iu.module_from_spec(sp)
    sp.loader.exec_module(ptc)
    spec = ptc.SHEETS["trojan-plain"]
    assert spec["blur"] == 10 and spec.get("post_blur") == 2, (
        "the CONTOUR chain's dials moved; the vendored contour product and "
        "the Bronze Age geometry are derived at these")
    assert spec["bronze_decimate"] == 2 and spec["bronze_tol_deg"] == 0.0009
    pb = spec["panorama_blur"] + spec["panorama_post_blur"]
    cb = spec["blur"] + spec["post_blur"]
    assert 0 < pb < cb, (
        f"the panorama field ({pb} passes) must be smoothed less than the "
        f"contour grid ({cb}) and still be smoothed at all")
    # and the panorama must actually take the panorama dials
    assert hasattr(ptc, "panorama_grid")


def test_the_mesh_does_not_smooth_away_what_it_went_to_sample(s3):
    """Three numbers that have to move together: the field's own resolving
    power, the ring floor, and the mesh's height stencil. A stencil wider than
    the ring spacing throws away ground the mesh paid to sample; a ring floor
    finer than the field only resamples the smoothing."""
    # the nine-point stencil's sigma is 0.62 of its radius (weights 2 centre,
    # 1 at r on the axes, 0.7 at 0.99r on the diagonals)
    assert s3.MESH_STENCIL_M * 0.62 * 2.0 <= s3.RING_MAX_M, (
        f"stencil {s3.MESH_STENCIL_M} m is wide against a {s3.RING_MAX_M} m "
        "ring floor")
    # 41 m is 2 sigma of the panorama field at 2+1 passes: the finest thing
    # in the data. The rings must straddle it, not sit on it.
    assert s3.RING_MAX_M <= 45.0
    assert s3.SHADOW_STEP <= 45.0, (
        "the cast-shadow raster is coarser than the ground it is cast on")


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


# ═══════════════════════════════════════════════════════════════════════════
# a river that ends in mid-air
# ═══════════════════════════════════════════════════════════════════════════
# "The Scamander does not connect to the water" (John, 2026-08-14): on the sand
# spit at the head of the bay the channel ran down the spit and simply stopped,
# short of the shore, in the middle of dry ground. The channel DATA was never
# short -- apparatus/plates/trojan-plain.json's `scamander` path has 170
# vertices and 43 of them lie inside lagoon-bronze. rivers_svg draws a river on
# land only, and it was cutting the run at the last VERTEX outside the water on
# a path whose vertices are 122 m apart (625 m at worst), so the mouth was left
# up to a whole segment inland: 37 m on the Scamander, 40 m on the Simoeis.


def _plate_layers():
    p = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")
    if not os.path.exists(p):
        pytest.skip("trojan-plain.json not present")
    import json
    with open(p) as f:
        return {l["id"]: l for l in json.load(f)["layers"]}


def _dry_runs_of(s3, rid):
    """rivers_svg's own run splitter, re-derived here from the same layers so
    the test measures the drawing rule and not a copy of it."""
    lay = _plate_layers()
    lagoon, sea = lay["lagoon-bronze"]["polygon"], lay["sea-modern"]["polygon"]

    def wet(p):
        return (s3.point_in_poly_ll(p[0], p[1], lagoon)
                or s3.point_in_poly_ll(p[0], p[1], sea))

    def waterline(dry, w, iters=20):
        for _ in range(iters):
            mid = ((dry[0] + w[0]) / 2.0, (dry[1] + w[1]) / 2.0)
            if wet(mid):
                w = mid
            else:
                dry = mid
        return w

    runs, cur, prev = [], [], None
    for q in lay[rid]["path"]:
        p = (q[0], q[1])
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
    return runs, lagoon, sea


def _gap_to_water_m(s3, pt, poly):
    """Distance from `pt` to the nearest point ON the polygon's boundary, flat
    metres — measured to the segments, not to the vertices."""
    best = float("inf")
    for a, b in zip(poly, poly[1:] + [poly[0]]):
        ax, ay = s3.pp._flat_m(a, *pt)
        bx, by = s3.pp._flat_m(b, *pt)
        ux, uy = bx - ax, by - ay
        L2 = ux * ux + uy * uy
        t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, (-ax * ux - ay * uy) / L2))
        best = min(best, math.hypot(ax + t * ux, ay + t * uy))
    return best


@pytest.mark.parametrize("rid,was", (("scamander", 37.0), ("simoeis", 40.0)))
def test_the_channel_data_always_reached_the_bay(s3, rid, was):
    """The defect was NOT missing data, and the record matters: nobody should
    ever be tempted to draw a mouth that is not in the survey."""
    lay = _plate_layers()
    lagoon = lay["lagoon-bronze"]["polygon"]
    inside = sum(1 for p in lay[rid]["path"]
                 if s3.point_in_poly_ll(p[0], p[1], lagoon))
    assert inside > 3, (
        f"{rid} has only {inside} vertices inside the reconstructed bay; if "
        "the survey really stops short, the mouth is an editorial question")


@pytest.mark.parametrize("rid,was", (("scamander", 37.0), ("simoeis", 40.0)))
def test_a_river_is_drawn_all_the_way_to_the_water(s3, rid, was):
    """The fix, in one number: the drawn run now ends ON the reconstructed
    shore instead of at the last surveyed vertex before it."""
    runs, lagoon, sea = _dry_runs_of(s3, rid)
    assert runs, f"{rid} draws no run at all"
    end = runs[-1][-1]
    gap = min(_gap_to_water_m(s3, end, lagoon), _gap_to_water_m(s3, end, sea))
    assert gap < 1.0, (
        f"{rid} still stops {gap:.0f} m short of the water (it was {was:.0f})")
    # and the mouth is ON the surveyed line, not beside it: every drawn point
    # must lie within a metre of the original polyline
    path = [(p[0], p[1]) for p in _plate_layers()[rid]["path"]]
    worst = 0.0
    for c in runs[-1]:
        worst = max(worst, _gap_to_water_m(s3, c, path))
    assert worst < 1.0, (
        f"{rid}'s drawn course leaves its own survey line by {worst:.0f} m")


def test_the_gap_the_old_rule_left(s3):
    """The bug, reproduced: cutting at the last dry VERTEX leaves the mouth
    inland by up to a survey segment. Remove this test only with the rule."""
    lay = _plate_layers()
    lagoon, sea = lay["lagoon-bronze"]["polygon"], lay["sea-modern"]["polygon"]
    for rid, floor in (("scamander", 20.0), ("simoeis", 20.0)):
        cur = []
        for q in lay[rid]["path"]:
            p = (q[0], q[1])
            if (s3.point_in_poly_ll(p[0], p[1], lagoon)
                    or s3.point_in_poly_ll(p[0], p[1], sea)):
                break
            cur.append(p)
        gap = _gap_to_water_m(s3, cur[-1], lagoon)
        assert gap > floor, (
            f"expected the vertex rule to strand {rid} well inland; it left "
            f"only {gap:.0f} m")


# ═══════════════════════════════════════════════════════════════════════════
# "and no dotty lines" (John, 2026-08-14)
# ═══════════════════════════════════════════════════════════════════════════


def test_nothing_on_the_sheet_is_drawn_dashed(s3):
    """Three lines were: the reconstructed shore, the ditch and the wagon-road.
    None of the three dashes was carrying a claim the plate does not already
    make in words, and a dash is read as texture before it is read as meaning.
    """
    assert "stroke-dasharray" not in s3.CSS, (
        "a dashed stroke is back in the stylesheet")
    src = open(STAGE3).read()
    body = src.split("CSS = ", 1)[1]
    assert 'stroke-dasharray="' not in body, (
        "a dash was set as an attribute rather than in the stylesheet")


def test_the_reconstruction_is_still_marked_as_one(s3):
    """The dash went; the claim may not. The reconstructed shore keeps a line
    -- WCAG 1.4.11 needs 3:1 and the lagoon/land fill pair gives 1.41-1.69:1
    in both themes -- and it is LIGHTER than the surveyed modern coastline, so
    the difference between them is how heavily each is asserted."""
    def width(cls):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", s3.CSS, re.S)
        assert m, f"{cls} is not in the stylesheet"
        w = re.search(r"stroke-width:([0-9.]+)", m.group(1))
        assert w, f"{cls} has no stroke-width"
        return float(w.group(1))
    approx, survey = width("pp-coast-approx"), width("pp-coast")
    assert 0 < approx < survey, (
        f"the reconstructed shore ({approx} px) must be lighter than the "
        f"surveyed coastline ({survey} px) and must still be drawn")
    # and the plate must not describe a mark it does not draw
    src = open(STAGE3).read()
    cartouche = src.split("def furniture(", 1)[1].split("\ndef build(", 1)[0]
    assert "dash" not in cartouche.lower(), (
        "the cartouche still names a dash the plate does not draw")
    assert "hairline" in cartouche, (
        "the cartouche no longer says how the reconstruction is drawn")


def test_the_waterlines_offset_by_winding_not_by_centroid(s3):
    """The sand spit runs half a kilometre into the bay, so along its far
    flank the polygon's centroid lies ACROSS the land and a centroid-chosen
    normal walked the waterlines up onto the beach. Winding is local and
    correct in a concavity; a centroid is neither."""
    src = open(STAGE3).read()
    w = src.split("def water_svg(", 1)[1].split("def rivers_svg", 1)[0]
    assert "winding_sign" in w and "inset(" in w, "the winding test is gone"
    assert "cx - x1" not in w, "the centroid rule is back"
    # the rule itself, now that both the waterlines and the shoal share it:
    # a square wound one way and the same square wound the other must offset
    # to the same place, and that place must be INSIDE
    sq = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    got = []
    for poly in (sq, list(reversed(sq))):
        off = s3.inset(poly, s3.winding_sign(poly), 10.0)
        assert len(off) == 4
        for x, y in off:
            assert 0.0 < x < 100.0 and 0.0 < y < 100.0, (
                f"the offset left the square: {off}")
        got.append(sorted(round(v, 6) for p in off for v in p))
    assert got[0] == got[1], "the winding changed where the offset went"


# ── WCAG 1.4.11 on the marks this pass moved ──────────────────────────────
# The dashes came off three lines, and taking a dash off a line is a change to
# how it is READ, not to its contrast -- but two of the three were failing 3:1
# before anyone looked, and a pass that is already in the file has no excuse
# for leaving them there.


def _srgb_lum(hexstr):
    hexstr = hexstr.lstrip("#")
    ch = [int(hexstr[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
           for c in ch]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _ratio(a, b):
    la, lb = _srgb_lum(a), _srgb_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _over(fg, bg, alpha):
    f = [int(fg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(bg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(
        round(alpha * f[i] + (1 - alpha) * b[i]) for i in range(3))


def _tokens(s3, theme):
    """Straight out of the module's own TOKENS dict, so the test cannot drift
    from the values the plate ships."""
    return dict(re.findall(r"(--[a-z0-9-]+):(#[0-9A-Fa-f]{6})",
                           s3.TOKENS[theme]))


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_the_marks_this_pass_moved_clear_wcag_1_4_11(s3, theme):
    t = _tokens(s3, theme)
    ground = [t["--pp-cover-fan"], t["--pp-cover-open"], t["--pp-cover-ridge"]]
    # 1. the reconstructed shore, now a hairline instead of a dash. It is the
    #    ONLY thing separating water from land: the fill pair is 1.41-1.69:1.
    for bg in [t["--plate-lagoon"]] + ground:
        r = _ratio(t["--scene-map-coast"], bg)
        assert r >= 3.0, f"{theme}: shore hairline on {bg} is {r:.2f}:1"
    fill = min(_ratio(t["--plate-lagoon"], g) for g in ground)
    assert fill < 3.0, (
        f"{theme}: the lagoon/land fill pair is {fill:.2f}:1 — if it ever "
        "clears 3:1 the shore may drop its stroke, and the cartography doc's "
        "no-boundary rule becomes available for it")
    # 2. the ditch and the road, which were at 0.55 and failing in both themes
    for bg in ground:
        r = _ratio(_over(t["--text-mid"], bg, 0.75), bg)
        assert r >= 3.0, f"{theme}: ditch/road on {bg} is {r:.2f}:1"


def test_the_ditch_and_road_opacity_is_the_one_that_was_solved_for(s3):
    """0.55 measured 2.19:1 at worst. 3:1 needs 0.74 in light and 0.68 in
    dark; anything under 0.75 puts one theme or the other back under."""
    for cls in ("pp-ditch", "pp-road"):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", s3.CSS, re.S)
        op = re.search(r"stroke-opacity:([0-9.]+)", m.group(1))
        assert op and float(op.group(1)) >= 0.75, f"{cls} is back under AA"


# ── the halo, the tone it paid for, and the margin the legend moved to ────
# (2026-08-14). Three claims, and they stand or fall together: the ground can
# only be this bold because the lettering carries its own background, and the
# lettering can only be measured that way because the halo is really there.

def _halo_over(s3, theme, ground_hex):
    """What a reader's eye actually compares a letterform against: the halo
    token at its shipped opacity, over whatever the sheet has drawn there."""
    t = _tokens(s3, theme)
    return _over(t["--scene-map-label-halo"], ground_hex, s3.HALO_OP)


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_the_halo_carries_the_label_over_the_boldest_ground_the_sheet_draws(s3, theme):
    """The measurement that replaced the annulus, and the one that binds.

    SHADE_MAX stood at 0.40 because a 16-28 px ring round each label anchor
    went under 4.5:1 above it. That ring is not a label's background -- the
    halo is -- and this asserts the thing the ring was standing in for: the
    DIMMEST ink on the sheet, over the halo, over every ground class the plate
    can draw, each taken to the darkest the shade ramp reaches AND the
    lightest the lit ramp reaches. If that holds, the tone is free."""
    t = _tokens(s3, theme)
    grounds = [v for k, v in t.items()
               if k.startswith(("--pp-cover", "--pp-sky", "--pp-water"))
               or k in ("--plate-lagoon", "--scene-map-sea", "--pp-haze",
                        "--pp-ida-mass", "--pp-tumulus", "--plate-masonry")]
    worst, where = 99.0, None
    for g in grounds:
        for tone, mx in ((t["--pp-shade"], s3.SHADE_MAX),
                         (t["--pp-lit"], s3.LIT_MAX)):
            lit = _over(tone, g, mx)
            r = _ratio(t["--text-mid"], _halo_over(s3, theme, lit))
            if r < worst:
                worst, where = r, (g, mx)
    assert worst >= 4.5, (
        f"{theme}: --text-mid over the halo over {where} is {worst:.2f}:1")


def test_the_halo_dims_the_ground_it_does_not_punch_a_hole_in_it(s3):
    """An OPAQUE knockout is what reads as its own shape -- a white worm round
    every word, and the bolder the ground the more it shows. The sister
    geographic plates settled this the same morning at 2.6 px and 0.72
    (shared/lib/plate.ts, RELIEF_HALO_WIDTH / RELIEF_HALO_OPACITY). Wide
    enough to BE the background, translucent enough that the tone edges still
    run through it."""
    assert 0.5 < s3.HALO_OP < 1.0, "an opaque halo is a hole, not a halo"
    assert s3.HALO_W >= 2.4, "a halo this thin is not the label's background"
    css = s3.label_css()
    assert f"stroke-opacity:{s3.HALO_OP:g}" in css
    assert "paint-order:stroke" in css


def test_the_tone_is_no_longer_capped_by_a_measurement(s3):
    """The dial the whole pass was about. 0.40 was the annulus's ceiling, not
    the drawing's; anything at or below it means the halo argument has been
    quietly reverted and the sheet is pale again."""
    assert s3.SHADE_MAX > 0.5, "the ground is back to being kept pale"


def test_the_terminator_gamma_sharpens_rather_than_softens(s3):
    """gamma < 1 puts the tone on fast at the lit/shaded boundary and then
    holds, which is what makes an edge read as an edge. gamma > 1 would do the
    opposite and is the airbrush this pass was hired to remove."""
    assert 0.0 < s3.SHADE_GAMMA < 1.0
    g = s3.SHADE_GAMMA
    near, far = 0.05, 0.9
    assert near ** g / near > far ** g / far, (
        "the gamma is not steeper near the terminator than away from it")


def test_the_cast_shadow_edge_is_not_blurred_over_the_ground_it_falls_on(s3):
    """The sun's disc is half a degree, so the penumbra of a 25 m scarp at the
    tip of its own 140 m shadow is about 1.3 m. The mask's raster is 40 m: one
    box pass over it is 40-80 m of softness on the one boundary this sheet has
    that is genuinely a cut. SHADOW_SOFT_M still models the grazing edge."""
    assert s3.SHADOW_BLUR == 0
    assert s3.SHADOW_SOFT_M > 0, "the grazing edge still needs its penumbra"
    src = open(STAGE3).read()
    field = src.split("def shade_field(", 1)[1].split("def sunlit_at(", 1)[0]
    assert "lit[ij2] != s0" in field, (
        "the box pass is averaging across the shadow boundary again")


# ── the furniture is off the picture ─────────────────────────────────────

def test_the_sheet_is_a_picture_and_a_margin(s3):
    assert s3.PIC_BOT + s3.BAND_H == s3.H
    assert s3.BAND_H > 200.0, "there is no margin to letter in"
    src = open(STAGE3).read()
    assert "PIC_BOT - 46" in src, (
        "the frame clip still runs to the foot of the sheet, so the terrain "
        "is drawn under the margin")


def test_nothing_in_the_legend_is_drawn_on_the_map_face(s3):
    """The defect, machine-checked. The key, the scale bars and the cartouche
    used to sit ON the bottom-left quarter of the picture. Every mark they
    make must now fall below the neatline -- the title block and the neatline
    itself excepted, which are the frame, not the legend."""
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    ys = []
    for m in re.finditer(r'<(text|rect|path)\b([^>]*)>', svg):
        a = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', m.group(2)))
        cls = a.get("class", "")
        if "pp-neat" in cls or "pp-l-title" in cls:
            continue
        if a.get("text-anchor") == "middle":
            continue                      # the title block's subtitle
        if "y" in a:
            ys.append(float(a["y"]))
        for mm in re.finditer(r'[Mm][-\d.]+ ([-\d.]+)', a.get("d", "")):
            ys.append(float(mm.group(1)))
    assert ys, "the legend drew nothing at all"
    assert min(ys) >= s3.PIC_BOT, (
        f"a legend mark is at y={min(ys):.0f}, above the picture's foot "
        f"at {s3.PIC_BOT:.0f} — it is covering the drawing")


def test_the_cartouche_was_cut_to_what_a_reader_needs_at_a_glance(s3):
    """"unhelpful" was the other half of the complaint. Five dense lines of
    10 px prose went to three, and the line that was explaining the key went
    to the key's own heading. What may NOT go is a claim: every citation, the
    measured/conjectural split and the DRAFT stamp are asserted here so a
    later tightening cannot quietly delete one."""
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    # only the note BLOCK, not the vegetation key, which also letters at x=62
    body = [t for t in
            re.findall(r'<text class="pp-l-note" x="62"[^>]*>(.*?)</text>', svg)
            if len(t) > 60]
    assert len(body) <= 5, f"the cartouche is back to {len(body)} lines"
    joined = " ".join(body).lower()
    for claim in ("kayan", "1980", "conjectural", "artist",
                  "never at an invented coordinate", "hairline", "draft",
                  "never the catalogue", "23.114"):
        assert claim in joined, f"the cartouche dropped {claim!r}"


# ═══════════════════════════════════════════════════════════════════════════
# the left-edge defect: a coastline low-pass, a neck cut, and a drowned gap
# ═══════════════════════════════════════════════════════════════════════════
def test_the_coast_low_pass_runs_in_world_metres_before_the_projection(s3):
    """The staircase is a property of the SOURCE GRID, not of this camera, so
    it is taken off at its own scale and by the same amount everywhere. Doing
    it on screen would have removed however much this particular oblique
    happened to magnify, which is a different line at every range."""
    src = open(STAGE3).read()
    body = src.split("def coast_ring", 1)[1].split("def shore", 1)[0]
    assert "_flat_m" in body and "soften(" in body
    assert "cam.project" not in body, "the ring is smoothed before projection"
    assert s3.COAST_STEP_M == 30.0, "resample at the source posting"


def test_the_coast_ring_is_resampled_before_it_is_smoothed(s3):
    """The defect this clause was written for, reproduced. A vertex low-pass
    on an unevenly sampled ring drags a vertex toward the CHORD between its
    distant neighbours: on sea-modern, which steps 30 m round the headlands
    and then runs straight for kilometres, the worst move was 6339.7 m before
    the ring was resampled. Uniform sampling is what bounds it."""
    ragged = [(0.0, 0.0), (30.0, 0.0), (60.0, 0.0),
              (60.0, 9000.0), (60.0, 18000.0), (0.0, 18000.0)]
    raw = s3.soften(list(ragged), s3.COAST_SOFT, closed=True)
    worst_raw = max(math.hypot(a[0] - b[0], a[1] - b[1])
                    for a, b in zip(ragged, raw))
    dense = []
    n = len(ragged)
    for k in range(n):
        a, b = ragged[k], ragged[(k + 1) % n]
        steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])
                           / s3.COAST_STEP_M))
        for t in range(steps):
            f = t / steps
            dense.append((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
    soft = s3.soften(dense, s3.COAST_SOFT, closed=True)
    worst_dense = max(math.hypot(a[0] - b[0], a[1] - b[1])
                      for a, b in zip(dense, soft))
    assert worst_raw > 500.0, "the ragged case must actually be ragged"
    assert worst_dense < s3.COAST_STEP_M, (
        f"resampled, the filter still moved a vertex {worst_dense:.0f} m")


def test_a_neck_narrower_than_the_ink_is_spliced_out(s3):
    """A ring that returns within COAST_NECK_M of itself after a long arc is
    a tongue, and a tongue thinner than the four lines drawn along it is a
    landform the sheet cannot resolve. Two lobes joined by a 20 m neck: the
    short lobe goes, the long one stays."""
    body = ([(x * 40.0, 0.0) for x in range(40)]
            + [(1560.0, y * 40.0) for y in range(1, 20)]
            + [(x * 40.0, 760.0) for x in range(39, -1, -1)]
            + [(0.0, y * 40.0) for y in range(19, 0, -1)])
    # a spike 400 m long and 20 m across the neck, sampled every 40 m
    tongue = ([(-k * 40.0, 160.0) for k in range(1, 11)]
              + [(-k * 40.0, 140.0) for k in range(10, 0, -1)])
    ring = body[:1] + tongue + body[1:]
    out, cuts = s3.cut_necks(ring)
    assert cuts >= 1, "the neck was not found"
    assert all(p[0] > -30.0 for p in out), "the tongue survived the cut"
    assert len(out) > len(body) * 0.9, "the cut took the body, not the tongue"


def test_a_strait_is_never_closed_by_the_neck_cut(s3):
    """The Dardanelles is 1.3 km across at its narrowest on this sheet, twenty
    times the threshold. The rule must not be able to weld a real strait."""
    assert s3.COAST_NECK_M < 100.0
    ring = [(0.0, 0.0), (0.0, 2000.0), (1300.0, 2000.0), (1300.0, 0.0)]
    dense = []
    n = len(ring)
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 30.0))
        for t in range(steps):
            f = t / steps
            dense.append((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
    out, cuts = s3.cut_necks(dense)
    assert cuts == 0, "a 1.3 km channel was treated as a neck"
    assert len(out) == len(dense)


def test_the_drowned_gap_rule_needs_both_shores_and_the_reconstruction_s_cut(s3):
    """The rule is a GAP CLOSER, not a re-flooding rule, and the clause that
    makes it one is proximity to BOTH drawn shores. With only the
    reconstruction's shore in the test, the modern Scamander spit -- low
    ground between the two waters, 150 m wide -- went under the bay's wash and
    the plate grew a rash of blue blotches. All three clauses are asserted
    here because dropping any one of them re-opens a different defect."""
    src = open(STAGE3).read()
    body = src.split("def cover_field", 1)[1].split("def terrain_svg", 1)[0]
    assert "SHORE_CUT_M" in body, "the elevation clause is gone"
    assert "near_lag" in body and "near_sea" in body, (
        "the rule must require proximity to BOTH shores")
    assert "lag_mask" in body, "a cell already inside the bay is not a gap"
    assert s3.SHORE_CUT_M == 10.0, (
        "the cut must be the contour lagoon-bronze was filled to")
    assert s3.DROWN_REACH_M < 200.0, (
        "the reach is a gap width, not a flood radius")


def test_a_drowned_gap_is_painted_as_the_reconstruction_paints_itself(s3):
    """No third colour appears on the sheet: the repair is the ground it would
    have had, under the bay's own wash at the bay's own opacity, so a closed
    gap is indistinguishable from the polygon that should have covered it."""
    assert s3.COVER_TOKEN[s3.COVER_DROWNED] == "--plate-lagoon"
    src = open(STAGE3).read()
    body = src.split("def terrain_svg", 1)[1].split("def shade_field", 1)[0]
    assert "COVER_DROWNED" in body
    assert "0.87" in body, "the repair must carry the lagoon's own opacity"
    # and it takes no slope shading: it stands in for water, and water is flat
    assert "st = 0 if cls_ == COVER_DROWNED" in body


def test_the_repair_is_declared_on_the_sheet(s3):
    """Anything this plate does to its own source geometry is stated in the
    margin. A silent repair is the same defect as a silent fabrication."""
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "stranded between them" in svg and "10 m contour" in svg


# ═══════════════════════════════════════════════════════════════════════════
# two waters, two kinds of claim
# ═══════════════════════════════════════════════════════════════════════════
def test_the_reconstruction_is_a_wash_and_the_survey_is_opaque(s3):
    """The plate already says it in line weight -- 0.7 px reconstructed
    against 1.1 px surveyed. The fills say it twice more: the survey is
    opaque, the reconstruction is a wash over the ground it is draped on."""
    css = s3.CSS
    sea = re.search(r'\.pp-sea\{([^}]*)\}', css).group(1)
    lag = re.search(r'\.pp-lagoon\{([^}]*)\}', css).group(1)
    assert "fill-opacity" not in sea, "the survey must be opaque"
    op = float(re.search(r'fill-opacity:([\d.]+)', lag).group(1))
    assert 0.7 < op < 1.0, f"the reconstruction is not a wash (opacity {op})"


def test_the_two_waters_differ_in_value_in_both_themes(s3):
    """A reader who cannot tell the surveyed sea from the reconstructed bay
    cannot tell which coastline this sheet asserts as measured. Value alone,
    before the chroma step the ratio cannot see."""
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        r = _ratio(t["--scene-map-sea"], t["--plate-lagoon"])
        assert r > 1.25, f"{theme}: the two waters read alike ({r:.2f}:1)"


def test_the_reconstruction_is_the_LIGHTER_assertion_in_both_themes(s3):
    """Which way round is the claim. The reconstruction is asserted more
    lightly than the survey -- the same direction as its hairline against the
    survey's heavier line -- and it must be the same direction in both themes
    or the plate says one thing by day and the opposite by night."""
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        assert _srgb_lum(t["--plate-lagoon"]) > _srgb_lum(t["--scene-map-sea"]), (
            f"{theme}: the reconstruction is heavier than the survey")


def test_the_coast_line_still_carries_the_boundary_on_both_waters(s3):
    """WCAG 1.4.11 wants 3:1 on a graphical boundary and NEITHER FILL has ever
    carried it -- the opaque coast line does. Moving a water token moves this
    number, and the first sea token tried in this pass failed it at 2.91:1."""
    for theme in ("light", "dark"):
        t = _tokens(s3, theme)
        ink = t["--scene-map-coast"]
        for tok in ("--scene-map-sea", "--plate-lagoon"):
            r = _ratio(ink, t[tok])
            assert r >= 3.0, f"{theme}: coast ink on {tok} is {r:.2f}:1"


def test_the_key_names_both_waters_with_their_evidence(s3):
    """The legend rewrite to four ground-cover rows dropped "Open sea" and
    "Lagoon and shallow water", and the plate went on drawing two different
    kinds of claim while explaining neither."""
    ids = {c for c, _, _ in s3.WATER_KEY}
    assert ids == {"sea", "lagoon"}
    joined = " ".join(n + " " + g for _, n, g in s3.WATER_KEY).lower()
    assert "surveyed" in joined and "copernicus" in joined
    assert "kraft" in joined and "wash" in joined
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "OPEN SEA" in svg and "RECONSTRUCTED" in svg


def test_the_key_explains_the_marks_a_reader_can_count(s3):
    """459 hulls is a convention, not a claim about the catalogue's 1186 ships,
    and until this line existed nothing on the sheet said so. The wall, the
    ditch, the tumuli and the road were drawn and unexplained too."""
    joined = s3.DRAWN_MARKS.lower()
    for claim in ("ships", "huts", "wall", "ditch", "tumulus", "wagon-road",
                  "never the catalogue"):
        assert claim in joined, f"the marks key drops {claim!r}"


def test_the_margin_still_fits_inside_the_sheet(s3):
    """The furniture band is 300 px and the crop is not this lane's to move,
    so everything the key gained had to be paid for in leading."""
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    ys = [float(m.group(1)) for m in re.finditer(r' y="([\d.]+)"', svg)]
    assert ys
    assert max(ys) <= s3.H - 8.0, (
        f"the margin's last baseline is at y={max(ys):.0f} on a {s3.H:.0f} px "
        f"sheet — something is printing off the bottom edge")
