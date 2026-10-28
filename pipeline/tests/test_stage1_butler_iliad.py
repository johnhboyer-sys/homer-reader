"""Butler's own Iliad (stage1_butler_iliad): the Wikisource scan to XIV.485,
Gutenberg #2199 from XIV.486 to the end. Every book is read, every printed
number becomes a tick on a Greek line that exists, every footnote is carried
once, every correction is applied or listed, the seam in Book XIV loses and
doubles nothing, and no wikitext or Gutenberg boilerplate survives.

The Greek here is the Perseus Monro–Allen text (perseus-grc2), which is in
the repository. The real Iliad spine is TLG Allen 1931 (stage1_tlg_iliad,
licensed, not in the repository), which lacks 8.548 and 8.550-552 where
Perseus supplies them (manifests/Iliad.yaml); a tick on one of those lines
would be on a line the real spine lacks, so the test forbids them too.
"""

from __future__ import annotations

import html
import json
import re

import pytest

from homer_pipeline import stage1_butler_iliad as bi
from homer_pipeline import stage1_butler_wikisource as bw
from homer_pipeline import stage1_perseus_greek
from homer_pipeline.config import SOURCES_DIR, Manifest

SRC = SOURCES_DIR / "butler" / "wikisource" / "iliad"
GUT = SOURCES_DIR / "butler" / "butler-iliad.txt"
MARKUP = ("{{", "}}", "<ref", "[[", "<noinclude", "<section", "<pages")
BOILERPLATE = ("Project Gutenberg", "PROJECT GUTENBERG", "*** START", "*** END", "Gutenberg")
MARKER = re.compile(r"\[\^butler\.(\d+)\.(\d+)\]")
TLG_LACKS = {8: {548, 550, 551, 552}}


@pytest.fixture(scope="module")
def manifest():
    return Manifest.for_work("Iliad")


@pytest.fixture(scope="module")
def spine_lines(manifest):
    spine = stage1_perseus_greek.parse_spine(
        SOURCES_DIR / manifest.data["work"]["greek_source"], manifest)
    return {s["book"]: {l["n"] for l in s["lines"]} for s in spine["segments"]}


@pytest.fixture(scope="module")
def parsed(manifest, spine_lines):
    return bi.parse_work(manifest, spine_lines)


@pytest.fixture(scope="module")
def pages():
    return bi.book_pages(SRC)


@pytest.fixture(scope="module")
def gut():
    return bi.gutenberg_books(GUT)


def _body(page: int) -> str:
    return bw.page_body((SRC / f"page-{page:03d}.wiki").read_text(encoding="utf-8"), None, None)


def _anoms(parsed, kind, book=None):
    return [a for a in parsed["log"]["anomalies"]
            if a["kind"] == kind and (book is None or a["book"] == book)]


def test_twenty_four_books(parsed, pages):
    assert sorted(parsed["books"]) == list(range(1, 25))
    assert all(r["text"] for r in parsed["books"].values())
    assert sorted(pages) == list(range(1, 15))
    assert pages[1][0] == 21 and pages[14][-1] == 256


def test_scan_tick_counts_tied_to_the_source(parsed, pages):
    """Per scan book: the {{pline}} grep, plus the numbers the level-1 fixes
    restore from bare OCR digits, less the page-foot numbers dropped and the
    page-break duplicate, is the count of distinct numbers; ticks are those
    plus the line-1 book start (no book prints a 1)."""
    restored = {}
    for page, old, new, _ in bi.SCAN_FIXES:
        restored[page] = restored.get(page, 0) + new.count("{{pline|") - old.count("{{pline|")
    total = 0
    for b, ps in pages.items():
        grep = sum(len(re.findall(r"\{\{pline\|", _body(p))) for p in ps)
        grep += sum(restored.get(p, 0) for p in ps)
        dropped = len(_anoms(parsed, "pline_page_foot_dropped", b))
        dup = len(_anoms(parsed, "pline_page_break_duplicate", b))
        r = parsed["books"][b]
        assert r["plines_distinct"] == grep - dropped - dup, b
        assert r["plines_printed"] == r["plines_distinct"], b
        scan_ticks = parsed["log"]["tick_sources"][b]["scan"]
        assert scan_ticks == r["plines_distinct"] + 1, b
        assert r["bekker"][0] == {"n": 1, "offset": 0, "real": True}
        total += r["plines_distinct"]
    assert total == 638 + 4 - 5 - 1 == 636
    # Book XIV's page-foot numbers, and the one duplicate (14.445, pp. 255-256).
    assert [(a["page"], a["n_raw"]) for a in _anoms(parsed, "pline_page_foot_dropped")] == [
        (245, 67), (247, 146), (249, 221), (251, 296), (256, 486)]
    assert [(a["page"], a["n_raw"]) for a in _anoms(parsed, "pline_page_break_duplicate")] == [
        (255, 445)]
    assert {a["kind"] for a in parsed["log"]["anomalies"]} == {
        "pline_page_foot_dropped", "pline_page_break_duplicate", "pline_mid_paragraph",
        "pline_gap_snap"}
    # 14.269 is not in the vulgate text; Butler's 269 opens the line after.
    assert [(a["n_raw"], a["snapped_to"]) for a in _anoms(parsed, "pline_gap_snap")] == [(269, 270)]


