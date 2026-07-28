"""Stage 8: the rules that decide which phrases exist at all.

A phrase excluded here is beyond the reach of any later filter - it was never
indexed - so these tests guard the exclusions specifically: book edges,
keyless tokens, the recurrence rule, and the lemma readings that must NOT be
narrowed.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import stage8_ngrams as ngrams  # noqa: E402


def grams(stream, books, total, n=None):
    """{phrase: [offsets]} for a stream of option-lists."""
    out = {}
    for gram, at in ngrams._phrases(stream, books, total):
        if n is None or len(gram.split(" ")) == n:
            out.setdefault(gram, []).append(at)
    return out


def one(*words):
    """A stream of unambiguous positions."""
    return [[w] for w in words]


def _write_work(build_dir: Path, doc: dict) -> None:
    ngrams_dir = build_dir / "ngrams"
    ngrams_dir.mkdir(parents=True, exist_ok=True)
    (ngrams_dir / f"{doc['work']}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


class TestBoundaries:
    def test_a_phrase_never_spans_a_book_edge(self):
        # Book 1 is offsets 0-2, book 2 is 3-5.
        stream = one("a", "b", "c", "d", "e", "f")
        found = grams(stream, [0, 3], 6, n=2)
        assert "b c" in found          # inside book 1
        assert "d e" in found          # inside book 2
        assert "c d" not in found      # across the edge

    def test_a_phrase_never_spans_a_keyless_token(self):
        stream = one("a", "b") + [None] + one("c", "d")
        found = grams(stream, [0], 5, n=2)
        assert "a b" in found
        assert "c d" in found
        assert "b c" not in found      # the gap breaks the stream
        assert not any(g for g in grams(stream, [0], 5, n=3) if g.startswith("b"))

    def test_offsets_are_the_phrase_start(self):
        stream = one("a", "b", "c")
        assert grams(stream, [0], 3, n=2) == {"a b": [0], "b c": [1]}

    def test_every_length_from_two_to_five(self):
        stream = one(*"abcdef")
        lengths = {len(g.split(" ")) for g in grams(stream, [0], 6)}
        assert lengths == {2, 3, 4, 5}


class TestLemmaReadings:
    def test_an_ambiguous_position_contributes_every_reading(self):
        # The second position licenses two lemmas; both phrases must exist.
        stream = [["a"], ["b", "c"]]
        assert set(grams(stream, [0], 2, n=2)) == {"a b", "a c"}

    def test_readings_multiply_across_positions(self):
        stream = [["a", "b"], ["c", "d"]]
        assert set(grams(stream, [0], 2, n=2)) == {"a c", "a d", "b c", "b d"}

    def test_readings_of_an_unambiguous_window_is_one_phrase(self):
        assert ngrams._readings([["a"], ["b"]]) == [["a", "b"]]

    def test_every_reading_shares_the_one_offset(self):
        stream = [["a"], ["b", "c"]]
        found = grams(stream, [0], 2, n=2)
        assert found["a b"] == [0] and found["a c"] == [0]


def test_run_emits_split_ngram_and_lemma_map_files(tmp_path, monkeypatch):
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "iliad",
            "token_count": 8,
            "book_bounds": [{"book": 1, "start": 0}, {"book": 2, "start": 6}],
            "chapter_bounds": [],
            # The first "a b" crosses a line break here, but stage 8 must keep
            # it because straddling is a query-time toggle.
            "segments": [
                {"book": 1, "column": "1", "line_runs": [[1, 2], [2, 4]]},
                {"book": 2, "column": "2", "line_runs": [[1, 2]]},
            ],
            "form": ["u", "a", "b", "a", "b", "b", "c", "d"],
            "lemma": [["u"], ["a"], ["b"], ["a"], ["b"], ["b"], ["c"], ["d"]],
        },
    )
    _write_work(
        build_dir,
        {
            "work": "odyssey",
            "token_count": 6,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "segments": [{"book": 1, "column": "1", "line_runs": [[1, 6]]}],
            "form": ["b", "c", "logou", "y", "b", "c"],
            "lemma": [["b"], ["c"], ["logos"], ["y"], ["b"], ["c"]],
        },
    )

    out_root = ngrams.run()

    assert out_root == build_dir / "dist" / "ngrams"

    form_a = json.loads((build_dir / "dist" / "ngrams" / "form" / "a.json").read_text(encoding="utf-8"))
    form_b = json.loads((build_dir / "dist" / "ngrams" / "form" / "b.json").read_text(encoding="utf-8"))
    lemma_l = json.loads((build_dir / "dist" / "lemma-map" / "l.json").read_text(encoding="utf-8"))

    assert form_a["a b"][:2] == [2, 2]
    assert form_a["a b"][3] == 1
    assert form_b["b c"][:2] == [2, 2]
    assert form_b["b c"][3] == 1
    assert lemma_l == {"logou": ["logos"]}

    occ_a = json.loads((build_dir / "dist" / "ngrams" / "form" / "occ" / "a-2.json").read_text(encoding="utf-8"))
    occ_b = json.loads((build_dir / "dist" / "ngrams" / "form" / "occ" / "b-2.json").read_text(encoding="utf-8"))

    assert occ_a["a b"] == {"iliad": [1, 2]}
    assert occ_b["b c"] == {"odyssey": [0, 4]}

    all_browse = {}
    for shard in (build_dir / "dist" / "ngrams" / "form").glob("*.json"):
        all_browse.update(json.loads(shard.read_text(encoding="utf-8")))
    assert "logou y" not in all_browse
