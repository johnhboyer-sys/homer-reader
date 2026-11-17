"""Where each scene starts in each translation's words: search/eng-chapters.json.

The ported search (aristotle-reader 7ddd67b7ef, shared/lib/chapter-pages.ts
chapterPlaces) puts an English hit in its chapter from this file alone:
{slot: {seg_idx: [[word_pos, chapter], ...]}}, a word belonging to the last
chapter whose start is at or before it. Homer's chapters are its scenes, and
the word positions are counted exactly as the slot's English index counts
them (stage6_search.english_words).

The split follows the reader's own scene pages. app/scripts/build-scene-pages.mjs
runs the reader's paging code (shared/lib/scene-paging.ts) over every book and
translation and writes, per scene, the character spans of the translation's
text that the scene's page shows (build/scene-pages/<work>.json). Here each
word goes to the page that shows its first letter. Where two pages show it (the
reader's hollow-page backstop repeats a little text) or none does (a stretch
the reader's line groups leave out), it goes to the scene whose lines hold the
word's estimated line: interpolated by character offset between the
translation's two surrounding line marks. A book the reader cannot page in a
translation (fewer than two marks: it shows the whole book at once) has every
word placed that way, and the summary names the book.

Usage (after build-scene-pages.mjs):
    python -m homer_pipeline.search_scenes <build/dist> <build/scene-pages>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .stage6_search import english_word_starts, segment_pieces


def estimated_line(marks: list[dict], c: int, *, first_line: int, last_line: int,
                   text_len: int) -> float:
    """The Greek line a character offset of a translation stands at,
    interpolated between the marks on either side of it. The text's start
    stands for the book's first line and its end for the last line. With fewer
    than two marks there is nothing to interpolate: the one mark's line (or
    the first line) is every offset's line."""
    pts = sorted((m["offset"], m["n"]) for m in marks)
    if len(pts) < 2:
        return pts[0][1] if pts else first_line
    if pts[0][0] > 0:
        pts.insert(0, (0, first_line))
    if pts[-1][0] < text_len:
        pts.append((text_len, last_line))
    before = after = None
    for off, n in pts:
        if off <= c:
            before = (off, n)
        elif after is None:
            after = (off, n)
    if before is None:
        return pts[0][1]
    if after is None:
        return before[1]
    return before[1] + (c - before[0]) * (after[1] - before[1]) / (after[0] - before[0])


def _scene_of_line(scenes: list[tuple[int, int]], line: float, among=None) -> int:
    """The scene whose lines hold `line` (scene a-b holds a <= line < b + 1),
    or, failing that, the nearest one; only scenes in `among` when given."""
    cands = range(len(scenes)) if among is None else among

    def dist(j: int) -> float:
        a, b = scenes[j]
        if a <= line < b + 1:
            return 0.0
        return min(abs(line - a), abs(line - (b + 1)))

    return min(cands, key=lambda j: (dist(j), j))


def place_words(
    starts: list[int],
    pages: list[list[list[int]]] | None,
    scenes: list[tuple[int, int]],
    marks: list[dict],
    text_len: int,
    first_line: int,
    last_line: int,
) -> tuple[list[int], dict[str, int]]:
    """The scene index of each word, given each word's first character.

    `pages[j]` lists the [start, end) character spans scene j's page shows,
    or `pages` is None when the reader does not page this text. A word never
    goes back to an earlier scene than the word before it: where the rules
    above would send it back, it stays, and `backwards` counts it.
    """
    stats = {"words": len(starts), "on_two_pages": 0, "on_no_page": 0, "backwards": 0}
    placed: list[int] = []
    prev = 0
    for c in starts:
        covering = [] if pages is None else [
            j for j, spans in enumerate(pages) if any(s <= c < e for s, e in spans)
        ]
        if len(covering) == 1:
            j = covering[0]
        else:
            line = estimated_line(marks, c, first_line=first_line, last_line=last_line,
                                  text_len=text_len)
            if covering:
                stats["on_two_pages"] += 1
                j = _scene_of_line(scenes, line, covering)
            else:
                stats["on_no_page"] += 1
                j = _scene_of_line(scenes, line)
        if j < prev:
            stats["backwards"] += 1
            j = prev
        placed.append(j)
        prev = j
    return placed, stats


