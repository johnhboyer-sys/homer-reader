import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_places


def _place(**overrides):
    base = {
        "id": "testplace",
        "name": "Test Place",
        "certainty": "certain",
        "maps": ["greece"],
        "mentions": [],
        "note": "A note.",
    }
    base.update(overrides)
    return base


def _plate(**overrides):
    base = {
        "id": "testplate",
        "title": "Test Plate",
        "kind": "geographic",
        "status": "draft",
        "seed": 1,
        "bbox": [39.86, 26.12, 40.02, 26.36],
        "size": [880, 620],
        "layers": [
            {"id": "river-1", "kind": "river", "path": [[39.90, 26.15], [39.95, 26.20]]}
        ],
        "sources": [{"cite": "A Book."}],
    }
    base.update(overrides)
    return base


# ── validate_places: deliberate-corruption tests ────────────────────────────


def test_validate_places_good_fixture_passes():
    doc = {"status": "draft", "places": [_place()]}
    assert apparatus_places.validate_places(doc) == []


def test_validate_places_detects_duplicate_ids():
    doc = {"status": "draft", "places": [_place(id="dup"), _place(id="dup")]}
    problems = apparatus_places.validate_places(doc)
    assert any("duplicate id" in p for p in problems)


def test_validate_places_traditional_requires_tradition():
    doc = {"status": "draft", "places": [_place(certainty="traditional")]}
    problems = apparatus_places.validate_places(doc)
    assert any("requires a non-empty tradition" in p for p in problems)


def test_validate_places_mythical_rejects_pleiades():
    doc = {
        "status": "draft",
        "places": [_place(certainty="mythical", pleiades="https://pleiades.stoa.org/places/1")],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("mythical places may not carry a pleiades URL" in p for p in problems)


def test_validate_places_source_requires_nonempty_cite():
    doc = {"status": "draft", "places": [_place(sources=[{"cite": "  "}])]}
    problems = apparatus_places.validate_places(doc)
    assert any("sources[0].cite must be a non-empty string" in p for p in problems)


def test_validate_places_source_url_must_be_http():
    doc = {
        "status": "draft",
        "places": [_place(sources=[{"cite": "A Book.", "url": "ftp://example.com"}])],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("sources[0].url must be http(s)" in p for p in problems)


def test_validate_places_plate_anchors_without_position_basis_rejected():
    doc = {"status": "draft", "places": [_place(plateAnchors={"trojan-plain": [0.5, 0.5]})]}
    problems = apparatus_places.validate_places(doc)
    assert any("positionBasis is not 'conjectural'" in p for p in problems)


def test_validate_places_position_basis_without_plate_anchors_rejected():
    doc = {"status": "draft", "places": [_place(positionBasis="conjectural")]}
    problems = apparatus_places.validate_places(doc)
    assert any("requires plateAnchors" in p for p in problems)


def test_validate_places_plate_anchors_with_position_basis_passes():
    doc = {
        "status": "draft",
        "places": [
            _place(
                plateAnchors={"trojan-plain": [0.5, 0.5]},
                positionBasis="conjectural",
            )
        ],
    }
    assert apparatus_places.validate_places(doc) == []


def test_validate_places_grandfathers_legacy_records_without_kind_or_sources():
    # Not tagged for a plate (maps has no troad-plain/troy-citadel prefix) —
    # kind and sources stay optional, exactly like today's 280 real records.
    doc = {"status": "draft", "places": [_place(maps=["wanderings"])]}
    assert apparatus_places.validate_places(doc) == []


def test_validate_places_plate_tagged_record_requires_kind_and_sources():
    doc = {"status": "draft", "places": [_place(maps=["troad-plain"])]}
    problems = apparatus_places.validate_places(doc)
    assert any("kind is required" in p for p in problems)
    assert any("sources is required" in p for p in problems)


# ── validate_plate: deliberate-corruption tests ─────────────────────────────


def test_validate_plate_good_fixture_passes():
    places_by_id = {}
    assert apparatus_places.validate_plate(_plate(), places_by_id) == []


def test_validate_plate_requires_plate_level_sources():
    plate = _plate()
    del plate["sources"]
    problems = apparatus_places.validate_plate(plate, {})
    assert any("sources is required" in p for p in problems)


def test_validate_plate_rejects_empty_plate_level_sources():
    plate = _plate(sources=[])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("sources must be a non-empty list" in p for p in problems)


def test_validate_plate_detects_transposed_lat_lon():
    # bbox is lat 39.86-40.02, lon 26.12-26.36; a transposed pair (lon, lat)
    # lands miles outside it.
    plate = _plate(layers=[
        {"id": "river-1", "kind": "river", "path": [[26.15, 39.90]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("lies outside bbox" in p and "river-1" in p for p in problems)


def test_validate_plate_detects_dangling_place_id():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "placeId": "nonexistent-place"}
    ])
    problems = apparatus_places.validate_plate(plate, {"troy": {"id": "troy"}})
    assert any("placeId 'nonexistent-place' does not resolve" in p for p in problems)


def test_validate_plate_resolves_real_place_id():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "placeId": "troy"}
    ])
    problems = apparatus_places.validate_plate(plate, {"troy": {"id": "troy"}})
    assert problems == []


