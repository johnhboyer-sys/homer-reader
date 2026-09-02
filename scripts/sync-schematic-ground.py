#!/usr/bin/env python3
"""Synchronise ground layers from the geographic Trojan-plain sheet onto
the schematic-v2 plate.

The geographic sheet (`apparatus/plates/trojan-plain.json`) is the source of
truth for coast, sea, relief, rivers, and the Bronze Age reconstruction.
This script copies those 25 layers by id (not the Achaean camp zone) onto
`apparatus/plates/trojan-plain-schematic-v2.json` so the schematic plate
draws the same ground, rotated east-up, with a right margin.

Re-runnable: if the target already exists, only those 25 layers are
replaced by id; every other key and any extra layers stay put. On first
run the document is created with the schematic-v2 skeleton.

JSON is written the same way `prep-terrain-contours.py`'s `--patch-plates`
path writes a plate: two-space indent, purely numeric arrays collapsed onto
one line, trailing newline.

Usage:
  python3 scripts/sync-schematic-ground.py
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "apparatus", "plates", "trojan-plain.json")
TARGET = os.path.join(REPO, "apparatus", "plates", "trojan-plain-schematic-v2.json")

# Paint order on the geographic sheet, minus achaean-camp-zone.
GROUND_IDS = [
    "sea-modern",
    "scamandrian-plain",
    "relief-band-0010",
    "relief-band-0015",
    "relief-band-0020",
    "relief-band-0025",
    "relief-band-0030",
    "relief-band-0040",
    "relief-band-0060",
    "relief-band-0100",
    "relief-band-0150",
    "relief-band-0200",
    "relief-band-0320",
    "relief-sigeion-ridge",
    "relief-plain-south",
    "relief-troy-ridge",
    "relief-rhoiteion-ridge",
    "relief-plain-east-200",
    "lagoon-bronze",
    "delta-swamp",
    "shore-bronze",
    "barrier-bronze",
    "coast-modern",
    "scamander",
    "simoeis",
]

NOTE = (
    "Ground layers are synchronised from trojan-plain.json by "
    "scripts/sync-schematic-ground.py; do not edit them here."
)

_NUM_ARRAY = re.compile(
    r"\[\s*\n\s*(-?\d[\d.eE+-]*(?:,\s*\n\s*-?\d[\d.eE+-]*)*)\s*\n\s*\]")


def _write_plate(path: str, plate: dict) -> None:
    """Writes the plate in the house style: two-space indent, but a purely
    numeric array (a bbox, a size, a coordinate pair) collapsed onto one line.
    Copied from scripts/prep-terrain-contours.py so a sync round-trips the
    same way a terrain patch does."""
    text = json.dumps(plate, indent=2, ensure_ascii=False)
    while True:
        collapsed = _NUM_ARRAY.sub(
            lambda m: "[" + ", ".join(v.strip() for v in m.group(1).split(",")) + "]",
            text)
        if collapsed == text:
            break
        text = collapsed
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def _replace_block(layers: list, managed: set[str], new_layers: list) -> list:
    """Swaps a set of layers for a new set, in place: the block lands where
    its first member was, and every layer outside it keeps its exact
    position and content. Mirrors prep-terrain-contours.py's _replace_block."""
    idx = [i for i, l in enumerate(layers) if l.get("id") in managed]
    keep = [l for i, l in enumerate(layers) if i not in set(idx)]
    at = idx[0] if idx else len(layers)
    return keep[:at] + new_layers + keep[at:]


def _skeleton(sources: list) -> dict:
    return {
        "id": "trojan-plain-schematic-v2",
        "title": "The Plain of Troy as the Iliad lays it out",
        "kind": "schematic",
        "status": "draft",
        "size": [1460, 1265],
        "marginRight": 340,
        "rotationDeg": 90,
        "groundOpacity": 0.55,
        "bbox": [39.86, 26.1, 40.05, 26.38],
        "north": "True north",
        "sources": copy.deepcopy(sources),
        "note": NOTE,
        "layers": [],
    }


def main() -> int:
    with open(SOURCE, encoding="utf-8") as f:
        geo = json.load(f)
    by_id = {l["id"]: l for l in geo["layers"]}
    missing = [lid for lid in GROUND_IDS if lid not in by_id]
    if missing:
        print(
            "trojan-plain.json is missing ground layer(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    ground = [copy.deepcopy(by_id[lid]) for lid in GROUND_IDS]

    if os.path.exists(TARGET):
        with open(TARGET, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = _skeleton(geo["sources"])

    doc["layers"] = _replace_block(doc.get("layers") or [], set(GROUND_IDS), ground)
    _write_plate(TARGET, doc)
    rel = os.path.relpath(TARGET, REPO)
    print(f"wrote {rel}: {len(ground)} ground layers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
