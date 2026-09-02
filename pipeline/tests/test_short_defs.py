import re
import sys
from functools import lru_cache
from pathlib import Path

import pytest
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline.config import Manifest
from homer_pipeline.stage5_lsj import derive_short_def
from homer_pipeline.stage7_emit import merge_short_def, resolve_parses
import homer_pipeline.stage7_emit as stage7_emit


@pytest.mark.parametrize(
    ("key", "body", "expected"),
    [
        (
            "politiko/s",
            "<i>of, for</i>, or <i>relating to citizens</i>, "
            "<foreign>σύλλογος</foreign>",
            "of, for, or relating to citizens",
        ),
        (
            "e)pimele/omai",
            "<i>take</i> <i>care of, have charge</i> or "
            "<i>management of</i>, rare in Poets, as <bibl>Ph. 556</bibl>",
            "take care of, have charge or management of",
        ),
        (
            "a(/ptw",
            "<i>fasten</i> or <i>bind to,</i> used by <author>Hom.</author>",
            "fasten or bind to",
        ),
        (
            "a)/gw",
            "<i>lead, carry, fetch, bring</i>, of living creatures, "
            "<foreign>φέρω</foreign>",
            "lead, carry, fetch, bring",
        ),
    ],
)
def test_derive_short_def_from_leading_italic_run(key, body, expected):
    div2 = etree.fromstring(
        f'<div2 key="{key}"><head>head</head><sense>{body}</sense></div2>'
    )

    assert derive_short_def(div2) == expected


def test_derive_short_def_falls_back_to_entry_body_without_a_sense():
    div2 = etree.fromstring(
        "<div2><head>head</head><i>first</i> and <i>second</i>, used by "
        "<author>Author</author></div2>"
    )

    assert derive_short_def(div2) == "first and second"


@pytest.mark.parametrize(
    "body",
    [
        "<i>of</i> or <i>belonging to a</i> <foreign>δαίμων</foreign>",
        "<i>of</i> or <i>for an</i> <foreign>ἰατρός</foreign>",
        "<i>in, of</i>, or <i>belonging to the</i> <foreign>ἀγορά</foreign>",
    ],
)
def test_derive_short_def_rejects_a_stranded_article(body):
    """The noun the article governs is untranslated Greek outside the run."""
    div2 = etree.fromstring(f"<div2><head>head</head><sense>{body}</sense></div2>")

    assert derive_short_def(div2) == ""


def test_derive_short_def_rejects_an_over_long_clause():
    long_def = "a " + "very long clause, " * 6
    div2 = etree.fromstring(
        f"<div2><head>head</head><sense><i>{long_def}</i> etc.</sense></div2>"
    )

    assert derive_short_def(div2) == ""


def test_merge_short_def_extends_prefix_gloss():
    assert merge_short_def(
        "of, for",
        "politiko/s",
        ["poli_ti^ko/s"],
        {"poli_ti^ko/s": "of, for, or relating to citizens"},
    ) == "of, for, or relating to citizens"


def test_merge_short_def_normalizes_case_whitespace_and_trailing_punctuation():
    assert merge_short_def(
        "  Of,   For... ",
        "politiko/s",
        ["poli_ti^ko/s"],
        {"poli_ti^ko/s": "of, for, or relating to citizens"},
    ) == "of, for, or relating to citizens"


def test_merge_short_def_leaves_complete_gloss_untouched():
    gloss = "lead, carry, fetch, bring"

    assert merge_short_def(
        gloss, "a)/gw", ["a)/gw"], {"a)/gw": "lead, carry, fetch, bring"}
    ) == gloss


def test_merge_short_def_refuses_non_prefix_replacement():
    gloss = "citizen"

    assert merge_short_def(
        gloss,
        "politiko/s",
        ["poli_ti^ko/s"],
        {"poli_ti^ko/s": "of, for, or relating to citizens"},
    ) == gloss


def test_merge_short_def_empty_gloss_adopts_derived_def():
    """Empty Morpheus gloss adopts the lemma's own short def (no prefix test)."""
    assert merge_short_def(
        "", "politiko/s", ["politiko/s"], {"politiko/s": "of, for"}
    ) == "of, for"
    assert merge_short_def(
        " \t", "politiko/s", ["politiko/s"], {"politiko/s": "of, for"}
    ) == "of, for"


