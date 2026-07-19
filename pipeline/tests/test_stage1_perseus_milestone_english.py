"""Stage 1e: milestoned Perseus English (Murray/Butler) — the milestone parser,
anomaly handling, footnote extraction, and paragraph-preservation round-trip.
"""

from __future__ import annotations

from pathlib import Path

from homer_pipeline import stage1_perseus_milestone_english as s1

FIXTURE = Path(__file__).parent / "fixtures" / "perseus_milestone_english" / "tiny.xml"
DEFECTS_FIXTURE = Path(__file__).parent / "fixtures" / "perseus_milestone_english" / "defects.xml"

# Book 1: no vulgate gap. Book 2: line 4 is a vulgate gap (3 -> 5). Book 3 is
# deliberately absent from the fixture (missing_book_div tests rely on that).
# Book 4: two Loeb notes, each the first footnote on its own (simulated)
# page, so both carry the same printed citation number "1" — the collision
# fixture.
VALID_LINES = {1: {1, 2, 3, 4, 5}, 2: {1, 2, 3, 5, 6}, 4: {1, 2}}

# Defect-regression fixture (defects.xml):
#   Book 1: terminal milestone (n=5) has no following text at all (B1).
#   Book 2: two milestones glued mid-word with no surrounding whitespace (M1).
#   Book 3: a Loeb note preceded by a trailing space in the source (M5).
#   Book 4: the book's last real milestone (n=3) lags one line behind the
#           book's last valid line (4) — no milestone tags n=4 (M2 shape).
DEFECTS_VALID_LINES = {
    1: {1, 2, 3, 4, 5},
    2: {1, 2, 3, 4},
    3: {1, 2, 3},
    4: {1, 2, 3, 4},
}


def _parse(book_ns=(1, 2), extract_footnotes=True):
    return s1.parse_translation(FIXTURE, VALID_LINES, list(book_ns), extract_footnotes)


def _parse_defects(book_ns=(1, 2, 3, 4), extract_footnotes=True):
    return s1.parse_translation(DEFECTS_FIXTURE, DEFECTS_VALID_LINES, list(book_ns), extract_footnotes)


def test_normal_milestones_produce_monotonic_real_ticks():
    parsed = _parse()
    ticks1 = parsed["ticks_by_book"][1]
    ns = [t["n"] for t in ticks1]
    # The fixture's second n="1" milestone is a duplicate (merged, not a tick).
    assert ns == [1, 3, 5]
    assert all(t["real"] for t in ticks1)
    # Offsets strictly increase and land at real word starts in the final text.
    text = parsed["chunks"][1]["text"]
    offs = [t["offset"] for t in ticks1]
    assert offs == sorted(offs)
    assert text[offs[1]:].lstrip().startswith("Many souls")
    assert text[offs[2]:].lstrip().startswith("and made them")


def test_duplicate_milestone_is_merged_and_reported_not_double_ticked():
    parsed = _parse()
    dups = [a for a in parsed["anomalies"] if a["kind"] == "milestone_duplicate" and a["book"] == 1]
    assert len(dups) == 1
    assert dups[0]["n_raw"] == 1
    # No tick lost or duplicated: exactly one n=1 tick survives.
    assert [t["n"] for t in parsed["ticks_by_book"][1]].count(1) == 1


def test_out_of_order_milestone_uses_document_order_and_is_reported():
    parsed = _parse()
    ticks2 = parsed["ticks_by_book"][2]
    # Document order is 1, 4(->gap-snap 5), 99(out-of-range, skipped), 6, 3 —
    # the trailing 3 is a genuine backward jump and must NOT create/reset a
    # tick.
    assert [t["n"] for t in ticks2] == [1, 5, 6]
    ooo = [a for a in parsed["anomalies"] if a["kind"] == "milestone_out_of_order"]
    assert len(ooo) == 1
    assert ooo[0]["book"] == 2 and ooo[0]["n_raw"] == 3 and ooo[0]["last_accepted"] == 6


