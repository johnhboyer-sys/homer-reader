"""Stage 1: Homeric Greek spine from a vendored Perseus TEI (perseus-grc2).

Parses a CTS-style TEI whose body holds ``<div type="textpart" subtype="Book"
n="1..24">`` (case of ``Book``/``book`` is ignored) each containing ``<l n="…">``
verse lines. Line numbers come from the ``n`` attribute **verbatim** — never
renumbered. Non-digit ``n`` values (e.g. title lines ``n="t"``) are skipped and
reported under ``headings``. Lines are emitted in ascending ``n`` order within
each book so TEI document-order glitches (rare swapped physical order) cannot
corrupt the vulgate sequence.

Output shape matches the stage1 spine that stage2/stage3 consume: one segment
per book, ``column`` = book number as a string (the verse-line "column" is the
book container; see scheme ``verse-line``).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from lxml import etree

from .config import BUILD_DIR, Manifest
from .stage1_common import collapse_ws, local_name

_WS = re.compile(r"\s+")


def _line_text(el: etree._Element) -> str:
    """Flatten an <l>, dropping note/head/comment subtrees, collapsing ws, NFC.

    Perseus occasionally embeds editorial notes as XML comments inside a verse
    line (e.g. Il. 13.60 ``<!-- keko/pwn in 1920 reprint -->``). Comment bodies
    must not enter the Greek token stream; only their tails (main-text
    continuation) are kept.
    """
    parts: list[str] = []

    def walk(node, is_root: bool = False) -> None:
        # Comments / PIs are not elements (tag is a callable); keep only tail.
        if not isinstance(getattr(node, "tag", None), str):
            if not is_root and getattr(node, "tail", None):
                parts.append(node.tail)
            return
        tag = local_name(node) or ""
        if tag in ("note", "head") and not is_root:
            if node.tail:
                parts.append(node.tail)
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if not is_root and node.tail:
            parts.append(node.tail)

    walk(el, is_root=True)
    text = collapse_ws("".join(parts)).strip()
    return unicodedata.normalize("NFC", text)


def _is_book_div(div: etree._Element) -> bool:
    """True for a Perseus book container (subtype Book/book, numeric n)."""
    subtype = (div.get("subtype") or "").lower()
    n = div.get("n")
    return subtype == "book" and bool(n) and n.isdigit()


def parse_spine(xml_path: Path, manifest: Manifest) -> dict:
    """Parse a Perseus grc TEI into the stage1 greek_spine dict."""
    tree = etree.parse(str(xml_path))
    body = tree.find(".//{*}body")
    if body is None:
        raise ValueError(f"no TEI body in {xml_path}")

    segments: list[dict] = []
    headings: list[dict] = []
    title_n_count = 0
    non_digit_n: dict[str, int] = {}

    # Prefer direct book divs under the edition container; fall back to any.
    book_divs = [d for d in body.iter("{*}div") if _is_book_div(d)]
    # Keep document order; if a nested book somehow appears, first-seen wins.
    seen_books: set[int] = set()
    ordered_books: list[tuple[int, etree._Element]] = []
    for div in book_divs:
        bn = int(div.get("n"))
        if bn in seen_books:
            continue
        seen_books.add(bn)
        ordered_books.append((bn, div))
    ordered_books.sort(key=lambda x: x[0])

    for book_n, div in ordered_books:
        # Collect by line number so vulgate order wins over document order.
        by_n: dict[int, str] = {}
        for l in div.iter("{*}l"):
            # Only lines whose nearest book ancestor is this book (avoid nested
            # book pollution — none expected in perseus-grc2, but be strict).
            anc = l.getparent()
            owner = None
            while anc is not None:
                if _is_book_div(anc):
                    owner = int(anc.get("n"))
                    break
                anc = anc.getparent()
            if owner is not None and owner != book_n:
                continue

            n_attr = l.get("n")
            if n_attr is None:
                non_digit_n["(none)"] = non_digit_n.get("(none)", 0) + 1
                continue
            if not n_attr.isdigit():
                non_digit_n[n_attr] = non_digit_n.get(n_attr, 0) + 1
                if n_attr == "t":
                    title_n_count += 1
                headings.append(
                    {
                        "column": str(book_n),
                        "n": n_attr,
                        "text": _line_text(l),
                    }
                )
                continue
            line_no = int(n_attr)
            # First occurrence wins if a duplicate n= appears (should not).
            if line_no not in by_n:
                by_n[line_no] = _line_text(l)

        column = str(book_n)
        lines = [{"n": n, "text": by_n[n]} for n in sorted(by_n)]
        segments.append(
            {
                "id": f"{book_n}:{column}",
                "book": book_n,
                "column": column,
                "lines": lines,
            }
        )

    return {
        "work": manifest.work_id,
        "edition": manifest.data["work"]["greek_edition"],
        "segments": segments,
        "headings": headings,
        "unassigned_lines": [],
        # Diagnostic: non-verse <l n="…"> counts (title lines etc.).
        "skipped_line_attrs": dict(non_digit_n),
        "title_lines_skipped": title_n_count,
    }


def run(manifest: Manifest) -> Path:
    xml_path = manifest.perseus_grc()
    if not xml_path.exists():
        raise FileNotFoundError(f"Perseus Greek TEI missing: {xml_path}")
    spine = parse_spine(xml_path, manifest)
    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "greek_spine.json"
    out.write_text(json.dumps(spine, ensure_ascii=False, indent=1), encoding="utf-8")

    # Greek-only (Phase 1): write empty English/alignment stubs so stage2/6/7
    # can load them without a translation pass.
    eng = {
        "work": manifest.work_id,
        "translation": None,
        "chunks": [],
        "chapters": [],
    }
    (out_dir / "english_chunks.json").write_text(
        json.dumps(eng, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    align = {"pairs": [], "english_only": []}
    (out_dir / "alignment.json").write_text(
        json.dumps(align, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return out
