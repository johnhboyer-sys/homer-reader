"""Computed apparatus stage: per-book vocabulary lists ("words to know
before Book N", the Perseus vocab-list pattern), computed fresh from our own
lemma data -- no hand-curated word lists.

Emits build/dist/<work>/vocab.json:
    {"status": "draft", "books": {"<book>": [
        {"lemma": <Beta Code lemma>, "count": <in-book occurrences>,
         "gloss": <short English, OMITTED when none was found>},
        ...  (up to MAX_ENTRIES_PER_BOOK, ranked by in-book frequency)
    ], ...}}
`lemma` is the Beta Code form already used corpus-wide for cross-referencing
(see apparatus_epithets.json's `lemmaKeys`) -- the reader's existing
shared/lib/betacode.ts converts it to Greek for display; this stage does not
duplicate that conversion. `status: "draft"` per CLAUDE.md's apparatus-
honesty rule: the ranking is mechanical, but the gloss join is a heuristic
lemma-level lookup, not philologically reviewed.

Gloss source (design decision)
-------------------------------
Three candidate sources were inspected before writing this stage:

  - Cunliffe (sources/cunliffe/*.jsonl, ~11.4k entries, near-complete corpus
    coverage): each row's `definition` is a full lexicon entry -- headword,
    optional bracketed etymology, cited inflected forms, THEN the actual
    sense prose, with no structural delimiter separating "forms" from
    "sense" other than English punctuation that varies entry to entry (see
    e.g. the ἀάατος/ἀάζω rows). Extracting a clean one-line gloss
    mechanically would need a heuristic prose parser with real risk of
    silently grabbing a form or citation instead of a sense -- unacceptable
    under the project's no-fabrication rule for a mechanical stage.
  - Autenrieth (sources/autenrieth/entries-partial.jsonl): genuinely the
    cleanest per-entry prose (a real <gloss> tag) but the acquisition is
    STOPPED PARTWAY -- 119 of 1,793 alpha-letter entries only (see
    sources/autenrieth/RESUME.md), letters beta onward not even enumerated.
    Unusable as a corpus-wide source today.
  - Morpheus's own short gloss, already present on every stage4-resolved
    analyses entry and already merged into the emitted
    build/dist/<work>/analyses.json this stage reads (entry["gloss"], e.g.
    "wrath", "horse", "lord, master") -- plain text, no markup, already
    one clause, median length well under MAX_GLOSS_LEN. Measured across the
    live Iliad corpus: 5,856 distinct glosses, longest 65 characters, zero
    HTML/citation noise to strip.

Morpheus's gloss wins on every axis that matters for a MECHANICAL one-line
gloss (already clean, already complete for corpus lemmata, zero extraction
risk) even though Cunliffe's prose is philologically richer -- richness is
exactly what a mechanical join cannot safely condense. If a future pass
wants Cunliffe's fuller sense, that is a hand-reviewed apparatus job, not
this stage's.

Lemma resolution and the proper-name/stoplist filters
-------------------------------------------------------
Each token's lemma is `analyses[token["k"]][0]["lemma"]` -- the same
"first entry wins" convention apparatus_epithets.py uses for its own
(unrelated) lemma resolution, kept here for consistency rather than
reinvented. A token whose key has no analyses entry is skipped (never
counted, never falls back to the raw key -- a raw Beta Code key is not a
real "word to know").

Two independent filters, both applied before ranking:
  - stoplist: the STOPLIST_SIZE most frequent lemmata by whole-CORPUS
    (both epics pooled) occurrence count. This is a fully mechanical,
    no-hand-list way to remove particles, the demonstrative/article ὁ ἡ
    τό, personal pronouns, εἰμί, etc. -- see top_stoplist().
  - proper names: any lemma whose Beta Code form is capitalized (the '*'
    prefix Diogenes/Morpheus uses for proper-name lemmata, e.g. '*(/ektwr'
    for Ἕκτωρ -- see beta.py's capital_key/lookup_variants and
    stage4_morphology.py's capitalized-token handling, which is exactly
    the signal that produces a '*'-prefixed lemma in analyses.json in the
    first place). Distinct from the stoplist: a proper name need not be
    globally frequent to be excluded here.

Determinism: no hash-seed-dependent iteration ever decides output order —
sets are used only for O(1) membership tests (stoplist, proper-name
tracking), never iterated to produce emitted content; every ranked list is
built with an explicit (-count, lemma) sort.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .config import BUILD_DIR, Manifest

STOPLIST_SIZE = 100
MAX_ENTRIES_PER_BOOK = 25
MAX_GLOSS_LEN = 80


def _load_analyses(dist_dir: Path) -> dict[str, list[dict]]:
    path = dist_dir / "analyses.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_book_lines(dist_dir: Path) -> list[tuple[int, int, list[dict]]]:
    """[(book, line_n, tokens)] for every line under dist_dir/book-*.json, in
    the corpus's own emitted order (mirrors apparatus_epithets._load_book_lines
    / apparatus_scansion._load_book_lines)."""
    out = []
    for path in sorted(dist_dir.glob("book-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        book_n = doc["book"]
        for seg in doc["segments"]:
            for line in seg["greek"]:
                out.append((book_n, line["n"], line["tokens"]))
    return out


def resolve_lemma(tok: dict, analyses: dict[str, list[dict]]) -> str | None:
    """A token's lemma via analyses[k][0]["lemma"] (see module docstring for
    why index 0, and why an unresolved key is skipped rather than faked)."""
    entries = analyses.get(tok["k"])
    if not entries:
        return None
    return entries[0].get("lemma")


def is_proper_name(lemma: str) -> bool:
    """True when `lemma` is the Beta Code capitalized form ('*'-prefixed) --
    the proper-name signal (see module docstring)."""
    return lemma.startswith("*")


def book_lemma_counts(dist_dir: Path) -> dict[int, Counter]:
    """book number -> Counter(lemma -> in-book occurrence count), over every
    resolvable token in dist_dir/book-*.json."""
    analyses = _load_analyses(dist_dir)
    counts: dict[int, Counter] = defaultdict(Counter)
    for book_n, _line_n, tokens in _load_book_lines(dist_dir):
        for tok in tokens:
            lemma = resolve_lemma(tok, analyses)
            if lemma is not None:
                counts[book_n][lemma] += 1
    return counts


def lemma_gloss_map(dist_dir: Path) -> dict[str, str]:
    """lemma -> first non-empty Morpheus gloss found for it, scanning this
    work's analyses.json in sorted-key (deterministic) order. A lemma with no
    non-empty gloss anywhere in the work is simply absent -- callers must
    never fabricate one (the honesty rule)."""
    analyses = _load_analyses(dist_dir)
    out: dict[str, str] = {}
    for key in sorted(analyses):
        for entry in analyses[key]:
            lemma = entry.get("lemma")
            gloss = (entry.get("gloss") or "").strip()
            if lemma and gloss and lemma not in out:
                out[lemma] = gloss
    return out


def _capped_gloss(gloss: str) -> str:
    """Defensive length cap (see module docstring: not observed to trigger on
    the live corpus today, but a future gloss source or corpus growth could
    produce a longer one). Truncates on a word boundary and marks the cut."""
    if len(gloss) <= MAX_GLOSS_LEN:
        return gloss
    truncated = gloss[:MAX_GLOSS_LEN].rsplit(" ", 1)[0]
    return truncated + "…"


def top_stoplist(pooled: Counter, size: int = STOPLIST_SIZE) -> set[str]:
    """The `size` most frequent lemmata in `pooled` (whole-corpus, both epics
    pooled), by deterministic (-count, lemma) rank. See module docstring."""
    ranked = sorted(pooled.items(), key=lambda kv: (-kv[1], kv[0]))
    return {lemma for lemma, _count in ranked[:size]}


def pooled_lemma_counts(per_work_book_counts: dict[str, dict[int, Counter]]) -> Counter:
    pooled: Counter = Counter()
    for book_counts in per_work_book_counts.values():
        for counter in book_counts.values():
            pooled.update(counter)
    return pooled


def book_vocab_entries(
    counts: Counter,
    stoplist: set[str],
    gloss_map: dict[str, str],
    limit: int = MAX_ENTRIES_PER_BOOK,
) -> tuple[list[dict], set[str]]:
    """One book's ranked vocab list plus the set of distinct proper-name
    lemmata this book's candidates excluded (for the run()-level report)."""
    candidates: list[tuple[str, int]] = []
    proper_lemmas: set[str] = set()
    for lemma, count in counts.items():
        if is_proper_name(lemma):
            proper_lemmas.add(lemma)
            continue
        if lemma in stoplist:
            continue
        candidates.append((lemma, count))
    candidates.sort(key=lambda lc: (-lc[1], lc[0]))

    entries: list[dict] = []
    for lemma, count in candidates[:limit]:
        entry: dict = {"lemma": lemma, "count": count}
        gloss = gloss_map.get(lemma)
        if gloss:
            entry["gloss"] = _capped_gloss(gloss)
        entries.append(entry)
    return entries, proper_lemmas


