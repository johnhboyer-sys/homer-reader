"""Stage 8: the rules that decide which phrases exist at all.

A phrase excluded here is beyond the reach of any later filter - it was never
indexed - so these tests guard the exclusions specifically: book edges,
keyless tokens, the recurrence rule, and the lemma readings that must NOT be
narrowed.
"""

import json
import sys
from pathlib import Path

import pytest

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
    # summary.json's token total is read from the SERVED
    # build/dist/<work>/search/offsets.json, not this stage-6 stream doc — a
    # real build always has one by the time stage 8 runs (module docstring).
    # Every test using this helper gets a matching one for free; the dedicated
    # summary test below overwrites it to prove the source really is this file.
    search_dir = build_dir / "dist" / doc["work"] / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    (search_dir / "offsets.json").write_text(
        json.dumps({"token_count": doc["token_count"]}), encoding="utf-8"
    )


def _write_book(build_dir: Path, work: str, book: int, segments: list[dict]) -> None:
    """Write build/dist/<work>/book-<NN>.json, the shape stage 7 emits and
    `_english_stream` reads from — segments[].english.text."""
    work_dir = build_dir / "dist" / work
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / f"book-{book:02d}.json").write_text(
        json.dumps({"book": book, "segments": segments}, ensure_ascii=False),
        encoding="utf-8",
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


def test_recurrence_is_corpus_wide_not_per_work(tmp_path, monkeypatch):
    """A phrase occurring once in each of two works must be KEPT (2 corpus-wide),
    and a phrase occurring once in only one work must be DROPPED. Neither case
    is provable by a fixture where every kept phrase already recurs inside a
    single work — a per-work threshold would pass that fixture too."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "alpha",
            "token_count": 4,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["p", "q", "r", "s"],
            "lemma": ["p", "q", "r", "s"],
        },
    )
    _write_work(
        build_dir,
        {
            "work": "beta",
            "token_count": 4,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["x", "p", "q", "y"],
            "lemma": ["x", "p", "q", "y"],
        },
    )

    ngrams.run()

    browse = {}
    for shard in (build_dir / "dist" / "ngrams" / "form").glob("*.json"):
        browse.update(json.loads(shard.read_text(encoding="utf-8")))

    # "p q" occurs once in alpha and once in beta: 1 + 1 = 2 corpus-wide, kept.
    assert "p q" in browse
    assert browse["p q"][1] == 2  # count
    assert browse["p q"][3] == 2  # across 2 works

    # "r s" occurs once total (alpha only): dropped.
    assert "r s" not in browse


def test_browse_row_distinguishes_length_from_count(tmp_path, monkeypatch):
    """[n, count, score, works] — n and count must not be interchangeable. A
    2-gram occurring twice can't tell a swap bug from a correct build; a 3-gram
    occurring twice (n=3, count=2) can."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "gamma",
            "token_count": 6,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            # "a b c" recurs at offsets 0 and 3.
            "form": ["a", "b", "c", "a", "b", "c"],
            "lemma": ["a", "b", "c", "a", "b", "c"],
        },
    )

    ngrams.run()

    form_a = json.loads(
        (build_dir / "dist" / "ngrams" / "form" / "a.json").read_text(encoding="utf-8")
    )
    row = form_a["a b c"]
    assert row[0] == 3  # n (length of the phrase)
    assert row[1] == 2  # count (times it recurs)


