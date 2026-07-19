"""Stage 1 Perseus grc2 TEI reader: lineation is sacred."""

from __future__ import annotations

from pathlib import Path

from homer_pipeline.config import Manifest
from homer_pipeline import stage1_perseus_greek as s1
from homer_pipeline import scheme as scheme_mod

FIXTURE = Path(__file__).parent / "fixtures" / "perseus_greek" / "tiny_with_gap.xml"


def _manifest() -> Manifest:
    data = {
        "work": {
            "id": "fixture",
            "title": "Fixture",
            "author": "Homer",
            "tlg_author": "0012",
            "tlg_work": "001",
            "greek_edition": "synthetic",
            "greek_source": "unused.xml",
        },
        "citation": {"scheme": "verse-line"},
        "english": {},
        "books": [
            {"n": 1, "start": "1.1", "end": "1.5"},
            {"n": 2, "start": "2.1", "end": "2.3"},
        ],
        "expected_line_gaps": [{"book": 1, "after": 2, "next": 5}],
        "sources": {
            "tlg_dir_env": "TLG_DIR",
            "tlg_dir_default": ".",
            "diogenes_server": ".",
            "diogenes_data": ".",
        },
    }
    return Manifest(data, Path("Fixture.yaml"))


def test_parse_preserves_verbatim_lineation_including_gap():
    """Numbering 1,2,5 stays 1,2,5 — never renumbered to fill the hole."""
    spine = s1.parse_spine(FIXTURE, _manifest())
    by_book = {s["book"]: s for s in spine["segments"]}
    assert set(by_book) == {1, 2}

    b1 = by_book[1]
    assert b1["column"] == "1"
    assert b1["id"] == "1:1"
    nums = [ln["n"] for ln in b1["lines"]]
    assert nums == [1, 2, 5]
    assert "μῆνιν" in b1["lines"][0]["text"]
    assert "οἰωνοῖσί" in b1["lines"][2]["text"]


def test_parse_sorts_document_order_glitches_by_n():
    """TEI document order may swap lines; spine emits ascending n=."""
    spine = s1.parse_spine(FIXTURE, _manifest())
    b2 = next(s for s in spine["segments"] if s["book"] == 2)
    assert [ln["n"] for ln in b2["lines"]] == [1, 2, 3]
    assert "πλάγχθη" in b2["lines"][1]["text"]
    assert "πολλῶν" in b2["lines"][2]["text"]


def test_validate_line_sequence_honours_declared_gap():
    spine = s1.parse_spine(FIXTURE, _manifest())
    lines_by_book = {
        s["book"]: [ln["n"] for ln in s["lines"]] for s in spine["segments"]
    }
    unexpected = scheme_mod.validate_line_sequence(
        lines_by_book, [{"book": 1, "after": 2, "next": 5}]
    )
    assert unexpected == []

    # Without the declaration the 2→5 jump is a defect.
    assert scheme_mod.validate_line_sequence(lines_by_book, []) == [
        {"book": 1, "after": 2, "next": 5}
    ]


def test_nfc_normalization_and_punctuation_kept():
    spine = s1.parse_spine(FIXTURE, _manifest())
    text = spine["segments"][0]["lines"][1]["text"]
    # Curly apostrophe from the fixture is kept; no NFC corruption of letters.
    assert "μυρίʼ" in text or "μυρί'" in text
    assert "," in text