def test_out_of_range_milestone_is_skipped_not_snapped_to_the_edge():
    """A milestone far outside the book's whole line range (a garbled digit in
    the source, e.g. Od. 16 Murray's n="580" for what should read "280") must
    NOT be snapped to the book's edge line — doing so would poison last_n and
    cascade-reject every correctly-labeled milestone still to come. It is
    reported and skipped instead, so the very next genuine milestone (n=6)
    still advances normally."""
    parsed = _parse()
    oor = [a for a in parsed["anomalies"] if a["kind"] == "milestone_out_of_range"]
    assert oor == [{"kind": "milestone_out_of_range", "book": 2, "n_raw": 99, "valid_range": [1, 6]}]
    assert [t["n"] for t in parsed["ticks_by_book"][2]] == [1, 5, 6]


def test_gap_adjacent_milestone_snaps_to_nearest_existing_line():
    parsed = _parse()
    snaps = [a for a in parsed["anomalies"] if a["kind"] == "milestone_gap_snap"]
    assert len(snaps) == 1
    # n=4 is missing from book 2's spine (gap 3->5); equidistant tie snaps
    # FORWARD to the next existing line (documented tie-break).
    assert snaps[0] == {"kind": "milestone_gap_snap", "book": 2, "n_raw": 4, "snapped_to": 5}
    assert 5 in [t["n"] for t in parsed["ticks_by_book"][2]]


def test_footnote_extraction_anchors_loeb_note_and_strips_it_from_prose():
    # Label = {book}.{seqInBook}.{raw}: book 1's lone Loeb note is its first
    # (seqInBook=1), citation number "1" -> "1.1.1". seqInBook sits BEFORE
    # raw so the label's trailing segment (what the reader displays, see
    # fnDisplay in Reader.svelte/FootnotePopup.svelte) is still bare "1",
    # unchanged from the pre-fix scheme.
    parsed = _parse(extract_footnotes=True)
    assert parsed["footnotes"] == {"1.1.1": "1"}
    assert parsed["label_by_book_seq"] == {(1, 1): "1.1.1"}
    text = parsed["chunks"][1]["text"]
    assert "[^1.1.1]" in text
    # The note's own content ("1") isn't left dangling in the prose stream.
    assert "the wrath.1 Of" not in text
    assert "the wrath.[^1.1.1] Of Peleus" in text


def test_footnote_labels_are_unique_even_when_citation_numbers_collide():
    """The historic bug: Murray's Loeb pages each restart their own
    footnote numbering, so two different notes in the same book can both
    print citation number "1". The old `{book}.{raw}` label scheme collapsed
    them into one key (336 TEI markers -> ~145 unique keys); the fixed
    `{book}.{seqInBook}.{raw}` scheme keeps both, distinguished by document
    order, and both markers in the prose point at their own distinct key."""
    parsed = _parse(book_ns=(1, 2, 4), extract_footnotes=True)
    assert parsed["footnotes"]["4.1.1"] == "1"
    assert parsed["footnotes"]["4.2.1"] == "1"
    assert parsed["label_by_book_seq"][(4, 1)] == "4.1.1"
    assert parsed["label_by_book_seq"][(4, 2)] == "4.2.1"
    text = parsed["chunks"][4]["text"]
    assert "[^4.1.1]" in text
    assert "[^4.2.1]" in text


def test_footnotes_not_extracted_when_flag_is_off_but_note_body_still_stripped():
    parsed = _parse(extract_footnotes=False)
    assert parsed["footnotes"] == {}
    text = parsed["chunks"][1]["text"]
    assert "[^" not in text
    assert "the wrath. Of Peleus" in text


