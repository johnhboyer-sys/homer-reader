"""Computed apparatus stage (Phase 4e, docs/APPARATUS-SCHEMAS.md): import
DICES speech spans into per-work apparatus/speeches/<work>.json, and fill
apparatus/characters.json's `dicesId` for characters successfully joined by
name. Computed from sources/dices/speechdb.json (CC-BY 4.0), not authored --
no philological judgment beyond the deterministic joins below.

DICES source shape
-------------------
sources/dices/speechdb.json is a Django fixture dump (`{model, pk, fields}`
records, flat list, no nesting) covering 52 works across many authors. The
models this stage reads:

  - speechdb.work: pk 1 = Iliad, pk 2 = Odyssey (see DICES_WORK_IDS).
  - speechdb.character: a GLOBAL cast list (character pk is stable across
    every work/author it appears in -- verified: Odysseus is char pk 722 in
    both the Iliad and Odyssey characterinstance rows, not two separate
    rows). `public_id` is DICES's own stable external id (used on
    dices.data.fas.harvard.edu), which is what gets written into
    apparatus/characters.json's `dicesId` -- NOT the fixture-local `pk`,
    which is an artifact of this particular export.
  - speechdb.characterinstance: a per-work speaking role (`context` field,
    e.g. "Homer Iliad"). `char` FK points at the global character when one
    applies; disguises and epithet-instances (e.g. "Athena-Mentor",
    "Odysseus-Nobody", "ghost of Patroclus", "dead Patroclus") all carry the
    `char` FK of the underlying figure (Athena, Odysseus, Patroclus), so
    resolving speaker/addressee through `char` -- not through the instance's
    own per-context `name` -- is what correctly collapses disguises back to
    the base character. Anonymous/collective participants ("Greeks",
    "suitors of Penelope", "Trojan.1") have `char = null` and keep their own
    instance name.
  - speechdb.speech: `work` FK, `l_fi`/`l_la` are "book.line" strings,
    `spkr`/`addr` are lists of characterinstance pks, `level` is embedding
    depth (0 = direct speech in the primary narrative), `cluster`/`part`
    group a speech within a conversational exchange, `type` is DICES's
    single-letter speech-type code (G/M/D/S), passed through verbatim.
  - speechdb.speechcluster, speechdb.speechtag: not used by this stage (out
    of the docs/APPARATUS-SCHEMAS.md speeches.json contract).

Name join (speaker/addressee -> apparatus/characters.json id)
---------------------------------------------------------------
Exact case-insensitive match on the resolved DICES name against
apparatus/characters.json's `name` field, plus a small, hand-verified alias
table (NAME_ALIASES) for real DICES/apparatus spelling variants: the two
Ajaxes (DICES "Aias (son of X)" vs our "Ajax (son of X)"), "Helena"/"Helen",
"Phoinix"/"Phoenix", "Euryclea"/"Eurycleia", "Glaucus (Lycian)"/"Glaucus",
and "Paris"/"Paris (Alexander)". Deliberately NOT a general fuzzy match or a
blanket "strip the parenthetical" rule: stripping parens from apparatus
names naively collapses "Ajax (son of Telamon)" and "Ajax (son of Oileus)"
onto the same key, which would silently mismatch one of the two Ajaxes --
exactly the "never force a wrong match" failure this stage must avoid.
Everything else that fails the exact-plus-alias check is reported unmatched
and kept as a plain lowercase string of the DICES name (never dropped).

Line validation
----------------
Every l_fi/l_la is checked against the actual line numbers present in the
already-emitted build/dist/<work>/book-NN.json (not just the manifest's
declared book bounds), so a DICES reference that lands on a real vulgate
numbering gap in THIS edition is caught. One confirmed real example: DICES
speech pk 931 (Odyssey) starts at "10.456", which is exactly the Od. 10.456
line omitted from the Perseus grc2 text this corpus uses (manifest
expected_line_gaps: {book: 10, after: 455, next: 457}). Such refs are
reported in `line_ref_errors`, never silently clamped to the nearest real
line and never dropped from the emitted file.

Apologoi finding (failure-mode registry cross-check)
-------------------------------------------------------
DICES does NOT mark the whole Odysseus-to-the-Phaeacians narrative (Od.
9-12) as a single deeply-nested speech. It is two top-level (`level: 0`)
speeches -- Od. 9.2-11.332 and Od. 11.378-12.453, split by the brief
Phaeacian-court interlude at 11.333-377 -- each of which legitimately
crosses book boundaries (9->11, 11->12) and is emitted here with
`crossBook: true`. The narrative-within-speech nesting the registry warns
about IS present in DICES, but on the ~87 speeches Odysseus quotes WITHIN
his tale (Polyphemus, the Cyclopes, his own companions, etc.), which
correctly carry `level: 1`. So `level` and `crossBook` are orthogonal here:
consuming code must not assume a crossBook span is automatically
high-nesting, and must not assume level 0 means "safe to render as a single
book's speech" -- check both flags independently.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .config import BUILD_DIR, REPO_ROOT, Manifest

APPARATUS_DIR = REPO_ROOT / "apparatus"
SPEECHES_DIR = APPARATUS_DIR / "speeches"
CHARACTERS_PATH = APPARATUS_DIR / "characters.json"
SPEECHDB_PATH = REPO_ROOT / "sources" / "dices" / "speechdb.json"

# speechdb.work.pk -> our work id. speechdb.json spans 52 works; this stage
# only ever imports the two Homeric epics.
DICES_WORK_IDS = {1: "iliad", 2: "odyssey"}

# See module docstring's "Name join" section for why each of these exists
# and why this is a fixed table rather than a fuzzy matcher.
NAME_ALIASES = {
    "aias (son of telamon)": "ajax-telamonian",
    "aias (son of oileus)": "ajax-oileus",
    "glaucus (lycian)": "glaucus",
    "helena": "helen",
    "phoinix": "phoenix",
    "euryclea": "eurycleia",
    "paris": "paris",
}


# ── DICES fixture loading ───────────────────────────────────────────────────


def load_speechdb(path: Path | None = None) -> dict[str, list[dict]]:
    """model name -> list of {pk, fields} records, in file order. `path`
    defaults to the module-level SPEECHDB_PATH, resolved at call time (not
    bound as a def-time default) so tests can monkeypatch the module
    attribute rather than having to pass the path explicitly."""
    records = json.loads((path or SPEECHDB_PATH).read_text(encoding="utf-8"))
    by_model: dict[str, list[dict]] = {}
    for r in records:
        by_model.setdefault(r["model"], []).append(r)
    return by_model


def _parse_ref(ref: str) -> tuple[int, int]:
    """'9.2' -> (9, 2)."""
    book, line = ref.split(".", 1)
    return int(book), int(line)


def build_instance_name_map(
    char_records: list[dict], inst_records: list[dict]
) -> dict[int, str]:
    """characterinstance pk -> resolved name: the global speechdb.character
    name when the instance carries a `char` FK (collapses disguises/epithet
    instances to their base figure -- see module docstring), else the
    instance's own per-work name (anonymous/collective participants)."""
    char_names = {r["pk"]: r["fields"]["name"] for r in char_records}
    inst_names: dict[int, str] = {}
    for r in inst_records:
        f = r["fields"]
        char_fk = f.get("char")
        inst_names[r["pk"]] = char_names[char_fk] if char_fk is not None else f["name"]
    return inst_names