def test_merge_short_def_empty_gloss_resolves_cross_reference(monkeypatch):
    """One-hop stub resolution: v. / = Greek referent → that entry's short def."""
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            "du/w2": {"html": '<b class="lsj-head">δύω</b>, v. δύο.'},
            "du/o": {"html": '<b class="lsj-head">δύο</b>', "short": "two"},
            "pera/w2": {
                "html": '<b class="lsj-head">περάω</b> (B), v. πέρνημι.',
            },
            "pe/rnhmi": {
                "html": '<b class="lsj-head">πέρνημι</b>',
                "short": "sell",
            },
            "la/w1": {"html": '<b class="lsj-head">λάω</b> (A), = βλέπω.'},
            "ble/pw": {"html": '<b class="lsj-head">βλέπω</b>', "short": "see"},
            "plou=tos2": {
                "html": (
                    '<b class="lsj-head">πλοῦτος</b>, εος, τό, = πλοῦτος, ὁ'
                ),
            },
            "plou=tos1": {
                "html": '<b class="lsj-head">πλοῦτος</b>',
                "short": "wealth, riches",
            },
        },
    )

    assert merge_short_def("", "du/w2", ["du/w2"], {}) == "two"
    assert merge_short_def("", "pera/w2", ["pera/w2"], {}) == "sell"
    assert merge_short_def("", "la/w1", ["la/w1"], {}) == "see"
    assert merge_short_def("", "plou=tos2", ["plou=tos2"], {}) == "wealth, riches"


def test_merge_short_def_empty_gloss_refuses_stub_whose_referent_lacks_def(
    monkeypatch,
):
    """Referent that is itself definitionless (or another stub) stays empty."""
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            "stub1": {"html": '<b class="lsj-head">foo</b>, v. βάρ.'},
            "ba/r": {"html": '<b class="lsj-head">βάρ</b>, v. βάζ.'},
            "ba/z": {"html": '<b class="lsj-head">βάζ</b>', "short": "baz"},
        },
    )

    assert merge_short_def("", "stub1", ["stub1"], {}) == ""


def test_merge_short_def_empty_gloss_refuses_ambiguous_cross_reference(
    monkeypatch,
):
    """Homonymous referents with different short defs → refuse, leave empty."""
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            "plou=tos2": {
                "html": (
                    '<b class="lsj-head">πλοῦτος</b>, εος, τό, = πλοῦτος, ὁ'
                ),
            },
            "plou=tos1": {
                "html": '<b class="lsj-head">πλοῦτος</b>',
                "short": "wealth",
            },
            "plou=tos3": {
                "html": '<b class="lsj-head">πλοῦτος</b>',
                "short": "riches",
            },
        },
    )

    assert merge_short_def("", "plou=tos2", ["plou=tos2"], {}) == ""


def test_merge_short_def_empty_gloss_refuses_disagreeing_homonym_stubs(
    monkeypatch,
):
    """Two numbered LSJ keys naming different referents → refuse."""
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            "oi)/h1": {"html": '<b class="lsj-head">οἴη</b> (A), = κώμη.'},
            "oi)/h2": {"html": '<b class="lsj-head">οἴη</b> (B), v. ὄα.'},
            "kw/mh": {"html": '<b class="lsj-head">κώμη</b>', "short": "village"},
            "o)/a1": {"html": '<b class="lsj-head">ὄα</b>', "short": "service-tree"},
        },
    )

    assert merge_short_def("", "oi)/h", ["oi)/h1", "oi)/h2"], {}) == ""


def test_merge_short_def_nonempty_gloss_preserves_existing_behavior():
    """Non-empty glosses still only extend on prefix match (regression guard)."""
    assert merge_short_def(
        "of, for",
        "politiko/s",
        ["politiko/s"],
        {"politiko/s": "of, for, or relating to citizens"},
    ) == "of, for, or relating to citizens"
    assert merge_short_def(
        "sink", "du/w2", ["du/w2"], {"du/w": "sink, plunge"}
    ) == "sink"
    assert merge_short_def(
        "of, for",
        "politiko/s",
        ["politiko/s"],
        {"politiko/s": "of, for"},
    ) == "of, for"


def test_merge_short_def_requires_a_word_boundary():
    assert merge_short_def(
        "take", "test", ["test"], {"test": "takeover, assumption"}
    ) == "take"


def test_merge_short_def_prefers_exact_key_when_multiple_candidates_match():
    assert merge_short_def(
        "take",
        "test",
        ["test1", "test"],
        {"test1": "take the first fallback", "test": "take the exact entry"},
    ) == "take the exact entry"


