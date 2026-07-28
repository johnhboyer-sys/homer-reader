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

Also emits build/dist/ngrams/summary.json — the guide page's ONLY source of
corpus numbers:

  { "works": [<work>, ...],
    "tokens": {"<work>": <token_count>, ..., "total": <sum>},
    "streams": {"<stream>": {"kept": <phrases kept>}, ...} }

`tokens` is read from each work's SERVED build/dist/<work>/search/offsets.json
(stage 7's output), not from this stage's own build/ngrams/<work>.json — the
guide page cites the number the site actually serves. Every figure the
/advanced page prints must trace to this file via a build-time read; a number
typed from a session goes stale silently (handoff §5 — this is the mistake
that shipped a phrase count 4x off in the sibling repo).

Three streams are indexed: `form` (the surface word as written), `lemma`, and
`english`. A position licensing several lemmas contributes EVERY reading, not a
chosen one — excluding a reading here would put it beyond the reach of any
later filter. The English stream does not come from stage 6's fold streams —
there is no such thing for a translation — it is tokenized straight out of
build/dist/<work>/book-*.json's segments[].english.text, after stage 7 has
written those files. Stage 8 must therefore run after stage 7 for every work;
scripts/build-public.mjs already sequences it that way (`all --work <work>`,
then `stage8`). Stage 8 also emits build/dist/ngrams/english-segments.json, the
English stream's offset -> citation map, the counterpart of the Greek
offsets.json the reader already fetches.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import BUILD_DIR

NS = (2, 3, 4, 5)
MIN_COUNT = 2
GREEK_STREAMS = ("form", "lemma")
# Tokenized separately from the Greek streams (see module docstring): the
# English stream comes from the emitted books, not stage 6's fold streams.
ENGLISH_STREAM = "english"
STREAMS = (*GREEK_STREAMS, ENGLISH_STREAM)
_ENGLISH_WORD = re.compile(r"[a-z']+")


def _shard_letter(phrase: str) -> str:
    """The phrase's fold-initial letter, or "_" for anything else.

    This holds only because stage 6 already emits fold-normalised (lower-case,
    diacritic-stripped) keys for `form` and `lemma`, and the English tokenizer
    below lower-cases its own output — this function does no folding of its
    own. If a future producer stopped pre-folding, phrases would silently pile
    into the "_" shard instead of failing, so the contract is asserted here
    rather than trusted.
    """
    first = phrase[0] if phrase else ""
    assert not first or first.isascii(), (
        f"stage8: {phrase!r} is not fold-normalised ASCII — the producer must "
        "fold before stage 8 shards, or every non-ASCII phrase silently lands "
        "in the '_' shard"
    )
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


def _book_starts(work: str, book_bounds: list, total: int) -> list[int]:
    """Book start offsets for `work`, or a loud failure.

    Homer's segments ARE books: an empty or missing book_bounds must never
    degrade to "the whole work is one book", because that would let a phrase
    span a real book edge (e.g. the last token of Iliad 1 into the first token
    of Iliad 2) — a hard build-time rule violation, not a shrug-and-continue.
    """
    if not book_bounds:
        raise ValueError(
            f"stage8: {work} has no book_bounds — refusing to treat the whole "
            "work as one book (that would let phrases span book edges)"
        )
    starts: list[int] = []
    for bound in book_bounds:
        start = bound.get("start") if isinstance(bound, dict) else bound
        if start is None:
            continue
        starts.append(int(start))
    if not starts:
        raise ValueError(f"stage8: {work} book_bounds contained no start offsets")
    if starts[0] != 0:
        starts = [0, *starts]
    if starts[-1] > total:
        raise ValueError(f"stage8: {work} book bounds extend past token_count")
    return starts


def _english_stream(work: str) -> tuple[list[list[str]], list[int], list[dict]]:
    """One work's English as a token stream, with the segment bounds it obeys.

    Ported verbatim from aristotle_pipeline.stage8_ngrams. There, English is
    aligned per Bekker column and several segments make up a book; for Homer a
    book *is* one segment (stage6_search's docstring: "Homer's segments are
    BOOKS"), so bounding by segment and bounding by book coincide here today.
    The segment-based bound is kept rather than hardcoding book edges, so this
    stays correct if a work is ever split into multiple English segments per
    book.

    Returns (stream, bounds, segments). `stream` is one list per position,
    matching the shape `_phrases` expects for the Greek streams — English
    carries a single reading, where the Greek lemma stream may carry several.
    `bounds` are the offsets a phrase may not cross. `segments` turns an offset
    back into a citation (book/column).

    Reads build/dist/<work>/book-*.json, which stage 7 writes — stage 8 must
    run after a full `all --work <work>` for every work, never before.
    """
    stream: list[list[str]] = []
    bounds: list[int] = []
    segments: list[dict] = []
    work_dir = BUILD_DIR / "dist" / work
    for book_path in sorted(work_dir.glob("book-*.json")):
        book = json.loads(book_path.read_text(encoding="utf-8"))
        for seg in book.get("segments", []):
            text = (seg.get("english") or {}).get("text") or ""
            words = _ENGLISH_WORD.findall(text.lower())
            if not words:
                continue
            bounds.append(len(stream))
            segments.append({
                "book": book.get("book"),
                "column": seg.get("column"),
                "base": len(stream),
                "words": len(words),
            })
            stream.extend([w] for w in words)
    return stream, bounds, segments


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
    # Offset -> citation for the English stream, the counterpart of the Greek
    # offsets.json the reader already fetches.
    english_segments: dict[str, list[dict]] = {}
    works: list[str] = []

    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        work = doc["work"]
        works.append(work)
        total = int(doc["token_count"])
        books = _book_starts(work, doc.get("book_bounds") or [], total)
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
            surface_lemmas[surface].update(v for v in lemma_values if v)

        for stream_name in GREEK_STREAMS:
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

        # English, from the emitted books rather than stage 6's fold streams
        # (see module docstring and `_english_stream`).
        eng_stream, eng_bounds, eng_segments = _english_stream(work)
        if eng_stream:
            english_segments[work] = eng_segments
            for options in eng_stream:
                unigrams[ENGLISH_STREAM][options[0]] += 1
                tokens[ENGLISH_STREAM] += 1
            for gram, at in _phrases(eng_stream, eng_bounds, len(eng_stream)):
                counts[ENGLISH_STREAM][gram] += 1
                offsets[ENGLISH_STREAM][gram][work].append(at)

    out_root = BUILD_DIR / "dist" / "ngrams"
    summary: dict = {"streams": {}}
    for stream_name in STREAMS:
        out_dir = out_root / stream_name
        occ_dir = out_dir / "occ"
        _clean_json_dir(out_dir)
        _clean_json_dir(occ_dir)

        kept = {gram: count for gram, count in counts[stream_name].items() if count >= MIN_COUNT}
        summary["streams"][stream_name] = {"kept": len(kept)}
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

    (out_root / "english-segments.json").write_text(
        json.dumps(english_segments, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    # Corpus token total, from the SERVED offsets.json per work (see module
    # docstring) — never from build/ngrams/<work>.json, which is an
    # intermediate the site does not serve.
    tokens_by_work: dict[str, int] = {}
    for work in sorted(set(works)):
        offsets_path = BUILD_DIR / "dist" / work / "search" / "offsets.json"
        if not offsets_path.exists():
            raise ValueError(
                f"stage8: no search/offsets.json for {work} — stage 7 must "
                "run for every work before stage 8 (module docstring)"
            )
        offsets_doc = json.loads(offsets_path.read_text(encoding="utf-8"))
        tokens_by_work[work] = int(offsets_doc["token_count"])
    summary["works"] = sorted(tokens_by_work)
    summary["tokens"] = {**tokens_by_work, "total": sum(tokens_by_work.values())}
    (out_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True),
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
