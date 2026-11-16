"""The data the ported search reads (docs/search-port/PLAN.md, lane A).

Aristotle's client engine counts English hits by word position and puts every
hit in a chapter. Homer's chapters are its scenes. These tests pin, on small
hand-made fixtures:

- english_words(): the one English word split, shared with the client through
  fixtures/english_words.json (copied from aristotle-reader 7ddd67b7ef);
- english_word_starts(): where each of those words starts in the text;
- one English index per translation, with word positions, named by slot;
- chapter_bounds: one bound per scene, at the global Greek token offset of
  the scene's first line;
- eng-chapters: the word at which each scene starts in each translation,
  following the reader's scene pages (build/scene-pages, written by
  app/scripts/build-scene-pages.mjs) and, where a stretch shows on two pages
  or on none, the line estimated from the translation's own line marks;
- the preflight gate over all of it.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import preflight  # noqa: E402
from homer_pipeline.search_scenes import (  # noqa: E402
    emit_eng_chapters,
    estimated_line,
    place_words,
)
from homer_pipeline.stage2_validate import check_offsets  # noqa: E402
from homer_pipeline.stage6_search import (  # noqa: E402
    emit_translation_indexes,
    english_word_starts,
    english_words,
    scene_chapter_bounds,
    segment_translations,
)

FIXTURE = json.loads(
    (ROOT / "pipeline" / "tests" / "fixtures" / "english_words.json").read_text(encoding="utf-8")
)


# -- The word split ----------------------------------------------------------

@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda c: c["text"][:24] or "empty")
def test_english_words_matches_the_shared_fixture(case):
    assert english_words(case["text"]) == case["words"]


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda c: c["text"][:24] or "empty")
def test_word_starts_count_the_same_words(case):
    assert len(english_word_starts(case["text"])) == len(case["words"])


def test_word_starts_point_at_each_words_first_letter():
    text = "‘Sing,’ goddess,[^1.1.1] of Peleus’ son—Achilles"
    starts = english_word_starts(text)
    assert english_words(text) == ["sing", "goddess", "of", "peleus", "son", "achilles"]
    assert [text[s] for s in starts] == ["S", "g", "o", "P", "s", "A"]


def test_a_leading_apostrophe_is_not_the_words_start():
    # "'Tis" is the word "tis": its first letter, not the quote mark, starts it.
    assert english_word_starts("'Tis so") == [1, 5]


# -- One index per translation ----------------------------------------------

def _piece(text, chapter="1"):
    return {"chapter": chapter, "text": text, "cont": False, "bekker": [{"n": 1, "offset": 0, "real": True}]}


def _work(tmp_path, segments):
    work = tmp_path / "iliad"
    (work / "search").mkdir(parents=True)
    for i, seg in enumerate(segments, 1):
        (work / f"book-{i:02d}.json").write_text(json.dumps({"book": i, "segments": [seg]}))
    (work / "search" / "meta.json").write_text(json.dumps(
        [{"id": s["id"], "book": i, "column": str(i)} for i, s in enumerate(segments, 1)]))
    return work


def _seg(book, **slots):
    return {"id": f"{book}:1", "column": str(book), "greek": [], "english": None, **slots}


def _load(work, name):
    return json.loads((work / "search" / name).read_text(encoding="utf-8"))


def test_homer_slots_name_the_index_files(tmp_path):
    work = _work(tmp_path, [
        _seg(1, ross=[_piece("Sing, O goddess, the anger")],
             third=[_piece("Achilles’ wrath, to Greece")],
             overlays={"kosmos": [_piece("Anger, goddess, sing it")]}),
    ])
    summary = emit_translation_indexes(work)
    assert set(summary) == {"ross", "third", "overlay-kosmos"}
    assert _load(work, "english-ross.json")["anger"] == [[0, 4]]
    assert _load(work, "english-third.json")["achilles"] == [[0, 0]]
    assert _load(work, "english-overlay-kosmos.json")["sing"] == [[0, 2]]


def test_seg_idx_is_the_books_place_in_meta(tmp_path):
    work = _work(tmp_path, [_seg(1, ross=[_piece("one")]), _seg(2, ross=[_piece("two one")])])
    emit_translation_indexes(work)
    assert _load(work, "english-ross.json") == {"one": [[0, 0], [1, 1]], "two": [[1, 0]]}


def test_a_stale_translation_index_is_removed(tmp_path):
    work = _work(tmp_path, [_seg(1, third=[_piece("old")])])
    emit_translation_indexes(work)
    book = json.loads((work / "book-01.json").read_text())
    del book["segments"][0]["third"]
    (work / "book-01.json").write_text(json.dumps(book))
    assert emit_translation_indexes(work) == {}
    assert not list((work / "search").glob("english-*.json"))


def test_an_overlay_id_that_cannot_name_a_file_is_refused():
    with pytest.raises(ValueError):
        segment_translations({"overlays": {"../x": [_piece("a")]}})


# -- chapter_bounds: the scenes ---------------------------------------------

def _stage3_segments():
    # Book 1: lines 1-4, two tokens each. Book 2: lines 1, 2, 6, 7 (a declared
    # gap after 2), one token each except line 6, which has three.
    def toks(n):
        return [{"t": "x", "k": "x"}] * n
    return [
        {"id": "1:1", "book": 1, "column": "1",
         "lines": [{"n": n, "tokens": toks(2)} for n in (1, 2, 3, 4)]},
        {"id": "2:1", "book": 2, "column": "2",
         "lines": [{"n": 1, "tokens": toks(1)}, {"n": 2, "tokens": toks(1)},
                   {"n": 6, "tokens": toks(3)}, {"n": 7, "tokens": toks(1)}]},
    ]


def _scene_books():
    return [
        {"book": 1, "scenes": [{"lines": [1, 2]}, {"lines": [3, 4]}]},
        {"book": 2, "scenes": [{"lines": [1, 2]}, {"lines": [6, 7]}]},
    ]


def test_chapter_bounds_are_the_scenes_first_lines():
    bounds = scene_chapter_bounds(_scene_books(), _stage3_segments(), [0, 8])
    assert bounds == [
        {"book": 1, "chapter": "1-2", "start": 0, "accuracy": "exact"},
        {"book": 1, "chapter": "3-4", "start": 4, "accuracy": "exact"},
        {"book": 2, "chapter": "1-2", "start": 8, "accuracy": "exact"},
        # Line 6 follows the gap: 8 + 1 + 1, never a renumbered line 3.
        {"book": 2, "chapter": "6-7", "start": 10, "accuracy": "exact"},
    ]


def test_a_scene_starting_on_a_missing_line_is_an_error():
    books = [{"book": 1, "scenes": [{"lines": [1, 4]}]},
             {"book": 2, "scenes": [{"lines": [1, 3]}, {"lines": [4, 7]}]}]
    with pytest.raises(ValueError, match="2.4"):
        scene_chapter_bounds(books, _stage3_segments(), [0, 8])


def test_a_book_without_scenes_is_an_error():
    with pytest.raises(ValueError, match="book 2"):
        scene_chapter_bounds(_scene_books()[:1], _stage3_segments(), [0, 8])


def _offsets(bounds):
    segs = _stage3_segments()
    return {
        "token_count": 14,
        "seg_base_offset": [0, 8],
        "segments": [{"book": s["book"], "column": s["column"],
                      "line_runs": [[l["n"], len(l["tokens"])] for l in s["lines"]]} for s in segs],
        "book_bounds": [{"book": 1, "start": 0}, {"book": 2, "start": 8}],
        "chapter_bounds": bounds,
    }


_GAP = [{"book": 2, "after": 2, "next": 6}]


def test_check_offsets_accepts_scene_bounds():
    bounds = scene_chapter_bounds(_scene_books(), _stage3_segments(), [0, 8])
    result = check_offsets(_offsets(bounds), _stage3_segments(), _GAP)
    assert result["ok"], result["problems"]


def test_check_offsets_rejects_bounds_out_of_order_or_outside_their_book():
    bounds = scene_chapter_bounds(_scene_books(), _stage3_segments(), [0, 8])
    swapped = [bounds[1], bounds[0], *bounds[2:]]
    assert not check_offsets(_offsets(swapped), _stage3_segments(), _GAP)["ok"]
    stray = [*bounds[:3], {**bounds[3], "book": 1}]
    assert not check_offsets(_offsets(stray), _stage3_segments(), _GAP)["ok"]


def test_check_offsets_rejects_a_book_with_no_bounds():
    bounds = scene_chapter_bounds(_scene_books(), _stage3_segments(), [0, 8])[:2]
    assert not check_offsets(_offsets(bounds), _stage3_segments(), _GAP)["ok"]


# -- eng-chapters: the scene each translation's words fall in ---------------

# Twenty characters a line: marks at line 1 (offset 0) and line 6 (offset 100).
MARKS = [{"n": 1, "offset": 0}, {"n": 6, "offset": 100}]


def test_estimated_line_interpolates_between_marks():
    assert estimated_line(MARKS, 0, first_line=1, last_line=10, text_len=200) == 1
    assert estimated_line(MARKS, 50, first_line=1, last_line=10, text_len=200) == 3.5
    # After the last mark, the end of the text stands for the book's last line.
    assert estimated_line(MARKS, 150, first_line=1, last_line=10, text_len=200) == 8


def test_estimated_line_with_one_mark_is_that_marks_line():
    marks = [{"n": 1, "offset": 0}]
    assert estimated_line(marks, 0, first_line=1, last_line=10, text_len=200) == 1
    assert estimated_line(marks, 199, first_line=1, last_line=10, text_len=200) == 1


SCENES = [(1, 4), (5, 10)]


def test_each_word_goes_to_the_page_that_shows_it():
    # Page 1 shows [0, 60), page 2 [60, 200): the word at 70 is on page 2 only,
    # though its estimated line (4.5) is in scene 1.
    placed, stats = place_words([0, 30, 70, 120], [[[0, 60]], [[60, 200]]], SCENES, MARKS, 200, 1, 10)
    assert placed == [0, 0, 1, 1]
    assert stats["on_two_pages"] == 0 and stats["on_no_page"] == 0


def test_a_word_on_two_pages_goes_to_the_scene_of_its_estimated_line():
    # Both pages show [60, 100). Line 4.0 (offset 60) is scene 1; line 5.5
    # (offset 90) is scene 2.
    placed, stats = place_words([60, 90], [[[0, 100]], [[60, 200]]], SCENES, MARKS, 200, 1, 10)
    assert placed == [0, 1]
    assert stats["on_two_pages"] == 2


def test_a_word_on_no_page_goes_to_the_scene_of_its_estimated_line():
    placed, stats = place_words([30, 95], [[[0, 20]], [[150, 200]]], SCENES, MARKS, 200, 1, 10)
    assert placed == [0, 1]
    assert stats["on_no_page"] == 2


def test_with_no_pages_every_word_goes_by_its_estimated_line():
    placed, stats = place_words([0, 50, 90, 150], None, SCENES, MARKS, 200, 1, 10)
    assert placed == [0, 0, 1, 1]
    assert stats["on_no_page"] == 4


def test_a_word_that_would_go_back_a_scene_is_counted_not_hidden():
    # Page 2 alone shows the word at 2; the word at 5 is on both pages and its
    # line (1.25) is scene 1, which would go back. It stays in scene 2, and
    # the step back is counted.
    placed, stats = place_words([2, 5], [[[5, 60]], [[0, 10], [60, 200]]], SCENES, MARKS, 200, 1, 10)
    assert placed == [1, 1]
    assert stats["backwards"] == 1


def _scene_work(tmp_path):
    """One book, lines 1-10, two scenes; Murray (english) and Kosmos (overlay)."""
    text = "Sing goddess. The wrath of Achilles. Then Zeus spoke. And all was done."
    seg = {
        "id": "1:1", "column": "1", "greek": [{"n": n} for n in range(1, 11)],
        "english": {"text": text, "bekker": [{"n": 1, "offset": 0, "real": True},
                                             {"n": 5, "offset": 37, "real": True}]},
        "overlays": {"kosmos": [{"chapter": "1", "cont": False, "text": "Anger sing. Then speech.",
                                 "bekker": [{"n": 1, "offset": 0, "real": True}]}]},
    }
    work = _work(tmp_path, [seg])
    book = json.loads((work / "book-01.json").read_text())
    book["apparatus"] = {"scenes": [{"lines": [1, 4]}, {"lines": [5, 10]}]}
    (work / "book-01.json").write_text(json.dumps(book))
    pages = {"work": "iliad", "books": {"1": {
        "scenes": ["1-4", "5-10"],
        "translations": {
            "murray": {"slot": "english", "anchored": True, "pages": [[[0, 37]], [[37, len(text)]]]},
            # Kosmos has one mark in this book: the reader cannot page it.
            "kosmos": {"slot": "overlay-kosmos", "anchored": False, "pages": None},
        },
    }}}
    return work, pages


def test_eng_chapters_shape_and_starts(tmp_path):
    work, pages = _scene_work(tmp_path)
    summary = emit_eng_chapters(work, pages)
    chapters = _load(work, "eng-chapters.json")
    # "Then" is word 6 of Murray's book.
    assert chapters["english"] == {"0": [[0, "1-4"], [6, "5-10"]]}
    # One mark at line 1: every Kosmos word is in the scene line 1 opens.
    assert chapters["overlay-kosmos"] == {"0": [[0, "1-4"]]}
    assert summary["overlay-kosmos"]["unpaged_books"] == [1]


def test_eng_chapters_refuses_pages_for_other_scenes(tmp_path):
    work, pages = _scene_work(tmp_path)
    pages["books"]["1"]["scenes"] = ["1-3", "4-10"]
    with pytest.raises(ValueError, match="scenes"):
        emit_eng_chapters(work, pages)


def test_eng_chapters_refuses_a_translation_the_pages_do_not_cover(tmp_path):
    work, pages = _scene_work(tmp_path)
    del pages["books"]["1"]["translations"]["kosmos"]
    with pytest.raises(ValueError, match="overlay-kosmos"):
        emit_eng_chapters(work, pages)


# -- The preflight gate -----------------------------------------------------

def _gate(work):
    problems: list = []
    preflight._validate_search_port(work.name, work, problems)
    return [f"{p[1]}: {p[2]}" for p in problems]


def _gated_work(tmp_path):
    work, pages = _scene_work(tmp_path)
    emit_translation_indexes(work)
    emit_eng_chapters(work, pages)
    text = json.loads((work / "book-01.json").read_text())["segments"][0]["english"]["text"]
    index: dict = {}
    for pos, word in enumerate(english_words(text)):
        index.setdefault(word, []).append([0, pos])
    (work / "search" / "english.json").write_text(json.dumps(index))
    (work / "search" / "offsets.json").write_text(json.dumps({
        "token_count": 30, "seg_base_offset": [0],
        "segments": [{"book": 1, "column": "1", "line_runs": [[n, 3] for n in range(1, 11)]}],
        "book_bounds": [{"book": 1, "start": 0}],
        "chapter_bounds": [{"book": 1, "chapter": "1-4", "start": 0, "accuracy": "exact"},
                           {"book": 1, "chapter": "5-10", "start": 12, "accuracy": "exact"}],
    }))
    return work


def test_gate_passes_a_complete_work(tmp_path):
    assert _gate(_gated_work(tmp_path)) == []


@pytest.mark.parametrize("name", ["english.json", "english-overlay-kosmos.json", "eng-chapters.json"])
def test_gate_fails_on_a_missing_file(tmp_path, name):
    work = _gated_work(tmp_path)
    (work / "search" / name).unlink()
    assert any(name in p for p in _gate(work))


def test_gate_fails_on_an_index_from_another_build(tmp_path):
    work = _gated_work(tmp_path)
    (work / "search" / "english.json").write_text(json.dumps({"sing": [[0, 0]]}))
    assert any("english.json" in p for p in _gate(work))


def test_gate_fails_when_scene_starts_do_not_increase(tmp_path):
    work = _gated_work(tmp_path)
    offsets = _load(work, "offsets.json")
    offsets["chapter_bounds"][1]["start"] = 0
    (work / "search" / "offsets.json").write_text(json.dumps(offsets))
    assert any("increase" in p for p in _gate(work))


def test_gate_fails_when_a_book_has_no_scene_bounds(tmp_path):
    work = _gated_work(tmp_path)
    offsets = _load(work, "offsets.json")
    offsets["chapter_bounds"] = []
    (work / "search" / "offsets.json").write_text(json.dumps(offsets))
    assert any("no scene bounds" in p for p in _gate(work))


def test_gate_fails_when_bounds_disagree_with_the_books_scenes(tmp_path):
    work = _gated_work(tmp_path)
    offsets = _load(work, "offsets.json")
    offsets["chapter_bounds"][1]["chapter"] = "5-9"
    (work / "search" / "offsets.json").write_text(json.dumps(offsets))
    assert any("scenes" in p for p in _gate(work))


def test_gate_fails_when_an_eng_chapters_entry_does_not_increase(tmp_path):
    work = _gated_work(tmp_path)
    chapters = _load(work, "eng-chapters.json")
    chapters["english"]["0"] = [[0, "1-4"], [0, "5-10"]]
    (work / "search" / "eng-chapters.json").write_text(json.dumps(chapters))
    assert any("increase" in p for p in _gate(work))
