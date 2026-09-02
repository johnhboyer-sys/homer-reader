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
            "pp-ida-wood", "pp-tumulus")}
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
            if name in ("pp-ida-wood", "pp-tumulus"):
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


def test_ida_is_coloured_as_a_wooded_mountain_and_planted_with_nothing(s3):
    """THIS TEST REPLACES ONE THAT ASSERTED THE OPPOSITE, and the replacement is
    the point. The old claim was "attested, lettered, and not drawn", reasoning
    that a 20 m tree at 66 km behind 0.73 of haze is a tenth of a pixel and that
    no source gives a treeline. Both facts are true and neither bears on what
    the poem says: Il. 23.114-20 has the Achaeans cut δρῦς ὑψικόμους on Ida's
    spurs and 14.287 puts an ἐλάτη περιμήκετος there, and a FORESTED MOUNTAIN
    DOES NOT READ AS TREES AT ANY RANGE -- it reads as a darker, greener mass.
    Tone is the one register the distance leaves open, it places nothing, and it
    needs no treeline. What the old refusal actually shipped was a bare warm tan
    across the whole horizon of the plate, which is what the text denies."""
    src = open(STAGE3).read()
    # the citation travels with the mark, as every other plant's does
    cites = {n: g for n, g in s3.VEG_KEY}
    ida = next(v for k, v in cites.items() if "IDA" in k)
    assert "23.114" in ida and "14.287" in ida
    assert "no treeline" in ida, "the sheet must not imply a treeline it cannot source"
    # the claim is a colour, and it is the mountain's whole fill
    ida_rule = re.search(r"\.pp-ida\{([^}]*)\}", s3.CSS).group(1)
    assert "--pp-ida-wood" in ida_rule
    assert "--pp-ida-mass" not in "".join(s3.TOKENS.values()), (
        "the bare-rock token is gone; nothing may quietly restore it")
    # and it is a GREEN, in both themes
    for theme in ("light", "dark"):
        r, g, b = _parse_tokens(s3.TOKENS[theme])["pp-ida-wood"]
        assert g > r and g > b, f"{theme}: --pp-ida-wood is not a green"
    # nothing is planted on it
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    assert "ida" not in veg.lower(), "nothing is planted on Ida"
    assert "23.114" in s3.COVER_KEY_UNDRAWN, (
        "the sheet must still say why Ida carries no drawn tree")


def test_the_thickets_pitch_is_the_poems_own_density_word(s3):
    """"more vegetation" is not, by itself, a licence to draw more. It is here,
    for exactly one class, because 21.352 says τὰ περὶ καλὰ ῥέεθρα ἅλις ποταμοῖο
    πεφύκει -- the assemblage grew ἅλις, IN ABUNDANCE, about the river's streams.
    ἅλις is a density word in the text's own voice, so the clump pitch is the one
    number on this sheet that more marks make MORE faithful, not less. The offset
    is untouched, because that one the poem does not give."""
    assert s3.BANK_STEP_M < 96.0, "the fringe was set thinner than ἅλις asks for"
    cites = {n: g for n, g in s3.VEG_KEY}
    assert "ἅλις" in cites["RIVERBANK THICKET"] and "21.350" in cites["RIVERBANK THICKET"]
    assert s3.BANK_OFFSET_M == 26.0, (
        "the WIDTH is an artist's convention and is not this lane's to move")


def test_no_reed_bed_grows_on_the_wet_delta(s3):
    """THE ONE THING ASKED FOR THAT THE EVIDENCE REFUSES. Il. 21.351 does name
    θρύον and κύπειρον, and a reed MASS at 8 km is drawable where a single stem
    is not -- but GROUND-COVER-TROJAN-PLAIN.md §5.8 forbids this flora "spread
    broadcast across the whole swamp rather than confined to the river's
    immediate margin", on the strength of 21.352, and §5.2 forbids reed dressing
    outright. 21.351 is the same sentence as 21.352: the locative that licenses
    the thicket is the locative that denies the delta. So the wet delta stays a
    wash, it gains vegetation only where the drawn courses cross it, and the
    sheet says so."""
    src = open(STAGE3).read()
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    for word in ("swamp", "marsh", "reed", "SWAMP_LAYER"):
        assert word not in veg.lower().replace("swamp_layer", ""), (
            f"{word!r} appears in the placement pass: something grows on the delta")
    assert "Reeds over the wet delta" in s3.COVER_KEY_UNDRAWN
    assert "21.352" in s3.COVER_KEY_UNDRAWN, (
        "the refusal must carry the line it rests on, like every other claim here")


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


def test_the_overview_draws_a_mass_and_the_zoom_draws_its_members(s3):
    """THIS TEST REPLACES ONE THAT PINNED THE DEFECT, and the replacement is
    the point. The old claim was that the overview carries a SUBSET of the
    crowd and the zoom tiers the rest -- fewer marks of the same kind. That is
    still a crowd, and at 800 m up with Ilios 7 km out a crowd is the whole
    problem: an 8 m canopy is under a pixel there, so anything a reader can
    COUNT at 1x is drawing something that cannot be seen ("those look like
    individual trees"; "it looks like stubble on a man's chin" -- John,
    2026-08-14).

    So the two tiers now carry DIFFERENT MARKS, which is what "regenerate, do
    not scale" was always trying to say. The overview gets a mass -- one lobed
    ribbon for the fringe, merged scalloped patches for the cover -- and the
    zoom tier gets the clumps and the tufts that mass stands for. Nothing is
    the same mark at two sizes."""
    src = open(STAGE3).read()
    veg = src.split("def vegetation_svg", 1)[1].split("def camp", 1)[0]
    assert "marks_t1" in veg and "marks_t3" in veg
    # the members are gated to the zoom tier ...
    assert '"tm3"' in veg, "the crowd is never gated to a zoom tier"
    # ... and the overview's own marks step aside there
    assert '"t1-only"' in veg, "the mass is never gated to the overview"
    assert "bank_mass(" in veg and "scrub_mass_svg(" in veg
    assert "tm3" in s3.TIER_CSS[1] and "t1-only" in s3.TIER_CSS[3], (
        "tier 1 must hide the members and tier 3 must hide the mass")
    # deterministic: the same seed gives the same mark every render, so the
    # patch that resolves is the patch that was there
    assert s3._rnd(4, 11) == s3._rnd(4, 11)
    assert s3._rnd(4, 11) != s3._rnd(5, 11)
    assert 0.0 <= s3._rnd(7, 3, 9) < 1.0


def test_the_mass_mark_is_bounded_by_a_foliate_edge_not_by_the_lattice(s3):
    """In the drawn tradition a wood is recognised by its OUTLINE, so the mass
    marks live or die on their boundary. A union of mesh cells is a staircase
    and reads as a region; what makes it read as cover is the scallop laid on
    it, and the offsets have to be hashed or the lobes are a pitch of their
    own."""
    pts = [(0.0, 0.0), (40.0, 0.0), (40.0, 30.0), (0.0, 30.0)]
    d = s3.rel_scallop(pts, 4.0, seed=3, closed=True)
    assert d.startswith("M") and d.endswith("Z")
    assert d.count("q") >= 4, "every segment must bend"
    assert d == s3.rel_scallop(pts, 4.0, seed=3, closed=True)
    assert d != s3.rel_scallop(pts, 4.0, seed=4, closed=True)
    # `fixed` puts the lobes on one side however the run runs, which is what
    # an open canopy edge needs
    up = s3.rel_scallop([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], 3.0, seed=1,
                        closed=False, fixed=(0.0, -1.0))
    assert up and "q" in up and not up.endswith("Z")


def test_the_ridge_covers_density_is_measured_and_leaves_bare_ground(s3):
    """The class is a regional default with no survey behind it and the key
    says so; what this pins is that its DENSITY is not a constant. A constant
    is a pitch, the eye finds a pitch at once, and countable marks follow --
    which is the stubble. Curvature, slope and aspect are all read off the DEM
    the plate already carries, so the patchiness costs no honesty; and the
    floor is as load-bearing as the weights, because without genuinely bare
    ground the stands have nothing to be stands against."""
    src = open(STAGE3).read()
    body = src.split("def scrub_cover", 1)[1].split("\n    def ", 1)[0]
    for term in ("curv", "steep", "face"):
        assert term in body, f"the {term} control is gone"
    assert "elev_smooth" in body, "the controls must come off the DEM"
    # measured over a GROUND radius, never over a mesh cell: the lattice is
    # 20 m near and 300 m far and wider across the view than along it, and a
    # field read on it prints as streaks lying along the rings
    assert "SCRUB_STENCIL_M" in body and s3.SCRUB_STENCIL_M > 0
    assert all(w > 0 for w in (s3.SCRUB_W_CURV, s3.SCRUB_W_SLOPE,
                               s3.SCRUB_W_ASPECT))
    assert s3.SCRUB_BARE > 0.0, "no floor means no bare ground"
    assert s3.SCRUB_MASS_MIN >= s3.SCRUB_BARE
    assert s3.SCRUB_CORE_MIN > s3.SCRUB_MASS_MIN, (
        "the stand must be closed in the middle and open at its margin")


