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

from functools import lru_cache
from typing import Any

CERTAINTY_TIERS = {"certain", "traditional", "speculative", "mythical"}

PLACE_KIND_ENUM = {
    "settlement", "river", "mountain", "hill", "island", "promontory",
    "region", "plain", "harbour", "strait",
    "gate", "tower", "tomb", "spring", "ford", "camp", "wall", "shrine", "tree",
}

PLATE_TAG_PREFIXES = ("troad-plain", "troy-citadel")

# shared/lib/plate.ts's assertPointsInBBox/assertPointsInUnitRange both use
# this same 1e-9 tolerance on their boundary checks: exact float equality on
# an authored boundary coordinate is a real hazard (a coordinate authored as
# the bbox edge can fail containment by one ULP). Kept as one constant so the
# two implementations of this schema cannot drift apart on it.
_BBOX_EPS = 1e-9

PLATE_KIND_ENUM = {"geographic", "schematic"}
LAYER_KIND_ENUM = {
    "coast", "river", "relief", "shipRow", "wall", "route", "region", "band",
    # A burial mound in section, not a ridge. The tombs of Ilos and Batieia are
    # mounds on the plain, and hachuring them as relief said the wrong thing.
    "tumulus",
}
# Terrain fills, resolved through a closed whitelist in shared/lib/plate.ts
# (REGION_FILL_TOKENS). Kept here so the two implementations of this schema
# cannot drift apart again -- and they HAD drifted: the renderer and
# docs/APPARATUS-SCHEMAS.md gained lagoon/land/marsh/plain on 2026-07-28 (the
# ground + fill land/water contract) while this set still read {tint, sea},
# so a Troad plate declaring its landmasses `fill: "land"` was rejected here
# and drawn there.
# "none" (added 2026-07-29) is a region that draws nothing at all: a lettering
# zone for a named tract of country whose extent nobody surveyed. See
# REGION_FILL_TOKENS in shared/lib/plate.ts, which this mirrors.
# "masonry" (added 2026-07-30, citadel plate) is surveyed built stone -- a wall,
# a tower, a house block traced off an excavation plan -- drawn opaque with an
# ink face rather than as a wash, because on a plan of a dug site the difference
# between measured masonry and restored line is the content of the sheet.
# "zone" (added 2026-09-02, stage 4b LOOK-gate fix) is the apparatus's own
# lettered scene band (A-G): a faint tint in the sheet's own neutral ground
# token, distinct from "tint" (a decorative wash strong enough to read as a
# feature, e.g. a claimed camp zone) so seven stacked scene zones never
# outweigh the relief and coastline under them.
# "masonry-ground" (2026-09-03, ruling 13) is the same surveyed masonry drawn
# quieter as the ground under the poem's city; shared/lib/plate.ts keys it on
# the masonry legend row.
REGION_FILL_ENUM = {"tint", "zone", "masonry", "masonry-ground", "sea", "lagoon", "land", "marsh", "plain", "none"}
# What the bare sheet is under every layer, per the same contract.
GROUND_ENUM = {"land", "sea"}
STOCHASTIC_STYLES = {"stipple", "hachure"}

# Layer fields that carry coordinate geometry. "rings" nests one level deeper
# than the rest: a list of rings, each ring a list of [a, b] pairs. The flat
# fields are a plain list of pairs.
# `lines`, `columns` and `solids` are the plan register's extra ring lists
# (shared/lib/plate.ts, `style: "plan"`, 2026-09-03): same shape as `rings`.
_RING_FIELDS = ("rings", "lines", "columns", "solids")
_FLAT_COORD_FIELDS = ("path", "polygon", "baseline", "trace")


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_pair(x: Any) -> bool:
    return isinstance(x, list) and len(x) == 2 and all(_is_number(v) for v in x)


# `mentions[].work` values this module knows how to bounds-check, mapped to
# the manifest filename (manifests/<Work>.yaml) that carries that work's
# vulgate line counts.
_MENTION_WORK_MANIFESTS = {"iliad": "Iliad", "odyssey": "Odyssey"}


