import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import stage4_morphology as s4


# ── resolve_key: capitalized-source-token lemma resolution ─────────────────
#
# Bug (found by the epithets-stage lane, worked around in apparatus_epithets
# via its own capitalized-only re-resolution): stage4's key resolution tried
# the plain-lowercase Beta Code variant FIRST regardless of whether the
# source token was actually capitalized, so a proper name sharing a Beta Code
# key with a common word (e.g. Τηλέμαχος 'Telemachus' / τηλέμαχος 'fighting
# from afar', both key "thle/maxos") silently mis-lemmatized to the common
# word corpus-wide, even where the source text plainly capitalizes the name.


def test_capitalized_token_prefers_proper_name_analysis_when_both_exist():
    # Diogenes' analyses data has both a plain-lowercase common-word reading
    # and a capitalized ('*'-prefixed) proper-name reading for this key --
    # exactly the Τηλέμαχος/τηλέμαχος homonym pair from the corpus.
    found = {
        "thle/maxos": [
            {
                "lemma_id": 1,
                "form": "thle/maxos",
                "lemma": "thle/maxos",
                "gloss": "fighting from afar",
                "parse": "masc/fem nom sg",
            }
        ],
        "*thle/maxos": [
            {
                "lemma_id": 2,
                "form": "*thle/maxos",
                "lemma": "*thle/maxos",
                "gloss": "",
                "parse": "masc nom sg",
            }
        ],
    }
    # A capitalized source token (the name) must resolve to the proper-name
    # analysis, not the common-word one.
    assert s4.resolve_key("thle/maxos", True, found) == "*thle/maxos"


def test_lowercase_token_still_prefers_lowercase_analysis():
    found = {
        "thle/maxos": [{"lemma_id": 1, "form": "thle/maxos", "lemma": "thle/maxos",
                         "gloss": "fighting from afar", "parse": "masc/fem nom sg"}],
        "*thle/maxos": [{"lemma_id": 2, "form": "*thle/maxos", "lemma": "*thle/maxos",
                          "gloss": "", "parse": "masc nom sg"}],
    }
    # An occurrence never seen capitalized in the source must keep resolving
    # to the common-word reading (current, correct behavior; must not regress).
    assert s4.resolve_key("thle/maxos", False, found) == "thle/maxos"


def test_capitalized_token_falls_back_to_lowercase_when_no_capitalized_analysis():
    # Sentence-initial capitalization is extremely common in verse (every
    # line may start capitalized) and proves nothing about properness on its
    # own -- e.g. a line starting Αὐτὰρ. Diogenes has no '*'-prefixed entry
    # for such ordinary words, so the capitalized token must still fall back
    # to the only analysis that exists.
    found = {
        "au)ta/r": [{"lemma_id": 3, "form": "au)ta/r", "lemma": "au)ta/r",
                     "gloss": "but, however", "parse": "conj"}],
    }
    assert s4.resolve_key("au)ta/r", True, found) == "au)ta/r"


def test_capitalized_token_with_no_analysis_at_all_returns_none():
    assert s4.resolve_key("qzqzqz", True, {}) is None