def test_no_stand_of_scrub_may_grow_into_a_forest(s3):
    """The one thing the poem does constrain here. Il. 23.114-20 sends the
    Achaeans twenty-odd km up Ida's spurs with mules to cut δρῦς ὑψικόμους for
    the pyre; men do not haul beams that far past timber, so the ground in this
    frame carries no wood worth felling. Scrub in the ravines is not one and
    may be drawn; a canopy sheet over a whole ridge is, and may not. So an
    oversized merged patch keeps the thin skirt and is refused the closed
    core."""
    src = open(STAGE3).read()
    body = src.split("def scrub_mass_svg", 1)[1].split("\n    def ", 1)[0]
    assert "SCRUB_PATCH_MAX" in body
    assert "23.114" in body, "the refusal must carry the line it rests on"
    assert s3.SCRUB_PATCH_MAX > s3.SCRUB_PATCH_PX2 > 0


def test_the_mass_tokens_stay_darker_than_every_ground_they_lie_on(s3):
    """The mass rule, extended to the mark this pass added. --pp-veg-mass is a
    LIGHTER green than the crown token on purpose -- spread over hillsides at
    two coats the crown colour took the ground under SIGEION and THE SHIPS
    with it, and a label's background is not a drawing's to spend -- but
    lighter may not become light: in both themes it must still read as cover
    ON ground, which means darker than every ground class it can stand on, so
    the tonal rank cannot photo-negative between the themes."""
    for theme in ("light", "dark"):
        t = _parse_tokens(s3.TOKENS[theme])
        mass = _luminance(t["pp-veg-mass"])
        assert mass > _luminance(t["pp-veg"]), (
            f"{theme}: --pp-veg-mass is not lighter than the crown token")
        for name, rgb in _ground_values(s3, theme).items():
            if name in ("pp-ida-wood", "pp-tumulus"):
                continue              # marks, not ground the cover lies on
            assert mass < _luminance(rgb), (
                f"{theme}: --pp-veg-mass is not darker than {name}")
        r, g, b = t["pp-veg-mass"]
        assert g > r and g > b, f"{theme}: --pp-veg-mass is not a green"


def test_ida_is_darker_in_its_folds_and_thinner_toward_its_tops(s3):
    """A forested massif is not one tone. The fold band is read off the SAME
    per-column DEM samples the skyline itself is drawn from -- the running
    local maximum is the summit line, and a column's drop below it is how deep
    a col stands there -- so it places no tree and claims no treeline, which
    is the only register 66 km of air leaves open."""
    src = open(STAGE3).read()
    body = src.split("def ida_folds", 1)[1].split("\n    def ", 1)[0]
    assert "IDA_FOLD_WIN" in body and "IDA_FOLD_K" in body
    assert "pp-ida-fold" in body
    assert s3.IDA_FOLD_WIN >= 1 and s3.IDA_FOLD_K > 0
    for theme in ("light", "dark"):
        t = _parse_tokens(s3.TOKENS[theme])
        assert _luminance(t["pp-ida-fold"]) < _luminance(t["pp-ida-wood"]), (
            f"{theme}: the folds are not darker than the mountain")
        r, g, b = t["pp-ida-fold"]
        assert g > r and g > b, f"{theme}: --pp-ida-fold is not a green"
    # a skyline with no fold in it gets no band at all
    flat = [(float(x), 100.0) for x in range(0, 60)]
    assert s3.Plate.ida_folds(None, flat) == ""


def test_the_key_says_the_density_is_a_drawing_rule_and_not_a_survey(s3):
    """Every other claim on this sheet carries its evidence beside the mark.
    The cover's patchiness is a DRAWING decision taken off measured terrain,
    and the key has to say both halves of that or a reader is entitled to read
    the stands as surveyed vegetation."""
    cites = {n: g for n, g in s3.VEG_KEY}
    scrub = cites["RIDGE SCRUB"]
    assert "no line of the poem" in scrub, (
        "ridge scrub is a regional default and the key must not imply a text")
    for word in ("curvature", "slope", "aspect"):
        assert word in scrub, f"the key does not name the {word} control"
    assert "not a survey" in scrub


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
                        "--pp-ida-wood", "--pp-tumulus", "--plate-masonry")]
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


def test_the_colophon_is_set_to_a_measure_and_keeps_every_claim(s3, restore_camera):
    """THIS TEST REPLACES ONE WHOSE MECHANISM STOPPED MATCHING ITS INTENT, and
    the replacement is the point. The intent was right and is kept: no later
    tightening may quietly drop a claim. The mechanism was "the long <text>
    elements at x=62", which was the same thing as "the note block" only while
    the notes were FULL-WIDTH SINGLE LINES -- which was the defect. Set in
    columns, x=62 is column one, so the old scrape read a fifth of the block
    and would have reported four claims missing that are all still on the
    sheet.

    So the claims are now asserted against the whole margin, wherever it
    chooses to carry them, and the thing that was actually wrong is asserted
    directly: SVG text does not wrap, so every note was one physical line of
    about 380 characters across 2,276 px, five times a readable measure and a
    grey slab with no entry point.

    Pinned to plate B: that is the plate that still draws the camp and the
    plain together, so every claim in this list still belongs on the sheet.
    Plate A's companion-plate camp key is asserted separately."""
    if hasattr(s3, "apply_plate_preset"):
        s3.apply_plate_preset("B")
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    body = re.findall(r'<text class="pp-l-note pp-colophon"[^>]*>(.*?)</text>',
                      svg)
    assert body, "the colophon drew nothing"
    assert max(len(t) for t in body) <= 110, (
        f"the colophon is back to a {max(len(t) for t in body)}-character "
        f"measure: it is not wrapped into columns")
    # a column is only a column if there are several of them, at their own x
    xs = {m.group(1) for m in re.finditer(
        r'<text class="pp-l-note pp-colophon" x="([\d.]+)"', svg)}
    assert len(xs) >= 4, f"the colophon is in {len(xs)} column(s)"
    # every claim, anywhere in the margin -- the key may carry it or the
    # colophon may, but the sheet may not stop saying it
    joined = " ".join(re.findall(r'<text[^>]*>(.*?)</text>', svg)).lower()
    for claim in ("kayan", "1980", "conjectural", "artist",
                  "never at an invented coordinate", "hairline", "draft",
                  "never the catalogue", "23.114"):
        assert claim in joined, f"the margin dropped {claim!r}"


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
    so everything the key gained had to be paid for in leading.

    THE BAR IS THE NEATLINE'S OWN INSET, not 8 px. It was 8, which is the
    number that let the shipped sheet put its last baseline at y=1341 of 1350
    and pass: 9 px of air under a 10 px face with descenders, while every
    other edge on the plate holds 16. A test set to the symptom licenses the
    symptom. The block is anchored to the foot now (see furniture), so this
    holds by construction and fails loudly if that anchoring is undone."""
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    ys = [float(m.group(1)) for m in re.finditer(r' y="([\d.]+)"', svg)]
    assert ys
    assert max(ys) <= s3.H - s3.NEAT_M, (
        f"the margin's last baseline is at y={max(ys):.0f} on a {s3.H:.0f} px "
        f"sheet — it is inside the {s3.NEAT_M:g} px the neatline holds")


# ═══════════════════════════════════════════════════════════════════════════
# tier 1, and the ground the plate exists to show
# ═══════════════════════════════════════════════════════════════════════════

def _tier_of_puts(src):
    """{waypoint id: tier} for every put() call in build()."""
    body = src.split("def build(", 1)[1]
    return {m.group(1): int(m.group(2)) for m in
            re.finditer(r'put\("([a-z\-]+)",\s*-?[\d.]+,\s*-?[\d.]+,\s*'
                        r'"[a-z\-]+",\s*(\d)', body)}


def test_the_battlefield_is_lettered_on_the_ground_and_not_only_in_the_legend(s3):
    """The key has always said "dry delta fan -- the battlefield (Kayan 2002)",
    so the sheet knew the one fact about that surface a reader of the Iliad
    needs and said it in a swatch caption. It is on the ground now.

    THE REGISTER IS KAYAN'S AND THE KEY SAYS SO. He makes the correlation in his
    own voice -- "Characteristics of the surface recall Homer's descriptions of
    the battlefield: a sand-covered and dusty plain ... there is no need to look
    for a battlefield in the distance" (Kayan 2002, 1003) -- so this is a
    geologist's reading of a measured surface, not a name the poem gives the
    ground, and the key must not let it read as one."""
    src = open(STAGE3).read()
    body = src.split("def build(", 1)[1]
    assert "THE BATTLEFIELD" in body
    # region lettering: letterspaced caps across an unbounded tract, no pin
    assert re.search(r'pp-l-region[^>]*>THE BATTLEFIELD', body), (
        "the battlefield must be lettered in the region manner, not pinned")
    # placed ON its own class, by the class's own cells -- never at a constant
    assert "cover_centre(COVER_FAN" in body
    # tier 1: its own group carries no tier class, so it is in the overview
    grp = body.rsplit("THE BATTLEFIELD", 1)[0].rsplit("L.append(", 1)[1]
    assert "<g>" in grp and 'class="tm' not in grp, (
        "the battlefield may not be gated behind a zoom tier")
    fan = next(g for c, n, g in s3.COVER_KEY if c == s3.COVER_FAN)
    assert "Kayan 2002" in fan and "BATTLEFIELD" in fan
    assert "not the poem" in fan, (
        "the key must not let a geologist's identification read as the poem's "
        "own name for the ground")


def test_tier_one_letters_the_named_geography_and_leaves_the_waypoints_to_tier_two(s3):
    """Tier 1 carries what ORIENTS: the city, the bay, the two rivers, the two
    headlands the camp's own ends are measured against, the mountain, the fleet,
    and the ground they fought over. Tier 2 keeps the poem's fine waypoints and
    everything conjectural in position. The plate is a picture before it is an
    index, so this is a bounded list and the test's job is to keep it bounded."""
    tiers = _tier_of_puts(open(STAGE3).read())
    t1 = {k for k, v in tiers.items() if v == 1}
    assert {"ilios", "bay-of-troy", "scamander", "simoeis",
            "sigeion", "rhoiteion"} <= t1
    assert len(t1) <= 8, f"tier 1 is becoming a gazetteer: {sorted(t1)}"
    # what stays at 2 and 3, and why: conjectural in position, or fine detail
    for pid in ("ford-of-the-scamander", "callicolone", "achaean-wall",
                "throsmos", "delta-swamp"):
        assert tiers.get(pid) == 2, f"{pid} belongs at tier 2"
    for pid in ("scaean-gate", "fig-tree", "two-springs-of-scamander",
                "tomb-of-ilos", "wagon-road", "batieia", "wall-of-heracles"):
        assert tiers.get(pid) == 3, f"{pid} belongs at tier 3"


