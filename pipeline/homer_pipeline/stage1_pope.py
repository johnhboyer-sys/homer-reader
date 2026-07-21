"""Stage 1g: Alexander Pope's verse Iliad/Odyssey (Project Gutenberg #6130,
#3160) — the 'third' overlay slot (shared/lib/works.ts).

Pope has no line numbering of his own, so alignment to the Greek vulgate can
never be exact by parsing his text alone. Two anchoring strategies:

  - BOOK-anchored (the original, permanent fallback): each book gets exactly
    one `real: true` tick at its own first Greek line — a book-level
    correspondence that is exact by construction, no interpolation. His
    couplets run 15-30% longer than the Greek per book (measured across all
    48 books) and the ratio is highly uneven WITHIN a book — a 5-scene spot
    check (see pipeline docs / the stage1 run report) found one canonical,
    slow-paced dialogue scene (the Iliad 6 Hector/Andromache farewell) whose
    proportional position drifted ~15% of the book (~80 Greek lines) from
    where Pope actually renders it, alongside two scenes that matched within
    a few percent. Per the binding degrade rule (PROMPT.md), a coarse
    PROPORTIONAL intra-book gutter is NEVER shipped: showing readers a tick
    that can silently misplace them by 15% of a book is worse than showing
    no tick at all. This remains the fallback for any book the curated
    dataset below doesn't (yet) cover — see load_scene_starts.

  - SCENE-anchored (supersedes the book-only degrade wherever both a staged
    scene list and a curated anchor exist): resolve_scene_anchors resolves
    each non-first scene-start line to a `real: true` tick by finding the
    EXACT, UNIQUE substring in Pope's own built verse text that a human
    editor identified as where that scene begins in his rendering — see
    sources/pope/scene-anchors-{iliad,odyssey}.json (schema documented on
    load_scene_anchor_dataset). This is still not interpolation: every tick
    is either a real substring match or absent (status: "unanchored",
    skipped) — there is no nearest-match fallback and no proportional guess.
    A resolution that doesn't actually match Pope's text cleanly (ambiguous
    or absent anchor text, offsets out of order, an anchor that doesn't
    begin at a verse-line start, a scene start missing its one required
    entry) is a hard ValueError at stage1 — a scene dataset that disagrees
    with Pope's actual text is a data bug to fix, not something to degrade
    around. A book simply not yet present in the staged scenes
    (apparatus/staging — see load_scene_starts) is not an error: it keeps
    its book-level fallback tick and is reported, not failed.

  The curated dataset FILE itself is required once a work declares a `third`
  (Pope) translation: a missing sources/pope/scene-anchors-<work>.json is a
  hard error at stage1 (see load_scene_anchor_dataset). Nothing under
  sources/ is created or modified by this module.

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
    numeric gutter, only the footnote markers above), so book-level anchors
    plus the curated scene dataset are the only source of alignment.

Emits build/stage1/third_chunks.json in the same overlay shape stage7_emit
already reads for any 'third'-slot translation: {segment_id: [{chapter,
text, cont: False, bekker}]} — one piece per book (verse-line's citation
scheme has no chapter axis, so `chapter` just carries the book number, as
stage1_perseus_milestone_english's Butler overlay already does).
"""

from __future__ import annotations

import json
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

_SENTENCE_ENDERS = (".", "?", "!")
_CLOSING_QUOTES = "'\"’”)"

_ANCHOR_STATUSES = ("verified", "draft", "unanchored")


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


# ── curated scene-anchor dataset (sources/pope/scene-anchors-<work>.json) ──


def _dataset_path(work_id: str) -> Path:
    return SOURCES_DIR / "pope" / f"scene-anchors-{work_id}.json"


def dataset_available(work_id: str) -> bool:
    """True once sources/pope/scene-anchors-<work_id>.json has landed. Lets a
    caller check before calling load_scene_anchor_dataset, which raises when
    the file is absent."""
    return _dataset_path(work_id).exists()


