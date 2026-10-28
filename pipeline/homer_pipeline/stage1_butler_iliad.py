"""Stage 1b (Iliad): Samuel Butler's own Iliad (Longmans, 1898) in the
``ross`` overlay slot (english.secondary), in place of the Perseus
``*-eng4.xml``, which is the Power–Nagy revision, not Butler (John,
2026-10-26; CLAUDE.md "The Butler slot is Butler's own text").

The Odyssey's twin is ``stage1_butler_wikisource``; this module reuses its
template reduction, corrections, footnote and tick machinery
(``parse_assembled``) and differs only where the Iliad's sources differ.
Provenance and findings: ``sources/INVENTORY.md``, section butler/.

Two sources, joined in Book XIV (John's decision, 2026-10-26):

  1. Books I-XIII and XIV to line 485: the Wikisource scan transcription,
     ``sources/butler/wikisource/iliad/page-NNN.wiki`` (scan pp. 21-256),
     aligned by Butler's own printed marginal line numbers (``{{pline}}``).
  2. From XIV.486 (the join) to the end of Book XXIV: the words of Project
     Gutenberg #2199 (``sources/butler/butler-iliad.txt``), which has no line
     numbers and no notes. Line numbers come from the Perseus revision's
     ``<milestone unit="line">`` that fall at paragraph starts (the rule
     below). Butler's own footnotes for these books are in no source we have:
     the report lists the books whose notes are missing, and the site's
     attribution page says so.

The scan, decisions beyond the Odyssey stage's (each visible in
``butler_report.json``):

  - There are no book wrappers. The scan pages run in order and a book
    starts on the page that carries its ``{{larger|BOOK N}}`` heading; that
    page's first paragraph is the heading (with the title "THE ILIAD OF
    HOMER" on the first page) and its second is Butler's one-line argument.
    Both are recorded in the report, not emitted, as in the Odyssey.
  - Butler's 1898 printing sets a line number in the margin at each
    paragraph head, and in Book XIV (the page images of pp. 245-256 show it)
    also beside the first and last printed line of most pages. The
    transcription of Books I-XIII carries paragraph-head numbers only; that
    of Book XIV (scan pp. 244-256) carries the page-head and page-foot
    numbers too. A page-head number is Butler's number for the page's first
    printed line: it becomes a tick there, mid-paragraph. A page-foot number
    that the transcription puts after the page's last word marks a printed
    line the run-on text no longer locates: it is dropped and reported
    (``pline_page_foot_dropped``). When the next page opens with the same
    number it is the page-break duplicate (Il. 14.445, pp. 255-256): one
    marker, kept at the head, where its words begin
    (``pline_page_break_duplicate``).
  - ``{{pline}}`` with a space after it (Book XIV's transcribers write
    ``{{pline|458|l}} The``) puts the space before the number, so a tick
    never opens on a space.
  - ``{{SIC|printed}}`` with no correction (once: Il. 6, p. 122, a stray
    ``'`` before the closing quote) is a flag only: the printed text stands
    and the flag is listed with the bare ``{{sic}}``.
  - Scan pp. 247-254 are proofreading level 1: raw OCR, never proofread. They
    are used, but read through ``SCAN_FIXES``: every OCR misreading (``CEneus``
    for "Œneus", ``Achseans`` for "Achæans"), the running head OCR'd into the
    text of p. 254, its five marginal numbers OCR'd as bare digits, and the
    paragraph breaks the OCR invented or lost. Each fix is checked against the
    page image on Wikimedia Commons, with Gutenberg's words as a second
    witness, and must match its page exactly once. The OCR's spacing (a space
    before ``; : ? !``, after an opening quote, around an em dash) is closed
    up on those pages, as the proofread pages print it. A few fixes on the
    proofread Book XIV pages (level 3) correct a transcription slip against
    the page image; they are in the same table and marked so.

The join (Book XIV): the scan's last paragraph must equal, word for word,
one Gutenberg paragraph; the Gutenberg paragraphs after it follow. Nothing is
lost or doubled at the seam, and ``run`` fails otherwise.

The Gutenberg text: the PG header and licence are cut at the START/End
markers; paragraphs are blank-line separated and kept; a book's first
paragraph after its "BOOK N" heading is Butler's argument (recorded, not
emitted, as for the scan); PG's ``--`` is Butler's close-set em dash ``—``;
the first word(s) of a book, which PG sets in capitals for the print's small
capitals ("BUT when"), are set in ordinary case ("But when"), as the scan's
``{{sc|But}}`` reduces. PG spells æ/œ as ae/oe and uses straight quotes; that
is left as it is (restoring the ligatures word by word would be guessing).

The Perseus rule (Phase A, measured on Books III-XIII against Butler's own
printed numbers; numbers in the report): a Perseus milestone is a Butler
paragraph number when it opens a Perseus ``<p>`` (no word text before it in
that ``<p>``) AND that position, under a word alignment of the Perseus text to
Gutenberg's (difflib on case- and accent-folded words, Perseus's bracketed
Greek glosses removed), is the start of a Gutenberg paragraph. The second
condition matters: Perseus adds its own ``<p>`` break and milestone inside
many long paragraphs (95 in Books III-XIII, none of them a number Butler
printed), and Gutenberg's paragraphs, which are Butler's (they pair one to
one with the scan's in Books I-XIII), filter them out. In Books III-XIII the
rule reproduces 447 of Butler's 453 printed numbers, at the same paragraphs,
and 447 of its 455 numbers are Butler's (recall 0.987, precision 0.982); the
misses are numbers that differ by one to ten lines, several of them Butler's
own misprints. So rule ticks are ``real: true``: they are anchors at
paragraph starts, not interpolated estimates, and Butler's numbers in all but
a few cases. Each tick's source is listed in the report.
"""

