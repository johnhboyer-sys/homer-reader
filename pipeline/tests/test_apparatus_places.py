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
    # Range is no longer this validator's job: a lat/lon pair is a legal
    # shape here. Pairing with positionBasis still is.
    doc = {"status": "draft", "places": [_place(plateAnchors={"trojan-plain": [39.95, 26.20]})]}
    problems = apparatus_places.validate_places(doc)
    assert any("positionBasis is not 'conjectural'" in p for p in problems)


def test_validate_places_position_basis_without_plate_anchors_rejected():
    doc = {"status": "draft", "places": [_place(positionBasis="conjectural")]}
    problems = apparatus_places.validate_places(doc)
    assert any("requires plateAnchors" in p for p in problems)


def test_validate_places_plate_anchors_with_position_basis_passes():
    # A lat/lon pair (not in 0..1) must pass here — the range check lives
    # on validate_plate, which knows whether THIS plate has a bbox.
    doc = {
        "status": "draft",
        "places": [
            _place(
                plateAnchors={"trojan-plain": [39.95, 26.20]},
                positionBasis="conjectural",
            )
        ],
    }
    assert apparatus_places.validate_places(doc) == []


def test_validate_places_plate_anchors_must_be_a_2_number_list():
    doc = {
        "status": "draft",
        "places": [
            _place(
                plateAnchors={"trojan-plain": [0.5]},
                positionBasis="conjectural",
            )
        ],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("plateAnchors['trojan-plain'] must be a 2-element numeric array" in p for p in problems)


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


# Finding F4 (stage 6 review, 2026-09-03): marginRight was not checked
# against size[0] at all on the Python side; a plate whose margin ate the
# whole sheet width (or more) passed preflight clean and only broke at
# render time in shared/lib/plate.ts (frameWidth = width - marginRight goes
# negative).
def test_validate_plate_rejects_margin_right_at_size_width():
    plate = _plate(marginRight=880)  # equals size[0], leaves no map frame
    problems = apparatus_places.validate_plate(plate, {})
    assert any("marginRight" in p and "must be less than size[0]" in p for p in problems)


def test_validate_plate_rejects_margin_right_over_size_width():
    plate = _plate(marginRight=1000)  # exceeds size[0] = 880
    problems = apparatus_places.validate_plate(plate, {})
    assert any("marginRight" in p and "must be less than size[0]" in p for p in problems)


def test_validate_plate_accepts_margin_right_under_size_width():
    plate = _plate(marginRight=200)
    problems = apparatus_places.validate_plate(plate, {})
    assert problems == []


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


def test_validate_plate_accepts_lat_lon_anchor_inside_bbox():
    plate = _plate()
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"testplate": [39.95, 26.20]},
            "positionBasis": "conjectural",
        }
    }
    assert apparatus_places.validate_plate(plate, places) == []


def test_validate_plate_rejects_lat_lon_anchor_outside_bbox():
    plate = _plate()
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"testplate": [0.2, 0.4]},
            "positionBasis": "conjectural",
        }
    }
    problems = apparatus_places.validate_plate(plate, places)
    assert any("plateAnchors['testplate']" in p and "lies outside bbox" in p for p in problems)


def test_validate_plate_without_bbox_still_requires_unit_anchor():
    plate = _plate(
        kind="schematic",
        layers=[{"id": "river-1", "kind": "river", "path": [[0.2, 0.4]]}],
    )
    del plate["bbox"]
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"testplate": [39.95, 26.20]},
            "positionBasis": "conjectural",
        }
    }
    problems = apparatus_places.validate_plate(plate, places)
    assert any(
        "plateAnchors['testplate']" in p and "must be a unit [u, v] pair in 0..1" in p
        for p in problems
    )


def test_validate_plate_ignores_anchor_keyed_for_a_different_plate():
    plate = _plate()
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"some-other-plate": [0.2, 0.4]},
            "positionBasis": "conjectural",
        }
    }
    assert apparatus_places.validate_plate(plate, places) == []