def test_merge_short_def_refuses_ambiguous_fallback_homonyms():
    """Fallback homonyms whose extensions disagree refuse the extension."""
    defs = {
        "a)/naltos1": "not to be filled, insatiate",
        "a)/naltos2": "not salted",
    }

    assert merge_short_def(
        "not", "a)/naltos", ["a)/naltos1", "a)/naltos2"], defs
    ) == "not"
    assert merge_short_def(
        "not", "a)/naltos", ["a)/naltos2", "a)/naltos1"], defs
    ) == "not"


def test_merge_short_def_exact_fallback_means_gloss_is_complete():
    defs = {"ma^lo/s2": "white-tailed", "ma_lo/s1": "white"}

    assert merge_short_def(
        "white", "malo/s", ["ma^lo/s2", "ma_lo/s1"], defs
    ) == "white"
    assert merge_short_def(
        "white", "malo/s", ["ma_lo/s1", "ma^lo/s2"], defs
    ) == "white"


def test_merge_short_def_extends_when_fallback_homonyms_agree():
    """Several fallbacks with the same extension still extend the gloss."""
    defs = {
        "a)/naltos1": "not to be filled, insatiate",
        "a)/naltos2": "not to be filled, insatiate",
    }

    assert merge_short_def(
        "not", "a)/naltos", ["a)/naltos1", "a)/naltos2"], defs
    ) == "not to be filled, insatiate"


def test_resolve_parses_filters_on_morpheus_glosses_before_extending():
    """A spurious LSJ-less reading is recognized by its gloss duplicating a
    resolved sibling's — so the extension has to happen after the filter, or the
    junk reading survives and can become the token's primary analysis."""
    parses = [
        {"lemma": "e)pimele/omai", "gloss": "take", "parse": "aor inf mp",
         "lsj": ["e)pimele/omai"]},
        {"lemma": "e)pimela/omai", "gloss": "take", "parse": "aor inf mp", "lsj": []},
    ]
    short_defs = {"e)pimele/omai": "take care of, have charge or management of"}

    kept = resolve_parses(parses, short_defs)

    assert [p["lemma"] for p in kept] == ["e)pimele/omai"]
    assert kept[0]["gloss"] == "take care of, have charge or management of"


def test_resolve_parses_keeps_a_distinct_unresolved_reading():
    parses = [
        {"lemma": "a", "gloss": "take", "parse": "p", "lsj": ["a"]},
        {"lemma": "b", "gloss": "wholly other", "parse": "p", "lsj": []},
    ]

    kept = resolve_parses(parses, {"a": "take care of"})

    assert [p["gloss"] for p in kept] == ["take care of", "wholly other"]


REAL_DIST_DIR = ROOT / "build" / "dist"


@pytest.mark.skipif(
    not (REAL_DIST_DIR / "lsj").is_dir(),
    reason="requires a local build/dist/lsj (stage5, then stage7)",
)
def test_real_lsj_entries_ship_their_own_short_def():
    """Every shipped LSJ entry carries the short def derived for its own key.

    The reader gives each dictionary-level homonym its own box, headed by its
    own definition (shared/components/LexiconPanel.svelte, toCards). That is
    only possible if the definition travels ON the entry — short_defs.json is
    a build artifact and is never shipped.
    """
    import json

    short_defs = json.loads(
        (ROOT / "build" / "stage5" / "short_defs.json").read_text(encoding="utf-8")
    )
    checked = 0
    for shard in sorted((REAL_DIST_DIR / "lsj").glob("*.json")):
        for key, entry in json.loads(shard.read_text(encoding="utf-8")).items():
            short = entry.get("short")
            if short is not None:
                assert isinstance(short, str) and short.strip(), f"{key}: blank short"
            # build/dist/lsj is the union across BOTH works, while
            # short_defs.json holds only the last work built — so a key absent
            # here is an other-work key, not a missing definition. Check the
            # keys this build did derive.
            expected = short_defs.get(key)
            if expected is None:
                continue
            assert short == expected, f"{key}: short def not shipped"
            checked += 1
    assert checked > 1000, f"only {checked} entries carried a short def"


def test_ambiguous_homonyms_the_guard_refuses_become_separate_reader_boxes():
    """What the guard declines to guess, the reader now shows in full.

    merge_short_def refuses to extend a gloss when two homonyms disagree — it
    cannot tell which is meant. That refusal costs the reader nothing now: the
    same input renders as one box PER homonym, each headed by its own
    definition, so both senses reach the screen without the pipeline picking a
    winner.

    The guard still earns its place, so it stays. The surfaces that have no
    boxes take exactly one gloss per lemma — apparatus_vocab.lemma_gloss_map
    and app/scripts/build-lemmata.mjs — and there a wrong guess would ship
    unchallenged.
    """
    defs = {
        "a)/naltos1": "not to be filled, insatiate",
        "a)/naltos2": "not salted",
    }
    keys = ["a)/naltos1", "a)/naltos2"]

    # The pipeline declines to choose.
    assert merge_short_def("not", "a)/naltos", keys, defs) == "not"

    # The reader's split rule: two or more distinct short defs among the keys
    # means two or more boxes (LexiconPanel toCards).
    distinct = {defs[k] for k in keys if defs.get(k)}
    assert distinct == {"not to be filled, insatiate", "not salted"}