from __future__ import annotations

import csv
import difflib
import re
import unicodedata
from pathlib import Path

from lxml import etree

from . import stage1_butler_wikisource as bw
from .config import BUILD_DIR, SOURCES_DIR, Manifest
from .stage1_common import write_json
from .stage1_perseus_milestone_english import _nearest_line

TRANSLATION_ID = "butler"
SCAN_FIRST, SCAN_LAST = 21, 256
JOIN_BOOK = 14

ROMAN = {r: i for i, r in enumerate(
    "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX "
    "XXI XXII XXIII XXIV".split(), 1)}

_BOOK_HEAD = re.compile(r"\{\{larger\|BOOK ([IVXL]+)\}\}")
_SIC_ONE = re.compile(r"\{\{(?:SIC|sic)\|([^{}|]*)\}\}")
_PLINE_N = r"\{\{pline\|(\d+)\s*(?:\|[^{}]*)?\}\}"
_FOOT_PLINE = re.compile(_PLINE_N + r"\s*$")
_HEAD_PLINE = re.compile(r"^\s*" + _PLINE_N)
_PLINE_SPACE = re.compile(r"[ \t]*(\{\{pline\|[^{}]*\}\})[ \t]+")

# Scan fixes: (page, transcribed, corrected, why). Level 1 (pp. 247-254) is
# raw OCR; each fix is read off the page image (Wikimedia Commons, File:The
# Iliad of Homer (Butler).djvu, page N), Gutenberg agreeing unless noted.
# Level 3 entries correct a proofread page against its image.
SCAN_FIXES: list[tuple[int, str, str, str]] = [
    (244, "the cry of the battle", "the cry of battle",
     "level 3: the image prints \"cry of battle\" (Gutenberg too)"),
    (244, "wind seeps down", "wind sweeps down",
     "level 3: the image prints \"sweeps\" (Gutenberg too)"),
    (245, "as they 28 were", "as they were",
     "level 3: the page-head number 28 (printed at the end of the first line) is "
     "transcribed twice, as {{pline|28}} and as digits in the text"),
    (246, "therefore. Sir captain", "therefore, Sir captain",
     "level 3: the image prints a comma (Gutenberg too)"),
    (247, "Eor Portheus", "For Portheus", "OCR"),
    (247, "knight CEneus", "knight Œneus", "OCR"),
    (247, "QSneus remained", "Œneus remained", "OCR"),
    (247, "Achseans", "Achæans", "OCR"),
    (247, 'their city." {{pline|146}}', 'their city." {{pline|146}}{{nop}}',
     "OCR: the page ends a paragraph (the image opens p. 248 with one; Gutenberg too)"),
    (248, "Achseans", "Achæans", "OCR"),
    (248, "herseK", "herself", "OCR"),
    (248, "three brilliant\n\n{{pline|183|l}} pendants", "three brilliant {{pline|183|l}}pendants",
     "OCR paragraph break: 183 is beside the page's last line, mid-paragraph"),
    (249, 'Trojan 1 "', 'Trojan?"', "OCR"),
    (249, "Rhsea", "Rhæa", "OCR"),
    (249, 'bootless."{{pline|221 }}', 'bootless."{{pline|221 }}{{nop}}',
     "OCR: the page ends a paragraph (the image opens p. 250 with one; Gutenberg too)"),
    (250, '{{pline|222|l}}"When she heard', "{{pline|222|l}}When she heard",
     "OCR: no quotation mark in the image (narrative)"),
    (250, "Bmathia", "Emathia", "OCR"),
    (250, "aegis-bearing", "ægis-bearing", "OCR: the image prints the ligature"),
    (250, "heard \n\n{{pline|259|l}}of any more", "heard {{pline|259|l}}of any more",
     "OCR paragraph break: 259 is beside the page's last line, mid-paragraph"),
    (251, "son 1 Come", "son? Come", "OCR"),
    (251, 'youngest of the \n\n{{pline|277|l}}Graces — Pasithea, whom I have always wanted to marry." Juno did',
     'youngest of the Graces — Pasithea, whom I have always wanted to marry."\n\n{{pline|277|l}}Juno did',
     "OCR paragraph breaks: the image breaks at \"Juno did as he had said\" (14.277; "
     "Gutenberg agrees) and not before \"Graces\"; its 277 is printed at the end of "
     "the line above"),
    (251, "Oymindis", "Cymindis", "OCR"),
    (252, "Pirithoiis", "Pirithoüs", "OCR"),
    (252, "Danae the", "Danaë the", "OCR: the image prints the diaeresis"),
    (252, "of Phoenix", "of Phœnix", "OCR: the image prints the ligature"),
    (253, "dew-bespangeled", "dew-bespangled", "OCR"),
    (253, "you cna help", "you can help", "OCR"),
    (253, "I have snet him", "I have sent him", "OCR"),
    (253, "to hlep the", "to help the", "OCR"),
    (254, "234 HECTOR LEADS THE TROJANS ON [iuad \n\n375 lead", "{{pline|375|l}}lead",
     "OCR: running head in the text; page-head number 375 as bare digits"),
    (254, "\n\n378 Thus", "\n\n{{pline|378|l}}Thus", "OCR: marginal number as bare digits"),
    (254, "\n\n389 Hector", "\n\n{{pline|389|l}}Hector", "OCR: marginal number as bare digits"),
    (254, "\n\n402 Hector", "\n\n{{pline|402|l}}Hector", "OCR: marginal number as bare digits"),
    (254, "were \n410 many", "were many",
     "OCR: page-foot number 410 as bare digits; p. 255 prints 410 again at its head, "
     "where it is kept"),
    (256, "Satniödeis", "Satniöeis", "level 3: the image prints Satniöeis (Gutenberg Satnioeis)"),
]


