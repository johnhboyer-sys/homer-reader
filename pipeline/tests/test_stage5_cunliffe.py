import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import stage5_cunliffe as sc
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


# ── Cunliffe as a T8 record ────────────────────────────────────────────────
# Every case below is a real entry, and each one broke a rule that sounded
# right before it was measured.

def test_sense_numbers_are_kept_by_sequence_not_by_lookahead():
    # ἄγαμαι carries a citation line number that reads as a sense ("… Od.
    # 5.41 Ἀ…"), and lookahead rules accept it. It cannot continue the run,
    # so sequence rejects it.
    out = sc.split_senses("x 1 First. 41 Stray. 2 Second. 3 Third.")
    assert [s["n"] for s in out["senses"]] == ["1", "2", "3"]


def test_person_and_number_labels_are_never_senses():
    # 2,651 entries carry these. "1 sing." is morphology, not a division of
    # meaning, and taking it as one silently invents senses.
    out = sc.split_senses("†ἄγαμαι 1 sing. pres. ἄγαμαι Od. 6.168. 2 pl. ἀγάασθε Od. 5.119.")
    assert out["senses"] == []


def test_a_homonym_reference_inside_an_etymology_is_not_a_sense():
    # ἀμβατός reads "[ἀμ-, ἀνα- 1 + βα-, βαίνω.]" — that 1 points at ἀνα-1.
    # A round-trip check cannot catch this: a false 1 still forms a valid run
    # and loses no characters. 185 entries were affected.
    out = sc.split_senses("ἀμβατός -όν [ἀμ-, ἀνα- 1 + βα-, βαίνω.] Capable of being scaled: πόλις Il. 6.434.")
    assert out["senses"] == []


def test_numbering_restarts_under_a_division():
    # ἄγω runs 1-10, then II, then 1-7. A flat rule keeps only the first run.
    out = sc.split_senses("ἄγω 1 One. 2 Two. II In mid. 1 Mid one. 2 Mid two.")
    assert [s["n"] for s in out["senses"]] == ["1", "2", "1", "2"]
    assert [d["n"] for d in out["divisions"]] == ["II"]


def test_the_definition_stops_where_the_evidence_starts():
    z, ex = sc.parse_sense("Wrath, ire : μῆνιν ἄειδε Ἀχιλῆος Il. 1.1. Cf. Il. 1.75.")
    assert z.rstrip(" :") == "Wrath, ire"
    assert ex.startswith("μῆνιν ἄειδε")


def test_a_headword_abbreviation_does_not_end_the_definition():
    # "ἁ." is Cunliffe abbreviating ἅμα INSIDE its own quotation. Reading that
    # period as a sentence end cut 3,179 quotations in half, stranding the
    # front of the quotation in the definition.
    z, ex = sc.parse_sense("At the same time: σκεψάμενος ἐς νῆʼ ἁ. καὶ μεθʼ ἑταίρους Od. 12.247.")
    assert "σκεψάμενος" not in z
    assert ex.startswith("σκεψάμενος")


def test_a_division_banner_takes_its_numeral_out_of_the_running_text():
    # Emitting the numeral without removing it made 63 entries GAIN characters.
    t8 = sc.to_t8("a", "ἅμα", "ἅμα [σα-.] I Adv. 1 With. 2 Together. II Prep. 1 Along with Il. 3.1.")
    banners = [r for r in t8["rows"] if r.get("b")]
    assert [b["n"] for b in banners] == ["I", "II"]
    joined = t8["i"] + "".join((r.get("n") or "") + (r.get("z") or "") + (r.get("ex") or "")
                               for r in t8["rows"])
    assert joined.count("II") == 1


def test_no_row_ever_carries_s():
    # grammata draws a continuation dash on a row with `s` AND an empty
    # numeral. Three quarters of this dictionary is one unnumbered row, and
    # every one of them would sprout a dash it should not have.
    t8 = sc.to_t8("m", "μῆνις", "μῆνις ἡ. 1 Wrath Il. 1.1. 2 Its effect Il. 5.34.")
    assert all("s" not in r for r in t8["rows"])


def test_gr_is_offered_only_when_there_are_divisions_to_tab():
    plain = sc.to_t8("m", "μῆνις", "μῆνις ἡ. 1 Wrath Il. 1.1. 2 Its effect Il. 5.34.")
    assert "gr" not in plain
    divided = sc.to_t8("a", "ἅμα", "ἅμα [σα-.] I Adv. 1 With. 2 Together. II Prep. 1 Along with Il. 3.1.")
    assert [g[0] for g in divided["gr"]] == ["I", "II"]


def test_an_unnumbered_entry_is_one_row():
    t8 = sc.to_t8("x", "ἄλειφαρ", "ἄλειφαρ -ατος, τό [ἀλείφω.] Unguent, oil Il. 18.351.")
    assert len(t8["rows"]) == 1
    assert t8["rows"][0]["n"] == ""


