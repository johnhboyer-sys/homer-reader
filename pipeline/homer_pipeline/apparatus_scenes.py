"""Apparatus stage: merge drafted scenes.json staging batches into the
canonical per-work file, then emit each book's apparatus data (cartouche
metadata + marginal scene chips) onto the already-emitted book-{n}.json.

Two artifacts:
  - apparatus/scenes/<work>.json   canonical merged scenes, sorted by book,
                                    schema-validated (see docs/APPARATUS-SCHEMAS.md).
                                    Carries `status: "draft"` at both the file
                                    level and per-book (so John can flip a
                                    single book to "reviewed" without touching
                                    the rest).
  - build/dist/<work>/book-{n}.json  gains an "apparatus" key matching the
                                    shape app/src/components/ReaderShell.astro
                                    reads off `bookData.apparatus`:
                                    {argument, where, who, day, draft, scenes}.

Validation is schema-driven, not vibes-driven: every scene range must fall
inside the book's real (manifest-declared) line bounds, must not start/end on
a vulgate numbering gap's missing lines, scenes must be non-overlapping and
must tile the book with no holes (a jump between scenes is legal only at a
declared expected_line_gaps boundary), and summaries stay <=20 words. The same
`validate_scenes_list` core runs at merge time (staging -> canonical) and at
preflight time (the emitted book JSON's apparatus.scenes), so both gates enforce
identical rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import BUILD_DIR, REPO_ROOT, Manifest

APPARATUS_DIR = REPO_ROOT / "apparatus"
STAGING_DIR = APPARATUS_DIR / "staging"
SCENES_DIR = APPARATUS_DIR / "scenes"

MAX_SUMMARY_WORDS = 20
MAX_ARGUMENT_WORDS = 15


class ApparatusValidationError(ValueError):
    """Raised when merged/staged scenes data violates the schema. Carries the
    full list of violations so the caller can print all of them at once
    instead of failing on the first."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


# ── manifest-derived book geometry ──────────────────────────────────────────


def book_bounds(manifest_data: dict) -> dict[int, int]:
    """book number -> last real vulgate line (from books[].end, verse refs are
    'book.line'). Takes a raw manifest data dict (works for both the pipeline's
    Manifest.data and preflight's WorkManifest.data — same YAML shape) so this
    has no dependency on which manifest wrapper class the caller uses."""
    bounds = {}
    for b in manifest_data.get("books", []):
        n = b["n"]
        end_line = int(str(b["end"]).split(".", 1)[1])
        bounds[n] = end_line
    return bounds


def gaps_by_book(manifest_data: dict) -> dict[int, list[tuple[int, int]]]:
    """book number -> [(after, next), ...] declared expected_line_gaps."""
    gaps: dict[int, list[tuple[int, int]]] = {}
    for g in manifest_data.get("expected_line_gaps") or []:
        gaps.setdefault(g["book"], []).append((g["after"], g["next"]))
    return gaps


# ── core scene-list validation (shared by merge + preflight) ───────────────


def _is_valid_line(line: int, book_end: int, gaps: list[tuple[int, int]]) -> bool:
    if not (1 <= line <= book_end):
        return False
    return not any(after < line < nxt for after, nxt in gaps)


