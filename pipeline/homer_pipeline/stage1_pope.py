"""Stage 1g: Alexander Pope's verse Iliad/Odyssey (Project Gutenberg #6130,
#3160) — the 'third' overlay slot (shared/lib/works.ts).

Pope is BOOK-anchored only. His couplets run 15-30% longer than the Greek
per book (measured across all 48 books below) and the ratio is highly
uneven WITHIN a book — a 5-scene spot check (see pipeline docs / the stage1
run report) found one canonical, slow-paced dialogue scene (the Iliad 6
Hector/Andromache farewell) whose proportional position drifted ~15% of the
book (~80 Greek lines) from where Pope actually renders it, alongside two
scenes that matched within a few percent. Per the binding degrade rule
(PROMPT.md), a coarse PROPORTIONAL intra-book gutter is not shipped: showing
readers a tick that can silently misplace them by 15% of a book is worse
than showing no tick at all. Each book carries exactly one anchor — a
`real: true` tick at its own first Greek line (book-level correspondence is
exact by construction, no interpolation) — and otherwise flows as a
continuous, unaligned reading text. This is a data decision, not a
placeholder: revisit only if a future pass builds real cross-lingual
anchors (e.g. a gloss aligner, as EN's Ross has).

Source structure (verified against the vendored plaintext, both works):
  - Standard PG header/footer, delimited by exact
    "*** START OF THE PROJECT GUTENBERG EBOOK" / "*** END OF ..." markers.
  - A Contents/Illustrations front matter block whose "BOOK N." and
    "CONCLUDING NOTE." entries are indented one space — real body headings
    are NOT indented, so a start-of-line match (no leading whitespace)
    disambiguates automatically; no separate front-matter skip is needed.
  - Exactly 24 unindented "BOOK <roman>." headings per work, strictly in
    order — split_books() asserts this and raises loudly otherwise.
  - Each book: heading, then (normally) an "ARGUMENT." marker, an ALL-CAPS
    one-line sub-title, and wrapped prose paragraphs summarizing the book,
    THEN the verse. Odyssey Book VIII carries the summary prose but omits
    the "ARGUMENT." marker itself (a source quirk, handled, not treated as
    an error). The argument is parsed and counted but deliberately NOT
    emitted (see parse_book / run docstrings) — no reader surface consumes
    a per-book note for an overlay-slot translation without touching
    stage7_emit.py / Reader.svelte, which is out of this module's blast
    radius; skipped-with-report per the written degrade rule.
  - Verse is identified by a purely typographic rule, not content sniffing:
    every line of 18th-century English verse capitalizes its first word
    regardless of syntax position, while the argument's wrapped prose
    paragraphs continue a sentence in lowercase after a soft wrap. A
    paragraph qualifies as verse when every line but its first starts with
    an uppercase letter (allowing a leading quotation mark); a lone
    ALL-CAPS line (the sub-title) stays classified as argument. Verified
    clean (non-empty argument, >=10 verse lines, no fallback path hit) on
    all 48 books.
  - The Iliad (only) carries 300 Buckley footnote markers, "[N]", inline in
    the verse, and a "CONCLUDING NOTE." critical essay followed by ~300
    numbered endnotes after Book XXIV's verse. Neither carries any
    Pope-authored content worth an apparatus pass on their own (the notes
    are Buckley's 19th-c. editorial commentary, not Pope's), so: the
    endnotes/essay tail is excised entirely (truncated at the unindented
    "CONCLUDING NOTE." heading) and the inline "[N]" markers are stripped
    from the verse text (there is no popup payload to point them at).
  - 71 "[Illustration: ] CAPTION" lines (Iliad only; the Odyssey PG text
    carries none) are always paragraph-initial (verified: 0 counter-examples
    across all 71) and are dropped whole.
  - Pope's plaintext carries no line numbering of his own (verified: no
    numeric gutter, only the footnote markers above), so there is nothing
    to "keep" — see the anchoring decision above for what's used instead.

Emits build/stage1/third_chunks.json in the same overlay shape stage7_emit
already reads for any 'third'-slot translation: {segment_id: [{chapter,
text, cont: False, bekker}]} — one piece per book (verse-line's citation
scheme has no chapter axis, so `chapter` just carries the book number, as
stage1_perseus_milestone_english's Butler overlay already does).
"""