def test_the_tone_washes_close_their_seam_at_the_stratum_join(s3):
    """THE PALE HAIRLINE ACROSS THE FOREGROUND. The cover fills have always
    closed their own seams by stroking a band in its own fill; the washes were
    deliberately not stroked, on the reasoning that a gap between two tones
    reads as the tone between them -- true within a stratum and false across
    one, where the neighbour is bare cover and every nested wash misses the same
    sliver at once. See SHADE_SEAM_W for the elimination that found it.

    Two things are pinned. The wash carries a seam-closing stroke IN ITS OWN
    TONE at its own opacity -- any other colour would be a new mark on the
    sheet. And the stroke stays well under the cover's, because a wide one laps
    the far stratum's surviving wash and prints a DARK line in place of a pale
    one; the cure and the defect are the same knob turned too far."""
    src = open(STAGE3).read()
    shade = re.search(r'out\.append\(f\'<path class="pp-shade".*?\)\n',
                      src, re.S).group(0)
    assert 'stroke="{tone}"' in shade, "the wash has no seam-closing stroke"
    assert 'stroke-opacity="{a:.4f}"' in shade, (
        "the stroke must carry the wash's own opacity, or it prints as a line")
    assert "SHADE_SEAM_W" in shade
    assert 0.0 < s3.SHADE_SEAM_W < 0.5, (
        f"{s3.SHADE_SEAM_W} px of own-tone stroke will overshoot into a dark "
        "seam; measured, 0.7 turns a +26 luminance gap into a -14 one")
    # and the wash edge is generalised no harder than the cover edge it is cut
    # against, which is half of why the gap was 2 px instead of a fraction
    assert s3.SHADE_SIMPLIFY <= 0.7


# ═══════════════════════════════════════════════════════════════════════════
# the ships: the plate is named for them, and they were the weakest thing on it
# ═══════════════════════════════════════════════════════════════════════════
CAMP_MATERIALS = (
    # token, the line it rests on, the Greek that has to appear beside it
    ("pp-hull-side", "9.235", "μέλαιναι"),
    ("pp-hull-prow", "15.693", "κυανόπρῳρος"),
    ("pp-hull-cheek", "2.637", "μιλτοπάρῃοι"),
    ("pp-timber", "24.450", "ἐλάτης"),
    ("pp-thatch", "24.450–51", "ὄροφον"),
)


def test_the_black_ships_stay_the_darkest_thing_on_the_beach(s3):
    """νηυσὶ μελαίνῃσιν (Il. 9.235 = 11.824 = 12.107), machine-checked, and
    it is this plate's oldest bug wearing its third face. Stage 2 keyed hulls
    to --text and the fleet went label-white at night. The fix gave them
    --pp-hull*, but the RIM stayed --pp-hull-edge, which in dark theme is a
    near-cream chosen for the citadel's pale stone — so at 8x the fleet was
    bone-white canoes with cream posts, the lightest marks on the beach, and
    at 1x the overview's rank read as a row of white ticks.

    So: every token the fleet is drawn with — the two fills, the rim, and
    both painted prows — must be darker than every ground class it lies on,
    in BOTH themes. Not just the fill: a mark is as light as its lightest
    part when the part is a stroke on a fifteen-pixel glyph."""
    for theme in ("light", "dark"):
        t = _parse_tokens(s3.TOKENS[theme])
        ground = _ground_values(s3, theme)
        for name in ("pp-hull", "pp-hull-side", "pp-hull-rim",
                     "pp-hull-prow", "pp-hull-cheek"):
            ship_l = _luminance(t[name])
            for gname, rgb in ground.items():
                assert ship_l < _luminance(rgb), (
                    f"{theme}: --{name} (L={ship_l:.4f}) is not darker than "
                    f"{gname} (L={_luminance(rgb):.4f}) — the black ships "
                    "have inverted again")
        # and darker than the camp's own timber and straw, which stand behind
        # them: pitch against fir and cut reed is the tonal fact the poem
        # states, and it is what tells a hull from a hut at plate scale
        for name in ("pp-hull", "pp-hull-side"):
            for lighter in ("pp-timber", "pp-thatch"):
                assert _luminance(t[name]) < _luminance(t[lighter]), (
                    f"{theme}: --{name} is not darker than --{lighter}")


def test_the_fleet_is_never_keyed_to_the_citadels_rim_or_to_ink(s3):
    """The same bug, pinned at the stylesheet instead of at the palette, so
    an edit cannot quietly key a hull back to the token that inverts."""
    css = s3.CSS
    # pp-erma is the props, and it is on this list for the same reason the
    # posts are: a shore under a hull is a piece of the fleet's ink, and a
    # light stroke there would put the beach's lightest mark directly under
    # its darkest fill.
    for cls in ("pp-hull", "pp-hull-side", "pp-post", "pp-post-t1",
                "pp-prow", "pp-prow-miltos", "pp-erma"):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", css)
        assert m, f"{cls} is not in the stylesheet"
        block = m.group(1)
        for bad in ("var(--text)", "var(--text-mid)", "var(--pp-hull-edge)"):
            assert bad not in block, f"{cls} is keyed to {bad}: {block}"


def test_every_material_on_the_beach_carries_its_line(s3):
    """The camp is four materials and the poem names all four. Same rule the
    vegetation key runs on: the mark carries the line that puts it there, in
    the same breath as the mark — so the citation lives in the plate's own
    data and not only in a comment."""
    key = " ".join(n + " " + g for n, g in s3.CAMP_KEY)
    for token, line, greek in CAMP_MATERIALS:
        assert f"--{token}" in s3.TOKENS["light"], f"--{token} has no value"
        assert f"--{token}" in s3.TOKENS["dark"], f"--{token} has no dark value"
        assert line in key, f"the camp key drops the citation {line} for {token}"
        assert greek in key, f"the camp key drops {greek!r} for {token}"
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "THE CAMP" in svg and "THE SHIPS" in svg and "THE HUTS" in svg