def test_a_lone_homonym_definition_still_extends_and_stays_one_box():
    """One candidate is not ambiguity: the gloss extends, and the reader keeps
    a single box rather than inventing a second from a borrowed definition."""
    defs = {"poth/2": "sample of wine"}
    keys = ["poth/1", "poth/2"]

    assert merge_short_def("sample", "poth/", keys, defs) == "sample of wine"
    assert len({defs[k] for k in keys if defs.get(k)}) == 1


def test_cross_ref_refuses_when_referent_headword_is_split(monkeypatch):
    """ἕ is the LSJ stub "ἕ, v. οὗ", and οὗ is two entries: the adverb ou(=1
    "where" and the pronoun ou(=2, which has no derived short def.

    Counting *definitions found* elects "where" unopposed and would ship an
    adverb of place as the sense of οἱ / οἵ / οὗ / ἕθεν / ἕο — 2,053 top-analysis
    token occurrences across both poems. Counting *entries* refuses, because the
    pronoun homonym never spoke.
    """
    entries = {
        "e(/": {"html": '<b class="lsj-head">ἕ</b>, v. οὗ.'},
        "ou(=1": {
            "html": '<b class="lsj-head">οὗ</b>, gen. of relat. Pron.',
            "short": "where",
        },
        "ou(=2": {"html": '<b class="lsj-head">οὗ</b>, οἷ, ἕ,'},
    }
    monkeypatch.setattr(stage7_emit, "_LSJ_ENTRY_CACHE", entries)
    assert stage7_emit._resolve_cross_ref_target("οὗ", {}) is None

    # The refusal is the split headword, not an unfindable referent: drop the
    # definitionless homonym and the very same pointer resolves.
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {k: v for k, v in entries.items() if k != "ou(=2"},
    )
    assert stage7_emit._resolve_cross_ref_target("οὗ", {}) == "where"

    # Nor is it "more than one entry" on its own — homonyms that agree resolve.
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            **{k: v for k, v in entries.items() if k != "ou(=2"},
            "ou(=2": {"html": '<b class="lsj-head">οὗ</b>', "short": "where"},
        },
    )
    assert stage7_emit._resolve_cross_ref_target("οὗ", {}) == "where"


def test_merge_short_def_keeps_he_blank(monkeypatch):
    """ἕ ships with no definition, and for a stated reason.

    The digit restriction below _empty_gloss_def's own-key pass already skips
    the unnumbered key e(/, so the second stanza uses a numbered key to reach
    the stub path: what refuses there is the homonym guard, which is what must
    keep holding if the digit restriction is ever lifted.
    """
    monkeypatch.setattr(
        stage7_emit,
        "_LSJ_ENTRY_CACHE",
        {
            "e(/": {"html": '<b class="lsj-head">ἕ</b>, v. οὗ.'},
            "e(/1": {"html": '<b class="lsj-head">ἕ</b>, v. οὗ.'},
            "ou(=1": {"html": '<b class="lsj-head">οὗ</b>', "short": "where"},
            "ou(=2": {"html": '<b class="lsj-head">οὗ</b>, οἷ, ἕ,'},
        },
    )

    assert merge_short_def("", "e(/", ["e(/"], {}) == ""
    assert merge_short_def("", "e(/1", ["e(/1"], {}) == ""


# The cases below run on the WHOLE entry, read from the same grc.lsj.xml that
# stage 5 reads. Abridged fixtures are reconstructions, and a reconstruction has
# already hidden a defect in this lane's history (ἄατος, 2026-09-01): a test can
# then pass on text the pipeline never sees. Nothing here is retyped.
_LSJ_KEY_RE = re.compile(r'<div2 [^>]*key="([^"]*)"')


