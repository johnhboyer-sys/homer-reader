import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline.parse_filter import (
    MORPHOLOGY_OVERRIDES,
    apply_morphology_override,
    filter_parses,
)
from homer_pipeline.stage7_emit import resolve_parses


def test_filter_parses_drops_redundant_unresolved_readings_only():
    resolved = {"lemma": "ἡδονή", "gloss": "pleasure", "lsj": [{"id": "h(donh/"}]}
    duplicate_unresolved = {"lemma": "ἡδονά", "gloss": "pleasure", "lsj": []}
    blank_unresolved = {"lemma": "noise", "gloss": "  ", "lsj": []}
    distinct_unresolved = {"lemma": "πέλω", "gloss": "to be", "lsj": []}

    assert filter_parses(
        [resolved, duplicate_unresolved, blank_unresolved, distinct_unresolved]
    ) == [resolved, distinct_unresolved]


def test_filter_parses_keeps_all_unresolved_tokens_so_it_never_empties():
    parses = [
        {"lemma": "rare", "gloss": "", "lsj": []},
        {"lemma": "name", "gloss": "proper name", "lsj": []},
    ]

    assert filter_parses(parses) == parses


def test_filter_parses_keeps_unresolved_distinct_gloss_with_resolved_sibling():
    resolved = {"lemma": "resolved", "gloss": "carrying", "lsj": [{"id": "ferw"}]}
    distinct = {"lemma": "unresolved", "gloss": "bearing away", "lsj": []}

    assert filter_parses([resolved, distinct]) == [resolved, distinct]


def test_resolve_parses_promotes_homeric_particle_over_spurious_pronoun():
    parses = [
        {
            "lemma": "su/",
            "gloss": "thou",
            "parse": "acc 2nd sg (doric)",
            "lsj": ["su/"],
        },
        {
            "lemma": "te",
            "gloss": "both . . and",
            "parse": "enclitic indeclform (particle)",
            "lsj": ["te1"],
        },
    ]

    primary = resolve_parses(parses, short_defs={})[0]

    assert primary["lemma"] == "te"


def test_resolve_parses_prefers_cunliffe_nominal_over_unbacked_denominal_verb():
    parses = [
        {
            "lemma": "a)ndro/w",
            "gloss": "change into a man",
            "parse": "pres inf act (doric)",
            "lsj": ["a)ndro/w"],
            "cunliffe": [],
        },
        {
            "lemma": "a)nh/r",
            "gloss": "man",
            "parse": "masc gen pl",
            "lsj": ["a)nh/r"],
            "cunliffe": ["a)nh/r"],
        },
    ]

    resolved = resolve_parses(parses, short_defs={}, token_key="a)ndrw=n")

    assert resolved[0]["lemma"] == "a)nh/r"


def test_resolve_parses_applies_curated_surface_override():
    parses = [
        {
            "lemma": "ou)",
            "gloss": "u",
            "parse": "proclitic indeclform (adverb)",
            "lsj": ["ou)"],
            "cunliffe": ["ou)"],
        }
    ]

    resolved = resolve_parses(parses, short_defs={}, token_key="ou)")

    assert resolved[0]["lemma"] == "ou)"
    assert resolved[0]["gloss"] == "not"
    assert len(MORPHOLOGY_OVERRIDES) == 28


def test_morphology_override_can_correct_an_absent_lemma_without_reordering():
    parses = [
        {
            "lemma": "junk",
            "gloss": "particle",
            "parse": "indeclform (particle)",
            "lsj": [],
            "cunliffe": [],
        },
        {
            "lemma": "other",
            "gloss": "other",
            "parse": "indeclform (particle)",
            "lsj": [],
            "cunliffe": [],
        },
    ]
    overrides = {
        "surface": {
            "surface": "surface",
            "lemma": "correct",
            "justification": "The correct lemma is absent from Morpheus.",
        }
    }

    resolved = apply_morphology_override(parses, "surface", overrides)

    assert [parse["lemma"] for parse in resolved] == ["correct", "other"]
    assert parses[0]["lemma"] == "junk"


def test_resolve_parses_is_stable_when_no_rule_fires():
    parses = [
        {
            "lemma": "a",
            "gloss": "first",
            "parse": "masc nom sg",
            "lsj": ["a"],
            "cunliffe": ["a"],
        },
        {
            "lemma": "b",
            "gloss": "second",
            "parse": "masc nom sg",
            "lsj": ["b"],
            "cunliffe": ["b"],
        },
    ]

    resolved = resolve_parses(parses, short_defs={}, token_key="neutral")

    assert [parse["lemma"] for parse in resolved] == ["a", "b"]


def test_resolve_parses_does_not_reorder_debatable_toi_homonym():
    parses = [
        {
            "lemma": "su/",
            "gloss": "thou",
            "parse": "dat 2nd sg (doric)",
            "lsj": ["su/"],
            "cunliffe": ["su/"],
        },
        {
            "lemma": "toi",
            "gloss": "let me tell you",
            "parse": "enclitic indeclform (particle)",
            "lsj": ["toi"],
            "cunliffe": ["toi"],
        },
    ]

    resolved = resolve_parses(parses, short_defs={}, token_key="toi")

    assert [parse["lemma"] for parse in resolved] == ["su/", "toi"]