def validate_scenes_list(
    scenes: Any, book_n: int, book_end: int, gaps: list[tuple[int, int]]
) -> list[str]:
    """Structural + coverage validation of a book's scenes[] against its real
    line bounds and declared numbering gaps. Returns human-readable violation
    strings (empty when clean)."""
    problems: list[str] = []
    if not isinstance(scenes, list) or not scenes:
        return [f"book {book_n}: scenes must be a non-empty list"]

    parsed: list[tuple[int, int]] = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            problems.append(f"book {book_n}: scenes[{i}] must be an object")
            continue
        lines = scene.get("lines")
        if (
            not isinstance(lines, list)
            or len(lines) != 2
            or not all(isinstance(x, int) for x in lines)
        ):
            problems.append(f"book {book_n}: scenes[{i}].lines must be [int, int]")
            continue
        lo, hi = lines
        if lo > hi:
            problems.append(f"book {book_n}: scenes[{i}].lines {lo}-{hi} out of order")
            continue
        if not _is_valid_line(lo, book_end, gaps):
            problems.append(
                f"book {book_n}: scenes[{i}] starts on nonexistent/out-of-range line {lo}"
            )
        if not _is_valid_line(hi, book_end, gaps):
            problems.append(
                f"book {book_n}: scenes[{i}] ends on nonexistent/out-of-range line {hi}"
            )
        summary = scene.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            problems.append(f"book {book_n}: scenes[{i}].summary must be a non-empty string")
        elif len(summary.split()) > MAX_SUMMARY_WORDS:
            problems.append(
                f"book {book_n}: scenes[{i}].summary exceeds {MAX_SUMMARY_WORDS} words "
                f"({len(summary.split())}): {summary!r}"
            )
        if not isinstance(scene.get("location"), str) or not scene["location"].strip():
            problems.append(f"book {book_n}: scenes[{i}].location must be a non-empty string")
        day_number = scene.get("dayNumber")
        if day_number is not None and not isinstance(day_number, int):
            problems.append(f"book {book_n}: scenes[{i}].dayNumber must be an integer or null")
        parsed.append((lo, hi))

    # Coverage: ascending, non-overlapping, tiling the whole book — a jump
    # between consecutive scenes is legal only across a declared gap.
    prev_hi = 0
    for i, (lo, hi) in enumerate(parsed):
        if prev_hi == 0:
            if lo != 1:
                problems.append(
                    f"book {book_n}: coverage hole — scenes[{i}] starts at line {lo}, "
                    f"expected line 1"
                )
        else:
            gap = next((g for g in gaps if g[0] == prev_hi), None)
            expected_lo = gap[1] if gap else prev_hi + 1
            if lo < expected_lo:
                problems.append(
                    f"book {book_n}: scenes[{i}] overlaps the previous scene "
                    f"(starts at {lo}, previous ended at {prev_hi})"
                )
            elif lo > expected_lo:
                problems.append(
                    f"book {book_n}: coverage hole between line {prev_hi} and {lo} "
                    f"(scenes[{i}])"
                )
        prev_hi = hi
    if parsed and prev_hi != book_end:
        problems.append(
            f"book {book_n}: coverage incomplete — last scene ends at line {prev_hi}, "
            f"book ends at line {book_end}"
        )
    return problems