def test_paragraph_break_round_trips_as_a_marker_not_flattened():
    parsed = _parse()
    chunk = parsed["chunks"][1]
    para_markers = [m for m in chunk["markers"] if m["kind"] == "paragraph"]
    assert len(para_markers) == 1
    off = para_markers[0]["offset"]
    # The marker sits exactly at the sentence boundary between the two <p>s.
    assert chunk["text"][:off].rstrip().endswith("countless woes.")
    assert chunk["text"][off:].lstrip().startswith("Many souls")


def test_missing_book_div_is_reported_and_produces_no_chunk():
    parsed = _parse(book_ns=(1, 2, 3))
    missing = [a for a in parsed["anomalies"] if a["kind"] == "missing_book_div"]
    assert missing == [{"kind": "missing_book_div", "book": 3}]
    assert 3 not in parsed["chunks"]


def test_coverage_clean_despite_anomalies():
    parsed = _parse()
    holes = s1.check_coverage(
        {1: sorted(VALID_LINES[1]), 2: sorted(VALID_LINES[2])},
        parsed["ticks_by_book"],
        [1, 2],
    )
    assert holes == []


def test_coverage_reports_a_hole_for_a_missing_book_div():
    parsed = _parse(book_ns=(1, 2, 3))
    valid = {1: sorted(VALID_LINES[1]), 2: sorted(VALID_LINES[2]), 3: [1, 2, 3]}
    holes = s1.check_coverage(valid, parsed["ticks_by_book"], [1, 2, 3])
    assert holes == [
        {"book": 3, "kind": "book_uncovered", "first_line": 1, "last_line": 3}
    ]


def test_nearest_line_ties_snap_forward():
    assert s1._nearest_line([1, 2, 3, 5, 6], 4) == 5
    assert s1._nearest_line([1, 2, 3, 6, 7], 4) == 3  # unambiguous nearest
    assert s1._nearest_line([1, 2, 3, 6, 7], 5) == 6  # unambiguous nearest


# --- Defect regression tests (align-verify gate findings B1, M1, M2, M5) ---


def test_terminal_milestone_with_no_following_text_is_dropped_not_empty():
    """B1: a milestone at the very end of a book's prose (nothing follows it)
    must not survive as a tick — that would create a zero-width window. It is
    dropped and recorded as `terminal_empty_dropped`; the real final English
    stays reachable via the previous (non-empty) tick."""
    parsed = _parse_defects()
    ticks1 = parsed["ticks_by_book"][1]
    ns = [t["n"] for t in ticks1]
    assert 5 not in ns
    assert ns == [1, 3]
    text = parsed["chunks"][1]["text"]
    assert text == "Word one line. Word three line text."
    # No tick may have an empty window.
    for t in ticks1:
        assert t["offset"] < len(text)
    dropped = [a for a in parsed["anomalies"] if a["kind"] == "terminal_empty_dropped"]
    assert dropped == [{"kind": "terminal_empty_dropped", "book": 1, "n": 5, "offset": len(text)}]


def test_milestone_strip_inserts_space_when_source_has_none():
    """M1: stripping a <milestone/> that sits between two words with no
    surrounding whitespace must not glue them together."""
    parsed = _parse_defects()
    text = parsed["chunks"][2]["text"]
    assert "wisewill" not in text
    assert "didHector" not in text
    assert "wise will they hearken" in text
    assert "did Hector move on" in text
    # A milestone that already had real whitespace on its far side must not
    # gain a second, spurious space.
    assert "on.  The end" not in text
    assert "on. The end line four." in text


def test_footnote_marker_offset_lands_on_marker_not_preceding_space():
    """M5: when the source has a trailing space before the <note>, the
    recorded note offset must point at the marker's actual first character
    ('['), not at the space before it."""
    parsed = _parse_defects()
    chunk = parsed["chunks"][3]
    text = chunk["text"]
    marker_pos = text.index("[^3.1.1]")
    assert chunk["notes"] == [{"offset": marker_pos, "text": "1"}]
    # Rendered text is untouched — still exactly one space before the marker.
    assert text[marker_pos - 1] == " "
    assert text[marker_pos - 2] != " "