def test_the_whole_lexicon_survives_the_t8_parse(tmp_path):
    """Not a sample: every entry, every character.

    This assertion caught three separate bugs that nothing else could see —
    a regex eating the separator it matched on (all 2,555 split entries lost
    a character), a division banner printing a numeral without removing it
    from the text (63 entries gained one), and the Roman matcher indexing the
    separator rather than the numeral. None of them changed a count; all of
    them changed the text.
    """
    import json
    import re
    src = SOURCES = Path("/Users/johnboyer/Developer/homer-reader/sources/cunliffe/cunliffe-1-lex.jsonl")
    if not src.exists():
        import pytest
        pytest.skip(f"Cunliffe source not present at {src}")
    from collections import Counter
    nows = lambda s: re.sub(r"\s+", "", s)
    # Connectors ("Cf.", ",", ":", "=") carry nothing a T8 row keeps — it joins
    # citations with its own separator — and the brackets around a parenthetical
    # go when its text is lifted into `e`. Those are the ONLY characters this
    # parse is allowed to drop, and the assertion names them rather than
    # stripping both sides, which would blind it to what it is auditing.
    allowed = set(",.:;=()") | set("Cfcand")   # "Cf." and lowercase "cf."
    lossy = []
    rows = 0
    for line in src.open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        t8 = sc.to_t8(r["key"], r["headword"], r["definition"])
        rows += len(t8["rows"])
        parts = [t8["head"], t8["i"]]
        for x in t8["rows"]:
            parts += [x.get("n") or "", x.get("z") or ""]
            for item in x.get("ex") or []:
                parts += [item.get("g") or "", item.get("e") or "", item.get("c") or ""]
            parts += list(x.get("au") or [])
        dropped = Counter(nows(r["definition"])) - Counter(nows("".join(parts)))
        added = Counter(nows("".join(parts))) - Counter(nows(r["definition"]))
        assert not added, f"{r['headword']} gained {list(added)}"
        real = [ch for ch in dropped if ch not in allowed]
        if real:
            lossy.append((r["headword"], real))
    assert lossy == [], f"{len(lossy)} entries lost content: {lossy[:5]}"
    assert rows > 20000, rows


def test_a_quotation_becomes_an_example_and_a_bare_citation_an_author():
    t8 = sc.to_t8("m", "μῆνις",
                  "μῆνις ἡ. 1 Wrath, ire : μῆνιν ἄειδε Ἀχιλῆος Il. 1.1. Cf. Il. 1.75, Il. 5.178.")
    row = t8["rows"][0]
    assert row["ex"] == [{"g": "μῆνιν ἄειδε Ἀχιλῆος", "c": "Il. 1.1"}]
    assert row["au"] == ["Il. 1.75", "Il. 5.178"]


def test_a_parenthetical_translation_becomes_the_example_gloss():
    t8 = sc.to_t8("a", "ἀναιδής",
                  "ἀναιδής 1 Shameless: ἀναιδέα δηϊοτῆτος (app., shamelessly insatiate) Il. 5.593.")
    assert t8["rows"][0]["ex"] == [
        {"g": "ἀναιδέα δηϊοτῆτος", "c": "Il. 5.593", "e": "app., shamelessly insatiate"}
    ]


def test_prose_between_citations_is_never_dropped():
    # ἀγακλεής puts its DEFINITION after its principal parts, so it lands in the
    # evidence run rather than in `z`. An earlier version discarded any evidence
    # text with no Greek in it, and this entry lost "Very famous, glorious,
    # splendid, worthy" outright — 2,534 entries (25.8%) lost content that way.
    t8 = sc.to_t8("a", "ἀγακλεής",
                  "ἀγακλεής -ές Genit. ἀγακλῆος Il. 16.738. Very famous, glorious Il. 17.716.")
    assert any("Very famous, glorious" in (r.get("z") or "") for r in t8["rows"])


def test_prose_between_citations_keeps_the_citations_that_follow_it():
    t8 = sc.to_t8("a", "ἀναιδής",
                  "ἀναιδής 1 Shameless Od. 1.254. Absol. Il. 1.158.")
    tail = t8["rows"][-1]
    assert tail["z"] == "Absol."
    assert tail["au"] == ["Il. 1.158"]
    assert tail["n"] == ""      # a continuation carries no number of its own
    assert "s" not in tail      # and never `s`, which would draw a dash


def test_an_unnumbered_entrys_morphology_is_not_read_as_a_quotation():
    # αἴγειρος came out with z="-" and "ου, ἡ. The poplar" inside `g`, reading
    # as though Homer had written it — the definition in the wrong field, and
    # the endings split in half. 151 entries did this.
    t8 = sc.to_t8("a", "αἴγειρος", "αἴγειρος -ου, ἡ. The poplar Il. 4.482: Od. 5.64.")
    assert t8["i"] == "-ου, ἡ."
    row = t8["rows"][0]
    assert row["z"] == "The poplar"
    assert all("poplar" not in e.get("g", "") for e in row.get("ex", []))


def test_an_etymology_bracket_stays_out_of_the_quotation():
    t8 = sc.to_t8("a", "ἄλειφαρ", "ἄλειφαρ -ατος, τό [ἀλείφω.] Unguent, oil Il. 18.351.")
    assert "[ἀλείφω.]" in t8["i"]
    assert t8["rows"][0]["z"] == "Unguent, oil"


def test_a_note_joins_the_citation_list_not_the_definition():
    # "etc." qualifies the citations above it. Given a row to itself it produced
    # sense rows whose whole definition read "etc." (839 of them); appended to
    # the definition instead it produced "With, along with, in company with
    # etc. etc.". It belongs in `au`, which renders as "Il. 1.424 · etc.".
    t8 = sc.to_t8("a", "ἅμα", "ἅμα 1 With Il. 1.424. etc.: κήρυχʼ ἁ. ὀπάσσας Od. 9.90.")
    assert len(t8["rows"]) == 1
    row = t8["rows"][0]
    assert row["z"] == "With"
    assert "etc." in row["au"]
