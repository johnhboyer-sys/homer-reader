"""Preflight validation for emitted Homer Reader corpus data."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from . import scheme as scheme_mod
from .refs import column_key, column_prefix_key, line_key, ref_key


Problem = tuple[str, str, str]


@dataclass
class WorkManifest:
    work_id: str
    path: Path
    data: dict[str, Any]
    public_path: Path | None = None
    private_data: dict[str, Any] | None = None


def validate(data_dir: Path, manifests_dir: Path) -> list[Problem]:
    problems: list[Problem] = []
    manifests = _load_manifests(manifests_dir, problems)
    for manifest in manifests:
        _validate_manifest_schema(manifest, problems)
        _validate_work_data(data_dir, manifest, problems)
    _validate_global_apparatus_emits(data_dir, manifests, problems)
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python3 -m homer_pipeline.preflight <data-dir> <manifests-dir>", file=sys.stderr)
        return 2

    data_dir = Path(argv[0])
    manifests_dir = Path(argv[1])
    problems = validate(data_dir, manifests_dir)
    if problems:
        for work, file_name, problem in problems:
            print(f"{work}: {file_name}: {problem}")
        return 1

    print(f"preflight ok: validated {data_dir} against {manifests_dir}")
    return 0


def _load_manifests(manifests_dir: Path, problems: list[Problem]) -> list[WorkManifest]:
    if not manifests_dir.exists():
        problems.append(("-", str(manifests_dir), "manifests directory does not exist"))
        return []

    parsed: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(manifests_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - exact parser text is not stable
            problems.append(("-", path.name, f"invalid YAML: {exc}"))
            continue
        if not isinstance(raw, dict):
            problems.append(("-", path.name, "manifest root must be an object"))
            continue
        parsed.append((path, raw))

    by_work: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, data in parsed:
        work_id = ((data.get("work") or {}).get("id") if isinstance(data.get("work"), dict) else None)
        if not isinstance(work_id, str) or not work_id:
            problems.append(("-", path.name, "work.id must be a non-empty string"))
            continue
        by_work.setdefault(work_id, []).append((path, data))

    selected: list[WorkManifest] = []
    for work_id, variants in sorted(by_work.items()):
        public = next(((p, d) for p, d in variants if p.name.endswith("-public.yaml")), None)
        private = next(((p, d) for p, d in variants if not p.name.endswith("-public.yaml")), None)
        path, data = public or private or variants[0]
        selected.append(
            WorkManifest(
                work_id=work_id,
                path=path,
                data=data,
                public_path=public[0] if public else None,
                private_data=private[1] if private and public else None,
            )
        )
    return selected


def _validate_manifest_schema(manifest: WorkManifest, problems: list[Problem]) -> None:
    """Validate a manifest's schema, dispatching on its citation scheme.

    The scheme-agnostic frame (work identity, english/sources objects, the books
    list) is shared. The scheme then decides the rest: a *bekker* manifest names
    its English on ``work.english_translation`` and cites by Bekker column
    (``bekker_range``), an explicit chapter div, and books bounded by full Bekker
    refs; a *section* manifest (stephanus) carries its English in the
    ``english.primary`` block, cites by page+section token with no Bekker range
    or chapter div, pins the observed spine with a ``section_spine`` fingerprint,
    and bounds books by section tokens. stage1/stage2 dispatch the same way."""
    data = manifest.data
    file_name = manifest.path.name
    scheme = scheme_mod.for_manifest(data)
    _require_object(manifest, data, "work", problems)
    _require_object(manifest, data, "english", problems)
    _require_object(manifest, data, "sources", problems)
    _require_list(manifest, data, "books", problems)

    work = data.get("work") if isinstance(data.get("work"), dict) else {}
    work_keys = ["id", "title", "author", "tlg_author", "tlg_work", "greek_edition"]
    if scheme.bekker_native:
        # Bekker manifests name the translation on work.english_translation;
        # section schemes carry it in english.primary (validated per-scheme below).
        work_keys.append("english_translation")
    for key in work_keys:
        if not isinstance(work.get(key), str) or not work.get(key):
            problems.append((manifest.work_id, file_name, f"work.{key} must be a non-empty string"))

    if scheme.bekker_native:
        _validate_bekker_manifest_schema(manifest, problems)
    elif scheme.name == "verse-line":
        _validate_verse_manifest_schema(manifest, problems)
    else:
        _validate_section_manifest_schema(manifest, problems)


def _validate_bekker_manifest_schema(manifest: WorkManifest, problems: list[Problem]) -> None:
    """Bekker-scheme manifest rules: a required Bekker column range, an optional
    explicit chapter list, and books bounded by full Bekker refs (with lines)."""
    data = manifest.data
    file_name = manifest.path.name
    _require_object(manifest, data, "bekker_range", problems)
    _require_object(manifest, data, "chapters", problems)

    bekker = data.get("bekker_range") if isinstance(data.get("bekker_range"), dict) else {}
    for key in ["first_column", "last_column"]:
        if not _is_column(bekker.get(key)):
            problems.append((manifest.work_id, file_name, f"bekker_range.{key} must be a Bekker column string"))

    _validate_books_schema(
        manifest, problems,
        token_ok=_is_ref, sort_key=ref_key, token_label="a Bekker ref string",
    )

    chapters = data.get("chapters") if isinstance(data.get("chapters"), dict) else {}
    if chapters.get("source") == "explicit":
        chapter_list = chapters.get("list")
        if not isinstance(chapter_list, list):
            problems.append((manifest.work_id, file_name, "chapters.list must be a list when chapters.source is explicit"))
        else:
            previous: tuple[int, str, int] | None = None
            for i, chapter in enumerate(chapter_list):
                if not isinstance(chapter, dict):
                    problems.append((manifest.work_id, file_name, f"chapters.list[{i}] must be an object"))
                    continue
                if not isinstance(chapter.get("n"), int):
                    problems.append((manifest.work_id, file_name, f"chapters.list[{i}].n must be an integer"))
                bekker_ref = chapter.get("bekker")
                if not _is_ref(bekker_ref):
                    problems.append((manifest.work_id, file_name, f"chapters.list[{i}].bekker must be a Bekker ref string"))
                    continue
                current = ref_key(bekker_ref)
                if previous is not None and current < previous:
                    problems.append((manifest.work_id, file_name, f"chapters.list[{i}].bekker is out of order"))
                previous = current


def _is_verse_ref(value: Any) -> bool:
    """True for a book.line token like '9.366'."""
    return isinstance(value, str) and bool(re.fullmatch(r"\d+\.\d+", value))


def _verse_ref_key(ref: str) -> tuple[int, int]:
    book, line = ref.split(".", 1)
    return (int(book), int(line))


def _validate_verse_manifest_schema(manifest: WorkManifest, problems: list[Problem]) -> None:
    """Verse-line (Homer) manifest rules: books bounded by book.line refs, no
    Bekker range / section spine / required english.primary (Greek-only builds
    are legal; Phase 2 adds translations). expected_line_gaps entries, when
    present, must carry {book, after, next}."""
    data = manifest.data
    file_name = manifest.path.name

    _validate_books_schema(
        manifest, problems,
        token_ok=_is_verse_ref, sort_key=_verse_ref_key,
        token_label="a verse book.line ref (e.g. '1.1')",
    )

    for i, g in enumerate(data.get("expected_line_gaps") or []):
        if not isinstance(g, dict):
            problems.append((manifest.work_id, file_name, f"expected_line_gaps[{i}] must be an object"))
            continue
        if not isinstance(g.get("book"), int):
            problems.append((manifest.work_id, file_name, f"expected_line_gaps[{i}].book must be an integer"))
        if not isinstance(g.get("after"), int) or not isinstance(g.get("next"), int):
            problems.append(
                (manifest.work_id, file_name,
                 f"expected_line_gaps[{i}] must have integer after/next")
            )

    # greek_source (path under sources/) is the preferred Perseus path key.
    work = data.get("work") if isinstance(data.get("work"), dict) else {}
    gs = work.get("greek_source")
    if gs is not None and (not isinstance(gs, str) or not gs):
        problems.append((manifest.work_id, file_name, "work.greek_source must be a non-empty string when set"))


def _validate_section_manifest_schema(manifest: WorkManifest, problems: list[Problem]) -> None:
    """Section-scheme (stephanus) manifest rules: an english.primary translation
    block, a section_spine fingerprint, and books bounded by section tokens. A
    Bekker range and an explicit chapter div do not apply (the reader cites by
    section and gets outline nav from sections.json); they are validated only if
    a manifest chooses to declare them."""
    data = manifest.data
    file_name = manifest.path.name

    english = data.get("english") if isinstance(data.get("english"), dict) else {}
    primary = english.get("primary")
    if not isinstance(primary, dict):
        problems.append((manifest.work_id, file_name, "english.primary must be an object"))
    else:
        for key in ["id", "name", "model", "file"]:
            if not isinstance(primary.get(key), str) or not primary.get(key):
                problems.append((manifest.work_id, file_name, f"english.primary.{key} must be a non-empty string"))

    spine = data.get("section_spine")
    if not isinstance(spine, dict):
        problems.append((manifest.work_id, file_name, "section_spine must be an object"))
    else:
        if not isinstance(spine.get("count"), int):
            problems.append((manifest.work_id, file_name, "section_spine.count must be an integer"))
        sha256 = spine.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            problems.append((manifest.work_id, file_name, "section_spine.sha256 must be a 64-character hex string"))

    _validate_books_schema(
        manifest, problems,
        token_ok=_is_section_token, sort_key=column_prefix_key,
        token_label="a Stephanus section token",
    )

    # A section manifest normally omits bekker_range/chapters; validate them only
    # if present so a future variant can still declare them meaningfully.
    bekker = data.get("bekker_range")
    if bekker is not None:
        if not isinstance(bekker, dict):
            problems.append((manifest.work_id, file_name, "bekker_range must be an object"))
        else:
            for key in ["first_column", "last_column"]:
                if not _is_column(bekker.get(key)):
                    problems.append((manifest.work_id, file_name, f"bekker_range.{key} must be a section token"))


def _validate_books_schema(
    manifest: WorkManifest,
    problems: list[Problem],
    *,
    token_ok,
    sort_key,
    token_label: str,
) -> None:
    """Shared books-list schema: unique integer numbers and ordered, in-range,
    non-overlapping boundaries. The boundary token grammar (full Bekker ref vs.
    section token) and its sort key vary by scheme, passed in by the caller."""
    file_name = manifest.path.name
    books = manifest.data.get("books") if isinstance(manifest.data.get("books"), list) else []
    previous_end = None
    seen_books: set[int] = set()
    for i, book in enumerate(books):
        if not isinstance(book, dict):
            problems.append((manifest.work_id, file_name, f"books[{i}] must be an object"))
            continue
        n = book.get("n")
        if not isinstance(n, int):
            problems.append((manifest.work_id, file_name, f"books[{i}].n must be an integer"))
        elif n in seen_books:
            problems.append((manifest.work_id, file_name, f"duplicate book number {n}"))
        else:
            seen_books.add(n)
        start = book.get("start")
        end = book.get("end")
        if not token_ok(start):
            problems.append((manifest.work_id, file_name, f"books[{i}].start must be {token_label}"))
            continue
        if not token_ok(end):
            problems.append((manifest.work_id, file_name, f"books[{i}].end must be {token_label}"))
            continue
        start_key = sort_key(start)
        end_key = sort_key(end)
        if start_key > end_key:
            problems.append((manifest.work_id, file_name, f"books[{i}] start must not be after end"))
        if previous_end is not None and start_key < previous_end:
            problems.append((manifest.work_id, file_name, f"books[{i}] start is before previous book end"))
        previous_end = end_key


def _validate_work_data(data_dir: Path, manifest: WorkManifest, problems: list[Problem]) -> None:
    work_dir = data_dir / manifest.work_id
    if not work_dir.exists():
        problems.append((manifest.work_id, str(work_dir), "emitted work directory does not exist"))
        return
    if not work_dir.is_dir():
        problems.append((manifest.work_id, str(work_dir), "emitted work path is not a directory"))
        return

    loaded: dict[str, Any] = {}
    required = ["manifest.json", "chapters.json", "columns.json", "analyses.json"]
    for book in manifest.data.get("books", []):
        if isinstance(book, dict) and isinstance(book.get("n"), int):
            required.append(f"book-{book['n']:02d}.json")
    for name in required:
        path = work_dir / name
        if not path.exists():
            problems.append((manifest.work_id, name, "emitted JSON file is missing"))
            continue
        try:
            loaded[name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append((manifest.work_id, name, f"invalid JSON: {exc}"))

    # Non-Bekker works (e.g. Porphyry's Isagoge, citation.scheme: busse; Homer
    # verse-line) carry synthetic column/line numbers that do not obey Bekker
    # ordering/anchoring semantics, so the Bekker-specific structural checks are
    # skipped for them (schema, file existence, JSON validity, columns, analyses,
    # and public gating still run).
    scheme = scheme_mod.for_manifest(manifest.data)
    bekker_native = scheme.bekker_native
    verse = scheme.name == "verse-line"

    # Manifests declare known, verified irregularities in the line numbering
    # (`expected_line_gaps`). Bekker shape: {column, after, next}. Verse shape:
    # {book, after, next} — normalised below to (column_str, after, next) so the
    # shared book walker can honour them.
    expected_gaps: set[tuple[str, int, int]] = set()
    for g in (manifest.data.get("expected_line_gaps") or []):
        if not isinstance(g, dict):
            continue
        if {"column", "after", "next"} <= g.keys():
            expected_gaps.add((g["column"], g["after"], g["next"]))
        elif verse and {"book", "after", "next"} <= g.keys():
            expected_gaps.add((str(g["book"]), g["after"], g["next"]))

    _validate_emitted_manifest(manifest, loaded.get("manifest.json"), problems)
    segments, anchors, token_keys = _validate_books(
        manifest, loaded, problems, bekker_native, expected_gaps, verse=verse,
    )
    _validate_chapters(manifest, loaded.get("chapters.json"), segments, anchors, problems, bekker_native)
    _validate_columns(manifest, loaded.get("columns.json"), segments, problems, verse=verse)
    _validate_analyses(manifest, data_dir, loaded.get("analyses.json"), token_keys, problems)
    _validate_public_gating(manifest, loaded, problems)
    if verse:
        _validate_apparatus(manifest, data_dir, loaded, problems)


def _validate_emitted_manifest(manifest: WorkManifest, emitted: Any, problems: list[Problem]) -> None:
    if emitted is None:
        return
    if not isinstance(emitted, dict):
        problems.append((manifest.work_id, "manifest.json", "root must be an object"))
        return
    work = emitted.get("work")
    if not isinstance(work, dict):
        problems.append((manifest.work_id, "manifest.json", "work must be an object"))
        return
    if work.get("id") != manifest.work_id:
        problems.append((manifest.work_id, "manifest.json", f"work.id {work.get('id')!r} does not match manifest"))


def _validate_books(
    manifest: WorkManifest,
    loaded: dict[str, Any],
    problems: list[Problem],
    bekker_native: bool = True,
    expected_gaps: set[tuple[str, int, int]] | None = None,
    *,
    verse: bool = False,
) -> tuple[dict[tuple[int, str], dict[str, Any]], set[tuple[int, str, int]], set[str]]:
    expected_gaps = expected_gaps or set()
    segments_by_book_col: dict[tuple[int, str], dict[str, Any]] = {}
    anchors: set[tuple[int, str, int]] = set()
    token_keys: set[str] = set()
    seen_segment_ids: set[str] = set()
    previous_segment_key: tuple[int, str, int] | None = None

    for book in manifest.data.get("books", []):
        if not isinstance(book, dict) or not isinstance(book.get("n"), int):
            continue
        name = f"book-{book['n']:02d}.json"
        doc = loaded.get(name)
        if doc is None:
            continue
        if not isinstance(doc, dict):
            problems.append((manifest.work_id, name, "root must be an object"))
            continue
        if doc.get("book") != book["n"]:
            problems.append((manifest.work_id, name, f"book field must be {book['n']}"))
        segments = doc.get("segments")
        if not isinstance(segments, list):
            problems.append((manifest.work_id, name, "segments must be a list"))
            continue
        previous_in_book: tuple[int, str, int] | None = None
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                problems.append((manifest.work_id, name, f"segments[{i}] must be an object"))
                continue
            seg_id = segment.get("id")
            column = segment.get("column")
            if not isinstance(seg_id, str) or not seg_id:
                problems.append((manifest.work_id, name, f"segments[{i}].id must be a non-empty string"))
            elif seg_id in seen_segment_ids:
                problems.append((manifest.work_id, name, f"duplicate segment id {seg_id}"))
            else:
                seen_segment_ids.add(seg_id)
            col_ok = (
                (isinstance(column, str) and column.isdigit()) if verse else _is_column(column)
            )
            if not col_ok:
                label = "a book-number column" if verse else "a Bekker column string"
                problems.append((manifest.work_id, name, f"segments[{i}].column must be {label}"))
                continue
            greek = segment.get("greek")
            if not isinstance(greek, list) or not greek:
                problems.append((manifest.work_id, name, f"segments[{i}].greek must be a non-empty list"))
                continue
            line_numbers: set[int] = set()
            previous_line: int | None = None
            for j, line in enumerate(greek):
                if not isinstance(line, dict):
                    problems.append((manifest.work_id, name, f"{seg_id}: greek[{j}] must be an object"))
                    continue
                n = line.get("n")
                if not isinstance(n, int):
                    problems.append((manifest.work_id, name, f"{seg_id}: greek[{j}].n must be an integer"))
                    continue
                prior_line = previous_line
                declared_gap = (column, prior_line, n) in expected_gaps
                if (bekker_native or verse) and prior_line is not None and n < prior_line and not declared_gap:
                    kind = "verse" if verse else "Bekker"
                    problems.append(
                        (manifest.work_id, name,
                         f"{seg_id}: Greek {kind} lines are out of order at {column}.{n}" if verse
                         else f"{seg_id}: Greek Bekker lines are out of order at {column}{n}")
                    )
                # Verse continuity: n must be prior+1 unless a declared gap.
                if verse and prior_line is not None and n != prior_line + 1 and not declared_gap:
                    problems.append(
                        (manifest.work_id, name,
                         f"{seg_id}: unexpected verse gap {prior_line} -> {n} in book {column}")
                    )
                previous_line = n
                anchor = (book["n"], column, n)
                if (bekker_native or verse) and anchor in anchors and not declared_gap:
                    problems.append(
                        (manifest.work_id, name,
                         f"duplicate verse anchor {column}.{n}" if verse
                         else f"duplicate Bekker anchor {column}{n}")
                    )
                anchors.add(anchor)
                line_numbers.add(n)
                _collect_token_keys(manifest, name, seg_id or f"segments[{i}]", line, token_keys, problems)

            first_line = min(line_numbers) if line_numbers else 0
            if verse:
                # Sort key: (book, line) — column IS the book number string.
                current_key = (book["n"], "", first_line)
            else:
                current_key = line_key(column, first_line)
            if bekker_native and previous_in_book is not None and current_key < previous_in_book:
                problems.append((manifest.work_id, name, f"{seg_id}: segment Bekker order moved backwards at {column}{first_line}"))
            if bekker_native and previous_segment_key is not None and current_key < previous_segment_key:
                problems.append((manifest.work_id, name, f"{seg_id}: work Bekker order moved backwards at {column}{first_line}"))
            previous_in_book = current_key
            previous_segment_key = current_key
            segments_by_book_col[(book["n"], column)] = {"segment": segment, "lines": line_numbers, "file": name}
            if not verse:
                _validate_english_bekker(manifest, name, seg_id or f"segments[{i}]", segment, line_numbers, problems)
                _validate_chapter_starts(manifest, name, seg_id or f"segments[{i}]", segment, line_numbers, anchors, book["n"], column, problems, bekker_native)
            else:
                _validate_third_bekker(manifest, name, seg_id or f"segments[{i}]", segment, line_numbers, problems)
    return segments_by_book_col, anchors, token_keys


def _collect_token_keys(
    manifest: WorkManifest,
    file_name: str,
    seg_id: str,
    line: dict[str, Any],
    token_keys: set[str],
    problems: list[Problem],
) -> None:
    tokens = line.get("tokens")
    if not isinstance(tokens, list):
        problems.append((manifest.work_id, file_name, f"{seg_id}: greek line tokens must be a list"))
        return
    for token in tokens:
        if not isinstance(token, dict):
            problems.append((manifest.work_id, file_name, f"{seg_id}: token must be an object"))
            continue
        key = token.get("k")
        if not isinstance(key, str) or not key:
            problems.append((manifest.work_id, file_name, f"{seg_id}: token.k must be a non-empty string"))
        else:
            token_keys.add(key)
    for cell in line.get("cells", []) or []:
        if not isinstance(cell, dict):
            problems.append((manifest.work_id, file_name, f"{seg_id}: cell must be an object"))
            continue
        if not isinstance(cell.get("tokens"), list):
            problems.append((manifest.work_id, file_name, f"{seg_id}: cell tokens must be a list"))


def _validate_english_bekker(
    manifest: WorkManifest,
    file_name: str,
    seg_id: str,
    segment: dict[str, Any],
    line_numbers: set[int],
    problems: list[Problem],
) -> None:
    english = segment.get("english")
    if english is None:
        return
    if not isinstance(english, dict):
        problems.append((manifest.work_id, file_name, f"{seg_id}: english must be an object or null"))
        return
    for marker in english.get("bekker", []) or []:
        if not isinstance(marker, dict):
            problems.append((manifest.work_id, file_name, f"{seg_id}: english.bekker marker must be an object"))
            continue
        n = marker.get("n")
        if not isinstance(n, int):
            problems.append((manifest.work_id, file_name, f"{seg_id}: english.bekker.n must be an integer"))
            continue
        # NOTE: english.bekker markers carry only a line number `n`, not the
        # column. A segment's English prose routinely runs past its own column
        # into the next one, so the marker list legitimately contains e.g.
        # ...,30,35,1 (column X line 35 then column X+1 line 1). Without a column
        # tag we cannot tell that valid reset apart from real disorder, nor
        # verify a marker's Greek anchor (line 1 belongs to the next column's
        # Greek, absent from this segment's line set). Both checks produced only
        # false positives on the live corpus, so marker *shape* is validated but
        # ordering/anchoring is not.


def _validate_third_bekker(
    manifest: WorkManifest,
    file_name: str,
    seg_id: str,
    segment: dict[str, Any],
    line_numbers: set[int],
    problems: list[Problem],
) -> None:
    """Validate segment.third[*].bekker (the Pope-overlay tick lists emitted
    by stage1_pope.py's curated scene-anchor resolution) more strictly than
    english.bekker (_validate_english_bekker above, which validates shape
    only): every tick's `n` must be a real Greek line of this book's single
    verse-line segment, its `offset` must fall within that piece's own text
    length, and both n and offset must be non-decreasing across the list.
    Pope's overlay is book-anchored with at most one segment per book
    (unlike English, whose prose legitimately resets across column
    boundaries — see that function's NOTE), so there is no equivalent excuse
    for disorder here."""
    third = segment.get("third")
    if not third:
        return
    if not isinstance(third, list):
        problems.append((manifest.work_id, file_name, f"{seg_id}: third must be a list"))
        return
    for pi, piece in enumerate(third):
        if not isinstance(piece, dict):
            problems.append((manifest.work_id, file_name, f"{seg_id}: third[{pi}] must be an object"))
            continue
        piece_text = piece.get("text")
        text_len = len(piece_text) if isinstance(piece_text, str) else 0
        prev_n: int | None = None
        prev_offset: int | None = None
        for ti, marker in enumerate(piece.get("bekker") or []):
            if not isinstance(marker, dict):
                problems.append(
                    (manifest.work_id, file_name, f"{seg_id}: third[{pi}].bekker[{ti}] must be an object")
                )
                continue
            n = marker.get("n")
            offset = marker.get("offset")
            if not isinstance(n, int):
                problems.append(
                    (manifest.work_id, file_name, f"{seg_id}: third[{pi}].bekker[{ti}].n must be an integer")
                )
                continue
            if not isinstance(offset, int):
                problems.append(
                    (manifest.work_id, file_name, f"{seg_id}: third[{pi}].bekker[{ti}].offset must be an integer")
                )
                continue
            if n not in line_numbers:
                problems.append(
                    (manifest.work_id, file_name,
                     f"{seg_id}: third[{pi}].bekker[{ti}] n={n} is not a Greek line of this book")
                )
            if not (0 <= offset < text_len):
                problems.append(
                    (manifest.work_id, file_name,
                     f"{seg_id}: third[{pi}].bekker[{ti}] offset={offset} is outside the piece "
                     f"text (length {text_len})")
                )
            if prev_n is not None and n < prev_n:
                problems.append(
                    (manifest.work_id, file_name, f"{seg_id}: third[{pi}].bekker is not non-decreasing in n at index {ti}")
                )
            if prev_offset is not None and offset < prev_offset:
                problems.append(
                    (manifest.work_id, file_name,
                     f"{seg_id}: third[{pi}].bekker is not non-decreasing in offset at index {ti}")
                )
            prev_n, prev_offset = n, offset


def _validate_chapter_starts(
    manifest: WorkManifest,
    file_name: str,
    seg_id: str,
    segment: dict[str, Any],
    line_numbers: set[int],
    anchors: set[tuple[int, str, int]],
    book: int,
    column: str,
    problems: list[Problem],
    bekker_native: bool = True,
) -> None:
    starts = segment.get("chapterStarts", []) or []
    if not isinstance(starts, list):
        problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStarts must be a list"))
        return
    previous_line: int | None = None
    for start in starts:
        if not isinstance(start, dict):
            problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStart must be an object"))
            continue
        before_line = start.get("beforeLine")
        if not isinstance(before_line, int):
            problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStarts.beforeLine must be an integer"))
            continue
        if bekker_native and previous_line is not None and before_line < previous_line:
            problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStarts are out of order at line {before_line}"))
        if bekker_native and before_line not in line_numbers:
            problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStart beforeLine {before_line} has no Greek line"))
        if bekker_native and (book, column, before_line) not in anchors:
            problems.append((manifest.work_id, file_name, f"{seg_id}: chapterStart beforeLine {before_line} has no Bekker anchor"))
        previous_line = before_line


def _validate_chapters(
    manifest: WorkManifest,
    chapters: Any,
    segments: dict[tuple[int, str], dict[str, Any]],
    anchors: set[tuple[int, str, int]],
    problems: list[Problem],
    bekker_native: bool = True,
) -> None:
    if chapters is None:
        return
    if not isinstance(chapters, dict):
        problems.append((manifest.work_id, "chapters.json", "root must be an object"))
        return
    for book_key, refs in chapters.items():
        try:
            book = int(book_key)
        except (TypeError, ValueError):
            problems.append((manifest.work_id, "chapters.json", f"book key {book_key!r} is not an integer string"))
            continue
        if not isinstance(refs, list):
            problems.append((manifest.work_id, "chapters.json", f"book {book_key} value must be a list"))
            continue
        previous: tuple[int, str, int] | None = None
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                problems.append((manifest.work_id, "chapters.json", f"{book_key}[{i}] must be an object"))
                continue
            column = ref.get("column")
            line_raw = ref.get("line")
            if not _is_column(column):
                problems.append((manifest.work_id, "chapters.json", f"{book_key}[{i}].column must be a Bekker column string"))
                continue
            try:
                line = int(line_raw)
            except (TypeError, ValueError):
                problems.append((manifest.work_id, "chapters.json", f"{book_key}[{i}].line must be an integer string"))
                continue
            current = line_key(column, line)
            if bekker_native and previous is not None and current < previous:
                problems.append((manifest.work_id, "chapters.json", f"chapter refs are out of order at {column}{line}"))
            previous = current
            # Book divisions do not always align with Bekker column boundaries:
            # a book's opening chapter can begin mid-column in a column that is
            # emitted under the PREVIOUS book (e.g. Rhetoric, where Freese marks
            # the I/II and II/III divisions one column before the Greek). When
            # the same column exists under book-1, treat the anchor as a
            # legitimate book-boundary offset rather than a dangling reference.
            missing_segment = (book, column) not in segments
            boundary_offset = missing_segment and (book - 1, column) in segments
            if missing_segment and not boundary_offset:
                problems.append((manifest.work_id, "chapters.json", f"chapter {ref.get('chapter')!r} points to missing segment {book}:{column}"))
            elif not missing_segment and bekker_native and line not in segments[(book, column)]["lines"]:
                problems.append((manifest.work_id, "chapters.json", f"chapter {ref.get('chapter')!r} points to missing Bekker anchor {column}{line}"))
            if bekker_native and not boundary_offset and (book, column, line) not in anchors:
                problems.append((manifest.work_id, "chapters.json", f"chapter {ref.get('chapter')!r} has dangling Bekker anchor {column}{line}"))
            if bekker_native and not boundary_offset:
                _validate_bekker_span(manifest, "chapters.json", ref.get("bekker"), anchors, book, problems)


def _validate_columns(
    manifest: WorkManifest,
    columns: Any,
    segments: dict[tuple[int, str], dict[str, Any]],
    problems: list[Problem],
    *,
    verse: bool = False,
) -> None:
    if columns is None:
        return
    if not isinstance(columns, dict):
        problems.append((manifest.work_id, "columns.json", "root must be an object"))
        return
    for column, entries in columns.items():
        col_ok = (isinstance(column, str) and column.isdigit()) if verse else _is_column(column)
        if not col_ok:
            label = "a book-number column" if verse else "a Bekker column"
            problems.append((manifest.work_id, "columns.json", f"column key {column!r} is not {label}"))
            continue
        if not isinstance(entries, list):
            problems.append((manifest.work_id, "columns.json", f"{column} entries must be a list"))
            continue
        previous_book: int | None = None
        for entry in entries:
            if not isinstance(entry, dict):
                problems.append((manifest.work_id, "columns.json", f"{column} entry must be an object"))
                continue
            book = entry.get("book")
            lo = entry.get("lo")
            hi = entry.get("hi")
            if not isinstance(book, int) or not isinstance(lo, int) or not isinstance(hi, int):
                problems.append((manifest.work_id, "columns.json", f"{column} entry book/lo/hi must be integers"))
                continue
            if lo > hi:
                problems.append((manifest.work_id, "columns.json", f"{column} book {book} lo must not exceed hi"))
            if previous_book is not None and book < previous_book:
                problems.append((manifest.work_id, "columns.json", f"{column} book entries are out of order"))
            previous_book = book
            segment = segments.get((book, column))
            if segment is None:
                problems.append((manifest.work_id, "columns.json", f"{column} book {book} has no emitted segment"))
            else:
                lines = segment["lines"]
                if lines and (min(lines) != lo or max(lines) != hi):
                    problems.append((manifest.work_id, "columns.json", f"{column} book {book} range {lo}-{hi} does not match Greek lines"))
    for book, column in segments:
        if column not in columns:
            problems.append((manifest.work_id, "columns.json", f"missing column entry for {book}:{column}"))


def _validate_analyses(
    manifest: WorkManifest,
    data_dir: Path,
    analyses: Any,
    token_keys: set[str],
    problems: list[Problem],
) -> None:
    if analyses is None:
        return
    if not isinstance(analyses, dict):
        problems.append((manifest.work_id, "analyses.json", "root must be an object"))
        return
    # A referenced Greek token having no entry in analyses is EXPECTED, not a
    # defect: Morpheus fails to parse some rare/inflected forms and the
    # spurious-parse filter deliberately drops others, so the reader simply
    # shows no word popup for them. Flagging every such token produced ~1300
    # false positives against the live corpus, so token-key *presence* is not
    # validated. (token_keys is still passed in for possible future coverage
    # reporting.) The structural validation of the entries that DO exist, and
    # LSJ-key resolution, remain below.
    lsj_keys: set[str] = set()
    for key, entries in analyses.items():
        if not isinstance(entries, list):
            problems.append((manifest.work_id, "analyses.json", f"{key}: analyses value must be a list"))
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                problems.append((manifest.work_id, "analyses.json", f"{key}: analysis entry must be an object"))
                continue
            for required in ["lemma", "gloss", "parse"]:
                if not isinstance(entry.get(required), str):
                    problems.append((manifest.work_id, "analyses.json", f"{key}: {required} must be a string"))
            lsj = entry.get("lsj")
            if not isinstance(lsj, list):
                problems.append((manifest.work_id, "analyses.json", f"{key}: lsj must be a list"))
                continue
            for lsj_key in lsj:
                if not isinstance(lsj_key, str) or not lsj_key:
                    problems.append((manifest.work_id, "analyses.json", f"{key}: lsj key must be a non-empty string"))
                else:
                    lsj_keys.add(lsj_key)
    _validate_lsj_keys(manifest, data_dir, lsj_keys, problems)


def _validate_lsj_keys(
    manifest: WorkManifest,
    data_dir: Path,
    lsj_keys: set[str],
    problems: list[Problem],
) -> None:
    shards: dict[str, dict[str, Any]] = {}
    for key in sorted(lsj_keys):
        shard_name = _lsj_shard(key)
        shard_path = data_dir / "lsj" / f"{shard_name}.json"
        if not shard_path.exists():
            problems.append((manifest.work_id, f"lsj/{shard_name}.json", f"LSJ key {key!r} references missing shard"))
            continue
        if shard_name not in shards:
            try:
                shard = json.loads(shard_path.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append((manifest.work_id, f"lsj/{shard_name}.json", f"invalid JSON: {exc}"))
                continue
            if not isinstance(shard, dict):
                problems.append((manifest.work_id, f"lsj/{shard_name}.json", "shard root must be an object"))
                continue
            shards[shard_name] = shard
        if key not in shards.get(shard_name, {}):
            problems.append((manifest.work_id, f"lsj/{shard_name}.json", f"LSJ key {key!r} is not present in shard"))


def _validate_public_gating(
    manifest: WorkManifest,
    loaded: dict[str, Any],
    problems: list[Problem],
) -> None:
    if manifest.public_path is None or manifest.private_data is None:
        return
    omitted = _omitted_translation_slots(manifest.private_data, manifest.data)
    if not omitted:
        return
    for file_name, doc in loaded.items():
        if not file_name.startswith("book-") or not isinstance(doc, dict):
            continue
        for segment in doc.get("segments", []) or []:
            if not isinstance(segment, dict):
                continue
            for slot in omitted:
                if slot == "secondary" and "ross" in segment:
                    problems.append((manifest.work_id, file_name, "private secondary translation appears in public data"))
                elif slot == "third" and "third" in segment:
                    problems.append((manifest.work_id, file_name, "private third translation appears in public data"))
                elif slot.startswith("overlay:"):
                    overlay_id = slot.split(":", 1)[1]
                    overlays = segment.get("overlays")
                    if isinstance(overlays, dict) and overlay_id in overlays:
                        problems.append((manifest.work_id, file_name, f"private overlay {overlay_id!r} appears in public data"))


def _validate_apparatus(
    manifest: WorkManifest,
    data_dir: Path,
    loaded: dict[str, Any],
    problems: list[Problem],
) -> None:
    """Validate the optional `apparatus` object on each emitted book-{n}.json
    (scenes chips + cartouche metadata, see apparatus_scenes.py). A book with
    no apparatus yet (a still-in-flight drafting sweep) is not a failure —
    apparatus coverage is allowed to be partial across a work — but a book
    that DOES carry one must be fully clean: real line bounds, no coverage
    holes/overlaps, gap-boundary respected, summaries <=20 words, draft flag
    present.

    Beyond that per-book quality check, three more emits are asserted here:
    the emitted apparatus.scenes must actually MATCH the canonical
    apparatus/scenes/<work>.json wherever the canonical file covers a book
    (the Gate-4 hardening — see _validate_apparatus_scenes_coverage), and the
    speeches.json / epithets.json emits scripts/build-public.mjs and the
    pipeline's own stages are expected to produce must be present."""
    from . import apparatus_scenes

    bounds = apparatus_scenes.book_bounds(manifest.data)
    gaps = apparatus_scenes.gaps_by_book(manifest.data)
    for book in manifest.data.get("books", []):
        n = book.get("n") if isinstance(book, dict) else None
        if not isinstance(n, int):
            continue
        file_name = f"book-{n:02d}.json"
        doc = loaded.get(file_name)
        if not isinstance(doc, dict) or "apparatus" not in doc:
            continue
        book_end = bounds.get(n)
        if book_end is None:
            continue
        for message in apparatus_scenes.validate_emitted_apparatus(
            n, doc["apparatus"], book_end, gaps.get(n, []),
            reviewed=apparatus_scenes.work_reviewed(manifest.work_id),
        ):
            problems.append((manifest.work_id, file_name, message))

    _validate_apparatus_scenes_coverage(manifest, loaded, problems)
    _validate_apparatus_speeches_emitted(manifest, data_dir, problems)
    _validate_apparatus_epithets_emitted(manifest, data_dir, problems)
    _validate_apparatus_scansion_emitted(manifest, data_dir, problems)
    _validate_apparatus_vocab_emitted(manifest, data_dir, problems)


def _validate_apparatus_scenes_coverage(
    manifest: WorkManifest,
    loaded: dict[str, Any],
    problems: list[Problem],
) -> None:
    """Gate-4 hardening (the priority fix this function exists for): once
    apparatus/scenes/<work>.json — the canonical, merged apparatus source,
    see apparatus_scenes.py's module docstring — covers a book, the emitted
    build/dist/<work>/book-NN.json for that book MUST carry a matching,
    non-empty apparatus.scenes. Before this check, apparatus was validated
    only if present (see _validate_apparatus above): a full rebuild that
    quietly skipped the apparatus merge/emit stage (e.g. because
    apparatus/staging/ had already been cleaned up after an earlier merge —
    apparatus_scenes.run() returns early with no staging files to merge and
    never touches the book JSON at all, see its module docstring) produced
    book files with NO apparatus key, and preflight said nothing. That silent
    corpus-wide wipe is the Gate-4 incident; failing loudly here is the
    point, so this check runs unconditionally whenever the canonical file
    exists — it does not care whether "apparatus" is present in doc at all."""
    from . import apparatus_scenes

    canonical_path = apparatus_scenes.SCENES_DIR / f"{manifest.work_id}.json"
    if not canonical_path.exists():
        return
    try:
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append((manifest.work_id, canonical_path.name, f"invalid JSON: {exc}"))
        return
    if not isinstance(canonical, dict):
        problems.append((manifest.work_id, canonical_path.name, "root must be an object"))
        return

    canonical_name = canonical_path.name
    for book in canonical.get("books", []) or []:
        if not isinstance(book, dict) or not isinstance(book.get("book"), int):
            continue
        book_n = book["book"]
        file_name = f"book-{book_n:02d}.json"
        expected_scenes = apparatus_scenes.emit_book_apparatus(book).get("scenes")
        doc = loaded.get(file_name)
        if not isinstance(doc, dict):
            problems.append(
                (manifest.work_id, file_name,
                 f"apparatus/scenes/{canonical_name} covers book {book_n} but the "
                 f"emitted book file is missing")
            )
            continue
        apparatus = doc.get("apparatus")
        emitted_scenes = apparatus.get("scenes") if isinstance(apparatus, dict) else None
        if not isinstance(emitted_scenes, list) or not emitted_scenes:
            problems.append(
                (manifest.work_id, file_name,
                 f"apparatus/scenes/{canonical_name} covers book {book_n} but the "
                 f"emitted apparatus.scenes is missing or empty (stale/failed apparatus emit)")
            )
            continue
        if emitted_scenes != expected_scenes:
            problems.append(
                (manifest.work_id, file_name,
                 f"emitted apparatus.scenes for book {book_n} does not match "
                 f"apparatus/scenes/{canonical_name} (stale or partial build)")
            )


def _validate_apparatus_speeches_emitted(
    manifest: WorkManifest,
    data_dir: Path,
    problems: list[Problem],
) -> None:
    """scripts/build-public.mjs copies apparatus/speeches/<work>.json verbatim
    to build/dist/<work>/speeches.json ('Copying DICES speech-span apparatus
    into the public data root'). If the source exists, the copy must too."""
    from . import apparatus_scenes

    speeches_src = apparatus_scenes.APPARATUS_DIR / "speeches" / f"{manifest.work_id}.json"
    if not speeches_src.exists():
        return
    speeches_dist = data_dir / manifest.work_id / "speeches.json"
    if not speeches_dist.exists():
        problems.append(
            (manifest.work_id, "speeches.json",
             f"apparatus/speeches/{manifest.work_id}.json exists but was not copied "
             f"into the public data root")
        )
        return
    try:
        json.loads(speeches_dist.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append((manifest.work_id, "speeches.json", f"invalid JSON: {exc}"))


def _validate_apparatus_epithets_emitted(
    manifest: WorkManifest,
    data_dir: Path,
    problems: list[Problem],
) -> None:
    """The 'epithets' pipeline stage (apparatus_epithets.py) is registered for
    every verse-line work and always emits build/dist/<work>/epithets.json —
    absence means the stage silently failed or was skipped."""
    epithets_path = data_dir / manifest.work_id / "epithets.json"
    if not epithets_path.exists():
        problems.append(
            (manifest.work_id, "epithets.json",
             "the epithets pipeline stage is registered but epithets.json was not emitted")
        )
        return
    try:
        json.loads(epithets_path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append((manifest.work_id, "epithets.json", f"invalid JSON: {exc}"))


def _validate_apparatus_scansion_emitted(
    manifest: WorkManifest,
    data_dir: Path,
    problems: list[Problem],
) -> None:
    """The 'scansion' pipeline stage (apparatus_scansion.py) is registered for
    every verse-line work and always emits one
    build/dist/<work>/scansion-<NN>.json per book in the manifest (split from
    a single whole-work file — ~1.5MB for the Iliad — so the reader's Meter
    toggle can lazy-fetch one book at a time). A book with no book-<NN>.json
    emitted yet is not this check's concern (the book-emission gate elsewhere
    already flags that); a book whose book-<NN>.json DOES exist but has no
    matching scansion-<NN>.json means the stage silently failed or was
    skipped for that book."""
    work_dir = data_dir / manifest.work_id
    for book in manifest.data.get("books", []):
        n = book.get("n") if isinstance(book, dict) else None
        if not isinstance(n, int):
            continue
        if not (work_dir / f"book-{n:02d}.json").exists():
            continue
        scansion_path = work_dir / f"scansion-{n:02d}.json"
        if not scansion_path.exists():
            problems.append(
                (manifest.work_id, f"scansion-{n:02d}.json",
                 "the scansion pipeline stage is registered but "
                 f"scansion-{n:02d}.json was not emitted")
            )
            continue
        try:
            json.loads(scansion_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append((manifest.work_id, f"scansion-{n:02d}.json", f"invalid JSON: {exc}"))


def _validate_apparatus_vocab_emitted(
    manifest: WorkManifest,
    data_dir: Path,
    problems: list[Problem],
) -> None:
    """The 'vocab' pipeline stage (apparatus_vocab.py) is registered for
    every verse-line work and always emits build/dist/<work>/vocab.json —
    absence means the stage silently failed or was skipped."""
    vocab_path = data_dir / manifest.work_id / "vocab.json"
    if not vocab_path.exists():
        problems.append(
            (manifest.work_id, "vocab.json",
             "the vocab pipeline stage is registered but vocab.json was not emitted")
        )
        return
    try:
        json.loads(vocab_path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append((manifest.work_id, "vocab.json", f"invalid JSON: {exc}"))


def _validate_global_apparatus_emits(
    data_dir: Path,
    manifests: list[WorkManifest],
    problems: list[Problem],
) -> None:
    """Cross-work apparatus emits scripts/build-public.mjs produces once for
    the whole corpus rather than per work: apparatus/characters.json (the
    cast list) copied to build/dist/characters.json, and repetitions.json
    (the 'repetitions' pipeline stage, cross-epic by construction) at
    build/dist/repetitions.json. Checked only when at least one verse-line
    (Homer) work is present, since both are Homer-specific apparatus and this
    preflight also serves the Bekker/section-scheme siblings' corpora."""
    if not any(scheme_mod.for_manifest(m.data).name == "verse-line" for m in manifests):
        return

    from . import apparatus_scenes

    characters_src = apparatus_scenes.APPARATUS_DIR / "characters.json"
    if characters_src.exists():
        characters_dist = data_dir / "characters.json"
        if not characters_dist.exists():
            problems.append(
                ("-", "characters.json",
                 "apparatus/characters.json exists but was not copied into the public data root")
            )
        else:
            try:
                json.loads(characters_dist.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append(("-", "characters.json", f"invalid JSON: {exc}"))

    repetitions_dist = data_dir / "repetitions.json"
    if not repetitions_dist.exists():
        problems.append(
            ("-", "repetitions.json",
             "the repetitions pipeline stage is registered but repetitions.json was not emitted")
        )
    else:
        try:
            json.loads(repetitions_dist.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(("-", "repetitions.json", f"invalid JSON: {exc}"))

    # apparatus/audio/manifest.json (feature #19, "Hear this passage" —
    # David Chamberlain's recitation audio) copied to build/dist/audio.json,
    # same plain-copy-if-present treatment as characters.json above. This is
    # OPTIONAL apparatus: its absence (no manifest committed yet) is not
    # checked at all, and per-work/per-book coverage gaps (Odyssey 8-24 have
    # no audio whatsoever) are normal and never asserted here — only "if the
    # source exists, the copy must too", same posture as speeches.json.
    audio_src = apparatus_scenes.APPARATUS_DIR / "audio" / "manifest.json"
    if audio_src.exists():
        audio_dist = data_dir / "audio.json"
        if not audio_dist.exists():
            problems.append(
                ("-", "audio.json",
                 "apparatus/audio/manifest.json exists but was not copied into the public data root")
            )
        else:
            try:
                json.loads(audio_dist.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append(("-", "audio.json", f"invalid JSON: {exc}"))


# ── alignment coverage: Murray/Butler/Pope milestone-tick density per book ─
#
# Murray (primary `english` slot) and Butler (`ross` overlay slot) are both
# anchored to the Greek spine by REAL milestone ticks from their Perseus TEI
# (see stage1_perseus_milestone_english.py's module docstring) — each ticks
# list entry is `{n, offset, real: true}`. Pope (`third` overlay slot) now
# carries real ticks too, from stage1_pope.py's curated scene-anchor
# resolution. A book's tick COUNT is a cheap, meaningful proxy for alignment
# density (roughly one tick per ~5 Murray lines, ~5-13 Butler lines): a
# future ingest regression that thins out ticks (a milestone-parsing bug, a
# re-export that drops anchors, ...) would still pass every other structural
# check here while silently degrading the reader's in-line English
# positioning. Pinning today's healthy counts as a floor (see
# test_alignment_coverage.py) turns that into a loud test failure.
#
# TODO(pope floor): alignment_coverage_floor.json does not pin "pope" counts
# yet — the curated scene-anchor dataset (sources/pope/scene-anchors-*.json)
# doesn't exist in this checkout (a parallel lane drafts it; see
# stage1_pope.py's module docstring), so there is no healthy baseline to pin
# today. tick_coverage_violations only checks translators present in the
# floor fixture, so an absent "pope" key is tolerated automatically; pin
# real pope floors once the dataset lands and a full build has run.


def translation_tick_counts(data_dir: Path, work_id: str) -> dict[int, dict[str, int]]:
    """book number -> {"murray": tick_count, "butler": tick_count, "pope":
    tick_count}, read off the emitted build/dist/<work_id>/book-NN.json
    files. Verse-line books have exactly one segment; `english.bekker`
    carries Murray's ticks, `ross[*].bekker` carries Butler's, and
    `third[*].bekker` carries Pope's (each summed generally in case a book
    ever carries more than one piece)."""
    counts: dict[int, dict[str, int]] = {}
    work_dir = data_dir / work_id
    if not work_dir.is_dir():
        return counts
    for path in sorted(work_dir.glob("book-*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        book = doc.get("book")
        if not isinstance(book, int):
            continue
        murray = 0
        butler = 0
        pope = 0
        for segment in doc.get("segments", []) or []:
            if not isinstance(segment, dict):
                continue
            english = segment.get("english")
            if isinstance(english, dict):
                murray += len(english.get("bekker") or [])
            for piece in segment.get("ross") or []:
                if isinstance(piece, dict):
                    butler += len(piece.get("bekker") or [])
            for piece in segment.get("third") or []:
                if isinstance(piece, dict):
                    pope += len(piece.get("bekker") or [])
        counts[book] = {"murray": murray, "butler": butler, "pope": pope}
    return counts


def tick_coverage_violations(
    counts: dict[int, dict[str, int]],
    floor: dict[int, dict[str, int]],
) -> list[str]:
    """Every (book, translator) pair in `floor` whose actual count in
    `counts` is below its pinned minimum. Empty means every book meets or
    exceeds its recorded coverage."""
    violations: list[str] = []
    for book in sorted(floor):
        actual = counts.get(book, {})
        for translator, minimum in sorted(floor[book].items()):
            got = actual.get(translator, 0)
            if got < minimum:
                violations.append(
                    f"book {book} {translator} ticks {got} below recorded floor {minimum}"
                )
    return violations


def _omitted_translation_slots(private: dict[str, Any], public: dict[str, Any]) -> set[str]:
    private_english = private.get("english") if isinstance(private.get("english"), dict) else {}
    public_english = public.get("english") if isinstance(public.get("english"), dict) else {}
    omitted: set[str] = set()
    for slot in ["secondary", "third"]:
        if slot in private_english and slot not in public_english:
            omitted.add(slot)
    private_overlays = {
        item.get("id")
        for item in private_english.get("overlays", []) or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    public_overlays = {
        item.get("id")
        for item in public_english.get("overlays", []) or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for overlay_id in private_overlays - public_overlays:
        omitted.add(f"overlay:{overlay_id}")
    return omitted


def _validate_bekker_span(
    manifest: WorkManifest,
    file_name: str,
    span: Any,
    anchors: set[tuple[int, str, int]],
    book: int,
    problems: list[Problem],
) -> None:
    if not isinstance(span, str) or not span:
        problems.append((manifest.work_id, file_name, "chapter bekker span must be a non-empty string"))
        return
    parts = span.split("–")
    if len(parts) == 1:
        refs = [_span_ref(parts[0], None)]
    elif len(parts) == 2:
        refs = [_span_ref(parts[0], None), _span_ref(parts[1], parts[0])]
    else:
        problems.append((manifest.work_id, file_name, f"invalid Bekker span {span!r}"))
        return
    parsed: list[tuple[str, int]] = []
    for ref in refs:
        if ref is None:
            problems.append((manifest.work_id, file_name, f"invalid Bekker span {span!r}"))
            return
        column, line = ref
        parsed.append(ref)
        if (book, column, line) not in anchors:
            problems.append((manifest.work_id, file_name, f"chapter span {span!r} references missing Bekker anchor {column}{line}"))
    if len(parsed) == 2 and line_key(*parsed[0]) > line_key(*parsed[1]):
        problems.append((manifest.work_id, file_name, f"chapter span {span!r} is out of order"))


def _span_ref(raw: str, first_part: str | None) -> tuple[str, int] | None:
    raw = raw.strip()
    if _is_ref(raw):
        page, side, line = ref_key(raw)
        return f"{page}{side}", line
    if first_part and raw.isdigit() and _is_ref(first_part.strip()):
        page, side, _line = ref_key(first_part.strip())
        return f"{page}{side}", int(raw)
    return None


def _require_object(manifest: WorkManifest, data: dict[str, Any], key: str, problems: list[Problem]) -> None:
    if not isinstance(data.get(key), dict):
        problems.append((manifest.work_id, manifest.path.name, f"{key} must be an object"))


def _require_list(manifest: WorkManifest, data: dict[str, Any], key: str, problems: list[Problem]) -> None:
    if not isinstance(data.get(key), list):
        problems.append((manifest.work_id, manifest.path.name, f"{key} must be a list"))


def _is_column(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        column_key(value)
    except ValueError:
        return False
    return True


def _is_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        ref_key(value)
    except ValueError:
        return False
    return True


def _is_section_token(value: Any) -> bool:
    """A section-scheme book boundary is a page+section token, given either as a
    bare column ('357a') or a full ref ('2a1') — the book table may use either
    interchangeably (only the page+letter prefix decides book membership)."""
    return _is_column(value) or _is_ref(value)


def _lsj_shard(key: str) -> str:
    for ch in key:
        if ch == "*":
            continue
        if "a" <= ch <= "z":
            return ch
    return "_"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