def load_scene_anchor_dataset(work_id: str) -> dict:
    """Load and schema-check sources/pope/scene-anchors-<work_id>.json:
    `{_source, _semantics, work, anchors: [{book, n, anchor, status, note?}]}`
    — `status` is one of verified|draft|unanchored; `anchor` is a non-empty
    substring of that book's Pope verse text for verified/draft entries, and
    must be null for unanchored ones. A missing file is a hard error: once a
    work declares a `third` (Pope) translation, this dataset is load-bearing
    for every scene tick, not an optional enhancement (see module
    docstring)."""
    path = _dataset_path(work_id)
    if not path.exists():
        raise ValueError(
            f"pope scene-anchor dataset missing: {path} — stage1 requires a "
            f"curated scene-anchors-{work_id}.json once english.third (pope) "
            f"is configured; see stage1_pope module docstring"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("work") != work_id:
        raise ValueError(f"{path.name}: work {raw.get('work')!r} does not match {work_id!r}")
    anchors = raw.get("anchors")
    if not isinstance(anchors, list):
        raise ValueError(f"{path.name}: anchors must be a list")
    for i, entry in enumerate(anchors):
        if not isinstance(entry, dict):
            raise ValueError(f"{path.name}: anchors[{i}] must be an object")
        if not isinstance(entry.get("book"), int) or not isinstance(entry.get("n"), int):
            raise ValueError(f"{path.name}: anchors[{i}].book and .n must be integers")
        status = entry.get("status")
        if status not in _ANCHOR_STATUSES:
            raise ValueError(
                f"{path.name}: anchors[{i}].status must be one of "
                f"{_ANCHOR_STATUSES}, got {status!r}"
            )
        if status == "unanchored":
            if entry.get("anchor") is not None:
                raise ValueError(
                    f"{path.name}: anchors[{i}] status 'unanchored' must have anchor: null"
                )
        elif not isinstance(entry.get("anchor"), str) or not entry["anchor"]:
            raise ValueError(f"{path.name}: anchors[{i}].anchor must be a non-empty string")
    return raw


def load_scene_starts(manifest: Manifest) -> dict[int, list[int]]:
    """book number -> this book's staged scene-start Greek line numbers (the
    first line of each apparatus scene), read via
    apparatus_scenes.merge_staging (pure, schema-validated — see that
    module's docstring). A book with no staged scenes yet is simply absent
    from the returned dict; run() treats that as "keep the book-level
    fallback tick", not an error — apparatus drafting and Pope anchor-dataset
    drafting run on independent schedules."""
    from . import apparatus_scenes

    doc = apparatus_scenes.merge_staging(manifest)
    return {
        book["book"]: [scene["lines"][0] for scene in book.get("scenes", [])]
        for book in doc.get("books", [])
        if isinstance(book.get("book"), int)
    }


def resolve_scene_anchors(
    text: str, entries: list[dict], scene_starts: list[int], book_n: int
) -> list[dict]:
    """Resolve one book's curated Pope scene-anchor entries (already filtered
    to this book) against its built verse text and its staged scene-start
    Greek line numbers. Pure: no I/O, no side effects.

    Returns one result dict per input entry, sorted by `n`:
    `{"n", "offset", "status", "warning"}` — `offset` is None for a
    `status: "unanchored"` entry (no tick emitted for it; the caller counts
    it); `warning` carries a non-fatal sentence-boundary note or is None.

    Hard-fails (ValueError naming book, n, and an anchor snippet) rather
    than degrading, on:
      - an entry's n is not one of this book's staged scene starts;
      - an entry's n equals the book's FIRST scene start — that scene is
        auto-anchored by run() with its own book-opening tick, so a
        curated entry for it would emit a duplicate tick;
      - a scene start other than the FIRST (which needs no entry — run()
        gives it an automatic book-opening tick) has anything but exactly
        one entry;
      - a verified/draft entry's anchor text occurs zero or 2+ times in the
        book's text (no nearest-match fallback);
      - a resolved anchor does not begin at a verse-line start (offset 0, or
        immediately preceded by "\\n");
      - resolved offsets are not strictly increasing in n order.

    Non-fatal: when the non-whitespace text immediately before a resolved
    anchor doesn't end in . ? ! (optionally followed by a closing quote), a
    warning is attached to that entry's result instead of raising — Pope's
    couplets don't always break exactly on scene boundaries, and that's
    worth a human's attention, not a build failure.
    """
    scene_start_set = set(scene_starts)
    first_start = scene_starts[0] if scene_starts else None
    non_first_starts = [s for s in scene_starts if s != first_start]

    entries_by_n: dict[int, list[dict]] = {}
    for entry in entries:
        n = entry.get("n")
        if n not in scene_start_set:
            raise ValueError(
                f"book {book_n}: anchor entry n={n} is not one of this "
                f"book's staged scene starts {sorted(scene_start_set)}"
            )
        entries_by_n.setdefault(n, []).append(entry)

    if first_start is not None and entries_by_n.get(first_start):
        raise ValueError(
            f"book {book_n}: scene start n={first_start} is this book's "
            f"first scene, which is auto-anchored by run() — remove the "
            f"curated entry for it (it would emit a duplicate tick)"
        )

    for start in non_first_starts:
        count = len(entries_by_n.get(start, []))
        if count != 1:
            raise ValueError(
                f"book {book_n}: scene start n={start} has {count} anchor "
                f"entries (expected exactly 1)"
            )

    results: list[dict] = []
    for entry in sorted(entries, key=lambda e: e["n"]):
        n = entry["n"]
        status = entry.get("status", "verified")
        anchor = entry.get("anchor")
        if status == "unanchored":
            results.append({"n": n, "offset": None, "status": status, "warning": None})
            continue
        if not anchor:
            raise ValueError(
                f"book {book_n}: anchor entry n={n} has status {status!r} "
                f"but no anchor text"
            )
        snippet = anchor if len(anchor) <= 60 else anchor[:57] + "..."
        occurrences = text.count(anchor)
        if occurrences != 1:
            raise ValueError(
                f"book {book_n}: anchor n={n} {snippet!r} occurs "
                f"{occurrences} times in the book's text (expected exactly 1)"
            )
        offset = text.index(anchor)
        if offset != 0 and text[offset - 1] != "\n":
            raise ValueError(
                f"book {book_n}: anchor n={n} {snippet!r} does not begin at "
                f"a verse-line start"
            )
        warning = None
        preceding = text[:offset].rstrip()
        if preceding:
            trimmed = preceding.rstrip(_CLOSING_QUOTES)
            if not trimmed.endswith(_SENTENCE_ENDERS):
                warning = (
                    f"book {book_n}: anchor n={n} {snippet!r} follows text "
                    f"not ending in . ? ! — ...{trimmed[-30:]!r}"
                )
        results.append({"n": n, "offset": offset, "status": status, "warning": warning})

    prev_offset = None
    for r in results:
        if r["offset"] is None:
            continue
        if prev_offset is not None and r["offset"] <= prev_offset:
            raise ValueError(
                f"book {book_n}: resolved anchor offsets are not strictly "
                f"increasing at n={r['n']}"
            )
        prev_offset = r["offset"]

    return results


def run(manifest: Manifest, spine: dict) -> dict:
    cfg = (manifest.data.get("english") or {}).get("third")
    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not cfg:
        write_json(out_dir / "third_chunks.json", {})
        return {
            "chunks": 0,
            "books": 0,
            "no_argument_marker": [],
            "anchors_resolved": 0,
            "unanchored": [],
            "draft_count": 0,
            "sentence_warnings": [],
            "books_without_staged_scenes": [],
        }

    book_ns = [b["n"] for b in manifest.books]
    src_path = SOURCES_DIR / cfg["source"]
    parsed = parse_work(src_path, len(book_ns))

    first_line_by_book = {seg["book"]: seg["lines"][0]["n"] for seg in spine["segments"]}
    seg_id_by_book = {seg["book"]: seg["id"] for seg in spine["segments"]}

    # The curated anchor dataset is load-bearing, not optional (see module
    # docstring): a missing file raises here, before any chunk is written.
    dataset = load_scene_anchor_dataset(manifest.work_id)
    entries_by_book: dict[int, list[dict]] = {}
    for entry in dataset["anchors"]:
        entries_by_book.setdefault(entry["book"], []).append(entry)

    scene_starts = load_scene_starts(manifest)

    chunks: dict[str, list[dict]] = {}
    no_argument_marker: list[int] = []
    footnote_markers_stripped = 0
    illustrations_dropped = 0
    anchors_resolved = 0
    unanchored: list[tuple[int, int]] = []
    draft_count = 0
    sentence_warnings: list[str] = []
    books_without_staged_scenes: list[int] = []

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
        # The book-opening tick: real by construction (the book's own first
        # Greek line), independent of whether scene data covers this book.
        ticks = [{"n": first_line, "offset": 0, "real": True}]

        starts = scene_starts.get(n)
        if starts is None:
            # Not yet staged in apparatus/staging — keep the book-level
            # fallback tick (see module docstring); reported, not fatal.
            books_without_staged_scenes.append(n)
        else:
            resolved = resolve_scene_anchors(text, entries_by_book.get(n, []), starts, n)
            for r in resolved:
                if r["offset"] is None:
                    unanchored.append((n, r["n"]))
                    continue
                if r["status"] == "draft":
                    draft_count += 1
                if r["warning"]:
                    sentence_warnings.append(r["warning"])
                ticks.append({"n": r["n"], "offset": r["offset"], "real": True})
                anchors_resolved += 1
            ticks.sort(key=lambda t: t["offset"])

        chunks[seg_id] = [
            {
                "chapter": str(n),
                "text": text,
                "cont": False,
                "bekker": ticks,
            }
        ]

    write_json(out_dir / "third_chunks.json", chunks)
    return {
        "chunks": len(chunks),
        "books": len(parsed),
        "no_argument_marker": no_argument_marker,
        "footnote_markers_stripped": footnote_markers_stripped,
        "illustrations_dropped": illustrations_dropped,
        "anchors_resolved": anchors_resolved,
        "unanchored": unanchored,
        "draft_count": draft_count,
        "sentence_warnings": sentence_warnings,
        "books_without_staged_scenes": books_without_staged_scenes,
    }
