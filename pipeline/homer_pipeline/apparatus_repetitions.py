"""Computed apparatus stage (Phase 4d, docs/APPARATUS-SCHEMAS.md):
repetitions.json -- exact repeated whole lines and long word-sequences,
cross-epic (single output, not per-work).

Emits build/dist/repetitions.json: a JSON array of
`{key, text, count, refs: [{work, book, line}]}`. Fully mechanical exact-text
n-gram counting -- no authored content.

Matching is on exact SURFACE TEXT, not lemma (contrast apparatus_epithets,
which is lemma-based): whitespace is normalized (collapsed, stripped) but
Greek accents/breathings/elisions are kept exactly as printed, per
docs/APPARATUS-SCHEMAS.md.

Two categories, unified into one n-gram scan per line:
  - whole-line repeats: a line's full word sequence, at ANY length, is a
    candidate whenever the identical sequence occurs elsewhere (same work or
    the other epic).
  - partial n-gram repeats: any contiguous run of MIN_NGRAM_LEN+ words within
    a line that recurs elsewhere, whether or not either occurrence is a
    whole-line match.
n-grams never cross line boundaries -- the corpus's formulaic/rhapsodic
repetition is a within-line phenomenon here; concatenating across lines
would be a different, unrequested analysis.

Maximal-n-gram rule (explosion control, the same rule apparatus_epithets
uses for formulas): a candidate sequence is DROPPED when a strictly longer
candidate exists that (a) contains it as a contiguous sub-sequence and (b)
has the IDENTICAL set of {work, book, line} refs -- i.e. it adds no
information beyond the longer entry. A shorter candidate whose ref set
differs from every longer super-sequence (even a subset) is kept
independently, since it represents a genuinely broader recurring phrase.

Determinism: the only per-run-varying Python feature touched here is `set`
iteration order (hash-seed-dependent in CPython); every set is used solely
for O(1) ref-set-equality tests, never iterated to produce output order (see
the stage's determinism test).
"""

from __future__ import annotations

import json
from collections import defaultdict

from .config import BUILD_DIR, REPO_ROOT, Manifest

MANIFESTS_DIR = REPO_ROOT / "manifests"

MIN_NGRAM_LEN = 4
MIN_COUNT = 2

Ref = tuple[str, int, int]  # (work, book, line)


def discover_work_ids() -> list[str]:
    """Work ids from every manifests/*.yaml, in filename order."""
    return [Manifest.load(path).work_id for path in sorted(MANIFESTS_DIR.glob("*.yaml"))]


def _load_lines(work_id: str) -> list[tuple[str, int, int, str]]:
    """[(work, book, line, normalized_text)] for every line under
    build/dist/<work_id>/book-*.json. Silently empty (not a crash) if the
    work hasn't been through stage7 yet -- lets this stage be re-run as more
    works come online without special-casing missing dist dirs."""
    out = []
    dist_dir = BUILD_DIR / "dist" / work_id
    for path in sorted(dist_dir.glob("book-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        book_n = doc["book"]
        for seg in doc["segments"]:
            for line in seg["greek"]:
                text = " ".join(line["text"].split())
                out.append((work_id, book_n, line["n"], text))
    return out


def _is_contiguous_subsequence(short: tuple, long: tuple) -> bool:
    ls, ll = len(short), len(long)
    if ls >= ll:
        return short == long and ls == ll
    return any(long[i:i + ls] == short for i in range(ll - ls + 1))


def find_repetitions(lines: list[tuple[str, int, int, str]]) -> list[dict]:
    """Core, testable n-gram mining over pre-extracted (work, book, line,
    text) rows -- run() just wires this to the real corpus."""
    by_words: dict[tuple[str, ...], list[Ref]] = defaultdict(list)
    for work, book_n, line_n, text in lines:
        words = tuple(text.split())
        length = len(words)
        if length == 0:
            continue
        lengths = {length} | set(range(MIN_NGRAM_LEN, length + 1))
        for n in lengths:
            for start in range(0, length - n + 1):
                gram = words[start:start + n]
                by_words[gram].append((work, book_n, line_n))

    candidates = {gram: refs for gram, refs in by_words.items() if len(refs) >= MIN_COUNT}

    # Domination only ever fires between candidates sharing the IDENTICAL
    # ref set (see module docstring), so bucketing already-accepted grams by
    # their ref set turns the pruning pass from O(candidates^2) into O(one
    # small-bucket scan per candidate) -- the exact same result, just not
    # re-checked against every unrelated accepted gram.
    accepted: list[tuple[tuple[str, ...], list[Ref]]] = []
    accepted_by_refset: dict[frozenset[Ref], list[tuple[str, ...]]] = defaultdict(list)
    for gram in sorted(candidates, key=lambda g: (-len(g), g)):
        refs = candidates[gram]
        rs = frozenset(refs)
        dominated = any(
            _is_contiguous_subsequence(gram, acc_gram)
            for acc_gram in accepted_by_refset.get(rs, ())
        )
        if not dominated:
            accepted.append((gram, refs))
            accepted_by_refset[rs].append(gram)

    out = []
    for gram, refs in accepted:
        text = " ".join(gram)
        out.append(
            {
                "key": text,
                "text": text,
                "count": len(refs),
                "refs": [{"work": w, "book": b, "line": l} for w, b, l in refs],
            }
        )
    out.sort(key=lambda e: (-e["count"], e["text"]))
    return out


def run() -> dict:
    work_ids = discover_work_ids()
    lines: list[tuple[str, int, int, str]] = []
    for work_id in work_ids:
        lines.extend(_load_lines(work_id))

    repetitions = find_repetitions(lines)

    out_path = BUILD_DIR / "dist" / "repetitions.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(repetitions, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return {
        "works": work_ids,
        "lines_scanned": len(lines),
        "repetitions": len(repetitions),
        "path": out_path,
    }