@lru_cache(maxsize=None)
def _book_line_counts() -> dict[str, dict[int, int]]:
    """{"iliad"|"odyssey": {book_number: last_line_in_that_book}}, read from
    manifests/Iliad.yaml and manifests/Odyssey.yaml's `books: [{n, start,
    end}]` list -- `end` is a "book.line" vulgate ref, the last line present
    in that book under this project's sacred, never-renumbered lineation
    (CLAUDE.md). Chosen over reading build/dist/<work>/*.json directly: the
    manifest table is committed data, so this rule works even before a
    pipeline build exists, and it is the same table stage1/preflight already
    treat as authoritative for vulgate line counts -- not a second, invented
    source of truth. Never raises: a missing/malformed manifest just yields
    an empty table for that work, and callers degrade to skipping the range
    check rather than crashing (matching this module's documented contract).
    """
    from .config import Manifest

    counts: dict[str, dict[int, int]] = {}
    for work, manifest_name in _MENTION_WORK_MANIFESTS.items():
        book_counts: dict[int, int] = {}
        try:
            manifest = Manifest.for_work(manifest_name)
            books = manifest.books
        except Exception:
            books = []
        for book in books:
            if not isinstance(book, dict):
                continue
            n = book.get("n")
            end = book.get("end")
            if isinstance(n, int) and isinstance(end, str) and "." in end:
                try:
                    book_counts[n] = int(end.rsplit(".", 1)[1])
                except ValueError:
                    continue
        counts[work] = book_counts
    return counts


def _validate_mentions(mentions: Any, label: str) -> list[str]:
    """`mentions` referential-integrity check (2026-09-02, stage 4c): a
    `{"work", "book", "lines": [lo, hi]}` reference must name a real book
    (Iliad and Odyssey both run 1-24) and a real line within that book's
    vulgate length. This catches a citation-authoring slip that produced two
    real findings: a document section number like "(§3.5)" or "(§1.75)",
    left unresolved in prose, harvested as if it were a verse ref and turned
    into a `mentions` entry -- book 3 line 5, book 1 line 75. NEITHER of
    those numbers is out of range (book 3 has far more than 5 lines; book 1
    far more than 75), so THIS RULE, by itself, cannot catch that class of
    error -- it only catches a book or line number that does not exist at
    all (book 25, or a line past a book's last line). The two section-number
    ghosts were caught by hand (verified against the real Greek text) and
    removed as data fixes; this rule guards against the disjoint, purely
    structural failure mode: a typo'd book/line that is simply out of
    bounds.
    """
    if not isinstance(mentions, list):
        return [f"{label}: mentions must be a list"]
    problems: list[str] = []
    line_counts = _book_line_counts()
    for i, mention in enumerate(mentions):
        if not isinstance(mention, dict):
            problems.append(f"{label}: mentions[{i}] must be an object")
            continue
        work = mention.get("work")
        book = mention.get("book")
        lines = mention.get("lines")
        if not isinstance(book, int) or isinstance(book, bool) or not (1 <= book <= 24):
            problems.append(
                f"{label}: mentions[{i}] book {book!r} must be an integer 1-24"
            )
            continue
        work_counts = line_counts.get(work) if isinstance(work, str) else None
        if not work_counts:
            # Unknown `work` value, or the manifest table could not be read
            # (e.g. manifests/ absent in this environment) -- can't
            # bounds-check the line without it, but the book-range check
            # above still ran.
            continue
        max_line = work_counts.get(book)
        if max_line is None or not isinstance(lines, list):
            continue
        for ln in lines:
            if _is_number(ln) and ln > max_line:
                problems.append(
                    f"{label}: mentions[{i}] {work} {book}.{ln} exceeds book "
                    f"{book}'s length ({max_line} lines)"
                )
    return problems


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

        mentions = place.get("mentions")
        if mentions is not None:
            problems += _validate_mentions(mentions, f"place {label}")

        # `zone` (2026-09-02, camp-zone ruling 2e-iv): a gazetteer place's own
        # attributed-zone polygon -- the source of truth a plate layer's
        # matching polygon is checked against (see
        # test_real_achaean_camp_zone_polygon_matches_the_plate_layer), since
        # no layer-from-gazetteer geometry mechanism exists to make the two
        # copies drift-proof by construction. Only `polygon`'s shape is
        # checked here, matching this module's existing leniency toward
        # `basis`/`source`/`note`-style descriptive fields it does not
        # enumerate.
        zone = place.get("zone")
        if zone is not None:
            if not isinstance(zone, dict):
                problems.append(f"place {label}: zone must be an object")
            else:
                polygon = zone.get("polygon")
                if not isinstance(polygon, list):
                    problems.append(f"place {label}: zone.polygon must be a list")
                elif len(polygon) < 3:
                    problems.append(
                        f"place {label}: zone.polygon must have at least 3 points, "
                        f"got {len(polygon)}"
                    )
                else:
                    for pi, pair in enumerate(polygon):
                        if not _is_pair(pair):
                            problems.append(
                                f"place {label}: zone.polygon[{pi}] must be a "
                                f"2-element numeric array"
                            )

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
                    if not _is_pair(uv):
                        problems.append(
                            f"place {label}: plateAnchors[{plate_id!r}] must be a "
                            f"2-element numeric array"
                        )

        kind = place.get("kind")
        if kind is not None and kind not in PLACE_KIND_ENUM:
            problems.append(f"place {label}: kind {kind!r} not in {sorted(PLACE_KIND_ENUM)}")

        label_tier = place.get("labelTier")
        if label_tier is not None and (not _is_number(label_tier) or label_tier not in (1, 2)):
            problems.append(
                f"place {label}: labelTier must be 1 or 2, got {label_tier!r}"
            )
        label_size = place.get("labelSize")
        if label_size is not None and label_size not in ("small", "base"):
            problems.append(
                f"place {label}: labelSize must be 'small' or 'base', got {label_size!r}"
            )

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


