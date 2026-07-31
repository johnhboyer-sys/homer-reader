import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import stage5_cunliffe as sc
from homer_pipeline import stage5_lsj as sl
from homer_pipeline import verify_shared_cunliffe as vsc
from homer_pipeline.stage5_lsj import shard_letter


# ── destar_key: undo the TLG capital-diacritic grouping ────────────────────

def test_destar_key_moves_breathing_and_accent_after_the_base_letter():
    # Ἕκτωρ: Morpheus lemma groups the rough breathing + acute before the
    # base letter; Cunliffe's key keeps the ordinary letter-then-diacritic
    # order. Verified against the real corpus (build/dist), not invented.
    assert sc.destar_key("*(/ektwr") == "e(/ktwr"


def test_destar_key_handles_smooth_breathing_only():
    assert sc.destar_key("*)age/lews") == "a)ge/lews"


def test_destar_key_none_for_non_capitalized_lemma():
    assert sc.destar_key("mh=nis") is None


# ── cunliffe_candidates: ranked fallback order ──────────────────────────────

def test_cunliffe_candidates_exact_and_base_before_fold():
    cands = sc.cunliffe_candidates("mh=nis")
    kinds = [k for k, _ in cands]
    assert kinds[0] == "exact"
    assert kinds[1] == "base"
    assert "fold" in kinds


def test_cunliffe_candidates_includes_destarred_forms_for_proper_nouns():
    cands = sc.cunliffe_candidates("*(/ektwr")
    values = [v for _, v in cands]
    assert "e(/ktwr" in values


def test_cunliffe_candidates_ionic_alpha_eta_fallback():
    # Hera: Morpheus's Attic-normalized lemma is *(/hra (ending -a); Cunliffe
    # keys the Ionic/epic headword Ἥρη (ending -h, key h(/rh). The swap is
    # tried on the destarred fold ("h(ra" -> "h(rh"), which is exactly what
    # lets this proper noun resolve (confirmed against the real corpus build:
    # "*(/hra" is NOT in build/stage5/cunliffe_missing_lemmata.json).
    cands = sc.cunliffe_candidates("*(/hra")
    values = [v for k, v in cands if k == "fold"]
    assert "h(rh" in values


def test_ionic_variants_does_not_fire_across_a_diphthong():
    # ἁρμονία's stem before the final -α is -ι- (hiatus, not a real Ionic
    # target here in fold-space terms); the guard must not swap it, so the
    # heuristic stays narrow rather than over-firing on any trailing -a.
    assert sc._ionic_variants("a(rmonia") == []


# ── breathing_swap: the ἴστωρ/ἵστωρ crux (RESEARCH-SHIELD.md §6.2) ──────────
# Morpheus's own lemma for the Il. 18.501 trial-scene word is rough-breathing
# i(/stwr (verified directly against Diogenes' greek-analyses.txt: the entry
# for surface form i)/stori is "{48772810 9 i)/stori,i(/stwr ... masc/fem dat
# sg}"), but both LSJ and Cunliffe key their entry smooth-breathing i)/stwr
# (verified directly against grc.lsj.xml's key="i)/stwr" div2 and
# cunliffe-1-lex.jsonl's "key": "i)/stwr" row, both citing Il. 18.501). No
# existing candidate (exact/base/fold/ws/teos/ionic) strips or flips a
# breathing mark, so this single-word disagreement dropped the entry from
# both lexicon shards before this fallback existed.

def test_breathing_swap_flips_a_lone_rough_breathing():
    assert sl.breathing_swap("i(stwr") == "i)stwr"


def test_breathing_swap_flips_a_lone_smooth_breathing():
    assert sl.breathing_swap("i)stwr") == "i(stwr"


def test_breathing_swap_none_when_no_breathing_present():
    assert sl.breathing_swap("mhnis") is None


def test_breathing_swap_none_for_a_compound_with_two_breathings():
    # A guard against over-firing on a synthetic compound that legitimately
    # carries two marks (a)nti/-bla/ptw-style) — narrow like _ionic_variants.
    assert sl.breathing_swap("a(rma-e(lissw") is None


