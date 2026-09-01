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


def test_every_morphology_override_carries_its_reasoning():
    """The table is an editorial record, not a lookup.

    This used to assert the table's LENGTH, which says nothing about whether
    any entry is right and fails the moment a correct entry is added. What has
    to hold is that each one states a lemma, a gloss and the reason a human
    overrode Morpheus — so the next reader can check the judgement rather than
    trust the count.
    """
    for surface, entry in MORPHOLOGY_OVERRIDES.items():
        assert entry.get("lemma"), surface
        assert entry.get("gloss"), surface
        assert len(entry.get("justification", "")) > 20, surface


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


# ── ghost lemmata ───────────────────────────────────────────────────────────

def test_a_ghost_lemma_is_dropped_when_something_else_reads_the_form():
    # χωόμενος: Morpheus ranks χάω first — Simplicius' sixth-century coinage,
    # LSJ s.v. "coined as etym. of χάος by Simp. in Ph. 620.14" — ahead of
    # χώομαι "to be angry", which is what the form actually is.
    parses = [
        {"lemma": "xa/w", "gloss": "", "parse": "pres part mp", "lsj": ["xa/w"]},
        {"lemma": "xw/omai", "gloss": "to be angry", "parse": "pres part mp",
         "lsj": ["xw/omai"]},
    ]
    assert [p["lemma"] for p in filter_parses(parses)] == ["xw/omai"]


def test_a_ghost_is_kept_rather_than_stranding_the_token():
    # Dropping the only reading leaves the form unresolvable, which is worse
    # than a bad lemma: the reader would get nothing at all for that word.
    only = [{"lemma": "xa/w", "gloss": "", "parse": "pres part act",
             "lsj": ["xa/w"]}]
    assert filter_parses(only) == only


def test_no_shipped_token_is_left_empty():
    """Over the real corpus, not a fixture: every token keeps a reading."""
    import json
    dist = ROOT / "build" / "dist"
    if not (dist / "iliad").is_dir():
        import pytest
        pytest.skip("requires a local build/dist")
    stranded = []
    for work in ("iliad", "odyssey"):
        f = dist / work / "analyses.json"
        if not f.exists():
            continue
        for key, entries in json.loads(f.read_text(encoding="utf-8")).items():
            if not entries:
                stranded.append((work, key))
    assert stranded == [], f"tokens with no reading: {stranded[:5]}"


def test_an_override_promotes_the_real_analysis_rather_than_relabelling_one():
    """χωόμενος is χώομαι's PRESENT participle and Morpheus has that reading;
    it just ranks χάζομαι's future participle first. Relabelling the front
    entry would have published "χώομαι, fut part mp" with no lexicon link — a
    parse the language does not have."""
    parses = [
        {"lemma": "xa/zomai", "gloss": "cause to retire",
         "parse": "fut part mp masc nom sg (epic)", "lsj": [], "cunliffe": []},
        {"lemma": "xw/omai", "gloss": "to be angry",
         "parse": "pres part mp masc nom sg", "lsj": ["xw/omai"], "cunliffe": ["xw/omai"]},
    ]
    out = apply_morphology_override(parses, "xwo/menos")
    assert out[0]["lemma"] == "xw/omai"
    assert out[0]["parse"].startswith("pres part"), "kept its own parse"
    assert out[0]["lsj"] == ["xw/omai"], "kept its lexicon link"
    # the displaced reading is not destroyed, only demoted
    assert any(p["lemma"] == "xa/zomai" for p in out)


def test_an_override_still_repairs_in_place_when_the_lemma_is_absent():
    # The negative particle: Morpheus's gloss comes through as "u" and there is
    # no better candidate to promote.
    parses = [{"lemma": "ou)", "gloss": "u",
               "parse": "proclitic indeclform (adverb)", "lsj": ["ou)"], "cunliffe": []}]
    out = apply_morphology_override(parses, "ou)")
    assert out[0]["gloss"] == "not"
