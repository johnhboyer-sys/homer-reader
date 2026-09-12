"""The Kosmos Society revision of Butler (stage1_kosmos): every book of both
poems survives extraction verbatim, every note is carried, and every verse
group maps to Greek lines that exist.

The round trip is checked against an independent reading of the vendored
source: the book's HTML with tags stripped (a regex, not the stage's parser),
minus the page furniture the stage leaves out on purpose (per-book credit,
"Return to top", date stamps, "__", the Notes block) and minus the printed
line numbers, which the stage turns into ticks and marks rather than text.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

from homer_pipeline import stage1_kosmos as k
from homer_pipeline.config import Manifest

ROOT = Path(__file__).resolve().parents[2]
WORKS = ("Iliad", "Odyssey")


def _source_books(work: str) -> dict[int, str]:
    page = (ROOT / "sources" / "kosmos" / f"homeric-{work.lower()}.html").read_text(encoding="utf-8")
    heads = [(int(m.group(1)), m.start(), m.end())
             for m in re.finditer(r"<h2[^>]*>.*?Rhapsody\s+(\d+)\s*</h2>", page, re.S)]
    out = {}
    for i, (n, _s, e) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else min(
            p for p in (page.find("<h2", e), page.find('<div class="sharedaddy', e)) if p > 0)
        out[n] = page[e:end]
    return out


def _norm(s: str) -> str:
    return " ".join(s.split())


def _source_text(book_html: str) -> str:
    body = book_html.split("<strong>Notes</strong>")[0]
    body = re.sub(r'<p align="center">.*?</p>', " ", body, flags=re.S)             # credit
    body = re.sub(r"<p>(?:(?!</p>).)*Return to top(?:(?!</p>).)*</p>", " ", body, flags=re.S)
    body = re.sub(r'<a href="#\d+fn\d+">.*?</a>', " ", body, flags=re.S)             # note refs
    body = re.sub(r"<sub>.*?</sub>", " ", body, flags=re.S)                          # sub numbers
    # Block tags separate words; inline tags (<em>, <span>) do not.
    body = re.sub(r"</?(?:p|br)\b[^>]*>", " ", body)
    text = html.unescape(re.sub(r"<[^>]+>", "", body))
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)                                      # [N] numbers
    text = re.sub(r"(?m)^\s*(\d{4}-\d{2}-\d{2}|__)\s*$", " ", text)
    return _norm(text)


def _extracted_text(text: str) -> str:
    return _norm(re.sub(r"\[\^kosmos\.\d+\.\d+\]", " ", text))


@pytest.fixture(scope="module")
def parsed():
    return {w: k.parse_work(Manifest.for_work(w)) for w in WORKS}


def _no_space_norm(s: str) -> str:
    # Marker removal can leave a space before punctuation on one side only
    # ("fell— [5] and" vs a sub number glued to a word); compare with every
    # whitespace run removed as well as normalised.
    return re.sub(r"\s+", "", s)


@pytest.mark.parametrize("work", WORKS)
def test_every_book_round_trips(parsed, work):
    src = _source_books(work)
    assert sorted(parsed[work]) == list(range(1, 25))
    failures = []
    for b in range(1, 25):
        got = _extracted_text(parsed[work][b]["text"])
        want = _source_text(src[b])
        if _no_space_norm(got) != _no_space_norm(want):
            i = next(i for i, (x, y) in enumerate(zip(_no_space_norm(got), _no_space_norm(want))) if x != y)
            failures.append(f"{work} {b}: first difference near …{_no_space_norm(want)[max(0, i - 40):i + 40]}…")
    assert failures == []


@pytest.mark.parametrize("work", WORKS)
def test_whitespace_is_collapsed_not_lost(parsed, work):
    # The space-free comparison above could hide a lost word boundary; this
    # one keeps spaces, allowing only a space that marker removal left before
    # punctuation in the independent reading.
    src = _source_books(work)
    for b in range(1, 25):
        got = _extracted_text(parsed[work][b]["text"])
        want = re.sub(r" ([,.;:!?’”—)\]])", r"\1", _source_text(src[b]))
        got = re.sub(r" ([,.;:!?’”—)\]])", r"\1", got)
        assert got == want, f"{work} {b}"


@pytest.mark.parametrize("work", WORKS)
def test_footnote_count_matches_source(parsed, work):
    src = _source_books(work)
    for b in range(1, 25):
        refs = len(re.findall(rf'href="#{b}fn\d+"', src[b]))
        notes = len(re.findall(rf'<a name="{b}fn\d+"', src[b]))
        r = parsed[work][b]
        markers = re.findall(rf"\[\^kosmos\.{b}\.(\d+)\]", r["text"])
        assert len(markers) == refs == notes == len(r["notes"]), f"{work} {b}"
        assert sorted(f"kosmos.{b}.{m}" for m in markers) == sorted(r["notes"])


@pytest.mark.parametrize("work", WORKS)
def test_every_group_maps_to_existing_greek_lines(parsed, work):
    lines, _gaps = k.greek_line_sets(Manifest.for_work(work))
    for b in range(1, 25):
        ticks = parsed[work][b]["bekker"]
        assert ticks[0]["offset"] == 0 and ticks[0]["n"] == min(lines[b])
        for t in ticks:
            assert t["n"] in lines[b], f"{work} {b}: tick {t['n']} has no Greek line"
            # A group needs English: its tick must sit inside the text
            # (preflight's overlay check refuses offset == len(text)).
            assert t["offset"] < len(parsed[work][b]["text"]), f"{work} {b}: tick {t['n']} opens an empty group"
        pairs = [(t["n"], t["offset"]) for t in ticks]
        assert all(a[0] < b_[0] and a[1] < b_[1] for a, b_ in zip(pairs, pairs[1:])), f"{work} {b}"


@pytest.mark.parametrize("work", WORKS)
def test_every_printed_number_is_a_break_or_a_mark(parsed, work):
    src = _source_books(work)
    for b in range(1, 25):
        body = src[b].split("<strong>Notes</strong>")[0]
        subs = len(re.findall(r"<sub>", body))
        brackets = len(re.findall(r"\[\s*\d+\s*\]", html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<sub>.*?</sub>", "", body, flags=re.S)))))
        r = parsed[work][b]
        breaks = sum(1 for t in r["bekker"] if not t.get("implied"))
        assert breaks + len(r["marks"]) == subs + brackets, f"{work} {b}"


def test_iliad_9_460_is_a_mark_in_the_declared_gap(parsed):
    marks = parsed["Iliad"][9]["marks"]
    gap = [m for m in marks if m["reason"] == "not-in-greek"]
    assert [m["n"] for m in gap] == [460]
    ticks = [t["n"] for t in parsed["Iliad"][9]["bekker"]]
    assert 455 in ticks and 465 in ticks and not any(456 <= n <= 461 for n in ticks)
    # The only printed number in either poem that names no Greek line.
    others = [(w, b, m["n"]) for w in WORKS for b in range(1, 25)
              for m in parsed[w][b]["marks"] if m["reason"] == "not-in-greek"]
    assert others == [("Iliad", 9, 460)]


def test_iliad_16_closing_867_is_a_mark(parsed):
    # Il. 16 ends "…bore Automedon swiftly from the field. [867]": the book's
    # last line number printed after its last words. No English follows it,
    # so it cannot open a group; the [865] group already runs to 867.
    r = parsed["Iliad"][16]
    assert {(m["n"], m["reason"]) for m in r["marks"]} >= {(867, "at-end")}
    assert r["bekker"][-1]["n"] == 865


def test_known_misprints_are_marks_not_breaks(parsed):
    il = parsed["Iliad"]
    assert {(m["n"], m["reason"]) for m in il[17]["marks"]} == {(95, "out-of-sequence")}
    assert (50, "out-of-sequence") in {(m["n"], m["reason"]) for m in il[18]["marks"]}
    assert [t for t in il[7]["bekker"] if t["n"] == 321][0]["label"] == "321–322"


def test_source_sentinel_character_fails_loudly():
    """shared/lib/kosmos.ts reserves U+E000-U+E005 (TR_OPEN..MARK_CLOSE) for
    the standoff markup it writes into a piece's own text; a source character
    already in that range (here, a numeric character reference the page
    happened to carry -- &#57344; decodes to U+E000) would be indistinguishable
    from one the reader generated, forging a <span class="k-tr"> or an
    unbalanced tag once it reached sentinelsToHtml. The pipeline must refuse
    this loudly rather than pass it through. Built via chr(), not a literal
    \\u escape, so this test file never itself contains the code point."""
    sentinel = chr(0xE000)
    assert ord(sentinel) == 57344
    book_html = "<p>Anger &#57344;goddess, sing it.</p>"
    with pytest.raises(ValueError, match="U\\+E000"):
        k.parse_book(1, book_html, {1, 2, 3}, set())


def test_real_sources_carry_no_sentinel_characters():
    """The current Kosmos sources contain none of these characters (verified
    directly, not just asserted) -- parse_work succeeds for both works."""
    for work in WORKS:
        k.parse_work(Manifest.for_work(work))


def test_bracket_kinds(parsed):
    text = parsed["Iliad"][1]["text"]
    kinds = {text[s:e]: kind for s, e, kind in parsed["Iliad"][1]["spans"] if kind != "em"}
    assert kinds["[mēnis]"] == "tr"
    assert kinds["[= Apollo]"] == "ed"
    assert kinds["[Agamemnon]"] == "ed"
    # Every span's text is a bracket, and brackets never overlap each other.
    for b in range(1, 25):
        r = parsed["Iliad"][b]
        br = sorted((s, e) for s, e, kind in r["spans"] if kind != "em")
        assert all(r["text"][s] == "[" and r["text"][e - 1] == "]" for s, e in br)
        assert all(a[1] <= b_[0] for a, b_ in zip(br, br[1:]))
