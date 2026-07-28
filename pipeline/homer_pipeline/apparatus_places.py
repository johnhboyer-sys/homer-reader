"""Apparatus stage: validators for the Landmark-style place gazetteer
(apparatus/places.json) and the illustrated map "plates" that draw on it
(apparatus/plates/<id>.json — schema in docs/APPARATUS-SCHEMAS.md). Plate
*geometry* — bbox, layers, coordinate rings/paths — is authored by hand (a
scholarship lane) in lat/lon (or, for a schematic plate, unit [0,1]x[0,1])
JSON; a later phase projects that geometry into rendered SVG. This module
only validates; it never raises and never touches the filesystem — callers
(preflight.py) do the reading and decide what to do with the problem list.

Both validators follow apparatus_scenes.py's convention exactly: a pure
function taking an already-JSON-parsed doc and returning a list of
human-readable problem strings (empty when clean). No exception class, no
side effects.

Grandfathering: places.json already carries 280 records authored before this
schema existed. The stricter new per-place rules (`kind` required, `sources`
required) apply ONLY to records explicitly tagged for a plate — i.e. whose
`maps` array contains a tag starting with "troad-plain" or "troy-citadel" —
never to the legacy gazetteer at large. Verified against the real corpus at
the end of test_apparatus_places.py (existing tags are "greece", "journeys",
"ships", "troad", "wanderings" — none of which match those prefixes, so
today's 280 records are unaffected).
"""

from __future__ import annotations

from typing import Any

CERTAINTY_TIERS = {"certain", "traditional", "speculative", "mythical"}

PLACE_KIND_ENUM = {
    "settlement", "river", "mountain", "hill", "island", "promontory",
    "region", "plain", "harbour", "strait",
    "gate", "tower", "tomb", "spring", "ford", "camp", "wall", "shrine", "tree",
}

PLATE_TAG_PREFIXES = ("troad-plain", "troy-citadel")

PLATE_KIND_ENUM = {"geographic", "schematic"}
LAYER_KIND_ENUM = {
    "coast", "river", "relief", "shipRow", "wall", "route", "region", "band",
    # A burial mound in section, not a ridge. The tombs of Ilos and Batieia are
    # mounds on the plain, and hachuring them as relief said the wrong thing.
    "tumulus",
}
# Region/band fills, resolved through a closed whitelist in shared/lib/plate.ts.
# Kept here so the two implementations of this schema cannot drift apart again.
REGION_FILL_ENUM = {"tint", "sea"}
STOCHASTIC_STYLES = {"stipple", "hachure"}

# Layer fields that carry coordinate geometry. "rings" nests one level deeper
# than the rest: a list of rings, each ring a list of [a, b] pairs. The flat
# fields are a plain list of pairs.
_RING_FIELDS = ("rings",)
_FLAT_COORD_FIELDS = ("path", "polygon", "baseline", "trace")


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_pair(x: Any) -> bool:
    return isinstance(x, list) and len(x) == 2 and all(_is_number(v) for v in x)


# ── apparatus/places.json ───────────────────────────────────────────────────


def validate_places(doc: Any) -> list[str]:
    """Validate apparatus/places.json's whole document. Returns violation
    strings, one per problem (empty when clean)."""
    if not isinstance(doc, dict):
        return ["places.json: document must be an object"]
    places = doc.get("places")
    if not isinstance(places, list):
        return ["places.json: places must be a list"]

    problems: list[str] = []
    seen_ids: set[str] = set()
    for i, place in enumerate(places):
        if not isinstance(place, dict):
            problems.append(f"places[{i}]: must be an object")
            continue
        pid = place.get("id")
        label = pid if isinstance(pid, str) and pid else f"places[{i}]"
        if not isinstance(pid, str) or not pid:
            problems.append(f"places[{i}]: id must be a non-empty string")
        elif pid in seen_ids:
            problems.append(f"place {pid}: duplicate id")
        else:
            seen_ids.add(pid)

        certainty = place.get("certainty")
        if certainty not in CERTAINTY_TIERS:
            problems.append(
                f"place {label}: certainty must be one of {sorted(CERTAINTY_TIERS)}, "
                f"got {certainty!r}"
            )

        coords = place.get("coords")
        if coords is not None:
            if not _is_pair(coords):
                problems.append(f"place {label}: coords must be a 2-element numeric array")
            else:
                lat, lon = coords
                if not (-90 <= lat <= 90):
                    problems.append(
                        f"place {label}: coords latitude {lat} out of range [-90, 90]"
                    )
                if not (-180 <= lon <= 180):
                    problems.append(
                        f"place {label}: coords longitude {lon} out of range [-180, 180]"
                    )

        if certainty in ("traditional", "speculative"):
            tradition = place.get("tradition")
            if not isinstance(tradition, str) or not tradition.strip():
                problems.append(
                    f"place {label}: certainty {certainty!r} requires a non-empty tradition"
                )

        if certainty == "mythical" and place.get("pleiades"):
            problems.append(f"place {label}: mythical places may not carry a pleiades URL")

        sources = place.get("sources")
        if sources is not None:
            problems += _validate_sources(sources, f"place {label}")

        plate_anchors = place.get("plateAnchors")
        position_basis = place.get("positionBasis")
        if plate_anchors is not None and position_basis != "conjectural":
            problems.append(
                f"place {label}: plateAnchors present but positionBasis is not "
                f"'conjectural'"
            )
        if position_basis == "conjectural" and plate_anchors is None:
            problems.append(
                f"place {label}: positionBasis 'conjectural' requires plateAnchors"
            )
        if plate_anchors is not None:
            if not isinstance(plate_anchors, dict):
                problems.append(f"place {label}: plateAnchors must be an object")
            else:
                for plate_id, uv in plate_anchors.items():
                    if not _is_pair(uv) or not all(0 <= v <= 1 for v in uv):
                        problems.append(
                            f"place {label}: plateAnchors[{plate_id!r}] must be a "
                            f"[u, v] pair in 0..1"
                        )

        kind = place.get("kind")
        if kind is not None and kind not in PLACE_KIND_ENUM:
            problems.append(f"place {label}: kind {kind!r} not in {sorted(PLACE_KIND_ENUM)}")

        maps = place.get("maps") if isinstance(place.get("maps"), list) else []
        tagged_for_plate = any(
            isinstance(tag, str) and tag.startswith(PLATE_TAG_PREFIXES) for tag in maps
        )
        if tagged_for_plate:
            if kind is None:
                problems.append(f"place {label}: kind is required (tagged for a plate via maps)")
            if not sources:
                problems.append(
                    f"place {label}: sources is required (tagged for a plate via maps)"
                )

    return problems


