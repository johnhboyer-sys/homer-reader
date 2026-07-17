"""Stage 1e: milestoned Perseus English prose (Murray/Butler) for verse-line
works (Homer), aligned to the Greek spine by the TEI's own ``<milestone
unit="line">`` anchors.

Both the Murray (Loeb) and Butler prose TEIs share one structure: ``book``
divs containing ``card`` divs containing ``<p>`` prose, with a ``<milestone
n="N" unit="line"/>`` dropped inline roughly every 5 (Murray, Butler Iliad) to
~13 (Butler Odyssey) lines. This module is parameterized by edition file +
translation id so ONE parser serves both translations for both epics.

Verse-line's citation scheme has no letter axis: a Greek spine "column" IS the
book number, so each book is exactly ONE spine segment (``stage1_perseus_
greek.py``). This module therefore builds exactly one chunk per book — reusing
``StandoffChunkMixin`` with book/column pinned for the whole walk — and anchors
the translation to the Greek lineation with a ``bekker``-shaped gutter of REAL
milestone ticks (``{n, offset, real: true}``; no proportional interpolation,
since these TEIs carry genuine anchors — unlike the Ross/archive path, which
has none). Murray fills the primary ``english`` slot; Butler fills the
``ross`` overlay slot (single un-chaptered piece per book — verse-line has no
chapter concept, so ``chapterStarts`` stays empty and the reader always picks
that lone piece). Both shapes are byte-compatible with what stage7/the Reader
already consume — no reader changes required.

Loeb ``<note>`` footnotes (Murray only) are spliced into the prose as inline
``[^label]`` markers (the reader's existing footnote-popup convention) and
collected into a ``{label: html}`` map. The source TEI's Loeb notes carry only
a bare Loeb page.footnote citation number as their content by default; where
``sources/loeb-notes/notes-<work>.json`` supplies audited, high-confidence
real note text for a marker (see ``apply_loeb_note_overrides``), that text
replaces the bare citation number. Markers with no shippable note keep the
bare-number behavior.

Label uniqueness: a label is ``{book}.{seqInBook}.{raw}`` — ``seqInBook`` is
this book's Nth Loeb note in document order (matches the loeb-notes JSON's
``markerId`` third component exactly), and ``raw`` is the printed citation
number (unchanged from the pre-fix scheme). ``seqInBook`` alone guarantees
uniqueness, since the Reader's footnote popup (``FootnotePopup.svelte`` /
Reader.svelte's ``fnDisplay``) only ever shows the label's text AFTER its
LAST ``.`` — i.e. ``raw`` — so inserting ``seqInBook`` in the middle leaves
the on-page displayed footnote number byte-identical to before. This is a
pipeline-only fix: no reader change needed. The prior scheme, ``{book}.
{raw}``, collided whenever a book's Loeb pages each restarted their own
citation numbering (e.g. two different pages each print a footnote "1"),
which is why the TEI's 336 real markers previously collapsed into ~145
unique keys — later occurrences silently overwrote earlier ones in the
footnotes map even though both inline markers were still present and
visually distinct in the prose.

Milestone anomalies (non-numeric ``n``, duplicate/out-of-order ``n``, a
milestone landing on a vulgate gap line) are handled rather than crashing, and
every one is collected into a machine-readable report (see ``run()``).
"""

from __future__ import annotations

import bisect
import json
import re
from pathlib import Path

from lxml import etree

from .config import BUILD_DIR, SOURCES_DIR, Manifest
from .stage1_common import StandoffChunkMixin, collapse_ws, local_name, write_json


def _is_book_div(div) -> bool:
    subtype = (div.get("subtype") or "").lower()
    n = div.get("n")
    return subtype == "book" and bool(n) and n.isdigit()


def _nearest_line(valid_sorted: list[int], n: int) -> int:
    """The valid spine line nearest `n` (which is NOT itself in valid_sorted).
    Ties (equidistant before/after — a single-line vulgate gap) snap FORWARD,
    to the next existing line, so a block boundary keeps advancing."""
    idx = bisect.bisect_left(valid_sorted, n)
    if idx == 0:
        return valid_sorted[0]
    if idx == len(valid_sorted):
        return valid_sorted[-1]
    before, after = valid_sorted[idx - 1], valid_sorted[idx]
    if (n - before) < (after - n):
        return before
    return after