def test_the_camp_is_not_built_of_the_citadels_masonry(s3):
    """The huts wore --plate-masonry, the token Ilios's walls and roofs are
    drawn in, and read as terracotta dominoes. Il. 24.450-51 is explicit:
    Achilles' hut is fir timber under thatch mown from the meadow."""
    for cls, tok in (("pp-hut-wall", "--pp-timber"),
                     ("pp-hut-roof", "--pp-thatch")):
        m = re.search(r"\." + cls + r"\{([^}]*)\}", s3.CSS)
        assert m, f"{cls} is not in the stylesheet"
        assert f"fill:var({tok})" in m.group(1), (
            f"{cls} is not keyed to {tok}: {m.group(1)}")
        assert "--plate-masonry" not in m.group(1)


def test_the_overview_draws_a_rank_and_the_zoom_draws_the_fleet(s3):
    """The tier-1 mark was ONE FILLED POLYGON per stretch of beach with a
    zigzag along its seaward edge, and a reader had to ask outright whether
    it was ships or a wall. A solid has no air in it and air between the
    hulls is the only thing that makes a hull a hull.

    What stands there now is a rank: coarser pitch, fewer rows, each hull
    drawn larger — Pope's plate of 1716 draws the beached fleet as one glyph
    repeated at a pitch, which is why his reads at plate scale
    (docs/research/DEPICTIONS-OF-TROY.md). The true fleet is still drawn and
    is what the zoom shows."""
    src = open(STAGE3).read()
    assert "pp-ship-mass" not in src, "the serrated mass is back"
    assert s3.FLEET_T1_PITCH_M > 13.0, "the rank is at the true berth pitch"
    assert s3.FLEET_T1_ROWS < 5, "the rank is as deep as the true fleet"
    assert s3.FLEET_T1_BEAM_K > 1.0 and s3.FLEET_T1_LEN_K > 1.0
    # THE ENLARGEMENT IS ISOTROPIC, and this assertion REPLACES its opposite.
    # The test used to require FLEET_T1_LEN_K > FLEET_T1_BEAM_K, on the
    # argument that a hull seen end-on down this depression loses most of her
    # length and needs it back. The premise is true and measured -- ten metres
    # of depth draws 0.5-1.2 px against 4.0 for ten metres across -- but the
    # remedy was wrong: stretching length x3.4 against beam x2.0 pulls the
    # shape 1.7x along one axis, and what came out was not a ship but a quill.
    # "they look frigging huge relative to everything else" (John), on a glyph
    # measuring 12.7 px -- the bulk was in the anisotropy and the post's
    # stroke, never in the extent. Scale the two together or the mark stops
    # being a ship. The end-on loss is answered by the SIZE of the
    # enlargement, which the key now declares outright.
    assert s3.FLEET_T1_LEN_K == s3.FLEET_T1_BEAM_K, (
        "the overview's enlargement is anisotropic: it makes a quill, not a "
        "ship. Scale length and beam together")
    build = src.split("def build(", 1)[1].split("def emit(", 1)[0]
    assert 'class="t1-only">\' + "".join(s for s in ships_t1' in build, (
        "the rank is not gated to the overview")
    assert 'class="tm2">\' + "".join(s for s in ships' in build, (
        "the true fleet is not gated to the zoom")


def test_the_overview_glyph_never_scales_a_height(s3):
    """The recorded finding, kept: a 4x stem-post reads as a mast. beam_k and
    len_k are a DRAWING convention in the horizontal plane only — deck and
    stem-post stay at their true 2.4 and 6.4 m at every tier, so a glyph and
    a hull throw the same true-length shadow."""
    src = open(STAGE3).read()
    body = src.split("def ship(", 1)[1].split("\ndef hut(", 1)[0]
    for h in ("SHIP_DECK_H", "SHIP_POST_H"):
        for bad in (f"{h} * beam_k", f"{h} * len_k",
                    f"beam_k * {h}", f"len_k * {h}"):
            assert bad not in body, f"the glyph scales a height: {bad}"
    assert s3.SHIP_DECK_H == 2.4 and s3.SHIP_POST_H == 6.4
    # and the shadow is thrown by the TRUE ship, not by the drawn glyph:
    # at the glyph's size it came out bigger and squarer than the hull, and
    # eighty grey slabs with a ship on each is a rank of pallets
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    assert "HULL_SIL_T1" not in camp
    # Both fleets throw the TRUE ship's silhouette, and both throw it from the
    # keel: `lift` is matched on the same call because a shadow that starts at
    # the footprint is the cue that reads as CONTACT, which is what made the
    # hulls look buried. Matched loosely on purpose -- the old exact-literal
    # form broke the moment the lift argument was added, which told us nothing
    # about the drawing.
    calls = re.findall(r"object_shadow\(cam, terr, lat, lon, bearing,\s*"
                       r"HULL_SIL,\s*lift=SHIP_KEEL_H\)", camp)
    assert len(calls) == 2, (
        "both fleets must cast the true hull's silhouette, lifted off the "
        f"sand onto its props; found {len(calls)}")


def test_odysseus_twelve_are_twelve_and_lie_in_the_middle(s3):
    """δυώδεκα μιλτοπάρῃοι (Il. 2.637) is said of Odysseus's contingent and
    of no other in the Iliad, and 8.222-23 puts his own ship ἐν μεσσάτῳ, in
    the very middle, so that he can be heard both ways down the line. The
    count is therefore the one number on this beach that IS a claim, and the
    vermilion is a block in the middle rather than a colour the fleet has."""
    assert s3.ODYSSEUS_TWELVE == 12
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    mil = camp.split("def miltos(", 1)[1].split("\n        true_berths", 1)[0]
    assert "2.637" in mil and "8.222" in mil, (
        "the vermilion block does not carry the lines it rests on")
    assert "med" in mil and "abs(" in mil, (
        "the block is not chosen by distance from the middle of the line")
    assert "miltos(true_berths, ODYSSEUS_TWELVE)" in camp


def test_the_prow_bearing_is_taken_over_a_beach_and_not_over_a_wobble(s3):
    """A rank that fans is not a rank. shore_forward used to return the last
    dry 25 m step and seaward() differentiated it over a 26 m baseline, so a
    single step of that staircase swung a hull's bearing by 44 degrees and
    neighbours in the same row pointed different ways. Invisible at a 2.7 px
    hull; the whole defect at the overview's glyph. προκρόσσας (Il. 14.35)
    is a claim about ORDER, and a drawing either keeps it or does not."""
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    fwd = camp.split("def shore_forward(", 1)[1].split("\n        def ", 1)[0]
    assert "for _ in range(4)" in fwd and "0.5 * (a + b)" in fwd, (
        "the shoreline is still quantised to its 25 m search step")
    sea = camp.split("def seaward(", 1)[1].split("\n        def ", 1)[0]
    assert "range(-5, 6)" in sea, (
        "the shore slope is still taken over one berth's baseline")
    assert "14.35" in sea and "προκρόσσας" in sea


def test_the_huts_are_grounded_at_every_tier_the_huts_are_drawn_at(s3):
    """The huts have always been on at tier 1 — without them the near third
    of the frame is bare ridge — but their shadows sat in the tier-2 group
    with the hulls', so at the overview the whole camp behind the fleet
    floated. It floats hardest now that a hut is pale timber and straw on
    pale ground rather than a near-black box."""
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    assert "hut_sh.append(sd)" in camp, "the huts' shadows are not kept apart"
    build = src.split("def build(", 1)[1].split("def emit(", 1)[0]
    assert '\'<g>\' + "".join(hut_sh) + "</g>"' in build, (
        "the huts' shadows are gated to a tier the huts are not")


# ═══════════════════════════════════════════════════════════════════════════
# ὑψοῦ ἐπὶ ψαμάθοις: the ships stand on the beach, not in it
# ═══════════════════════════════════════════════════════════════════════════
CORPUS = os.path.join(REPO, "build", "dist", "iliad")


def _iliad_line(book: int, n: int):
    """The Greek of one line, straight out of the built corpus. Returns None
    if the corpus is not here -- callers SKIP LOUDLY rather than pass, which
    is the recorded gotcha: a corpus test that quietly returns early is a
    test that has never once run."""
    path = os.path.join(CORPUS, f"book-{book:02d}.json")
    if not os.path.exists(path):
        return None
    import json
    with open(path) as f:
        doc = json.load(f)
    for seg in doc.get("segments", []):
        for ln in seg.get("greek", []):
            if ln.get("n") == n:
                return ln.get("text", "")
    return ""


