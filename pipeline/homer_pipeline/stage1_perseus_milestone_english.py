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
a bare Loeb page.footnote citation number as their content (no annotation
prose survives in this Perseus digitization) — the popup will show that
citation number verbatim; we do not fabricate commentary that isn't there.

Milestone anomalies (non-numeric ``n``, duplicate/out-of-order ``n``, a
milestone landing on a vulgate gap line) are handled rather than crashing, and
every one is collected into a machine-readable report (see ``run()``).
"""

from __future__ import annotations

import bisect
import json
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
        label = f"{self.book}.{raw}" if raw else f"{self.book}.n{self._note_ctr}"
        chunk["notes"].append({"offset": len(chunk["text"].rstrip()), "text": raw})
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
        w.add_text(el.tail)
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
    [...], ticks_by_book: {book: [tick,...]}}``. ``book_ns`` is the manifest's
    declared book list, walked in order; a book with no matching TEI div is
    reported as a ``missing_book_div`` anomaly and simply produces no chunk
    (the coverage check then reports it as a full hole)."""
    tree = etree.parse(str(xml_path))
    body = tree.find(".//{*}body")
    if body is None:
        raise ValueError(f"no TEI body in {xml_path}")

    book_divs = {int(d.get("n")): d for d in body.iter("{*}div") if _is_book_div(d)}

    chunks: dict[int, dict] = {}
    footnotes: dict[str, str] = {}
    anomalies: list[dict] = []
    ticks_by_book: dict[int, list[dict]] = {}

    for book in book_ns:
        div = book_divs.get(book)
        if div is None:
            anomalies.append({"kind": "missing_book_div", "book": book})
            continue
        w = _BookWalker(book, valid_lines_by_book.get(book, set()), extract_footnotes)
        _walk(w, div, is_root=True)
        chunk = w._chunk()
        chunk["text"] = chunk["text"].strip()
        if chunk["text"]:
            chunks[book] = chunk
        ticks_by_book[book] = w.ticks
        footnotes.update(w.footnotes)
        anomalies.extend(w.anomalies)

    return {
        "chunks": chunks,
        "footnotes": footnotes,
        "anomalies": anomalies,
        "ticks_by_book": ticks_by_book,
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
        write_json(out_dir / "murray_footnotes.json", parsed["footnotes"])
        holes = check_coverage(valid_lines_by_book, parsed["ticks_by_book"], book_ns)
        report["translations"][primary["id"]] = {
            "chunks": len(english["chunks"]),
            "footnotes": len(parsed["footnotes"]),
            "anomalies": parsed["anomalies"],
            "coverage_holes": holes,
        }
        summary[primary["id"]] = {
            "chunks": len(english["chunks"]),
            "footnotes": len(parsed["footnotes"]),
            "anomalies": len(parsed["anomalies"]),
            "holes": len(holes),
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
