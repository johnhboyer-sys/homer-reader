"""Stage 1g: Pope's verse translation (PG boilerplate stripping, 24-book
split, verse-structure preservation, book-level anchor monotonicity).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from homer_pipeline import stage1_pope as s1
from homer_pipeline.config import SOURCES_DIR

FIXTURE = Path(__file__).parent / "fixtures" / "pope" / "tiny.txt"
REAL_ILIAD = SOURCES_DIR / "pope" / "pope-iliad.txt"
REAL_ODYSSEY = SOURCES_DIR / "pope" / "pope-odyssey.txt"


# --- PG boilerplate stripping ------------------------------------------------

def test_strip_pg_boilerplate_drops_header_and_footer():
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1.strip_pg_boilerplate(raw, "tiny.txt")
    assert "This eBook is for the use of anyone" not in body
    assert "This is boilerplate license text" not in body
    assert "*** START OF THE PROJECT GUTENBERG EBOOK" not in body
    assert "*** END OF THE PROJECT GUTENBERG EBOOK" not in body
    # The stray "BOOK III." planted in the footer must never surface.
    assert "BOOK III." not in body


def test_strip_pg_boilerplate_raises_loudly_when_markers_missing():
    with pytest.raises(ValueError, match="markers not found"):
        s1.strip_pg_boilerplate("no markers here at all", "broken.txt")
    with pytest.raises(ValueError, match="markers not found"):
        s1.strip_pg_boilerplate(
            "*** START OF THE PROJECT GUTENBERG EBOOK X ***\nonly a start",
            "broken.txt",
        )


def test_truncate_endmatter_excises_concluding_note_and_footnote_tail():
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1._truncate_endmatter(s1.strip_pg_boilerplate(raw, "tiny.txt"))
    # The real (unindented) heading and everything after it — the critical
    # essay and the numbered footnote endnotes — must be gone. The Contents
    # page's indented " CONCLUDING NOTE." entry, being front matter that
    # precedes the excised tail, legitimately remains.
    assert not s1._CONCLUDING_NOTE_RE.search(body)
    assert "We have now passed through" not in body
    assert "natural root of this quarrel" not in body
    # Book II's real verse (before the excised tail) must survive.
    assert "wheel of state" in body


def test_truncate_endmatter_indented_toc_entry_is_not_mistaken_for_the_heading():
    # The fixture's Contents block lists " CONCLUDING NOTE." (indented) well
    # before the real body — truncating there would wipe out every book.
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1.strip_pg_boilerplate(raw, "tiny.txt")
    truncated = s1._truncate_endmatter(body)
    assert "BOOK I." in truncated
    assert "BOOK II." in truncated
    assert "wheel of state" in truncated


# --- 24-book split (both real works) -----------------------------------------

def test_split_books_fixture_finds_exactly_two_in_order():
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1._truncate_endmatter(s1.strip_pg_boilerplate(raw, "tiny.txt"))
    blocks = s1.split_books(body, 2, "tiny.txt")
    assert [n for n, _ in blocks] == [1, 2]
    assert "Achilles' wrath" in blocks[0][1]
    assert "wheel of state" in blocks[1][1]


def test_split_books_raises_on_wrong_book_count():
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1._truncate_endmatter(s1.strip_pg_boilerplate(raw, "tiny.txt"))
    with pytest.raises(ValueError, match="expected BOOK 1..3"):
        s1.split_books(body, 3, "tiny.txt")


@pytest.mark.parametrize(
    "path", [REAL_ILIAD, REAL_ODYSSEY], ids=["iliad", "odyssey"]
)
def test_split_books_real_sources_have_exactly_24_books_in_order(path):
    if not path.exists():
        pytest.skip(f"{path} not vendored in this checkout")
    raw = path.read_text(encoding="utf-8")
    body = s1._truncate_endmatter(s1.strip_pg_boilerplate(raw, path.name))
    blocks = s1.split_books(body, 24, path.name)
    assert [n for n, _ in blocks] == list(range(1, 25))


# --- parse_book: argument/verse split, footnote/illustration cleanup --------

def _fixture_books():
    raw = FIXTURE.read_text(encoding="utf-8")
    body = s1._truncate_endmatter(s1.strip_pg_boilerplate(raw, "tiny.txt"))
    blocks = s1.split_books(body, 2, "tiny.txt")
    return {n: s1.parse_book(text, n) for n, text in blocks}


def test_parse_book_separates_argument_prose_from_verse():
    books = _fixture_books()
    b1 = books[1]
    assert "In the war of Toyland" in b1["argument"]
    assert b1["had_argument_marker"] is True
    # Verse never leaks into the argument string.
    assert "Achilles" not in b1["argument"]
    # Argument text never leaks into the verse.
    verse_flat = " ".join(l for p in b1["verse_paragraphs"] for l in p)
    assert "Toyland" not in verse_flat
    assert "Achilles" in verse_flat


def test_parse_book_handles_missing_argument_marker():
    # Book II's fixture text has no "ARGUMENT." line at all (mirrors the
    # real Odyssey Book VIII quirk) — the summary prose is still captured.
    books = _fixture_books()
    b2 = books[2]
    assert b2["had_argument_marker"] is False
    assert "catalogue of the toy forces" in b2["argument"]
    verse_flat = " ".join(l for p in b2["verse_paragraphs"] for l in p)
    assert "wheel of state" in verse_flat


def test_parse_book_strips_inline_footnote_markers_from_verse():
    books = _fixture_books()
    verse_flat = " ".join(l for p in books[1]["verse_paragraphs"] for l in p)
    assert "[2]" not in verse_flat
    assert "[3]" not in verse_flat
    assert books[1]["footnote_markers_stripped"] == 2
    # The word the marker was attached to survives untouched.
    assert "direful spring" in verse_flat


def test_parse_book_drops_illustration_caption_paragraphs():
    books = _fixture_books()
    verse_flat = " ".join(l for p in books[1]["verse_paragraphs"] for l in p)
    assert "HOMER INVOKING THE MUSE" not in verse_flat
    assert "Illustration" not in verse_flat
    assert books[1]["illustrations_dropped"] == 1
    # The couplets on either side of the caption both survive.
    assert "untimely slain" in verse_flat
    assert "mountains of the dead" in verse_flat


# --- verse-structure preservation (round trip) -------------------------------

def test_build_verse_text_preserves_lines_and_stanza_breaks():
    books = _fixture_books()
    text = s1.build_verse_text(books[1]["verse_paragraphs"])
    # Every source line survives as its own line (poetry, not flattened
    # prose) — round trip: splitting back on the stanza/line separators
    # reconstructs the original per-line structure.
    stanzas = text.split("\n\n")
    assert len(stanzas) == len(books[1]["verse_paragraphs"])
    for stanza_text, stanza_lines in zip(stanzas, books[1]["verse_paragraphs"]):
        assert stanza_text.split("\n") == stanza_lines
    # A single line break within a stanza, not a paragraph-flattening space.
    assert "\n" in stanzas[0]
    assert "  " not in text  # no accidental double-space from a bad join


def test_build_verse_text_empty_input_is_empty_string():
    assert s1.build_verse_text([]) == ""


# --- run(): end-to-end emit shape + anchor monotonicity ---------------------

class _FakeManifest:
    def __init__(self, data, books):
        self.data = data
        self.books = books


def _fake_spine(book_first_lines: dict[int, int]):
    return {
        "segments": [
            {"id": f"{n}:{n}", "book": n, "lines": [{"n": first}]}
            for n, first in book_first_lines.items()
        ]
    }


def test_run_emits_third_chunks_in_ross_overlay_shape(tmp_path, monkeypatch):
    from homer_pipeline import config as config_mod

    monkeypatch.setattr(config_mod, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "SOURCES_DIR", FIXTURE.parents[1])
    monkeypatch.setattr(s1, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(s1, "SOURCES_DIR", FIXTURE.parents[1])

    manifest = _FakeManifest(
        data={"english": {"third": {"id": "pope", "source": "pope/tiny.txt"}}},
        books=[{"n": 1}, {"n": 2}],
    )
    spine = _fake_spine({1: 1, 2: 45})

    result = s1.run(manifest, spine)

    assert result["books"] == 2
    assert result["chunks"] == 2
    assert result["no_argument_marker"] == [2]

    import json

    chunks = json.loads((tmp_path / "stage1" / "third_chunks.json").read_text())
    assert set(chunks) == {"1:1", "2:2"}
    for seg_id, pieces in chunks.items():
        assert len(pieces) == 1
        piece = pieces[0]
        assert piece["cont"] is False
        assert piece["chapter"] in {"1", "2"}
        assert "\n" in piece["text"]  # verse line breaks preserved
        # Anchor monotonicity: exactly one tick, real, at the book's own
        # first Greek line, offset 0 — trivially monotonic (a single-tick
        # sequence can't be out of order) and honestly certain.
        assert piece["bekker"] == [
            {"n": 1 if piece["chapter"] == "1" else 45, "offset": 0, "real": True}
        ]


def test_run_with_no_third_config_writes_empty_chunks(tmp_path, monkeypatch):
    from homer_pipeline import config as config_mod

    monkeypatch.setattr(config_mod, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(s1, "BUILD_DIR", tmp_path)

    manifest = _FakeManifest(data={"english": {}}, books=[{"n": 1}])
    result = s1.run(manifest, _fake_spine({1: 1}))

    assert result == {"chunks": 0, "books": 0, "no_argument_marker": []}
    import json

    assert json.loads((tmp_path / "stage1" / "third_chunks.json").read_text()) == {}