def test_the_props_are_the_poems_own_and_quoted_from_the_corpus():
    """Il. 1.485-86 is the warrant for the whole ships-on-props fix, so the
    plate's own comment and key must quote what the corpus actually reads and
    not what anybody remembers it reading.

    νῆα μὲν οἵ γε μέλαιναν ἐπ' ἠπείροιο ἔρυσσαν
    ὑψοῦ ἐπὶ ψαμάθοις, ὑπὸ δ' ἕρματα μακρὰ τάνυσσαν

    and 2.154, ὑπὸ δ' ᾕρεον ἕρματα νηῶν, is what fixes the STANDING condition:
    the props come out to launch, so a beached ship is a propped ship."""
    l485, l486 = _iliad_line(1, 485), _iliad_line(1, 486)
    if l485 is None:
        pytest.skip(f"Iliad corpus not built at {CORPUS} — this test needs it")
    assert "ἐπ' ἠπείροιο ἔρυσσαν" in l485 or "ἐπ’ ἠπείροιο ἔρυσσαν" in l485, l485
    assert "ὑψοῦ" in l486 and "ψαμάθοις" in l486, l486
    assert "ἕρματα μακρὰ" in l486, l486
    l154 = _iliad_line(2, 154)
    assert "ἕρματα νηῶν" in l154, l154
    # and the wall goes in at their STERNS, which is what puts the prows
    # seaward and the props under a hull facing the water
    l32 = _iliad_line(14, 32)
    assert "πρύμνῃσιν" in l32 and "τεῖχος" in l32, l32
    # the ranks are the poem's own word, not the drawing's idea
    l35 = _iliad_line(14, 35)
    assert "προκρόσσας" in l35, l35
    src = open(STAGE3).read()
    for cite in ("1.485-86", "2.154"):
        assert cite in src, f"the props are drawn without citing {cite}"
    for greek in ("ὑψοῦ", "ἕρματα", "ψαμάθοις"):
        assert greek in src, f"the plate draws props without {greek} anywhere"


def test_a_hull_has_freeboard_and_never_meets_the_sand(s3):
    """"the ships look like they are buried in the sand at an angle" (John).

    The flank ran from the deck down to h=0, so the hull's outline closed on
    the beach the whole way round and it read as a shape painted on the sand.
    An object with no visible side cannot read as standing on anything -- the
    huts never had the problem because they have 1.8 m of wall. The flank now
    runs from the garboard at SHIP_KEEL_H to the gunwale at SHIP_DECK_H, and
    NO height is stretched to buy it: the same true 2.4 m is divided into the
    part that is hull and the part that is air under her."""
    assert 0.0 < s3.SHIP_KEEL_H < s3.SHIP_DECK_H, (
        "the keel is on the sand or above the deck")
    assert s3.SHIP_DECK_H - s3.SHIP_KEEL_H >= 1.2, (
        "less than 1.2 m of freeboard is not a hull side a reader can see")
    assert 0.0 < s3.SHIP_KEEL_V < 1.0, "the garboard is outboard of the gunwale"
    src = open(STAGE3).read()
    body = src.split("def ship(", 1)[1].split("\ndef hut(", 1)[0]
    assert "SHIP_KEEL_V, SHIP_KEEL_H)" in body, (
        "the hull's flank no longer runs to the garboard")
    assert "+ v * 0.8, 0.0)" not in body, "the flank runs to the sand again"
    # the true heights are untouched, which is the standing finding
    assert s3.SHIP_DECK_H == 2.4 and s3.SHIP_POST_H == 6.4
    # and the props stay UNDER her: raked outboard of the gunwale they read
    # as legs, and a rank of them as a column of beetles
    assert s3.SHIP_PROP_V < 1.0, (
        "the props rake outside the hull's own silhouette — they draw as legs")


def test_the_hulls_shadow_starts_at_the_keel_so_daylight_runs_under_her(s3):
    """The cue that says CONTACT WITH THE GROUND is shade hard against an
    object's outline all the way round, and the old shadow was exactly that:
    the convex hull of the deck outline's FEET and their shadow points. A ship
    0.9 m up on her ἕρματα casts from the keel, and at this plate's 9.9-degree
    sun that throws the near edge of the shade about five metres clear."""
    assert s3.LIGHT_ALT < 15.0, "the sun moved; the lit gap is a low-sun effect"
    gap = s3.SHIP_KEEL_H / math.tan(math.radians(s3.LIGHT_ALT))
    assert gap > 3.0, (
        f"the props lift her {s3.SHIP_KEEL_H} m and the shade only clears "
        f"{gap:.1f} m — no daylight under the hull")
    src = open(STAGE3).read()
    sh = src.split("def object_shadow(", 1)[1].split("\n# ", 1)[0]
    assert "lift=0.0" in sh, "object_shadow has no lift, so nothing stands off"
    assert "sun_offset(lift)" in sh, "the lift is not thrown down-sun"
    # a hut SITS on the ground and must keep its footprint: lift defaults to 0
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    hut_call = re.search(r"object_shadow\([^)]*HUT_SIL[^)]*\)", camp)
    assert hut_call and "lift" not in hut_call.group(0), (
        "a hut has been lifted off the ground; only ships stand on props")


def test_no_hull_is_berthed_with_its_forefoot_in_the_water(s3):
    """A hull straddling the waterline reads as afloat or half-launched, which
    is the opposite of a fleet hauled up ὑψοῦ ἐπὶ ψαμάθοις and shored for ten
    years. The berth's anchor is her STERN and she runs forward along the
    SHORE NORMAL, not the camera's heading, so the clearance has to be tested
    at the forefoot -- which both advances toward the water and slides along
    the beach to a lateral whose waterline is somewhere else."""
    assert s3.DRY_MARGIN_M > 0.0, "no sand is required between hull and water"
    src = open(STAGE3).read()
    camp = src.split("def camp(", 1)[1].split("def waypoints", 1)[0]
    af = camp.split("def afloat(", 1)[1].split("\n        def ", 1)[0]
    assert "DRY_MARGIN_M" in af, "the clearance test admits a hull to the edge"
    assert af.count("for u, v in") == 1 and "reach_m * 0.80" in af, (
        "only one point of the bow is tested; a bow is not a needle")
    # and it is actually APPLIED, at both fleets, with each one's own reach
    assert "if afloat(f, lateral, bearing, reach_m):" in camp, (
        "afloat() is defined and never called")
    assert "reach_m=24.0)" in camp, "the true fleet is berthed without a reach"
    assert "reach_m=24.0 * FLEET_T1_LEN_K)" in camp, (
        "the overview's longer glyph is berthed at the true ship's reach")


def test_the_ranks_are_spaced_further_apart_than_a_ship_is_long(s3):
    """προκρόσσας (14.35) is a claim about ORDER. Five rows at 38 m left 11 m
    of sand between a stem-post and the row in front — generous on the ground
    and nothing on the page, because ten metres of DEPTH draws 0.5-1.2 px down
    this sight-line against 4.0 px for ten metres ACROSS it. So the rows were
    about a pixel apart while each ship stood 2.5 px tall on her post, and
    every rank was drawn straight through the one ahead."""
    reach = 24.0 * 1.12          # stem-post tip, the furthest-forward point
    clear = s3.FLEET_ROW_M - reach
    assert clear > 40.0, (
        f"only {clear:.0f} m between one rank and the next: at this camera "
        f"that is about {clear / 10.0:.1f} px, and a ship stands 2.5 px tall")
    assert s3.FLEET_ROWS >= 2, "προκρόσσας is a plural: one row is not ranks"
    # the camp must still finish inland of the huts, which start at 300 m
    assert s3.FLEET_ROWS * s3.FLEET_ROW_M < 300.0, (
        "the fleet's ranks now reach back into the huts")


