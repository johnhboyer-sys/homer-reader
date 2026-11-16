"""Count Homer search hits under each candidate counting unit.

For John's ruling on Homer's counting unit (the port of aristotle-reader's new
search, which counts chapters). Reads the built corpus (build/dist) directly;
no site needed.

Units:
  line    one verse line (Greek only: Murray's English marks every 5th line,
          so an English hit can be placed only within a five-line run)
  run5    the five-line run between two of Murray's line marks
  para    one of Murray's English paragraphs (the Greek has none); its Greek
          lines start at the line mark before the paragraph break, so its
          edges are right to within five lines
  scene   the reader's scenes (apparatus/scenes)
  speech  a top-level speech (DICES, level 0); hits outside any speech are
          counted as narrative, not as a unit
  book    the 48 books (what Homer's search groups by, and what its "and"
          means today: one search segment per book)

Greek hits are lemma postings from search/greek_lemma.json; English hits are
whole-word, case-blind matches in the main translation (Murray), the text the
site's English search reads.

Usage: python3 docs/search-port/unit-counts.py [build/dist] > out.json
"""
from __future__ import annotations

import bisect
import json
import re
import statistics
import sys
from pathlib import Path

DIST = Path(sys.argv[1] if len(sys.argv) > 1 else "build/dist")
WORKS = ["iliad", "odyssey"]
SEARCHES = [
    {"name": "μῆνις (Greek only)", "lemma": ["mhnis"], "english": None},
    {"name": "θάλασσα + sea", "lemma": ["qalassa"], "english": "sea"},
    {"name": "δάκρυον + tears", "lemma": ["dakruon"], "english": "tears"},
]


def load(path: Path):
    return json.loads(path.read_text())


def book_data(work: str):
    """Per book: lines, Murray text + line marks + paragraph offsets, scenes."""
    books = {}
    for f in sorted((DIST / work).glob("book-*.json")):
        b = load(f)
        seg = b["segments"]
        assert len(seg) == 1, f"{f}: expected one segment per book"
        s = seg[0]
        lines = [g["n"] for g in s["greek"]]
        eng = s["english"]
        marks = sorted((m["offset"], m["n"]) for m in eng["bekker"])
        paras = [0] + sorted(m["offset"] for m in eng["markers"] if m["kind"] == "paragraph")
        books[b["book"]] = {
            "lines": lines,
            "text": eng["text"],
            "mark_offsets": [o for o, _ in marks],
            "mark_lines": [n for _, n in marks],
            "para_offsets": paras,
            "scenes": [tuple(sc["lines"]) for sc in b["apparatus"]["scenes"]],
        }
    return books


def line_of_offset(bk, off):
    """The line mark at or before an English offset (a five-line run start)."""
    i = bisect.bisect_right(bk["mark_offsets"], off) - 1
    return bk["mark_lines"][max(i, 0)]


def run_of_line(bk, line):
    i = bisect.bisect_right(bk["mark_lines"], line) - 1
    return bk["mark_lines"][max(i, 0)]


def para_starts(bk):
    return [line_of_offset(bk, o) for o in bk["para_offsets"]]


def para_of_line(bk, line):
    starts = para_starts(bk)
    return bisect.bisect_right(starts, line) - 1


def para_of_offset(bk, off):
    return bisect.bisect_right(bk["para_offsets"], off) - 1


def scene_of_line(bk, line):
    for i, (a, b) in enumerate(bk["scenes"]):
        if a <= line <= b:
            return i
    return None


def speech_index(work):
    sp = load(DIST / work / "speeches.json")["speeches"]
    top = [s for s in sp if s.get("level", 0) == 0]
    by_book = {}
    for s in top:
        by_book.setdefault(s["book"], []).append((s["lines"][0], s["lines"][1], s["id"]))
    return top, by_book


def speech_of_line(by_book, book, line):
    for a, b, sid in by_book.get(book, []):
        if a <= line <= b:
            return sid
    return None


def greek_hits(work, keys):
    lem = load(DIST / work / "search" / "greek_lemma.json")
    offs = load(DIST / work / "search" / "offsets.json")["segments"]
    hits = []
    for key in keys:
        for si, pos in lem.get(key, []):
            seg = offs[si]
            n = 0
            for line, count in seg["line_runs"]:
                if pos < n + count:
                    hits.append((seg["book"], line))
                    break
                n += count
            else:
                raise ValueError(f"{work} {key}: position {pos} past segment {si}")
    return hits