def _validate_sources(sources: Any, label: str) -> list[str]:
    """Shared cite/url shape check for both places.json entries and plate
    layers. CLAUDE.md's citation rule: every source needs a non-empty
    `cite`; a `url`, when present, must be http(s) (the hyperlink-to-source
    convention for web resources)."""
    if not isinstance(sources, list):
        return [f"{label}: sources must be a list"]
    problems: list[str] = []
    for j, src in enumerate(sources):
        if not isinstance(src, dict):
            problems.append(f"{label}: sources[{j}] must be an object")
            continue
        cite = src.get("cite")
        if not isinstance(cite, str) or not cite.strip():
            problems.append(f"{label}: sources[{j}].cite must be a non-empty string")
        url = src.get("url")
        if url is not None and not (
            isinstance(url, str) and url.startswith(("http://", "https://"))
        ):
            problems.append(f"{label}: sources[{j}].url must be http(s)")
    return problems


# ── apparatus/plates/<id>.json ──────────────────────────────────────────────


def _iter_layer_coords(layer: dict):
    """Yield (field_name, pair, path_desc) for every coordinate pair present
    in a plate layer's geometry fields."""
    for field in _RING_FIELDS:
        rings = layer.get(field)
        if not isinstance(rings, list):
            continue
        for ri, ring in enumerate(rings):
            if not isinstance(ring, list):
                continue
            for pi, pair in enumerate(ring):
                yield field, pair, f"[{ri}][{pi}]"
    for field in _FLAT_COORD_FIELDS:
        coords = layer.get(field)
        if not isinstance(coords, list):
            continue
        for pi, pair in enumerate(coords):
            yield field, pair, f"[{pi}]"