def test_the_key_declares_the_enlargement_and_the_props(s3, restore_camera):
    """The plate may not draw a convention it does not declare. The key's
    standing wording covers the drawn NUMBER ("filling the frontage in view
    and never the catalogue's count") and says nothing about the drawn SIZE,
    which is the freedom the overview actually spends -- so the size and its
    factor are stated outright, and so are the props.

    Pinned to plate B: the overview rank lives on the ships plate."""
    if hasattr(s3, "apply_plate_preset"):
        s3.apply_plate_preset("B")
    key = s3.furniture(None, None, 2600.0, 5500.0)
    assert f"×{s3.FLEET_T1_LEN_K:g} oversize" in key, (
        "the overview enlarges the hulls and the key does not say by how much")
    assert "length and beam alike" in key, (
        "the key does not say the enlargement is isotropic")
    assert "ἕρματα μακρά" in key and "1.485–86" in key, (
        "the props are drawn and the key does not cite them")
    assert "ὑψοῦ ἐπὶ ψαμάθοις" in key
    assert "2.154" in key, "the key omits the line that makes propping the "\
                           "STANDING condition of a beached ship"
    # and the margin still fits: the new row is paid for out of the leading
    ys = [float(m.group(1)) for m in re.finditer(r' y="([\d.]+)"', key)]
    assert max(ys) <= s3.H - s3.NEAT_M, (
        f"the key's new row is being paid for out of the sheet: last baseline "
        f"y={max(ys):.0f} on {s3.H:.0f} px")


# ═══════════════════════════════════════════════════════════════════════════
# the beach is the Aegean, not the bay (ruling 4, 2026-09-02)
# ═══════════════════════════════════════════════════════════════════════════
KRAFT_2003 = (
    "Kraft, John C., George Rapp, Ilhan Kayan, and John V. Luce. "
    '"Harbor Areas at Ancient Troy: Sedimentology and Geomorphology '
    'Complement Homer\'s Iliad." Geology 31, no. 2 (2003): 163-66.'
)


def _camp_polys():
    lay = _plate_layers()
    return (lay["sea-modern"]["polygon"],
            lay["lagoon-bronze"]["polygon"],
            lay["achaean-camp-zone"]["polygon"])


def _easting(s3, lat, lon, origin):
    return s3.pp._flat_m((lat, lon), *origin)[0]


@pytest.fixture
def restore_camera(s3):
    saved = (s3.VIEWPOINT, s3.HEADING_DEG, s3.ALT, s3.SETBACK,
             s3.RANGE_NEAR, s3.HFOV_DEG, s3.FOCAL)
    extra = {k: getattr(s3, k) for k in (
        "PLATE", "PLATE_FAMILY", "DRAW_FLEET", "DRAW_HUTS",
        "PLATE_TITLE", "PLATE_SUBTITLE", "OBJ_SHADOW",
    ) if hasattr(s3, k)}
    yield
    (s3.VIEWPOINT, s3.HEADING_DEG, s3.ALT, s3.SETBACK,
     s3.RANGE_NEAR, s3.HFOV_DEG, s3.FOCAL) = saved
    for k, v in extra.items():
        setattr(s3, k, v)


def test_every_berth_is_on_the_aegean_flank_west_of_the_zone(s3):
    """The fleet beaches on sea-modern, west of the Sigeum-ridge camp zone,
    never in the reconstructed bay."""
    sea, lagoon, zone = _camp_polys()
    fleet = s3.aegean_fleet(sea, zone, lagoon)
    berths = fleet["berths"]
    origin = fleet["origin"]
    assert berths, "the Aegean beach produced no berths"
    for along, _row, f, lat, lon, _brg in berths:
        assert not s3.point_in_poly_ll(lat, lon, sea), (
            f"berth {(lat, lon)} is inside sea-modern")
        assert not s3.point_in_poly_ll(lat, lon, lagoon), (
            f"berth {(lat, lon)} is inside lagoon-bronze")
        assert not s3.point_in_poly_ll(lat, lon, zone), (
            f"berth {(lat, lon)} is inside the ridge-crest zone")
        assert f > 0.0, (
            f"berth {(lat, lon)} is not seaward of the camp axis")
        if abs(along) < 40.0:
            assert _easting(s3, lat, lon, origin) < 0.0, (
                f"mid-camp berth {(lat, lon)} is not west of the centroid")


def test_the_rearmost_rank_is_east_of_the_frontmost(s3):
    """Ranks step landward (east) from the Aegean waterline."""
    sea, lagoon, zone = _camp_polys()
    berths = s3.aegean_fleet(sea, zone, lagoon)["berths"]
    rows = {}
    for _along, row, _f, lat, lon, _brg in berths:
        rows.setdefault(row, []).append((lat, lon))
    assert 0 in rows and (s3.FLEET_ROWS - 1) in rows
    front_e = sum(p[1] for p in rows[0]) / len(rows[0])
    rear_e = sum(p[1] for p in rows[s3.FLEET_ROWS - 1]) / len(rows[s3.FLEET_ROWS - 1])
    assert rear_e > front_e, (
        f"rearmost rank lon {rear_e:.5f} is not east of frontmost {front_e:.5f}")


def test_the_achaean_wall_is_dry_east_of_the_sterns_west_of_the_centroid(s3):
    """Il. 7.436-41 / 14.30-36: wall landward of the rearmost sterns, still
    on the outer flank, not in the bay."""
    sea, lagoon, zone = _camp_polys()
    fleet = s3.aegean_fleet(sea, zone, lagoon)
    wlat, wlon = fleet["wall"]
    origin = fleet["origin"]
    assert not s3.point_in_poly_ll(wlat, wlon, sea), "wall is in the Aegean"
    assert not s3.point_in_poly_ll(wlat, wlon, lagoon), "wall is in the bay"
    wall_e = _easting(s3, wlat, wlon, origin)
    assert wall_e < 0.0, "wall is not west of the camp-zone centroid"
    # the waypoint is the central station; the wall line itself sits
    # landward of that station's sterns (the north end of a 13.3° beach
    # is east of this one pin and is not what the pin claims)
    mid = [q for q in fleet["berths"] if abs(q[0]) < 20.0]
    assert mid, "no sterns at the wall's central station"
    for _along, _row, _f, lat, lon, _brg in mid:
        assert wall_e > _easting(s3, lat, lon, origin), (
            f"wall is not east of stern at {(lat, lon)}")


def test_the_true_fleet_hull_count_is_at_least_200(s3):
    """Diagnosis 2026-09-02 (ruling 4): the pre-move (bay-side) true fleet
    drew 258 hulls; near_camp's polygon-vertex blob was gating berths
    against the ridge-LANDFORM zone (not a thin crest — 600-900 m wide
    station to station, apparatus/plates/trojan-plain.json's own note on
    achaean-camp-zone) for no reason connected to whether a berth is a sane
    place to stand a ship, rejecting ~1/4 of otherwise-good stations. Camera
    framing aside (a single render only ever shows a slice of 9 km), the
    beach itself must still hold a fleet of the pre-move's own order — not
    the 28 a bad gate left standing."""
    sea, lagoon, zone = _camp_polys()
    berths = s3.aegean_fleet(sea, zone, lagoon, pitch=13.0, rows=s3.FLEET_ROWS,
                             row_m=s3.FLEET_ROW_M,
                             first_m=s3.FLEET_FIRST_M)["berths"]
    assert len(berths) >= 200, (
        f"the Aegean beach holds only {len(berths)} true-fleet berths, well "
        f"under the pre-move (bay-side) fleet's own 258")


def test_every_hut_stands_east_of_the_true_fleet_at_its_station(s3):
    """Huts behind the ships, not among them: the huts loop's own front row
    (scripts/panorama-stage3.py ~5407-5409, fs - 300 m) must sit east
    (landward, a smaller west-offset) of even the true fleet's deepest,
    most-staggered rank (fs - first_m - (rows-1)*row_m - stagger) at the
    SAME station, for every station the beach actually offers."""
    sea, lagoon, zone = _camp_polys()
    fleet = s3.aegean_fleet(sea, zone, lagoon)
    HUT_FRONT_M = 300.0          # scripts/panorama-stage3.py: f = fs - 300.0
    stagger = 11.0                # aegean_fleet's own default
    deepest_true_rank = (s3.FLEET_FIRST_M
                         + (s3.FLEET_ROWS - 1) * s3.FLEET_ROW_M + stagger)
    assert HUT_FRONT_M > deepest_true_rank, (
        f"the huts' front row ({HUT_FRONT_M} m back from shore) is not east "
        f"of the true fleet's deepest rank ({deepest_true_rank:.0f} m)")
    # and the same holds against every station's own measured shore, not
    # just the constants above
    for lateral, fs in fleet["shore"].items():
        if fs is None:
            continue
        hut_f = fs - HUT_FRONT_M
        stern_f = fs - deepest_true_rank
        assert hut_f < stern_f, (
            f"at along={lateral:.0f}, hut offset {hut_f:.0f} is not east of "
            f"the deepest stern offset {stern_f:.0f}")


