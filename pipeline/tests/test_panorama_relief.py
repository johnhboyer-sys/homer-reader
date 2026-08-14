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