def test_milestone_strip_inserts_space_after_punctuation_not_just_alnum():
    """M6: the M1 fix only covered word-word glue ("wisewill"). The source
    also drops the milestone's surrounding whitespace after ending
    punctuation (comma, period, semicolon, colon, ?, !, closing quote) --
    e.g. real corpus case Od. 9: "what last?<milestone/>for woes" ->
    glued "last?for". Book 5 of the fixture chains three cases: (1) '?'
    directly abutting the next word (must gain a space), (2) an existing
    single space around a milestone (must NOT become a double space), and
    (3) an em dash abutting the next word (must NOT gain a space -- Loeb's
    dash-as-punctuation convention binds tight on both sides)."""
    parsed = s1.parse_translation(DEFECTS_FIXTURE, DEFECTS_VALID_LINES | {5: {1, 2, 3, 4}}, [5])
    text = parsed["chunks"][5]["text"]
    assert "last?for" not in text
    assert "what last? for woes" in text.lower()
    assert "eye— even" not in text and "eye —even" not in text
    assert "eye—even so" in text
    assert "  " not in text


def test_book_final_milestone_lag_is_not_fabricated():
    """M2 shape: when the source's last real milestone in a book doesn't sit
    on the book's last valid line (sparser tagging near a book's end), the
    parser must not invent a tick for that trailing line — it's real source
    granularity, not a parser slice error. The last real tick's block simply
    runs on to cover the remaining (untagged) content."""
    parsed = _parse_defects()
    ticks4 = parsed["ticks_by_book"][4]
    ns = [t["n"] for t in ticks4]
    assert ns == [1, 3]
    assert 4 not in ns
    text = parsed["chunks"][4]["text"]
    # The line-4 content is real and present, just inside tick 3's window.
    assert "also covers line four content" in text
    holes = s1.check_coverage(
        {4: sorted(DEFECTS_VALID_LINES[4])}, {4: ticks4}, [4],
    )
    assert holes == []


# --- Loeb note real-text join (sources/loeb-notes/notes-<work>.json) ---


def _note(markerId, book, approxLine, noteText, confidence="high"):
    return {
        "work": markerId.split(".")[0],
        "book": book,
        "approxLine": approxLine,
        "marker": markerId.rsplit(".", 1)[-1],
        "markerId": markerId,
        "teiLabel": f"{book}.{markerId.rsplit('.', 1)[-1]}",
        "noteText": noteText,
        "confidence": confidence,
    }


def test_far_line_ref_within_tolerance_returns_none():
    assert s1.far_line_ref("Line 352 was rejected by Aristarchus.", 345) is None
    assert s1.far_line_ref("No internal line reference here at all.", 1) is None


def test_far_line_ref_detects_distant_single_reference():
    # "line 716" is 116 lines from approxLine=600 — well past the 25-line
    # tolerance (real case: iliad.13.9).
    text = "the sling is clearly alluded to in line 716 of this book"
    assert s1.far_line_ref(text, 600) == 716


def test_far_line_ref_expands_abbreviated_range_and_detects_near_hit():
    # "Lines 454-6" means 454-456 (abbreviated second number shares the
    # first's leading digit); both ends are within tolerance of 475.
    assert s1.far_line_ref("Lines 454-6 were lacking in most editions.", 475) is None
    # "Lines 18-20" measured against a marker at line 870 is far on both ends.
    assert s1.far_line_ref("Lines 18-20 were rejected by Zenodotus.", 870) == 18


