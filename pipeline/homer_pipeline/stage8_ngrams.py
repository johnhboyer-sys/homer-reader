"""Stage 8: recurrent phrases across the whole corpus.

The pipeline's first CROSS-WORK stage. Every other stage builds one manifest per
invocation, but a phrase that appears once in the Iliad and once in the Odyssey
recurs in Homer and is exactly the kind a reader wants; deciding that needs all
the works at once. Stage 6 leaves each work's fold streams in
build/ngrams/<work>.json; this merges them.

Sharded by the phrase's fold-initial letter — the pattern the LSJ and the lemma
picker already use — and split again by what a reader actually needs when. The
browse list needs every phrase; only an EXPANDED phrase needs its offsets, and
keeping the two together made one shard 10.4 MB, which defeats the point of
sharding at all.

  build/dist/ngrams/<stream>/<letter>.json          the browse list
      { "<fold phrase>": [n, count, score, works] }

  build/dist/ngrams/<stream>/occ/<letter>-<n>.json  fetched on expand
      { "<fold phrase>": { "iliad": [1204, 88, 310], "odyssey": [90211] } }

Occurrences are per-work global offsets, delta-encoded after the first. The
work map doubles as the per-work breakdown, so a reader can be told "37 times
across 2 works" from the browse list alone, without loading a single offset.

Rules, none of them re-derived here:
  * A phrase never spans a BOOK edge. Book bounds come from the same
    offsets.json the search uses.
  * A phrase never spans a token no index can key (a stage 3 key failure).
  * A phrase is kept only if it occurs at least twice CORPUS-WIDE.
  * Cross-line straddling is NOT filtered at build time. It is a query-time
    toggle defaulting to keep, and dropping the occurrences here would make the
    toggle unimplementable. The client uses line_runs from offsets.json later
    to decide whether a hit stays within one verse.

Also emits build/dist/lemma-map/<letter>.json — fold(surface) -> the headwords
that surface can belong to. Not an n-gram artifact, but it needs the same
corpus-wide pass, and it is what lets a typed phrase be widened to its inflected
variants without the reader knowing any headwords.

Both streams are indexed: `form` (the surface word as written) and `lemma`. A
position licensing several lemmas contributes EVERY reading, not a chosen one —
excluding a reading here would put it beyond the reach of any later filter.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .config import BUILD_DIR

NS = (2, 3, 4, 5)
MIN_COUNT = 2
STREAMS = ("form", "lemma")


def _shard_letter(phrase: str) -> str:
    first = phrase[0] if phrase else ""
    return first if "a" <= first <= "z" else "_"


def _readings(entry, limit: int = 0):
    """Every phrase a window of positions licenses, not a chosen one."""
    combos = [[]]
    for options in entry:
        unique = []
        for option in options:
            if option not in unique:
                unique.append(option)
        combos = [c + [o] for c in combos for o in unique]
        if limit and len(combos) > limit:
            return combos[:limit]
    return combos


def _phrases(stream: list, books: list[int], total: int):
    """Yield (gram, offset) for every n-gram that respects the boundaries."""
    edges = books + [total]
    for b in range(len(edges) - 1):
        lo, hi = edges[b], edges[b + 1]
        for n in NS:
            for i in range(lo, hi - n + 1):
                window = stream[i:i + n]
                if any(o is None for o in window):
                    continue
                for reading in _readings(window):
                    yield " ".join(reading), i


def _stream_options(raw: list) -> list:
    out = []
    for entry in raw:
        if entry is None:
            out.append(None)
        elif isinstance(entry, str):
            out.append([entry] if entry else None)
        else:
            values = []
            for value in entry:
                if value and value not in values:
                    values.append(value)
            out.append(values or None)
    return out


def _book_starts(book_bounds: list, total: int) -> list[int]:
    starts: list[int] = []
    for bound in book_bounds:
        start = bound.get("start") if isinstance(bound, dict) else bound
        if start is None:
            continue
        starts.append(int(start))
    if not starts:
        starts = [0]
    elif starts[0] != 0:
        starts = [0, *starts]
    if starts[-1] > total:
        raise ValueError("stage8: book bounds extend past token_count")
    return starts


def _clean_json_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for existing in path.glob("*.json"):
        existing.unlink()


def run() -> Path:
    source = BUILD_DIR / "ngrams"
    files = sorted(source.glob("*.json"))
    if not files:
        raise ValueError(
            "stage8: no per-work streams in build/ngrams — run stage6 for every work first"
        )

    surface_lemmas: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, Counter] = {s: Counter() for s in STREAMS}
    offsets: dict[str, dict[str, dict[str, list[int]]]] = {
        s: defaultdict(lambda: defaultdict(list)) for s in STREAMS
    }
    unigrams: dict[str, Counter] = {s: Counter() for s in STREAMS}
    tokens: dict[str, int] = {s: 0 for s in STREAMS}

    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        work = doc["work"]
        total = int(doc["token_count"])
        books = _book_starts(doc.get("book_bounds") or [], total)
        if len(doc.get("form") or []) != total or len(doc.get("lemma") or []) != total:
            raise ValueError(
                f"stage8: {work} stream length disagrees with token_count={total}"
            )

        form_raw = doc["form"]
        lemma_raw = doc["lemma"]
        for surface, lemmas in zip(form_raw, lemma_raw):
            if not surface or not lemmas:
                continue
            lemma_values = [lemmas] if isinstance(lemmas, str) else lemmas
            surface_lemmas[surface].update(lemma_values)

        for stream_name in STREAMS:
            raw = doc[stream_name]
            stream = _stream_options(raw)
            for options in stream:
                if not options:
                    continue
                for token in options:
                    unigrams[stream_name][token] += 1
                    tokens[stream_name] += 1
            for gram, at in _phrases(stream, books, total):
                counts[stream_name][gram] += 1
                offsets[stream_name][gram][work].append(at)

    out_root = BUILD_DIR / "dist" / "ngrams"
    for stream_name in STREAMS:
        out_dir = out_root / stream_name
        occ_dir = out_dir / "occ"
        _clean_json_dir(out_dir)
        _clean_json_dir(occ_dir)

        kept = {gram: count for gram, count in counts[stream_name].items() if count >= MIN_COUNT}
        shards: dict[str, dict] = defaultdict(dict)
        occ_shards: dict[tuple[str, int], dict] = defaultdict(dict)
        total_tokens = tokens[stream_name]
        for gram in sorted(kept):
            count = kept[gram]
            words = gram.split(" ")
            expected = total_tokens
            for word in words:
                expected *= unigrams[stream_name][word] / total_tokens
            score = count * math.log2(count / expected) if expected > 0 else 0.0
            per_work: dict[str, list[int]] = {}
            for work, at in offsets[stream_name][gram].items():
                at.sort()
                per_work[work] = [at[0]] + [at[i] - at[i - 1] for i in range(1, len(at))]
            letter = _shard_letter(gram)
            n = len(words)
            shards[letter][gram] = [n, count, round(score, 1), len(per_work)]
            occ_shards[(letter, n)][gram] = per_work

        for letter in sorted(shards):
            (out_dir / f"{letter}.json").write_text(
                json.dumps(shards[letter], ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
        for (letter, n) in sorted(occ_shards):
            (occ_dir / f"{letter}-{n}.json").write_text(
                json.dumps(occ_shards[(letter, n)], ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )

    map_dir = BUILD_DIR / "dist" / "lemma-map"
    _clean_json_dir(map_dir)
    map_shards: dict[str, dict] = defaultdict(dict)
    for surface in sorted(surface_lemmas):
        map_shards[_shard_letter(surface)][surface] = sorted(surface_lemmas[surface])
    for letter in sorted(map_shards):
        (map_dir / f"{letter}.json").write_text(
            json.dumps(map_shards[letter], ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

    return out_root