def test_validate_plate_accepts_inset_frame_in_the_margin_with_unit_polygon():
    plate = _plate(
        size=[880, 620],
        layers=[
            {
                "id": "locator",
                "kind": "region",
                "style": "inset",
                "frame": [700, 20, 160, 120],
                "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
            }
        ],
    )
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_rejects_inset_frame_outside_the_sheet():
    plate = _plate(
        size=[880, 620],
        layers=[
            {
                "id": "locator",
                "kind": "region",
                "style": "inset",
                "frame": [800, 10, 200, 100],
                "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]],
            }
        ],
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("frame" in p and "outside" in p for p in problems)


def test_validate_plate_accepts_scene_key_naming_a_layer():
    plate = _plate(
        layers=[
            {
                "id": "zone-camp",
                "kind": "region",
                "polygon": [[39.90, 26.15], [39.92, 26.18], [39.90, 26.20]],
            }
        ],
        sceneKey=[
            {"letter": "A", "title": "The camp", "ref": "Il. 8.222–26", "layerId": "zone-camp"}
        ],
    )
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_rejects_scene_key_layer_id_that_is_not_a_layer():
    plate = _plate(
        sceneKey=[
            {"letter": "A", "title": "The camp", "ref": "Il. 8.222–26", "layerId": "no-such"}
        ]
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("sceneKey" in p and "layerId" in p and "no-such" in p for p in problems)


def test_validate_plate_rejects_duplicate_scene_key_letter():
    # F3, 2026-09-03 stage 6 review: two rows sharing a letter draw one
    # glyph on the sheet for two different keyed rows.
    plate = _plate(
        layers=[
            {
                "id": "zone-camp",
                "kind": "region",
                "polygon": [[39.90, 26.15], [39.92, 26.18], [39.90, 26.20]],
            },
            {"id": "mound", "kind": "tumulus", "path": [[39.90, 26.15]]},
        ],
        sceneKey=[
            {"letter": "A", "title": "The camp", "ref": "Il. 8.222–26", "layerId": "zone-camp"},
            {"letter": "A", "title": "The mound", "ref": "Il. 23.245", "layerId": "mound"},
        ],
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any(
        "sceneKey" in p and "'A'" in p and "more than once" in p for p in problems
    )


def test_validate_plate_accepts_distinct_scene_key_letters():
    plate = _plate(
        layers=[
            {
                "id": "zone-camp",
                "kind": "region",
                "polygon": [[39.90, 26.15], [39.92, 26.18], [39.90, 26.20]],
            },
            {"id": "mound", "kind": "tumulus", "path": [[39.90, 26.15]]},
        ],
        sceneKey=[
            {"letter": "A", "title": "The camp", "ref": "Il. 8.222–26", "layerId": "zone-camp"},
            {"letter": "B", "title": "The mound", "ref": "Il. 23.245", "layerId": "mound"},
        ],
    )
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_accepts_feature_key_naming_an_anchored_place_and_a_layer():
    plate = _plate(
        id="keyed-plate",
        layers=[
            {
                "id": "mound",
                "kind": "tumulus",
                "path": [[39.90, 26.15]],
            }
        ],
        featureKey=[
            {
                "title": "The camp and its wall",
                "items": [
                    {"placeId": "camp", "label": "The camp"},
                    {"layerId": "mound", "label": "Patroclus"},
                ],
            }
        ],
    )
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"keyed-plate": [39.90, 26.15]},
            "positionBasis": "conjectural",
        }
    }
    assert apparatus_places.validate_plate(plate, places) == []


def test_validate_plate_rejects_feature_key_empty_title():
    plate = _plate(featureKey=[{"title": "  ", "items": [{"placeId": "camp"}]}])
    problems = apparatus_places.validate_plate(plate, {"camp": {"id": "camp"}})
    assert any("featureKey" in p and "title" in p for p in problems)


def test_validate_plate_rejects_feature_key_item_with_both_ids():
    plate = _plate(
        layers=[{"id": "mound", "kind": "tumulus", "path": [[39.90, 26.15]]}],
        featureKey=[
            {
                "title": "The camp and its wall",
                "items": [{"placeId": "camp", "layerId": "mound"}],
            }
        ],
    )
    problems = apparatus_places.validate_plate(plate, {"camp": {"id": "camp"}})
    assert any("featureKey" in p and "exactly one" in p for p in problems)


