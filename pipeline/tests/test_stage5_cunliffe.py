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
    # z, i and an example's g carry markup now (grammata runs them through
    # wrapGreekInHtml, not escapeHtml, which is what lets the cross-references
    # survive into the records). Compare the TEXT, and check the tags separately
    # rather than letting them count as content.
    def plain(v):
        v = re.sub(r"<[^>]*>", "", v)
        return (v.replace("&amp;", "&").replace("&lt;", "<")
                 .replace("&gt;", ">").replace("&quot;", '"').replace("&#x27;", "'"))
    nows = lambda s: re.sub(r"\s+", "", plain(s))
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
        # the forms block and the entry-level citations it pulled out of the
        # head run
        for lab, form in t8.get("f") or []:
            parts += [lab, form]
        parts += list(t8.get("au") or [])
        for x in t8["rows"]:
            parts += [x.get("n") or "", x.get("z") or ""]
            for item in x.get("ex") or []:
                parts += [item.get("g") or "", item.get("e") or "", item.get("c") or ""]
            parts += list(x.get("au") or [])
        dropped = Counter(nows(r["definition"])) - Counter(nows("".join(parts)))
        added = Counter(nows("".join(parts))) - Counter(nows(r["definition"]))
        # Gains are allowed ONLY where a continuation reference has had its book
        # restored — "496" becoming "Il. 1.496" — so the permitted characters
        # are exactly a work abbreviation, digits and a dot. Anything else means
        # the parse invented text.
        restorable = set("IlOd.0123456789")
        invented = [ch for ch in added if ch not in restorable]
        assert not invented, f"{r['headword']} invented {invented}"
        # every anchor this parse inserts must be closed
        for field in [t8["i"]] + [x.get("z") or "" for x in t8["rows"]] + [
                e.get("g") or "" for x in t8["rows"] for e in (x.get("ex") or [])]:
            assert field.count("<a ") == field.count("</a>"), r["headword"]
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


def test_a_continuation_reference_keeps_its_book():
    # "Il. 1.83, 496, 533" means Il. 1.83, Il. 1.496, Il. 1.533. Cunliffe drops
    # the book because the previous reference established it — which reads
    # correctly in prose and not at all once the references are a separated
    # list, where "496 · 533" has nothing to attach to (John, on seeing it).
    segs = sc.split_evidence("ἑός Il. 1.83, 496, 533, Il. 2.662 : Od. 1.216, 218.")
    assert segs[0]["au"] == ["Il. 1.496", "Il. 1.533", "Il. 2.662",
                             "Od. 1.216", "Od. 1.218"]


def test_a_full_reference_resets_the_book_across_the_poems():
    segs = sc.split_evidence("ἑός Il. 1.10, 20 : Od. 5.30, 40.")
    au = [c for seg in segs for c in seg["au"]]
    assert "Il. 1.20" in au
    assert "Od. 5.40" in au
    # the book must not leak across the colon that separates the poems
    assert "Il. 5.40" not in au


def test_a_bare_reference_pointer_joins_the_citation_list_not_the_definition():
    # ἅμα: "– Other combinations in Il. 1.417, Il. 2.281, …" names no sense
    # of its own — the citations ARE what "in" points at. Given a row of its
    # own it read as though Cunliffe defined ἅμα as "Other combinations in"
    # (John, on seeing it). It joins the list above instead, dash and all.
    t8 = sc.to_t8("a", "ἅμα",
                  "ἅμα 1 With Il. 1.424. – Other combinations in Il. 1.417, Il. 2.281.")
    assert len(t8["rows"]) == 1
    row = t8["rows"][0]
    assert row["z"] == "With"
    assert "– Other combinations in" in row["au"]


def test_a_leading_reference_pointer_does_not_become_the_definition():
    """ἄατος, on its REAL source text rather than a reconstruction.

    parse_sense draws the sense/evidence boundary at the first citation, and
    here there is nothing before it, so the pointer "Except in" became the
    whole definition of a row of its own. It carries no sense; it joins the
    citation list instead. This is the only entry in the corpus the rule
    reaches (1 of 11,416).

    Use the real string. A simplified version drops the etymology bracket,
    which changes what `i` absorbs and what the first row holds — a shortened
    fixture here would pass while the shipped entry did something else.

    The row that survives used to read "in contr. form", because ἄατος's
    actual gloss ("Insatiate of, indefatigable in") sat inside a Greek
    EXAMPLE, as though Homer wrote it. That was a separate defect and is
    fixed separately, in split_evidence — see
    test_a_gloss_behind_a_form_does_not_become_a_quotation. This test still
    asserts only what pointer folding owns.
    """
    real = ("ἄατος [ἀ-1 + (σ)άω.] Except in Il. 22.218 in contr. form ἆτος. "
            "Insatiate of, indefatigable in. With genit.: πολέμοιο Il. 5.388. "
            "Cf. Il. 5.863, Il. 6.203")
    t8 = sc.to_t8("a)/atos", "ἄατος", real)
    assert not any((r.get("z") or "").strip() == "Except in" for r in t8["rows"])
    au = [a for r in t8["rows"] for a in (r.get("au") or [])]
    assert "Except in" in au, "the pointer is kept, never dropped"
    assert au.index("Except in") < au.index("Il. 22.218")


def test_a_sub_sense_letter_becomes_a_row_not_part_of_the_definition():
    # "1 His a ἑός Il. 1.83 …" is sense 1 "His" with a sub-sense a. Left in the
    # text it read "His a".
    t8 = sc.to_t8("e", "ἑός", "ἑός 1 His a ἑός Il. 1.83, 496. – b ὅς Il. 1.609.")
    assert not any("His a" in (r.get("z") or "") for r in t8["rows"])
    subs = [r for r in t8["rows"] if r.get("n") in ("a", "b")]
    assert [r["n"] for r in subs] == ["a", "b"]
    assert all(r["lv"] == 2 for r in subs)


# ── Cunliffe's English never belongs inside a quotation ─────────────────────