def _iter_layer_coords(layer: dict, label: str, layer_label: str, problems: list[str]):
    """Yield (field_name, pair, path_desc) for every coordinate pair present
    in a plate layer's geometry fields. A geometry field that is present but
    not shaped as an array (or, for `rings`, an array of arrays) is reported
    as a problem here rather than silently skipped, matching
    shared/lib/plate.ts's parseLayer, which fails loudly on the same shape
    (e.g. `"path": "nope"`)."""
    for field in _RING_FIELDS:
        rings = layer.get(field)
        if rings is None:
            continue
        if not isinstance(rings, list):
            problems.append(f"{label}: layer {layer_label} {field} must be a list of rings")
            continue
        for ri, ring in enumerate(rings):
            if not isinstance(ring, list):
                problems.append(
                    f"{label}: layer {layer_label} {field}[{ri}] must be a list of points"
                )
                continue
            for pi, pair in enumerate(ring):
                yield field, pair, f"[{ri}][{pi}]"
    for field in _FLAT_COORD_FIELDS:
        coords = layer.get(field)
        if coords is None:
            continue
        if not isinstance(coords, list):
            problems.append(f"{label}: layer {layer_label} {field} must be a list of points")
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

    # Mirrors parsePlate's `typeof d.id !== 'string' || !d.id` / same for
    # title: a numeric or empty id/title passed preflight here before, while
    # the TS lane already rejected it.
    for key in ("id", "title"):
        if key in doc:
            val = doc.get(key)
            if not isinstance(val, str) or not val:
                problems.append(f"{label}: {key} must be a non-empty string")

    kind = doc.get("kind")
    if "kind" in doc and (not isinstance(kind, str) or kind not in PLATE_KIND_ENUM):
        problems.append(f"{label}: kind must be one of {sorted(PLATE_KIND_ENUM)}, got {kind!r}")

    ground = doc.get("ground")
    if "ground" in doc and (not isinstance(ground, str) or ground not in GROUND_ENUM):
        problems.append(
            f"{label}: ground must be one of {sorted(GROUND_ENUM)}, got {ground!r}"
        )

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
            seen_rings: set[int] = set()
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

                band_label = band_id if isinstance(band_id, str) and band_id else f"bands[{i}]"

                # shared/lib/shield.ts's renderShield dereferences every one
                # of these unconditionally: title/greek build the label text,
                # summary feeds aria-label/title, lines feeds aria-label, and
                # a non-distinct or non-negative-integer ring is a hard
                # `throw`. An under-specified band (e.g. `{"id": "cosmos"}`)
                # used to pass this validator clean and then crash the
                # renderer at runtime — this block closes that gap.
                for field in ("title", "summary", "greek"):
                    val = band.get(field)
                    if not isinstance(val, str) or not val:
                        problems.append(
                            f"{label}: band {band_label} {field} must be a non-empty string"
                        )

                ring = band.get("ring")
                if not isinstance(ring, int) or isinstance(ring, bool) or ring < 0:
                    problems.append(
                        f"{label}: band {band_label} ring must be a non-negative integer"
                    )
                elif ring in seen_rings:
                    problems.append(f"{label}: band {band_label} duplicate ring {ring}")
                else:
                    seen_rings.add(ring)

                lines = band.get("lines")
                if not (
                    isinstance(lines, list)
                    and len(lines) == 2
                    and all(isinstance(v, int) and not isinstance(v, bool) for v in lines)
                    and lines[0] <= lines[1]
                ):
                    problems.append(
                        f"{label}: band {band_label} lines must be a [from, to] pair of "
                        f"integers with from <= to"
                    )

    if "status" in doc and (not isinstance(doc.get("status"), str) or not doc["status"].strip()):
        problems.append(f"{label}: status must be a non-empty string")

    # Plate-level sources: every plate is a scholarly artefact, not just its
    # individually-tagged places/layers, so it must cite what it drew from.
    # Required unconditionally (unlike the per-place/per-layer sources
    # checks above, which only bite when tagged for a plate) — a plate
    # document IS the thing tagged for a plate.
    plate_sources = doc.get("sources")
    if "sources" not in doc:
        problems.append(f"{label}: sources is required (a non-empty plate-level sources array)")
    elif not isinstance(plate_sources, list) or not plate_sources:
        problems.append(f"{label}: sources must be a non-empty list")
    else:
        problems += _validate_sources(plate_sources, label)

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
        size = None

    # Finding F4 (stage 6 review, 2026-09-03): this check did not exist on the
    # Python side at all — a plate.json with marginRight >= size[0] passed
    # preflight clean, and only failed at render time in shared/lib/plate.ts
    # (frameWidth = width - marginRight goes negative, and the map frame
    # projects off-canvas). Mirrors parsePlate's own marginRight checks.
    margin_right = doc.get("marginRight")
    if margin_right is not None:
        if not _is_number(margin_right) or margin_right < 0:
            problems.append(f"{label}: marginRight must be a number >= 0, got {margin_right!r}")
        elif isinstance(size, list) and len(size) == 2 and margin_right >= size[0]:
            problems.append(
                f"{label}: marginRight {margin_right} must be less than size[0] {size[0]} "
                f"(it would leave no map frame)"
            )

    # Plate pixels per metre of ground: a schematic plate's declaration that it
    # IS drawn to a true and constant scale, which is what lets the renderer draw
    # a bar scale on a sheet that otherwise has no metre in it (parsePlate's
    # `pxPerMetre` / metreBarMarkup in shared/lib/plate.ts). A bar computed from
    # a zero or negative figure would be a drawn lie, so it is rejected rather
    # than coerced away, matching the TS lane.
    px_per_metre = doc.get("pxPerMetre")
    if px_per_metre is not None and (not _is_number(px_per_metre) or px_per_metre <= 0):
        problems.append(
            f"{label}: pxPerMetre must be a number > 0, got {px_per_metre!r}"
        )

    # The caption under the north arrow, and the arrow's own switch. The words
    # ARE the caveat -- an 1890s magnetic bearing is not true north -- so a blank
    # one would draw an arrow that claims an orientation it does not name.
    north = doc.get("north")
    if north is not None and (not isinstance(north, str) or not north.strip()):
        problems.append(f"{label}: north must be a non-empty string")

    layers = doc.get("layers")
    if "layers" in doc and not isinstance(layers, list):
        problems.append(f"{label}: layers must be a list")
        layers = []
    layers = layers or []

    needs_seed = False
    seen_layer_ids: set[str] = set()
    # Layer ids that are framed inset panels with an insetBBox, and the
    # `insetOf` / `featureKey[].inset` references that must name one. Both are
    # resolved after the layer loop, because a reference may point forward.
    inset_panel_ids: set[str] = set()
    inset_of_refs: list[tuple[str, str]] = []
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            problems.append(f"{label}: layers[{i}] must be an object")
            continue
        layer_id = layer.get("id")
        layer_label = layer_id if isinstance(layer_id, str) and layer_id else f"layers[{i}]"
        if not isinstance(layer_id, str) or not layer_id:
            problems.append(f"{label}: layers[{i}].id must be a non-empty string")
        elif layer_id in seen_layer_ids:
            # shared/lib/plate.ts's per-layer stipple/hachure randomness is
            # salted by the layer id (deriveSeed) — a duplicate id draws
            # identical texture, so it is rejected here rather than merely
            # noted. Message shape matches the TS lane's.
            problems.append(f"plate {label}: duplicate layer id {layer_id!r}")
        else:
            seen_layer_ids.add(layer_id)

        # Every one of these next three fields does an `in`-test against a
        # set or dict. A list-valued field (e.g. `"kind": ["river"]`) used to
        # raise `TypeError: unhashable type: 'list'` there, breaking this
        # module's documented contract that it never raises — guarded with an
        # isinstance check first so a malformed field is reported as a
        # problem string like everything else.
        layer_kind = layer.get("kind")
        if not isinstance(layer_kind, str) or layer_kind not in LAYER_KIND_ENUM:
            problems.append(
                f"{label}: layer {layer_label} kind must be one of "
                f"{sorted(LAYER_KIND_ENUM)}, got {layer_kind!r}"
            )

        place_id = layer.get("placeId")
        if place_id is not None and (
            not isinstance(place_id, str) or place_id not in places_by_id
        ):
            problems.append(
                f"{label}: layer {layer_label} placeId {place_id!r} does not resolve "
                f"in the gazetteer"
            )

        claims = layer.get("claims")
        if claims is not None:
            if not isinstance(claims, list):
                problems.append(f"{label}: layer {layer_label} claims must be a list")
            else:
                for claimed_id in claims:
                    if not isinstance(claimed_id, str) or claimed_id not in places_by_id:
                        problems.append(
                            f"{label}: layer {layer_label} claims unknown place "
                            f"{claimed_id!r}"
                        )

        default = layer.get("default")
        if default is not None and default not in ("on", "off"):
            problems.append(f"{label}: layer {layer_label} default must be 'on' or 'off'")

        # The words this layer's key row is to read, overriding the register
        # name the renderer would derive (layerLegendEntry in
        # shared/lib/plate.ts). Blank is an authoring slip, not an instruction
        # to key the row with an empty string.
        legend = layer.get("legend")
        if legend is not None and (not isinstance(legend, str) or not legend.strip()):
            problems.append(
                f"{label}: layer {layer_label} legend must be a non-empty string"
            )

        fill = layer.get("fill")
        if fill is not None and (not isinstance(fill, str) or fill not in REGION_FILL_ENUM):
            problems.append(
                f"{label}: layer {layer_label} fill must be one of "
                f"{sorted(REGION_FILL_ENUM)}, got {fill!r}"
            )

        # A relief band's contour level in metres (2026-07-29). Its presence
        # is what puts the layer in the hypsometric register in
        # shared/lib/plate.ts -- filled from the sheet's elevation ramp and
        # edged with a hairline, rather than hachured -- so a malformed one
        # would silently demote a contoured band back to the hand-drawn
        # treatment. Mirrors parseLayer's check exactly; sea level (0) is a
        # legal elevation, a negative one is not.
        elevation = layer.get("elevation")
        if elevation is not None and (
            not _is_number(elevation) or elevation < 0
        ):
            problems.append(
                f"{label}: layer {layer_label} elevation must be a number >= 0, "
                f"got {elevation!r}"
            )

        label_tier = layer.get("labelTier")
        if label_tier is not None and (
            not _is_number(label_tier) or label_tier not in (1, 2)
        ):
            problems.append(
                f"{label}: layer {layer_label} labelTier must be 1 or 2, "
                f"got {label_tier!r}"
            )
        label_size = layer.get("labelSize")
        if label_size is not None and label_size not in ("small", "base"):
            problems.append(
                f"{label}: layer {layer_label} labelSize must be 'small' or "
                f"'base', got {label_size!r}"
            )

        style = layer.get("style")
        if isinstance(style, str) and style in STOCHASTIC_STYLES:
            needs_seed = True

        sources = layer.get("sources")
        if sources is not None:
            problems += _validate_sources(sources, f"{label}: layer {layer_label}")

        # `style: "inset"` may declare a sheet-pixel `frame` so the panel
        # can sit in the margin of a lat/lon sheet. Polygon/path on such a
        # layer are unit coordinates inside the frame, not lat/lon.
        framed_inset = False
        frame = layer.get("frame")
        if frame is not None:
            if (
                not isinstance(frame, list)
                or len(frame) != 4
                or not all(_is_number(v) for v in frame)
            ):
                problems.append(
                    f"{label}: layer {layer_label} frame must be a 4-element "
                    f"numeric array [x, y, w, h]"
                )
            else:
                fx, fy, fw, fh = frame
                if not (fw > 0 and fh > 0):
                    problems.append(
                        f"{label}: layer {layer_label} frame width and height must be > 0"
                    )
                else:
                    size_ok = (
                        isinstance(size, list)
                        and len(size) == 2
                        and all(_is_number(v) and v > 0 for v in size)
                    )
                    if size_ok and (
                        fx < 0 or fy < 0 or fx + fw > size[0] or fy + fh > size[1]
                    ):
                        problems.append(
                            f"{label}: layer {layer_label} frame {frame} lies outside "
                            f"the sheet size {size}"
                        )
                    elif style == "inset":
                        framed_inset = True
                        if isinstance(layer.get("insetBBox"), list):
                            inset_panel_ids.add(layer_id)

        # A framed inset panel may be a PROJECTED WINDOW rather than a free
        # drawing (ruling 10, 2026-09-03): `insetBBox` is the ground it shows,
        # and sibling layers naming it in `insetOf` are drawn from their own
        # lat/lon geometry through that window. Mirrors parsePlate's checks in
        # shared/lib/plate.ts -- two implementations of one contract.
        inset_bbox = layer.get("insetBBox")
        if inset_bbox is not None:
            if (
                not isinstance(inset_bbox, list)
                or len(inset_bbox) != 4
                or not all(_is_number(v) for v in inset_bbox)
            ):
                problems.append(
                    f"{label}: layer {layer_label} insetBBox must be a 4-element "
                    f"numeric array [minLat, minLon, maxLat, maxLon]"
                )
            elif not framed_inset:
                problems.append(
                    f"{label}: layer {layer_label} has an insetBBox but is not a "
                    f"framed inset panel"
                )
            elif min_lat is None:
                problems.append(
                    f"{label}: layer {layer_label} has an insetBBox but the plate "
                    f"has no bbox"
                )
            elif not (inset_bbox[2] > inset_bbox[0] and inset_bbox[3] > inset_bbox[1]):
                problems.append(
                    f"{label}: layer {layer_label} insetBBox must have maxLat > "
                    f"minLat and maxLon > minLon"
                )
        inset_of = layer.get("insetOf")
        if inset_of is not None:
            if not isinstance(inset_of, str) or not inset_of:
                problems.append(
                    f"{label}: layer {layer_label} insetOf must be a layer id"
                )
            elif frame is not None:
                problems.append(
                    f"{label}: layer {layer_label} cannot carry both frame and insetOf"
                )
            elif style == "inset":
                problems.append(
                    f"{label}: layer {layer_label} cannot be both an inset panel "
                    f"and insetOf one"
                )
            else:
                inset_of_refs.append((layer_label, inset_of))

        for field, pair, path_desc in _iter_layer_coords(layer, label, layer_label, problems):
            if not _is_pair(pair):
                problems.append(
                    f"{label}: layer {layer_label} {field}{path_desc} must be a "
                    f"[a, b] numeric pair"
                )
                continue
            a, b = pair
            # Coordinate space is declared by the PRESENCE of a bbox, not by
            # kind: a plate that carries a bbox projects lat/lon; a plate
            # with none (schematic, always) stays in unit [u, v] space.
            # A framed inset is the exception: its geometry is unit coords
            # inside the sheet-pixel frame.
            use_bbox = min_lat is not None
            if framed_inset:
                if not (
                    -_BBOX_EPS <= a <= 1 + _BBOX_EPS and -_BBOX_EPS <= b <= 1 + _BBOX_EPS
                ):
                    problems.append(
                        f"{label}: layer {layer_label} {field}{path_desc} = [{a}, {b}] "
                        f"must be a unit [u, v] pair in 0..1"
                    )
            elif use_bbox:
                if not (
                    min_lat - _BBOX_EPS <= a <= max_lat + _BBOX_EPS
                    and min_lon - _BBOX_EPS <= b <= max_lon + _BBOX_EPS
                ):
                    problems.append(
                        f"{label}: layer {layer_label} {field}{path_desc} = [{a}, {b}] "
                        f"lies outside bbox {bbox}"
                    )
            elif kind == "schematic":
                if not (
                    -_BBOX_EPS <= a <= 1 + _BBOX_EPS and -_BBOX_EPS <= b <= 1 + _BBOX_EPS
                ):
                    problems.append(
                        f"{label}: layer {layer_label} {field}{path_desc} = [{a}, {b}] "
                        f"must be a unit [u, v] pair in 0..1"
                    )

    for layer_label, ref in inset_of_refs:
        if ref not in inset_panel_ids:
            problems.append(
                f"{label}: layer {layer_label} insetOf {ref!r} is not a framed "
                f"inset panel with an insetBBox"
            )

    if needs_seed and "seed" not in doc:
        problems.append(f"{label}: seed is required (a layer uses a stochastic style)")

    scene_key = doc.get("sceneKey")
    if scene_key is not None:
        if not isinstance(scene_key, list):
            problems.append(f"{label}: sceneKey must be a list")
        else:
            # A duplicate letter would draw two rows in the printed key for
            # one glyph on the sheet, indistinguishable to the reader.
            # (2026-09-03, stage 6 review)
            seen_scene_letters: set[str] = set()
            for i, row in enumerate(scene_key):
                if not isinstance(row, dict):
                    problems.append(f"{label}: sceneKey[{i}] must be an object")
                    continue
                letter = row.get("letter")
                if not isinstance(letter, str) or not (1 <= len(letter) <= 2):
                    problems.append(
                        f"{label}: sceneKey[{i}].letter must be 1 or 2 characters"
                    )
                elif letter in seen_scene_letters:
                    problems.append(
                        f"{label}: sceneKey[{i}].letter {letter!r} is used more "
                        f"than once"
                    )
                else:
                    seen_scene_letters.add(letter)
                title = row.get("title")
                if not isinstance(title, str) or not title.strip():
                    problems.append(
                        f"{label}: sceneKey[{i}].title must be a non-empty string"
                    )
                ref = row.get("ref")
                if not isinstance(ref, str) or not ref.strip():
                    problems.append(
                        f"{label}: sceneKey[{i}].ref must be a non-empty string"
                    )
                row_layer_id = row.get("layerId")
                if not isinstance(row_layer_id, str) or not row_layer_id:
                    problems.append(
                        f"{label}: sceneKey[{i}].layerId must be a non-empty string"
                    )
                elif row_layer_id not in seen_layer_ids:
                    problems.append(
                        f"{label}: sceneKey[{i}].layerId {row_layer_id!r} is not a "
                        f"layer of this plate"
                    )

    # Numbered feature key (stage 5c). Sibling of sceneKey: groups of
    # place/layer ids lettered as numerals. Validation mirrors parsePlate.
    feature_key = doc.get("featureKey")
    if feature_key is not None:
        if not isinstance(feature_key, list):
            problems.append(f"{label}: featureKey must be a list")
        else:
            seen_key_ids: set[str] = set()
            for gi, group in enumerate(feature_key):
                if not isinstance(group, dict):
                    problems.append(f"{label}: featureKey[{gi}] must be an object")
                    continue
                title = group.get("title")
                if not isinstance(title, str) or not title.strip():
                    problems.append(
                        f"{label}: featureKey[{gi}].title must be a non-empty string"
                    )
                items = group.get("items")
                if items is None:
                    continue
                if not isinstance(items, list):
                    problems.append(f"{label}: featureKey[{gi}].items must be a list")
                    continue
                # Ruling 10: this group's marks and numerals are drawn inside
                # the named panel instead of on the map face.
                group_inset = group.get("inset")
                if group_inset is not None:
                    if not isinstance(group_inset, str) or not group_inset:
                        problems.append(
                            f"{label}: featureKey[{gi}].inset must be a layer id"
                        )
                    elif group_inset not in inset_panel_ids:
                        problems.append(
                            f"{label}: featureKey[{gi}].inset {group_inset!r} is not "
                            f"a framed inset panel with an insetBBox"
                        )
                for ii, item in enumerate(items):
                    if not isinstance(item, dict):
                        problems.append(
                            f"{label}: featureKey[{gi}].items[{ii}] must be an object"
                        )
                        continue
                    place_id = item.get("placeId")
                    layer_id = item.get("layerId")
                    has_place = isinstance(place_id, str) and bool(place_id)
                    has_layer = isinstance(layer_id, str) and bool(layer_id)
                    if has_place == has_layer:
                        problems.append(
                            f"{label}: featureKey[{gi}].items[{ii}] must name "
                            f"exactly one of placeId/layerId"
                        )
                    key_id: str | None = None
                    if has_layer:
                        if layer_id not in seen_layer_ids:
                            problems.append(
                                f"{label}: featureKey[{gi}].items[{ii}].layerId "
                                f"{layer_id!r} is not a layer of this plate"
                            )
                        key_id = layer_id
                    elif has_place:
                        place = places_by_id.get(place_id)
                        anchors = (
                            place.get("plateAnchors")
                            if isinstance(place, dict)
                            else None
                        )
                        anchored = (
                            isinstance(anchors, dict)
                            and isinstance(plate_id, str)
                            and plate_id in anchors
                        )
                        if not anchored:
                            problems.append(
                                f"{label}: featureKey[{gi}].items[{ii}].placeId "
                                f"{place_id!r} is not anchored on this plate"
                            )
                        key_id = place_id
                    if key_id is not None:
                        if key_id in seen_key_ids:
                            problems.append(
                                f"{label}: featureKey[{gi}].items[{ii}] id "
                                f"{key_id!r} appears twice"
                            )
                        else:
                            seen_key_ids.add(key_id)

    # See Plate.suppressLayerLabels in shared/lib/plate.ts, which this
    # mirrors: layer ids whose fallback name (the gazetteer name of
    # `placeId`, drawn when the layer has no `label` of its own) must not be
    # lettered on this plate -- a ground layer synced verbatim from a
    # geographic sheet (scripts/sync-schematic-ground.py) carrying a name
    # the schematic sheet already gives through its own pin or glyph.
    suppress_layer_labels = doc.get("suppressLayerLabels")
    if suppress_layer_labels is not None:
        if not isinstance(suppress_layer_labels, list):
            problems.append(f"{label}: suppressLayerLabels must be a list")
        else:
            for i, layer_id in enumerate(suppress_layer_labels):
                if not isinstance(layer_id, str) or not layer_id:
                    problems.append(
                        f"{label}: suppressLayerLabels[{i}] must be a "
                        f"non-empty string"
                    )
                elif layer_id not in seen_layer_ids:
                    problems.append(
                        f"{label}: suppressLayerLabels[{i}] {layer_id!r} is "
                        f"not a layer of this plate"
                    )

    # plateAnchors range belongs here, not in validate_places: a schematic
    # plate with a bbox authors lat/lon anchors, a plate without one stays
    # in unit 0..1. Only a pair keyed to THIS plate's id is this plate's
    # concern — an anchor for another sheet is ignored.
    if isinstance(plate_id, str) and plate_id:
        for place_key, place in places_by_id.items():
            if not isinstance(place, dict):
                continue
            anchors = place.get("plateAnchors")
            if not isinstance(anchors, dict) or plate_id not in anchors:
                continue
            uv = anchors[plate_id]
            if not _is_pair(uv):
                continue
            a, b = uv
            place_label = (
                place["id"]
                if isinstance(place.get("id"), str) and place["id"]
                else place_key
            )
            use_bbox = min_lat is not None
            if use_bbox:
                if not (
                    min_lat - _BBOX_EPS <= a <= max_lat + _BBOX_EPS
                    and min_lon - _BBOX_EPS <= b <= max_lon + _BBOX_EPS
                ):
                    problems.append(
                        f"{label}: place {place_label} plateAnchors[{plate_id!r}] "
                        f"= [{a}, {b}] lies outside bbox {bbox}"
                    )
            elif not (
                -_BBOX_EPS <= a <= 1 + _BBOX_EPS and -_BBOX_EPS <= b <= 1 + _BBOX_EPS
            ):
                problems.append(
                    f"{label}: place {place_label} plateAnchors[{plate_id!r}] "
                    f"= [{a}, {b}] must be a unit [u, v] pair in 0..1"
                )

    return problems


def validate_plate_anchors(
    places_by_id: dict[str, Any], plate_ids: set[str]
) -> list[str]:
    """Check every place's `plateAnchors` keys against the full set of plate
    ids that actually exist. `validate_plate` only ever sees ONE plate, so it
    can range-check the anchor keyed to that plate's own id but cannot tell a
    typo'd key (naming a plate that doesn't exist at all) from one meant for
    a sibling sheet. Call once, after every apparatus/plates/*.json has been
    loaded, with the full set of loaded plate ids. (2026-09-03, stage 6
    review)
    """
    problems: list[str] = []
    for place_key, place in places_by_id.items():
        if not isinstance(place, dict):
            continue
        anchors = place.get("plateAnchors")
        if not isinstance(anchors, dict):
            continue
        place_label = (
            place["id"]
            if isinstance(place.get("id"), str) and place["id"]
            else place_key
        )
        for plate_key in anchors:
            if plate_key not in plate_ids:
                problems.append(
                    f"place {place_label}: plateAnchors[{plate_key!r}] names a "
                    f"plate id that does not exist"
                )
    return problems
