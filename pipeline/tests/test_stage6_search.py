"""Stage 6: the offset primitive, the morphology feature parser/signatures,
and the grammar/n-gram validators ported from aristotle_pipeline.

The honesty tier is what these tests defend. Morpheus emits one raw parse
string per analysis, and a single analysis can itself be ambiguous ("fem
nom/voc sg"). Counting analysis records would call that a sole certain parse;
expanding syncretic values inside each reading is what makes the ambiguity
count mean what a reader is told it means. And the vulgate lineation is
sacred: `line_runs` must carry the EMITTED line numbers (gaps and all), never
a renumbered enumeration index.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline.stage6_search import (  # noqa: E402
    _curated_entries,
    fold_lemma,
    parse_reading,
    signature,
)
from homer_pipeline.stage2_validate import (  # noqa: E402
    check_grammar,
    check_ngram_streams,
    check_offsets,
    merge_search_checks,
)


def _tokens(*surfaces):
    return [{"t": s, "o": 0} for s in surfaces]


class TestParseReading:
    def test_reads_a_full_verbal_parse(self):
        assert parse_reading("pres ind act 2nd sg") == {
            "tense": ["pres"],
            "mood": ["ind"],
            "voice": ["act"],
            "person": ["2nd"],
            "number": ["sg"],
        }

    def test_expands_syncretic_values_inside_one_reading(self):
        # e.g. a single Morpheus analysis that is genuinely nom-or-voc.
        assert parse_reading("fem nom/voc sg")["case"] == ["nom", "voc"]
        assert parse_reading("neut nom/voc/acc pl")["case"] == ["acc", "nom", "voc"]
        assert parse_reading("masc/fem acc sg")["gender"] == ["fem", "masc"]

    def test_strips_glued_parentheses_from_qualifier_runs(self):
        # Morpheus glues parens to the first and last word: "(epic ionic)".
        assert parse_reading("pres ind act 2nd sg (epic ionic)") == parse_reading(
            "pres ind act 2nd sg"
        )

    def test_ignores_dialect_and_clitic_markers(self):
        assert parse_reading("epic doric aeolic enclitic nu_movable indeclform") == {}

    def test_indexes_explicit_markers_but_infers_no_part_of_speech(self):
        assert parse_reading("indeclform (conj)") == {"marker": ["conj"]}
        assert "marker" not in parse_reading("masc nom sg")

    def test_part_is_the_participle_mood_not_the_particle_marker(self):
        assert parse_reading("pres part act masc nom sg")["mood"] == ["part"]
        assert parse_reading("(particle)") == {"marker": ["particle"]}


class TestSignature:
    def test_keeps_whole_readings_so_correlations_survive(self):
        # A flattened per-category union would let masc+acc+sg match, though
        # neither of these two readings licenses that combination.
        sig = signature([{"parse": "masc nom sg"}, {"parse": "fem acc pl"}])
        combos = [dict(r) for r in sig]
        assert len(combos) == 2
        for reading in combos:
            assert not (
                reading.get("gender") == ("masc",)
                and reading.get("case") == ("acc",)
            )

    def test_is_order_independent(self):
        a = signature([{"parse": "masc nom sg"}, {"parse": "fem acc pl"}])
        b = signature([{"parse": "fem acc pl"}, {"parse": "masc nom sg"}])
        assert a == b

    def test_single_analysis_can_still_be_ambiguous(self):
        # One analysis record, three possible cases -- not one certain parse.
        sig = signature([{"parse": "neut nom/voc/acc pl"}])
        assert len(sig) == 1
        values = {v for reading in sig for cat, vs in reading if cat == "case" for v in vs}
        assert values == {"nom", "voc", "acc"}

    def test_empty_for_analyses_with_no_usable_parse(self):
        assert signature([]) == ()
        assert signature([{"parse": ""}, {"parse": "epic"}]) == ()


class TestCuratedEntries:
    """The grammar signature builder reads this corpus's own curation
    (filter_parses), not Morpheus's raw candidate list -- see
    stage6_search._curated_entries's docstring for why overrides/ranking are
    structurally inert here and filtering is not.
    """

    def test_filters_a_redundant_unresolved_reading(self):
        # A resolved (LSJ-backed) genitive reading, plus an unresolved
        # nominative reading whose gloss exactly duplicates it -- the kind of
        # Morpheus noise filter_parses exists to drop.
        entries = [
            {"parse": "masc gen sg", "lemma": "a", "gloss": "man"},
            {"parse": "masc nom sg", "lemma": "b", "gloss": "man"},
        ]
        lemma_map = {"a": ["a1"]}  # only "a" has LSJ backing
        curated = _curated_entries(entries, lemma_map)
        assert len(curated) == 1
        assert signature(curated) == signature([entries[0]])

    def test_keeps_a_genuinely_distinct_unresolved_reading(self):
        entries = [
            {"parse": "masc gen sg", "lemma": "a", "gloss": "man"},
            {"parse": "masc nom sg", "lemma": "b", "gloss": "totally different"},
        ]
        lemma_map = {"a": ["a1"]}
        curated = _curated_entries(entries, lemma_map)
        assert len(curated) == 2
        assert len(signature(curated)) == 2

    def test_single_entry_is_never_filtered(self):
        entries = [{"parse": "masc gen sg", "lemma": "a", "gloss": ""}]
        assert _curated_entries(entries, {}) == entries


class TestFoldLemma:
    def test_strips_beta_code_diacritics(self):
        assert fold_lemma("a)/nqrwpos") == "anqrwpos"


def _semantic_fixture():
    """Two one-line books, each carrying one token per line, mirroring
    aristotle_pipeline's stage6-grammar test fixture but keyed by Homer's
    `book` field rather than a Bekker `column`."""
    segments = [
        {
            "id": "1",
            "book": 1,
            "lines": [
                {"n": 1, "tokens": [{"t": "alpha", "k": "alpha"}]},
                {"n": 2, "tokens": [{"t": "beta", "k": "beta"}]},
            ],
        },
        {
            "id": "2",
            "book": 2,
            "lines": [
                {"n": 1, "tokens": [{"t": "gamma", "k": "alpha"}]},
                {"n": 2, "tokens": [{"t": "delta", "k": "beta"}]},
            ],
        },
    ]
    key_map = {"alpha": "alpha", "beta": "beta"}
    analyses = {
        "alpha": [{"parse": "masc nom sg", "lemma": "alpha", "gloss": ""}],
        "beta": [{"parse": "fem acc pl", "lemma": "beta", "gloss": ""}],
    }
    sigs = [(), ()]
    for key in ("alpha", "beta"):
        sigs.append(signature(analyses[key]))
    grammar = {
        "token_count": 4,
        "width": 2,
        "categories": ["case", "gender", "number"],
        "reserved": {"unkeyed": 0, "unanalysed": 1},
        "sigs": [
            [
                {category: list(values) for category, values in reading}
                for reading in sig
            ]
            for sig in sigs
        ],
    }
    offsets = {
        "token_count": 4,
        "seg_base_offset": [0, 2],
        "segments": [
            {"book": 1, "column": "1", "line_runs": [[1, 1], [2, 1]]},
            {"book": 2, "column": "2", "line_runs": [[1, 1], [2, 1]]},
        ],
        "book_bounds": [{"book": 1, "start": 0}, {"book": 2, "start": 2}],
        "chapter_bounds": [],
    }
    column = [2, 3, 2, 3]
    return segments, key_map, analyses, grammar, offsets, column


class TestCheckOffsets:
    def test_line_runs_reproduce_a_declared_numbering_gap(self):
        # Il. 9.457 -> 462: a genuine vulgate skip, declared in the manifest.
        segments, *_ = _semantic_fixture()
        segments = [
            {
                "id": "1",
                "book": 1,
                "lines": [
                    {"n": 457, "tokens": _tokens("a")},
                    {"n": 462, "tokens": _tokens("b")},
                ],
            }
        ]
        offsets = {
            "token_count": 2,
            "seg_base_offset": [0],
            "segments": [{"book": 1, "column": "1", "line_runs": [[457, 1], [462, 1]]}],
            "chapter_bounds": [],
        }
        result = check_offsets(
            offsets, segments, [{"book": 1, "after": 457, "next": 462}]
        )
        assert result["ok"], result["problems"]
        assert result["lineation_unexpected"] == []

    def test_rejects_a_renumbered_line_sequence_not_in_the_declared_gaps(self):
        # Same skip, but NOT declared -- a renumbering defect must be caught,
        # not silently accepted as if the enumeration index were the citation.
        segments = [
            {
                "id": "1",
                "book": 1,
                "lines": [
                    {"n": 457, "tokens": _tokens("a")},
                    {"n": 462, "tokens": _tokens("b")},
                ],
            }
        ]
        offsets = {
            "token_count": 2,
            "seg_base_offset": [0],
            "segments": [{"book": 1, "column": "1", "line_runs": [[457, 1], [462, 1]]}],
            "chapter_bounds": [],
        }
        result = check_offsets(offsets, segments, [])
        assert not result["ok"]
        assert result["lineation_unexpected"] == [
            {"book": 1, "after": 457, "next": 462}
        ]
        assert "line_runs" in result["problems"][0]

    def test_a_declared_gap_in_a_different_book_does_not_excuse_this_one(self):
        segments = [
            {
                "id": "1",
                "book": 9,
                "lines": [
                    {"n": 457, "tokens": _tokens("a")},
                    {"n": 462, "tokens": _tokens("b")},
                ],
            }
        ]
        offsets = {
            "token_count": 2,
            "seg_base_offset": [0],
            "segments": [{"book": 9, "column": "9", "line_runs": [[457, 1], [462, 1]]}],
            "chapter_bounds": [],
        }
        result = check_offsets(
            offsets, segments, [{"book": 1, "after": 457, "next": 462}]
        )
        assert not result["ok"]

    def test_line_runs_mismatch_against_stage3_lines_fails(self):
        segments = [
            {
                "id": "1",
                "book": 1,
                "lines": [
                    {"n": 1, "tokens": _tokens("a", "b")},
                    {"n": 2, "tokens": _tokens("c", "d")},
                ],
            }
        ]
        offsets = {
            "token_count": 4,
            "seg_base_offset": [0],
            "segments": [{"book": 1, "column": "1", "line_runs": [[2, 2], [1, 2]]}],
            "chapter_bounds": [],
        }
        result = check_offsets(offsets, segments)
        assert not result["ok"]
        assert "line_runs do not match stage3 lines" in result["problems"][0]

    def test_nonempty_chapter_bounds_is_rejected(self):
        # Homer has no chapter analogue: chapter_bounds must always be [].
        segments = [{"id": "1", "book": 1, "lines": [{"n": 1, "tokens": _tokens("a")}]}]
        offsets = {
            "token_count": 1,
            "seg_base_offset": [0],
            "segments": [{"book": 1, "column": "1", "line_runs": [[1, 1]]}],
            "chapter_bounds": [{"book": 1, "chapter": 1, "start": 0}],
        }
        result = check_offsets(offsets, segments)
        assert not result["ok"]


class TestCheckGrammar:
    def test_column_length_matches_token_count(self):
        segments, key_map, analyses, grammar, offsets, column = _semantic_fixture()
        assert len(column) == offsets["token_count"] == grammar["token_count"]

    def test_accepts_the_true_column(self):
        segments, key_map, analyses, grammar, offsets, column = _semantic_fixture()
        result = check_grammar(
            grammar, column, offsets, segments, key_map, analyses, signature
        )
        assert result["ok"], result["problems"]
        assert result["semantic_offsets_sampled"] == 4

    def test_rejects_transposed_signature_ids(self):
        segments, key_map, analyses, grammar, offsets, column = _semantic_fixture()
        corrupt = [3 if sid == 2 else 2 for sid in column]
        result = check_grammar(
            grammar, corrupt, offsets, segments, key_map, analyses, signature
        )
        assert not result["ok"]
        assert "grammar semantic mismatch" in result["problems"][0]


class TestCheckNgramStreams:
    def test_detects_a_stream_that_drifts_from_the_lexical_index(self):
        greek_form = {"alpha": [[0, 0]]}
        greek_lemma = {"alpha": [[0, 0]]}
        base = [0]
        # The stream disagrees with the index above -- a defect the phrase
        # browser must never ship silently.
        form_stream = ["beta"]
        lemma_stream = [["alpha"]]
        result = check_ngram_streams(
            form_stream, lemma_stream, greek_form, greek_lemma, base, 1
        )
        assert not result["ok"]
        assert "form-stream mismatch" in result["problems"][0]

    def test_agreeing_streams_pass(self):
        greek_form = {"alpha": [[0, 0]]}
        greek_lemma = {"alpha": [[0, 0]]}
        base = [0]
        result = check_ngram_streams(
            ["alpha"], [["alpha"]], greek_form, greek_lemma, base, 1
        )
        assert result["ok"], result["problems"]


def test_merge_search_checks_folds_new_sections_into_an_existing_report():
    report = {"ok": True, "checks": {"columns": {"ok": True}}}
    merge_search_checks(
        report,
        offsets={"ok": True},
        grammar={"ok": False},
        ngram_streams={"ok": True},
    )
    assert set(report["checks"]) == {"columns", "offsets", "grammar", "ngram_streams"}
    assert report["ok"] is False  # one failing section fails the whole report