def test_pline_errata_applied(parsed):
    # Each checked against the Greek; see sources/butler/pline-errata.yaml.
    assert parsed["log"]["pline_errata_applied"] == [
        {"book": 2, "printed": 811, "occurrence": 1, "correct": 807},
        {"book": 7, "printed": 445, "occurrence": 1, "correct": 454},
        {"book": 10, "printed": 312, "occurrence": 1, "correct": 313},
        {"book": 12, "printed": 387, "occurrence": 1, "correct": 378},
        {"book": 13, "printed": 582, "occurrence": 1, "correct": 581},
        {"book": 13, "printed": 743, "occurrence": 1, "correct": 748}]
    ns7 = [t["n"] for t in parsed["books"][7]["bekker"]]
    assert 454 in ns7 and 445 not in ns7
    ns = [t["n"] for t in parsed["books"][2]["bekker"]]
    assert 807 in ns and ns.count(811) == 1


def test_ticks_strictly_increase(parsed):
    for b, r in parsed["books"].items():
        ns = [t["n"] for t in r["bekker"]]
        offs = [t["offset"] for t in r["bekker"]]
        assert ns == sorted(set(ns)), b
        assert offs == sorted(set(offs)), b
        assert offs[0] == 0 and ns[0] == 1, b
        assert offs[-1] < len(r["text"]), b
        assert all(t["real"] is True for t in r["bekker"])
        text = r["text"]
        assert all(not text[t["offset"]].isspace() for t in r["bekker"]), b


def test_every_tick_on_a_spine_line(parsed, spine_lines):
    for b, r in parsed["books"].items():
        missing = [t["n"] for t in r["bekker"] if t["n"] not in spine_lines[b]]
        assert not missing, (b, missing)
        assert not {t["n"] for t in r["bekker"]} & TLG_LACKS.get(b, set()), b


def test_rule_ticks_open_gutenberg_paragraphs(parsed):
    """From the join on, every tick sits at a paragraph start."""
    for b in range(14, 25):
        r = parsed["books"][b]
        start = len("\n".join(r["text"].split("\n")[:37])) + 1 if b == 14 else 0
        for t in r["bekker"]:
            if t["offset"] >= start:
                assert t["offset"] == 0 or r["text"][t["offset"] - 1] == "\n", (b, t)
    src = parsed["log"]["tick_sources"]
    for b in range(15, 25):
        assert src[b] == {"perseus_rule": len(parsed["books"][b]["bekker"])}, b


def test_no_markup_or_boilerplate_survives(parsed):
    for b, r in parsed["books"].items():
        for t in (r["text"], *r["notes"].values()):
            for bad in MARKUP + BOILERPLATE:
                assert bad not in t, (b, bad, t[max(0, t.find(bad) - 40):t.find(bad) + 40])
        text = r["text"]
        assert "''" not in text and "--" not in text and "  " not in text, b
        assert not re.search(r"\d", MARKER.sub("", text).replace("(see line 21)", "")), b
        assert not re.search(r"^BOOK [IVXL]+", text, re.M), b
        assert parsed["log"]["arguments"][b] not in text, b


def test_book_one_opening(parsed):
    t = parsed["books"][1]["text"]
    assert t.startswith("Sing, O goddess, the anger of Achilles son of Peleus")
    assert "Sing, O goddess, the anger of Achilles" in t
    assert "counsels of Jove" in t
    assert "[mênis]" not in t and "mênis" not in t
    assert "THE ILIAD OF HOMER" not in t
    assert "\n" in t
    assert parsed["log"]["furniture_dropped"] == [{"book": 1, "text": "THE ILIAD OF HOMER"}]


def test_last_words(parsed):
    t = parsed["books"][24]["text"]
    assert t.endswith("\nThus, then, did they celebrate the funeral of Hector tamer of horses.")