def test_filter_loeb_notes_keeps_high_excludes_medium_and_low():
    notes = [
        _note("iliad.1.1", 1, 5, "Real explanatory prose.", confidence="high"),
        _note("iliad.1.2", 1, 10, "Medium-confidence text.", confidence="medium"),
        _note("iliad.1.3", 1, 15, "Low-confidence text.", confidence="low"),
    ]
    kept, excluded = s1.filter_loeb_notes(notes)
    assert [n["markerId"] for n in kept] == ["iliad.1.1"]
    reasons = {n["markerId"]: n["exclusionReason"] for n in excluded}
    assert reasons["iliad.1.2"] == "confidence:medium"
    assert reasons["iliad.1.3"] == "confidence:low"


def test_filter_loeb_notes_excludes_distant_line_ref_even_if_high():
    notes = [_note("iliad.13.9", 13, 600, "alluded to in line 716 of this book")]
    kept, excluded = s1.filter_loeb_notes(notes)
    assert kept == []
    assert excluded[0]["exclusionReason"] == "distant_line_ref:716"


def test_filter_loeb_notes_excludes_curated_apparatus_only_marker():
    # iliad.17.4 is on the curated apparatus-criticus-only exclusion list
    # (pure variant-rejection notice, no English explanatory prose) even
    # though its own text carries no distant internal line reference.
    notes = [_note("iliad.17.4", 17, 545, "Line 545 was rejected by Zenodotus")]
    kept, excluded = s1.filter_loeb_notes(notes)
    assert kept == []
    assert excluded[0]["exclusionReason"] == "apparatus_criticus_only"


def test_apply_loeb_note_overrides_merges_high_note_at_correct_collision_key():
    # Mirrors the fixture collision case: book 3 has two Loeb notes, both
    # citation "1" (seqInBook 1 and 2), emitted as "3.1.1" and "3.2.1". The
    # join must land the real text on the SECOND occurrence's key without
    # touching the first, using (book, seqInBook) — not the colliding raw
    # citation number — as the join key.
    footnotes = {"3.1.1": "1", "3.2.1": "1"}
    label_by_book_seq = {(3, 1): "3.1.1", (3, 2): "3.2.1"}
    notes = [_note("odyssey.3.2", 3, 20, "Real recovered note text for the second note.")]
    report = s1.apply_loeb_note_overrides(footnotes, label_by_book_seq, notes)
    assert footnotes == {
        "3.1.1": "1",  # untouched: no shippable note -> bare-number behavior
        "3.2.1": "Real recovered note text for the second note.",
    }
    assert report["applied"] == [{"markerId": "odyssey.3.2", "label": "3.2.1"}]
    assert report["excluded"] == []
    assert report["missing"] == []


def test_apply_loeb_note_overrides_reports_missing_marker_without_inventing_a_key():
    footnotes = {"1.1.1": "1"}
    label_by_book_seq = {(1, 1): "1.1.1"}
    notes = [_note("iliad.9.9", 9, 5, "No pipeline marker exists at book 9 seq 9.")]
    report = s1.apply_loeb_note_overrides(footnotes, label_by_book_seq, notes)
    assert footnotes == {"1.1.1": "1"}
    assert report["applied"] == []
    assert report["missing"][0]["markerId"] == "iliad.9.9"


def test_apply_loeb_note_overrides_is_deterministic():
    footnotes_a = {"3.1.1": "1", "3.2.1": "1"}
    footnotes_b = dict(footnotes_a)
    label_by_book_seq = {(3, 1): "3.1.1", (3, 2): "3.2.1"}
    notes = [
        _note("odyssey.3.1", 3, 5, "First note text."),
        _note("odyssey.3.2", 3, 20, "Second note text."),
    ]
    report_a = s1.apply_loeb_note_overrides(footnotes_a, label_by_book_seq, notes)
    report_b = s1.apply_loeb_note_overrides(footnotes_b, label_by_book_seq, notes)
    assert footnotes_a == footnotes_b
    assert report_a == report_b


def test_load_loeb_notes_returns_none_for_a_work_with_no_file():
    assert s1.load_loeb_notes("not-a-real-work") is None