def test_lemma_stream_files_are_populated(tmp_path, monkeypatch):
    """An empty dist/ngrams/lemma/** would pass a test that never opens it.
    Open the lemma shard and assert the expected row is really there."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "delta",
            "token_count": 4,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            # Surface forms never repeat, but the lemma reading "aa bb" recurs.
            "form": ["w1", "w2", "w3", "w4"],
            "lemma": ["aa", "bb", "aa", "bb"],
        },
    )

    ngrams.run()

    lemma_dir = build_dir / "dist" / "ngrams" / "lemma"
    assert lemma_dir.is_dir()
    shard_files = list(lemma_dir.glob("*.json"))
    assert shard_files, "lemma stream produced no shard files"

    lemma_browse = {}
    for shard in shard_files:
        lemma_browse.update(json.loads(shard.read_text(encoding="utf-8")))
    assert "aa bb" in lemma_browse
    row = lemma_browse["aa bb"]
    assert row[0] == 2  # n
    assert row[1] == 2  # count
    assert row[3] == 1  # 1 work

    occ = json.loads(
        (lemma_dir / "occ" / "a-2.json").read_text(encoding="utf-8")
    )
    assert occ["aa bb"] == {"delta": [0, 2]}


def test_cross_line_phrase_survives(tmp_path, monkeypatch):
    """A phrase whose tokens fall in two different line_runs entries is kept —
    straddling is a query-time toggle, not a build-time filter. This asserts
    the behaviour against a real line_runs fixture, not just the absence of a
    filter."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "epsilon",
            "token_count": 8,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            # Four lines of 2 tokens each. "n o" straddles line 1/2 at offset 1
            # and line 3/4 at offset 5 — never within one line_runs entry.
            "segments": [{
                "book": 1,
                "column": "1",
                "line_runs": [[1, 2], [2, 2], [3, 2], [4, 2]],
            }],
            "form": ["m", "n", "o", "p", "m", "n", "o", "p"],
            "lemma": ["m", "n", "o", "p", "m", "n", "o", "p"],
        },
    )

    ngrams.run()

    browse = {}
    for shard in (build_dir / "dist" / "ngrams" / "form").glob("*.json"):
        browse.update(json.loads(shard.read_text(encoding="utf-8")))

    assert "n o" in browse
    assert browse["n o"][1] == 2


def test_english_stream_indexed_and_segments_emitted(tmp_path, monkeypatch):
    """The English stream is tokenized from build/dist/<work>/book-*.json, not
    stage 6's fold streams, and a phrase recurring across both works is
    indexed there too. english-segments.json carries the fields the client
    needs to turn an English offset back into a citation."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    # Minimal Greek streams — irrelevant here beyond satisfying run()'s
    # per-work bookkeeping and giving _english_stream a work name to look up.
    _write_work(
        build_dir,
        {
            "work": "zeta",
            "token_count": 2,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["z1", "z2"],
            "lemma": ["z1", "z2"],
        },
    )
    _write_work(
        build_dir,
        {
            "work": "eta",
            "token_count": 2,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["e1", "e2"],
            "lemma": ["e1", "e2"],
        },
    )

    _write_book(build_dir, "zeta", 1, [
        {"column": "1", "english": {"text": "rosy fingered dawn appeared"}},
    ])
    _write_book(build_dir, "eta", 1, [
        {"column": "1", "english": {"text": "then rosy fingered dawn came"}},
    ])

    ngrams.run()

    eng_dir = build_dir / "dist" / "ngrams" / "english"
    browse = {}
    for shard in eng_dir.glob("*.json"):
        browse.update(json.loads(shard.read_text(encoding="utf-8")))

    assert "rosy fingered dawn" in browse
    row = browse["rosy fingered dawn"]
    assert row[0] == 3  # n
    assert row[1] == 2  # count: once per work
    assert row[3] == 2  # across 2 works

    occ = json.loads((eng_dir / "occ" / "r-3.json").read_text(encoding="utf-8"))
    assert occ["rosy fingered dawn"] == {"eta": [1], "zeta": [0]}

    segments = json.loads(
        (build_dir / "dist" / "ngrams" / "english-segments.json").read_text(encoding="utf-8")
    )
    assert segments["zeta"] == [{"book": 1, "column": "1", "base": 0, "words": 4}]
    assert segments["eta"] == [{"book": 1, "column": "1", "base": 0, "words": 5}]


def test_missing_book_bounds_fails_loudly(tmp_path, monkeypatch):
    """Empty/missing book_bounds must never degrade to treating the whole work
    as one book — that would let a phrase span a real book edge. It must fail
    loudly and name the work."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "theta",
            "token_count": 4,
            "book_bounds": [],
            "chapter_bounds": [],
            "form": ["a", "b", "c", "d"],
            "lemma": ["a", "b", "c", "d"],
        },
    )

    with pytest.raises(ValueError, match="theta"):
        ngrams.run()