def test_a_gloss_behind_a_form_does_not_become_a_quotation():
    """ἄατος, on its REAL source text.

    split_evidence cut the lead at the FIRST Greek word, so the form
    "ἆτος." carried the gloss behind it into `g`: the entry defined the
    word as "in contr. form" and rendered "Insatiate of, indefatigable in"
    as though Homer had written it. That is the one thing a reader came to
    ἄατος for.

    The real string, not a shortened one: a reconstruction that drops the
    etymology bracket changes what `i` absorbs and what the first row holds,
    and would pass here while the shipped entry did something else.
    """
    real = (
        "ἄατος [ἀ-1 + (σ)άω.] Except in Il. 22.218 in contr. form ἆτος. "
        "Insatiate of, indefatigable in. With genit.: πολέμοιο Il. 5.388. "
        "Cf. Il. 5.863, Il. 6.203, Il. 11.430, Il. 13.746, Il. 22.218: Od. "
        "13.293."
    )
    t8 = sc.to_t8("a)/atos", "ἄατος", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert quoted == ["πολέμοιο"]
    assert any("Insatiate of, indefatigable in" in (r.get("z") or "")
               for r in t8["rows"])


def test_a_definition_between_a_lemma_and_its_quotation_stays_a_definition():
    # θηρευτής, whole and real. "With κύων, a hunting dog: ἐν κυσὶ
    # θηρευτῇσιν" names the word Cunliffe is pairing with and then quotes.
    # The lemma is Greek, so the cut at the first Greek left "a hunting dog"
    # inside the quotation and "With" alone as the definition.
    real = (
        "θηρευτής ὁ [θηρεύω.] A hunter Il. 12.41. With κύων, a hunting dog: "
        "ἐν κυσὶ θηρευτῇσιν Il. 11.325."
    )
    t8 = sc.to_t8("qhreuth/s", "θηρευτής", real)
    row = t8["rows"][-1]
    assert row["z"] == "With κύων, a hunting dog"
    assert [it["g"] for it in row["ex"]] == ["ἐν κυσὶ θηρευτῇσιν"]


def test_an_adverbial_gloss_is_not_read_as_homers_words():
    # ὑπέρβιος, whole and real: the neuter-as-adverb note opens with the
    # form itself, and its gloss ("in overweening wise, wantonly,
    # recklessly") was reading as part of the quotation after it.
    real = (
        "ὑπέρβιος -ον [ὑπερ- 6 + βίη.] 1 Headlong, headstrong, not to be "
        "restrained or turned aside Il. 18.262 : Od. 15.212. 2 Overweening, "
        "arrogant, wanton : ὕβριν Od. 1.368=Od. 4.321, Od. 16.410. In neut. "
        "ὑπέρβιον as adv., in overweening wise, wantonly, recklessly : βοῦς "
        "μευ ἔκτειναν ὑ. Od. 12.379. Cf. Il. 17.19 : Od. 14.92, 95, Od. "
        "16.315."
    )
    t8 = sc.to_t8("u(pe/rbios", "ὑπέρβιος", real)
    row = t8["rows"][-1]
    assert row["z"] == ("In neut. ὑπέρβιον as adv., in overweening wise, "
                        "wantonly, recklessly")
    assert [it["g"] for it in row["ex"]] == ["βοῦς μευ ἔκτειναν ὑ."]


def test_a_compound_list_cut_off_by_a_citation_is_not_a_quotation():
    """βράχω, whole and real.

    The citation before it ends inside Cunliffe's list of compounds, so the
    run "(ἀνα-) Of armour, to rattle, clash, ring" opens with Greek and
    closes a parenthesis it never opened. Read as a quotation it put the
    whole first definition of the verb into Homer's mouth.
    """
    real = (
        "†βράχω 3 sing. aor. ἔβραχε, βράχε. (ἀνα-) Of armour, to rattle, "
        "clash, ring Il. 4.420, Il. 12.396, Il. 13.181, Il. 14.420, Il. "
        "16.566. Of an axle, to creak, grate Il. 5.838. So of a door Od. "
        "21.49. Of a river, to resound under the splash of something "
        "falling into it Il. 21.9. Of the earth, to give forth a sound, "
        "resound Il. 21.387. Of persons, to roar, shriek Il. 5.859, 863, "
        "Il. 16.468."
    )
    t8 = sc.to_t8("bra/xw", "†βράχω", real)
    assert not any(r.get("ex") for r in t8["rows"]), \
        "no part of this entry is a quotation"
    assert any((r.get("z") or "").startswith("(ἀνα-) Of armour")
               for r in t8["rows"])


def test_a_stop_the_prose_has_already_crossed_does_not_hold_the_quotation():
    # πάννυχος, whole and real. Cunliffe writes " : " with a space on
    # each side, so the sentence stop and the colon are two stops in a row
    # with nothing between them; requiring English behind EVERY stop left
    # the colon itself at the head of the quotation.
    real = (
        "πάννυχος [as παννύχιος.] =παννύχιος. Il. 11.551=Il. 17.660, Il. "
        "23.218 : Od. 14.458, Od. 20.53. In neut. sing. πάννυχον as adv. : "
        "τί π. ἀωτεῖς; Il. 10.159."
    )
    t8 = sc.to_t8("pa/nnuxos", "πάννυχος", real)
    row = t8["rows"][-1]
    assert row["z"] == "In neut. sing. πάννυχον as adv."
    assert [it["g"] for it in row["ex"]] == ["τί π. ἀωτεῖς;"]


def test_an_unmatched_bracket_without_english_leaves_the_quotation_alone():
    """τεκμαίρομαι, whole and real: the mirror image, and a guard.

    A citation falls inside the bracket Cunliffe supplies the subject in, so
    "[Κρονίδης] τεκμαίρεται ἀμφοτέροισιν" reaches split_evidence with the
    "[" already gone. An unmatched delimiter alone must NOT condemn a run:
    this is Homer, and the first draft of that rule moved 39 quotations like
    it into the definition.
    """
    real = (
        "τεκμαίρομαι [τέκμαρ = τέκμωρ.] 3 sing. aor. τεκμήρατο Od. 10.563. "
        "3 pl. τεκμήραντο Il. 6.349, 1 To ordain, appoint, decree : τάδε "
        "κακά Il. 6.349, [Κρονίδης] τεκμαίρεται ἀμφοτέροισιν, εἰς ὅ κεν ἢ . "
        ". . ἢ . . . (app., settles an appointed time against which either "
        ". . . or . . .) Il. 7.70. Cf. Od. 7.317, Od. 10.563. 2 To foretell "
        ": ὄλεθρον Od. 11.112 = Od. 12.139."
    )
    t8 = sc.to_t8("tekmai/romai", "τεκμαίρομαι", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert "Κρονίδης] τεκμαίρεται ἀμφοτέροισιν, εἰς ὅ κεν ἢ . . . ἢ . . ." in quoted


def test_a_parenthesised_translation_does_not_cut_its_own_quotation():
    """δίκη, whole and real: the other guard.

    "οὐ δίκας εἰδότα οὐδὲ θέμιστας (having no regard for justice
    . . .)" is a quotation carrying its own translation. English inside the
    parenthesis is that translation, never Cunliffe's prose resuming, so it
    cannot be grounds for cutting the quotation it belongs to.
    """
    real = (
        "δίκη -ης, ἡ. 1 Custom, usage, way: βασιλήων Od. 4.691. Cf. Od. "
        "18.275, Od. 19.43. With notion of privilege: γερόντων Od. 24.255. "
        "Applied to a mode of existence or action imposed from without: "
        "δμώων Od. 14.59. Cf. Od. 11.218. Something that always happens in "
        "specified circumstances Od. 19.168. 2 Right, justice Il. 16.388, "
        "Il. 19.180: Od. 14.84. In pl., rules of right, principles of "
        "justice: οὐ δίκας εἰδότα οὐδὲ θέμιστας (having no regard for "
        "justice or the usages of (civilized) men; see εἴδω III.12) Od. "
        "9.215. Cf. Od. 3.244. 3 A judgement or doom: ὃς λυκίην εἴρυτο "
        "δίκῃσιν (by his (impartial) administration of justice) Il. 16.542. "
        "Cf. Il. 18.508. 4 A plea of right, a claim: δίκας εἴροντο (were "
        "asking questions about their . . ., seeking decisions in regard to "
        "them) Od. 11.570. Cf. Il. 23.542."
    )
    t8 = sc.to_t8("di/kh", "δίκη", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert any(g.startswith("οὐ δίκας εἰδότα οὐδὲ θέμιστας") for g in quoted)


# ── a parenthesis Cunliffe opens is a parenthesis he closes ────────────────
# `z` and an example's `g` carry markup (grammata runs them through
# wrapGreekInHtml), so a full reference inside them arrives as an anchor.
# These tests are about where the TEXT lands, so they read it without tags.
def _text(v: str) -> str:
    import re as _re
    v = _re.sub(r"<[^>]*>", "", v)
    return (v.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"').replace("&#x27;", "'"))


def test_a_parenthetical_remark_is_not_cut_by_the_citations_inside_it():
    """ἁμός, whole and real: the entry this pass was opened on.

    Cunliffe closes the entry with a remark of his own — "(But the sense my
    (cf. ἡμέτερος 2) is always admissible, and in Il. 6.414, and perh. in Il.
    8.178, is preferable.)". Every citation in it used to end a run, so the
    remark reached the reader as four separate rows, each of them presented as
    a definition of ἁμός: "(But the sense my (cf.", ") is always admissible,
    and in", "perh. in", "is preferable.)". A citation inside one of his
    parentheses is part of the remark, not evidence standing on its own.
    """
    real = (
        "ἁμός -ή, -όν. Our ( = ἡμέτερος) Il. 6.414, Il. 8.178, Il. 10.448, "
        "Il. 13.96, Il. 16.830: Od. 11.166 = 481. (But the sense my (cf. "
        "ἡμέτερος 2) is always admissible, and in Il. 6.414, and perh. in "
        "Il. 8.178, is preferable.)"
    )
    t8 = sc.to_t8("a(mo/s", "ἁμός", real)
    prose = [_text(r["z"]) for r in t8["rows"] if r.get("z")]
    assert (
        "(But the sense my (cf. ἡμέτερος 2) is always admissible, and in "
        "Il. 6.414, and perh. in Il. 8.178, is preferable.)"
    ) in prose


def test_a_word_named_inside_a_parenthesis_is_not_homers_words():
    """ἁμός again: the other half of the same entry.

    "Our ( = ἡμέτερος)" is Cunliffe naming the word he is glossing ἁμός by.
    Cutting at the first Greek put ἡμέτερος in an example — Homer credited
    with "ἡμέτερος)" at Il. 6.414 — and left "Our ( =" standing as the whole
    definition of the word.
    """
    real = (
        "ἁμός -ή, -όν. Our ( = ἡμέτερος) Il. 6.414, Il. 8.178, Il. 10.448, "
        "Il. 13.96, Il. 16.830: Od. 11.166 = 481. (But the sense my (cf. "
        "ἡμέτερος 2) is always admissible, and in Il. 6.414, and perh. in "
        "Il. 8.178, is preferable.)"
    )
    t8 = sc.to_t8("a(mo/s", "ἁμός", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert quoted == []
    assert "Our ( = ἡμέτερος)" in [
        _text(r["z"]) for r in t8["rows"] if r.get("z")
    ]


def test_a_cross_reference_parenthesis_is_not_homers_words():
    """ἀερσίπους, whole and real: _paren_holds_cite's own case.

    "Applied to ἵπποι in sense chariot (see ἵππος 3) Il. 18.532" is one
    statement of Cunliffe's, and the sense-number 3 is not a line of Homer.
    Reading it as a citation used to end the run at "(see ἵππος", so the
    reader was shown a quotation running "Applied to ἵπποι in sense chariot
    (see ἵππος" — his prose in Homer's mouth — and a bare ")" on the row
    below. This is the shape _unbalanced used to catch by accident, before
    the parenthesis was kept whole.
    """
    real = (
        "ἀερσίπους -ποδος [ἀερ-, ἀείρω + -σι- + πούς.] Lifting the feet, "
        "high-stepping. Epithet of horses: Il. 3.327, Il. 23.475. Applied "
        "to ἵπποι in sense chariot (see ἵππος 3) Il. 18.532."
    )
    t8 = sc.to_t8("a)ersi/pous", "ἀερσίπους", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert quoted == []
    assert "Applied to ἵπποι in sense chariot (see ἵππος 3)" in [
        r["z"] for r in t8["rows"] if r.get("z")
    ]


def test_a_nested_parenthesis_reaches_the_reader_whole():
    """Ἴασος-2, whole and real: a parenthesis inside a parenthesis.

    "(Argos-1 (3))" is one cross-reference, and both its numbers used to be
    read as lines of Homer: the entry came out as three rows — "…all southern
    Greece (Argos-", then "(", then "))" — none of which says anything. The
    depth walk has to count nesting, not merely notice a parenthesis.
    """
    real = (
        "Ἴασος-2 (ῑ). Ἴασον Ἄργος, of doubtful origin, apparently denoting "
        "all southern Greece (Argos-1 (3)) Od. 18.246."
    )
    t8 = sc.to_t8("i)/asos", "Ἴασος-2", real)
    prose = [_text(r["z"]) for r in t8["rows"] if r.get("z")]
    assert prose == [
        "Ἴασον Ἄργος, of doubtful origin, apparently denoting all southern "
        "Greece (Argos-1 (3))"
    ]


def test_an_etymology_bracket_still_holds_cunliffes_prose_out_of_homers_mouth():
    """πολεμιστής, whole and real: _unbalanced's first remaining shape.

    The depth walk in split_evidence counts PARENTHESES only, so the
    etymology bracket is untouched by it: "πολεμίζω.] A fighter, warrior"
    still arrives with its "[" gone, and only _unbalanced can tell that this
    is the tail of Cunliffe's etymology rather than a line of the poem.
    A characterization test — it passes before the parenthesis fix as well as
    after, which is the point: the fix must not have taken this signal away.
    """
    real = (
        "πολεμιστής ὁ. πτολεμιστής Il. 22.132. [πολεμίζω.] A fighter, "
        "warrior Il. 5.289= Il. 20.78= Il. 22.267, Il. 5.571, 602= Il. "
        "16.493= Il. 22.269, Il. 10.549, Il. 13.300, Il. 15.585, Il. 17.26, "
        "Il. 21.589, Il. 22.132 : Od. 24.499. With implied notion of "
        "stoutness : πολεμιστὰ μετʼ ἀνδράσιν Il. 16.492."
    )
    t8 = sc.to_t8("polemisth/s", "πολεμιστής", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert any("A fighter, warrior" in _text(r.get("z") or "") for r in t8["rows"])
    assert not any("A fighter" in _text(g) for g in quoted)


def test_a_parenthesis_opened_before_the_evidence_still_holds_cunliffes_prose():
    """ὀκτωκαιδέκατος, whole and real: _unbalanced's second remaining shape.

    parse_sense cuts the sense at its first citation, so the "(" of "(sc.
    ἡμέρῃ)" stands in the definition and never enters the string
    split_evidence measures depth over. What reaches the guard is
    "ἡμέρῃ), on the eighteenth day" — a stray close with no opener in sight.
    The depth map cannot see the opener; _unbalanced can see the orphan.
    Characterization, like the bracket above: it must still hold after the
    parenthesis fix.
    """
    real = (
        "ὀκτωκαιδέκατος -η, -ον [ὀκτώ + καί + δέκατος.] The eighteenth : "
        "ὀκτωκαιδεκάτῃ (sc. ἡμέρῃ), on the eighteenth day Od. 5.279 = "
        "Od. 7.268, Od. 24.65."
    )
    t8 = sc.to_t8("o)ktwkaide/katos", "ὀκτωκαιδέκατος", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert not any("on the eighteenth day" in _text(g) for g in quoted)
    assert any("on the eighteenth day" in _text(r.get("z") or "")
               for r in t8["rows"])


def test_a_quotation_inside_a_parenthesis_is_still_homers_words():
    """ἐπισσείω, whole and real: the guard on all of the above.

    "τῇ (sc. αἰγίδι) ἐπισσείων φοβέειν Ἀχαιούς" is Homer, with Cunliffe's
    supplement parenthesised inside it. Nothing in this pass may move it into
    the definition: the parenthesis here closes where it opened and carries no
    citation, so neither the depth walk nor _paren_holds_cite touches it.
    """
    real = (
        "ἐπισσείω [ἐπι- 5.] 1 To shake something (threateningly) at a "
        "person: τῇ (sc. αἰγίδι) ἐπισσείων φοβέειν Ἀχαιούς Il. 15.230 (τῇ "
        "with φοβέειν). 2 To shake (thus) at. With dat.: αἰγίδα πᾶσιν "
        "Il. 4.167."
    )
    t8 = sc.to_t8("e)pissei/w", "ἐπισσείω", real)
    quoted = [it["g"] for r in t8["rows"] for it in (r.get("ex") or [])]
    assert any("ἐπισσείων φοβέειν Ἀχαιούς" in _text(g) for g in quoted)


# ── Cunliffe's own sense numbers are not line numbers ──────────────────────
# He cross-references his senses constantly — "As in 4.b", "Sim. in 3 pl.",
# "See also under ἵημι1 9" — and every one of those digits used to be read as
# a bare continuation and restored to the book the previous reference had
# established. The reader got a live link to a real line with nothing to do
# with the entry. See _is_sense_ref and _holds_sense_ref.
#
# Every fixture below is a whole real source entry, copied from
# sources/cunliffe/cunliffe-1-lex.jsonl and wrapped, never reconstructed: a
# shortened one is exactly what let the last defect in this module hide.


def _cites(t8: dict) -> list[str]:
    """Every reference the entry hands the reader as a link."""
    out = []
    for r in t8["rows"]:
        out += list(r.get("au") or [])
        out += [it["c"] for it in (r.get("ex") or []) if it.get("c")]
    return out


def _all_text(t8: dict) -> str:
    parts = [_text(t8.get("i") or "")]
    for r in t8["rows"]:
        parts.append(_text(r.get("z") or ""))
        for it in (r.get("ex") or []):
            parts.append(_text(it.get("g") or ""))
    return " | ".join(parts)


def test_a_sub_sense_pointer_is_not_a_line_number():
    """ἄγω, whole and real: the entry this defect was reported on.

    Sense II.5 reads "a As in 4.a : ... b As in 4.b : ἄξομαι ἀμφοτέροις
    ἀλόχους Od. 21.214. Cf. Od. 4.10." The 4 of "As in 4.b" points at sense
    II.4, and it was emitted as Od. 15.4 — the book the reference before it
    left behind. The pointer is content: it must stay in the row, whole and
    readable, and it must not be a citation.
    """
    real = (
        "ἄγω Fut. ἄξω, -εις Il. 1.139, Il. 3.401, Il. 4.239, Il. 8.166, Il. "
        "9.429, 692, Il. 24.154, 183: Od. 2.326, Od. 10.268, Od. 16.272, "
        "Od. 17.22, 250. Acc. sing. masc. pple. ἄξοντα Il. 8.368: Od. "
        "11.623. Infin. ἀξέμεναι Od. 23.221. ἀξέμεν Il. 23.668. ἄξειν Il. "
        "16.832, Il. 19.298: Od. 13.212. Aor. ἤγαγον, -ες Il. 4.179, Il. "
        "5.731, Il. 6.426, Il. 11.480, 663, Il. 24.547, etc.: Od. 1.172, "
        "Od. 3.383, Od. 4.258, Od. 7.9, 248, Od. 9.495, Od. 11.509, 625, "
        "Od. 13.323, Od. 17.171, 376, etc. ἄγαγον, -ες Il. 1.346, Il. "
        "11.112, Il. 19.118, Il. 24.447, 577, etc.: Od. 14.404, Od. 16.227. "
        "Subj. ἀγάγωμι Il. 24.717. ἀγάγω Il. 2.231. 3 sing. -ῃσι Il. "
        "24.155. -ῃ Od. 15.311. 1 pl. -ωμεν Il. 20.300. 3 sing. opt. ἀγάγοι "
        "Od. 17.243, Od. 21.201. Imp. ἄγαγε Il. 24.337. Pple. ἀγαγών, -οῦσα "
        "Il. 4.407, Il. 8.490: Od. 4.175, 407, Od. 15.428, Od. 23.295. Aor. "
        "imp. pl. ἄξετε Il. 3.105, Il. 24.778: Od. 14.414. Infin. ἀξέμεναι "
        "Il. 23.50. ἀξέμεν Il. 23.111, Il. 24.663. Mid. Fut. ἄξομαι Il. "
        "9.367: Od. 4.601, Od. 21.214. Infin. ἄξεσθαι Od. 21.316, 322. Aor. "
        "ἠγαγόμην Od. 4.82, Od. 14.211. 3 sing. -ετο Il. 7.390, Il. 16.190, "
        "Il. 22.116, 471: Od. 15.238. 3 sing. subj. ἀγάγηται Od. 6.159. "
        "Infin. ἀγαγέσθαι Il. 18.87. 3 pl. aor. ἄξοντο (v. l. ἄξαντο) Od. "
        "8.545. Imp. pl. ἄξεσθε (v.l. ἄξασθε) Od. 8.505. (ἀν-, ἀπ-, δι-, "
        "εἰσ-, εισαν-, ἐξ-, ἐπ-, κατ-, προσ-, συν-, ὑπ-, ὑπεξ-.) I In act. "
        "1 To drive, lead, bring (an animal) Il. 21.368, Il. 11.480, Il. "
        "13.572, Il. 17.134, Il. 23.596, 613, 654: Od. 3.439, Od. 4.622, "
        "Od. 11.623, 625, Od. 14.27, 414, Od. 17.171, 213= Od. 20.174, Od. "
        "17.600, Od. 20.186, etc. To take as a prize: ἵππον Il. 23.577, "
        "ἡμίονον 662, 668. – to put (under the yoke) Il. 5.731, Il. 10.293, "
        "Il. 23.294, 300: Od. 3.383, 476, Od. 15.47. 2 In reference to "
        "persons, to cause to come or go, lead, conduct, take, bring, fetch "
        "Il. 1.346, 440, Il. 3.105, Il. 4.541, Il. 6.291, Il. 7.310, Il. "
        "9.89, etc.: Od. 2.326, Od. 3.270, Od. 4.262, Od. 9.98, Od. 13.134, "
        "etc. In reference to corpses Il. 7.418, Il. 22.392, etc. : Od. "
        "24.419. Of an impersonal agency: τίπτε δέσε χρειὼ δεῦρʼ ἤγαγεν; "
        "Od. 4.312. Of fate, to lead on Il. 2.834, Il. 5.614, etc. In "
        "reference to leading astray Il. 10.391. 3 To lead as a chief Il. "
        "2.557, 580, 631, Il. 4.179, Il. 12.330, Il. 17.96, etc.: Od. "
        "3.189, Od. 6.7, Od. 10.551, Od. 14.469, Od. 24.427. To take "
        "(companions) with one Od. 4.434. 4 To carry off (a horse) as spoil "
        "Il. 16.153. To carry off (persons) captive: υἱόν Il. 2.231. Cf. "
        "Il. 4.239, Il. 6.426, Il. 8.166, Il. 9.594, Il. 11.112, Il. 21.36, "
        "etc.: γυναῖκας Od. 14.264, etc. Sim. with φέρω (φέρω referring to "
        "things, ἄγω to men and cattle) Il. 5.484. In reference to the rape "
        "of Helen Il. 24.764. In reference to taking her back Od. 23.221. "
        "In reference to taking back her and the spoils Il. 7.351, Il. "
        "22.117. In reference to carrying off Briseïs Il. 1.184, 323, 338, "
        "391, Il. 19.273, etc. To seizing and taking away (a γέρας) Il. "
        "1.139. 5 Of a chariot, horses, etc., to bear, carry, bring Il. "
        "5.839, Il. 11.598: Od. 6.37. Of ships Il. 24.396: Od. 7.9, Od. "
        "24.299. 6 In reference to things, to fetch, bring, carry, take Il. "
        "1.99, Il. 7.335, Il. 11.632, Il. 15.531, Il. 23.50, Il. 24.367, "
        "etc.: Od. 1.184, Od. 3.312, Od. 13.216, Od. 14.296, Od. 15.159, "
        "etc. To bring in, import: οἶνον Il. 7.467, Il. 9.72, μέθυ Il. "
        "7.471. To carry off as spoil Il. 1.367. In reference to levying "
        "compensation Od. 22.57. 7 To bring on, cause: πῆμα Il. 24.547: "
        "τερπωλήν Od. 18.37. In reference to atmospheric phenomena: νέφος "
        "ἄγει λαίλαπα Il. 4.278. Cf. Il. 23.188. To bring on (a period of "
        "time): ἦμαρ Od. 18.137, Ἠῶ Od. 23.246. 8 In various uses. In "
        "reference to conducting water in a channel Il. 21.262. To direct "
        "the course of (a battle) Il. 11.721. To cause (a ship) to take a "
        "certain direction Od. 9.495. To bring (to the birth) Il. 19.118. "
        "Of hunters, to draw (a cordon) Od. 4.792. To bring back "
        "(intelligence) Od. 4.258. To keep in memory Od. 5.311. 9 In pres. "
        "pple. with a finite vb., to take and . . . (cf. αἱρέω I 10, εἶμι "
        "1.c, εἶμι 6.b, ἔρχομαι 1, 4, κίον 2, λαμβάνω 7, φέρω 6, 10): ἀνὰ "
        "δʼ εἷσεν ἄγων Il. 1.311, στῆσεν ἄγων Il. 2.558. Cf. Il. 4.392, "
        "etc.: Od. 1.130, Od. 3.416, Od. 4.525, 634, Od. 15.542, etc. 10 "
        "For imp. sing. and pl. ἄγε, ἄγετε, used interjectionally see these "
        "words. II In mid. (often hardly to be distinguished from the "
        "act.). 1 In reference to cattle, to drive, bring Il. 8.505, 545. 2 "
        "To carry or take, take with one: χρυσόν Il. 9.367. Cf. Il. 16.223: "
        "εἵματα Od. 6.58. Cf. Od. 4.82, 601, Od. 10.35, 40. In reference to "
        "corpses Il. 17.163, Il. 24.139. 3 To carry off captive or as spoil "
        "Il. 2.659, Il. 6.455, Il. 7.390, Il. 22.116, Il. 23.829. In "
        "reference to Helen and the spoils Il. 3.72 = 93. To the spoils Il. "
        "7.363. To taking her back Il. 4.19. To take as a prize Il. 23.263. "
        "4 To take to oneself as a wife, marry. a With οἴκαδε or the like: "
        "οἴκαδʼ ἄγεσθαι Il. 3.404, ἠγάγετο πρὸς δώματα Il. 16.190. Cf. Il. "
        "9.146, etc.: Od. 6.159, Od. 21.316. b Without such a word Il. "
        "18.87, Il. 22.471: Od. 14.211, Od. 21.322. 5 To get (a wife for "
        "another). a As in 4.a : κασιγνήτῳ γυναῖκα ἠγάγετο πρὸς δώματα Od. "
        "15.238. b As in 4.b : ἄξομαι ἀμφοτέροις ἀλόχους Od. 21.214. Cf. "
        "Od. 4.10. 6 In reference to conducting a bride to her new home Od. "
        "6.28. 7 In reference to speech, to cause to pass, utter: μῦθον ὃν "
        "οὔ κεν ἀνὴρ διὰ στόμʼ ἄγοιτο Il. 14.91."
    )
    t8 = sc.to_t8("a)/gw", "ἄγω", real)
    assert "Od. 15.4" not in _cites(t8)
    assert "As in 4.b" in _all_text(t8)
    assert "As in 4.a" in _all_text(t8)
    # and the real references either side of it are untouched
    assert "Od. 21.214" in _cites(t8)
    assert "Od. 4.10" in _cites(t8)


def test_person_and_number_after_a_pointer_is_not_a_line_number():
    """φημί, whole and real: the shape split_senses already refuses.

    "Sim. in 3 pl. impf. mid. : ἔφαντό μιν ἐπιδήμιον εἶναι Od. 1.194" — the 3
    is person, not a line, and it came out as Od. 13.3. _MORPH_RE decides it
    here exactly as it decides a sense number in split_senses.
    """
    real = (
        "†φημί (Enclitic in pres. indic. act. except 2 sing.) 1 sing. pres. "
        "φημί Il. 2.129, Il. 5.652, Il. 6.98, etc. : Od. 2.171, Od. 4.141, "
        "Od. 5.290, etc. 2 sing. φῄς Il. 4.351, Il. 14.265, Il. 17.174 : "
        "Od. 1.391, Od. 7.239. φῇσθα Od. 14.149. 3 sing. φησί Il. 1.521, "
        "Il. 14.366, Il. 15.107, etc. : Od. 1.215, Od. 5.105, Od. 17.352, "
        "etc. 1 pl. φαμέν Il. 15.735. 2 pl. φατέ Od. 16.93, Od. 17.196. 3 "
        "pl. φασί Il. 2.783, Il. 4.375, Il. 5.635, etc. : Od. 1.33, Od. "
        "3.84, Od. 4.201, etc. 3 sing. subj. φήῃ Od. 11.128, Od. 23.275. "
        "φῇσι Od. 1.168. φῇ Od. 19.122. Opt. φαίην Il. 6.285 : Od. 20.326. "
        "2 sing. φαίης Il. 3.220, 392, Il. 4.429, Il. 15.697, Il. 17.366 : "
        "Od. 3.124. 3 sing. φαίη Od. 18.218, Od. 23.135. 1 pl. φαῖμεν Il. "
        "2.81, Il. 24.222. Pple. φάς Il. 9.35. Nom. pl. masc. φάντες Il. "
        "3.44, Il. 14.126. Impf. ἔφην Il. 16.61, Il. 20.348 : Od. 4.171, "
        "Od. 11.430, 540, Od. 14.176. φῆν Il. 18.326 : Od. 2.174. 2 sing. "
        "ἔφης Il. 22.280, 331. φῆς Il. 5.473 : Od. 14.117. ἔφησθα Il. "
        "1.397, Il. 16.830 : Od. 3.357, Od. 23.71. φῆσθα Il. 21.186. 3 "
        "sing. ἔφη Il. 1.584, Il. 2.265, Il. 5.111, etc. : Od. 2.377, Od. "
        "12.390, Od. 17.409, etc. φῆ Il. 2.37, Il. 21.361, Il. 24.608 : Od. "
        "4.504, Od. 8.567, Od. 11.237, etc. 1 pl. ἔφαμεν Od. 24.24. φάμεν "
        "Il. 8.229, Il. 23.440 : Od. 4.664, Od. 9.496, Od. 16.347. 2 pl. "
        "φάτε Od. 17.25. 3 pl. ἔφασαν Il. 15.700 : Od. 10.35, 46, Od. "
        "20.384. φάσαν Il. 2.278, Il. 4.374 : Od. 9.500, Od. 10.67, Od. "
        "12.192, Od. 21.366, Od. 22.31. ἔφαν Il. 3.161, 302, Il. 7.206, "
        "etc.: Od. 9.413, Od. 10.422, Od. 17.488, etc. φάν Il. 6.108 : Od. "
        "2.337, Od. 7.343, Od. 18.342. 3 sing. fut. φήσει Il. 8.148, 153. "
        "Mid. 2 pl. pres. φάσθε Od. 6.200, Od. 10.562. Imp. φάο Od. 16.168, "
        "Od. 18.171. 3 sing. φάσθω Od. 20.100. Pple. φάμενος Il. 5.290. Pl. "
        "φάμενοι Od. 10.446. Fem. φαμένη Il. 5.835, Il. 22.247, 460 : Od. "
        "11.150, Od. 13.429, Od. 18.206, Od. 23.85. Infin. φάσθαι Il. "
        "1.187, Il. 9.100, Il. 11.788, etc. : Od. 8.549, Od. 9.504, Od. "
        "11.443, etc. Impf. ἐφάμην Il. 3.366, Il. 5.190, Il. 8.498, etc. : "
        "Od. 4.382, Od. 9.272, Od. 10.70, etc. 3 sing. ἔφατο Il. 1.33, Il. "
        "2.807, Il. 4.326, etc. : Od. 1.42, Od. 2.267, Od. 5.301, etc. φάτο "
        "Il. 1.188, Il. 2.182, Il. 3.28, etc. : Od. 1.420, Od. 2.296, Od. "
        "4.37, etc. 3 pl. ἔφαντο Il. 6.510, Il. 12.106, 125, Il. 17.379 : "
        "Od. 1.194, Od. 4.638, Od. 13.211. φάντο Od. 24.460. (ἀπο-, ἐκ-, "
        "μετα-, παρα-, προσ-) In act. and mid. 1 To utter speech, speak, "
        "say : ὣς ἔφη Il. 1.584, ὣς φάμενος Il. 5.290. Cf. Il. 1.188, Il. "
        "2.278, Il. 3.161, Il. 21.361, etc. : Od. 1.42, Od. 2.35, 377, Od. "
        "4.382, Od. 10.46, etc. 2 To utter, speak, say, tell : ἔπος ἔφατο "
        "Il. 1.361. Cf. Il. 9.100, Il. 18.17, Il. 21.393, etc. : μῦθόν κε "
        "φαίην Od. 20.326. Cf. Od. 2.384, Od. 3.357, Od. 16.168, etc. 3 To "
        "speak out, make disclosure Od. 8.549, Od. 21.194. To say, "
        "communicate, reveal, disclose : τὸ μὲν φάσθαι, τὸ δὲ καὶ "
        "κεκρυμμένον εἶναι Od. 11.443. 4 To say, state, assert, declare : "
        "ὡς φάσαν οἵ μιν ἴδοντο πονεύμενον Il. 4.374. With infin. : "
        "κρονίωνι λοιγὸν ἀμῦναι Il. 1.397, ἄτερ λαῶν πόλιν ἑξέμεν Il. "
        "5.473. Cf. Il. 2.129, Il. 4.351, Il. 6.206, Il. 8.229, Il. 17.174, "
        "etc. : Od. 1.33, Od. 2.171, Od. 4.504, Od. 7.239, Od. 8.567, Od. "
        "9.504, Od. 11.540, etc. With omission of the infin. : εἴ δε κακὸν "
        "φήσει Il. 8.153. 5 In 3 pl. pres. with indefinite subject "
        "understood, they say, men say, it is said. With infin. : περὶ "
        "ἄλλων φασὶ γενέσθαι Il. 4.375, ζώειν ἔτι φασὶ μενοίτιον Il. 16.14. "
        "Cf. Il. 2.783, Il. 5.635, Il. 6.100, Il. 9.401, etc. : Od. 1.189, "
        "Od. 3.188, Od. 4.387, Od. 6.42, Od. 13.249, etc. Sim. in 3 pl. "
        "impf. mid. : ἔφαντό μιν ἐπιδήμιον εἶναι Od. 1.194. 6 With neg., to "
        "declare that . . . not . . . (cf. φάσκω 1) : ἡμίονον δʼ οὔ φημί "
        "τινʼ ἀξέμεν ἄλλον Il. 23.668. Cf. Il. 23.579, etc. : Od. 8.138, "
        "etc. To refuse : οὔ φησιν δώσειν Il. 7.393. 7 To deem, suppose, "
        "think. With infin. : αἱρήσειν πόλιν Il. 2.37, ἀθανάτων τίνʼ "
        "κατελθέμεν Il. 6.108, δηΐφοβον παρεῖναι Il. 22.298. Cf. Il. 3.44, "
        "366, Il. 4.429, Il. 5.190, Il. 8.498, etc. : Od. 1.391, Od. 4.171, "
        "Od. 6.200, Od. 9.496, Od. 11.430, Od. 13.357, etc. With omission "
        "of the infin. : ψεῦδός κεν φαῖμεν Il. 2.81=Il. 24.222. Cf. Il. "
        "5.184, Il. 14.126. Without construction : ἦ τοι ἔφης γε Il. "
        "22.280. 8 To have such and such an opinion of oneself, think so "
        "and so of oneself, be minded so and so : ἶσον ἐμοὶ φάσθαι Il. "
        "1.187, Il. 15.167. Cf. Il. 14.366, Il. 15.183."
    )
    t8 = sc.to_t8("fhmi/", "†φημί", real)
    assert "Od. 13.3" not in _cites(t8)
    assert "Sim. in 3 pl. impf. mid." in _all_text(t8)
    assert "Od. 1.194" in _cites(t8)


def test_a_sub_sense_letter_marks_the_digit_before_it():
    """δεύτερος, whole and real.

    "d So as to come in as in 3.b: ὁρμηθείς Il. 16.467. Cf. Il. 3.349." The 3
    of "3.b" points at sense 3 and was emitted as Od. 18.3 — and the pointer
    was left standing as two rows, one of them a definition reading "b".
    """
    real = (
        "δεύτερος [prob. fr. δεύω2.] 1 Coming second in a contest: γνώσεσθʼ "
        "ἵππους οἳ δεύτεροι οἵ τε πάροιθεν Il. 23.498. With ellipse of sb.: "
        "τῷ δευτέρῳ ἵππον ἔθηκεν Il. 23.265. Cf. Il. 23.750. In neut. pl. "
        "δεύτερα, the prize for the secondIl. 23.538. 2 Coming second in "
        "gaining estimation, taking a second place: ἵνα μὴ δ. ἔλθοι Il. "
        "10.368. Cf. Il. 22.207. 3 (except in Il. 17.45, Il. 21.596 "
        "strengthened by αὖτε) a Second in doing something, following "
        "another in doing it: ἠρᾶτο Il. 10.283. Cf. Il. 23.729, 841. b In "
        "fighting, coming in with one's throw or stroke after an opponent: "
        "προΐει ἔγχος Il. 7.248, Il. 20.273. Cf. Il. 5.855, Il. 7.268, Il. "
        "17.45, Il. 21.169, 596. 4 With genit.: ἐμεῖο δεύτεροι (left behind "
        "or surviving me) Il. 23.248. 5 In neut. δεύτερον as adv. a In the "
        "second place. With αὖ: δ. αὖ θώρηκʼ ἔδυνεν Il. 3.332 = Il. 11.19 = "
        "Il. 16.133 = Il. 19.371. Cf. Il. 6.184. b A second time, again: "
        "ὁρμηθείς Il. 16.402. With αὖτε Il. 3.191. With αὖτις Il. 1.513: "
        "Od. 3.161, Od. 19.65 (cf. Od. 18.321), Od. 22.69. Sim.: ᾔτεέ με δ. "
        "αὖτις (asked for a second supply) Od. 9.354. c Another time, for "
        "the future. With αὖτε: δ. αὖτʼ ἀλέασθαι ἀμείνονας ἠπεροπεύειν Il. "
        "23.605. Again, in the future: οὔ μʼ ἔτι δ. ὦδε ἵξετʼ ἄχος Il. "
        "23.46. Cf. Od. 18.24. d So as to come in as in 3.b: ὁρμηθείς Il. "
        "16.467. Cf. Il. 3.349."
    )
    t8 = sc.to_t8("deu/teros", "δεύτερος", real)
    assert "Od. 18.3" not in _cites(t8)
    assert "as to come in as in 3.b" in _all_text(t8)
    assert "Il. 16.467" in _cites(t8)
    assert "Il. 3.349" in _cites(t8)


def test_a_division_numeral_marks_the_digit_after_it():
    """ἤπιος, whole and real: the Roman-numeral shape.

    "See in reference to these εἴδω III.12." points at division III sense 12
    of εἴδω. The 12 was emitted as Od. 15.12. Nothing but the numeral in front
    of it tells you so — it carries no sub-sense letter and no morphology.
    """
    real = (
        "ἤπιος -η, -ον. 1 Well or kindly disposed, kindly, gentle, mild, "
        "not harsh or rigorous: ἤπια δήνεα οἶδεν (is well disposed towards "
        "me) Il. 4.361 (see εἴδω III.12), ἐθέλω τοι ἠ. εἶναι Il. 8.40 = Il. "
        "22.184. Cf. Il. 24.770, 775: Od. 2.47, 230 = Od. 5.8, Od. 2.234 = "
        "Od. 5.12, Od. 10.337, Od. 11.441, Od. 13.314, Od. 14.139, Od. "
        "15.152, 490. Absol. in neut. pl.: εἴ μοι ἤπια εἰδείη (were well "
        "disposed towards me) Il. 16.73: ὁμῶς τοι ἤπια οἶδεν (is at one "
        "with you in loyalty of heart) Od. 13.405 = Od. 15.39, ἀνάκτεσιν "
        "ἤπια εἰδώς (loyal to them) Od. 15.557. See in reference to these "
        "εἴδω III.12. 2 Giving kindly tendance, solicitous for the "
        "well-being of what is committed to one Il. 23.281. 3 Of speech, "
        "tending to effect reconcilement or bring peace Od. 20.327. 4 Of "
        "medicinal applications, soothing, allaying pain Il. 4.218, Il. "
        "11.515, 830."
    )
    t8 = sc.to_t8("h)/pios", "ἤπιος", real)
    assert "Od. 15.12" not in _cites(t8)
    assert "See in reference to these εἴδω III.12." in _all_text(t8)
    assert "Il. 16.73" in _cites(t8)


def test_a_pointer_at_another_entry_is_prose_not_a_quotation():
    """ἐδητύς, whole and real: the other half of the fix.

    The entry ends "See also under ἵημι1 9." — the 9 was emitted as Od. 17.9.
    Once it stops being a citation the run has none, and Greek in it alone
    made it a quotation of Homer's. It is Cunliffe's own prose and belongs in
    the definition (see _holds_sense_ref).
    """
    real = (
        "ἐδητύς -ύος, ἡ [ἔδω.] Food, meat Il. 11.780, Il. 19.231, 320: Od. "
        "4.788, Od. 5.201, Od. 6.250, Od. 10.384, Od. 17.603. See also "
        "under ἵημι1 9."
    )
    t8 = sc.to_t8("e)dhtu/s", "ἐδητύς", real)
    assert "Od. 17.9" not in _cites(t8)
    quoted = [_text(it.get("g") or "") for r in t8["rows"] for it in (r.get("ex") or [])]
    assert not any("ἵημι" in g for g in quoted)
    assert any("See also under ἵημι1 9." in _text(r.get("z") or "")
               for r in t8["rows"])


def test_a_bare_continuation_still_names_its_book():
    """ἀποεῖπον, whole and real: the behaviour the fix must not break.

    "μῆνιν Il. 19.35, 75" means Il. 19.75, and a bare continuation like it is
    the reason a loose digit is read as a citation at all. 75 carries none of
    the marks a sense number carries — no sub-sense letter, no person and
    number, no division numeral in front, no cross-reference introducing it —
    so nothing in this pass can reach it.
    """
    real = (
        "ἀποεῖπον ἀπέειπον aor. [ἀπο- 1, ἀπο- 7.] Pple. ἀποειπών Il. 19.35. "
        "1 To make refusal, refuse: ὑπόσχεο ἤ ὐπόειπε Il. 1.515, κρατερῶς "
        "Il. 9.431 (or perh. this should come under (3)). Cf. Il. 9.510, "
        "675. 2 To renounce: θεῶν ἀπόειπε κελεύθους Il. 3.406 (u.l.ἀπόεικε "
        "κελεύθου), μῆνιν Il. 19.35, 75. 3 To speak out, declare freely: "
        "μῦθον Il. 9.309: Od. 1.373. Absol. to speak one's mind freely Od. "
        "1.91. 4 To announce publicly, state: ἀγγελίην Il. 7.416. Cf. Il. "
        "23.361. To deliver (a message) Od. 16.340 (the prefix here app. "
        "giving the notion at full length)."
    )
    t8 = sc.to_t8("a)poei=pon", "ἀποεῖπον", real)
    cites = _cites(t8)
    assert "Il. 19.35" in cites
    assert "Il. 19.75" in cites


def test_the_one_mis_scanned_connector_does_not_become_a_definition():
    """ἐπιτρέχω, whole and real: Cunliffe printed "Cf.", the scan says "Of."

    Once, in 11,416 entries. Left standing it is a row whose whole definition
    reads "Of.", sitting between "Of dogs" and "Of a spear" as though it were
    a third sense of the same shape. It is not dropped and the text is not
    corrected — it joins the citation list it introduces, as "etc." does.
    See _MISSCAN_CF_RE.
    """
    real = (
        "ἐπιτρέχω [ἐπι- 11 14.] Genit. sing. neut. aor. pple. ἐπιθρέξαντος "
        "Il. 13.409. 3 sing. aor. ἐπέδραμε Il. 4.524, Il. 5.617. 3 dual "
        "ἐπεδραμέτην, ἐπιδραμέτην Il. 10.354, Il. 23.418, 433, 447. 3 pl. "
        "ἐπέδραμον Il. 14.421, Il. 18.527: Od. 14.30. 3 sing. pf. "
        "ἐπιδέδρομε Od. 6.45, Od. 20.357. 1 To run towards in its course, "
        "tend to approach. With dat.: ἅρμαθʼ ἵπποις ἐπέτρεχον Il. 23.504. 2 "
        "To run towards or up to a person, etc., with hostile intent: "
        "ἐπέδραμεν ὅς ῥʼ ἔβαλεν Il. 4.524. Of. Il. 5.617, Il. 10.354, Il. "
        "14.421, Il. 18.527. Of dogs Od. 14.30. 3 To run after or in "
        "pursuit of a competitor in a race. Of horses Il. 23.418, 447. 4 To "
        "run over (a space). Of horses: πόσσον ἐπιδραμέτην Il. 23.433. Of a "
        "spear, to pass over (and graze) something: ἀσπὶς ἐπιθρέξαντος "
        "ἄϋσεν ἔγχεος (genit. absolute) Il. 13.409. 5 In pf., of light, to "
        "play or be shed upon something: λευκὴ ἐπιδέδρομεν αἴγλη Od. 6.45. "
        "Of a mist, to be spread over something Od. 20.357."
    )
    t8 = sc.to_t8("e)pitre/xw", "ἐπιτρέχω", real)
    assert not any(_text(r.get("z") or "").strip() == "Of." for r in t8["rows"])
    # its citations join the sense above, exactly as a "Cf." list does
    hostile = next(r for r in t8["rows"] if r.get("n") == "2")
    assert "Il. 5.617" in (hostile.get("au") or [])
    assert "Il. 18.527" in (hostile.get("au") or [])
    # nothing is dropped: what was printed is still on the page
    assert "Of." in (hostile.get("au") or [])
    # and the real "Of ..." senses either side are untouched
    zs = [_text(r.get("z") or "") for r in t8["rows"]]
    assert "Of dogs" in zs and "Of a spear, to pass over (and graze) something" in zs


# ── a work abbreviation the scan glued to the word before it ───────────────

def test_a_reference_glued_to_the_word_before_it_is_still_one_reference():
    """ἄγριος, on its REAL source text.

    The scan lost the space: the entry reads "wild creaturesIl. 5.52". Every
    regex in the module matched the abbreviation behind a `\\b`, and after "s"
    there is no word boundary before "I", so "Il." was never seen. The parse
    read a loose 5 and a loose 52 instead, and restored each of them to the
    book the reference before it had established — Il. 19, from "Applied to
    flies Il. 19.30" — so the entry shipped TWO live citations, Il. 19.5 and
    Il. 19.52, where Cunliffe printed one, and both pointed at lines that have
    nothing to do with ἄγριος. The English went with them, into `g`, so the
    quotation read "ἄγρια, wild creaturesIl." as though Homer had written it.
    """
    real = (
        "ἄγριος -η, -ον and -ος, -ον [ἀγρός.] 1 Of animals, wild, untamed "
        "Il. 3.24, Il. 4.106, Il. 8.338, Il. 9.539, Il. 15.271: Od. 9.119, "
        "Od. 14.50. Applied to flies Il. 19.30. Absol. in neut. pl. ἄγρια, "
        "wild creaturesIl. 5.52. 2 Of men, fierce, savage, raging Il. 6.97 = "
        "278, Il. 8.96, Il. 21.314. Of Scylla Od. 12.119. 3 Not conforming "
        "to the traditional order of society, uncivilized, barbarous, savage "
        "Od. 1.199, Od. 2.19, Od. 6.120 = Od. 9.175 = Od. 13.201, Od. 7.206, "
        "Od. 8.575, Od. 9.215, 494. 4 In gen., fierce, raging, ungoverned: "
        "χόλος Il. 4.23, πτόλεμος Il. 17.737. Cf. Il. 8.460, Il. 9.629, "
        "Il. 17.398, Il. 19.88, Il. 22.313: Od. 8.304. 5 Absol. in neut. pl. "
        "ἄγρια, fierceness: ἀ. οἶδεν (has fierceness in his heart) "
        "(see εἴδω III.12) Il. 24.41."
    )
    t8 = sc.to_t8("a)/grios", "ἄγριος", real)
    cites = [e.get("c") for r in t8["rows"] for e in (r.get("ex") or [])]
    cites += [c for r in t8["rows"] for c in (r.get("au") or [])]
    assert "Il. 5.52" in cites
    # the two the lost space fabricated
    assert "Il. 19.5" not in cites
    assert "Il. 19.52" not in cites
    # and Cunliffe's own English is out of Homer's mouth. "Absol. in neut. pl.
    # ἄγρια, wild creatures" is one sentence of his, and the parse now reads
    # it as one — exactly as it reads the same entry's sense 5, "Absol. in
    # neut. pl. ἄγρια, fierceness", whose colon hands the quotation over.
    # (This assertion replaces one that required "ἄγρια, wild creatures" to
    # BE the quotation, which left his gloss inside `g` — see
    # _sentence_runs_through.)
    assert not [e for r in t8["rows"] for e in (r.get("ex") or [])
                if "wild creatures" in _text(e.get("g") or "")]
    row = next(r for r in t8["rows"]
               if _text(r.get("z") or "").endswith("ἄγρια, wild creatures"))
    assert row["au"] == ["Il. 5.52"]


def test_a_glued_reference_does_not_move_a_citation_into_the_other_poem():
    """αἶθοψ, on its REAL source text.

    Two of its references are glued. The second, "gleamingIl. 4.495", falls
    after a run of Odyssey citations ending "Od. 24.364", so the loose 4 and
    495 were restored to Od. 24 — the entry shipped "Od. 24.4" and
    "Od. 24.495" for a line in the ILIAD. A citation in the wrong poem is the
    worst shape this defect takes, because nothing about the rendered link
    says it is wrong.
    """
    real = (
        "αἶθοψ -οπος [αἴθω + ὀπ-. See ὁράω.] Epithet of οἶνος, bright, "
        "sparklingIl. 1.462, Il. 4.259, Il. 5.341, Il. 6.266, Il. 11.775, "
        "Il. 14.5, Il. 16.226, 230, Il. 23.237, 250= Il. 24.791, Il. 24.641: "
        "Od. 2.57 = Od. 17.536, Od. 3.459, Od. 7.295, Od. 9.360, Od. 12.19, "
        "Od. 13.8, Od. 14.447, Od. 15.500, Od. 16.14, Od. 19.197, Od. 24.364. "
        "Of χαλκός, bright, flashing, gleamingIl. 4.495 = Il. 5.562 = 681 = "
        "Il. 17.3 = 87 = 592 = Il. 20.111, Il. 13.305, Il. 18.522, Il. 20.117 "
        ": Od. 21.434. Of καπνός, fire-lit (i.e. reflecting the light of the "
        "flame below) Od. 10.152."
    )
    t8 = sc.to_t8("ai)=qoy", "αἶθοψ", real)
    cites = [e.get("c") for r in t8["rows"] for e in (r.get("ex") or [])]
    cites += [c for r in t8["rows"] for c in (r.get("au") or [])]
    assert "Il. 1.462" in cites and "Il. 4.495" in cites
    assert "Od. 24.4" not in cites
    assert "Od. 24.495" not in cites
    # the run the glued reference opened still resets the book for the bare
    # continuations behind it: "= 681" is Il. 5.681, not Od. anything
    assert "Il. 5.681" in cites


def test_a_glued_reference_inside_a_form_is_not_read_as_two_numbers():
    """καθίζω, on its REAL source text.

    The glue is inside the head run here, so it is `split_forms` that reads
    it, not `split_evidence` — which is why the space is restored where the
    definition ENTERS the parse rather than by loosening the three regexes
    that happen to name the abbreviation. The participle shipped as the form
    "καθίσσαςIl", with the reference behind it broken into the bare tokens
    "9" and "488".
    """
    real = (
        "καθίζω [καθ-, κατα- 1.] 3 pl. aor. κάθισαν Il. 19.280: Od. 4.659. "
        "Imp. κάθισον Il. 3.68, Il. 7.49. Pple. καθίσσαςIl. 9.488. Fem. "
        "καθίσᾱσα Od. 17.572. 1 To cause to seat oneself, bid be seated: μή "
        "με κάθιζε Il. 6.360. Cf. Il. 3.68=Il. 7.49: Od. 4.659, Od. 17.572. "
        "To cause (an assembly) to sit for business, bring (it) together "
        "Od. 2.69. 2 To set, place: ἐπʼ ἐμοῖσι γούνεσσι καθίσσας Il. 9.488. "
        "To seat or settle in an appointed place: κάθισαν γυναῖκας (brought "
        "them to their new home) Il. 19.280. 3 To seat oneself, sit down: "
        "ἔνθα καθῖζʼ Ἑλένη Il. 3.426. Cf. Il. 8.436, Il. 11.623, Il. 20.151: "
        "ἐπὶ κληῗσι καθῖζον Od. 2.419=Od. 4.579, Od. 9.103 = 179 = 471 = "
        "563=Od. 11.638=Od. 12.146=Od. 15.549, Od. 13.76, Od. 15.221. Cf. "
        "Od. 5.326, Od. 8.6, 422, Od. 16.408, Od. 17.90, 256. 4 To have "
        "one's seat, be seated, sit: ἂμ πέτρῃσι καθίζων Od. 5.156. Cf. "
        "Il. 3.394, Il. 15.50."
    )
    t8 = sc.to_t8("kaqi/zw", "καθίζω", real)
    assert ["Pple.", "καθίσσας"] in t8["f"]
    assert "Il. 9.488" in t8["au"]
    assert "9" not in t8["au"] and "488" not in t8["au"]


def test_ungluing_a_reference_only_ever_inserts_a_space():
    # The one thing this must not do is emend. It restores a word separator
    # the page had and the scan dropped; every other character is untouched,
    # and text that is already well formed comes back identical.
    glued = "wild creaturesIl. 5.52. Cf. Od. 4.690."
    assert sc.unglue_refs(glued) == "wild creatures Il. 5.52. Cf. Od. 4.690."
    assert sc.unglue_refs(glued).replace(" ", "") == glued.replace(" ", "")
    clean = "ἄγρια, wild creatures Il. 5.52, Il. 19.30: Od. 9.119."
    assert sc.unglue_refs(clean) == clean
    # only in front of a FULL reference: a bare continuation is not one, and
    # neither is an abbreviation with no book and line behind it
    assert sc.unglue_refs("Il. 19.35, 75") == "Il. 19.35, 75"


def test_a_continuation_still_expands_after_the_glued_reference_fix():
    # The pin the glue fix must not disturb: "Il. 19.35, 75" is Il. 19.75.
    segs = sc.split_evidence("Il. 19.35, 75")
    assert segs[0]["au"] == ["Il. 19.35", "Il. 19.75"]


def test_the_two_misstated_references_point_at_the_lines_cunliffe_means():
    """The only two references in the corpus no parsing rule can reach, because
    the 1924 text itself states them wrongly.

    Both targets are established from our own Greek, not inferred. Il. 21.529
    is "ὃ δ' οἰμώξας ἀπὸ πύργου βαῖνε χαμᾶζε" — the participle οἰμώζω is
    listing, in the only book its ordered run (20.417 … 22.34) leaves room for;
    Od. 5.529 does not exist, Odyssey 5 ending at 493. Il. 22.29 is "ὅν τε κύν'
    Ὠρίωνος ἐπίκλησιν καλέουσι", the phrase Ὠρίων glosses as Sirius.

    Correcting a printed source is this edition's exception, not its habit: the
    mis-scanned "Of." in ἐπιτρέχω is kept verbatim, because dropping a letter
    loses content. These two are repaired because a wrong live link is worse
    than a wrong glyph, and because the right line is known rather than guessed.
    """
    oim = sc.fix_source_misscan(
        "oi)mw/zw",
        "Pple. οἰμώξας Il. 5.68, Il. 16.290, Il. 20.417, Od. Il.529, Il. 22.34")
    assert "Il. 21.529" in oim and "Od. Il.529" not in oim

    ori = sc.fix_source_misscan(
        "w)ri/wn",
        "The constellation Il. 14.486, 488: Od. 5.274. κύων Ὠρίωνος, Sirius 22.29 .")
    assert "Sirius Il. 22.29" in ori

    # Anchored to the entry: the same printed string elsewhere is left alone.
    assert sc.fix_source_misscan("a)/gw", "Sirius 22.29") == "Sirius 22.29"


# ── the line number of a reference is not a sense number ───────────────────

MERMHRIZW = (
    "μερμηρίζω [μερ- as in μέρμερος.] Aor. μερμήριξα Od. 10.50, 151, 438. "
    "3 sing. -ε Il. 1.189, Il. 5.671, Il. 14.159, etc. : Od. 2.93, Od. 4.791, "
    "Od. 17.235, etc. Subj. μερμηρίξω Od. 16.261. Pple. μερμηρίξας Od. 11.204, "
    "Od. 16.237. Infin. μερμηρίξαι Od. 16.256. 1 To turn (a thing) anxiously "
    "over in one's mind, to ponder or consider (it), meditate (it), have (it) "
    "in view : πολλά Od. 1.427, φόνον ἡμῖν Od. 2.325. Cf. Il. 20.17 : "
    "Od. 4.533, Od. 19.2 = 52, Od. 20.38, 41. Of a lion Od. 4.791. To think "
    "out or contrive : δόλον τόνδε Od. 2.93, Od. 24.128. To think of, find : "
    "ἀμύντορά τινα Od. 16.256, 261. 2 Absol., to ponder, consider, deliberate, "
    "meditate : τρὶς μερμήριξεν Il. 8.169, ἔτι μερμήριζον (were hesitating) "
    "Il. 12.199. Cf. Od. 5.354, Od. 11.204, Od. 16.237, Od. 20.93. With "
    "dependent clause. a With relative : ὅ τι κύντατον ἕρδοι Il. 10.503. "
    "b With clause introduced by ὡς (how) Il. 2.3. c By ὅπως Il. 14.159 : "
    "Od. 9.554, Od. 15.169, Od. 20.28, 38. d With alternatives introduced by "
    "ἢ... ἦ... Il. 1.189, Il. 5.671, Il. 13.455, Il. 16.647 : Od. 4.117, "
    "Od. 6.141, Od. 10.50, Od. 16.73, Od. 17.235, Od. 18.90, Od. 20.10, "
    "Od. 22.333. With the first alternative expressed by an infin. and the "
    "second introduced by ἦ: μερμήριξε κύσσαι... ἦ... Od. 24.235. With infin. "
    "expressing only one of the alternatives : διάνδιχα μερμήριξεν ἵππους "
    "στρέψαι (had half a mind to...) Il. 8.167. Cf. Od. 10.151, 438."
)


def test_a_reference_line_number_is_not_a_sense_number():
    """The whole μερμηρίζω, because the fault needs the entry's real length.

    "Od. 19.2 = 52" offers a 2 that continues the run and takes it, so the
    phantom sense swallows the number the REAL sense 2 ("Absol., to ponder")
    then cannot have, and the 19 left in front of it is restored to the last
    book the parse saw — a live link to Od. 4.19, which this entry never
    cites.
    """
    t8 = sc.to_t8("mermhri/zw", "μερμηρίζω", MERMHRIZW)
    cites = [c for r in t8["rows"]
             for c in list(r.get("au") or [])
                    + [e["c"] for e in (r.get("ex") or []) if e.get("c")]]
    assert "Od. 4.19" not in cites
    assert "Od. 19.2" in cites and "Od. 19.52" in cites
    # the real sense 2 keeps its number and its definition
    two = [r for r in t8["rows"] if r.get("n") == "2"]
    assert len(two) == 1
    assert "Absol., to ponder" in two[0]["z"]


def test_a_sense_number_inside_a_reference_is_refused_but_a_real_one_is_kept():
    """The exclusion is by POSITION, so a sense number that merely follows a
    reference is untouched."""
    inside = sc.split_senses("x 1 First Od. 3.3 = Od. 12.386. Cf. Il. 1.1.")
    assert [s["n"] for s in inside["senses"]] == ["1"]
    after = sc.split_senses("x 1 First Il. 1.5. 2 Second Il. 2.7.")
    assert [s["n"] for s in after["senses"]] == ["1", "2"]


# ── a suffix in brackets is Cunliffe's note, not Homer's words ─────────────

ABUDOS = (
    "Ἄβυδος A city on the southeast of the Hellespont, a little below Sestus "
    "on the other side Il. 2.836. Ἀβυδόθεν [-θεν], from Abydus Il. 4.500 . "
    "Ἀβυδόθι [-θι], at Abydus Il. 16.584 ."
)


def test_a_derived_adverb_named_by_its_ending_is_not_a_quotation():
    t8 = sc.to_t8("a)/budos", "Ἄβυδος", ABUDOS)
    quoted = [e["g"] for r in t8["rows"] for e in (r.get("ex") or [])]
    assert quoted == []
    defs = [r.get("z") or "" for r in t8["rows"]]
    assert "Ἀβυδόθεν [-θεν], from Abydus" in defs
    assert "Ἀβυδόθι [-θι], at Abydus" in defs
    assert [r.get("au") for r in t8["rows"]] == [
        ["Il. 2.836"], ["Il. 4.500"], ["Il. 16.584"]]


KLEPTW = (
    "κλέπτω 3 sing. aor, ἔκλεψε Il. 5.268, Il. 14.217. Infin. κλέψαι "
    "Il. 24.24, 71, 109. (ἐκ-, ὑποκλοπέομαι.) 1 To take away by stealth, "
    "filch, purloin : τῆς γενεῆς ἔκλεψεν Ἀγχίσης (filched (a strain) from "
    "that . . . ) Il. 5.268, κλέψαι [Ἕκτορα (i.e. his corpse)] ὀτρύνεσκον "
    "Ἀργειφόντην Il. 24.24. Cf. Il. 24.71, 109. 2 To cozen, beguile, lead "
    "astray : μὴ κλέπτε νόῳ Il. 1.132. Cf. Il. 14.217."
)


def test_a_supplied_word_in_brackets_is_still_a_quotation():
    """The hyphen is what tells them apart: κλέπτω supplies a WORD.

    The whole entry, because the bracket only reaches split_evidence as a
    lead once a citation stands in front of it.
    """
    t8 = sc.to_t8("kle/ptw", "κλέπτω", KLEPTW)
    quoted = [e["g"] for r in t8["rows"] for e in (r.get("ex") or [])]
    assert "κλέψαι [Ἕκτορα (i.e. his corpse)] ὀτρύνεσκον Ἀργειφόντην" in quoted


# ── a row with nothing in it is a blank line ───────────────────────────────

def test_a_sense_number_left_alone_moves_onto_its_own_definition():
    """ἀκριτόμυθος splits sense 2 at its quotation and leaves the number
    standing above an unnumbered row, so the entry printed a bare "2"."""
    t8 = sc.to_t8("a)krito/muqos", "ἀκριτόμυθος",
                  "ἀκριτόμυθος [ἄκριτος + μῦθος.] 1 Indiscriminate or reckless "
                  "in speech Il. 2.246. 2 Hard to be discerned or interpreted "
                  "ὄνειροι Od. 19.560.")
    assert [(r.get("n"), r.get("z")) for r in t8["rows"]] == [
        ("1", "Indiscriminate or reckless in speech"),
        ("2", "Hard to be discerned or interpreted"),
    ]
    assert t8["rows"][1]["ex"] == [{"g": "ὄνειροι", "c": "Od. 19.560"}]


def test_a_row_with_no_number_and_no_content_is_not_emitted():
    t8 = sc.to_t8("a)qhrhloigo/s", "ἀθηρηλοιγός",
                  "ἀθηρηλοιγός ὁ [ἀθήρ, ear of corn = λοιγός. Consumer of ears "
                  "of corn.] App., a shovel by which grain to be winnowed was "
                  "thrown against the wind ( = πτύον) Od. 11.128 = Od. 23.275.")
    assert len(t8["rows"]) == 1
    assert t8["rows"][0]["z"].startswith("App., a shovel")


DIFROS = (
    "δίφρος -ου, ὁ [contr. fr. διφόρος fr. δι-, δισ- + -φορος, φέρω. Something "
    "that carries two, i. e. (in war) the ἡνίοχος and the παραιβάτης.] "
    "1 a A chariot, whether used in war, for racing, for travel or for "
    "conveyance in general (hardly to be distinguished from ἅρμα) Il. 3.262, "
    "310, Il. 5.20, Il. 13.392, Il. 23.335, 370, Il. 24.322, etc.: Od. 3.324, "
    "369, 481, 483, Od. 4.590, Od. 14.280. b The platform thereof, composed of "
    "straps plaited and strained tight Il. 5.727. 2 A seat (the notion of two "
    "app. lost) Il. 3.424, Il. 6.354, Il. 24.578: Od. 4.717, Od. 17.330, "
    "Od. 19.97, Od. 20.259, etc."
)


def test_a_numbered_row_whose_sub_senses_carry_the_definition_is_kept():
    """δίφρος's sense 1 has no definition of its own because a and b hold it.
    That is how Cunliffe wrote it, and the number must not move onto a."""
    t8 = sc.to_t8("di/fros", "δίφρος", DIFROS)
    assert [(r.get("n"), r.get("lv")) for r in t8["rows"]] == [
        ("1", 1), ("a", 2), ("b", 2), ("2", 1)]
    assert not t8["rows"][0].get("z")
    assert t8["rows"][1]["z"].startswith("A chariot")


OKEANOS = (
    "Ὠκεανός (ἀκαλαρρείτης, ἀψόρροος , βαθυδίνης, βαθυρρείτης , βαθύρροος, "
    "Ὠ. ποταμός ). The river Oceanus, encircling the earth and flowing back "
    "upon itself Il. 1.423, Il. 3.5, Il. 5.6, Il. 7.422, Il. 21.485, "
    "Il. 16.151, Il. 18.240, 402, 489, 607, Il. 19.1, Il. 23.205: Od. 4.568, "
    "Od. 5.275, Od. 10.508, 511, Od. 11.13, 21, 158, 639, Od. 12.1, "
    "Od. 19.434, Od. 20.65, Od. 22.197, Od. 23.244, 347, Od. 24.11. "
    "Personified. A god Od. 3.7. Associated with Tethys in the rearing of "
    "Hera Il. 14.201, 302 Father (Il. 18.399) of Eurynome-1 and (Od. 10.139) "
    "of Perse. θεῶν γένεσις Od. 14.201 , 302. γ. πάντεσσιν Il. 14.246. Parent "
    "of all waters Il. 21.195 (but see Ξάνθος-1). δῶμʼ Ὠκεανοῖο Il. 14.311 ."
)


def test_a_homonym_suffix_is_not_a_line_number():
    """Ὠκεανός, whole and real.

    Cunliffe tells one Eurynome from another with a trailing digit. Read as a
    bare continuation it was restored to the book the reference before it left
    behind — a live, clickable "Il. 14.1" the entry never cites — and the name
    reached the reader cut in half, "of Eurynome-", with the sentence torn into
    two rows around the hole.
    """
    t8 = sc.to_t8("w)keano/s", "Ὠκεανός", OKEANOS)
    assert "Il. 14.1" not in _cites(t8)
    text = _all_text(t8)
    assert "Eurynome-1" in text
    assert "Eurynome-" not in text.replace("Eurynome-1", "")
    # one row, not two: the parenthesised references stay inside the sentence
    row = next(r for r in t8["rows"] if "Eurynome-1" in _text(r.get("z") or ""))
    assert _text(row["z"]) == (
        "Father (Il. 18.399) of Eurynome-1 and (Od. 10.139) of Perse.")
    # and the references the entry really does cite are all still there
    for c in ("Il. 14.201", "Il. 14.302", "Il. 14.246", "Il. 14.311"):
        assert c in _cites(t8), c


HEKABE = (
    "Ἑκάβη (ἠπιόδωρος). Daughter of Dymas-1, full sister of Asius-1 and wife "
    "of Priam (for her children see under Πρίαμος) Il. 6.251; collects the "
    "aged women to pray to Athene Il. 6.286, her gift to Α. 288, 293; "
    "Il. 6.451, Il. 16.718; vainly beseeches Hector to take refuge from "
    "Achilles Il. 22.79; Il. 22.234; she sees Hector's corpse being dragged "
    "away Il. 22.405, her lament 430; summoned by Priam Il. 24.193, she tries "
    "to dissuade him from going to the ships 200, she speeds him on his way "
    "283; her lament over Hector's ransomed, corpse Il. 24.747."
)


def test_a_homonym_suffix_before_any_reference_is_not_a_citation():
    """Ἑκάβη, whole and real.

    Her parentage is named before the entry has cited anything, so the two
    homonym digits had no book to expand against and reached the reader as a
    citation list reading "1" — with the sentence broken into three rows,
    "Daughter of Dymas-" / "full sister of Asius-" / the rest.
    """
    t8 = sc.to_t8("e(ka/bh", "Ἑκάβη", HEKABE)
    assert "1" not in _cites(t8)
    assert t8["rows"][0]["au"] == ["Il. 6.251"]
    assert _text(t8["rows"][0]["z"]) == (
        "Daughter of Dymas-1, full sister of Asius-1 and wife of Priam "
        "(for her children see under Πρίαμος)")
    # the bare continuations that ARE continuations still expand
    assert "Il. 22.430" in _cites(t8)
    assert "Il. 24.200" in _cites(t8)


ATREMAS = (
    "ἀτρέμας Before a consonant ἀτρέμα Il. 15.318. [ἀ-1 + τρέμω.] Without "
    "motion, still Il. 2.200, Il. 5.524, Il. 13.280, 438, 557, Il. 14.352, "
    "Il. 15.318: Od. 13.92, Od. 19.212."
)


def test_a_homonym_suffix_inside_an_etymology_is_not_a_line_number():
    """ἀτρέμας, whole and real.

    The same mark on a prefix: "[ἀ-1 + τρέμω.]" points at ἀ-1, and the digit
    was emitted as a live "Il. 15.1" with the bracket split across three rows
    — "[", then ἀ- as a quotation of Homer, then "+ τρέμω.]".
    """
    t8 = sc.to_t8("a)tre/mas", "ἀτρέμας", ATREMAS)
    assert "Il. 15.1" not in _cites(t8)
    row = next(r for r in t8["rows"] if "τρέμω" in _text(r.get("z") or ""))
    assert _text(row["z"]) == "[ἀ-1 + τρέμω.] Without motion, still"
    assert "Il. 13.438" in _cites(t8) and "Il. 13.557" in _cites(t8)


def test_what_stands_before_the_hyphen_decides_the_homonym_mark():
    """The mark is a digit hung on a NAME. A digit hung on another digit is
    the tail of a line range Cunliffe prints in full ("Od. 6.177-8"), which is
    a different shape with a different cure, and this rule must not claim it.
    """
    assert sc._is_homonym_suffix("of Eurynome-1", len("of Eurynome-"))
    assert sc._is_homonym_suffix("[ἀ-1 + τρέμω.]", len("[ἀ-"))
    assert not sc._is_homonym_suffix("Od. 6.177-8", len("Od. 6.177-"))
    # nor a loose digit that is a genuine bare continuation
    assert not sc._is_homonym_suffix("Il. 19.35, 75", len("Il. 19.35, "))


# ── a Greek name inside Cunliffe's sentence is not a quotation ──────────────
# The proper-name volume is written as "Patronymic <Greek> <English genealogy>",
# and _quote_start presumed the first Greek word opened a quotation. The entry
# then said Homer wrote the genealogy. Every fixture below is a WHOLE real
# source entry, copied verbatim from sources/cunliffe/cunliffe-2-hompers.jsonl —
# the tests for the homonym rule used Latin names and bracketed roots and so
# never touched this interaction. See _sentence_runs_through.

def test_a_greek_patronymic_does_not_turn_the_genealogy_into_a_quotation():
    """Ἀμφίων-3, whole and real (cunliffe-2-hompers.jsonl, key a)mfi/wn).

    "Patronymic Ἰασίδης-1 King of Orchomenus-1 and father of Chloris
    Od. 11.283" came out as z="Patronymic" with Homer credited for
    "Ἰασίδης-1 King of Orchomenus-1 and father of Chloris".
    """
    real = ("Ἀμφίων-3 Patronymic Ἰασίδης-1 King of Orchomenus-1 and father "
            "of Chloris Od. 11.283.")
    t8 = sc.to_t8("a)mfi/wn", "Ἀμφίων-3", real)
    quoted = [_text(it["g"]) for r in t8["rows"] for it in (r.get("ex") or [])]
    assert not any("King of Orchomenus" in g for g in quoted), quoted
    row = next(r for r in t8["rows"] if "Ἰασίδης-1" in _text(r.get("z") or ""))
    assert _text(row["z"]) == ("Patronymic Ἰασίδης-1 King of Orchomenus-1 "
                               "and father of Chloris")
    assert row["au"] == ["Od. 11.283"]


def test_a_second_greek_patronymic_entry_reads_the_same_way():
    """Ἴφιτος-1, whole and real (cunliffe-2-hompers.jsonl, key i)/fitos).

    The same sentence, and the second entry the homonym lane named as a known
    cost. Its quantity mark and epithet stay in `i`, where they already were.
    """
    real = ("Ἴφιτος-1 (ι) (μεγάθυμος). Patronymic Ναυβολίδης-1 Father of "
            "Schedius-1 and Epistrophus-1 Il. 2.518, Il. 17.306.")
    t8 = sc.to_t8("i)/fitos", "Ἴφιτος-1", real)
    quoted = [_text(it["g"]) for r in t8["rows"] for it in (r.get("ex") or [])]
    assert not any("Father of Schedius" in g for g in quoted), quoted
    row = next(r for r in t8["rows"] if "Ναυβολίδης-1" in _text(r.get("z") or ""))
    assert _text(row["z"]) == ("Patronymic Ναυβολίδης-1 Father of Schedius-1 "
                               "and Epistrophus-1")
    assert row["au"] == ["Il. 2.518", "Il. 17.306"]
    assert _text(t8["i"]) == "(ι) (μεγάθυμος)."


def test_a_closing_run_of_cunliffes_own_prose_is_not_a_quotation():
    """Ἑλλάς, whole and real (cunliffe-2-hompers.jsonl, key e(lla/s).

    The third entry the homonym lane named. It reaches `ex` by split_evidence's
    TAIL, which has no citation to test the run against, so the same
    presumption is made there and the same sentence — English first, Greek in
    the middle — was handed to Homer.
    """
    real = ("Ἑλλάς (εὐρύχορος, καλλιγύναιξ ). Part of the realm of Peleus, "
            "the valley of the Spercheius Il. 2.683, Il. 9.395, 447 , 478, "
            "Il. 16.595: Od. 11.496. Of northern in contrast to southern "
            "Greece, in phrase καθʼ (ἀνʼ) Ἑλλάδα καὶ μέσον Ἄργος. "
            "See Argos-1 (3).")
    t8 = sc.to_t8("e(lla/s", "Ἑλλάς", real)
    quoted = [_text(it["g"]) for r in t8["rows"] for it in (r.get("ex") or [])]
    assert not any("Of northern in contrast" in g for g in quoted), quoted
    assert any("Of northern in contrast to southern Greece" in _text(r.get("z") or "")
               for r in t8["rows"])


# ── a parenthesis Cunliffe opens before the evidence is still one remark ────

def test_a_citation_inside_a_parenthesis_does_not_cut_the_sense():
    """Ἀμύντωρ, whole and real (cunliffe-2-hompers.jsonl, key a)mu/ntwr).

    Its first citation stands inside "(but in Il. 10.266 he is spoken of as
    living in Eleon)". parse_sense cut the sense there, so the definition
    ended "Ruler of Hellas (but in" and the rest of the remark opened a row of
    its own beginning "he is spoken of as living in Eleon)". split_evidence
    already walks past a citation inside one of his parentheses; the cut that
    happens BEFORE it did not, and its depth map, measured on the text after
    the cut, could not see the opener.
    """
    real = ("Ἀμύντωρ Patronymic Ὀρμενίδης. Ruler of Hellas (but in Il. 10.266 "
            "he is spoken of as living in Eleon) and father of Phoenix-1 "
            "Il. 9.448 , Il. 10.266.")
    t8 = sc.to_t8("a)mu/ntwr", "Ἀμύντωρ", real)
    zs = [_text(r.get("z") or "") for r in t8["rows"]]
    assert not any(z.endswith("(but in") for z in zs), zs
    assert not any(z.startswith("he is spoken of") for z in zs), zs
    row = next(r for r in t8["rows"] if "Ruler of Hellas" in _text(r.get("z") or ""))
    assert _text(row["z"]) == (
        "Patronymic Ὀρμενίδης. Ruler of Hellas (but in Il. 10.266 he is "
        "spoken of as living in Eleon) and father of Phoenix-1")
    assert row["au"] == ["Il. 9.448", "Il. 10.266"]


def test_a_stop_inside_a_parenthesis_does_not_open_the_evidence():
    """ἐρίηρος, whole and real (cunliffe-1-lex.jsonl, key e)ri/hros).

    The other half of the same fix, and the one that proves parse_sense alone
    is not enough: once the cut moves to the first citation OUTSIDE his
    parentheses, _evidence_start walks back over the stops inside one — "(and
    in Od. 1.346, Od. 8.62, 471 of ἀοιδός)" — and cut the remark in half,
    leaving "Od." hanging on the definition and its book number reaching the
    row as three loose digits.

    Alone among these fixtures this one PASSES against the pre-fix module: the
    old cut fell at the citation inside the parenthesis and never reached
    these stops. It guards the fix's own second half, not the defect the fix
    was written for, and it caught that half — parse_sense was changed first
    and this entry lost Od. 8.62 outright.
    """
    real = ("ἐρίηρος [ἐρι- + (ϝ)ήρ. Cf. ἐπιήρανος.] Pl. ἐρίηρες. Epithet of "
            "ἑταῖρος, ἑταῖροι (and in Od. 1.346, Od. 8.62, 471 of ἀοιδός), "
            "worthy, faithful, trusty or the like Il. 3.47, Il. 3.378, "
            "Il. 4.266, Il. 8.332, Il. 13.421, Il. 16.363, Il. 23.6: "
            "Od. 1.346, Od. 8.62, 471, Od. 9.100, Od. 9.172, Od. 9.193, "
            "Od. 9.555, Od. 10.387, Od. 10.405, Od. 10.408, Od. 10.471, "
            "Od. 12.199, Od. 12.397.")
    t8 = sc.to_t8("e)ri/hros", "ἐρίηρος", real)
    cites = [c for r in t8["rows"] for c in (r.get("au") or [])]
    assert "Od. 8.62" in cites
    assert not [c for c in cites if c.strip().isdigit()], cites
    assert not any(_text(r.get("z") or "").endswith("Od.") for r in t8["rows"])
    assert any("(and in Od. 1.346, Od. 8.62, 471 of ἀοιδός)"
               in _text(r.get("z") or "") for r in t8["rows"])