def test_the_wall_line_is_east_of_every_true_fleet_stern(s3):
    """The drawn wall (per-station, camp()'s wall_pts) is placed at
    fs - wall_back for every station using the SAME global wall_back
    (layout['wall_back']); confirm that offset clears the true fleet's own
    deepest, most-staggered rank at every station the beach offers, so the
    wall never lands in front of (west of) a stern (Il. 7.436-441: the wall
    is built at the ships' sterns, landward of them)."""
    sea, lagoon, zone = _camp_polys()
    fleet = s3.aegean_fleet(sea, zone, lagoon)
    stagger = 11.0
    deepest_true_rank = (s3.FLEET_FIRST_M
                         + (s3.FLEET_ROWS - 1) * s3.FLEET_ROW_M + stagger)
    assert fleet["wall_back"] > deepest_true_rank, (
        f"wall_back ({fleet['wall_back']:.0f} m) is not east of the true "
        f"fleet's deepest rank ({deepest_true_rank:.0f} m)")
    for lateral, fs in fleet["shore"].items():
        if fs is None:
            continue
        wall_f = fs - fleet["wall_back"]
        stern_f = fs - deepest_true_rank
        assert wall_f < stern_f, (
            f"at along={lateral:.0f}, wall offset {wall_f:.0f} is not east "
            f"of the deepest stern offset {stern_f:.0f}")


def test_the_ditch_is_west_of_the_wall(s3):
    """20 m outside (west of) the wall, toward the sea."""
    sea, lagoon, zone = _camp_polys()
    fleet = s3.aegean_fleet(sea, zone, lagoon)
    origin = fleet["origin"]
    ditch_e = _easting(s3, fleet["ditch"][0], fleet["ditch"][1], origin)
    wall_e = _easting(s3, fleet["wall"][0], fleet["wall"][1], origin)
    assert ditch_e < wall_e, (
        f"ditch easting {ditch_e:.1f} is not west of wall {wall_e:.1f}")


def test_cli_viewpoint_reaches_the_camera(s3, restore_camera):
    """--viewpoint LAT,LON is applied before Camera reads VIEWPOINT."""
    ns = s3.build_arg_parser().parse_args(["--viewpoint", "39.95,26.16"])
    s3.apply_camera_args(ns)
    assert s3.VIEWPOINT[0] == pytest.approx(39.95)
    assert s3.VIEWPOINT[1] == pytest.approx(26.16)
    cam = s3.Camera(None, pitch=math.radians(13.23))
    p = cam.project_ll(39.95, 26.16, 0.0)
    assert p is not None, "Camera does not see the flagged viewpoint"
    assert abs(p[0] - s3.W / 2.0) < 2.0, (
        f"flagged viewpoint projects at x={p[0]:.1f}, not frame centre")


def test_the_ships_camera_target_row_exists(s3, restore_camera):
    if hasattr(s3, "apply_plate_preset"):
        s3.apply_plate_preset("B")
    wps = [{
        "id": "ilios", "name": "Ilios", "greek": "Ἴλιος", "tier": 1,
        "positionBasis": "measured", "citation": "Il. 3.145",
        "tradition": "", "rule": "", "kind": "settlement",
        "at": [39.957, 26.239],
        "_screen": [1200.0, 400.0, 7000.0],
        "_label": [1200.0, 400.0],
    }]
    stats = {
        "fleet_centroid": [39.9520, 26.1610],
        "fleet_centroid_screen": [900.0, 800.0, 1800.0],
        "hut_centroid": [39.9570, 26.1680],
        "hut_centroid_screen": [950.0, 780.0, 1900.0],
    }
    tgt = s3.camera_targets(wps, stats)
    ships = next((r for r in tgt["targets"] if r["id"] == "ships"), None)
    assert ships is not None, "camera_targets has no ships row"
    assert ships["showTiers"] == [1, 2]
    assert ships["at"] == [39.9520, 26.1610]


def test_the_subtitle_is_from_above_the_camp(s3):
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "from above the Achaean camp" in svg
    assert "from the Achaean camp" not in svg.replace(
        "from above the Achaean camp", "")


def test_the_camp_key_names_the_outer_flank_and_the_modern_coast(s3):
    """Placement sentence names Kraft 2003 (short form — the sheet's margin
    is a fixed 300 px and cannot carry the full Chicago citation without
    colliding with the key above it, diagnosed 2026-09-02) and the
    modern-coast caveat; the citation itself carries in the DATA, per
    CLAUDE.md's apparatus-sourcing rule ("every sourced claim carries its
    citation in the data, not just the prose") — the achaean-camp-zone
    layer's own `sources`, asserted below."""
    key = " ".join(n + " " + g for n, g in s3.CAMP_KEY) + " " + s3.DRAWN_MARKS
    assert "Kraft" in key and "2003" in key
    assert "outer" in key.lower() or "Aegean" in key
    assert "modern" in key.lower()
    lay = _plate_layers()
    zone_cites = " ".join(s["cite"] for s in lay["achaean-camp-zone"]["sources"])
    assert KRAFT_2003 in zone_cites, (
        "the full Kraft 2003 citation is missing from the achaean-camp-zone "
        "layer's own sources — the sheet's short form has nothing to point at")
    src = open(STAGE3).read()
    wp = src.split('add("achaean-wall"', 1)[1].split("add(", 1)[0]
    assert "embayment" not in wp, "the wall note still explains the old bay beach"
    assert "1500.0" not in wp, "the wall is still pinned 1500 m into the bay"


# ═══════════════════════════════════════════════════════════════════════════
# two plates from one script (John, 2026-09-02 14:47)
# ═══════════════════════════════════════════════════════════════════════════

def _axis_stations(s3):
    """Independent of plate_presets(): central / north / south on the camp
    zone's long axis, the same construction the brief names."""
    zone = _camp_polys()[2]
    origin = s3.camp_origin(zone)
    alongs = []
    ath = math.radians(s3.CAMP_AXIS_DEG)
    for p in zone:
        e, n = s3.pp._flat_m(p, *origin)
        alongs.append(e * math.sin(ath) + n * math.cos(ath))
    a0, a1 = min(alongs), max(alongs)
    south = s3.camp_ll(origin, a0, 0.0)
    north = s3.camp_ll(origin, a1, 0.0)
    centre = s3.camp_ll(origin, 0.5 * (a0 + a1), 0.0)
    return centre, north, south


def _fake_plate(s3):
    sea, lagoon, zone = _camp_polys()
    P = object.__new__(s3.Plate)

    class Cam:
        def project_ll(self, lat, lon, z):
            return (1200.0, 600.0, 2000.0)

        def project(self, e, n, z):
            return (1200.0, 600.0, 2000.0)

    class Terr:
        def elev(self, lat, lon):
            return 5.0

    P.cam = Cam()
    P.terr = Terr()
    P.lay = {"achaean-camp-zone": {"polygon": zone}}
    P.stats = {}
    rings = {"sea-modern": sea, "lagoon-bronze": lagoon}
    P.shore = lambda label: rings[label]
    return P


def _apply_plate(s3, *argv):
    ns = s3.build_arg_parser().parse_args(list(argv))
    s3.apply_plate_preset(ns.plate)
    s3.apply_camera_args(ns)
    return ns


def test_plate_flag_defaults_to_a_and_accepts_b_aliases(s3):
    ap = s3.build_arg_parser()
    assert ap.parse_args([]).plate == "A"
    assert ap.parse_args(["--plate", "B"]).plate == "B"
    assert ap.parse_args(["--plate", "B1"]).plate == "B1"
    assert ap.parse_args(["--plate", "B2"]).plate == "B2"


def test_preset_a_resolves_to_the_settled_bay_camera(s3, restore_camera):
    _apply_plate(s3, "--plate", "A")
    assert s3.VIEWPOINT[0] == pytest.approx(39.9755, abs=1e-6)
    assert s3.VIEWPOINT[1] == pytest.approx(26.1785, abs=1e-6)
    assert s3.HEADING_DEG == pytest.approx(104.0)
    assert s3.HFOV_DEG == pytest.approx(72.0)
    assert s3.ALT == pytest.approx(800.0)
    assert s3.SETBACK == pytest.approx(1500.0)
    assert s3.RANGE_NEAR == pytest.approx(420.0)