def english_hits(books, word):
    pat = re.compile(rf"(?<!\w){re.escape(word)}(?!\w)", re.IGNORECASE)
    return [(bn, m.start()) for bn, bk in books.items() for m in pat.finditer(bk["text"])]


def stats(lengths):
    return {
        "units": len(lengths),
        "mean": round(statistics.mean(lengths), 1),
        "median": statistics.median(lengths),
        "min": min(lengths),
        "max": max(lengths),
    }


def main():
    data = {w: book_data(w) for w in WORKS}
    speeches = {w: speech_index(w) for w in WORKS}

    # How long each unit runs, in Greek lines.
    lengths = {"line": [], "run5": [], "para": [], "scene": [], "speech": [], "book": []}
    in_speech = total_lines = 0
    for w in WORKS:
        top, by_book = speeches[w]
        for bn, bk in data[w].items():
            lines = bk["lines"]
            total_lines += len(lines)
            lengths["line"] += [1] * len(lines)
            lengths["book"].append(len(lines))
            ml = bk["mark_lines"] + [lines[-1] + 1]
            lengths["run5"] += [b - a for a, b in zip(ml, ml[1:]) if b > a]
            ps = para_starts(bk) + [lines[-1] + 1]
            lengths["para"] += [b - a for a, b in zip(ps, ps[1:]) if b > a]
            lengths["scene"] += [b - a + 1 for a, b in bk["scenes"]]
            for line in lines:
                if speech_of_line(by_book, bn, line):
                    in_speech += 1
        lengths["speech"] += [s["lines"][1] - s["lines"][0] + 1 for s in top]

    out = {
        "unit_lengths_in_lines": {k: stats(v) for k, v in lengths.items()},
        "lines_total": total_lines,
        "lines_inside_a_top_level_speech": in_speech,
        "searches": [],
    }

    def keyed(key, part):
        # A hit outside every unit of this kind (narrative, for speeches) has no key.
        return None if part is None else (*key, part)

    for s in SEARCHES:
        # One unit key per hit, per unit kind (None = outside every unit).
        g_keys = {u: [] for u in lengths}
        e_keys = {u: [] for u in lengths if u != "line"}
        for w in WORKS:
            books = data[w]
            _, by_book = speeches[w]
            for bn, line in greek_hits(w, s["lemma"]):
                bk = books[bn]
                g_keys["line"].append((w, bn, line))
                g_keys["run5"].append((w, bn, run_of_line(bk, line)))
                g_keys["para"].append((w, bn, para_of_line(bk, line)))
                g_keys["scene"].append(keyed((w, bn), scene_of_line(bk, line)))
                g_keys["speech"].append(speech_of_line(by_book, bn, line))
                g_keys["book"].append((w, bn))
            if s["english"]:
                for bn, off in english_hits(books, s["english"]):
                    bk = books[bn]
                    line = line_of_offset(bk, off)
                    e_keys["run5"].append((w, bn, line))
                    e_keys["para"].append((w, bn, para_of_offset(bk, off)))
                    e_keys["scene"].append(keyed((w, bn), scene_of_line(bk, line)))
                    e_keys["speech"].append(speech_of_line(by_book, bn, line))
                    e_keys["book"].append((w, bn))
        row = {"name": s["name"], "greek_hits": len(g_keys["book"]),
               "greek_hits_in_narrative": g_keys["speech"].count(None), "units": {}}
        if s["english"]:
            row["english_hits"] = len(e_keys["book"])
            row["english_hits_in_narrative"] = e_keys["speech"].count(None)
        for u in lengths:
            g = {k for k in g_keys[u] if k is not None}
            cell = {"greek": len(g), "greek_hits_outside": g_keys[u].count(None)}
            if s["english"] and u in e_keys:
                e = {k for k in e_keys[u] if k is not None}
                both = g & e
                cell.update({"english": len(e), "both": len(both), "either": len(g | e),
                             "greek_only": len(g - e), "english_only": len(e - g),
                             "english_hits_outside": e_keys[u].count(None),
                             # The bar under Aristotle's model: in "and", the
                             # hits are the Greek words inside the matching units.
                             "greek_hits_in_both": sum(k in both for k in g_keys[u])})
            row["units"][u] = cell
        out["searches"].append(row)

    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