from __future__ import annotations

import re
from pathlib import Path

from .config import BUILD_DIR, SOURCES_DIR, Manifest
from .stage1_common import write_json

_START_MARK = "*** START OF THE PROJECT GUTENBERG EBOOK"
_END_MARK = "*** END OF THE PROJECT GUTENBERG EBOOK"
_CONCLUDING_NOTE_RE = re.compile(r"^CONCLUDING NOTE\.\s*$", re.M)
_BOOK_HEAD_RE = re.compile(r"^BOOK ([IVXLC]+)\.\s*$")
_ARGUMENT_RE = re.compile(r"^ARGUMENT\.?(\[\d+\])?\s*$")
_FOOTNOTE_MARKER_RE = re.compile(r"\[\d{1,3}\]")
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _roman_to_int(s: str) -> int:
    total = prev = 0
    for ch in reversed(s):
        v = _ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def strip_pg_boilerplate(raw: str, source_name: str) -> str:
    """The text strictly between the PG START/END marker lines (exclusive of
    both). Raises if either exact marker is missing — no guessing at
    boilerplate bounds from a different PG layout."""
    si = raw.find(_START_MARK)
    ei = raw.find(_END_MARK)
    if si == -1 or ei == -1 or ei <= si:
        raise ValueError(
            f"{source_name}: Project Gutenberg START/END markers not found "
            f"(start={si}, end={ei}) — refusing to guess boilerplate bounds"
        )
    body_start = raw.find("\n", si)
    if body_start == -1:
        raise ValueError(f"{source_name}: malformed START marker line")
    return raw[body_start + 1 : ei]


def _truncate_endmatter(body: str) -> str:
    """Excise the critical essay + numbered footnote endnotes that follow
    Book XXIV's verse in the Iliad (see module docstring). A no-op when the
    unindented "CONCLUDING NOTE." heading isn't present (the Odyssey)."""
    m = _CONCLUDING_NOTE_RE.search(body)
    return body[: m.start()] if m else body


def split_books(text: str, n_books: int, source_name: str) -> list[tuple[int, str]]:
    """[(book_n, block_text), ...], each block running from its "BOOK N."
    heading up to (not including) the next one. Requires exactly `n_books`
    unindented headings in strict 1..n_books order (the indented
    Contents-page entries never match); raises loudly otherwise."""
    lines = text.split("\n")
    starts = [
        (i, _roman_to_int(m.group(1)))
        for i, l in enumerate(lines)
        if (m := _BOOK_HEAD_RE.match(l))
    ]
    found = [n for _, n in starts]
    if found != list(range(1, n_books + 1)):
        raise ValueError(
            f"{source_name}: expected BOOK 1..{n_books} headings in strict "
            f"order, found {found}"
        )
    blocks = []
    for idx, (line_i, n) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        blocks.append((n, "\n".join(lines[line_i:end])))
    return blocks


def _paragraphs(lines: list[str]) -> list[list[str]]:
    """Blank-line-delimited groups of non-blank lines, in order."""
    paras: list[list[str]] = []
    cur: list[str] = []
    for l in lines:
        if l.strip() == "":
            if cur:
                paras.append(cur)
                cur = []
        else:
            cur.append(l)
    if cur:
        paras.append(cur)
    return paras


