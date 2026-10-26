"""Stage 1b: Samuel Butler's own Odyssey (Longmans, 1900), read from the
Wikisource scan transcription, aligned to the Greek by Butler's OWN marginal
line numbers. Fills the ``ross`` overlay slot (english.secondary) in place of
the Perseus ``*-eng4.xml``, which is the Power–Nagy revision, not Butler
(John, 2026-10-26; CLAUDE.md "The Butler slot is Butler's own text").

Source: ``sources/butler/wikisource/odyssey/`` (provenance and findings in
``sources/INVENTORY.md``, section butler/). Two kinds of file:

  - ``book-NN.wiki``: the book's Wikisource wrapper. Its ``<pages index=…
    from=A to=B [exclude="x, y"] [fromsection=…] [tosection=…] />`` and
    ``<pages … include=N />`` tags fix which scan pages make the book and in
    what order. ``fromsection`` applies to the ``from`` page (that section to
    the page's end), ``tosection`` to the ``to`` page (page start to that
    section's end) — ProofreadPage's own semantics.
  - ``page-NNN.wiki``: one printed page's raw wikitext. ``<noinclude>`` (the
    page-quality tag, running head, footnote rule) is not page content.

Decisions, each one visible in ``butler_report.json``:

  - Plate pages (a ``[[File:…]]`` illustration with its caption, "To face
    p. N") are Butler's pictures, not the translation. The wrappers include
    six of them, some mid-book; they are left out of the text and listed.
    Blank pages (the plates' versos) carry nothing.
  - Pages join with one space, as Wikisource joins them, except: a page whose
    text ends in ``{{nop}}`` ends its paragraph (a blank line); a page ending
    in an em dash binds to the next with no space (Butler's dashes are set
    close: "world—and"); ``{{hws|part|whole}}`` / ``{{hwe|part|whole}}``, a
    word hyphenated across the page break, give the whole word once and glue
    whatever follows the ``hwe`` to it.
  - ``{{pline|N|l}}`` is Butler's printed marginal Greek line number at the
    head of a paragraph: one tick ``{n, offset, real: true}`` at that
    paragraph's first character. Misprinted numbers are corrected from
    ``sources/butler/pline-errata.yaml`` (book + printed number + occurrence,
    counted after the page-break collapse); a number repeated at the foot of
    one page and the head of the next, with no text between, is one marker.
    A number naming a Greek line the spine lacks (a declared vulgate gap) is
    snapped to the nearest line as the milestone module does; a number
    printed after a book's last words opens no English and is dropped. Every
    one of these is an anomaly in the report. A book whose first paragraph
    carries no number starts at its first Greek line, offset 0.
  - ``{{errata|printed|corrected|…}}`` (Butler's own corrigenda) and
    ``{{SIC|printed|correct}}`` (the transcribers' typo flags): the corrected
    reading is applied, both kinds (John, 2026-10-26), and every change is
    listed with its page (one ``{{SIC}}`` sits in a plate caption and leaves
    with its plate; it is listed ``in_plate``). A bare ``{{sic}}`` has no correction to apply; the
    printed text stands and the flag is listed.
  - ``{{Tooltip|text|note}}`` keeps ``text``; the notes say where Butler's
    book divisions split a sentence the Greek keeps whole, and are listed.
  - Each book opens with a heading ("BOOK I.") and Butler's one-line
    argument in small capitals. As with Pope's arguments (stage1_pope), the
    argument is recorded in the report but not emitted: no reader surface
    shows a per-book note for an overlay translation. The title furniture on
    the first page ("THE ODYSSEY / FOR ENGLISH READERS") is dropped too.
  - ``<ref>…</ref>`` is Butler's footnote. The prose gets an inline
    ``[^butler.<book>.<k>]`` marker, ``k`` counting the book's notes in
    order (the reader shows ``k``), glued to the word it follows; the note
    goes to ``build/stage1/butler_footnotes.json`` as HTML (text escaped;
    ``<em>`` for italics, ``<br>`` for verse lines, ``<p>`` when a note has
    more than one paragraph). stage7 merges that file into the work's
    ``footnotes.json``, which the reader's popup already reads.
    ``<ref name="x">`` + ``<ref follow="x">`` on the next page is ONE note
    continued across a page break: merged, never counted twice. A note on a
    book's argument has no place in the emitted text, so it is reported and
    not emitted.
  - Presentation templates reduce to their text (``sc``, ``smaller``,
    ``polytonic``, ``fine`` …) or vanish (``dhr``, ``rule``, ``rh``, ``nop``
    …). An unknown template is an error, so nothing unreviewed slips
    through. Italics (``''…''``) are kept in notes and dropped in the prose,
    which the overlay slot carries as plain text. ``{{parabr}}`` is a
    paragraph break inside a note; in the prose (once, Od. 4, scan p. 80,
    just before a note inside Telemachus's speech) it breaks no paragraph,
    since the speech runs on.

Paragraphs are kept as ``\\n`` in the text, as the Kosmos and Pope overlays
keep them; the reader's ``flowParts`` renders each as a paragraph break.
Output shape is the milestone module's ``ross_chunks.json`` exactly: one
piece per book, ``{"chapter": "<book>", "text", "cont": false, "bekker"}``.
"""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

