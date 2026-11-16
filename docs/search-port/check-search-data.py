"""Check the search data lane A builds (docs/search-port/PLAN.md), from build/dist.

Prints, and fails (exit 1) when an expected number does not hold:

- per work, the scene bounds in search/offsets.json (790 in all, the scene
  count unit-counts.py uses), and whether each bound's token offset maps back,
  through line_runs, to its scene's first line;
- θάλασσα (lemma qalassa): the distinct scenes its Greek hits fall in, placed
  as the client's chapterPlaces does (the last bound at or before the hit's
  global offset) — 94, unit-counts.py's scene "greek" count;
- "sea" in Murray: the hits in search/english.json (398, the site's count) and
  the distinct scenes they fall in through search/eng-chapters.json, beside
  unit-counts.py's 225 (which places a word by the line mark before it, not by
  the reader's pages, so a small gap is expected);
- the lemma picker (lemma-picker/<letter>.json): every fold key of both
  works' greek_lemma.json is listed, with the count of its postings.

Usage: python3 docs/search-port/check-search-data.py [build/dist]
"""
from __future__ import annotations

import bisect
import json
import subprocess
import sys
from pathlib import Path

DIST = Path(sys.argv[1] if len(sys.argv) > 1 else "build/dist")
WORKS = ["iliad", "odyssey"]
EXPECT = {"scenes": 790, "qalassa_scenes": 94, "sea_hits": 398, "sea_scenes_unit_counts": 225}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ok = True
    total_bounds = 0
    grk_scenes: set = set()
    sea_hits = 0
    sea_scenes: set = set()
    postings: dict[str, int] = {}
    for work in WORKS:
        search = DIST / work / "search"
        offsets = load(search / "offsets.json")
        base = offsets["seg_base_offset"]
        segs = offsets["segments"]
        bounds = offsets["chapter_bounds"]
        total_bounds += len(bounds)
        by_book: dict[int, list[dict]] = {}
        for b in bounds:
            by_book.setdefault(b["book"], []).append(b)
        seg_of_book = {s["book"]: i for i, s in enumerate(segs)}

        # Each bound maps back to its scene's first line.
        bad = []
        for b in bounds:
            si = seg_of_book[b["book"]]
            local = b["start"] - base[si]
            line = None
            for n, count in segs[si]["line_runs"]:
                if local < count:
                    line = n
                    break
                local -= count
            if str(line) != b["chapter"].split("-")[0]:
                bad.append((b["book"], b["chapter"], line))
        print(f"{work}: scene bounds {len(bounds)}; mapping back to the scene's first line: "
              f"{len(bounds) - len(bad)} of {len(bounds)}" + (f"; wrong: {bad[:5]}" if bad else ""))
        ok &= not bad

        starts = {bk: [b["start"] for b in bs] for bk, bs in by_book.items()}
        names = {bk: [b["chapter"] for b in bs] for bk, bs in by_book.items()}

        def chapter_of(book: int, g: int) -> str:
            i = max(bisect.bisect_right(starts[book], g) - 1, 0)
            return names[book][i]

        # θάλασσα: Greek hits by scene.
        lemma = load(search / "greek_lemma.json")
        for key, posts in lemma.items():
            postings[key] = postings.get(key, 0) + len(posts)
        for si, pos in lemma.get("qalassa", []):
            book = segs[si]["book"]
            grk_scenes.add((work, book, chapter_of(book, base[si] + pos)))

        # "sea" in Murray: hits and scenes through eng-chapters.
        english = load(search / "english.json")
        eng = load(search / "eng-chapters.json")["english"]
        for si, pos in english.get("sea", []):
            sea_hits += 1
            book = segs[si]["book"]
            chapter = None
            for word, name in eng.get(str(si), []):
                if word <= pos:
                    chapter = name
            # Before the first start, the chapter the Greek opens in.
            sea_scenes.add((work, book, chapter or chapter_of(book, base[si])))

    unit = json.loads(subprocess.run(
        [sys.executable, str(Path(__file__).with_name("unit-counts.py")), str(DIST)],
        check=True, capture_output=True, text=True).stdout)
    row = next(s for s in unit["searches"] if s["name"].startswith("θάλασσα"))
    scene = row["units"]["scene"]

    def line(label: str, got, want) -> bool:
        print(f"{label}: {got} (expected {want}) {'OK' if got == want else 'FAIL'}")
        return got == want

    ok &= line("scene bounds, both works", total_bounds, EXPECT["scenes"])
    ok &= line("θάλασσα: scenes with a Greek hit", len(grk_scenes), scene["greek"])
    ok &= line("θάλασσα: scenes, against the plan's number", len(grk_scenes), EXPECT["qalassa_scenes"])
    ok &= line("sea (Murray): hits in english.json", sea_hits, EXPECT["sea_hits"])
    ok &= line("sea (Murray): hits unit-counts.py finds", row["english_hits"], EXPECT["sea_hits"])
    print(f"sea (Murray): scenes through eng-chapters.json: {len(sea_scenes)}; "
          f"unit-counts.py (line mark before the word): {scene['english']} "
          f"(difference {len(sea_scenes) - scene['english']:+d})")

    picker: dict = {}
    for shard in sorted((DIST / "lemma-picker").glob("*.json")):
        picker.update(load(shard))
    wrong = [k for k, n in postings.items() if picker.get(k, {}).get("n") != n]
    print(f"lemma picker: {len(picker)} fold keys; index keys missing or miscounted: {len(wrong)}"
          + (f" {wrong[:5]}" if wrong else "") + f"; qalassa: {json.dumps(picker.get('qalassa'), ensure_ascii=False)}")
    ok &= not wrong and len(picker) > 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
