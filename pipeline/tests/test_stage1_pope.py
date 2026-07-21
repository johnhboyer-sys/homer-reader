"""Stage 1g: Pope's verse translation (PG boilerplate stripping, 24-book
split, verse-structure preservation, curated scene-anchor resolution).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from homer_pipeline import apparatus_scenes
from homer_pipeline import stage1_pope as s1
from homer_pipeline.config import Manifest, SOURCES_DIR

FIXTURE = Path(__file__).parent / "fixtures" / "pope" / "tiny.txt"
REAL_ILIAD = SOURCES_DIR / "pope" / "pope-iliad.txt"
REAL_ODYSSEY = SOURCES_DIR / "pope" / "pope-odyssey.txt"
REAL_ILIAD_ANCHORS = SOURCES_DIR / "pope" / "scene-anchors-iliad.json"


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


# --- resolve_scene_anchors: pure resolver -----------------------------------

def test_resolve_scene_anchors_correct_offsets_and_no_entry_needed_for_first_scene():
    text = (
        "First scene opens the book with calm words.\n"
        "It continues for one more line.\n\n"
        "Second scene begins the trouble now.\n"
        "More trouble follows swiftly.\n\n"
        "Third scene ends in triumph.\n"
        "The end."
    )
    scene_starts = [1, 10, 20]
    entries = [
        {"book": 1, "n": 10, "anchor": "Second scene begins the trouble now.", "status": "verified"},
        {"book": 1, "n": 20, "anchor": "Third scene ends in triumph.", "status": "verified"},
    ]
    results = s1.resolve_scene_anchors(text, entries, scene_starts, 1)
    assert [r["n"] for r in results] == [10, 20]
    assert results[0]["offset"] == text.index("Second scene begins the trouble now.")
    assert results[1]["offset"] == text.index("Third scene ends in triumph.")
    assert results[0]["offset"] < results[1]["offset"]
    assert all(r["warning"] is None for r in results)
    # Scene start 1 (the first) has no entry at all and raised nothing —
    # run() gives it the automatic book-opening tick, not this resolver.


def test_resolve_scene_anchors_duplicate_phrase_raises():
    text = "Here the same phrase begins.\nAgain the same phrase begins here."
    entries = [{"book": 1, "n": 5, "anchor": "the same phrase", "status": "verified"}]
    with pytest.raises(ValueError, match="occurs 2 times"):
        s1.resolve_scene_anchors(text, entries, [1, 5], 1)


def test_resolve_scene_anchors_missing_phrase_raises():
    text = "Nothing here matches at all."
    entries = [{"book": 1, "n": 5, "anchor": "a phrase never present", "status": "verified"}]
    with pytest.raises(ValueError, match="occurs 0 times"):
        s1.resolve_scene_anchors(text, entries, [1, 5], 1)


def test_resolve_scene_anchors_non_monotonic_raises():
    # n=20's anchor physically precedes n=10's anchor in the text — resolved
    # offsets go backwards relative to reading order.
    text = "Scene twenty starts here first.\nScene ten starts here second."
    entries = [
        {"book": 1, "n": 10, "anchor": "Scene ten starts here second.", "status": "verified"},
        {"book": 1, "n": 20, "anchor": "Scene twenty starts here first.", "status": "verified"},
    ]
    with pytest.raises(ValueError, match="not strictly increasing"):
        s1.resolve_scene_anchors(text, entries, [1, 10, 20], 1)


def test_resolve_scene_anchors_n_not_scene_start_raises():
    text = "Some verse text here.\nMore verse text."
    entries = [{"book": 1, "n": 999, "anchor": "More verse text.", "status": "verified"}]
    with pytest.raises(ValueError, match="not one of this book's staged scene starts"):
        s1.resolve_scene_anchors(text, entries, [1, 10], 1)


def test_resolve_scene_anchors_missing_entry_raises():
    text = "Some verse text here.\nMore verse text."
    entries: list[dict] = []  # scene start 10 has no entry at all
    with pytest.raises(ValueError, match=r"scene start n=10 has 0 anchor entries"):
        s1.resolve_scene_anchors(text, entries, [1, 10], 1)


def test_resolve_scene_anchors_duplicate_entries_for_one_scene_start_raises():
    text = "Some verse text here.\nMore verse text."
    entries = [
        {"book": 1, "n": 10, "anchor": "More verse text.", "status": "verified"},
        {"book": 1, "n": 10, "anchor": "More verse text.", "status": "draft"},
    ]
    with pytest.raises(ValueError, match=r"scene start n=10 has 2 anchor entries"):
        s1.resolve_scene_anchors(text, entries, [1, 10], 1)


def test_resolve_scene_anchors_unanchored_skips_tick_and_reports():
    text = "Some verse text here.\nMore verse text."
    entries = [{"book": 1, "n": 10, "anchor": None, "status": "unanchored"}]
    results = s1.resolve_scene_anchors(text, entries, [1, 10], 1)
    assert results == [{"n": 10, "offset": None, "status": "unanchored", "warning": None}]


def test_resolve_scene_anchors_sentence_boundary_warning_surfaces():
    # The line before the anchor has no terminal . ? ! — a soft signal the
    # scene boundary may not line up cleanly with Pope's own sentence break.
    text = "This line has no terminal mark\nScene two opens weirdly."
    entries = [{"book": 1, "n": 5, "anchor": "Scene two opens weirdly.", "status": "verified"}]
    results = s1.resolve_scene_anchors(text, entries, [1, 5], 1)
    assert len(results) == 1
    assert results[0]["offset"] == text.index("Scene two opens weirdly.")
    assert results[0]["warning"] is not None
    assert "not ending in . ? !" in results[0]["warning"]


def test_resolve_scene_anchors_clean_sentence_boundary_has_no_warning():
    text = "This line ends properly.\nScene two opens cleanly."
    entries = [{"book": 1, "n": 5, "anchor": "Scene two opens cleanly.", "status": "verified"}]
    results = s1.resolve_scene_anchors(text, entries, [1, 5], 1)
    assert results[0]["warning"] is None


def test_resolve_scene_anchors_non_line_start_anchor_raises():
    # The anchor text is real and unique, but starts mid-line (not preceded
    # by "\n" and not at offset 0) — not a legal verse-line start.
    text = "A line containing MIDLINE TARGET inside it.\nAnother line."
    entries = [{"book": 1, "n": 5, "anchor": "MIDLINE TARGET inside it.", "status": "verified"}]
    with pytest.raises(ValueError, match="does not begin at a verse-line start"):
        s1.resolve_scene_anchors(text, entries, [1, 5], 1)


# --- load_scene_starts: apparatus staging -> scene-start line numbers ------

def test_load_scene_starts_reads_staged_scene_first_lines(tmp_path, monkeypatch):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    (staging_dir / "scenes-testwork-01.json").write_text(
        json.dumps(
            {
                "work": "testwork",
                "status": "draft",
                "books": [
                    {
                        "book": 1,
                        "argument": "A short test argument for book one.",
                        "where": ["Troy"],
                        "who": ["Hector"],
                        "days": "1",
                        "scenes": [
                            {"lines": [1, 4], "summary": "First scene summary text.",
                             "location": "Troy", "dayNumber": None},
                            {"lines": [5, 8], "summary": "Second scene summary text.",
                             "location": "Troy", "dayNumber": None},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", staging_dir)

    manifest = _FakeManifest(data={"books": [{"n": 1, "end": "1.8"}]}, books=[{"n": 1}], work_id="testwork")
    assert s1.load_scene_starts(manifest) == {1: [1, 5]}


def test_load_scene_starts_book_absent_from_staging_is_simply_missing(tmp_path, monkeypatch):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", staging_dir)

    manifest = _FakeManifest(data={"books": []}, books=[], work_id="testwork")
    assert s1.load_scene_starts(manifest) == {}


# --- run(): end-to-end emit shape, scene resolution, and dataset gating ----

class _FakeManifest:
    def __init__(self, data, books, work_id="testwork"):
        self.data = data
        self.books = books
        self.work_id = work_id


def _fake_spine(book_first_lines: dict[int, int]):
    return {
        "segments": [
            {"id": f"{n}:{n}", "book": n, "lines": [{"n": first}]}
            for n, first in book_first_lines.items()
        ]
    }


def _patch_pope_paths(monkeypatch, tmp_path):
    """Route BUILD_DIR to tmp_path and SOURCES_DIR to tests/fixtures (so
    'pope/tiny.txt' and 'pope/scene-anchors-testwork.json' resolve to the
    committed fixtures) in both config and the already-imported stage1_pope
    module (which imported the names directly)."""
    from homer_pipeline import config as config_mod

    monkeypatch.setattr(config_mod, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "SOURCES_DIR", FIXTURE.parents[1])
    monkeypatch.setattr(s1, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(s1, "SOURCES_DIR", FIXTURE.parents[1])


def test_run_falls_back_to_book_level_tick_when_no_scenes_staged(tmp_path, monkeypatch):
    _patch_pope_paths(monkeypatch, tmp_path)
    # No apparatus staging at all for "testwork" — every book keeps its
    # book-level fallback tick, even though a (unused) scene-anchor dataset
    # entry exists for book 1 in the fixture dataset.
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", tmp_path / "empty-staging")

    manifest = _FakeManifest(
        data={"english": {"third": {"id": "pope", "source": "pope/tiny.txt"}}},
        books=[{"n": 1}, {"n": 2}],
    )
    spine = _fake_spine({1: 1, 2: 45})

    result = s1.run(manifest, spine)

    assert result["books"] == 2
    assert result["chunks"] == 2
    assert result["no_argument_marker"] == [2]
    assert result["anchors_resolved"] == 0
    assert result["unanchored"] == []
    assert result["draft_count"] == 0
    assert result["sentence_warnings"] == []
    assert result["books_without_staged_scenes"] == [1, 2]

    chunks = json.loads((tmp_path / "stage1" / "third_chunks.json").read_text())
    assert set(chunks) == {"1:1", "2:2"}
    for seg_id, pieces in chunks.items():
        assert len(pieces) == 1
        piece = pieces[0]
        assert piece["cont"] is False
        assert piece["chapter"] in {"1", "2"}
        assert "\n" in piece["text"]  # verse line breaks preserved
        # Book-level fallback: exactly one tick, real, at the book's own
        # first Greek line, offset 0.
        assert piece["bekker"] == [
            {"n": 1 if piece["chapter"] == "1" else 45, "offset": 0, "real": True}
        ]


def test_run_resolves_scene_anchors_for_staged_books(tmp_path, monkeypatch):
    _patch_pope_paths(monkeypatch, tmp_path)

    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    (staging_dir / "scenes-testwork-01.json").write_text(
        json.dumps(
            {
                "work": "testwork",
                "status": "draft",
                "books": [
                    {
                        "book": 1,
                        "argument": "A short test argument for book one.",
                        "where": ["Troy"],
                        "who": ["Achilles"],
                        "days": "1",
                        "scenes": [
                            {"lines": [1, 4], "summary": "First scene summary text.",
                             "location": "Troy", "dayNumber": None},
                            {"lines": [5, 8], "summary": "Second scene summary text.",
                             "location": "Troy", "dayNumber": None},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", staging_dir)

    manifest = _FakeManifest(
        data={
            "english": {"third": {"id": "pope", "source": "pope/tiny.txt"}},
            "books": [{"n": 1, "end": "1.8"}, {"n": 2, "end": "2.4"}],
        },
        books=[{"n": 1}, {"n": 2}],
    )
    spine = _fake_spine({1: 1, 2: 45})

    result = s1.run(manifest, spine)

    assert result["anchors_resolved"] == 1
    assert result["unanchored"] == []
    assert result["draft_count"] == 0
    assert result["books_without_staged_scenes"] == [2]  # book 2 never staged

    chunks = json.loads((tmp_path / "stage1" / "third_chunks.json").read_text())

    # Book 1: the automatic book-opening tick at offset 0, plus a real
    # resolved tick for the second staged scene (n=5) — sorted by offset,
    # first tick stays offset 0.
    parsed = s1.parse_work(FIXTURE, 2)
    text1 = s1.build_verse_text(parsed[1]["verse_paragraphs"])
    expected_offset = text1.index("Declare, O Muse! in what ill-fated hour")
    assert chunks["1:1"][0]["bekker"] == [
        {"n": 1, "offset": 0, "real": True},
        {"n": 5, "offset": expected_offset, "real": True},
    ]

    # Book 2: never staged — book-level fallback only.
    assert chunks["2:2"][0]["bekker"] == [{"n": 45, "offset": 0, "real": True}]


def test_run_raises_when_scene_anchor_dataset_missing(tmp_path, monkeypatch):
    _patch_pope_paths(monkeypatch, tmp_path)

    manifest = _FakeManifest(
        data={"english": {"third": {"id": "pope", "source": "pope/tiny.txt"}}},
        books=[{"n": 1}, {"n": 2}],
        work_id="nodataset",  # no fixtures/pope/scene-anchors-nodataset.json
    )
    spine = _fake_spine({1: 1, 2: 45})

    with pytest.raises(ValueError, match="scene-anchor dataset missing"):
        s1.run(manifest, spine)


def test_run_with_no_third_config_writes_empty_chunks(tmp_path, monkeypatch):
    from homer_pipeline import config as config_mod

    monkeypatch.setattr(config_mod, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(s1, "BUILD_DIR", tmp_path)

    manifest = _FakeManifest(data={"english": {}}, books=[{"n": 1}])
    result = s1.run(manifest, _fake_spine({1: 1}))

    assert result == {
        "chunks": 0,
        "books": 0,
        "no_argument_marker": [],
        "anchors_resolved": 0,
        "unanchored": [],
        "draft_count": 0,
        "sentence_warnings": [],
        "books_without_staged_scenes": [],
    }
    assert json.loads((tmp_path / "stage1" / "third_chunks.json").read_text()) == {}


# --- real dataset end-to-end (skips until the parallel drafting lane lands) -

@pytest.mark.skipif(
    not REAL_ILIAD_ANCHORS.exists(),
    reason="curated Pope scene-anchor dataset not yet drafted (sources/pope/scene-anchors-iliad.json)",
)
def test_resolve_scene_anchors_real_iliad_dataset_end_to_end():
    manifest = Manifest.for_work("Iliad")
    dataset = s1.load_scene_anchor_dataset("iliad")
    scene_starts = s1.load_scene_starts(manifest)
    parsed = s1.parse_work(REAL_ILIAD, 24)

    entries_by_book: dict[int, list[dict]] = {}
    for entry in dataset["anchors"]:
        entries_by_book.setdefault(entry["book"], []).append(entry)

    assert scene_starts, "expected apparatus/staging scenes for the Iliad"
    for book_n, starts in scene_starts.items():
        text = s1.build_verse_text(parsed[book_n]["verse_paragraphs"])
        # Must resolve cleanly against the real, current Pope text — any
        # ValueError here means the dataset has drifted from the source.
        s1.resolve_scene_anchors(text, entries_by_book.get(book_n, []), starts, book_n)
