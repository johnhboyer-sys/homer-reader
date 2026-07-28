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


def test_validate_plate_schematic_rejects_lat_lon_coordinates():
    plate = _plate(
        kind="schematic",
        bbox=[0, 0, 1, 1],
        layers=[{"id": "river-1", "kind": "river", "path": [[39.90, 26.15]]}],
    )
    problems = apparatus_places.validate_plate(plate, {})
    assert any("must be a unit [u, v] pair in 0..1" in p for p in problems)


def test_validate_plate_schematic_accepts_unit_coordinates():
    plate = _plate(
        kind="schematic",
        bbox=[0, 0, 1, 1],
        layers=[{"id": "river-1", "kind": "river", "path": [[0.2, 0.4]]}],
    )
    assert apparatus_places.validate_plate(plate, {}) == []


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