class _BookWalker(StandoffChunkMixin):
    """Accumulates one book's translation prose into a single standoff chunk
    (StandoffChunkMixin keys chunks by (book, column); pinning both for the
    whole walk collapses that to exactly one chunk, matching verse-line's
    one-segment-per-book spine)."""

    def __init__(self, book: int, valid_lines: set[int], extract_footnotes: bool):
        self.book = book
        self.column = str(book)
        self.chunks: list[dict] = []
        self._by_key: dict[tuple, dict] = {}
        self.valid_lines = valid_lines
        self.valid_sorted = sorted(valid_lines)
        self.extract_footnotes = extract_footnotes
        self.last_n = 0
        self.ticks: list[dict] = []
        self.footnotes: dict[str, str] = {}
        self.anomalies: list[dict] = []
        self._note_ctr = 0
        # seqInBook (this book's Nth Loeb note, document order) -> the label
        # assigned to it. Lets the loeb-notes override join recover the exact
        # emitted label for a given (book, seqInBook) markerId without having
        # to recompute/guess the label formula independently.
        self.label_by_seq: dict[int, str] = {}

    def add_milestone(self, n_attr: str | None) -> None:
        if not n_attr or not n_attr.isdigit():
            self.anomalies.append(
                {"kind": "non_numeric_milestone", "book": self.book, "n_raw": n_attr}
            )
            return
        n = int(n_attr)
        orig = n
        if n not in self.valid_lines:
            if not self.valid_sorted:
                return
            lo, hi = self.valid_sorted[0], self.valid_sorted[-1]
            if n < lo or n > hi:
                # Outside the book's whole line range entirely — almost always
                # a digitization typo (a single garbled digit; e.g. Od. 16
                # Murray's "580" for what document order shows should be
                # "280"), NOT a reference to a real nearby position. Snapping
                # this to the book's edge would poison monotonicity for every
                # correctly-labeled milestone still to come (last_n would jump
                # to the edge and reject the rest of the book as "out of
                # order"), so it is reported and skipped instead — last_n is
                # untouched and the next genuine milestone resumes cleanly.
                self.anomalies.append(
                    {
                        "kind": "milestone_out_of_range",
                        "book": self.book,
                        "n_raw": orig,
                        "valid_range": [lo, hi],
                    }
                )
                return
            snapped = _nearest_line(self.valid_sorted, n)
            self.anomalies.append(
                {
                    "kind": "milestone_gap_snap",
                    "book": self.book,
                    "n_raw": orig,
                    "snapped_to": snapped,
                }
            )
            n = snapped
        if n <= self.last_n:
            kind = "milestone_duplicate" if n == self.last_n else "milestone_out_of_order"
            self.anomalies.append(
                {
                    "kind": kind,
                    "book": self.book,
                    "n_raw": orig,
                    "last_accepted": self.last_n,
                }
            )
            return
        self.last_n = n
        chunk = self._chunk()
        self.ticks.append({"n": n, "offset": len(chunk["text"].rstrip()), "real": True})

    def add_milestone_tail(self, tail: str | None) -> None:
        """Text immediately following a removed <milestone/>. The source
        sometimes drops a milestone mid-sentence with no whitespace on
        either side (e.g. "in no wise<milestone .../>will they" -> glued
        "wisewill" once the tag is stripped and the two text nodes are
        concatenated). Insert exactly one space in that case only: when the
        text accumulated so far ends in a word character and the tail
        begins with one. Genuine hyphenation at a milestone would need the
        *preceding* text to end in "-" (not a word character), which this
        check leaves untouched — verified against the Iliad/Odyssey
        Murray/Butler TEIs: the only "-<milestone" adjacency in either
        corpus is an em-dash used as punctuation, not a hyphenated
        compound, so no such case exists to break here."""
        if not tail:
            return
        chunk = self._chunk()
        text = chunk["text"]
        if text and text[-1].isalnum() and tail[0].isalnum():
            chunk["text"] = text + " "
        self.add_text(tail)

    def add_footnote(self, el) -> None:
        chunk = self._chunk()
        raw = collapse_ws("".join(el.itertext())).strip()
        if el.get("resp") != "Loeb":
            # Not a Loeb apparatus note (e.g. a stray editorial/perseus note) —
            # its text is excluded from the prose (like a Greek-side <note>),
            # but it carries no footnote marker.
            self.anomalies.append(
                {"kind": "note_skipped_non_loeb", "book": self.book, "resp": el.get("resp")}
            )
            return
        self._note_ctr += 1
        # seqInBook (self._note_ctr) is inserted BEFORE raw so the label's
        # trailing segment (everything after the last '.') stays exactly
        # `raw` — see the module docstring's "Label uniqueness" note.
        suffix = raw if raw else f"n{self._note_ctr}"
        label = f"{self.book}.{self._note_ctr}.{suffix}"
        self.label_by_seq[self._note_ctr] = label
        # The marker is appended verbatim right after whatever's currently in
        # chunk["text"] (add_text does not strip a pre-existing trailing
        # space before a piece that doesn't itself start with whitespace), so
        # its first char ('[') always lands at the CURRENT length — not the
        # rstripped length, which undercounts by one whenever the source has
        # a trailing space before <note> and points the offset at that space
        # instead of at the marker.
        chunk["notes"].append({"offset": len(chunk["text"]), "text": raw})
        self.add_text(f"[^{label}]")
        self.footnotes[label] = raw