def _validate_common_fields(book_n: int, argument: Any, where: Any, who: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(argument, str) or not argument.strip():
        problems.append(f"book {book_n}: argument must be a non-empty string")
    elif len(argument.split()) > MAX_ARGUMENT_WORDS:
        problems.append(
            f"book {book_n}: argument exceeds {MAX_ARGUMENT_WORDS} words "
            f"({len(argument.split())}): {argument!r}"
        )
    if not isinstance(who, list) or not all(isinstance(w, str) for w in who):
        problems.append(f"book {book_n}: who must be a list of strings")
    if where is not None:
        if not isinstance(where, list) or not all(isinstance(w, str) for w in where):
            problems.append(f"book {book_n}: where must be a list of strings")
    return problems


def validate_staging_book(book: dict, book_end: int, gaps: list[tuple[int, int]]) -> list[str]:
    """Validate one staging-file book entry (pre-merge shape: argument, where,
    who, days, scenes — see docs/APPARATUS-SCHEMAS.md)."""
    book_n = book.get("book")
    if not isinstance(book_n, int):
        return ["book entry missing an integer 'book' number"]
    problems = _validate_common_fields(book_n, book.get("argument"), book.get("where"), book.get("who"))
    if "days" not in book or not isinstance(book.get("days"), str) or not book["days"].strip():
        problems.append(f"book {book_n}: days must be a non-empty string")
    problems += validate_scenes_list(book.get("scenes"), book_n, book_end, gaps)
    return problems


def validate_emitted_apparatus(
    book_n: int, apparatus: Any, book_end: int, gaps: list[tuple[int, int]],
    reviewed: bool = False,
) -> list[str]:
    """Validate the apparatus object as emitted onto book-{n}.json (post-merge
    shape: argument, where (string), who, day, draft, scenes)."""
    if not isinstance(apparatus, dict):
        return [f"book {book_n}: apparatus must be an object"]
    problems: list[str] = []
    if "argument" in apparatus:
        arg = apparatus["argument"]
        if not isinstance(arg, str) or not arg.strip():
            problems.append(f"book {book_n}: apparatus.argument must be a non-empty string")
        elif len(arg.split()) > MAX_ARGUMENT_WORDS:
            problems.append(
                f"book {book_n}: apparatus.argument exceeds {MAX_ARGUMENT_WORDS} words"
            )
    if "where" in apparatus and not isinstance(apparatus["where"], str):
        problems.append(f"book {book_n}: apparatus.where must be a string")
    if "who" in apparatus:
        who = apparatus["who"]
        if not isinstance(who, list) or not all(isinstance(w, str) for w in who):
            problems.append(f"book {book_n}: apparatus.who must be a list of strings")
    if "day" in apparatus and not isinstance(apparatus["day"], str):
        problems.append(f"book {book_n}: apparatus.day must be a string")
    if reviewed:
        if apparatus.get("draft") is not False:
            problems.append(
                f"book {book_n}: apparatus.draft must be present and False "
                "(work is signed off reviewed)"
            )
    elif apparatus.get("draft") is not True:
        problems.append(f"book {book_n}: apparatus.draft flag must be present and true")
    problems += validate_scenes_list(apparatus.get("scenes"), book_n, book_end, gaps)
    return problems


# ── merge: staging -> canonical apparatus/scenes/<work>.json ───────────────


def discover_staging(work_id: str) -> list[Path]:
    return sorted(STAGING_DIR.glob(f"scenes-{work_id}-*.json"))


def work_reviewed(work_id: str) -> bool:
    """John's draft->reviewed sign-off (the flip is his gate alone,
    CLAUDE.md): an apparatus/scenes/<work>.REVIEWED marker file, created at
    his explicit instruction (2026-07-18 launch night), promotes the merged
    apparatus out of draft. Staging batches themselves stay status "draft"
    forever - they are authorship records; the sign-off applies to the
    canonical merge."""
    return (SCENES_DIR / f"{work_id}.REVIEWED").exists()


def merge_staging(manifest: Manifest) -> dict:
    """Merge every apparatus/staging/scenes-<work>-*.json batch for this work
    into one canonical, sorted, schema-validated document. Raises
    ApparatusValidationError (listing every violation) instead of writing
    anything if any batch or any book fails validation. Missing books (e.g. a
    still-in-flight Odyssey sweep) are simply absent from the result — partial
    coverage across the WORK is not a merge failure, but every book that IS
    present must individually be complete and clean."""
    work_id = manifest.work_id
    files = discover_staging(work_id)
    status = "reviewed" if work_reviewed(work_id) else "draft"
    if not files:
        return {"work": work_id, "status": status, "books": []}

    bounds = book_bounds(manifest.data)
    gaps = gaps_by_book(manifest.data)

    problems: list[str] = []
    books_by_n: dict[int, dict] = {}
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if raw.get("work") != work_id:
            problems.append(f"{path.name}: work {raw.get('work')!r} does not match {work_id!r}")
            continue
        if raw.get("status") != "draft":
            problems.append(f"{path.name}: status must be 'draft'")
        for book in raw.get("books", []):
            book_n = book.get("book")
            if not isinstance(book_n, int):
                problems.append(f"{path.name}: book entry missing an integer 'book' number")
                continue
            if book_n in books_by_n:
                problems.append(
                    f"{path.name}: duplicate book {book_n} "
                    f"(already staged in another batch)"
                )
                continue
            book_end = bounds.get(book_n)
            if book_end is None:
                problems.append(f"{path.name}: book {book_n} is not in the manifest's book list")
                continue
            problems += validate_staging_book(book, book_end, gaps.get(book_n, []))
            books_by_n[book_n] = book

    if problems:
        raise ApparatusValidationError(problems)

    merged_books = []
    for n in sorted(books_by_n):
        book = dict(books_by_n[n])
        book["status"] = status
        merged_books.append(book)

    return {"work": work_id, "status": status, "books": merged_books}


def write_canonical(work_id: str, doc: dict) -> Path:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SCENES_DIR / f"{work_id}.json"
    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return out_path


# ── emit: canonical book entry -> bookData.apparatus (ReaderShell.astro shape) ─


def emit_book_apparatus(book: dict) -> dict:
    """Transform one merged scenes.json book entry into the exact shape
    app/src/components/ReaderShell.astro reads off bookData.apparatus:
    `interface BookApparatus { argument?: string; where?: string; who?: string[];
    day?: string; }` — `where` (a list in the authored schema) is joined into
    the single string the cartouche renders, and `days` (schema field name)
    becomes `day` (the field ReaderShell actually reads). `draft` is a single
    book-level flag (Apparatus honesty: the UI's discreet draft badge keys off
    it) plus `scenes[]` for the marginal scene chips, carried verbatim
    (lines/summary/location/dayNumber, per docs/APPARATUS-SCHEMAS.md)."""
    out: dict = {}
    if book.get("argument"):
        out["argument"] = book["argument"]
    where = book.get("where")
    if where:
        out["where"] = ", ".join(where)
    who = book.get("who")
    if who:
        out["who"] = list(who)
    if book.get("days"):
        out["day"] = book["days"]
    out["draft"] = book.get("status", "draft") == "draft"
    out["scenes"] = [
        {
            "lines": scene["lines"],
            "summary": scene["summary"],
            "location": scene["location"],
            "dayNumber": scene.get("dayNumber"),
        }
        for scene in book.get("scenes", [])
    ]
    return out


def run(manifest: Manifest, *, allow_partial: bool = False) -> dict:
    """The apparatus stage: merge staging -> canonical file, then emit each
    covered book's apparatus onto its already-emitted book-{n}.json under
    build/dist/<work>/. Safe to run standalone (re-emit without a full
    rebuild) as long as stage7 has already produced the book files; if a
    book's book-{n}.json doesn't exist yet, that book is reported as
    unemitted rather than crashing. Refuses to replace the canonical file
    with partial manifest coverage unless allow_partial is explicitly set."""
    work_id = manifest.work_id
    files = discover_staging(work_id)
    if not files:
        return {
            "work": work_id,
            "staging_files": [],
            "books_merged": 0,
            "books_emitted": [],
            "books_missing_emit_target": [],
            "books_without_staging": sorted(b["n"] for b in manifest.books),
        }

    doc = merge_staging(manifest)
    all_books = {b["n"] for b in manifest.books}
    covered = {b["book"] for b in doc["books"]}
    missing = sorted(all_books - covered)
    if missing and not allow_partial:
        raise ApparatusValidationError([
            f"{work_id}: staged scenes cover {len(covered)}/{len(all_books)} "
            f"manifest books; missing books: {missing}"
        ])
    write_canonical(work_id, doc)

    out_dir = BUILD_DIR / "dist" / work_id
    emitted, missing_target = [], []
    for book in doc["books"]:
        book_n = book["book"]
        book_path = out_dir / f"book-{book_n:02d}.json"
        if not book_path.exists():
            missing_target.append(book_n)
            continue
        book_doc = json.loads(book_path.read_text(encoding="utf-8"))
        book_doc["apparatus"] = emit_book_apparatus(book)
        book_path.write_text(json.dumps(book_doc, ensure_ascii=False), encoding="utf-8")
        emitted.append(book_n)

    return {
        "work": work_id,
        "staging_files": [p.name for p in files],
        "books_merged": len(doc["books"]),
        "books_emitted": emitted,
        "books_missing_emit_target": missing_target,
        "books_without_staging": missing,
    }