def test_validate_plate_detects_dangling_claim():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "claims": ["nonexistent-place"]}
    ])
    problems = apparatus_places.validate_plate(plate, {"troy": {"id": "troy"}})
    assert problems == [
        "testplate: layer town claims unknown place 'nonexistent-place'"
    ]


def test_validate_plate_resolves_known_claims():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "claims": ["troy", "ilion"]}
    ])
    problems = apparatus_places.validate_plate(
        plate, {"troy": {"id": "troy"}, "ilion": {"id": "ilion"}}
    )
    assert problems == []


def test_validate_plate_rejects_non_list_claims():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "claims": "troy"}
    ])
    problems = apparatus_places.validate_plate(plate, {"troy": {"id": "troy"}})
    assert any("layer town claims" in p for p in problems)


def test_validate_plate_schematic_rejects_lat_lon_coordinates():
    # Coordinate space is declared by the PRESENCE of bbox, not by kind or
    # by the bbox's own extent — a schematic plate that wants unit space
    # simply omits bbox (no dummy [0,0,1,1] needed).
    plate = _plate(
        kind="schematic",
        layers=[{"id": "river-1", "kind": "river", "path": [[39.90, 26.15]]}],
    )
    del plate["bbox"]
    problems = apparatus_places.validate_plate(plate, {})
    assert any("must be a unit [u, v] pair in 0..1" in p for p in problems)