def _walk(w: _BookWalker, el, is_root: bool = False) -> None:
    if not isinstance(getattr(el, "tag", None), str):
        w.add_text(el.tail)
        return
    tag = local_name(el)
    if tag == "note" and not is_root:
        if w.extract_footnotes:
            w.add_footnote(el)
        w.add_text(el.tail)
        return
    if tag == "head" and not is_root:
        # Book heading ("Scroll 1", Butler) — not translation prose.
        w.add_text(el.tail)
        return
    if tag == "milestone":
        if el.get("unit") == "line":
            w.add_milestone(el.get("n"))
        w.add_milestone_tail(el.tail)
        return
    if tag == "p" and not is_root:
        w.add_paragraph()
        w.add_text(el.text)
        for child in el:
            _walk(w, child)
        w.add_text(el.tail)
        return
    w.add_text(el.text)
    for child in el:
        _walk(w, child)
    if not is_root and el.tail:
        w.add_text(el.tail)


def parse_translation(
    xml_path: Path,
    valid_lines_by_book: dict[int, set[int]],
    book_ns: list[int],
    extract_footnotes: bool = False,
) -> dict:
    """Parse one milestoned Perseus English TEI into per-book chunks.

    Returns ``{chunks: {book: chunk}, footnotes: {label: text}, anomalies:
    [...], ticks_by_book: {book: [tick,...]}, label_by_book_seq: {(book,
    seqInBook): label}}``. ``book_ns`` is the manifest's declared book list,
    walked in order; a book with no matching TEI div is reported as a
    ``missing_book_div`` anomaly and simply produces no chunk (the coverage
    check then reports it as a full hole)."""
    tree = etree.parse(str(xml_path))
    body = tree.find(".//{*}body")
    if body is None:
        raise ValueError(f"no TEI body in {xml_path}")

    book_divs = {int(d.get("n")): d for d in body.iter("{*}div") if _is_book_div(d)}

    chunks: dict[int, dict] = {}
    footnotes: dict[str, str] = {}
    anomalies: list[dict] = []
    ticks_by_book: dict[int, list[dict]] = {}
    label_by_book_seq: dict[tuple[int, int], str] = {}

    for book in book_ns:
        div = book_divs.get(book)
        if div is None:
            anomalies.append({"kind": "missing_book_div", "book": book})
            continue
        w = _BookWalker(book, valid_lines_by_book.get(book, set()), extract_footnotes)
        _walk(w, div, is_root=True)
        chunk = w._chunk()
        chunk["text"] = chunk["text"].strip()
        # A milestone right at the very end of a book's prose (nothing real
        # follows it) would otherwise survive as a tick whose window is
        # empty (offset == len(text)). That's not useful — the real final
        # English lives in the previous tick's window — so it's dropped and
        # folded into that previous block, and reported rather than left as
        # a silent dead end.
        final_len = len(chunk["text"])
        while w.ticks and w.ticks[-1]["offset"] >= final_len:
            dropped = w.ticks.pop()
            w.anomalies.append(
                {
                    "kind": "terminal_empty_dropped",
                    "book": book,
                    "n": dropped["n"],
                    "offset": dropped["offset"],
                }
            )
        if chunk["text"]:
            chunks[book] = chunk
        ticks_by_book[book] = w.ticks
        footnotes.update(w.footnotes)
        anomalies.extend(w.anomalies)
        for seq, label in w.label_by_seq.items():
            label_by_book_seq[(book, seq)] = label

    return {
        "chunks": chunks,
        "footnotes": footnotes,
        "anomalies": anomalies,
        "ticks_by_book": ticks_by_book,
        "label_by_book_seq": label_by_book_seq,
    }