def _is_upper_line(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _verse_start_index(paras: list[list[str]]) -> int:
    """Index into `paras` (paras[0] is the "BOOK N." heading paragraph) of
    the first verse paragraph. See the module docstring for the
    capitalization rule; also handles a book with no "ARGUMENT." marker at
    all (Odyssey Book VIII) by scanning from right after the heading."""
    start = 0
    for i, p in enumerate(paras[:3]):
        if _ARGUMENT_RE.match(p[0].strip()):
            start = i
            break
    for i in range(start + 1, len(paras)):
        p = paras[i]
        if len(p) == 1:
            if _is_upper_line(p[0]):
                continue  # the argument's ALL-CAPS sub-title
            return i
        if all((l.lstrip("\"“‘'( ")[:1] or " ").isupper() for l in p[1:]):
            return i
    return len(paras)


def parse_book(block_text: str, book_n: int) -> dict:
    """One book's argument prose (joined, paragraph breaks as "\\n"; NOT
    emitted downstream — see module docstring) and verse (a list of
    stanza/paragraph blocks, each a list of cleaned lines, with footnote
    markers and [Illustration] caption paragraphs removed) from its raw
    block text (heading through just before the next book's heading)."""
    paras = _paragraphs(block_text.split("\n"))
    vi = _verse_start_index(paras)
    arg_paras = [p for p in paras[1:vi] if not _ARGUMENT_RE.match(p[0].strip())]
    argument = "\n".join(" ".join(l.strip() for l in p) for p in arg_paras)

    verse_paragraphs: list[list[str]] = []
    footnote_markers_stripped = 0
    illustrations_dropped = 0
    for p in paras[vi:]:
        if p[0].strip().startswith("[Illustration"):
            illustrations_dropped += 1
            continue
        cleaned = []
        for l in p:
            stripped, n = _FOOTNOTE_MARKER_RE.subn("", l)
            footnote_markers_stripped += n
            stripped = stripped.rstrip()
            if stripped.strip():
                cleaned.append(stripped.strip())
        if cleaned:
            verse_paragraphs.append(cleaned)

    return {
        "book": book_n,
        "argument": argument,
        "verse_paragraphs": verse_paragraphs,
        "footnote_markers_stripped": footnote_markers_stripped,
        "illustrations_dropped": illustrations_dropped,
        "had_argument_marker": any(
            _ARGUMENT_RE.match(p[0].strip()) for p in paras[1:vi]
        ),
    }


def build_verse_text(verse_paragraphs: list[list[str]]) -> str:
    """Verse lines joined with a single "\\n" (rendered as a line break by
    the reader's flowParts — see shared/components/Reader.svelte); stanza
    (paragraph) blocks separated by a blank line ("\\n\\n"), matching Pope's
    own blank-line stanza breaks and preserving his verse structure rather
    than flattening it to prose."""
    return "\n\n".join("\n".join(p) for p in verse_paragraphs)


def parse_work(source_path: Path, n_books: int) -> dict[int, dict]:
    """{book: parse_book(...)} for all `n_books` books of one PG source."""
    raw = source_path.read_text(encoding="utf-8")
    body = strip_pg_boilerplate(raw, source_path.name)
    body = _truncate_endmatter(body)
    blocks = split_books(body, n_books, source_path.name)
    return {n: parse_book(text, n) for n, text in blocks}


def run(manifest: Manifest, spine: dict) -> dict:
    cfg = (manifest.data.get("english") or {}).get("third")
    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not cfg:
        write_json(out_dir / "third_chunks.json", {})
        return {"chunks": 0, "books": 0, "no_argument_marker": []}

    book_ns = [b["n"] for b in manifest.books]
    src_path = SOURCES_DIR / cfg["source"]
    parsed = parse_work(src_path, len(book_ns))

    first_line_by_book = {seg["book"]: seg["lines"][0]["n"] for seg in spine["segments"]}
    seg_id_by_book = {seg["book"]: seg["id"] for seg in spine["segments"]}

    chunks: dict[str, list[dict]] = {}
    no_argument_marker: list[int] = []
    footnote_markers_stripped = 0
    illustrations_dropped = 0
    for n in book_ns:
        book = parsed.get(n)
        if book is None:
            continue
        if not book["had_argument_marker"] and book["argument"]:
            no_argument_marker.append(n)
        footnote_markers_stripped += book["footnote_markers_stripped"]
        illustrations_dropped += book["illustrations_dropped"]
        text = build_verse_text(book["verse_paragraphs"])
        if not text:
            continue
        seg_id = seg_id_by_book.get(n)
        if seg_id is None:
            continue
        first_line = first_line_by_book.get(n, 1)
        chunks[seg_id] = [
            {
                "chapter": str(n),
                "text": text,
                "cont": False,
                # Book-level anchor only (see module docstring for the
                # degrade decision): the book's own first Greek line is an
                # exact, certain correspondence; no interior ticks.
                "bekker": [{"n": first_line, "offset": 0, "real": True}],
            }
        ]

    write_json(out_dir / "third_chunks.json", chunks)
    return {
        "chunks": len(chunks),
        "books": len(parsed),
        "no_argument_marker": no_argument_marker,
        "footnote_markers_stripped": footnote_markers_stripped,
        "illustrations_dropped": illustrations_dropped,
    }
