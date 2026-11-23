"""The committed Greek: one line-level file per work, corpus/greek/<Work>.tsv.

The build reads these for a work's Greek; it never runs Diogenes and never
sees the TLG. `python -m homer_pipeline.extract` makes them, on a machine that
has the TLG (HANDOFF-PORTABILITY.md, decision 1). Only the Iliad has one: the
Odyssey's Greek is the Perseus file vendored under sources/perseus/.

A file is the printed lines of one work, in reading order, each under its
book:

    # work: Iliad
    # edition: Allen, T.W., Homeri Ilias (Oxford: Clarendon Press, 1931), …
    # columns: book	n	sigla	text
    1	t
    1	1		Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
    1	2	>	οὐλομένην, ἣ μυρί' Ἀχαιοῖς ἄλγε' ἔθηκε,

`n` is the line's own number as printed ("1", "605*", "t" for a book's title
line). `sigla` holds the Alexandrian critical signs the edition prints in the
margin of that line (the export's <seg rend="Marginalia">), or nothing. `text`
is the rest of the line's characters with runs of white space made one space,
and nothing else changed: no NFC, and a bullet the edition prints in the line
stays where it is. Stage 1 does the reading: the obelos rule, the bullet, the
NFC, the "605*", and the four supplied Book 8 lines. No markup, no beta code,
no Diogenes XML: pipeline/tests/test_corpus_greek.py holds that line.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import NamedTuple

from lxml import etree

from .config import REPO_ROOT, Manifest
from .stage1_common import collapse_ws, local_name

CORPUS_DIR = REPO_ROOT / "corpus" / "greek"
COLUMNS = "# columns: book\tn\tsigla\ttext"


class Row(NamedTuple):
    book: str           # the book's number, as the export's <div type="Book" n=…> has it
    n: str              # the line's own number as printed: "1", "605*", "t"
    sigla: str          # the margin's signs, parts joined by one space; "" for none
    text: str           # the line, white space collapsed, as printed


def corpus_path(manifest: Manifest) -> Path:
    return CORPUS_DIR / f"{manifest.path.stem.removesuffix('-public')}.tsv"


def work_name(manifest: Manifest) -> str:
    return manifest.path.stem.removesuffix("-public")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def flatten_line(el) -> tuple[str, list[str]]:
    """An <l> as stage 1 has always read it: (the line's text with runs of
    white space collapsed, each <seg rend="Marginalia"> taken out into its own
    part). A <label> below the line (the title line's wrapper) and an empty
    milestone (<pb/>, <space/>) give only their tails."""
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
    return collapse_ws("".join(parts)).strip(), sigla_parts


def _is_book_div(div) -> bool:
    n = div.get("n")
    return (div.get("type") or "").lower() == "book" and bool(n) and n.isdigit()


def rows_from_xml(xml_path: Path) -> list[Row]:
    """Every <l> in a book of the export's body, in document order.

    Raises where the line file could not say what the XML says, or where the
    export takes a shape no stage 1 of this reader has met: a book inside a
    book, a book number twice, a line with no number or an empty one."""
    tree = etree.parse(str(xml_path))
    body = tree.find(".//{*}body")
    if body is None:
        raise ValueError(f"{xml_path.name}: no TEI body")
    seen: set[str] = set()
    for div in body.iter("{*}div"):
        if not _is_book_div(div):
            continue
        # The old reader read n with int(), so "01" or an Arabic-Indic digit
        # was book 1 there and another book here.
        if not _BOOK.fullmatch(div.get("n")):
            raise ValueError(f"{xml_path.name}: a book number not written as plain digits: {div.get('n')!r}")
        if any(_is_book_div(a) for a in div.iterancestors("{*}div")):
            raise ValueError(f"{xml_path.name}: book {div.get('n')} inside another book")
        if div.get("n") in seen:
            raise ValueError(f"{xml_path.name}: book {div.get('n')} twice")
        seen.add(div.get("n"))
    rows: list[Row] = []
    for line in body.iter("{*}l"):
        book = next((a for a in line.iterancestors("{*}div") if _is_book_div(a)), None)
        if book is None:
            continue
        n = line.get("n")
        if not n:
            raise ValueError(f"{xml_path.name}: a line with no number in book {book.get('n')}")
        text, sigla_parts = flatten_line(line)
        rows.append(Row(book.get("n"), n, " ".join(p for p in sigla_parts if p), text))
    # A book with no line has no row to say it is there; the old reader gave
    # it a segment of its own (and Book 8 its supplied lines).
    empty = sorted(seen - {r.book for r in rows}, key=int)
    if empty:
        raise ValueError(f"{xml_path.name}: book {empty[0]} has no lines")
    return rows


_FIELD_BREAK = re.compile(r"[\t\n\r]")


def format_tsv(rows: list[Row], work: str, edition: str) -> str:
    out = [f"# work: {_flat(work)}", f"# edition: {_flat(edition)}", COLUMNS]
    for row in rows:
        fields = [row.book, row.n, row.sigla, row.text]
        if any(_FIELD_BREAK.search(f) for f in fields):
            raise ValueError(f"{work}: a field of book {row.book} line {row.n!r} holds a tab or a line break")
        if row.text != _flat(row.text) or row.sigla != _flat(row.sigla):
            raise ValueError(f"{work}: book {row.book} line {row.n!r} is not flat")
        out.append("\t".join(fields))
    return "\n".join(out) + "\n"


def parse_tsv(text: str, name: str = "line file") -> list[Row]:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    # Three heading lines and no more: a fourth "# " line would be a place to
    # keep anything at all.
    if len(lines) < 3 or not lines[0].startswith("# work: ") or not lines[1].startswith("# edition: ") \
            or lines[2] != COLUMNS:
        raise ValueError(f"{name}: expected # work, # edition, and then the line {COLUMNS!r}")
    rows = []
    for i, line in enumerate(lines[3:], 4):
        fields = line.split("\t")
        if len(fields) != 4 or "\r" in line:
            raise ValueError(f"{name} line {i}: expected 4 tab-separated fields")
        if not fields[0] or not fields[1]:
            raise ValueError(f"{name} line {i}: an empty book or line number")
        rows.append(Row(*fields))
    if not rows:
        raise ValueError(f"{name}: no lines of text")
    return rows


def load(path: Path) -> list[Row]:
    """A committed line file, or XML of the export's shape (the tests' fixtures)."""
    if path.suffix == ".tsv":
        return parse_tsv(path.read_text(encoding="utf-8"), path.name)
    return rows_from_xml(path)


# What a line file must never hold: the Diogenes XML, the TLG's own beta
# code, or anything that is not a line of Greek. The rule that does the work:
# every character of a line's text is a Greek one (its Unicode name says so:
# the letters, and the Greek marks · ;) or one of the marks in _MARKS, which
# are all the others Allen's Iliad prints. Beta code writes Greek in Latin
# letters (mh=nin a)/eide), and markup needs Latin names and attributes, so
# neither survives, with or without punctuation around the words; nor does a
# Latin letter in another dress (ⓐ, ａ, a combining a). A character outside
# both sets fails the file. An editor's new sign is added here by hand, after
# someone has looked at it. (The bullet is TLG's "%11", printed at the head of
# Il. 8.538-540 and 13.298; stage 1 moves it to the line's sigla.)
_MARKS = frozenset(" ',.•")
# The margin's signs: the obelos, the diplē, the diplē periestigmenē, the
# asteriskos and the antisigma, alone or run together, and two words of the
# apparatus, "corr." and "ras.", the only Latin a line file may hold.
_SIGLA_SIGNS = frozenset("—>⸖※ϽϾϿ")
_SIGLA_WORDS = frozenset({"corr.", "ras."})
# The lines below are the whole corpus's exceptions, each named. There are none.
NOT_GREEK_OK: dict[tuple[str, str], str] = {}
# Markup that needs no Latin letter: a tag's angle bracket, a character
# reference. The diplē ">" is a sign of the margin, and the sigla column has
# its own rule; nowhere else may "<" or ">" stand.
_TAG = re.compile(r"[<>]|&#|&[A-Za-z]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\x80-\x9f\u00a0\u2028\u2029]")
_BOOK = re.compile(r"[1-9][0-9]?")
# A line's number: "1", "605*" (the export's mark on one line), "t" (a title).
_N = re.compile(r"[1-9][0-9]*\*?|t")
_WORK = re.compile(r"# work: [A-Za-z0-9]+")


def not_greek(text: str) -> list[str]:
    return [ch for ch in text if ch not in _MARKS and not unicodedata.name(ch, "").startswith("GREEK")]


def bad_sigla(sigla: str) -> bool:
    return any(not (set(part) <= _SIGLA_SIGNS or part in _SIGLA_WORDS) for part in sigla.split(" ")) if sigla else False


def forbidden(text: str) -> list[str]:
    """Problems with a line file's contents; empty when it is clean. Every
    line of the file is examined: the three heading lines, each book and line
    number, the signs of each margin, and each line of text. The edition line
    is free text (an editor, a title, a year) and gets only the control check
    and a check against markup; the corpus test holds it to the manifest's own
    words."""
    problems: list[str] = []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) < 4 or not _WORK.fullmatch(lines[0]) or not lines[1].startswith("# edition: ") \
            or lines[2] != COLUMNS:
        return ["not a line file: it must open with # work, # edition and the # columns line, then lines of text"]
    if "\t" in lines[0] or "\t" in lines[1]:
        return ["not a line file: a tab in a heading line"]
    work = lines[0][len("# work: "):]
    controls = [line for line in lines if _CONTROL.search(line)]
    if controls:
        problems.append(f"a control character in {len(controls)} lines, first: {controls[0][:80]!r}")
    tags = [line for line in lines[:2] if _TAG.search(line)] + \
           [line for line in lines[3:] if _TAG.search(line.split("\t")[-1])]
    if tags:
        problems.append(f"markup in {len(tags)} lines, first: {tags[0][:80]!r}")
    bad_fields, odd, signs, letters = [], [], [], 0
    for line in lines[3:]:
        fields = line.split("\t")
        if len(fields) != 4 or not _BOOK.fullmatch(fields[0]) or not _N.fullmatch(fields[1]):
            bad_fields.append(line)
            continue
        book, n, sigla, body = fields
        letters += sum(ch.isalpha() for ch in body)
        if not_greek(body) and NOT_GREEK_OK.get((book, n)) != body:
            odd.append(line)
        if bad_sigla(sigla):
            signs.append(line)
    if bad_fields:
        problems.append(f"a book or line number that is not one, or the wrong number of fields, in {len(bad_fields)} lines, first: {bad_fields[0][:80]!r}")
    if odd:
        problems.append(f"characters that are not Greek in {len(odd)} lines, first: {odd[0][:80]!r}")
    if signs:
        problems.append(f"a margin that is not the edition's signs in {len(signs)} lines, first: {signs[0][:80]!r}")
    if not letters:
        problems.append("no letters at all")
    return problems