def check_coverage(
    valid_lines_by_book: dict[int, list[int]],
    ticks_by_book: dict[int, list[dict]],
    book_ns: list[int],
) -> list[dict]:
    """Coverage holes: a book with zero ticks (no milestones reached it at
    all), or whose first tick doesn't start at the book's first Greek line
    (an uncovered lead-in). The tick sequence is monotonically increasing by
    construction (add_milestone rejects non-advancing n), and the last tick's
    block is defined to run to the book's last Greek line, so those two
    checks are the only possible holes."""
    holes: list[dict] = []
    for book in book_ns:
        valid = valid_lines_by_book.get(book) or []
        if not valid:
            continue
        first_line = valid[0]
        ticks = ticks_by_book.get(book) or []
        if not ticks:
            holes.append(
                {"book": book, "kind": "book_uncovered", "first_line": first_line,
                 "last_line": valid[-1]}
            )
            continue
        first_tick = ticks[0]["n"]
        if first_tick != first_line:
            holes.append(
                {
                    "book": book,
                    "kind": "lead_in_uncovered",
                    "from_line": first_line,
                    "to_line": first_tick - 1,
                }
            )
    return holes


# --- Loeb footnote real-text join (sources/loeb-notes/notes-<work>.json) ---
#
# The loeb-notes directory (see its README.md) holds an audited re-match of
# Murray's Loeb apparatus/explanatory notes against the bare-number TEI
# markers this module extracts. John's binding audit verdict (2026-07-17):
# ship `confidence: "high"` only (~187 of 336 markers), further filtered by
# the two post-filters below. Everything else keeps the bare citation-number
# behavior (`self.footnotes[label] = raw`, already in place before this
# join runs).

# A note whose own prose contains an internal "Line(s) N[-M]" self-reference
# more than this many lines from its own marker's approxLine is presumed
# contaminated (e.g. two adjacent Loeb footnotes concatenated by the OCR
# extraction into one candidate) and excluded, even from the "high" band.
_LINE_REF_TOLERANCE = 25

_LINE_REF_RE = re.compile(
    r"\bLines?\s+(\d{1,4})"
    r"(?:\s*(?:[-–—]|\band\b)\s*(\d{1,4}))?",
    re.IGNORECASE,
)


def _expand_abbreviated_range(first: str, second: str) -> int:
    """"313-5" style abbreviated ranges print fewer digits for the second
    number than the first (it shares the first's leading digits). If the
    second number is already full-width (or longer), it stands on its own."""
    if len(second) < len(first):
        second = first[: len(first) - len(second)] + second
    return int(second)


def far_line_ref(note_text: str, approx_line: int, tol: int = _LINE_REF_TOLERANCE) -> int | None:
    """The first internal "Line(s) N[-M]" reference in `note_text` whose
    number is more than `tol` lines from `approx_line`, or None if every such
    reference (there may be zero) falls within tolerance. Deterministic: a
    given (note_text, approx_line) always yields the same verdict."""
    for m in _LINE_REF_RE.finditer(note_text):
        n1 = int(m.group(1))
        if abs(n1 - approx_line) > tol:
            return n1
        if m.group(2):
            n2 = _expand_abbreviated_range(m.group(1), m.group(2))
            if abs(n2 - approx_line) > tol:
                return n2
    return None