def join_character_id(dices_name: str, apparatus_by_name: dict[str, str]) -> tuple[str, bool]:
    """(apparatus id if matched else lowercased DICES name, matched?)."""
    lower = dices_name.lower()
    if lower in apparatus_by_name:
        return apparatus_by_name[lower], True
    if lower in NAME_ALIASES:
        return NAME_ALIASES[lower], True
    return lower, False


def _load_book_lines(dist_dir: Path) -> dict[int, set[int]]:
    """book number -> set of real (emitted) vulgate line numbers, read off
    the already-built build/dist/<work>/book-NN.json files."""
    out: dict[int, set[int]] = {}
    for path in sorted(dist_dir.glob("book-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        out[doc["book"]] = {
            line["n"] for seg in doc["segments"] for line in seg["greek"]
        }
    return out


# ── speech construction ─────────────────────────────────────────────────────


def build_speeches(
    dices_work_pk: int,
    work_id: str,
    speech_records: list[dict],
    inst_names: dict[int, str],
    apparatus_by_name: dict[str, str],
    book_lines: dict[int, set[int]],
) -> dict[str, Any]:
    """Build this work's speeches list plus the join/validation report.
    Returns {speeches, unmatched_names, line_ref_errors, matched_char_names}.
    `matched_char_names` is apparatus id -> exact-case DICES character name,
    scoped to only the DICES characters actually referenced as a speaker/
    addressee in THIS work -- deliberately not a lookup over the full
    1001-character global DICES cast, so a same-named character from an
    unrelated epic elsewhere in speechdb.json can never be joined in by
    accident."""
    speeches: list[dict] = []
    unmatched: set[str] = set()
    line_ref_errors: list[str] = []
    matched_char_names: dict[str, str] = {}

    def resolve_ids(pks: list[int]) -> list[str]:
        ids = []
        for pk in pks:
            name = inst_names.get(pk, f"unknown-instance-{pk}")
            cid, matched = join_character_id(name, apparatus_by_name)
            if matched:
                matched_char_names[cid] = name
            else:
                unmatched.add(name)
            ids.append(cid)
        return ids

    def check_line(pk: int, which: str, ref: str, book: int, line: int) -> None:
        if book not in book_lines:
            line_ref_errors.append(
                f"{work_id} speech {pk}: {which} book {book} has no emitted book-NN.json"
            )
        elif line not in book_lines[book]:
            line_ref_errors.append(
                f"{work_id} speech {pk}: {which} {ref} is not a real vulgate line "
                f"(numbering gap or out of range)"
            )

    for rec in speech_records:
        f = rec["fields"]
        if f["work"] != dices_work_pk:
            continue
        pk = rec["pk"]
        book_fi, line_fi = _parse_ref(f["l_fi"])
        book_la, line_la = _parse_ref(f["l_la"])
        check_line(pk, "l_fi", f["l_fi"], book_fi, line_fi)
        check_line(pk, "l_la", f["l_la"], book_la, line_la)

        speech = {
            "id": f"{work_id}-{pk}",
            "book": book_fi,
            "lines": [line_fi, line_la],
            "speaker": resolve_ids(f["spkr"]),
            "addressee": resolve_ids(f["addr"]),
            "level": f["level"],
            "cluster": f["cluster"],
            "part": f["part"],
            "type": f["type"],
        }
        if book_fi != book_la:
            speech["crossBook"] = True
        speeches.append(speech)

    speeches.sort(key=lambda s: (s["book"], s["lines"][0], s["id"]))
    return {
        "speeches": speeches,
        "unmatched_names": sorted(unmatched),
        "line_ref_errors": line_ref_errors,
        "matched_char_names": matched_char_names,
    }


# ── characters.json dicesId fill (surgical, non-destructive across runs) ───


def fill_dices_ids(
    characters_doc: dict,
    matched_char_names: dict[str, str],
    char_public_id_by_name: dict[str, str],
) -> int:
    """Set `dicesId` on every apparatus character this run resolved a DICES
    join for. Never touches characters not resolved THIS run (so running the
    stage for Iliad then Odyssey -- or in either order -- only ever adds
    dicesIds, never overwrites one run's finding with another's absence).
    Returns the number of characters newly filled."""
    filled = 0
    for char in characters_doc["characters"]:
        name = matched_char_names.get(char["id"])
        public_id = char_public_id_by_name.get(name) if name else None
        if public_id and char.get("dicesId") != public_id:
            char["dicesId"] = public_id
            filled += 1
    return filled


# ── stage entry point ───────────────────────────────────────────────────────


def run(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    dices_work_pk = next((k for k, v in DICES_WORK_IDS.items() if v == work_id), None)
    if dices_work_pk is None:
        raise ValueError(f"no DICES work mapping for work {work_id!r}")

    by_model = load_speechdb()
    char_records = by_model["speechdb.character"]
    inst_records = by_model["speechdb.characterinstance"]
    speech_records = by_model["speechdb.speech"]

    inst_names = build_instance_name_map(char_records, inst_records)
    char_public_id_by_name = {
        r["fields"]["name"]: r["fields"]["public_id"] for r in char_records
    }

    characters_doc = json.loads(CHARACTERS_PATH.read_text(encoding="utf-8"))
    apparatus_by_name = {
        c["name"].lower(): c["id"] for c in characters_doc["characters"]
    }

    dist_dir = BUILD_DIR / "dist" / work_id
    book_lines = _load_book_lines(dist_dir)

    result = build_speeches(
        dices_work_pk, work_id, speech_records, inst_names, apparatus_by_name, book_lines
    )

    doc = {"work": work_id, "status": "imported", "speeches": result["speeches"]}
    SPEECHES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SPEECHES_DIR / f"{work_id}.json"
    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    filled = fill_dices_ids(
        characters_doc, result["matched_char_names"], char_public_id_by_name
    )
    if filled:
        CHARACTERS_PATH.write_text(
            json.dumps(characters_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    speeches = result["speeches"]
    level_counts = dict(sorted(Counter(s["level"] for s in speeches).items()))
    cross_book_count = sum(1 for s in speeches if s.get("crossBook"))

    return {
        "work": work_id,
        "path": out_path,
        "speech_count": len(speeches),
        "cross_book_count": cross_book_count,
        "level_counts": level_counts,
        "unmatched_names": result["unmatched_names"],
        "line_ref_errors": result["line_ref_errors"],
        "characters_filled": filled,
    }