@lru_cache(maxsize=1)
def _real_lsj_entries() -> dict[str, str]:
    """Every div2 fragment this module asserts on, verbatim from grc.lsj.xml.

    The file is not one XML document (no root element) but a stream of div2
    fragments, so it is scanned line-wise exactly as stage5_lsj.run does.
    """
    path = Manifest.for_work("Iliad").diogenes_data() / "grc.lsj.xml"
    if not path.exists():
        return {}
    wanted = set(_REAL_ENTRY_KEYS)
    out: dict[str, str] = {}
    buf: list[str] = []
    key = ""
    want = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "<div2 " in line:
                m = _LSJ_KEY_RE.search(line)
                key = m.group(1) if m else ""
                want = key in wanted and key not in out
                buf = []
            if want:
                buf.append(line)
                if "</div2>" in line:
                    fragment = "".join(buf)
                    start = fragment.index("<div2 ")
                    end = fragment.rindex("</div2>") + len("</div2>")
                    out[key] = fragment[start:end]
                    want = False
                    if len(out) == len(wanted):
                        break
    return out


_REAL_ENTRY_KEYS = (
    "ou)",
    "a)lla/",
    "ki/rkos",
    "me/mona",
    "a)gro/teros",
    "*(eka/ergos",
    "qa/los",
    "ga/r",
    "pa=s1",
    "e)k",
)


def _real_entry(key: str):
    entries = _real_lsj_entries()
    if not entries:
        pytest.skip("grc.lsj.xml not present (manifest sources.diogenes_data)")
    assert key in entries, f"{key} not found in grc.lsj.xml"
    return etree.fromstring(entries[key])


def test_derive_short_def_refuses_italics_governed_by_the_lead_in():
    """οὐ: LSJ italicises words INSIDE its prose, and the run is a fragment.

    "the negative of <i>fact</i> and <i>statement</i>" yielded the short def
    "fact and statement" on 1,456 corpus occurrences — the commonest wrong
    gloss in the dictionary. Morpheus supplies the right one, "not".
    """
    assert derive_short_def(_real_entry("ou)")) == ""


def test_derive_short_def_refuses_a_name_for_a_number():
    """Ἑκάεργος: "Pythag. name for <i>nine</i>" is the same defect as οὐ's.

    The lead-in names a linguistic entity ("name for"), so the italic is what
    is being named, not what the headword means.
    """
    assert derive_short_def(_real_entry("*(eka/ergos")) == ""


def test_derive_short_def_keeps_a_definition_after_a_bare_of():
    """ἀγρότερος: "in <author>Hom.</author> always of <i>wild</i> animals".

    A bare "of" before the run governs the CLASS being described, not the run:
    "wild" is the Homeric gloss and LSJ gives no other. The first version of
    the οὐ rule refused every lead-in ending on of/for/as/to and lost this one
    along with 14 more sound definitions, 61 corpus occurrences between them.
    """
    assert derive_short_def(_real_entry("a)gro/teros")) == "wild"


def test_derive_short_def_still_drops_thalos():
    """θάλος: "= θαλλός, but only nom. and acc. in metaph. sense of <i>scion,
    child</i>" — a real definition, and the rule drops it anyway.

    "sense of" is on the list because περ's "a shortd. form of περί (q. v.) in
    the sense of <i>very much, however much</i>" attributes that sense to περί,
    not to περ, on 534 occurrences. The two shapes are identical and no signal
    in the entry separates them, so this test records the cost rather than
    pretending there is none. Morpheus glosses θάλος "scion, child" — the same
    string — so the card does not change.
    """
    assert derive_short_def(_real_entry("qa/los")) == ""


def test_derive_short_def_keeps_a_run_introduced_by_a_grammatical_label():
    """ἀλλά: a label ("in simple oppositions,") does not govern the run."""
    assert derive_short_def(_real_entry("a)lla/")) == "but"


def test_derive_short_def_absorbs_a_leading_article():
    """κίρκος: "a kind of" belongs to the definition, not to the lead-in."""
    assert derive_short_def(_real_entry("ki/rkos")) == "a kind of hawk or falcon"


def test_derive_short_def_refuses_an_etymological_root():
    """μέμονα: its first <sense> opens inside the etymology parenthesis.

    "(fr. <sense><i>mṇ</i>-), cogn. with μένος" made the Proto-Indo-European
    root the entry's definition, and stage7 propagated it to μεμαώς.
    """
    assert derive_short_def(_real_entry("me/mona")) == ""


@pytest.mark.parametrize(
    ("key", "expected"),
    [("a)lla/", "but"), ("ga/r", "for"), ("pa=s1", "all"), ("e)k", "from out of")],
)
def test_derive_short_def_leaves_the_commonest_entries_alone(key, expected):
    """The regression guard: four of the highest-frequency entries in Homer."""
    assert derive_short_def(_real_entry(key)) == expected