# Post-filter 2 (John's audit verdict, judgment call): "high"-confidence
# notes whose entire recovered text is apparatus criticus — a bare variant
# list or rejection/omission notice naming ancient editors (Zenodotus,
# Aristophanes of Byzantium, Aristarchus, Rhianus) or manuscript witnesses,
# with no English explanatory prose about meaning/translation — are excluded
# even though nothing in them is factually wrong. Reviewed by hand against
# every "high" note in both works (2026-07-17); markers with MIXED content
# (an apparatus fragment followed by real explanatory prose, e.g.
# iliad.5.2's "Aristarchus took ... to mean a coat of mail") are kept.
APPARATUS_ONLY_HIGH_MARKER_IDS: frozenset[str] = frozenset(
    {
        # Iliad
        "iliad.2.10", "iliad.4.2", "iliad.4.4", "iliad.7.3", "iliad.8.2",
        "iliad.16.2", "iliad.16.3", "iliad.17.2", "iliad.17.4", "iliad.19.8",
        "iliad.19.10", "iliad.23.2",
        # Odyssey
        "odyssey.1.13", "odyssey.2.6", "odyssey.4.11", "odyssey.6.8",
        "odyssey.8.6", "odyssey.10.7", "odyssey.11.5", "odyssey.11.6",
        "odyssey.14.3", "odyssey.15.1", "odyssey.15.5", "odyssey.21.6",
        "odyssey.22.2", "odyssey.22.3",
    }
)