def test_preset_b1_is_2500_m_west_of_the_central_station(s3, restore_camera):
    centre, _north, _south = _axis_stations(s3)
    vp = s3.ll_along(centre, s3.CAMP_SEAWARD_DEG, 2500.0)
    heading = s3.pp._bearing_deg(vp, centre)
    _apply_plate(s3, "--plate", "B1")
    assert s3.VIEWPOINT[0] == pytest.approx(vp[0], abs=1e-6)
    assert s3.VIEWPOINT[1] == pytest.approx(vp[1], abs=1e-6)
    assert s3.HEADING_DEG == pytest.approx(heading, abs=0.05)
    assert s3.HEADING_DEG == pytest.approx(103.0, abs=2.0)
    assert s3.ALT == pytest.approx(600.0)
    assert s3.SETBACK == pytest.approx(0.0)
    assert s3.HFOV_DEG == pytest.approx(72.0)
    assert s3.RANGE_NEAR == pytest.approx(150.0)


def test_preset_b2_looks_along_the_beach_from_the_north(s3, restore_camera):
    _centre, north, south = _axis_stations(s3)
    vp = s3.ll_along(north, s3.CAMP_SEAWARD_DEG, 1800.0)
    heading = s3.pp._bearing_deg(vp, south)
    _apply_plate(s3, "--plate", "B2")
    assert s3.VIEWPOINT[0] == pytest.approx(vp[0], abs=1e-6)
    assert s3.VIEWPOINT[1] == pytest.approx(vp[1], abs=1e-6)
    assert s3.HEADING_DEG == pytest.approx(heading, abs=0.05)
    assert s3.ALT == pytest.approx(700.0)
    assert s3.SETBACK == pytest.approx(0.0)
    assert s3.HFOV_DEG == pytest.approx(72.0)
    assert s3.RANGE_NEAR == pytest.approx(150.0)


def test_plate_b_aliases_b1(s3, restore_camera):
    _apply_plate(s3, "--plate", "B1")
    b1 = (s3.VIEWPOINT, s3.HEADING_DEG, s3.ALT, s3.SETBACK, s3.RANGE_NEAR)
    _apply_plate(s3, "--plate", "B")
    assert s3.VIEWPOINT == pytest.approx(b1[0])
    assert s3.HEADING_DEG == pytest.approx(b1[1])
    assert s3.ALT == pytest.approx(b1[2])
    assert s3.SETBACK == pytest.approx(b1[3])
    assert s3.RANGE_NEAR == pytest.approx(b1[4])


def test_explicit_heading_overrides_the_preset(s3, restore_camera):
    _apply_plate(s3, "--plate", "B", "--heading", "95")
    assert s3.HEADING_DEG == pytest.approx(95.0)
    assert s3.ALT == pytest.approx(600.0)
    assert s3.SETBACK == pytest.approx(0.0)


def test_plate_titles_and_subtitles_are_exact(s3, restore_camera):
    _apply_plate(s3, "--plate", "A")
    svg_a = s3.furniture(None, None, 2600.0, 5500.0)
    assert ">THE BAY AND ILIOS</text>" in svg_a
    assert ("the plain of Troy from above the Achaean camp, "
            "looking east-south-east") in svg_a
    assert s3.PLATE_TITLE == "THE BAY AND ILIOS"
    assert s3.PLATE_SUBTITLE == (
        "the plain of Troy from above the Achaean camp, looking east-south-east")
    _apply_plate(s3, "--plate", "B")
    svg_b = s3.furniture(None, None, 2600.0, 5500.0)
    assert ">THE SHIPS ON THE AEGEAN SHORE</text>" in svg_b
    assert ("the Achaean camp from over the sea, looking east; "
            "Ilios lies beyond the ridge, out of sight") in svg_b
    assert s3.PLATE_TITLE == "THE SHIPS ON THE AEGEAN SHORE"
    assert s3.PLATE_SUBTITLE == (
        "the Achaean camp from over the sea, looking east; "
        "Ilios lies beyond the ridge, out of sight")


def test_plate_a_camp_key_names_the_companion_plate(s3, restore_camera):
    _apply_plate(s3, "--plate", "A")
    svg = s3.furniture(None, None, 2600.0, 5500.0)
    assert "behind the viewer" in svg
    assert "companion plate" in svg


def test_plate_a_draws_zero_hulls_and_huts_and_keeps_the_wall(s3, restore_camera):
    _apply_plate(s3, "--plate", "A")
    s3.OBJ_SHADOW = False
    P = _fake_plate(s3)
    ships, ships_t1, huts, wall_svg, ditch_svg, ship_px, *_ = P.camp()
    assert P.stats["hulls"] == 0
    assert not ships and not ships_t1
    assert P.stats["huts"] == 0
    assert not huts
    assert "wall_at" in P.stats
    wps = [{
        "id": "achaean-wall", "name": "the wall of the Achaeans",
        "greek": "τεῖχος", "tier": 2, "positionBasis": "conjectural",
        "citation": "Il. 7.436-441", "tradition": "", "rule": "",
        "kind": "line", "at": P.stats["wall_at"],
        "_screen": [1100.0, 700.0, 2500.0], "_label": [1100.0, 722.0],
    }]
    tgt = s3.camera_targets(wps, dict(P.stats))
    ids = {r["id"] for r in tgt["targets"]}
    assert "achaean-wall" in ids
    assert "ships" not in ids


def test_plate_b_draws_at_least_200_true_fleet_hulls(s3, restore_camera):
    _apply_plate(s3, "--plate", "B")
    s3.OBJ_SHADOW = False
    P = _fake_plate(s3)
    ships, ships_t1, huts, wall_svg, ditch_svg, ship_px, *_ = P.camp()
    assert P.stats["hulls"] >= 200, (
        f"--plate B drew {P.stats['hulls']} true-fleet hulls")
    assert len(ships) >= 200


def test_plate_a_targets_drop_ships_plate_b_keeps_ships_and_huts(
        s3, restore_camera):
    wall = {
        "id": "achaean-wall", "name": "the wall of the Achaeans",
        "greek": "τεῖχος", "tier": 2, "positionBasis": "conjectural",
        "citation": "Il. 7.436-441", "tradition": "", "rule": "flank",
        "kind": "line", "at": [39.96, 26.17],
        "_screen": [1100.0, 700.0, 2500.0], "_label": [1100.0, 722.0],
    }
    sigeion = {
        "id": "sigeion", "name": "SIGEION", "greek": "Σίγειον", "tier": 2,
        "positionBasis": "measured", "citation": "Il. 14.31-36",
        "tradition": "", "rule": "", "kind": "region",
        "at": [39.9835, 26.1809],
        "_screen": [800.0, 500.0, 3000.0], "_label": [800.0, 486.0],
    }
    bay = {
        "id": "bay-of-troy", "name": "the bay of Troy", "greek": "", "tier": 1,
        "positionBasis": "reconstructed", "citation": "Kayan 1995",
        "tradition": "", "rule": "", "kind": "water",
        "at": [39.9880, 26.2060],
        "_screen": [1400.0, 550.0, 4000.0], "_label": [1400.0, 550.0],
    }
    ilios = {
        "id": "ilios", "name": "Ilios", "greek": "Ἴλιος", "tier": 1,
        "positionBasis": "measured", "citation": "Il. 3.145",
        "tradition": "", "rule": "", "kind": "settlement",
        "at": [39.957, 26.239],
        "_screen": [1200.0, 400.0, 7000.0], "_label": [1200.0, 400.0],
    }
    stats = {
        "fleet_centroid": [39.9520, 26.1610],
        "fleet_centroid_screen": [900.0, 800.0, 1800.0],
        "hut_centroid": [39.9570, 26.1680],
        "hut_centroid_screen": [950.0, 780.0, 1900.0],
    }
    _apply_plate(s3, "--plate", "A")
    ids_a = {r["id"] for r in s3.camera_targets(
        [wall, sigeion, bay, ilios], stats)["targets"]}
    assert "ships" not in ids_a
    assert "huts" not in ids_a
    assert "achaean-wall" in ids_a
    _apply_plate(s3, "--plate", "B")
    ids_b = {r["id"] for r in s3.camera_targets(
        [wall, sigeion, bay, ilios], stats)["targets"]}
    assert "ships" in ids_b
    assert "huts" in ids_b
    assert "achaean-wall" in ids_b
    assert "sigeion" in ids_b
    assert "bay-of-troy" in ids_b
    assert "ilios" not in ids_b


def test_output_stem_prefixes_the_plate_letter(s3):
    assert s3.output_stem("A", "full", "stage2b") == "stage3-A-fullstage2b"
    assert s3.output_stem("B1", "camera-targets", "stage2b") == (
        "stage3-B1-camera-targetsstage2b")
    assert s3.output_stem("B2", "full", "-x") == "stage3-B2-full-x"