def test_join_in_book_fourteen(parsed, gut):
    """The scan's last paragraph is Gutenberg's paragraph 37 word for word;
    Gutenberg's paragraphs 38 on follow, once each, and Book XIV has exactly
    Gutenberg's paragraph count, so nothing is lost or doubled."""
    j = parsed["log"]["join"]
    assert (j["book"], j["gutenberg_paragraph"], j["first_rule_tick"]) == (14, 37, 486)
    text = parsed["books"][14]["text"]
    paras = text.split("\n")
    g = gut[14]["paras"]
    assert len(paras) == len(g) == 40
    for k in range(40):
        assert bi.norm_words(paras[k])[:4] == bi.norm_words(g[k])[:4], k
    assert bi.norm_words(paras[36]) == bi.norm_words(g[36])
    assert paras[37:] == g[37:]
    assert paras[36].endswith("to avenge his fall.”")
    assert paras[37].startswith("His taunts infuriated the Argives")
    tick = [t for t in parsed["books"][14]["bekker"] if t["n"] == 486]
    assert tick and text[tick[0]["offset"]:].startswith("His taunts")
    # No tick in the Gutenberg part repeats a scan number.
    assert parsed["log"]["tick_sources"][14] == {"scan": 49, "perseus_rule": 3}


def test_gutenberg_books_are_gutenberg_words(parsed, gut):
    for b in range(15, 25):
        r = parsed["books"][b]
        assert bi.norm_words(r["text"]) == bi.norm_words("\n".join(gut[b]["paras"])), b
        assert r["text"].count("\n") + 1 == len(gut[b]["paras"]), b
        assert r["notes"] == {}
    # PG's capitals for the print's small capitals are set in ordinary case.
    assert parsed["books"][15]["text"].startswith("But when their flight")
    assert parsed["books"][17]["text"].startswith("Brave Menelaus")
    assert parsed["books"][20]["text"].startswith("Thus, then, did the Achaeans")


def test_missing_notes_recorded(parsed):
    missing = parsed["log"]["books_missing_notes"]
    assert [m["book"] for m in missing] == list(range(14, 25))
    assert missing[0] == {"book": 14, "from_line": 486, "whole_book": False}
    assert all(m["whole_book"] for m in missing[1:])


def test_corrections_accounted_for(parsed):
    log = parsed["log"]
    raw = "".join(_body(p) for p in range(bi.SCAN_FIRST, bi.SCAN_LAST + 1))
    assert len(log["errata"]) == len(re.findall(r"\{\{errata\|", raw)) == 0
    assert len(log["sic"]) == len(re.findall(r"\{\{(?:SIC|sic)\|[^{}|]*\|", raw)) == 8
    one_arg = re.findall(r"\{\{(?:SIC|sic)\|[^{}|]*\}\}", raw)
    bare = re.findall(r"\{\{(?:SIC|sic)\}\}", raw)
    assert len(log["sic_bare"]) == len(one_arg) + len(bare) == 1
    assert len(log["tooltips"]) == len(re.findall(r"\{\{Tooltip\|", raw)) == 0
    for e in log["sic"]:
        r = parsed["books"][e["book"]]
        where = r["text"] + "".join(html.unescape(v) for v in r["notes"].values())
        assert e["applied"] in where and e["applied"] != e["printed"], e
    assert {(e["page"], e["printed"], e["applied"]) for e in log["sic"]} >= {
        (37, "thinkiug", "thinking"), (235, "Alphareus", "Aphareus")}
    # {{SIC|'}} (p. 122) flags a stray printed quote and offers no reading.
    assert log["sic_bare"][0]["page"] == 122 and log["sic_bare"][0]["printed"] == "'"
    assert "mother's heart be glad.'\"" in parsed["books"][6]["text"]
    # Every scan fix applied exactly once (parse_work fails otherwise).
    assert len(log["scan_fixes"]) == len(bi.SCAN_FIXES)
    t14 = parsed["books"][14]["text"]
    for bad in ("CEneus", "QSneus", "Achseans", "Bmathia", "Oymindis", "cna", "snet", "hlep",
                "HECTOR LEADS", "[iuad", "Satniödeis"):
        assert bad not in t14, bad
    assert "the knight Œneus" in t14 and "Satniöeis" in t14


def test_footnotes_one_per_butler_note(parsed):
    raw = "".join(_body(p) for p in range(bi.SCAN_FIRST, bi.SCAN_LAST + 1))
    opened = len(re.findall(r"<ref(?:>|\s+name=)", raw))
    follows = len(re.findall(r"<ref\s+follow=", raw))
    assert (opened, follows) == (16, 0)
    notes = {k: v for r in parsed["books"].values() for k, v in r["notes"].items()}
    assert len(notes) == opened and not parsed["log"]["argument_notes"]
    for b, r in parsed["books"].items():
        ks = [int(m.group(2)) for m in MARKER.finditer(r["text"])]
        assert all(int(m.group(1)) == b for m in MARKER.finditer(r["text"]))
        assert ks == list(range(1, len(ks) + 1)), b
        assert set(r["notes"]) == {f"butler.{b}.{k}" for k in ks}
        assert not re.search(r"\s\[\^butler", r["text"])
    assert notes["butler.13.2"] == "This paragraph is generally suspected."