def _slot_texts(seg: dict) -> dict[str, tuple[str, list[dict]]]:
    """Each translation's text in one segment and its line marks, by slot."""
    out: dict[str, tuple[str, list[dict]]] = {}
    eng = seg.get("english") or {}
    if eng.get("text"):
        out["english"] = (eng["text"], eng.get("bekker") or [])
    for slot, pieces in segment_pieces(seg).items():
        if len(pieces) != 1:
            raise ValueError(
                f"segment {seg['id']}: {slot} has {len(pieces)} pieces; a Homer book "
                "carries one, and the reader's pages are worked out for one"
            )
        out[slot] = (pieces[0].get("text") or "", pieces[0].get("bekker") or [])
    return out


def emit_eng_chapters(work_dir: Path, scene_pages: dict) -> dict[str, dict]:
    """Write search/eng-chapters.json for one work from its emitted books,
    search/meta.json and the reader's scene pages. Returns a summary per slot.
    """
    search_dir = work_dir / "search"
    meta = json.loads((search_dir / "meta.json").read_text(encoding="utf-8"))
    seg_idx = {m["id"]: i for i, m in enumerate(meta)}
    chapters: dict[str, dict[str, list]] = {}
    summary: dict[str, dict] = {}
    for book_path in sorted(work_dir.glob("book-*.json")):
        doc = json.loads(book_path.read_text(encoding="utf-8"))
        book = doc["book"]
        if len(doc["segments"]) != 1:
            raise ValueError(f"{book_path.name}: expected one segment per book")
        seg = doc["segments"][0]
        scenes = [tuple(s["lines"]) for s in (doc.get("apparatus") or {}).get("scenes") or []]
        names = [f"{a}-{b}" for a, b in scenes]
        paged = scene_pages["books"].get(str(book))
        if not scenes or paged is None or paged["scenes"] != names:
            raise ValueError(
                f"{book_path.name}: the scene pages were worked out for other scenes "
                f"({None if paged is None else paged['scenes']} against {names}); "
                "rerun app/scripts/build-scene-pages.mjs"
            )
        by_slot = {t["slot"]: t for t in paged["translations"].values()}
        si = seg_idx.get(seg["id"])
        if si is None:
            raise ValueError(f"{book_path.name}: segment {seg['id']} is not in search/meta.json")
        lines = [line["n"] for line in seg.get("greek") or []]
        for slot, (text, marks) in _slot_texts(seg).items():
            t = by_slot.get(slot)
            if t is None:
                raise ValueError(f"{book_path.name}: no scene pages for the {slot} translation")
            starts = english_word_starts(text)
            pages = t["pages"] if t["anchored"] else None
            if pages is not None and len(pages) != len(scenes):
                raise ValueError(f"{book_path.name}: {slot}: {len(pages)} pages for {len(scenes)} scenes")
            placed, stats = place_words(starts, pages, scenes, marks, len(text),
                                        lines[0] if lines else scenes[0][0],
                                        lines[-1] if lines else scenes[-1][1])
            out: list[list] = []
            for word, j in enumerate(placed):
                if not out or out[-1][1] != names[j]:
                    out.append([word, names[j]])
            if out:
                chapters.setdefault(slot, {})[str(si)] = out
            s = summary.setdefault(slot, {"words": 0, "on_two_pages": 0, "on_no_page": 0,
                                          "backwards": 0, "scenes_without_words": 0,
                                          "unpaged_books": []})
            for k in ("words", "on_two_pages", "on_no_page", "backwards"):
                s[k] += stats[k]
            s["scenes_without_words"] += len(scenes) - len(out)
            if pages is None:
                s["unpaged_books"].append(book)
    (search_dir / "eng-chapters.json").write_text(
        json.dumps(chapters, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python -m homer_pipeline.search_scenes <build/dist> <build/scene-pages>",
              file=sys.stderr)
        return 2
    dist, pages_dir = Path(argv[0]), Path(argv[1])
    files = sorted(pages_dir.glob("*.json"))
    if not files:
        print(f"no scene pages in {pages_dir}; run app/scripts/build-scene-pages.mjs", file=sys.stderr)
        return 1
    for f in files:
        pages = json.loads(f.read_text(encoding="utf-8"))
        summary = emit_eng_chapters(dist / pages["work"], pages)
        for slot, s in sorted(summary.items()):
            print(f"eng-chapters {pages['work']} {slot}: " + " ".join(f"{k}={v}" for k, v in s.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