def validate_plate(doc: Any, places_by_id: dict[str, Any]) -> list[str]:
    """Validate one apparatus/plates/<id>.json document. `places_by_id` is
    the gazetteer's id -> place dict, used to resolve layer `placeId`
    references. Returns violation strings (empty when clean).

    The highest-value check here is the bbox containment test on every
    geographic-plate coordinate: it catches transposed lat/lon, the single
    most likely authoring error. A schematic plate's coordinates are checked
    against 0..1 instead; no separate "looks like lat/lon" heuristic is
    needed on top of that, because this project's real bboxes (Aegean
    lat/lon, tens of degrees) and the unit range 0..1 never overlap — a pair
    valid under one system is definitionally invalid under the other.
    """
    if not isinstance(doc, dict):
        return ["plate: document must be an object"]

    plate_id = doc.get("id")
    label = plate_id if isinstance(plate_id, str) and plate_id else "plate"
    problems: list[str] = []

    kind = doc.get("kind")
    if "kind" in doc and kind not in PLATE_KIND_ENUM:
        problems.append(f"{label}: kind must be one of {sorted(PLATE_KIND_ENUM)}, got {kind!r}")

    # Required keys depend on the kind, because the two kinds are different
    # things wearing one schema. A geographic plate is drawn by projecting
    # lat/lon through geo.ts, so it must declare the `bbox` it projects into
    # and the geographic `layers` it draws. A schematic plate has no geography
    # at all — the Shield of Achilles is concentric `bands` of Iliad 18, not a
    # place — so demanding a bbox of it would be demanding a coordinate for
    # something that has none.
    required = ["id", "title", "kind", "status", "size"]
    if kind != "schematic":
        required += ["bbox", "layers"]
    for key in required:
        if key not in doc:
            problems.append(f"{label}: missing required key {key!r}")

    # A schematic plate draws either concentric `bands` (the Shield of Achilles)
    # or unit-space `layers` (the Trojan plain as the poem lays it out), so it
    # must carry at least one of the two — an empty schematic draws nothing.
    if kind == "schematic" and "bands" not in doc and "layers" not in doc:
        problems.append(f"{label}: a schematic plate must declare 'bands' or 'layers'")

    bands = doc.get("bands")
    if "bands" in doc:
        if not isinstance(bands, list) or not bands:
            problems.append(f"{label}: bands must be a non-empty list")
        else:
            seen_band_ids: set[str] = set()
            for i, band in enumerate(bands):
                if not isinstance(band, dict):
                    problems.append(f"{label}: bands[{i}] must be an object")
                    continue
                band_id = band.get("id")
                if not isinstance(band_id, str) or not band_id:
                    problems.append(f"{label}: bands[{i}].id must be a non-empty string")
                elif band_id in seen_band_ids:
                    problems.append(f"{label}: duplicate band id {band_id!r}")
                else:
                    seen_band_ids.add(band_id)

    if "status" in doc and (not isinstance(doc.get("status"), str) or not doc["status"].strip()):
        problems.append(f"{label}: status must be a non-empty string")

    bbox = doc.get("bbox")
    min_lat = min_lon = max_lat = max_lon = None
    if "bbox" in doc:
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(v) for v in bbox):
            problems.append(
                f"{label}: bbox must be a 4-element numeric array "
                f"[minLat, minLon, maxLat, maxLon]"
            )
        else:
            min_lat, min_lon, max_lat, max_lon = bbox
            if not (min_lat < max_lat):
                problems.append(f"{label}: bbox minLat {min_lat} must be < maxLat {max_lat}")
            if not (min_lon < max_lon):
                problems.append(f"{label}: bbox minLon {min_lon} must be < maxLon {max_lon}")

    size = doc.get("size")
    if "size" in doc and (
        not isinstance(size, list) or len(size) != 2 or not all(_is_number(v) and v > 0 for v in size)
    ):
        problems.append(f"{label}: size must be a 2-element array of positive numbers")

    layers = doc.get("layers")
    if "layers" in doc and not isinstance(layers, list):
        problems.append(f"{label}: layers must be a list")
        layers = []
    layers = layers or []

    needs_seed = False
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            problems.append(f"{label}: layers[{i}] must be an object")
            continue
        layer_id = layer.get("id")
        layer_label = layer_id if isinstance(layer_id, str) and layer_id else f"layers[{i}]"
        if not isinstance(layer_id, str) or not layer_id:
            problems.append(f"{label}: layers[{i}].id must be a non-empty string")

        layer_kind = layer.get("kind")
        if layer_kind not in LAYER_KIND_ENUM:
            problems.append(
                f"{label}: layer {layer_label} kind must be one of "
                f"{sorted(LAYER_KIND_ENUM)}, got {layer_kind!r}"
            )

        place_id = layer.get("placeId")
        if place_id is not None and place_id not in places_by_id:
            problems.append(
                f"{label}: layer {layer_label} placeId {place_id!r} does not resolve "
                f"in the gazetteer"
            )

        default = layer.get("default")
        if default is not None and default not in ("on", "off"):
            problems.append(f"{label}: layer {layer_label} default must be 'on' or 'off'")

        fill = layer.get("fill")
        if fill is not None and fill not in REGION_FILL_ENUM:
            problems.append(
                f"{label}: layer {layer_label} fill must be one of "
                f"{sorted(REGION_FILL_ENUM)}, got {fill!r}"
            )

        if layer.get("style") in STOCHASTIC_STYLES:
            needs_seed = True

        sources = layer.get("sources")
        if sources is not None:
            problems += _validate_sources(sources, f"{label}: layer {layer_label}")

        for field, pair, path_desc in _iter_layer_coords(layer):
            if not _is_pair(pair):
                problems.append(
                    f"{label}: layer {layer_label} {field}{path_desc} must be a "
                    f"[a, b] numeric pair"
                )
                continue
            a, b = pair
            if kind == "geographic":
                if min_lat is None:
                    continue  # bbox itself already flagged invalid above
                if not (min_lat <= a <= max_lat and min_lon <= b <= max_lon):
                    problems.append(
                        f"{label}: layer {layer_label} {field}{path_desc} = [{a}, {b}] "
                        f"lies outside bbox {bbox}"
                    )
            elif kind == "schematic":
                if not (0 <= a <= 1 and 0 <= b <= 1):
                    problems.append(
                        f"{label}: layer {layer_label} {field}{path_desc} = [{a}, {b}] "
                        f"must be a unit [u, v] pair in 0..1"
                    )

    if needs_seed and "seed" not in doc:
        problems.append(f"{label}: seed is required (a layer uses a stochastic style)")

    return problems