def test_lemma_map_strips_empty_headwords(tmp_path, monkeypatch):
    """A surface form's lemma-map entry must never include an empty headword
    string, even when it sits alongside a real one in the same reading."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "iota",
            "token_count": 2,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["bar", "baz"],
            "lemma": [["", "foo"], ["baz"]],
        },
    )

    ngrams.run()

    lemma_map = json.loads(
        (build_dir / "dist" / "lemma-map" / "b.json").read_text(encoding="utf-8")
    )
    assert lemma_map["bar"] == ["foo"]


def test_summary_json_sources_tokens_from_served_offsets(tmp_path, monkeypatch):
    """summary.json is the guide page's only source of corpus numbers (handoff
    §5) — a stale, hand-typed figure is exactly the mistake it exists to
    prevent. This asserts two things a schema check alone would miss: the
    token total comes from the SERVED search/offsets.json (not the stage-6
    stream doc's own token_count, which is deliberately made to disagree
    here), and each stream's "kept" count matches what its shards actually
    hold."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "iliad",
            "token_count": 6,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["p", "q", "p", "q", "r", "s"],
            "lemma": ["p", "q", "p", "q", "r", "s"],
        },
    )
    _write_work(
        build_dir,
        {
            "work": "odyssey",
            "token_count": 4,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["p", "q", "x", "y"],
            "lemma": ["p", "q", "x", "y"],
        },
    )
    _write_book(build_dir, "iliad", 1, [
        {"column": "1", "english": {"text": "rosy dawn rosy dawn"}},
    ])

    # Deliberately disagree with the doc's own token_count (6/4 above) so the
    # test fails if summary.json ever reads the wrong source.
    (build_dir / "dist" / "iliad" / "search" / "offsets.json").write_text(
        json.dumps({"token_count": 61}), encoding="utf-8"
    )
    (build_dir / "dist" / "odyssey" / "search" / "offsets.json").write_text(
        json.dumps({"token_count": 41}), encoding="utf-8"
    )

    ngrams.run()

    summary = json.loads(
        (build_dir / "dist" / "ngrams" / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["works"] == ["iliad", "odyssey"]
    assert summary["tokens"] == {"iliad": 61, "odyssey": 41, "total": 102}

    for stream_name in ("form", "lemma", "english"):
        browse = {}
        for shard in (build_dir / "dist" / "ngrams" / stream_name).glob("*.json"):
            browse.update(json.loads(shard.read_text(encoding="utf-8")))
        assert summary["streams"][stream_name]["kept"] == len(browse)
        assert summary["streams"][stream_name]["kept"] > 0


def test_summary_json_fails_loudly_without_served_offsets(tmp_path, monkeypatch):
    """A work whose search/offsets.json is missing must fail the build, not
    silently omit that work's tokens from the corpus total."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(ngrams, "BUILD_DIR", build_dir)

    _write_work(
        build_dir,
        {
            "work": "kappa",
            "token_count": 2,
            "book_bounds": [{"book": 1, "start": 0}],
            "chapter_bounds": [],
            "form": ["a", "b"],
            "lemma": ["a", "b"],
        },
    )
    # _write_work already wrote a matching search/offsets.json; remove it to
    # simulate stage 7 not having run yet for this work.
    (build_dir / "dist" / "kappa" / "search" / "offsets.json").unlink()

    with pytest.raises(ValueError, match="kappa"):
        ngrams.run()
