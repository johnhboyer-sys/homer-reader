"""Stage 1k: the Kosmos Society revision of Butler — a fourth English text,
shown as verse groups (John, 2026-09-12; see CLAUDE.md's CC exception).

Source: the two saved Kosmos Society pages, sources/kosmos/homeric-{iliad,
odyssey}.html (Samuel Butler's translation revised by Soo-Young Kim, Kelly
McCray, Gregory Nagy and Timothy Power; CC BY-NC-ND 3.0 — the licence entry
lives on cc_translations.yaml, never on the public-domain list). Each page
carries all 24 books ("Rhapsody N" <h2> headings).

Kosmos prints its own line numbers: a bare ``[N]`` in the running text every
fifth line, plus scattered ``<sub>N</sub>`` numbers where the revisers went
line by line (about a quarter of all lines). Those numbers are the only
alignment this text has, so the English is cut at each one and set beside
that Greek span. Nothing is interpolated and no per-line break is invented.

ND means verbatim. The words, the bracketed Greek and the notes are kept as
printed; only the line numbers leave the running text, and they leave it as
data (ticks and marks), not as deletions:

  - ``bekker`` ticks ``{n, offset, real}`` — the group breaks. A printed
    number becomes a break only when it names a Greek line this book carries
    and is higher than the previous break. A book whose first printed number
    is not 1 (Il. 17, 18, 22 open at [5]) gets an ``implied`` tick at its
    first line, which is exact by construction (the book starts there).
  - ``marks`` ``{n, offset, label, reason}`` — every other printed number,
    kept at its place: ``repeat`` (the same number printed again, e.g. three
    ``<sub>167</sub>`` in Il. 9), ``out-of-sequence`` (a number lower than one
    already passed, e.g. ``[95]`` among the 190s of Il. 17 — a misprint for
    195) and ``not-in-greek`` (Il. 9.460, which falls in 9.458–461, lines
    Allen omits; see the manifest's expected_line_gaps). The reader shows a
    mark inline, muted; it never cuts a group.
  - ``spans`` ``[start, end, kind]`` — standoff over the text: ``tr`` a
    transliteration bracket (``[mēnis]``: the bracket holds italic Greek and
    does not open with "="; plus the two unitalicised ones, ``[moira]`` and
    ``[philos]``), ``ed`` any other bracket (``[= Apollo]``, ``[Agamemnon]``),
    ``em`` an italic run. The reader's toggle hides ``tr`` spans only.
  - footnote references are inline ``[^kosmos.<book>.<n>]`` markers (the
    reader's existing footnote convention); the note text goes to
    build/stage1/overlay_footnotes.json, which stage7 merges into the work's
    footnotes.json.

Paragraphs are kept as ``\\n`` in the text. The per-book credit line, the
"Return to top" links, the revision-date stamps and the "__" separators are
page furniture, not text, and are left out (the credit is carried in full on
the attribution page and in cc_translations.yaml).
"""

from __future__ import annotations

import html as html_mod
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from .config import BUILD_DIR, SOURCES_DIR, Manifest

TRANSLATION_ID = "kosmos"

# Transliteration brackets the source prints without italics. Every other
# unitalicised bracket is an English insertion ([Agamemnon], [from battle]).
UNITALICISED_TRANSLIT = {"moira", "philos"}

