"""Stage 1 TLG (Allen 1931) Iliad reader: lineation is sacred.

Covers the mechanics unique to this reader vs. stage1_perseus_greek: the
obelos -> bracketed mapping, non-obelos sigla preservation, the decorated-n
("605*"-style) normalization, and the omitted-line supplement injection
(the Book 8 mechanism, exercised here with a synthetic book/line so the test
doesn't depend on the real Perseus Book 8 text).
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from homer_pipeline.config import Manifest
from homer_pipeline import stage1_tlg_iliad as s1
from homer_pipeline import scheme as scheme_mod

FIXTURE = Path(__file__).parent / "fixtures" / "stage1_tlg" / "tiny_tlg_iliad.xml"


def _manifest() -> Manifest:
    data = {
        "work": {
            "id": "fixture",
            "title": "Fixture",
            "author": "Homer",
            "tlg_author": "0012",
            "tlg_work": "001",
            "greek_edition": "synthetic",
            "greek_source_kind": "tlg",
        },
        "citation": {"scheme": "verse-line"},
        "english": {},
        "books": [
            {"n": 1, "start": "1.1", "end": "1.5"},
            {"n": 2, "start": "2.1", "end": "2.4"},
        ],
        "expected_line_gaps": [],
        "sources": {
            "tlg_dir_env": "TLG_DIR",
            "tlg_dir_default": ".",
            "diogenes_server": ".",
            "diogenes_data": ".",
        },
    }
    return Manifest(data, Path("Fixture.yaml"))


def _segments(supplement=None) -> dict[int, dict]:
    spine = s1.parse_spine(FIXTURE, _manifest(), supplement=supplement)
    return {s["book"]: s for s in spine["segments"]}


def test_plain_line_carries_no_sigla_or_bracketed():
    b1 = _segments(supplement={})[1]
    line1 = next(l for l in b1["lines"] if l["n"] == 1)
    assert "Μῆνιν" in line1["text"]
    assert "sigla" not in line1
    assert "bracketed" not in line1


def test_obelos_sigla_sets_bracketed_and_is_preserved_verbatim():
    b1 = _segments(supplement={})[1]
    line2 = next(l for l in b1["lines"] if l["n"] == 2)
    assert line2["sigla"] == "—"
    assert line2["bracketed"] is True
    # The obelos itself never leaks into the Greek text stream.
    assert "—" not in line2["text"]
    assert "οὐλομένην" in line2["text"]


def test_non_obelos_sigla_preserved_but_not_bracketed():
    b1 = _segments(supplement={})[1]
    line3 = next(l for l in b1["lines"] if l["n"] == 3)
    assert line3["sigla"] == ">"
    assert "bracketed" not in line3
    assert ">" not in line3["text"]


def test_combo_sigla_containing_obelos_sets_bracketed():
    b1 = _segments(supplement={})[1]
    line4 = next(l for l in b1["lines"] if l["n"] == 4)
    assert line4["sigla"] == "※—"
    assert line4["bracketed"] is True


def test_decorated_n_normalizes_and_is_reported():
    spine = s1.parse_spine(FIXTURE, _manifest(), supplement={})
    b1 = next(s for s in spine["segments"] if s["book"] == 1)
    nums = [l["n"] for l in b1["lines"]]
    assert nums == [1, 2, 3, 4, 5]  # "5*" normalized to int 5, never a 6th line
    line5 = next(l for l in b1["lines"] if l["n"] == 5)
    assert "οἰωνοῖσί" in line5["text"]
    assert "bracketed" not in line5
    assert spine["normalized_line_attrs"] == [
        {"book": 1, "raw": "5*", "normalized": 5}
    ]


def test_title_line_excluded_from_lines_and_reported_as_heading():
    spine = s1.parse_spine(FIXTURE, _manifest(), supplement={})
    b1 = next(s for s in spine["segments"] if s["book"] == 1)
    assert all(l["n"] != "t" for l in b1["lines"])
    assert spine["title_lines_skipped"] == 1
    headings = [h for h in spine["headings"] if h["column"] == "1"]
    assert len(headings) == 1
    assert headings[0]["n"] == "t"


def test_omitted_line_is_not_a_gap_without_supplement():
    """Book 2 in the fixture omits n=3 (simulating Allen's Book 8 omission),
    same as an edition that just doesn't print the line."""
    b2 = _segments(supplement={})[2]
    nums = [l["n"] for l in b2["lines"]]
    assert nums == [1, 2, 4]
    lines_by_book = {2: nums}
    unexpected = scheme_mod.validate_line_sequence(lines_by_book, [])
    assert unexpected == [{"book": 2, "after": 2, "next": 4}]


def test_supplement_fills_the_gap_and_flags_bracketed():
    """The injection mechanism (production use: SUPPLEMENTED_LINES for Il.
    8.548/550/551/552), exercised here with a synthetic book/line so the test
    is independent of the real Perseus Book 8 text."""
    supplement = {2: {3: "πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,"}}
    b2 = _segments(supplement=supplement)[2]
    nums = [l["n"] for l in b2["lines"]]
    assert nums == [1, 2, 3, 4]  # no gap once supplied

    line3 = next(l for l in b2["lines"] if l["n"] == 3)
    assert line3["text"] == "πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,"
    assert line3["bracketed"] is True
    assert "sigla" not in line3  # supplied lines carry no TLG marginalia

    lines_by_book = {2: nums}
    assert scheme_mod.validate_line_sequence(lines_by_book, []) == []


def test_supplement_is_a_noop_when_the_edition_already_prints_the_line():
    """A supplement entry for a line the export DOES carry must never
    overwrite the edition's own text (Allen's own words win where he has
    any)."""
    supplement = {2: {2: "SHOULD NOT REPLACE THE REAL LINE"}}
    b2 = _segments(supplement=supplement)[2]
    line2 = next(l for l in b2["lines"] if l["n"] == 2)
    assert line2["text"] == "πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσε·"


def test_stray_bullet_sigil_is_pulled_out_of_the_text_and_not_bracketed():
    """TLG Beta Code "%11" decodes to a literal U+2022 bullet with no <seg>
    wrapper (attested at real Il. 8.538-540, 13.298) — it must not corrupt
    the Greek token stream, and per John's obelos-only rule it must NOT set
    bracketed (it is not the em-dash obelos)."""
    el = etree.fromstring('<l n="1">• ὠς δὸ βροτολοιγὸς </l>')
    text, sigla = s1._line_text_and_sigla(el)
    assert "•" not in text
    assert text.startswith("ὠς")
    assert sigla == "•"


def test_real_supplement_constant_covers_exactly_the_four_book8_lines():
    """Il. 9/11/14 have their own genuine editorial gaps (declared in
    manifests/Iliad.yaml's expected_line_gaps) and must NOT be supplemented —
    only Book 8's four Allen omissions get the Perseus-text injection."""
    assert set(s1.SUPPLEMENTED_LINES) == {8}
    assert set(s1.SUPPLEMENTED_LINES[8]) == {548, 550, 551, 552}
    for text in s1.SUPPLEMENTED_LINES[8].values():
        assert text.strip() == text
        assert text  # non-empty