def test_lemma_candidates_breathing_swap_resolves_the_istor_crux():
    cands = sl.lemma_candidates("i(/stwr")
    values = [v for k, v in cands if k == "fold"]
    assert "i)stwr" in values
    # And it lands on exactly LSJ's real key, folded the same way stage5_lsj
    # folds every div2 key it streams.
    assert sl.fold_key("i)/stwr") in values


def test_cunliffe_candidates_breathing_swap_resolves_the_istor_crux():
    cands = sc.cunliffe_candidates("i(/stwr")
    values = [v for k, v in cands if k == "fold"]
    assert "i)stwr" in values
    assert sl.fold_key("i)/stwr") in values


# ── linkify_definition: citation refs -> internal link markers ─────────────

def test_linkify_definition_wraps_citation_ref_with_work_book_line():
    citations = [
        {"data": {"ref": "Il. 18.271", "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:18.271"}},
    ]
    html = sc.linkify_definition("Cf. Il. 18.271.", citations)
    assert '<a class="cunliffe-cite"' in html
    assert 'data-work="iliad"' in html
    assert 'data-book="18"' in html
    assert 'data-line="271"' in html
    assert ">Il. 18.271</a>" in html
    # trailing period stays outside the link
    assert "</a>." in html


def test_linkify_definition_resolves_odyssey_from_tlg_work_number():
    citations = [
        {"data": {"ref": "Od. 21.91", "urn": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:21.91"}},
    ]
    html = sc.linkify_definition("ἄεθλον ἀάατον Od. 21.91", citations)
    assert 'data-work="odyssey"' in html
    assert 'data-book="21"' in html
    assert 'data-line="91"' in html


def test_linkify_definition_bare_continuation_ref_gets_own_target():
    # "541," carries no "Il."/"Od." prefix in the visible text; the urn alone
    # supplies the work/book/line (real shape from cunliffe-2-hompers.jsonl).
    citations = [
        {"data": {"ref": "Il. 2.536,", "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.536"}},
        {"data": {"ref": "541,", "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.541"}},
    ]
    html = sc.linkify_definition("Il. 2.536, 541, etc.", citations)
    assert 'data-book="2" data-line="536"' in html
    assert 'data-book="2" data-line="541"' in html
    assert ">541</a>" in html


def test_linkify_definition_escapes_plain_text_and_unlinked_refs():
    # A urn this module can't map to iliad/odyssey degrades to plain escaped
    # text rather than a dangling/incorrect link.
    citations = [
        {"data": {"ref": "fr. 1", "urn": "urn:cts:greekLit:tlg0011.tlg004.perseus-grc2:1"}},
    ]
    html = sc.linkify_definition("<script> fr. 1", citations)
    assert "&lt;script&gt;" in html
    assert "<a " not in html
    assert "fr. 1" in html


def test_linkify_definition_ref_not_found_in_text_is_skipped_not_crashed():
    citations = [{"data": {"ref": "NOWHERE", "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1"}}]
    html = sc.linkify_definition("plain text with no such ref", citations)
    assert html == "plain text with no such ref"


# ── shard-letter parity: Python (pipeline) vs TS (shared/lib/data.ts) ──────
# The exact same fixture list is asserted in shared/__tests__/data.test.ts
# against cunliffeShard(); both must agree with front_end_shard here (the
# verify gate) and with stage5_cunliffe.shard_letter (the emitter) — the same
# three-way agreement stage5_lsj/lsjShard/verify_shared_lsj already keep.
SHARD_FIXTURE = [
    ("mh=nis", "m"),
    ("a)ga/qwn", "a"),
    ("*mastori/dhs", "m"),
    ("e(/ktwr", "e"),
    ("*(/ektwr", "e"),
    ("999", "_"),
]


def test_front_end_shard_matches_fixture():
    for key, expected in SHARD_FIXTURE:
        assert vsc.front_end_shard(key) == expected


def test_emitter_shard_letter_agrees_with_front_end_shard_on_real_keys():
    # shard_letter (used to bucket build/stage5/cunliffe/<letter>.json) is
    # reused as-is from stage5_lsj; confirm it agrees with the front-end rule
    # on ordinary (non-'*') Cunliffe keys, which never carry the capital
    # marker (see module docstring — destar_key is the *lemma*-side fix).
    for key, expected in SHARD_FIXTURE:
        if key.startswith("*"):
            continue
        assert shard_letter(key) == expected