def filter_loeb_notes(notes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split loeb-notes records into (kept, excluded). Only `confidence:
    "high"` records are ever kept; every exclusion (including the tier
    filter) is reported so a caller can log/audit the decision — see
    `apply_loeb_note_overrides`'s report and stage1_perseus_milestone_
    english's module docstring for what "kept" means downstream."""
    kept: list[dict] = []
    excluded: list[dict] = []
    for n in notes:
        if n.get("confidence") != "high":
            excluded.append({**n, "exclusionReason": f"confidence:{n.get('confidence')}"})
            continue
        far = far_line_ref(n.get("noteText") or "", n["approxLine"])
        if far is not None:
            excluded.append({**n, "exclusionReason": f"distant_line_ref:{far}"})
            continue
        if n["markerId"] in APPARATUS_ONLY_HIGH_MARKER_IDS:
            excluded.append({**n, "exclusionReason": "apparatus_criticus_only"})
            continue
        kept.append(n)
    return kept, excluded


def apply_loeb_note_overrides(
    footnotes: dict[str, str],
    label_by_book_seq: dict[tuple[int, int], str],
    notes: list[dict],
) -> dict:
    """Mutate `footnotes` in place, replacing the bare-citation-number text
    at each surviving high-confidence marker's emitted label with its real
    noteText. `label_by_book_seq` (from `parse_translation`) maps a
    markerId's (book, seqInBook) — the SAME document-order count this
    module's own walker used — to the exact label under which that
    occurrence was emitted, so the join lands on the correct key even
    though `raw` (the printed citation number) may repeat within a book.
    Returns a report: {applied: [...], excluded: [...], missing: [...]}."""
    kept, excluded = filter_loeb_notes(notes)
    applied: list[dict] = []
    missing: list[dict] = []
    for n in kept:
        seq = int(n["markerId"].rsplit(".", 1)[-1])
        label = label_by_book_seq.get((n["book"], seq))
        if label is None:
            # No pipeline marker at this (book, seqInBook) — e.g. the TEI
            # changed since the loeb-notes extraction ran. Never invent a
            # key; report it instead.
            missing.append(n)
            continue
        footnotes[label] = n["noteText"]
        applied.append({"markerId": n["markerId"], "label": label})
    return {"applied": applied, "excluded": excluded, "missing": missing}


def load_loeb_notes(work_id: str) -> list[dict] | None:
    """Load sources/loeb-notes/notes-<work_id>.json's `notes` list, or None
    if this work has no audited Loeb-note file (works other than Iliad/
    Odyssey, or a not-yet-extracted work)."""
    path = SOURCES_DIR / "loeb-notes" / f"notes-{work_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("notes", [])


def _build_english_chunks(work_id: str, source_name: str, translation_id: str,
                          parsed: dict, book_ns: list[int]) -> dict:
    chunks = []
    for book in book_ns:
        chunk = parsed["chunks"].get(book)
        if not chunk:
            continue
        chunks.append(
            {
                "id": chunk["id"],
                "book": chunk["book"],
                "column": chunk["column"],
                "text": chunk["text"],
                "notes": chunk["notes"],
                "markers": chunk["markers"],
                "bekker": parsed["ticks_by_book"].get(book, []),
            }
        )
    return {
        "work": work_id,
        "source": source_name,
        "translation": translation_id,
        "chunks": chunks,
        "chapters": [],
    }


def _build_ross_chunks(parsed: dict, book_ns: list[int]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for book in book_ns:
        chunk = parsed["chunks"].get(book)
        if not chunk:
            continue
        out[chunk["id"]] = [
            {
                "chapter": str(book),
                "text": chunk["text"],
                "cont": False,
                "bekker": parsed["ticks_by_book"].get(book, []),
            }
        ]
    return out


def _build_alignment(work_id: str, spine: dict, english: dict) -> dict:
    eng_ids = {c["id"] for c in english["chunks"]}
    seg_ids = {s["id"] for s in spine["segments"]}
    pairs = [
        {"segment": s["id"], "english": s["id"] if s["id"] in eng_ids else None}
        for s in spine["segments"]
    ]
    return {"work": work_id, "pairs": pairs, "english_only": sorted(eng_ids - seg_ids)}


def run(manifest: Manifest, spine: dict) -> dict:
    eng_cfg = manifest.data.get("english") or {}
    primary = eng_cfg.get("primary")
    secondary = eng_cfg.get("secondary")
    book_ns = [b["n"] for b in manifest.books]
    valid_lines_by_book = {
        seg["book"]: sorted(l["n"] for l in seg["lines"]) for seg in spine["segments"]
    }
    valid_sets_by_book = {b: set(ns) for b, ns in valid_lines_by_book.items()}

    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {"work": manifest.work_id, "translations": {}}
    summary: dict = {}

    if primary:
        xml_path = SOURCES_DIR / primary["source"]
        parsed = parse_translation(xml_path, valid_sets_by_book, book_ns, extract_footnotes=True)
        english = _build_english_chunks(manifest.work_id, xml_path.name, primary["id"], parsed, book_ns)
        write_json(out_dir / "english_chunks.json", english)
        write_json(out_dir / "alignment.json", _build_alignment(manifest.work_id, spine, english))

        # Splice in audited real note text (sources/loeb-notes/) where
        # available, before writing murray_footnotes.json — see module
        # docstring and apply_loeb_note_overrides. Only Murray (primary) ever
        # carries Loeb notes; absent for works with no loeb-notes file.
        loeb_notes = load_loeb_notes(manifest.work_id)
        loeb_report = (
            apply_loeb_note_overrides(parsed["footnotes"], parsed["label_by_book_seq"], loeb_notes)
            if loeb_notes is not None
            else None
        )

        write_json(out_dir / "murray_footnotes.json", parsed["footnotes"])
        holes = check_coverage(valid_lines_by_book, parsed["ticks_by_book"], book_ns)
        report["translations"][primary["id"]] = {
            "chunks": len(english["chunks"]),
            "footnotes": len(parsed["footnotes"]),
            "anomalies": parsed["anomalies"],
            "coverage_holes": holes,
            **({"loeb_notes": loeb_report} if loeb_report is not None else {}),
        }
        summary[primary["id"]] = {
            "chunks": len(english["chunks"]),
            "footnotes": len(parsed["footnotes"]),
            "anomalies": len(parsed["anomalies"]),
            "holes": len(holes),
            **(
                {
                    "loeb_notes_applied": len(loeb_report["applied"]),
                    "loeb_notes_excluded": len(loeb_report["excluded"]),
                }
                if loeb_report is not None
                else {}
            ),
        }
    else:
        write_json(out_dir / "english_chunks.json", {"work": manifest.work_id, "translation": None, "chunks": [], "chapters": []})
        write_json(out_dir / "alignment.json", {"pairs": [], "english_only": []})

    if secondary:
        xml_path = SOURCES_DIR / secondary["source"]
        parsed = parse_translation(xml_path, valid_sets_by_book, book_ns, extract_footnotes=False)
        ross = _build_ross_chunks(parsed, book_ns)
        write_json(out_dir / "ross_chunks.json", ross)
        holes = check_coverage(valid_lines_by_book, parsed["ticks_by_book"], book_ns)
        report["translations"][secondary["id"]] = {
            "chunks": len(ross),
            "anomalies": parsed["anomalies"],
            "coverage_holes": holes,
        }
        summary[secondary["id"]] = {
            "chunks": len(ross),
            "anomalies": len(parsed["anomalies"]),
            "holes": len(holes),
        }
    else:
        write_json(out_dir / "ross_chunks.json", {})

    write_json(out_dir / "milestone_report.json", report)
    return {"report": report, "summary": summary}
