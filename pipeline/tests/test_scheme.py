import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import scheme as scheme_mod


def test_default_and_named_lookup():
    assert scheme_mod.get(None).name == "bekker"
    assert scheme_mod.get("").name == "bekker"
    assert scheme_mod.get("busse").name == "busse"
    assert scheme_mod.get("stephanus").name == "stephanus"
    assert scheme_mod.get("verse-line").name == "verse-line"


def test_for_manifest_reads_citation_scheme():
    assert scheme_mod.for_manifest({}).name == "bekker"
    assert scheme_mod.for_manifest({"citation": {"scheme": "stephanus"}}).name == "stephanus"
    assert scheme_mod.for_manifest({"citation": {"scheme": "verse-line"}}).name == "verse-line"

    class M:
        data = {"citation": {"scheme": "busse"}}

    assert scheme_mod.for_manifest(M()).name == "busse"


def test_bekker_capabilities():
    s = scheme_mod.get("bekker")
    assert s.page_div_type == "Bekker-page"
    assert not s.has_sections
    assert s.bekker_native
    assert s.lines_user_facing
    assert s.validation_mode == "range"
    assert s.range_sides == ("a", "b")
    assert s.compose_column("16a") == "16a"


def test_busse_capabilities_synthesize_a_side_column():
    s = scheme_mod.get("busse")
    assert s.page_div_type == "page"
    assert not s.has_sections
    assert not s.bekker_native
    assert s.validation_mode == "observed"
    assert s.range_sides is None
    assert s.compose_column("1") == "1a"


def test_stephanus_capabilities_compose_page_plus_section():
    s = scheme_mod.get("stephanus")
    assert s.page_div_type == "Stephanus-page"
    assert s.section_div_type == "section"
    assert s.has_sections
    assert not s.bekker_native
    assert not s.lines_user_facing          # Plato cited to the section, not line
    assert s.validation_mode == "observed"
    assert s.range_sides is None            # never enumerate a rectangular range
    assert s.section_letters == ("a", "b", "c", "d", "e")
    assert s.compose_column("2", "a") == "2a"
    assert s.compose_column("17", "e") == "17e"


def test_verse_line_capabilities_book_container_no_sections():
    s = scheme_mod.get("verse-line")
    assert s.name == "verse-line"
    assert s.page_div_type == "Book"
    assert s.section_div_type is None
    assert not s.has_sections
    assert not s.bekker_native
    assert s.lines_user_facing            # Homer is cited book.line
    assert s.validation_mode == "verse"
    assert s.range_sides is None          # books are a linear container, never a rectangle
    assert s.section_letters == ()        # no letter axis in verse
    assert s.compose_column("9") == "9"   # the book number IS the column token


def test_verse_line_validation_clean_and_declared_gap_pass():
    # Continuous ascent within each book is clean.
    assert scheme_mod.validate_line_sequence({1: [1, 2, 3], 2: [1, 2]}) == []
    # A declared gap (the vulgate legitimately skips line 367 in book 9) passes.
    assert (
        scheme_mod.validate_line_sequence(
            {9: [364, 365, 366, 368]},
            [{"book": 9, "after": 366, "next": 368}],
        )
        == []
    )


def test_verse_line_validation_undeclared_gap_fails():
    # The same skip, undeclared, is reported as an unexpected gap.
    assert scheme_mod.validate_line_sequence({9: [364, 365, 366, 368]}) == [
        {"book": 9, "after": 366, "next": 368}
    ]
    # A declared gap in a DIFFERENT book does not excuse this one.
    assert scheme_mod.validate_line_sequence(
        {9: [364, 365, 366, 368]},
        [{"book": 1, "after": 366, "next": 368}],
    ) == [{"book": 9, "after": 366, "next": 368}]


def test_unknown_scheme_raises():
    with pytest.raises(KeyError):
        scheme_mod.get("nonesuch")