def test_validate_plate_rejects_feature_key_item_with_neither_id():
    plate = _plate(
        featureKey=[{"title": "The camp and its wall", "items": [{"label": "The camp"}]}]
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("featureKey" in p and "exactly one" in p for p in problems)


def test_validate_plate_rejects_feature_key_layer_id_that_is_not_a_layer():
    plate = _plate(
        featureKey=[
            {
                "title": "The camp and its wall",
                "items": [{"layerId": "no-such", "label": "Patroclus"}],
            }
        ]
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("featureKey" in p and "layerId" in p and "no-such" in p for p in problems)


def test_validate_plate_rejects_feature_key_place_id_not_anchored_on_this_plate():
    plate = _plate(
        id="keyed-plate",
        featureKey=[
            {
                "title": "The camp and its wall",
                "items": [{"placeId": "camp", "label": "The camp"}],
            }
        ],
    )
    places = {"camp": {"id": "camp"}}
    problems = apparatus_places.validate_plate(plate, places)
    assert any("featureKey" in p and "anchored" in p and "camp" in p for p in problems)


def test_validate_plate_rejects_feature_key_duplicate_ids():
    plate = _plate(
        featureKey=[
            {
                "title": "The camp and its wall",
                "items": [
                    {"placeId": "camp", "label": "A"},
                    {"placeId": "camp", "label": "B"},
                ],
            }
        ],
    )
    places = {
        "camp": {
            "id": "camp",
            "plateAnchors": {"testplate": [39.90, 26.15]},
            "positionBasis": "conjectural",
        }
    }
    problems = apparatus_places.validate_plate(plate, places)
    assert any("featureKey" in p and "twice" in p for p in problems)


def test_validate_plate_accepts_suppress_layer_labels_naming_a_layer():
    plate = _plate(suppressLayerLabels=["river-1"])
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_rejects_suppress_layer_labels_id_that_is_not_a_layer():
    plate = _plate(suppressLayerLabels=["no-such"])
    problems = apparatus_places.validate_plate(plate, {})
    assert any(
        "suppressLayerLabels" in p and "no-such" in p for p in problems
    )


def test_validate_plate_rejects_suppress_layer_labels_that_is_not_a_list():
    plate = _plate(suppressLayerLabels="river-1")
    problems = apparatus_places.validate_plate(plate, {})
    assert any("suppressLayerLabels must be a list" in p for p in problems)


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


def _schematic_plate() -> dict:
    return json.loads(
        (ROOT / "apparatus" / "plates" / "trojan-plain-schematic.json").read_text(encoding="utf-8")
    )


def _schematic_places() -> dict:
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    return {p["id"]: p for p in places_doc["places"]}


# Ruling 10 (2026-09-03): the citadel is a margin inset, so a framed inset
# panel may declare `insetBBox` (the ground it shows), layers may name it in
# `insetOf`, and a featureKey group may route its numerals into it with
# `inset`. All three are references, and a typo in one silently drops content
# off the sheet -- which is what these check.
def test_inset_of_must_name_a_framed_inset_panel():
    plate = _schematic_plate()
    for layer in plate["layers"]:
        if layer.get("insetOf"):
            layer["insetOf"] = "no-such-panel"
    problems = apparatus_places.validate_plate(plate, _schematic_places())
    assert any("insetOf 'no-such-panel'" in p for p in problems), problems


def test_feature_key_group_inset_must_name_a_framed_inset_panel():
    plate = _schematic_plate()
    for group in plate["featureKey"]:
        if group.get("inset"):
            group["inset"] = "no-such-panel"
    problems = apparatus_places.validate_plate(plate, _schematic_places())
    assert any("inset 'no-such-panel'" in p for p in problems), problems


def test_inset_bbox_must_be_well_formed_and_on_a_framed_panel():
    plate = _schematic_plate()
    for layer in plate["layers"]:
        if layer.get("insetBBox"):
            layer["insetBBox"] = [1, 2, 3]
    problems = apparatus_places.validate_plate(plate, _schematic_places())
    assert any("insetBBox must be a 4-element" in p for p in problems), problems

    plate = _schematic_plate()
    for layer in plate["layers"]:
        if layer.get("insetBBox"):
            layer.pop("frame")
    problems = apparatus_places.validate_plate(plate, _schematic_places())
    assert any(
        "citadel-inset-panel has an insetBBox but is not a framed inset panel" in p
        for p in problems
    ), problems


def test_inset_bbox_must_not_be_inverted():
    plate = _schematic_plate()
    for layer in plate["layers"]:
        if layer.get("insetBBox"):
            lat0, lon0, lat1, lon1 = layer["insetBBox"]
            layer["insetBBox"] = [lat1, lon1, lat0, lon0]
    problems = apparatus_places.validate_plate(plate, _schematic_places())
    assert any("maxLat > minLat" in p for p in problems), problems


def test_real_trojan_plain_schematic_plate_validates_clean():
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    places_by_id = {p["id"]: p for p in places_doc["places"]}
    plate_doc = json.loads(
        (ROOT / "apparatus" / "plates" / "trojan-plain-schematic.json").read_text(encoding="utf-8")
    )
    plate_problems = apparatus_places.validate_plate(plate_doc, places_by_id)
    assert plate_problems == [], plate_problems


# ── validate_plate_anchors: plateAnchors keys against the real plate set ────
# (F3, 2026-09-03 stage 6 review)


def test_validate_plate_anchors_rejects_unknown_plate_id():
    places_by_id = {
        "camp": {"id": "camp", "plateAnchors": {"trojan-plain-schematicc": [0.2, 0.4]}}
    }
    problems = apparatus_places.validate_plate_anchors(
        places_by_id, {"trojan-plain-schematic"}
    )
    assert any("trojan-plain-schematicc" in p and "camp" in p for p in problems)


def test_validate_plate_anchors_accepts_known_plate_id():
    places_by_id = {
        "camp": {"id": "camp", "plateAnchors": {"trojan-plain-schematic": [0.2, 0.4]}}
    }
    assert (
        apparatus_places.validate_plate_anchors(places_by_id, {"trojan-plain-schematic"})
        == []
    )


def test_validate_plate_anchors_ignores_places_without_plate_anchors():
    places_by_id = {"camp": {"id": "camp"}}
    assert apparatus_places.validate_plate_anchors(places_by_id, set()) == []


def test_real_place_anchors_resolve_against_the_real_plate_set():
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    places_by_id = {p["id"]: p for p in places_doc["places"]}
    plate_ids = {p.stem for p in (ROOT / "apparatus" / "plates").glob("*.json")}
    problems = apparatus_places.validate_plate_anchors(places_by_id, plate_ids)
    assert problems == [], problems


def test_camp_label_tiers_declutter_the_beach_crop():
    """Stage 5b: John's LOOK-gate verdict on the camp crop ("that's a mess")
    found six tier-1 labels stacked on ~450px of beach. The fix promotes
    three sector zone layers to tier 1 (by holder: Achilles, Odysseus/the
    centre, Ajax), each with its own short `label`; every individual feature
    pin (the assembly, the wall-and-ditch, and the huts of Odysseus/Ajax/
    Achilles) is demoted to tier 2. `achaean-camp` itself stays the tier-1
    settlement pin it always was: a `region` reading of the same shared camp
    polygon was tried and abandoned (see the "No id overrides" comment in
    shared/lib/plate.ts) because its centroid sits on the ship/wall drawing
    it names, and — this stage's own finding — on top of
    `station-of-odysseus`'s centroid (both are un-collision-checked "centred"
    area requests). This locks the places.json half of the fix in as data,
    so a future edit that silently re-promotes one of the five demoted items
    back to tier 1 fails loudly."""
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    places_by_id = {p["id"]: p for p in places_doc["places"]}

    assert places_by_id["achaean-camp"]["labelTier"] == 1, "achaean-camp stays the tier-1 settlement pin"

    demoted_to_tier_2 = [
        "achaean-wall-and-ditch",
        "achaean-assembly-place",
        "hut-of-odysseus",
        "hut-of-ajax",
        "hut-of-achilles",
    ]
    for place_id in demoted_to_tier_2:
        place = places_by_id[place_id]
        assert place["labelTier"] == 2, f"{place_id} must be labelTier 2 (an individual camp feature, not a sector)"

    plate_doc = json.loads(
        (ROOT / "apparatus" / "plates" / "trojan-plain-schematic.json").read_text(encoding="utf-8")
    )
    layers_by_id = {layer["id"]: layer for layer in plate_doc["layers"]}

    # The `achaean-camp` region LAYER (as opposed to the place pin above)
    # stays inert — no `label` of its own — so the settlement pin remains
    # the sole tier-1 voice for the camp-wide name.
    achaean_camp_layer = layers_by_id["achaean-camp"]
    assert "label" not in achaean_camp_layer, "achaean-camp layer must not duplicate the settlement pin's name"

    # Stage 5c: sector captions leave the face. The polygons still draw;
    # the holder names are now group headings in the numbered key.
    for layer_id in (
        "station-of-achilles",
        "station-of-odysseus",
        "station-of-ajax",
    ):
        layer = layers_by_id[layer_id]
        assert "label" not in layer, f"{layer_id} must not letter a sector caption"

    # The three main shipRow layers keep three ranks (Il. 14.30-36) but thin
    # to 8 glyphs/rank (John: "I don't think we need so many ships in there").
    for ship_layer_id in ("ships-achilles-end", "ships-centre", "ships-ajax-end"):
        layer = layers_by_id[ship_layer_id]
        assert layer["rows"] == 3
        assert layer["count"] == 8


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


def test_validate_plate_accepts_zone_region_fill():
    # "zone" (2026-09-02, stage 4b LOOK-gate fix): the apparatus's own
    # lettered scene band, mirroring shared/lib/plate.ts's REGION_FILL_TOKENS.
    plate = _plate(layers=[
        {"id": "zone-a", "kind": "region", "fill": "zone", "polygon": [[39.95, 26.20]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_places_accepts_label_tier_and_size():
    assert apparatus_places.validate_places(
        {"status": "draft", "places": [_place(labelTier=1, labelSize="small")]}
    ) == []
    assert apparatus_places.validate_places(
        {"status": "draft", "places": [_place(labelTier=2, labelSize="base")]}
    ) == []


def test_validate_places_rejects_bad_label_tier_and_size():
    problems = apparatus_places.validate_places(
        {"status": "draft", "places": [_place(labelTier=3)]}
    )
    assert any("labelTier must be 1 or 2" in p for p in problems)
    problems = apparatus_places.validate_places(
        {"status": "draft", "places": [_place(labelSize="tiny")]}
    )
    assert any("labelSize must be 'small' or 'base'" in p for p in problems)


def test_validate_plate_accepts_label_tier_and_size_on_a_layer():
    plate = _plate(layers=[
        {"id": "r", "kind": "region", "labelTier": 2, "labelSize": "small",
         "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []
    plate = _plate(layers=[
        {"id": "r", "kind": "region", "labelTier": 1, "labelSize": "base",
         "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
    ])
    assert apparatus_places.validate_plate(plate, {}) == []


def test_validate_plate_rejects_bad_label_tier_and_size_on_a_layer():
    plate = _plate(layers=[
        {"id": "r", "kind": "region", "labelTier": 3,
         "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("labelTier must be 1 or 2" in p for p in problems)
    plate = _plate(layers=[
        {"id": "r", "kind": "region", "labelSize": "tiny",
         "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("labelSize must be 'small' or 'base'" in p for p in problems)


# 2026-09-03 review, finding 5: a layer had no certainty tier of its own,
# right for drawn geometry and wrong for a layer that IS a claim (the
# citadel's poem-drawn buildings have no gazetteer place of their own to
# carry a tier through). Mirrors CERTAINTY_TIERS, the same set validate_places
# already enforces on a place.
def test_validate_plate_accepts_certainty_on_a_layer():
    for tier in sorted(apparatus_places.CERTAINTY_TIERS):
        plate = _plate(layers=[
            {"id": "r", "kind": "region", "certainty": tier,
             "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
        ])
        assert apparatus_places.validate_plate(plate, {}) == [], tier


def test_validate_plate_rejects_unknown_certainty_on_a_layer():
    plate = _plate(layers=[
        {"id": "r", "kind": "region", "certainty": "confirmed",
         "polygon": [[39.90, 26.15], [39.91, 26.16], [39.90, 26.17]]}
    ])
    problems = apparatus_places.validate_plate(plate, {})
    assert any("certainty must be one of" in p for p in problems)


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


def test_real_plate_anchors_validate_against_every_real_plate():
    """The plateAnchors range check moved from validate_places into
    validate_plate (it must know whether THIS plate has a bbox). Prove it
    actually runs clean against the real gazetteer and every real plate,
    the way preflight.py's loop does — including the places anchored
    to trojan-plain-schematic, whose bbox means those anchors are lat/lon."""
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    places_by_id = {
        p["id"]: p
        for p in places_doc.get("places", [])
        if isinstance(p, dict) and isinstance(p.get("id"), str)
    }

    schematic_anchor_count = sum(
        1
        for p in places_by_id.values()
        if isinstance(p.get("plateAnchors"), dict)
        and "trojan-plain-schematic" in p["plateAnchors"]
    )
    assert schematic_anchor_count == 35, (
        f"expected 35 places anchored to trojan-plain-schematic, found "
        f"{schematic_anchor_count} — the plate list below assumes this "
        f"fixture count; update it if the gazetteer legitimately changed."
    )

    plates_dir = ROOT / "apparatus" / "plates"
    plate_paths = sorted(plates_dir.glob("*.json"))
    assert plate_paths, "expected real plates in apparatus/plates/"

    all_problems: list[str] = []
    for plate_path in plate_paths:
        plate_doc = json.loads(plate_path.read_text(encoding="utf-8"))
        all_problems += [
            f"{plate_path.name}: {msg}"
            for msg in apparatus_places.validate_plate(plate_doc, places_by_id)
        ]

    assert all_problems == []


# ── geo-enrich gazetteer entries (2026-09-02) ───────────────────────────────
# The new and updated Trojan-plain records must validate against the live
# corpus, and every one of them carries a non-empty sources array (CLAUDE.md:
# every sourced claim in the data).


_GEO_ENRICH_PLACE_IDS = (
    "besik-bay",
    "thymbrios",
    "pinarbasi",
    "tomb-of-ajax-in-tepe",
    "kesik-basin",
)


def test_real_geo_enrich_places_validate_and_carry_sources():
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in places_doc["places"]}
    for pid in _GEO_ENRICH_PLACE_IDS:
        place = by_id.get(pid)
        assert place is not None, f"gazetteer is missing {pid}"
        sources = place.get("sources")
        assert isinstance(sources, list) and sources, f"{pid} has empty sources"
        for j, src in enumerate(sources):
            assert isinstance(src, dict), f"{pid} sources[{j}] must be an object"
            cite = src.get("cite")
            assert isinstance(cite, str) and cite.strip(), (
                f"{pid} sources[{j}].cite must be a non-empty string"
            )
    problems = apparatus_places.validate_places(places_doc)
    assert problems == [], problems


# ── mentions referential integrity (2026-09-02, stage 4c) ───────────────────
#
# The rule: every `mentions[]` entry's `{work, book, lines}` must name a real
# book (1-24, both works) and a real line within that book's vulgate length
# (manifests/<Work>.yaml's `books[].end`). It is a pure bounds check.
#
# IMPORTANT LIMITATION, stated here because a bounds check cannot state it in
# its own problem messages: two of the real findings this rule was written
# after fixing were document section numbers -- "(§3.5)" and "(§1.75)",
# left unresolved in prose -- harvested as if they were verse refs into
# `mentions` entries reading book 3 line 5 and book 1 line 75. BOTH of those
# are perfectly real, in-range lines (Iliad 3 has 461 lines; Iliad 1 has 611)
# that simply have nothing to do with the place they were attached to (3.5 is
# the crane simile, not "the road to the ships"; 1.75 is Calchas asking
# Achilles for protection, not the Simoeis-Scamander confluence). A range
# check is structurally incapable of catching a wrong-but-existing citation;
# that class of error was caught here only by reading the Greek at the cited
# line and checking it against the place's own claim. This rule instead
# catches the other, disjoint failure mode: a book or line number that does
# not exist at all (confirmed empty on the real corpus as of this fix --
# see test_real_places_mentions_pass_the_line_bounds_check below).


def test_validate_places_mentions_rejects_book_out_of_range():
    doc = {
        "status": "draft",
        "places": [_place(mentions=[{"work": "iliad", "book": 25, "lines": [1, 1]}])],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("book 25 must be an integer 1-24" in p for p in problems)


def test_validate_places_mentions_rejects_book_zero():
    doc = {
        "status": "draft",
        "places": [_place(mentions=[{"work": "odyssey", "book": 0, "lines": [1, 1]}])],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("book 0 must be an integer 1-24" in p for p in problems)


def test_validate_places_mentions_rejects_line_past_book_end():
    # Iliad book 1 is 611 lines (manifests/Iliad.yaml); 612 does not exist.
    doc = {
        "status": "draft",
        "places": [_place(mentions=[{"work": "iliad", "book": 1, "lines": [1, 612]}])],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("iliad 1.612 exceeds book 1's length (611 lines)" in p for p in problems)


def test_validate_places_mentions_accepts_the_books_last_line():
    # The boundary itself must validate clean (611 is in range, 612 is not).
    doc = {
        "status": "draft",
        "places": [_place(mentions=[{"work": "iliad", "book": 1, "lines": [1, 611]}])],
    }
    assert apparatus_places.validate_places(doc) == []


def test_validate_places_mentions_checks_odyssey_book_lengths_independently():
    # Odyssey book 1 is 444 lines, not 611 -- the two works' tables must not
    # be conflated.
    doc = {
        "status": "draft",
        "places": [_place(mentions=[{"work": "odyssey", "book": 1, "lines": [1, 445]}])],
    }
    problems = apparatus_places.validate_places(doc)
    assert any("odyssey 1.445 exceeds book 1's length (444 lines)" in p for p in problems)


def test_validate_places_mentions_must_be_a_list():
    doc = {"status": "draft", "places": [_place(mentions="1.75")]}
    problems = apparatus_places.validate_places(doc)
    assert any("mentions must be a list" in p for p in problems)


def test_validate_places_mentions_entry_must_be_an_object():
    doc = {"status": "draft", "places": [_place(mentions=["1.75"])]}
    problems = apparatus_places.validate_places(doc)
    assert any("mentions[0] must be an object" in p for p in problems)


def test_validate_places_mentions_good_fixture_passes():
    doc = {
        "status": "draft",
        "places": [
            _place(
                mentions=[
                    {"work": "iliad", "book": 6, "lines": [433, 434]},
                    {"work": "odyssey", "book": 9, "lines": [39, 40]},
                ]
            )
        ],
    }
    assert apparatus_places.validate_places(doc) == []


def test_real_places_mentions_pass_the_line_bounds_check():
    """The new rule, run against the live gazetteer after the stage 4c
    content fixes (hut-of-ajax, fig-tree, road-to-the-ships,
    scamander-simoeis-confluence, hut-of-nestor, pyre-of-patroclus,
    funeral-games-ground and the rest): zero problems. This does not prove
    every citation is semantically right -- see the module docstring above
    for the two that were in-range and wrong regardless -- only that no
    `mentions` entry names a book or line that does not exist."""
    places_doc = json.loads((ROOT / "apparatus" / "places.json").read_text(encoding="utf-8"))
    problems = [
        p for p in apparatus_places.validate_places(places_doc) if "mentions[" in p
    ]
    assert problems == [], problems