def _plain(text: str) -> str:
    """Independent reduction of a scan page: corrections applied, templates to
    their last argument (layout ones to nothing), links to their label."""
    text = re.sub(r"\{\{(?:SIC|sic)\|[^{}|]*\|([^{}|]*)\}\}", r"\1", text)
    text = re.sub(r"\{\{(?:SIC|sic)\|([^{}|]*)\}\}", r"\1", text)
    drop = {"pline", "dhr", "nop", "hwe", "smallrefs"}

    def red(m):
        parts = m.group(1).split("|")
        name = parts[0].strip()
        if name in drop:
            return ""
        if name == "hws":
            return parts[2]
        return parts[-1] if len(parts) > 1 else ""

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{([^{}]*)\}\}", red, text)
    return text.replace("''", "")


def test_scan_prose_round_trip(parsed, pages):
    """Books I-XIII against a cruder reading of the committed pages (heading
    and argument paragraphs cut, notes cut), whitespace ignored."""
    for b in range(1, 14):
        src = ""
        for i, p in enumerate(pages[b]):
            body = _body(p)
            if i == 0:
                body = "\n\n".join(re.split(r"\n[ \t]*\n", body.strip())[2:])
            src += body
        src = re.sub(r"<ref[^>]*>.*?</ref>", "", src, flags=re.S)
        out = MARKER.sub("", parsed["books"][b]["text"])
        assert re.sub(r"\s+", "", out) == re.sub(r"\s+", "", _plain(src)), b


def test_rule_measured_on_butlers_own_numbers(parsed, gut, pages):
    """Phase A, pinned: on Books III-XIII the Perseus rule against Butler's
    printed numbers (paragraph by paragraph; scan and Gutenberg paragraphs
    pair one to one there)."""
    pers = bi.perseus_books(SOURCES_DIR / "perseus" / "tlg0012.tlg001.perseus-eng4.xml")
    both = butler_n = rule_n = rejected = 0
    for b in range(3, 14):
        r = parsed["books"][b]
        assert r["text"].count("\n") + 1 == len(gut[b]["paras"]), b
        starts = [0] + [i + 1 for i, c in enumerate(r["text"]) if c == "\n"]
        butler = {(t["n"], starts.index(t["offset"])) for t in r["bekker"] if t["n"] != 1}
        res = bi.rule_numbers(pers[b], gut[b]["paras"])
        rule = {(n, k) for n, k in res["ticks"] if n != 1}
        both += len(butler & rule)
        butler_n += len(butler)
        rule_n += len(rule)
        # Perseus's own extra <p> breaks, inside Butler's paragraphs: never
        # one of his printed numbers.
        rejected += len(res["rejected"])
        assert not set(res["rejected"]) & {n for n, _ in butler}, b
    # Against Butler's numbers with his misprints corrected (pline-errata):
    # 451 of 453 reproduced (0.996), 451 of 455 rule numbers his (0.991).
    assert (both, butler_n, rule_n, rejected) == (451, 453, 455, 95)
    assert both / butler_n >= 0.97 and both / rule_n >= 0.97


def test_run_writes_ross_chunks_shape(manifest, spine_lines, tmp_path, monkeypatch):
    monkeypatch.setattr(bi, "BUILD_DIR", tmp_path)
    spine = {"segments": [{"id": f"{b}:{b}", "book": b, "lines": [{"n": n} for n in sorted(ns)]}
                          for b, ns in sorted(spine_lines.items())]}
    summary = bi.run(manifest, spine)
    ross = json.loads((tmp_path / "stage1" / "ross_chunks.json").read_text(encoding="utf-8"))
    notes = json.loads((tmp_path / "stage1" / "butler_footnotes.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "stage1" / "butler_report.json").read_text(encoding="utf-8"))
    assert sorted(ross) == sorted(f"{b}:{b}" for b in range(1, 25))
    piece = ross["1:1"]
    assert len(piece) == 1 and set(piece[0]) == {"chapter", "text", "cont", "bekker"}
    assert piece[0]["chapter"] == "1" and piece[0]["cont"] is False
    assert summary["footnotes"] == len(notes) == 16
    assert summary["books"] == 24 and summary["scan_books"] == 14
    assert summary["books_missing_notes"] == 11 and summary["join"] == "14.486"
    assert summary["ticks"] == summary["ticks_scan"] + summary["ticks_rule"]
    assert report["ticks_by_book"] == {str(b): len(ross[f"{b}:{b}"][0]["bekker"])
                                       for b in range(1, 25)}
