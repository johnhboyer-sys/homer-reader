"""Stage 1: Iliad Greek spine from the TLG Diogenes verse-mode export.

John's decision (2026-07-17, binding): the Iliad re-bases from Perseus onto
the TLG export of **Allen, Oxford 1931** (editio maior). Gate A (line-set
identity, ``docs/`` scratch analysis) found the two editions identical for
23/24 books; the two exceptions this reader handles:

  * Book 18: TLG prints line 605 as ``n="605*"`` (a cosmetic export artifact,
    not a second line) — the ``*`` suffix is stripped, never treated as part
    of the vulgate number.
  * Book 8: Allen omits lines 548, 550, 551, 552 outright (the "hecatomb"
    lines, ll. 548-552, traditionally athetized as an early interpolation —
    schol. ad loc. — Allen goes further and does not print them at all).
    **Allen + supplement**: ship Allen's text, but supply those four lines
    from the current Perseus-derived build (the Monro-Allen OCT text, via
    ``perseus-grc2``; captured 2026-07-17 from ``build/dist/iliad/book-08.json``
    before this re-base, see ``SUPPLEMENTED_LINES`` below), each flagged
    ``bracketed: true``. Every vulgate line number stays present; the corpus
    total stays 15,687; no new ``expected_line_gaps`` entry is needed for
    Book 8, since the supplement removes what would otherwise be a gap.

Sigla: this export marks Alexandrian critical signs inline as
``<seg rend="Marginalia">`` on the line that carries them. Per John's ruling,
**only the obelos (—, U+2014, the athetesis mark) maps to ``bracketed:
true``** — diplē (``>``), diplē periestigmenē (``⸖``), asteriskos (``※``),
antisigma (``Ͻ``/``Ͼ``/``Ͽ``) and their combinations are NOT athetesis and are
never mapped. Every sigla glyph actually present (obelos included) is kept
verbatim on the line's optional ``sigla`` string field, so nothing this
edition marked is silently dropped — only interpreted.

Output shape is byte-compatible with ``stage1_perseus_greek``'s spine (same
``segments``/``headings``/``unassigned_lines``/``skipped_line_attrs``/
``title_lines_skipped`` keys), so stage2 onward and the milestoned-English
pass (which only needs vulgate book/line numbers) need no changes. Two
per-line fields are new here and optional: ``bracketed`` (bool, obelos or
supplement) and ``sigla`` (str, verbatim critical-sign text).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from lxml import etree

from .config import BUILD_DIR, Manifest
from .stage1_common import collapse_ws, local_name
from .stage1_greek import run_export

# The Alexandrian obelos (athetesis mark) as this export encodes it: a plain
# em dash inside <seg rend="Marginalia">, alone or combined with other sigla
# (e.g. "※—", "—ʼ>", "— ras."). Any sigla string containing this character
# maps its line to bracketed: true; every other glyph is preserved-only.
_OBELOS = "—"

# A vulgate line number decorated with a non-digit suffix (only "605*" is
# attested corpus-wide, per Gate A) — the suffix is a TLG export artifact,
# never part of the citation. Matches "605*" -> "605", not the title marker
# "t" (handled separately, before this regex is tried).
_DECORATED_N = re.compile(r"^(\d+)[^\d]+$")

# John's decision (2026-07-17, binding): supply these four Il. 8 lines (Allen
# omits them) from the Perseus Monro-Allen text captured from
# build/dist/iliad/book-08.json prior to this re-base. A constant, not a
# runtime read of build/dist/iliad/book-08.json, because stage7 overwrites
# that very file later in the same pipeline run — reading it live would make
# a second run of stage1 alone pick up the *already-supplemented* Allen text
# instead of the original Perseus source, silently losing the provenance
# trail. Keyed {book: {line: text}}; text is exactly as Perseus prints it
# (including its Unicode right-single-quote elision convention).
SUPPLEMENTED_LINES: dict[int, dict[int, str]] = {
    8: {
        548: "ἔρδον δ’ ἀθανάτοισι τεληέσσας ἑκατόμβας",
        550: "ἡδεῖαν· τῆς δ’ οὔ τι θεοὶ μάκαρες δατέοντο,",
        551: "οὐδ’ ἔθελον· μάλα γάρ σφιν ἀπήχθετο Ἴλιος ἱρή,",
        552: "καὶ Πρίαμος καὶ λαὸς ἐϋμμελίω Πριάμοιο",
    },
}


def _is_book_div(div) -> bool:
    """True for a TLG verse-mode book container (<div type="Book" n="N">)."""
    n = div.get("n")
    return (div.get("type") or "").lower() == "book" and bool(n) and n.isdigit()


# A second, unwrapped sigil this export produces: TLG Beta Code "%11" decodes
# straight to U+2022 BULLET as literal line-initial text (not inside a <seg
# rend="Marginalia">, unlike every other critical mark here) — confirmed
# against Diogenes/BetaHtml.pm's beta->Unicode table (`11 => "&#x2022;"`).
# Attested at exactly 4 Iliad lines: 8.538-540 and 13.298, all line-initial.
# It is NOT the em-dash obelos, so per John's ruling it must not set
# `bracketed` — but left inline it breaks stage3 tokenization (not a Greek
# character) and Aristarchus/Allen's obelos-only rule would silently swallow
# it. It is pulled into `sigla` uninterpreted, like the seg-wrapped marks.
# OPEN QUESTION for a classicist's Gate review: Il. 8.538-541 (the "would
# that I were immortal" boast) is a well-known Aristarchan athetesis locus —
# whether this bullet is TLG's own encoding of a multi-line obelos run there
# is not established by this data and is NOT assumed.
_BULLET = "•"


def _line_text_and_sigla(el) -> tuple[str, str | None]:
    """Flatten an <l>, pulling ``<seg rend="Marginalia">`` sigla and any
    stray ``_BULLET`` OUT of the Greek text stream (Alexandrian critical
    marks are apparatus, not text) and returning them as a separate combined
    string. ``<label type="head">`` (the title-line wrapper) and
    milestone-only ``<pb/>``/``<space/>`` carry no Greek text and are
    dropped, mirroring how the Perseus reader drops note/head subtrees."""
    parts: list[str] = []
    sigla_parts: list[str] = []

    def walk(node, is_root: bool = False) -> None:
        if not isinstance(getattr(node, "tag", None), str):
            if not is_root and getattr(node, "tail", None):
                parts.append(node.tail)
            return
        tag = local_name(node) or ""
        if tag == "seg" and (node.get("rend") or "") == "Marginalia":
            sigla_parts.append(collapse_ws("".join(node.itertext())).strip())
            if node.tail:
                parts.append(node.tail)
            return
        if tag == "label" and not is_root:
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
    raw = collapse_ws("".join(parts)).strip()
    if _BULLET in raw:
        sigla_parts.append(_BULLET)
        raw = collapse_ws(raw.replace(_BULLET, "")).strip()
    text = unicodedata.normalize("NFC", raw)
    sigla = " ".join(p for p in sigla_parts if p).strip() or None
    return text, sigla


def parse_spine(
    xml_path: Path,
    manifest: Manifest,
    supplement: dict[int, dict[int, str]] | None = None,
) -> dict:
    """Parse a TLG verse-mode export (Diogenes ``xml-export.pl -y``) into the
    stage1 greek_spine dict. ``supplement`` defaults to ``SUPPLEMENTED_LINES``
    (real Book 8 data); tests may pass a synthetic dict to exercise the
    injection mechanism without real vulgate line numbers."""
    supplement = SUPPLEMENTED_LINES if supplement is None else supplement
    tree = etree.parse(str(xml_path))
    body = tree.find(".//{*}body")
    if body is None:
        raise ValueError(f"no TEI body in {xml_path}")

    segments: list[dict] = []
    headings: list[dict] = []
    title_n_count = 0
    non_digit_n: dict[str, int] = {}
    normalized_n: list[dict] = []  # [{book, raw, normalized}], e.g. 18/"605*"/605

    book_divs = [d for d in body.iter("{*}div") if _is_book_div(d)]
    seen_books: set[int] = set()
    ordered_books: list[tuple[int, object]] = []
    for div in book_divs:
        bn = int(div.get("n"))
        if bn in seen_books:
            continue
        seen_books.add(bn)
        ordered_books.append((bn, div))
    ordered_books.sort(key=lambda x: x[0])

    for book_n, div in ordered_books:
        by_n: dict[int, dict] = {}
        for l in div.iter("{*}l"):
            # Only lines whose nearest book ancestor is this book div (no
            # nesting is attested in this export, but stay strict as the
            # Perseus reader does).
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
            if n_attr == "t":
                title_n_count += 1
                non_digit_n["t"] = non_digit_n.get("t", 0) + 1
                text, _sigla = _line_text_and_sigla(l)
                headings.append({"column": str(book_n), "n": n_attr, "text": text})
                continue
            if n_attr.isdigit():
                line_no = int(n_attr)
            else:
                m = _DECORATED_N.match(n_attr)
                if not m:
                    non_digit_n[n_attr] = non_digit_n.get(n_attr, 0) + 1
                    text, _sigla = _line_text_and_sigla(l)
                    headings.append({"column": str(book_n), "n": n_attr, "text": text})
                    continue
                line_no = int(m.group(1))
                normalized_n.append({"book": book_n, "raw": n_attr, "normalized": line_no})

            text, sigla = _line_text_and_sigla(l)
            if line_no in by_n:
                continue  # first occurrence wins if a duplicate n= appears
            entry: dict = {"n": line_no, "text": text}
            if sigla:
                entry["sigla"] = sigla
                if _OBELOS in sigla:
                    entry["bracketed"] = True
            by_n[line_no] = entry

        for line_no, supplied_text in sorted(supplement.get(book_n, {}).items()):
            if line_no in by_n:
                continue  # this edition already prints it; nothing to supply
            by_n[line_no] = {
                "n": line_no,
                "text": unicodedata.normalize("NFC", supplied_text),
                "bracketed": True,
            }

        column = str(book_n)
        lines = [by_n[n] for n in sorted(by_n)]
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
        "skipped_line_attrs": dict(non_digit_n),
        "title_lines_skipped": title_n_count,
        # Diagnostic: decorated-n normalizations applied (e.g. 18/"605*"/605).
        "normalized_line_attrs": normalized_n,
    }


def run(manifest: Manifest) -> Path:
    xml_path = run_export(manifest)
    spine = parse_spine(xml_path, manifest)
    out_dir = BUILD_DIR / "stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "greek_spine.json"
    out.write_text(json.dumps(spine, ensure_ascii=False, indent=1), encoding="utf-8")

    # Greek-only stubs; stage1_perseus_milestone_english/stage1_pope (called
    # separately by __main__ for verse-line works) overwrite these with the
    # real Murray/Butler/Pope passes.
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