# --- Dead-marker stripping (markers with no recovered note must not ship) ---


def test_marker_without_kept_seq_is_stripped_from_prose_and_footnotes():
    """A marker whose (book, seqInBook) is NOT in kept_seqs_by_book must not
    appear in the prose at all (no [^label]), must not be in the footnotes
    map, and must not be in label_by_book_seq -- honest absence, not a live
    marker whose popup would show only the bare Loeb citation number. Book 4
    of tiny.xml has two same-citation-number Loeb notes (seq 1 and seq 2);
    keeping only seq 2 exercises both the strip and the keep in one book."""
    parsed = s1.parse_translation(
        FIXTURE, VALID_LINES, [4], extract_footnotes=True,
        kept_seqs_by_book={4: {2}},
    )
    text = parsed["chunks"][4]["text"]
    assert "[^4.1.1]" not in text
    assert "[^4.2.1]" in text
    assert parsed["footnotes"] == {"4.2.1": "1"}
    assert parsed["label_by_book_seq"] == {(4, 2): "4.2.1"}
    stripped = [a for a in parsed["anomalies"] if a["kind"] == "note_marker_stripped_no_recovery"]
    assert stripped == [{"kind": "note_marker_stripped_no_recovery", "book": 4, "seq": 1, "raw": "1"}]
    # The stripped note's tail text is still real prose, not dropped.
    assert "First page's opening line. More text follows." in text


def test_kept_seqs_by_book_none_keeps_every_marker_pre_fix_behavior():
    """No filtering info (kept_seqs_by_book=None, e.g. a work with no
    loeb-notes audit file) must reproduce the original unfiltered
    behavior -- every marker survives with the bare-number placeholder."""
    parsed = s1.parse_translation(FIXTURE, VALID_LINES, [4], extract_footnotes=True)
    text = parsed["chunks"][4]["text"]
    assert "[^4.1.1]" in text and "[^4.2.1]" in text
    assert parsed["footnotes"] == {"4.1.1": "1", "4.2.1": "1"}


def test_kept_seqs_empty_set_strips_every_marker_in_that_book():
    parsed = s1.parse_translation(
        FIXTURE, VALID_LINES, [4], extract_footnotes=True,
        kept_seqs_by_book={4: set()},
    )
    text = parsed["chunks"][4]["text"]
    assert "[^" not in text
    assert parsed["footnotes"] == {}
    assert parsed["label_by_book_seq"] == {}


def test_stripped_marker_pipeline_end_to_end_with_real_filter_and_join():
    """Ties filter_loeb_notes -> kept_by_book -> parse_translation
    stripping -> apply_loeb_note_overrides together, mirroring run()'s
    actual sequencing: the medium-confidence note (seq 1) never reaches
    the prose at all, and the high-confidence note (seq 2) both survives
    and gets its real text joined in, with no 'missing' report entry."""
    notes = [
        _note("fixture.4.1", 4, 1, "Filtered out (medium).", confidence="medium"),
        _note("fixture.4.2", 4, 2, "Real recovered note for the second marker.", confidence="high"),
    ]
    kept, _excluded = s1.filter_loeb_notes(notes)
    kept_by_book: dict[int, set[int]] = {}
    for n in kept:
        kept_by_book.setdefault(n["book"], set()).add(int(n["markerId"].rsplit(".", 1)[-1]))
    parsed = s1.parse_translation(
        FIXTURE, VALID_LINES, [4], extract_footnotes=True, kept_seqs_by_book=kept_by_book,
    )
    text = parsed["chunks"][4]["text"]
    assert "[^4.1.1]" not in text
    assert "[^4.2.1]" in text
    report = s1.apply_loeb_note_overrides(parsed["footnotes"], parsed["label_by_book_seq"], notes)
    assert report["missing"] == []
    assert parsed["footnotes"] == {"4.2.1": "Real recovered note for the second marker."}