def test_validate_plate_schematic_accepts_unit_coordinates():
    plate = _plate(
        kind="schematic",
        layers=[{"id": "river-1", "kind": "river", "path": [[0.2, 0.4]]}],
    )
    del plate["bbox"]
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_schematic_with_geographic_bbox_accepts_lat_lon():
    plate = _plate(
        kind="schematic",
        bbox=[39.86, 26.12, 40.02, 26.36],
        layers=[{"id": "river-1", "kind": "river", "path": [[39.90, 26.15], [39.95, 26.20]]}],
    )
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_schematic_with_geographic_bbox_rejects_out_of_bbox():
    plate = _plate(
        kind="schematic",
        bbox=[39.86, 26.12, 40.02, 26.36],
        layers=[{"id": "river-1", "kind": "river", "path": [[0.2, 0.4]]}],
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("lies outside bbox" in p for p in problems)


def test_validate_plate_schematic_without_bbox_still_requires_unit_range():
    plate = {
        "id": "unit-sheet",
        "title": "Unit Sheet",
        "kind": "schematic",
        "status": "draft",
        "size": [100, 100],
        "sources": [{"cite": "A Book."}],
        "layers": [{"id": "river-1", "kind": "river", "path": [[39.90, 26.15]]}],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("must be a unit [u, v] pair in 0..1" in p for p in problems)


def test_validate_plate_schematic_needs_no_bbox():
    """A schematic plate has no geography, so demanding a bbox of it would be
    demanding a coordinate for something that has none. The Shield of Achilles
    is concentric bands of Iliad 18, not a place.

    Band fixture is well-formed (title/greek/summary/ring, not just id/lines):
    shared/lib/shield.ts's renderShield dereferences all of those
    unconditionally and throws on a non-distinct/non-negative-integer ring, so
    an under-specified band here used to pass this validator clean and then
    crash the renderer at runtime. That gap is now closed in validate_plate
    itself (see the band-field checks below) — this test's job is only to
    confirm a schematic plate still needs no bbox."""
    plate = {
        "id": "shield-of-achilles",
        "title": "The Shield of Achilles",
        "kind": "schematic",
        "status": "draft",
        "size": [640, 640],
        "sources": [{"cite": "A Book."}],
        "bands": [
            {
                "id": "cosmos",
                "title": "Cosmos",
                "greek": "γαῖα · οὐρανός · θάλασσα",
                "lines": [483, 489],
                "summary": "Earth, sky, sea, and the heavenly bodies fill the shield's centre.",
                "ring": 0,
            },
            {
                "id": "ocean",
                "title": "Ocean",
                "greek": "Ὠκεανός",
                "lines": [607, 608],
                "summary": "The river Ocean runs around the shield's outermost rim.",
                "ring": 1,
            },
        ],
    }
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_schematic_must_draw_something():
    plate = {
        "id": "empty",
        "title": "Empty",
        "kind": "schematic",
        "status": "draft",
        "size": [10, 10],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("must declare 'bands' or 'layers'" in p for p in problems)


def test_validate_plate_schematic_rejects_duplicate_band_ids():
    plate = {
        "id": "shield",
        "title": "Shield",
        "kind": "schematic",
        "status": "draft",
        "size": [10, 10],
        "bands": [{"id": "ocean"}, {"id": "ocean"}],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("duplicate band id 'ocean'" in p for p in problems)


def test_validate_plate_geographic_still_requires_bbox_and_layers():
    plate = {
        "id": "plain",
        "title": "Plain",
        "kind": "geographic",
        "status": "draft",
        "size": [10, 10],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("missing required key 'bbox'" in p for p in problems)
    assert any("missing required key 'layers'" in p for p in problems)


def test_validate_plate_stochastic_style_requires_seed():
    plate = _plate(layers=[
        {"id": "coast-1", "kind": "coast", "style": "stipple",
         "rings": [[[39.90, 26.15], [39.91, 26.16]]]}
    ])
    del plate["seed"]
    problems = apparatus_places.validate_plate(plate, {})
    assert any("seed is required" in p for p in problems)


def test_validate_plate_bbox_min_must_be_less_than_max():
    plate = _plate(bbox=[40.02, 26.12, 39.86, 26.36])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("minLat" in p and "must be <" in p for p in problems)


# ── positive test: the real corpus validates clean ──────────────────────────


def test_real_places_and_trojan_plain_plate_validate_clean():
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    place_problems = apparatus_places.validate_places(places_doc)
    assert place_problems == [], place_problems

    places_by_id = {p["id"]: p for p in places_doc["places"]}
    plate_doc = json.loads(
        (ROOT / "apparatus" / "plates" / "trojan-plain.json").read_text(encoding="utf-8")
    )
    plate_problems = apparatus_places.validate_plate(plate_doc, places_by_id)
    assert plate_problems == [], plate_problems


def test_validate_plate_accepts_tumulus_layer_kind():
    """The tombs of Ilos and Batieia are mounds on the plain, not ridges.
    The renderer draws them with a dome-in-section glyph; the enum has to
    admit the kind or the two implementations of this schema drift apart."""
    plate = _plate(layers=[
        {"id": "tomb-of-ilos", "kind": "tumulus", "path": [[39.95, 26.20]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_accepts_a_relief_elevation():
    """`elevation` (2026-07-29) is a contour level in metres, and its presence
    is what puts a relief band in shared/lib/plate.ts's hypsometric register
    -- filled from the sheet's elevation ramp and edged with a hairline rather
    than hachured. Sea level itself is a legal elevation."""
    plate = _plate(layers=[
        {"id": "relief-band-0040", "kind": "relief", "elevation": 40,
         "rings": [[[39.95, 26.20], [39.96, 26.21], [39.95, 26.22]]]},
        {"id": "relief-shore", "kind": "relief", "elevation": 0,
         "polygon": [[39.95, 26.20]]},
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_rejects_a_malformed_relief_elevation():
    """A malformed elevation would not fail loudly -- it would silently demote
    a contoured band back to the hand-drawn hachure treatment -- so it is
    rejected here, exactly as parseLayer rejects it on the TS side."""
    for bad in (-5, "40", None.__class__, [40]):
        plate = _plate(layers=[
            {"id": "relief-1", "kind": "relief", "elevation": bad,
             "polygon": [[39.95, 26.20]]}
        ])
        problems = apparatus_places.validate_plate(plate, {})
        assert any("elevation must be a number" in p for p in problems), bad


def test_validate_plate_rejects_unknown_region_fill():
    plate = _plate(layers=[
        {"id": "sea", "kind": "region", "fill": "red", "polygon": [[39.95, 26.20]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("fill must be one of" in p for p in problems)


def test_validate_plate_accepts_sea_region_fill():
    plate = _plate(layers=[
        {"id": "sea", "kind": "region", "fill": "sea", "polygon": [[39.95, 26.20]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


# ── validate_plate: adversarial-review findings ─────────────────────────────


def test_validate_plate_underspecified_band_is_rejected():
    """The bug test_validate_plate_schematic_needs_no_bbox used to lock in:
    a band with only id+lines passed clean here, then crashed
    shared/lib/shield.ts's renderShield at runtime (it dereferences
    title/greek/summary unconditionally and throws on a bad ring)."""
    plate = {
        "id": "shield-of-achilles",
        "title": "The Shield of Achilles",
        "kind": "schematic",
        "status": "draft",
        "size": [640, 640],
        "bands": [{"id": "cosmos", "lines": [483, 489]}],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("title must be a non-empty string" in p for p in problems)
    assert any("greek must be a non-empty string" in p for p in problems)
    assert any("summary must be a non-empty string" in p for p in problems)
    assert any("ring must be a non-negative integer" in p for p in problems)


def test_validate_plate_band_ring_must_be_distinct():
    plate = {
        "id": "shield",
        "title": "Shield",
        "kind": "schematic",
        "status": "draft",
        "size": [10, 10],
        "bands": [
            {"id": "cosmos", "title": "Cosmos", "greek": "g", "summary": "s", "lines": [1, 2], "ring": 0},
            {"id": "peace", "title": "Peace", "greek": "g", "summary": "s", "lines": [3, 4], "ring": 0},
        ],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("duplicate ring 0" in p for p in problems)


def test_validate_plate_band_lines_must_be_ordered_int_pair():
    plate = {
        "id": "shield",
        "title": "Shield",
        "kind": "schematic",
        "status": "draft",
        "size": [10, 10],
        "bands": [
            {"id": "cosmos", "title": "Cosmos", "greek": "g", "summary": "s", "lines": [489, 483], "ring": 0},
        ],
    }
    problems = apparatus_places.validate_plate(plate, {})
    assert any("lines must be a [from, to] pair" in p for p in problems)


def test_real_shield_of_achilles_plate_validates_clean():
    """The plate carries a real plate-level `sources` array as of 2026-08-14
    (9bf6e303f: Homer's own text, and Murray) -- so it must validate clean.
    Until then this test pinned the "sources is required" gap; a plate that
    loses its sources fails here again."""
    plate_doc = json.loads(
        (ROOT / "apparatus" / "plates" / "shield-of-achilles.json").read_text(encoding="utf-8")
    )
    problems = apparatus_places.validate_plate(plate_doc, {})
    assert problems == []


def test_validate_plate_rejects_numeric_or_empty_id_and_title():
    plate = _plate(id=7, title="")
    problems = apparatus_places.validate_plate(plate, {})
    assert any("id must be a non-empty string" in p for p in problems)
    assert any("title must be a non-empty string" in p for p in problems)


def test_validate_plate_rejects_non_array_geometry_field_instead_of_skipping():
    plate = _plate(layers=[{"id": "river-1", "kind": "river", "path": "nope"}])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("path must be a list of points" in p for p in problems)


def test_validate_plate_layer_kind_list_value_reports_problem_not_raise():
    plate = _plate(layers=[{"id": "river-1", "kind": ["river"], "path": [[39.90, 26.15]]}])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("kind must be one of" in p for p in problems)


def test_validate_plate_layer_fill_list_value_reports_problem_not_raise():
    plate = _plate(layers=[
        {"id": "sea", "kind": "region", "fill": ["sea"], "polygon": [[39.95, 26.20]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("fill must be one of" in p for p in problems)


def test_validate_plate_layer_place_id_list_value_reports_problem_not_raise():
    plate = _plate(layers=[
        {"id": "town", "kind": "region", "placeId": ["troy"], "polygon": [[39.95, 26.20]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("placeId" in p and "does not resolve" in p for p in problems)


def test_validate_plate_rejects_duplicate_layer_ids():
    plate = _plate(layers=[
        {"id": "river-1", "kind": "river", "path": [[39.90, 26.15]]},
        {"id": "river-1", "kind": "river", "path": [[39.91, 26.16]]},
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("duplicate layer id 'river-1'" in p for p in problems)


def test_validate_plate_bbox_tolerates_one_ulp_over_the_edge():
    # A coordinate authored exactly on the bbox's max edge, then perturbed by
    # one ULP, must not fail containment — matches shared/lib/plate.ts's
    # assertPointsInBBox 1e-9 tolerance.
    plate = _plate(layers=[
        {"id": "river-1", "kind": "river", "path": [[40.02 + 1e-10, 26.36]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


# ── validate_places: `zone.polygon` (2026-09-02, camp-zone ruling 2e-iv) ────
# There is no mechanism (checked shared/lib/plate.ts and this module) for a
# plate layer to take its geometry FROM a gazetteer place's zone, so the
# camp-zone polygon is authored twice: once on the layer that draws it
# (apparatus/plates/trojan-plain.json's achaean-camp-zone layer) and once on
# the gazetteer entry (apparatus/places.json's achaean-camp.zone) that is the
# source of truth other plates (schematic, panorama) read to stay in sync.
# These tests hold that duplication honest: the shape is validated, and the
# equality test below fails loudly the moment the two drift.


def test_validate_places_zone_polygon_must_be_at_least_three_pairs():
    doc = {
        "status": "draft",
        "places": [_place(zone={"polygon": [[39.9, 26.1], [39.91, 26.11]]})],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("zone.polygon must have at least 3" in p for p in problems)


def test_validate_places_zone_polygon_rejects_non_numeric_pair():
    doc = {
        "status": "draft",
        "places": [
            _place(
                zone={
                    "polygon": [
                        [39.9, 26.1],
                        [39.91, "26.11"],
                        [39.92, 26.12],
                    ]
                }
            )
        ],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("zone.polygon[1] must be a 2-element numeric array" in p for p in problems)


def test_validate_places_zone_polygon_rejects_non_list():
    doc = {"status": "draft", "places": [_place(zone={"polygon": "not-a-list"})]}
    problems = apparatus_places.validate_places(doc)
    assert any("zone.polygon must be a list" in p for p in problems)


def test_validate_places_zone_good_fixture_passes():
    doc = {
        "status": "draft",
        "places": [
            _place(zone={"polygon": [[39.9, 26.1], [39.91, 26.11], [39.92, 26.12]]})
        ],
    }
    assert apparatus_places.validate_places(doc) == []


def test_real_achaean_camp_zone_polygon_matches_the_plate_layer():
    """The gazetteer is the source of truth (docstring above): this is the
    guard that catches the two authored copies drifting apart, since no
    layer-from-gazetteer consumer mechanism exists to make drift impossible
    by construction."""
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    place = next(p for p in places_doc["places"] if p["id"] == "achaean-camp")
    gazetteer_polygon = place["zone"]["polygon"]

    plate_doc = json.loads(
        (ROOT / "apparatus" / "plates" / "trojan-plain.json").read_text(encoding="utf-8")
    )
    layer = next(l for l in plate_doc["layers"] if l["id"] == "achaean-camp-zone")
    layer_polygon = layer["polygon"]

    assert gazetteer_polygon == layer_polygon, (
        "apparatus/places.json's achaean-camp.zone.polygon is the source of "
        "truth for the shared camp zone (ruling 2e-iv); it must match "
        "apparatus/plates/trojan-plain.json's achaean-camp-zone layer "
        "exactly, or the geographic, schematic and panorama plates will "
        "draw the camp on different ground."
    )
