"""Butler's own Odyssey from the Wikisource scan (stage1_butler_wikisource):
every book is read, every printed marginal line number becomes a tick on a
Greek line that exists, every footnote is carried once, every correction is
applied, and no wikitext survives.

The round trips are checked against an independent reading of the committed
pages: a cruder regex reduction (templates to their last argument, refs cut
out) compared character for character with whitespace removed, so a dropped,
doubled or invented word fails while the stage's own spacing choices (page
joins, hyphenated words, glued note markers) do not.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

from homer_pipeline import stage1_butler_wikisource as bw
from homer_pipeline import stage1_perseus_greek
from homer_pipeline.config import SOURCES_DIR, Manifest

SRC = SOURCES_DIR / "butler" / "wikisource" / "odyssey"
MARKUP = ("{{", "}}", "<ref", "[[", "<section", "<noinclude", "<pages")
MARKER = re.compile(r"\[\^butler\.(\d+)\.(\d+)\]")


@pytest.fixture(scope="module")
def manifest():
    return Manifest.for_work("Odyssey")


@pytest.fixture(scope="module")
def spine_lines(manifest):
    spine = stage1_perseus_greek.parse_spine(
        SOURCES_DIR / manifest.data["work"]["greek_source"], manifest)
    return {s["book"]: {l["n"] for l in s["lines"]} for s in spine["segments"]}


@pytest.fixture(scope="module")
def parsed(manifest, spine_lines):
    return bw.parse_work(manifest, spine_lines)


def _book_pages(book: int) -> list[str]:
    """Page bodies (sections applied) in wrapper order, plates left out."""
    wrapper = (SRC / f"book-{book:02d}.wiki").read_text(encoding="utf-8")
    out = []
    for page, fsec, tsec in bw.parse_wrapper(wrapper):
        body = bw.page_body((SRC / f"page-{page:03d}.wiki").read_text(encoding="utf-8"), fsec, tsec)
        if "[[File:" not in body:
            out.append(body)
    return out


def _all_wrapper_pages() -> list[str]:
    return [p for b in range(1, 25) for p in _book_pages(b)]


def _plain(text: str) -> str:
    """Independent reduction: corrections applied, templates to their last
    argument (layout ones to nothing), links to their label."""
    text = re.sub(r"\{\{errata\|[^{}|]*\|([^{}|]*)[^{}]*\}\}", r"\1", text)
    text = text.replace("{{SIC|no man|Noman}}", "no man")    # SIC_KEEP_PRINTED
    text = re.sub(r"\{\{(?:SIC|sic)\|[^{}|]*\|([^{}|]*)\}\}", r"\1", text)
    text = re.sub(r"\{\{(?:SIC|sic)\}\}", "", text)
    text = re.sub(r"\{\{Tooltip\|([^{}|]*)\|[^{}]*\}\}", r"\1", text)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    drop = {"pline", "ph", "dhr", "nop", "rule", "smallrefs", "rh", "c", "center block",
            "hwe", "gap", "parabr"}

    def red(m):
        parts = m.group(1).split("|")
        name = parts[0].strip()
        if name in drop:
            return ""
        if name == "...":
            return "…"
        if name == "fqm":
            return '"'
        if name in ('" \'', "' \""):
            return name.replace(" ", "")
        return parts[-1] if len(parts) > 1 else ""

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{([^{}]*)\}\}", red, text)
    text = re.sub(r"</?P>|<br\s*/?>", "", text)
    return text.replace("''", "")


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", s)


def test_twenty_four_books(parsed):
    assert sorted(parsed["books"]) == list(range(1, 25))
    assert all(r["text"] for r in parsed["books"].values())


def test_pline_count_matches_the_source(parsed):
    # Every {{pline}} on the wrapper pages, counted by grep. The Odyssey has
    # no page-break duplicates (that rule bites in the Iliad, 14.445).
    grep = sum(len(re.findall(r"\{\{pline\|", p)) for p in _all_wrapper_pages())
    assert grep == 1021
    assert sum(r["plines_printed"] for r in parsed["books"].values()) == grep
    assert sum(r["plines_distinct"] for r in parsed["books"].values()) == grep
    kinds = {a["kind"] for a in parsed["log"]["anomalies"]}
    assert "pline_page_break_duplicate" not in kinds


def test_tick_count_per_book(parsed):
    # ticks = distinct plines + the line-1 book start (no book prints a 1)
    # - the closing line number some books print after their last words.
    after_last = {}
    for a in parsed["log"]["anomalies"]:
        if a["kind"] == "pline_after_last_words":
            after_last[a["book"]] = after_last.get(a["book"], 0) + 1
    assert sum(after_last.values()) == 21
    for b, r in parsed["books"].items():
        assert r["bekker"][0] == {"n": 1, "offset": 0, "real": True}
        assert len(r["bekker"]) == r["plines_distinct"] + 1 - after_last.get(b, 0), b


def test_only_expected_anomalies(parsed):
    kinds = {a["kind"] for a in parsed["log"]["anomalies"]}
    assert kinds == {"pline_after_last_words"}


def test_ticks_strictly_increase_after_errata(parsed):
    for b, r in parsed["books"].items():
        ns = [t["n"] for t in r["bekker"]]
        offs = [t["offset"] for t in r["bekker"]]
        assert ns == sorted(set(ns)), b
        assert offs == sorted(set(offs)), b
    applied = {(e["book"], e["printed"], e["correct"]) for e in parsed["log"]["pline_errata_applied"]}
    assert applied == {(4, 245, 425), (15, 169, 179)}
    assert 425 in [t["n"] for t in parsed["books"][4]["bekker"]]
    assert 179 in [t["n"] for t in parsed["books"][15]["bekker"]]


def test_every_tick_on_a_spine_line(parsed, spine_lines):
    for b, r in parsed["books"].items():
        missing = [t["n"] for t in r["bekker"] if t["n"] not in spine_lines[b]]
        assert not missing, (b, missing)


def test_tick_offsets_open_the_pline_paragraph(parsed):
    """Each tick sits at a paragraph start, and the words there are the words
    that follow that {{pline}} in the source."""
    errata = {(e["book"], e["printed"], e["occurrence"]): e["correct"] for e in bw.load_errata()}
    checked = 0
    for b, r in parsed["books"].items():
        text = r["text"]
        by_n = {t["n"]: t["offset"] for t in r["bekker"]}
        for t in r["bekker"]:
            assert t["offset"] == 0 or text[t["offset"] - 1] == "\n", (b, t)
        seen: dict[int, int] = {}
        for page in _book_pages(b):
            for m in re.finditer(r"\{\{pline\|(\d+)\|l[^}]*\}\}\n*([^{<\n]{0,30})", page):
                printed = int(m.group(1))
                seen[printed] = seen.get(printed, 0) + 1
                n = errata.get((b, printed, seen[printed]), printed)
                lead = m.group(2)
                if n not in by_n or len(lead) < 10:
                    continue      # closing number, or a template right after it
                assert text[by_n[n]:by_n[n] + len(lead)] == lead, (b, n, lead)
                checked += 1
    assert checked >= 940      # the rest open with a template ({{" '}}, {{sc}}, …)


def test_no_markup_survives(parsed):
    for b, r in parsed["books"].items():
        for t in (r["text"], *r["notes"].values()):
            for bad in MARKUP:
                assert bad not in t, (b, bad, t[max(0, t.find(bad) - 40):t.find(bad) + 40])
        assert "''" not in r["text"]


def test_book_one_opening(parsed):
    t = parsed["books"][1]["text"]
    assert t.startswith("Tell me, oh Muse, of that ingenious hero")
    assert "daughter of Jove" in t
    assert "[noos]" not in t
    assert "FOR ENGLISH READERS" not in t and "BOOK I" not in t
    assert "\n" in t                                   # paragraphs kept


def test_errata_and_sic_applied(parsed):
    log = parsed["log"]
    raw = "".join((SRC / f"page-{p:03d}.wiki").read_text(encoding="utf-8")
                  for p in range(25, 360))
    assert len(log["errata"]) == len(re.findall(r"\{\{errata\|", raw)) == 8
    assert len(log["sic"]) == len(re.findall(r"\{\{(?:SIC|sic)\|", raw)) == 15
    assert len(log["sic_bare"]) == len(re.findall(r"\{\{(?:SIC|sic)\}\}", raw)) == 1
    assert len(log["tooltips"]) == len(re.findall(r"\{\{Tooltip\|", raw)) == 4
    assert [e["page"] for e in log["sic"] if e["in_plate"]] == [288]
    for e in log["errata"] + [e for e in log["sic"] if not e["in_plate"]]:
        r = parsed["books"][e["book"]]
        where = r["text"] + "".join(html.unescape(v) for v in r["notes"].values())
        assert e["applied"] in where, e
    t9 = parsed["books"][9]["text"]
    assert "Noman is killing me by fraud; no man is killing me by force" in t9
    kept = [e for e in log["sic"] if e["applied"] == e["printed"]]
    assert [(e["book"], e["page"], e["printed"]) for e in kept] == [(9, 152, "no man")]
    assert "deal rigorously with me" in parsed["books"][2]["text"]


def test_footnotes_one_per_butler_note(parsed):
    pages = _all_wrapper_pages()
    opened = sum(len(re.findall(r"<ref(?:>|\s+name=)", p)) for p in pages)
    follows = sum(len(re.findall(r"<ref\s+follow=", p)) for p in pages)
    assert (opened, follows) == (191, 6)
    notes = {k: v for r in parsed["books"].values() for k, v in r["notes"].items()}
    assert len(notes) + len(parsed["log"]["argument_notes"]) == opened
    for b, r in parsed["books"].items():
        ks = [int(m.group(2)) for m in MARKER.finditer(r["text"])]
        assert all(int(m.group(1)) == b for m in MARKER.finditer(r["text"]))
        assert ks == list(range(1, len(ks) + 1)), b
        assert set(r["notes"]) == {f"butler.{b}.{k}" for k in ks}
        assert not re.search(r"\s\[\^butler", r["text"])          # glued to its word
    # A note continued across a page break is one note, both halves kept.
    p54 = parsed["books"][4]["notes"]["butler.4.13"]
    assert p54.startswith("<p>I give the usual translation") and "Come cavalca bene" in p54


def test_prose_round_trip(parsed):
    for b, r in parsed["books"].items():
        src = "".join(_book_pages(b))
        src = re.sub(r"<noinclude>.*?</noinclude>", "", src, flags=re.S)
        src = re.sub(r"<ref[^>]*>.*?</ref>", "", src, flags=re.S)
        src = _plain(src)
        out = MARKER.sub("", r["text"])
        assert _squash(out) == _squash(src), b


def test_notes_round_trip(parsed):
    for b, r in parsed["books"].items():
        src = "".join(_book_pages(b))
        refs = [m.group(1) for m in re.finditer(r"<ref[^>]*>(.*?)</ref>", src, flags=re.S)]
        out = "".join(html.unescape(re.sub(r"<[^>]+>", "", v)) for v in r["notes"].values())
        out += "".join(html.unescape(re.sub(r"<[^>]+>", "", a["html"]))
                       for a in parsed["log"]["argument_notes"] if a["book"] == b)
        assert sorted(_squash(out)) == sorted(_squash(_plain("".join(refs)))), b


def test_arguments_recorded_not_emitted(parsed):
    args = parsed["log"]["arguments"]
    assert sorted(args) == list(range(1, 25))
    assert args[1].startswith("THE GODS IN COUNCIL")
    for b, r in parsed["books"].items():
        assert args[b] not in r["text"]
    assert [a["book"] for a in parsed["log"]["argument_notes"]] == [11]


def test_plates_dropped(parsed):
    assert [(p["book"], p["page"]) for p in parsed["log"]["plates_dropped"]] == [
        (3, 63), (5, 99), (6, 109), (9, 139), (9, 146), (19, 288)]
    assert "SALT WORKS" not in parsed["books"][5]["text"]


def test_run_writes_ross_chunks_shape(manifest, spine_lines, tmp_path, monkeypatch):
    monkeypatch.setattr(bw, "BUILD_DIR", tmp_path)
    spine = {"segments": [{"id": f"{b}:{b}", "book": b, "lines": [{"n": n} for n in sorted(ns)]}
                          for b, ns in sorted(spine_lines.items())]}
    summary = bw.run(manifest, spine)
    import json
    ross = json.loads((tmp_path / "stage1" / "ross_chunks.json").read_text(encoding="utf-8"))
    notes = json.loads((tmp_path / "stage1" / "butler_footnotes.json").read_text(encoding="utf-8"))
    assert sorted(ross) == sorted(f"{b}:{b}" for b in range(1, 25))
    piece = ross["1:1"]
    assert len(piece) == 1 and set(piece[0]) == {"chapter", "text", "cont", "bekker"}
    assert piece[0]["chapter"] == "1" and piece[0]["cont"] is False
    assert summary["footnotes"] == len(notes) == 190
    assert summary["books"] == 24 and summary["plines_distinct"] == 1021