_BOOK_HEAD = re.compile(r'<h2[^>]*>\s*Homeric\s*<em>\w+</em>\s*<br\s*/?>\s*Rhapsody\s+(\d+)\s*</h2>', re.S)
_PARA = re.compile(r"<p(\s[^>]*)?>(.*?)</p>", re.S)
_LINE_NUM = re.compile(r"\[\s*(\d+)\s*\]")
_FN_REF = re.compile(r"#(\d+)fn(\d+)$")
_FN_NAME = re.compile(r"^(\d+)fn(\d+)$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WS = re.compile(r"[ \t\r\n\f]+")


def source_path(work_id: str) -> Path:
    return SOURCES_DIR / "kosmos" / f"homeric-{work_id}.html"


def split_books(page: str) -> dict[int, str]:
    """Book number -> that book's HTML, from after its <h2> to the next <h2>
    (the next book, or the page's "Related topics") or the share block."""
    heads = list(_BOOK_HEAD.finditer(page))
    books: dict[int, str] = {}
    for i, m in enumerate(heads):
        start = m.end()
        if i + 1 < len(heads):
            end = heads[i + 1].start()
        else:
            cands = [p for p in (page.find("<h2", start), page.find('<div class="sharedaddy', start)) if p > 0]
            end = min(cands) if cands else len(page)
        books[int(m.group(1))] = page[start:end]
    if sorted(books) != list(range(1, 25)):
        raise ValueError(f"kosmos: expected Rhapsody 1-24, found {sorted(books)}")
    return books


def _plain(fragment: str) -> str:
    return _WS.sub(" ", html_mod.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


class _ParaParser(HTMLParser):
    """One body paragraph -> text + standoff (em spans, printed line numbers,
    footnote refs). Line numbers and footnote-ref digits do not enter the
    text; everything else does, whitespace collapsed as a browser would."""

    def __init__(self, book: int):
        super().__init__(convert_charrefs=True)
        self.book = book
        self.out: list[str] = []
        self.len = 0
        self.em: list[list[int]] = []
        self.em_open: list[int] = []
        self.nums: list[tuple[int, str]] = []   # (offset, label)
        self.fns: list[tuple[int, int]] = []    # (offset, note n)
        self.in_sub = 0
        self.sub_buf = ""
        self.in_fn = 0

    def _emit(self, s: str) -> None:
        s = _WS.sub(" ", s)
        if not s:
            return
        # Collapse against what is already out (or the paragraph start).
        if s.startswith(" ") and (self.len == 0 or self.out[-1].endswith(" ")):
            s = s[1:]
        if s:
            self.out.append(s)
            self.len += len(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "em":
            self.em_open.append(self.len)
        elif tag == "sub":
            self.in_sub += 1
            self.sub_buf = ""
        elif tag == "a" and a.get("href") and _FN_REF.search(a["href"]):
            m = _FN_REF.search(a["href"])
            if int(m.group(1)) != self.book:
                raise ValueError(f"kosmos book {self.book}: footnote ref {a['href']} names another book")
            self.fns.append((self.len, int(m.group(2))))
            self.in_fn += 1
        elif tag == "br":
            self._emit(" ")

    def handle_endtag(self, tag):
        if tag == "em" and self.em_open:
            s = self.em_open.pop()
            if self.len > s:
                self.em.append([s, self.len])
        elif tag == "sub" and self.in_sub:
            self.in_sub -= 1
            label = self.sub_buf.strip()
            if not re.fullmatch(r"\d+(?:\s*[–-]\s*\d+)?", label):
                raise ValueError(f"kosmos book {self.book}: unexpected <sub> content {label!r}")
            self.nums.append((self.len, re.sub(r"\s+", "", label)))
        elif tag == "a" and self.in_fn:
            self.in_fn -= 1

    def handle_data(self, data):
        if self.in_sub:
            self.sub_buf += data
            return
        if self.in_fn:
            return  # the superscript digit of a footnote ref
        pos = 0
        for m in _LINE_NUM.finditer(data):
            self._emit(data[pos:m.start()])
            self.nums.append((self.len, m.group(1)))
            pos = m.end()
        self._emit(data[pos:])

    def result(self) -> dict:
        text = "".join(self.out)
        stripped = text.rstrip(" ")
        n = len(stripped)
        clamp = lambda o: min(o, n)  # noqa: E731
        return {
            "text": stripped,
            "em": [[clamp(s), clamp(e)] for s, e in self.em if clamp(s) < clamp(e)],
            "nums": [(clamp(o), lab) for o, lab in self.nums],
            "fns": [(clamp(o), k) for o, k in self.fns],
        }


def _parse_note(book: int, inner: str) -> tuple[int, str]:
    """A Notes-block paragraph -> (n, note HTML). Shape:
    <a name="3fn1"></a>[<a href="#r3fn1"> back </a>] <strong>1.</strong>&nbsp;Text…"""
    m = re.search(r'<a name="(\d+)fn(\d+)"', inner)
    if not m or int(m.group(1)) != book:
        raise ValueError(f"kosmos book {book}: unrecognised note paragraph {inner[:80]!r}")
    n = int(m.group(2))
    body = re.split(r"<strong>\s*\d+\.\s*</strong>", inner, maxsplit=1)
    if len(body) != 2:
        raise ValueError(f"kosmos book {book}: note {n} has no '<strong>N.</strong>' label")
    # Keep the words verbatim, italics as <em>, everything else escaped.
    parts = re.split(r"(</?em>)", body[1])
    out = []
    for p in parts:
        if p in ("<em>", "</em>"):
            out.append(p)
        else:
            out.append(html_mod.escape(html_mod.unescape(re.sub(r"<[^>]+>", "", p)), quote=False))
    return n, _WS.sub(" ", "".join(out)).strip()


def _classify_brackets(text: str, em: list[list[int]], book: int) -> list[list]:
    spans: list[list] = []
    opens = [i for i, c in enumerate(text) if c == "["]
    closes = [i for i, c in enumerate(text) if c == "]"]
    pairs = [(m.start(), m.end()) for m in re.finditer(r"\[[^\[\]]*\]", text)]
    if len(pairs) != len(opens) or len(opens) != len(closes):
        raise ValueError(f"kosmos book {book}: unbalanced or nested brackets")
    for s, e in pairs:
        inner = text[s + 1:e - 1].strip()
        italic = any(es < e and ee > s for es, ee in em)
        kind = "tr" if (not inner.startswith("=") and (italic or inner in UNITALICISED_TRANSLIT)) else "ed"
        spans.append([s, e, kind])
    return spans


def parse_book(book: int, book_html: str, greek_lines: set[int], gap_lines: set[int]) -> dict:
    """One book's HTML -> {text, bekker, marks, spans, notes, report}."""
    body_paras: list[str] = []
    notes: dict[int, str] = {}
    in_notes = False
    leftover = _PARA.sub("", book_html)
    leftover = re.sub(r"<a\s+name=\"[^\"]*\"\s*>\s*</a>", "", leftover)
    if leftover.strip():
        raise ValueError(f"kosmos book {book}: content outside <p>: {leftover.strip()[:120]!r}")
    for m in _PARA.finditer(book_html):
        attrs, inner = m.group(1) or "", m.group(2)
        plain = _plain(inner)
        if 'align="center"' in attrs:
            if not plain.startswith("Translated by Samuel Butler"):
                raise ValueError(f"kosmos book {book}: unexpected centred paragraph {plain[:80]!r}")
            continue
        if plain == "Notes" and "<strong>" in inner:
            in_notes = True
            continue
        if plain in ("__", "") or _DATE.match(plain) or plain.startswith("Return to top"):
            continue
        if in_notes:
            n, note = _parse_note(book, inner)
            notes[n] = note
            continue
        body_paras.append(inner)

    # Paragraphs -> one text, '\n' between paragraphs.
    text_parts: list[str] = []
    em: list[list[int]] = []
    nums: list[tuple[int, str]] = []
    fns: list[tuple[int, int]] = []
    base = 0
    for inner in body_paras:
        p = _ParaParser(book)
        p.feed(inner)
        p.close()
        r = p.result()
        if not r["text"] and not r["nums"]:
            continue
        if text_parts:
            base += 1  # the '\n'
        em += [[base + s, base + e] for s, e in r["em"]]
        # A number at the very end of a paragraph marks the next one's start.
        plen = len(r["text"])
        nums += [(base + o + (1 if o == plen else 0), lab) for o, lab in r["nums"]]
        fns += [(base + o, k) for o, k in r["fns"]]
        text_parts.append(r["text"])
        base += plen
    text = "\n".join(text_parts)
    nums = [(min(o, len(text)), lab) for o, lab in nums]

    spans = _classify_brackets(text, em, book) + [[s, e, "em"] for s, e in em]

    # Printed numbers -> group-break ticks and marks.
    first_line = min(greek_lines)
    ticks: list[dict] = []
    marks: list[dict] = []
    first_n = int(re.match(r"\d+", nums[0][1]).group(0)) if nums else None
    if first_n != first_line:
        ticks.append({"n": first_line, "offset": 0, "real": True, "implied": True})
    prev = 0
    for off, label in nums:
        n = int(re.match(r"\d+", label).group(0))
        reason = None
        if n not in greek_lines:
            reason = "not-in-greek"
            if n not in gap_lines:
                raise ValueError(f"kosmos book {book}: printed number {n} is neither a Greek line nor a declared gap")
        elif n <= prev:
            reason = "repeat" if n == prev else "out-of-sequence"
        elif ticks and off <= ticks[-1]["offset"] and not ticks[-1].get("implied"):
            raise ValueError(f"kosmos book {book}: numbers {ticks[-1]['n']} and {n} share offset {off}")
        if reason:
            marks.append({"n": n, "offset": off, "label": label, "reason": reason})
            continue
        if ticks and ticks[-1].get("implied") and off == 0:
            ticks.pop()  # the first printed number already sits at offset 0
        tick = {"n": n, "offset": off, "real": True}
        if label != str(n):
            tick["label"] = label  # e.g. Il. 7 "321–322"
        ticks.append(tick)
        prev = n

    # Footnote refs: insert the markers last, shifting every offset after them.
    refs = sorted(fns)
    ref_ns = [k for _, k in refs]
    if sorted(ref_ns) != sorted(notes) or len(set(ref_ns)) != len(ref_ns):
        raise ValueError(f"kosmos book {book}: footnote refs {ref_ns} do not match notes {sorted(notes)}")

    def shift(o: int, inclusive: bool) -> int:
        add = 0
        for ro, k in refs:
            if ro < o or (inclusive and ro == o):
                add += len(f"[^{TRANSLATION_ID}.{book}.{k}]")
        return o + add

    out, pos = [], 0
    for ro, k in refs:
        out.append(text[pos:ro])
        out.append(f"[^{TRANSLATION_ID}.{book}.{k}]")
        pos = ro
    out.append(text[pos:])
    final = "".join(out)
    # A marker sits after the word it annotates: spans ending at the ref keep
    # their end; points at the ref move past it.
    spans = sorted(([shift(s, True), shift(e, False), k] for s, e, k in spans), key=lambda x: (x[0], -x[1]))
    for t in ticks:
        t["offset"] = shift(t["offset"], True) if t["offset"] else 0
    for mk in marks:
        mk["offset"] = shift(mk["offset"], True)

    return {
        "text": final,
        "bekker": ticks,
        "marks": marks,
        "spans": spans,
        "notes": {f"{TRANSLATION_ID}.{book}.{k}": v for k, v in sorted(notes.items())},
        "report": {
            "printed_numbers": len(nums),
            "breaks": sum(1 for t in ticks if not t.get("implied")),
            "implied_start": any(t.get("implied") for t in ticks),
            "marks": marks,
            "footnotes": len(notes),
            "translit_brackets": sum(1 for s in spans if s[2] == "tr"),
            "editorial_brackets": sum(1 for s in spans if s[2] == "ed"),
        },
    }


def greek_line_sets(manifest: Manifest, spine: dict | None = None) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    """(book -> Greek line numbers, book -> declared-gap line numbers). From the
    spine when given; otherwise from the manifest's book ends and gaps."""
    gaps: dict[int, set[int]] = {}
    for g in manifest.data.get("expected_line_gaps") or []:
        gaps.setdefault(g["book"], set()).update(range(g["after"] + 1, g["next"]))
    lines: dict[int, set[int]] = {}
    if spine is not None:
        for seg in spine["segments"]:
            lines.setdefault(seg["book"], set()).update(l["n"] for l in seg["lines"])
    else:
        for b in manifest.books:
            last = int(str(b["end"]).split(".")[1])
            lines[b["n"]] = set(range(1, last + 1)) - gaps.get(b["n"], set())
    return lines, gaps


def parse_work(manifest: Manifest, spine: dict | None = None) -> dict[int, dict]:
    page = source_path(manifest.work_id).read_text(encoding="utf-8")
    lines, gaps = greek_line_sets(manifest, spine)
    return {
        b: parse_book(b, h, lines[b], gaps.get(b, set()))
        for b, h in split_books(page).items()
    }


def run(manifest: Manifest, spine: dict) -> dict:
    books = parse_work(manifest, spine)
    seg_by_book: dict[int, str] = {}
    for seg in spine["segments"]:
        if seg["book"] in seg_by_book:
            raise ValueError(f"kosmos: book {seg['book']} has more than one segment")
        seg_by_book[seg["book"]] = seg["id"]
    chunks: dict[str, list[dict]] = {}
    notes: dict[str, str] = {}
    report: dict[str, dict] = {}
    for b, r in books.items():
        piece = {"chapter": "1", "text": r["text"], "cont": False,
                 "bekker": r["bekker"], "spans": r["spans"]}
        if r["marks"]:
            piece["marks"] = [{k: m[k] for k in ("n", "offset", "label", "reason")} for m in r["marks"]]
        chunks[seg_by_book[b]] = [piece]
        notes.update(r["notes"])
        report[str(b)] = r["report"]
    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "overlays.json").write_text(
        json.dumps({TRANSLATION_ID: chunks}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "overlay_footnotes.json").write_text(
        json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "kosmos_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return {
        "books": len(books),
        "breaks": sum(r["breaks"] for r in report.values()),
        "marks": sum(len(r["marks"]) for r in report.values()),
        "footnotes": len(notes),
        "translit": sum(r["translit_brackets"] for r in report.values()),
        "editorial": sum(r["editorial_brackets"] for r in report.values()),
    }