import yaml

from .config import BUILD_DIR, SOURCES_DIR, Manifest
from .stage1_common import write_json
from .stage1_perseus_milestone_english import _nearest_line

TRANSLATION_ID = "butler"
NOTE_PREFIX = "butler"

_PAGES_TAG = re.compile(r"<pages\s+([^>]*?)/?>")
_ATTR = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|([^\s"/>]+))')
_NOINCLUDE = re.compile(r"<noinclude>.*?</noinclude>", re.S)
_SECTION_TAG = re.compile(r'<section\s+(?:begin|end)="[^"]*"\s*/>')
_REF = re.compile(r"<ref(\s[^>]*)?>(.*?)</ref>", re.S)
_REF_ATTR = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_LINK = re.compile(r"\[\[([^\[\]|]*)(?:\|([^\[\]]*))?\]\]")
_TEMPLATE = re.compile(r"\{\{([^{}]*)\}\}")
_NAMED_PARAM = re.compile(r"^\s*([A-Za-z][\w-]*)\s*=(.*)$", re.S)

_ERRATA = re.compile(r"\{\{errata\|([^{}|]*)\|([^{}|]*)(?:\|[^{}]*)?\}\}")
_SIC = re.compile(r"\{\{(?:SIC|sic)\|([^{}|]*)\|([^{}|]*)\}\}")
_SIC_BARE = re.compile(r"\{\{(?:SIC|sic)\}\}")
_TOOLTIP = re.compile(r"\{\{Tooltip\|([^{}|]*)\|([^{}|]*)\}\}")

# Sentinels (private-use / control characters never present in the source).
_S_PLINE = "\x01"   # \x01<n>\x01 — a printed line number
_S_REF = "\x02"     # \x02<i>\x02 — a footnote anchor (index into the note list)
_S_HWE = "\x03"     # end half of a word hyphenated across a page break
_S_PARA = "\x04"    # paragraph break inside a note
_S_BR = "\x05"      # line break inside a note
_S_EM = "\x06"      # italic toggle inside a note
_SENTINELS = (_S_PLINE, _S_REF, _S_HWE, _S_PARA, _S_BR, _S_EM)
_PROSE_TOKEN = re.compile(rf"{_S_PLINE}(\d+){_S_PLINE}|{_S_REF}(\d+){_S_REF}")

# Templates that reduce to their (last positional) text.
_TEXT_TEMPLATES = {"sc", "smaller", "larger", "xxxx-larger", "polytonic", "sp", "fine", "c"}
# Pure layout: vanish.
_DROP_TEMPLATES = {"dhr", "rule", "smallrefs", "rh", "nop"}


def source_dir(manifest: Manifest) -> Path:
    sec = (manifest.data.get("english") or {}).get("secondary") or {}
    return SOURCES_DIR / sec["source"]


# ── wrappers and pages ─────────────────────────────────────────────────────

def parse_wrapper(text: str) -> list[tuple[int, str | None, str | None]]:
    """A book wrapper -> ordered [(page, fromsection, tosection)]."""
    out: list[tuple[int, str | None, str | None]] = []
    for m in _PAGES_TAG.finditer(text):
        attrs = {a.group(1): (a.group(2) if a.group(2) is not None else a.group(3))
                 for a in _ATTR.finditer(m.group(1))}
        if "include" in attrs and "from" not in attrs:
            for p in attrs["include"].split(","):
                out.append((int(p), None, None))
            continue
        lo, hi = int(attrs["from"]), int(attrs["to"])
        excl = {int(x) for x in (attrs.get("exclude") or "").replace(" ", "").split(",") if x}
        for p in range(lo, hi + 1):
            if p in excl:
                continue
            out.append((p, attrs.get("fromsection") if p == lo else None,
                        attrs.get("tosection") if p == hi else None))
    if not out:
        raise ValueError("book wrapper has no <pages> tag")
    return out


def page_body(raw: str, fromsection: str | None, tosection: str | None) -> str:
    body = _NOINCLUDE.sub("", raw)
    if fromsection:
        tag = f'<section begin="{fromsection}" />'
        if tag not in body:
            raise ValueError(f"section {fromsection!r} not on page")
        body = body[body.index(tag):]
    if tosection:
        tag = f'<section end="{tosection}" />'
        if tag not in body:
            raise ValueError(f"section {tosection!r} not on page")
        body = body[:body.index(tag)]
    return _SECTION_TAG.sub("", body)


def _in_ref(body: str, pos: int) -> bool:
    before = body[:pos]
    return before.count("<ref") > before.count("</ref>")


def apply_corrections(body: str, page: int, book: int, log: dict, plate: bool = False) -> str:
    """{{errata}}, {{SIC}}, bare {{sic}} and {{Tooltip}}, each logged
    (``in_plate``: on a plate page, whose text is then left out)."""
    def rec(kind, m, printed, used):
        log[kind].append({"book": book, "page": page, "printed": printed, "applied": used,
                          "in_note": _in_ref(body, m.start()), "in_plate": plate})

    def errata(m):
        rec("errata", m, m.group(1), m.group(2))
        return m.group(2)

    def sic(m):
        rec("sic", m, m.group(1), m.group(2))
        return m.group(2)

    def sic_bare(m):
        ctx = re.sub(r"\s+", " ", body[max(0, m.start() - 40):m.start()])
        log["sic_bare"].append({"book": book, "page": page, "context": ctx,
                                "in_note": _in_ref(body, m.start())})
        return ""

    def tooltip(m):
        log["tooltips"].append({"book": book, "page": page, "text": m.group(1),
                                "note": m.group(2)})
        return m.group(1)

    body = _ERRATA.sub(errata, body)
    body = _SIC.sub(sic, body)
    body = _SIC_BARE.sub(sic_bare, body)
    return _TOOLTIP.sub(tooltip, body)


def assemble_book(src: Path, book: int, log: dict) -> str:
    """The book's wikitext: its pages in wrapper order, corrected, joined."""
    wrapper = (src / f"book-{book:02d}.wiki").read_text(encoding="utf-8")
    out = ""
    ends_para = False
    for page, fsec, tsec in parse_wrapper(wrapper):
        raw = (src / f"page-{page:03d}.wiki").read_text(encoding="utf-8")
        body = page_body(raw, fsec, tsec)
        plate = "[[File:" in body
        body = apply_corrections(body, page, book, log, plate).strip()
        if plate:
            caption = re.sub(r"\s+", " ", _LINK.sub("", body))[:120]
            log["plates_dropped"].append({"book": book, "page": page, "caption": caption})
            continue
        if not body:
            continue
        # A section cut falls between paragraphs (a plate sits there), so
        # both sides of it are paragraph ends.
        page_ends_para = bool(re.search(r"\{\{nop\}\}$", body)) or bool(tsec)
        if body.endswith("{{nop}}"):
            body = body[: -len("{{nop}}")].rstrip()
        if out:
            if ends_para or fsec:
                out += "\n\n"
            elif not out.endswith("—"):
                out += " "
        out += body
        ends_para = page_ends_para
    return out


# ── templates ──────────────────────────────────────────────────────────────

def _params(inner: str) -> tuple[str, list[str], dict[str, str]]:
    parts = inner.split("|")
    name = parts[0].strip()
    pos: list[str] = []
    named: dict[str, str] = {}
    for p in parts[1:]:
        m = _NAMED_PARAM.match(p)
        if m:
            named[m.group(1)] = m.group(2)
        else:
            pos.append(p)
    return name, pos, named


def reduce_templates(text: str, mode: str, book: int, report: dict) -> str:
    """Innermost-first template reduction. ``mode`` is "prose" or "note"."""
    def one(m):
        name, pos, named = _params(m.group(1))
        key = name.lower()
        if key == "pline":
            if mode != "prose":
                raise ValueError(f"book {book}: pline inside a note")
            return f"{_S_PLINE}{int(pos[0])}{_S_PLINE}"
        if key in _DROP_TEMPLATES:
            return ""
        if key == "ph":
            report["headings"][book] = pos[0].strip()
            return ""
        if key == "center block" and named.get("class") == "summary":
            report["arguments"][book] = pos[-1]
            return ""
        if key == "c" and mode == "prose":
            # Centred display type in the running text: only the title on the
            # first page ("THE ODYSSEY / FOR ENGLISH READERS").
            report["furniture_dropped"].append({"book": book, "text": " ".join(pos[-1].split())})
            return ""
        if key in _TEXT_TEMPLATES:
            return pos[-1] if pos else ""
        if key == "hws":
            return pos[1]
        if key == "hwe":
            return _S_HWE
        if key == "gap":
            return " "
        if key == "fqm":
            return '"'
        if key == "...":
            return "…"
        if key == "parabr":
            if mode == "note":
                return _S_PARA
            report["prose_parabr_ignored"].append(book)
            return " "
        if key in ('" \'', "' \""):
            return key.replace(" ", "")
        raise ValueError(f"book {book}: unhandled template {{{{{m.group(1)[:60]}}}}}")

    prev = None
    while prev != text:
        prev = text
        text = _TEMPLATE.sub(one, text)
    return text


def _links(text: str) -> str:
    return _LINK.sub(lambda m: m.group(2) if m.group(2) is not None else m.group(1), text)


def _italics(text: str, keep: bool) -> str:
    return text.replace("''", _S_EM if keep else "")


def note_html(raw: str, book: int, report: dict) -> str:
    """A note's wikitext -> HTML (escaped text, <em>, <br>, <p>)."""
    t = _links(raw)
    t = re.sub(r"<P>", _S_PARA, t, flags=re.I)
    t = re.sub(r"</P>", _S_PARA, t, flags=re.I)
    t = re.sub(r"<br\s*/?>", _S_BR, t, flags=re.I)
    t = reduce_templates(t, "note", book, report)
    t = re.sub(r"\n[ \t]*\n", _S_PARA, t)
    t = _italics(t, keep=True)
    if "<" in t or "{{" in t or "}}" in t or "[[" in t:
        raise ValueError(f"book {book}: unconverted markup in note {t[:80]!r}")
    paras = []
    for para in t.split(_S_PARA):
        para = re.sub(r"\s+", " ", para)
        para = re.sub(rf"\s*{_S_BR}\s*", _S_BR, para).strip(" " + _S_BR)
        if not para:
            continue
        if para.count(_S_EM) % 2:
            raise ValueError(f"book {book}: unbalanced italics in note {para[:80]!r}")
        para = html_mod.escape(para, quote=False)
        bits = para.split(_S_EM)
        para = "".join(b if i % 2 == 0 else f"<em>{b}</em>" for i, b in enumerate(bits))
        paras.append(para.replace(_S_BR, "<br>"))
    if not paras:
        raise ValueError(f"book {book}: empty note")
    if len(paras) == 1:
        return paras[0]
    return "".join(f"<p>{p}</p>" for p in paras)


# ── one book ───────────────────────────────────────────────────────────────

def parse_book(src: Path, book: int, valid_lines: set[int], errata: list[dict],
               log: dict) -> dict:
    """One book -> {text, bekker, notes, plines, report bits}."""
    raw = assemble_book(src, book, log)

    # Footnotes out first (they hold templates and can cross pages).
    notes_raw: list[str] = []
    named: dict[str, int] = {}

    def ref(m):
        attrs = dict(_REF_ATTR.findall(m.group(1) or ""))
        if "group" in attrs:
            raise ValueError(f"book {book}: unexpected ref group {attrs['group']!r}")
        if "follow" in attrs:
            i = named[attrs["follow"]]
            notes_raw[i] += " " + m.group(2)
            log["note_continuations"].append({"book": book, "name": attrs["follow"]})
            return ""
        notes_raw.append(m.group(2))
        if "name" in attrs:
            named[attrs["name"]] = len(notes_raw) - 1
        return f"{_S_REF}{len(notes_raw) - 1}{_S_REF}"

    body = _REF.sub(ref, raw)
    if "<ref" in body or "</ref>" in body:
        raise ValueError(f"book {book}: unbalanced <ref>")
    body = _links(body)
    body = reduce_templates(body, "prose", book, log)
    body = re.sub(rf"\s*{_S_HWE}", "", body)
    log["prose_italics_dropped"] += body.count("''") // 2
    body = _italics(body, keep=False)
    body = re.sub(r"<br\s*/?>", " ", body, flags=re.I)
    if any(s in body for s in ("<", "{{", "}}", "[[")):
        bad = re.search(r"<|\{\{|\}\}|\[\[", body)
        raise ValueError(f"book {book}: unconverted markup {body[bad.start():bad.start() + 60]!r}")

    # A note inside the argument has no place in the emitted text.
    argument = log["arguments"].get(book, "")
    arg_refs = [int(i) for i in re.findall(rf"{_S_REF}(\d+){_S_REF}", argument)]
    if argument:
        log["arguments"][book] = " ".join(re.sub(rf"{_S_REF}\d+{_S_REF}", "", argument).split())

    # Paragraphs -> text with markers; printed numbers -> raw plines.
    text = ""
    plines: list[dict] = []          # every printed number, in book order
    pending: list[dict] = []         # numbers printed after a paragraph's last word
    note_order: list[int] = []       # notes_raw indices, in marker order
    for para in re.split(r"\n[ \t]*\n", body):
        para = re.sub(r"\s+", " ", para).strip()
        if not para:
            continue
        if text:
            text += "\n"
        start = len(text)
        for p in pending:            # they open this paragraph
            p["offset"] = start
        pending = []
        pos = 0
        for m in _PROSE_TOKEN.finditer(para):
            text += para[pos:m.start()]
            pos = m.end()
            if m.group(1) is not None:
                p = {"n_printed": int(m.group(1)), "offset": len(text)}
                plines.append(p)
                rest = _PROSE_TOKEN.sub("", para[pos:]).strip()
                if not rest:
                    pending.append(p)
                elif text[start:].strip():
                    log["anomalies"].append({"kind": "pline_mid_paragraph", "book": book,
                                             "n_raw": p["n_printed"],
                                             "context": text[-50:] + " ‖ " + rest[:30]})
            else:
                text = text.rstrip(" ")
                k = len(note_order) + 1
                note_order.append(int(m.group(2)))
                text += f"[^{NOTE_PREFIX}.{book}.{k}]"
        text += para[pos:]
        text = text.rstrip(" ")
        if not text[start:]:
            text = text[:start].rstrip("\n")
    for p in pending:                # printed after the book's last words
        p["offset"] = len(text)

    # Page-break collapse: the same number twice with no text between.
    collapsed: list[dict] = []
    for i, p in enumerate(plines):
        if collapsed and collapsed[-1]["n_printed"] == p["n_printed"] and \
                not text[collapsed[-1]["offset"]:p["offset"]].strip():
            log["anomalies"].append({"kind": "pline_page_break_duplicate", "book": book,
                                     "n_raw": p["n_printed"]})
            continue
        collapsed.append(p)

    # Errata: book + printed number + occurrence (after the collapse).
    seen: dict[int, int] = {}
    for p in collapsed:
        seen[p["n_printed"]] = seen.get(p["n_printed"], 0) + 1
        p["n"] = p["n_printed"]
        for e in errata:
            if e["book"] == book and e["printed"] == p["n_printed"] and e["occurrence"] == seen[p["n_printed"]]:
                p["n"] = e["correct"]
                e["_applied"] = e.get("_applied", 0) + 1
                log["pline_errata_applied"].append({"book": book, "printed": e["printed"],
                                                    "occurrence": e["occurrence"],
                                                    "correct": e["correct"]})

    # Plines -> ticks.
    valid_sorted = sorted(valid_lines)
    ticks: list[dict] = []
    last_n = 0
    for p in collapsed:
        n = p["n"]
        if p["offset"] >= len(text):
            log["anomalies"].append({"kind": "pline_after_last_words", "book": book, "n_raw": n})
            continue
        if n not in valid_lines:
            if not valid_sorted or n < valid_sorted[0] or n > valid_sorted[-1]:
                log["anomalies"].append({"kind": "pline_out_of_range", "book": book, "n_raw": n})
                continue
            snapped = _nearest_line(valid_sorted, n)
            log["anomalies"].append({"kind": "pline_gap_snap", "book": book, "n_raw": n,
                                     "snapped_to": snapped})
            n = snapped
        if n <= last_n:
            log["anomalies"].append({"kind": "pline_out_of_order", "book": book, "n_raw": n,
                                     "last_accepted": last_n})
            continue
        ticks.append({"n": n, "offset": p["offset"], "real": True})
        last_n = n
    if valid_sorted and (not ticks or ticks[0]["offset"] > 0):
        if ticks and ticks[0]["n"] <= valid_sorted[0]:
            raise ValueError(f"book {book}: first printed number {ticks[0]['n']} precedes the book start")
        ticks.insert(0, {"n": valid_sorted[0], "offset": 0, "real": True})
    elif ticks and ticks[0]["n"] != valid_sorted[0]:
        log["anomalies"].append({"kind": "book_start_uncovered", "book": book,
                                 "first_tick": ticks[0]["n"]})

    notes: dict[str, str] = {}
    for k, i in enumerate(note_order, 1):
        notes[f"{NOTE_PREFIX}.{book}.{k}"] = note_html(notes_raw[i], book, log)
    for i in arg_refs:
        log["argument_notes"].append({"book": book, "html": note_html(notes_raw[i], book, log)})
    placed = set(note_order) | set(arg_refs)
    if placed != set(range(len(notes_raw))):
        raise ValueError(f"book {book}: notes {sorted(set(range(len(notes_raw))) - placed)} have no anchor")

    return {"text": text, "bekker": ticks, "notes": notes,
            "plines_printed": len(plines), "plines_distinct": len(collapsed)}


def _new_log() -> dict:
    return {"errata": [], "sic": [], "sic_bare": [], "tooltips": [], "plates_dropped": [],
            "note_continuations": [], "headings": {}, "arguments": {}, "argument_notes": [],
            "furniture_dropped": [], "prose_parabr_ignored": [], "prose_italics_dropped": 0,
            "pline_errata_applied": [], "anomalies": []}


def load_errata(work_key: str = "odyssey") -> list[dict]:
    data = yaml.safe_load((SOURCES_DIR / "butler" / "pline-errata.yaml").read_text(encoding="utf-8"))
    return [dict(e) for e in data.get(work_key) or []]


def parse_work(manifest: Manifest, valid_lines_by_book: dict[int, set[int]]) -> dict:
    src = source_dir(manifest)
    errata = load_errata(manifest.work_id)
    log = _new_log()
    books: dict[int, dict] = {}
    for b in manifest.books:
        books[b["n"]] = parse_book(src, b["n"], valid_lines_by_book.get(b["n"], set()), errata, log)
    unmatched = [e for e in errata if e.get("_applied") != 1]
    if unmatched:
        raise ValueError(f"pline errata not matched exactly once: {unmatched}")
    for book, r in books.items():
        if any(s in t for s in _SENTINELS for t in (r["text"], *r["notes"].values())):
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
    summary = {
        "books": len(books),
        "plines_printed": sum(r["plines_printed"] for r in books.values()),
        "plines_distinct": sum(r["plines_distinct"] for r in books.values()),
        "ticks": sum(len(r["bekker"]) for r in books.values()),
        "footnotes": len(notes),
        "argument_notes": len(log["argument_notes"]),
        "errata": len(log["errata"]),
        "sic": len(log["sic"]),
        "sic_bare": len(log["sic_bare"]),
        "pline_errata": len(log["pline_errata_applied"]),
        "plates_dropped": len(log["plates_dropped"]),
        "anomalies": len(log["anomalies"]),
    }
    report = {
        "work": manifest.work_id,
        "translation": TRANSLATION_ID,
        "source": str(source_dir(manifest).relative_to(SOURCES_DIR)),
        "summary": summary,
        "ticks_by_book": {str(b): len(r["bekker"]) for b, r in books.items()},
        **log,
        "headings": {str(k): v for k, v in log["headings"].items()},
        "arguments": {str(k): v for k, v in log["arguments"].items()},
    }
    write_json(out_dir / "butler_report.json", report)
    return summary