def run(manifest: Manifest, work_ids: list[str] | None = None) -> dict:
    """work_ids overrides cross-epic discovery (used by tests to run against
    a small fixture corpus without touching the real manifests/ directory);
    production calls (via __main__) always pass None, which discovers every
    manifests/*.yaml the same way apparatus_repetitions.py does."""
    work_id = manifest.work_id
    dist_root = BUILD_DIR / "dist"

    if work_ids is None:
        from .apparatus_repetitions import discover_work_ids

        work_ids = discover_work_ids()
    if work_id not in work_ids:
        work_ids = [*work_ids, work_id]

    per_work_book_counts = {wid: book_lemma_counts(dist_root / wid) for wid in work_ids}
    pooled = pooled_lemma_counts(per_work_book_counts)
    # STOPLIST_SIZE/MAX_ENTRIES_PER_BOOK are passed explicitly (rather than
    # relying on top_stoplist's/book_vocab_entries' default parameters) so a
    # module-level override (tests monkeypatch these constants against a
    # small fixture corpus) is actually honored -- Python binds a function's
    # default argument value once, at def time, so `v.STOPLIST_SIZE = N`
    # after import would otherwise silently have no effect here.
    stoplist = top_stoplist(pooled, STOPLIST_SIZE)

    gloss_map = lemma_gloss_map(dist_root / work_id)
    own_book_counts = per_work_book_counts[work_id]

    books_out: dict[str, list[dict]] = {}
    all_proper_lemmas: set[str] = set()
    total_entries = 0
    entries_with_gloss = 0
    for book_n in sorted(own_book_counts):
        entries, proper_lemmas = book_vocab_entries(
            own_book_counts[book_n], stoplist, gloss_map, MAX_ENTRIES_PER_BOOK
        )
        books_out[str(book_n)] = entries
        all_proper_lemmas |= proper_lemmas
        total_entries += len(entries)
        entries_with_gloss += sum(1 for e in entries if "gloss" in e)

    out_dir = dist_root / work_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "vocab.json"
    out_path.write_text(
        json.dumps({"status": "draft", "books": books_out}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    return {
        "work": work_id,
        "path": out_path,
        "books_covered": len(books_out),
        "total_entries": total_entries,
        "entries_with_gloss": entries_with_gloss,
        "gloss_coverage": round(entries_with_gloss / total_entries, 4) if total_entries else 0.0,
        "stoplist_size": len(stoplist),
        "proper_names_excluded_distinct": len(all_proper_lemmas),
    }