def scan_dir(manifest: Manifest) -> Path:
    return SOURCES_DIR / manifest.data["english"]["secondary"]["source"]


def _secondary(manifest: Manifest) -> dict:
    return (manifest.data.get("english") or {}).get("secondary") or {}


def page_levels(src: Path) -> dict[int, int]:
    """scan page -> proofreading level, from MANIFEST.tsv."""
    out: dict[int, int] = {}
    with (src / "MANIFEST.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[int(row["file"][5:8])] = int(row["quality"])
    return out


# ── the scan ───────────────────────────────────────────────────────────────

def book_pages(src: Path) -> dict[int, list[int]]:
    """book -> its scan pages, a book starting on its heading's page."""
    out: dict[int, list[int]] = {}
    cur = None
    for p in range(SCAN_FIRST, SCAN_LAST + 1):
        m = _BOOK_HEAD.search((src / f"page-{p:03d}.wiki").read_text(encoding="utf-8"))
        if m:
            cur = ROMAN[m.group(1)]
            if cur in out:
                raise ValueError(f"book {cur} heading twice (p. {p})")
            out[cur] = []
        if cur is None:
            raise ValueError(f"p. {p} precedes the first book heading")
        out[cur].append(p)
    return out


def _plain_template_text(s: str) -> str:
    """Display text of a heading/argument: templates to their last argument."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{\{(?:dhr|nop)\}\}", "", s)
        s = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", lambda m: m.group(1).split("|")[-1], s)
    return " ".join(s.split())


def _apply_fixes(body: str, page: int, log: dict) -> str:
    for p, old, new, why in SCAN_FIXES:
        if p != page:
            continue
        if body.count(old) != 1:
            raise ValueError(f"scan fix on p. {page} matches {body.count(old)} times: {old!r}")
        body = body.replace(old, new)
        log["scan_fixes"].append({"page": page, "transcribed": old, "corrected": new, "why": why})
    return body


def _close_ocr_spacing(body: str, page: int, log: dict) -> str:
    """Level-1 pages: close up the OCR's spaces before ; : ? !, after an
    opening quote and around an em dash."""
    n = 0
    for pat, rep in ((r"[ \t]+([;:?!])", r"\1"),
                     (r'(?:^|(?<=\s))" +(?=[A-Za-z])', '"'),
                     (r"[ \t]*—[ \t]*", "—")):
        body, k = re.subn(pat, rep, body)
        n += k
    log["ocr_spacing_closed"][page] = n
    return body


def assemble_scan_book(src: Path, book: int, pages: list[int], levels: dict[int, int],
                       log: dict, next_head: dict[int, int | None]) -> str:
    """The book's scan wikitext: heading and argument cut, fixes and
    corrections applied, pages joined as the Odyssey stage joins them."""
    out = ""
    ends_para = False
    for i, page in enumerate(pages):
        raw = (src / f"page-{page:03d}.wiki").read_text(encoding="utf-8")
        body = bw.page_body(raw, None, None)
        body = _apply_fixes(body, page, log)
        if levels[page] == 1:
            body = _close_ocr_spacing(body, page, log)
        if i == 0:
            paras = re.split(r"\n[ \t]*\n", body.strip())
            if not _BOOK_HEAD.search(paras[0]):
                raise ValueError(f"book {book}: p. {page} does not open with its heading")
            head = _plain_template_text(paras[0])
            title, _, heading = head.rpartition("BOOK")
            if title.strip():
                log["furniture_dropped"].append({"book": book, "text": title.strip()})
            log["headings"][book] = ("BOOK" + heading).strip()
            log["arguments"][book] = _plain_template_text(paras[1])
            body = "\n\n".join(paras[2:])

        def sic_one(m, page=page):
            ctx = re.sub(r"\s+", " ", body[max(0, m.start() - 40):m.start()])
            log["sic_bare"].append({"book": book, "page": page, "context": ctx,
                                    "printed": m.group(1), "in_note": bw._in_ref(body, m.start())})
            return m.group(1)

        body = _SIC_ONE.sub(sic_one, body)
        body = bw.apply_corrections(body, page, book, log).strip()
        body = _PLINE_SPACE.sub(r" \1", body).strip()
        page_ends_para = body.endswith("{{nop}}")
        if page_ends_para:
            body = body[: -len("{{nop}}")].rstrip()
        # A number after the page's last word is dropped: either it is the
        # page-break duplicate of the next page's head number (one marker,
        # kept at the head, where the words it numbers begin) or it marks a
        # printed line the run-on transcription no longer locates.
        foot = _FOOT_PLINE.search(body)
        if foot:
            n = int(foot.group(1))
            kind = ("pline_page_break_duplicate" if n == next_head.get(page)
                    else "pline_page_foot_dropped")
            log["anomalies"].append({"kind": kind, "book": book, "page": page, "n_raw": n})
            body = body[:foot.start()].rstrip()
        if out and body:
            if ends_para:
                out += "\n\n"
            elif not out.endswith("—"):
                out += " "
        out += body
        ends_para = page_ends_para
    return out


def _head_numbers(src: Path) -> dict[int, int | None]:
    """page -> the number that opens the NEXT scan page (None if none)."""
    heads: dict[int, int | None] = {}
    for p in range(SCAN_FIRST, SCAN_LAST + 1):
        nxt = src / f"page-{p + 1:03d}.wiki"
        m = _HEAD_PLINE.match(bw.page_body(nxt.read_text(encoding="utf-8"), None, None)) \
            if p < SCAN_LAST and nxt.exists() else None
        heads[p] = int(m.group(1)) if m else None
    return heads


# ── Gutenberg ──────────────────────────────────────────────────────────────

def gutenberg_books(path: Path) -> dict[int, dict]:
    """PG #2199 -> {book: {"argument", "paras"}}; header and licence cut."""
    raw = path.read_text(encoding="ascii").replace("\r\n", "\n")
    start = raw.index("*** START OF THIS PROJECT GUTENBERG EBOOK THE ILIAD ***")
    end = raw.index("End of the Project Gutenberg EBook of The Iliad")
    parts = re.split(r"(?m)^BOOK ([IVXL]+)[ \t]*$", raw[start:end])
    out: dict[int, dict] = {}
    for i in range(1, len(parts), 2):
        paras = [" ".join(p.split()) for p in re.split(r"\n[ \t]*\n", parts[i + 1]) if p.strip()]
        paras = [re.sub(r"\s*--\s*", "—", p) for p in paras]
        out[ROMAN[parts[i]]] = {"argument": paras[0], "paras": paras[1:]}
    if sorted(out) != list(range(1, 25)):
        raise ValueError(f"gutenberg: books {sorted(out)}")
    return out


def _sentence_case_opening(para: str) -> tuple[str, str | None]:
    """PG's capitals for the print's small capitals: "SO THE son" -> "So the son"."""
    m = re.match(r"[A-Z]{2,}(?: [A-Z]{2,})*(?![A-Za-z])", para)
    if not m:
        return para, None
    words = m.group(0).split()
    fixed = " ".join([words[0].capitalize()] + [w.lower() for w in words[1:]])
    return fixed + para[m.end():], m.group(0)


# ── word alignment ─────────────────────────────────────────────────────────

def norm_words(s: str) -> list[str]:
    """Case-, accent- and ligature-folded words (digits and punctuation out)."""
    s = s.replace("Æ", "Ae").replace("æ", "ae").replace("Œ", "Oe").replace("œ", "oe")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\[\^butler\.\d+\.\d+\]", "", s)
    return re.findall(r"[a-z]+", s.lower())


class _Aligner:
    """Word alignment a -> b; ``span(i)`` is the b-position(s) a[i] maps to."""

    def __init__(self, a: list[str], b: list[str]):
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        self.blocks = [bl for bl in sm.get_matching_blocks() if bl.size]

    def span(self, i: int) -> tuple[int, int]:
        prev = None
        for bl in self.blocks:
            if bl.a <= i < bl.a + bl.size:
                j = bl.b + i - bl.a
                return j, j
            if bl.a > i:
                return (prev.b + prev.size if prev else 0), bl.b
            prev = bl
        return (prev.b + prev.size if prev else 0), 10 ** 9


TEI = "{http://www.tei-c.org/ns/1.0}"


def perseus_books(path: Path) -> dict[int, list[dict]]:
    """Perseus eng4 -> {book: [{"text", "ms": [(n, char offset)]} per <p>]}.
    Milestones only; Perseus's bracketed Greek glosses stay in ``text`` (the
    word fold drops them)."""
    root = etree.parse(str(path)).getroot()
    out: dict[int, list[dict]] = {}
    for div in root.iter(TEI + "div"):
        if div.get("subtype") != "book":
            continue
        paras = []
        for p in div.iter(TEI + "p"):
            buf: list[str] = []
            ms: list[tuple[str, int]] = []

            def walk(el):
                if el.tag == TEI + "milestone":
                    if el.get("unit") == "line":
                        ms.append((el.get("n"), len("".join(buf))))
                elif el.tag != TEI + "note":
                    if el.text:
                        buf.append(el.text)
                    for ch in el:
                        walk(ch)
                        if ch.tail:
                            buf.append(ch.tail)

            walk(p)
            paras.append({"text": "".join(buf), "ms": ms})
        out[int(div.get("n"))] = paras
    return out


def _strip_glosses(s: str) -> str:
    return re.sub(r"\[[^\]]*\]", "", s)


def rule_numbers(perseus_paras: list[dict], gut_paras: list[str]) -> dict:
    """The Perseus rule on one book: {"ticks": [(n, gut paragraph index)],
    "rejected": [n ...] (opens a Perseus <p>, not a Gutenberg paragraph),
    "mid_p": [n ...] (not at a <p> start)}."""
    pw: list[str] = []
    cands: list[tuple[int, int]] = []
    mid_p: list[int] = []
    for p in perseus_paras:
        t = p["text"]
        for n, off in p["ms"]:
            nn = int(re.match(r"\d+", n).group())
            if re.search(r"\w", t[:off]):
                mid_p.append(nn)
                continue
            cands.append((nn, len(pw) + len(norm_words(_strip_glosses(t[:off])))))
        pw += norm_words(_strip_glosses(t))
    gw: list[str] = []
    starts: list[int] = []
    for para in gut_paras:
        starts.append(len(gw))
        gw += norm_words(para)
    al = _Aligner(pw, gw)
    ticks: list[tuple[int, int]] = []
    rejected: list[int] = []
    for nn, wi in cands:
        lo, hi = al.span(wi)
        hits = [k for k, s in enumerate(starts) if lo <= s <= hi]
        if hits:
            ticks.append((nn, hits[0]))
        else:
            rejected.append(nn)
    return {"ticks": ticks, "rejected": rejected, "mid_p": mid_p}


def _para_offsets(paras: list[str]) -> list[int]:
    offs, pos = [], 0
    for p in paras:
        offs.append(pos)
        pos += len(p) + 1
    return offs


def _validate_ticks(raw: list[dict], book: int, valid_lines: set[int], log: dict) -> list[dict]:
    """Snap ticks on lines the spine lacks; drop out-of-order ones (logged)."""
    valid_sorted = sorted(valid_lines)
    out: list[dict] = []
    for t in raw:
        n = t["n"]
        if n not in valid_lines:
            snapped = _nearest_line(valid_sorted, n)
            log["anomalies"].append({"kind": "rule_gap_snap", "book": book, "n_raw": n,
                                     "snapped_to": snapped})
            n = snapped
        if out and (n <= out[-1]["n"] or t["offset"] <= out[-1]["offset"]):
            log["anomalies"].append({"kind": "rule_out_of_order", "book": book, "n_raw": t["n"],
                                     "last_accepted": out[-1]["n"]})
            continue
        out.append({"n": n, "offset": t["offset"], "real": True})
    return out


# ── the work ───────────────────────────────────────────────────────────────

def _new_log() -> dict:
    log = bw._new_log()
    log.update({"scan_fixes": [], "ocr_spacing_closed": {}, "join": {}, "rule": {},
                "gutenberg_openings": [], "tick_sources": {}, "books_missing_notes": []})
    return log


def parse_work(manifest: Manifest, valid_lines_by_book: dict[int, set[int]]) -> dict:
    sec = _secondary(manifest)
    src = scan_dir(manifest)
    levels = page_levels(src)
    pages = book_pages(src)
    if sorted(pages) != list(range(1, JOIN_BOOK + 1)):
        raise ValueError(f"scan books {sorted(pages)}")
    heads = _head_numbers(src)
    errata = bw.load_errata(manifest.work_id)
    gut = gutenberg_books(SOURCES_DIR / sec["gutenberg"])
    pers = perseus_books(SOURCES_DIR / sec["milestones"])
    log = _new_log()
    books: dict[int, dict] = {}

    for b in manifest.books:
        b = b["n"]
        valid = valid_lines_by_book.get(b, set())
        if b in pages:
            raw = assemble_scan_book(src, b, pages[b], levels, log, heads)
            r = bw.parse_assembled(raw, b, valid, errata, log)
            log["tick_sources"][b] = {"scan": len(r["bekker"])}
            if b != JOIN_BOOK:
                books[b] = r
                continue
            # The join: the scan's last paragraph is one Gutenberg paragraph.
            scan_text = r["text"]
            last = norm_words(scan_text.rsplit("\n", 1)[-1])
            paras = gut[b]["paras"]
            at = [k for k, p in enumerate(paras) if norm_words(p) == last]
            if len(at) != 1:
                raise ValueError(f"book {b}: scan's last paragraph matches Gutenberg {len(at)} times")
            k0 = at[0] + 1
            log["join"] = {"book": b, "gutenberg_paragraph": k0,
                           "scan_ends": " ".join(scan_text.split()[-30:]),
                           "gutenberg_starts": " ".join(" ".join(paras[k0:]).split()[:30]),
                           "scan_paragraphs": scan_text.count("\n") + 1,
                           "gutenberg_paragraphs_matched": k0}
            rule = rule_numbers(pers[b], paras)
            offs = _para_offsets(paras[k0:])
            base = len(scan_text) + 1
            last_n = r["bekker"][-1]["n"]
            cand = [{"n": n, "offset": base + offs[k - k0]} for n, k in rule["ticks"]
                    if k >= k0 and n > last_n]
            ticks = r["bekker"] + _validate_ticks(cand, b, valid, log)
            log["join"]["first_rule_tick"] = cand[0]["n"] if cand else None
            log["rule"][b] = {"ticks": len(cand), "rejected": rule["rejected"]}
            log["tick_sources"][b]["perseus_rule"] = len(ticks) - len(r["bekker"])
            r = dict(r, text=scan_text + "\n" + "\n".join(paras[k0:]), bekker=ticks)
            log["books_missing_notes"].append({"book": b, "from_line": cand[0]["n"] if cand else None,
                                               "whole_book": False})
            books[b] = r
            continue
        # Gutenberg-only books.
        paras = list(gut[b]["paras"])
        paras[0], caps = _sentence_case_opening(paras[0])
        if caps:
            log["gutenberg_openings"].append({"book": b, "printed": caps,
                                              "set": paras[0][:len(caps)]})
        log["arguments"][b] = gut[b]["argument"]
        rule = rule_numbers(pers[b], paras)
        offs = _para_offsets(paras)
        cand = [{"n": n, "offset": offs[k]} for n, k in rule["ticks"]]
        ticks = _validate_ticks(cand, b, valid, log)
        valid_sorted = sorted(valid)
        if not ticks or ticks[0]["offset"] > 0:
            ticks.insert(0, {"n": valid_sorted[0], "offset": 0, "real": True})
            log["anomalies"].append({"kind": "rule_book_start_added", "book": b})
        log["rule"][b] = {"ticks": len(cand), "rejected": rule["rejected"]}
        log["tick_sources"][b] = {"perseus_rule": len(ticks)}
        log["books_missing_notes"].append({"book": b, "from_line": 1, "whole_book": True})
        books[b] = {"text": "\n".join(paras), "bekker": ticks, "notes": {},
                    "plines_printed": 0, "plines_distinct": 0}

    unmatched = [e for e in errata if e.get("_applied") != 1]
    if unmatched:
        raise ValueError(f"pline errata not matched exactly once: {unmatched}")
    if len(log["scan_fixes"]) != len(SCAN_FIXES):
        raise ValueError("a scan fix names a page outside the scan")
    for book, r in books.items():
        if any(s in t for s in bw._SENTINELS for t in (r["text"], *r["notes"].values())):
            raise ValueError(f"book {book}: sentinel left in text")
    return {"books": books, "log": log}


def run(manifest: Manifest, spine: dict) -> dict:
    valid = {seg["book"]: {l["n"] for l in seg["lines"]} for seg in spine["segments"]}
    seg_by_book: dict[int, str] = {}
    for seg in spine["segments"]:
        if seg["book"] in seg_by_book:
            raise ValueError(f"butler: book {seg['book']} has more than one segment")
        seg_by_book[seg["book"]] = seg["id"]
    parsed = parse_work(manifest, valid)
    books, log = parsed["books"], parsed["log"]

    ross: dict[str, list[dict]] = {}
    notes: dict[str, str] = {}
    for b, r in books.items():
        ross[seg_by_book[b]] = [{"chapter": str(b), "text": r["text"], "cont": False,
                                 "bekker": r["bekker"]}]
        notes.update(r["notes"])

    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "ross_chunks.json", ross)
    write_json(out_dir / "butler_footnotes.json", notes)
    sources = log["tick_sources"]
    summary = {
        "books": len(books),
        "scan_books": sum(1 for s in sources.values() if "scan" in s),
        "plines_printed": sum(r["plines_printed"] for r in books.values()),
        "plines_distinct": sum(r["plines_distinct"] for r in books.values()),
        "ticks": sum(len(r["bekker"]) for r in books.values()),
        "ticks_scan": sum(s.get("scan", 0) for s in sources.values()),
        "ticks_rule": sum(s.get("perseus_rule", 0) for s in sources.values()),
        "footnotes": len(notes),
        "books_missing_notes": len(log["books_missing_notes"]),
        "join": f"{log['join']['book']}.{log['join']['first_rule_tick']}",
        "errata": len(log["errata"]),
        "sic": len(log["sic"]),
        "sic_bare": len(log["sic_bare"]),
        "pline_errata": len(log["pline_errata_applied"]),
        "scan_fixes": len(log["scan_fixes"]),
        "anomalies": len(log["anomalies"]),
    }
    report = {
        "work": manifest.work_id,
        "translation": TRANSLATION_ID,
        "source": {"scan": str(scan_dir(manifest).relative_to(SOURCES_DIR)),
                   "gutenberg": _secondary(manifest)["gutenberg"],
                   "milestones": _secondary(manifest)["milestones"]},
        "summary": summary,
        "ticks_by_book": {str(b): len(r["bekker"]) for b, r in books.items()},
        **log,
        "headings": {str(k): v for k, v in log["headings"].items()},
        "arguments": {str(k): v for k, v in log["arguments"].items()},
        "ocr_spacing_closed": {str(k): v for k, v in log["ocr_spacing_closed"].items()},
        "rule": {str(k): v for k, v in log["rule"].items()},
        "tick_sources": {str(k): v for k, v in log["tick_sources"].items()},
    }
    write_json(out_dir / "butler_report.json", report)
    return summary
