"""Stage 1e: milestoned Perseus English (Murray/Butler) — the milestone parser,
anomaly handling, footnote extraction, and paragraph-preservation round-trip.
"""

from __future__ import annotations

from pathlib import Path

from homer_pipeline import stage1_perseus_milestone_english as s1

FIXTURE = Path(__file__).parent / "fixtures" / "perseus_milestone_english" / "tiny.xml"
DEFECTS_FIXTURE = Path(__file__).parent / "fixtures" / "perseus_milestone_english" / "defects.xml"

# Book 1: no vulgate gap. Book 2: line 4 is a vulgate gap (3 -> 5).
VALID_LINES = {1: {1, 2, 3, 4, 5}, 2: {1, 2, 3, 5, 6}}

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
    parsed = _parse(extract_footnotes=True)
    assert parsed["footnotes"] == {"1.1": "1"}
    text = parsed["chunks"][1]["text"]
    assert "[^1.1]" in text
    # The note's own content ("1") isn't left dangling in the prose stream.
    assert "the wrath.1 Of" not in text
    assert "the wrath.[^1.1] Of Peleus" in text


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
    marker_pos = text.index("[^3.1]")
    assert chunk["notes"] == [{"offset": marker_pos, "text": "1"}]
    # Rendered text is untouched — still exactly one space before the marker.
    assert text[marker_pos - 1] == " "
    assert text[marker_pos - 2] != " "


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
