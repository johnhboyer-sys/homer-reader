"""Stage 6: build the search index for the Astro frontend.

Emits these files under build/stage6/:

  greek_lemma.json — {fold_lemma: [[seg_idx, token_pos], ...]}
                 keyed by the token's dictionary HEADWORD (lemma), so a query
                 finds every inflected form of a word. fold_lemma strips all
                 accents, breathings, iotasubscript, macrons from the Beta Code
                 key (only base letters remain), so wildcard prefix matching
                 works uniformly.

  greek_form.json — {fold(surface): [[seg_idx, token_pos], ...]}
                 keyed by the SURFACE form as written (the inflected token), so
                 a query can match the exact form rather than the whole lemma.

  english.json — {word: [[seg_idx, word_pos], ...]}
                 The primary translation's (Murray's) words as english_words()
                 splits them, with each word's position in its segment, so a
                 phrase is an adjacency test over postings exactly as it is
                 for Greek (aristotle-reader's shape, 7ddd67b7ef).

  meta.json    — [{id, book, column, greek_head, english_head}]
                 Ordered list of segment metadata, indexed by seg_idx.
                 greek_head: first line of text (for result preview).
                 english_head: the FULL English chunk (name is legacy). Query
                   time uses it for exact-phrase verification and English
                   occurrence counting, so it must not be truncated.

  offsets.json — the word-offset primitive: one running token number per work,
                 in document order, plus the structural coordinates beside it.
                 {token_count, seg_base_offset[], segments[{book, column,
                 line_runs}], book_bounds[], chapter_bounds[]}. Global offset
                 of a posting = seg_base_offset[seg_idx] + token_pos.
                 Homer's segments are BOOKS (24/work), not Bekker columns, so
                 book_bounds is nearly the whole segment list and line_runs
                 (not column) is what carries book.line resolution — load-
                 bearing for this corpus, not an optimization. Homer's
                 "chapters" are its scenes (apparatus/scenes/<work>.json):
                 chapter_bounds holds one {book, chapter, start, accuracy}
                 per scene, chapter = "<firstLine>-<lastLine>", start = the
                 global offset of the scene's first token (see
                 scene_chapter_bounds).

  grammar-dict.json / grammar-col.bin — the grammatical index: a signature
                 dictionary (distinct whole morphological readings, keyed by
                 small int id) plus a packed column of one id per token,
                 indexed by GLOBAL OFFSET so it joins directly onto
                 offsets.json. Not an inverted index — grammatical predicates
                 (case=gen, etc.) are anti-selective and would make postings
                 near-dense.

  english-<slot>.json — one more English index per translation beyond the
                 primary, same shape as english.json: english-ross.json
                 (Butler), english-third.json (Pope), english-overlay-<id>.json
                 (Kosmos). Written by emit_translation_indexes() from the
                 emitted book JSON, which stage7 calls once the books exist.
                 search/eng-chapters.json, where each scene starts in each
                 translation's words, is written later, by search_scenes.py,
                 because it follows the reader's scene pages.

All of these are copied to build/dist/{work}/search/ by stage7. Stage 6 also
writes a per-work n-gram fold-stream file to build/ngrams/{work}.json (NOT
copied to dist by stage7 — it is cross-work scratch consumed by the separate
stage8 phrase-index build).
"""

from __future__ import annotations

import json
import re
import struct
import unicodedata
from collections import defaultdict
from pathlib import Path

from .config import BUILD_DIR, REPO_ROOT, Manifest
from .parse_filter import filter_parses
from .stage2_validate import (
    check_grammar,
    check_ngram_streams,
    check_offsets,
    merge_search_checks,
    write_report,
)

_FOLD = re.compile(r"[^a-z']")  # keep only base letters and apostrophe

# The canonical scenes (apparatus_scenes.SCENES_DIR); a module constant so a
# test can point it elsewhere.
SCENES_DIR = REPO_ROOT / "apparatus" / "scenes"

# -- The English word split -----------------------------------------------------
# Ported verbatim from aristotle_pipeline.stage6_search at aristotle-reader
# 7ddd67b7ef (lines 67-115 there), comments included. Its client mirror is
# englishWords() in Aristotle's shared/lib/search.ts (line 593 there), and
# pipeline/tests/fixtures/english_words.json pins the two together. A
# posting's word_pos is only right if both sides count words the same way.
_EN_WORD = re.compile(r"[a-z']+")
# The archive translations print possessives and contractions with U+2019
# (Aristotle’s, isn’t); U+02BC is the modifier-letter apostrophe. The reader
# folds a typed straight apostrophe to itself (englishFold) and the text's
# curly one to straight (englishWords) — so the index must key "aristotle's"
# as one word or neither path can find it.
_EN_APOSTROPHE = re.compile("[\u2019\u02bc]")
# Apparatus a translation's prose carries inline, which the reader renders as
# controls and not as words: a footnote marker [^1.9] is glued to the word
# before it and is simply dropped; a sidenote or figure marker [[s3]] / [[fig1]]
# stands between words and leaves a space. Indexed as text, [[s3]] was the word
# "s" and broke every phrase that ran across it. Mirrored by EN_FOOTNOTE /
# EN_SIDENOTE in shared/lib/search.ts.
_EN_FOOTNOTE = re.compile(r"\[\^[0-9A-Za-z_.*\u2020]+\]")
_EN_SIDENOTE = re.compile(r"\[\[(?:s|fig)[0-9]+\]\]")
# One pass, so a marker counts only as written: "[[s[^1]12]]" loses its
# footnote and keeps "[[s12]]" as text, never a sidenote, as the reader shows
# it: the footnote becomes a button and the rest stays prose. englishWords
# scans the same.
_EN_MARKER = re.compile(f"(?P<fn>{_EN_FOOTNOTE.pattern})|{_EN_SIDENOTE.pattern}")
# Older translations print Latin letters the fold would otherwise split on:
# "Lacedæmonians" was indexed as "laced" + "monians", "versâ" as "vers". The
# ligatures become two letters and accents drop off, so the word is the one a
# reader types. Mirrored by latinFold in shared/lib/search.ts.
_EN_COMBINING = re.compile("[\u0300-\u036f]")


def _latin_fold(text: str) -> str:
    text = _EN_COMBINING.sub("", unicodedata.normalize("NFD", text))
    return text.replace("\u00e6", "ae").replace("\u0153", "oe")


def fold_lemma(beta_key: str) -> str:
    """Strip all Beta Code diacritics; keep only base letters + apostrophe."""
    return _FOLD.sub("", beta_key.lower())


def english_words(text: str) -> list[str]:
    """The English word stream as the reader's fold sees it: lowercase, curly
    apostrophes made straight, split on anything outside [a-z']. An apostrophe
    at a word's edge is a quotation mark (‘change’ closes with the same U+2019
    that Aristotle’s elides with) and is not part of the word. Shared with
    stage8 so english.json and english-segments.json count the same words.
    Inline footnote, sidenote and figure markers are not words (see
    _EN_FOOTNOTE). Ligatures and accented letters fold to plain ones (see
    _latin_fold)."""
    text = _EN_MARKER.sub(lambda m: "" if m.group("fn") else " ", text)
    words = _EN_WORD.findall(_latin_fold(_EN_APOSTROPHE.sub("'", text).lower()))
    return [w for w in (raw.strip("'") for raw in words) if w]


def english_word_starts(text: str) -> list[int]:
    """The character offset in `text` at which each of english_words(text)
    begins: its first letter, after any leading apostrophe. Homer's addition,
    for placing words in scenes (search_scenes.py). It walks the text a
    character at a time as the client's englishWords() does, and is checked
    against english_words() on every call, so the two cannot disagree on how
    many words there are or which they are."""
    words: list[str] = []
    starts: list[int] = []
    word: list[str] = []
    at: list[int] = []

    def close() -> None:
        a, b = 0, len(word)
        while a < b and word[a] == "'":
            a += 1
        while b > a and word[b - 1] == "'":
            b -= 1
        if a < b:
            words.append("".join(word[a:b]))
            starts.append(at[a])
        word.clear()
        at.clear()

    i = 0
    while i < len(text):
        if text[i] == "[":
            m = _EN_FOOTNOTE.match(text, i)
            if m:
                i = m.end()
                continue
            m = _EN_SIDENOTE.match(text, i)
            if m:
                close()
                i = m.end()
                continue
        for ch in _latin_fold(_EN_APOSTROPHE.sub("'", text[i]).lower()):
            if "a" <= ch <= "z" or ch == "'":
                word.append(ch)
                at.append(i)
            else:
                close()
        i += 1
    close()
    if words != english_words(text):
        raise ValueError(
            "english_word_starts disagrees with english_words on "
            f"{text[:60]!r}…: fix the walk, not the index"
        )
    return starts


# -- Homer's scenes as the search's chapters ------------------------------------

def scene_chapter_bounds(
    scene_books: list[dict], segments: list[dict], seg_base_offset: list[int]
) -> list[dict]:
    """One chapter bound per scene: {book, chapter, start, accuracy}.

    `chapter` names the scene by its line range, "<first>-<last>" (ASCII
    hyphen); `start` is the global offset of the first token of the scene's
    first line (seg_base_offset of the segment holding that line, plus the
    tokens of the lines before it). Lines are matched by their vulgate number,
    never by position, so a numbering gap is carried as it stands. A scene
    whose first line is not in the text, or a book with no scenes, is an
    error: the client would otherwise put that book's hits nowhere.
    """
    by_book = {b["book"]: b.get("scenes") or [] for b in scene_books}
    # (book, line) -> global offset of the line's first token.
    line_start: dict[tuple[int, int], int] = {}
    for i, seg in enumerate(segments):
        pos = seg_base_offset[i]
        for line in seg["lines"]:
            line_start.setdefault((seg["book"], line["n"]), pos)
            pos += len(line["tokens"])
    bounds: list[dict] = []
    for book in dict.fromkeys(seg["book"] for seg in segments):
        scenes = by_book.get(book)
        if not scenes:
            raise ValueError(f"stage6: book {book} has no scenes to count search hits by")
        for scene in scenes:
            first, last = scene["lines"][0], scene["lines"][1]
            start = line_start.get((book, first))
            if start is None:
                raise ValueError(
                    f"stage6: scene {book}.{first}-{last} starts on line {book}.{first}, "
                    "which the Greek text does not have"
                )
            bounds.append({"book": book, "chapter": f"{first}-{last}",
                           "start": start, "accuracy": "exact"})
    return bounds


# -- Indexes for the translations beyond the primary ----------------------------
# Ported from aristotle_pipeline.stage6_search (7ddd67b7ef, lines 235-365),
# with Homer's slot names: Butler is 'ross' (Aristotle renamed its slot
# 'secondary'), so the client's englishIndexFile() names his index
# english-ross.json. eng-chapters.json is not written here; see
# search_scenes.py.

_OVERLAY_ID = re.compile(r"[a-z0-9_]+")


def segment_pieces(seg: dict) -> dict[str, list[dict]]:
    """The non-primary translation pieces of one emitted segment, by slot:
    'ross', 'third', and 'overlay-<id>' for each overlay — the names the
    client's englishIndexSlot() gives them."""
    out: dict[str, list[dict]] = {}
    if seg.get("ross"):
        out["ross"] = seg["ross"]
    if seg.get("third"):
        out["third"] = seg["third"]
    for tid, pieces in (seg.get("overlays") or {}).items():
        if not _OVERLAY_ID.fullmatch(tid):
            raise ValueError(f"overlay id {tid!r} cannot name an index file")
        if pieces:
            out[f"overlay-{tid}"] = pieces
    return out


def segment_translations(seg: dict) -> dict[str, list[str]]:
    """The non-primary translation texts of one emitted segment, by slot."""
    return {slot: [p.get("text") or "" for p in pieces]
            for slot, pieces in segment_pieces(seg).items()}


def translation_index_name(slot: str) -> str:
    return "english.json" if slot == "english" else f"english-{slot}.json"


def emit_translation_indexes(work_dir: Path) -> dict[str, dict[str, int]]:
    """Write search/english-<slot>.json for every non-primary translation.

    Reads the work's emitted book-NN.json and search/meta.json, which must
    already be in place; seg_idx is a segment's position in meta.json, exactly
    as in english.json. A segment's word_pos runs through its pieces in order,
    as the client counts them. Any english-*.json left from an earlier build
    is removed first, so an index can never outlive its translation. Returns,
    per slot, the number of distinct words and of segments indexed.
    """
    search_dir = work_dir / "search"
    meta = json.loads((search_dir / "meta.json").read_text(encoding="utf-8"))
    seg_idx = {m["id"]: i for i, m in enumerate(meta)}

    posts: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    segments: dict[str, set[int]] = defaultdict(set)
    for book_path in sorted(work_dir.glob("book-*.json")):
        doc = json.loads(book_path.read_text(encoding="utf-8"))
        for seg in doc["segments"]:
            slots = segment_translations(seg)
            if not slots:
                continue
            si = seg_idx.get(seg["id"])
            if si is None:
                raise ValueError(
                    f"{book_path.name}: segment {seg['id']} is not in search/meta.json"
                )
            for slot, texts in slots.items():
                pos = 0
                for text in texts:
                    for word in english_words(text):
                        posts[slot][word].append([si, pos])
                        pos += 1
                if pos:
                    segments[slot].add(si)

    for stale in search_dir.glob("english-*.json"):
        stale.unlink()
    summary: dict[str, dict[str, int]] = {}
    for slot in sorted(posts):
        # In document order, as english.json is.
        index = {word: sorted(plist) for word, plist in posts[slot].items()}
        (search_dir / translation_index_name(slot)).write_text(
            json.dumps(index, ensure_ascii=False), encoding="utf-8"
        )
        summary[slot] = {"words": len(posts[slot]), "segments": len(segments[slot])}
    return summary


# -- Morphology feature vocabulary -------------------------------------------
# Ported verbatim from aristotle_pipeline.stage6_search (that corpus's Attic
# prose). `parse` is a raw Morpheus string ("pres ind act 2nd sg (doric
# aeolic)") with parentheses glued to the first and last word of a qualifier
# run, so strip the parens and classify word by word.
#
# There is deliberately NO part-of-speech category. Morpheus emits no
# noun/verb/adjective field, and inferring one from feature presence would
# overstate the data: participles carry both nominal and verbal morphology, and
# nouns and adjectives are indistinguishable here. Only Morpheus's own explicit
# markers are indexed, under "marker". Note that `part` is the PARTICIPLE mood,
# not `particle` — they are different tags and must not be conflated.
#
# Dialect words (attic, epic, doric, …) and clitic/format markers (enclitic,
# nu_movable, indeclform, …) are not queryable features and are skipped. Two
# analyses differing only by dialect collapse to one reading, which is right:
# they are the same morphological reading.
#
# Homer-specific caution (not verified against a live corpus — see
# stage6_search's run() docstring note below): this vocabulary was built for
# Aristotle's Attic prose and ported unchanged, on the reasoning that Morpheus's
# feature TAGS (gender/case/number/person/tense/mood/voice/degree/marker) are
# the same closed set across dialects — only the VALUES a given form licenses
# differ (epic favours the dual, admits contracted/uncontracted doublets, etc.),
# and every value Homer needs (masc/fem/neut, all six cases including the
# syncretic nom/voc/acc, sg/pl/dual, all persons/tenses/moods/voices) is already
# present. `run()` below raises on any parse word that is neither a known
# feature value nor a listed `_IGNORED_TAG`, so a real corpus build surfaces a
# gap here rather than silently dropping it (see F1/F2 in
# docs/advanced-search-handoff.md's review trail).
#
# `adv` (found once in the real Odyssey stage-4 output, on ἁμόθεν / Beta
# `a(mo/qen`, Od. 1.10, parse == "adv" exactly) is Aristotle's Attic prose
# never emitting it — confirmed absent from aristotle-reader's own
# build/stage4/analyses.json — but it is the same kind of explicit,
# non-inflectional Morpheus marker as "adverb"/"adverbial", just an
# abbreviated spelling epic Morpheus data uses here. It belongs in "marker"
# alongside them, not in a new category.
_FEATURES: dict[str, str] = {
    value: category
    for category, values in {
        "gender": "masc fem neut masc/fem masc/neut masc/fem/neut",
        "case": "nom gen dat acc voc nom/acc nom/voc nom/voc/acc gen/dat",
        "number": "sg pl dual",
        "person": "1st 2nd 3rd",
        "tense": "pres imperf fut aor perf plup futperf",
        "mood": "ind subj opt imperat inf part",
        "voice": "act mid pass mp",
        "degree": "comp superl irreg_comp",
        "marker": "adv adverb adverbial particle prep conj interrog exclam indecl numeral letter",
    }.items()
    for value in values.split()
}

# Parse words that are NOT grammatical features and must never become one:
# dialect labels (this reading is also licensed in another dialect — it does
# not change what the reading MEANS) and clitic/format qualifiers (how the
# form is written or accented, not what it is). Counts are from a real,
# corpus-wide scan of the Odyssey's stage-4 analyses.json (the Iliad's was
# absent at review time — expect the full rebuild to add values here or to
# _FEATURES; it should not need to add both for the same tag).
#
#   epic (10,493), ionic (8,413), doric (3,943), attic (3,437),
#   aeolic (2,801), homeric (2,010)              -- dialect labels
#   indeclform (833), enclitic (54), poetic (47), parad_form (38),
#   proclitic (30), prose (20), nu_movable (9), a_priv (4), geog_name (3),
#   contr (2), irreg_superl (2)                  -- clitic/format qualifiers
#
# Two analyses differing only by one of these collapse to one reading, which
# is right: they are the same morphological reading.
_IGNORED_TAGS: frozenset[str] = frozenset({
    # dialect labels
    "epic", "ionic", "doric", "attic", "aeolic", "homeric",
    # clitic/format qualifiers
    "indeclform", "enclitic", "poetic", "parad_form", "proclitic", "prose",
    "nu_movable", "a_priv", "geog_name", "contr", "irreg_superl",
})

# Reserved signature ids, so the column stays aligned with the offset space
# even where there is nothing to say about a token.
SIG_UNKEYED = 0     # token had no Beta Code key (stage3 key failure)
SIG_UNANALYSED = 1  # key resolved, but Morpheus returned no analysis


def parse_reading(parse: str) -> dict[str, list[str]]:
    """One Morpheus parse string -> {category: [values]}.

    Syncretic values expand INSIDE the reading (nom/voc/acc -> nom, voc, acc).
    A single analysis spanning three cases is genuinely three-way ambiguous and
    must never be reported as one certain parse — that expansion is what makes
    the ambiguity count honest rather than a count of analysis records.
    """
    reading: dict[str, list[str]] = {}
    for word in parse.replace("(", " ").replace(")", " ").split():
        category = _FEATURES.get(word)
        if category is None:
            continue
        values = reading.setdefault(category, [])
        for value in word.split("/"):
            if value not in values:
                values.append(value)
    return {c: sorted(v) for c, v in reading.items()}


def check_known_tag(word: str, *, work_id: str, surface: str, key: str) -> None:
    """Raise if `word` is neither a known grammar feature nor a listed
    dialect/format qualifier — see _FEATURES / _IGNORED_TAGS above.

    A third possibility (neither) is a real Homeric tag this vocabulary has
    never seen, and letting it through would make it vanish from grammar
    search silently, which is exactly the failure this gate exists to catch
    (F2, docs/advanced-search-handoff.md). Fail loudly, naming the work, the
    tag, and an example surface form, so whoever hits it can decide
    feature-vs-ignore without re-deriving this context.
    """
    if word in _FEATURES or word in _IGNORED_TAGS:
        return
    raise ValueError(
        f"stage6 ({work_id}): unrecognized Morpheus parse tag {word!r} on "
        f"surface form {surface!r} (key {key!r}) — it is neither a known "
        "grammar feature in _FEATURES nor a listed dialect/format qualifier "
        "in _IGNORED_TAGS. If it is a genuine morphological value, add it "
        "to _FEATURES under the right category; if it is a dialect label or "
        "clitic/format qualifier like the others in _IGNORED_TAGS, add it "
        "there with a one-line reason. Do not drop it silently — an "
        "unhandled tag disappears from every grammar query."
    )


def signature(entries: list[dict]) -> tuple:
    """The distinct readings a token's analyses license, canonically ordered.

    Whole readings are kept rather than a per-category union, so correlations
    survive: analyses {masc nom sg, fem acc pl} must not satisfy a query for
    masc + acc + sg, which a flattened union would wrongly allow.
    """
    readings = []
    for entry in entries:
        reading = parse_reading(entry.get("parse") or "")
        if not reading:
            continue
        key = tuple((c, tuple(v)) for c, v in sorted(reading.items()))
        if key not in readings:
            readings.append(key)
    return tuple(sorted(readings))


def _curated_entries(entries: list[dict], lemma_map: dict[str, list[str]]) -> list[dict]:
    """The analyses a grammar signature is built from, after this corpus's own
    curation — not Morpheus's raw, unranked candidate list.

    Homer's `morphology_overrides.json` and the analysis ranking added in
    commit 6166beb23 (see stage7_emit.resolve_parses / parse_filter.rank_parses
    / parse_filter.apply_morphology_override) correct a token's LEMMA and
    GLOSS, never its `parse` (morphological tag) string, and `signature()`
    above dedupes+sorts readings regardless of input order — so neither the
    override nor the ranking step can change a grammar signature; they were
    verified (by reading parse_filter.load_morphology_overrides, whose
    `allowed` field set is only {surface, justification, lemma, gloss} — no
    "parse" key is ever accepted) to be structurally inert here, not silently
    bypassed.

    What DOES matter is `filter_parses`: it removes an analysis Morpheus
    offered that this corpus's editors have already judged spurious (redundant
    with a resolved sibling reading), and such a reading, left in, would inject
    a bogus grammatical category into the index that the reader itself would
    never show. That filter is applied here, using the same LSJ-backing test
    (`lemma_map`) stage7_emit.emit_analyses uses to build the reader's own
    parse cards, so the search index and the reader agree on which analyses
    are real.
    """
    if len(entries) < 2:
        return entries
    enriched = [
        {
            "parse": a.get("parse") or "",
            "gloss": a.get("gloss") or "",
            "lsj": lemma_map.get(a["lemma"], []) if a.get("lemma") else [],
        }
        for a in entries
    ]
    return filter_parses(enriched)


def run(manifest: Manifest) -> Path:
    tokens_doc = json.loads(
        (BUILD_DIR / "stage3" / "tokens.json").read_text(encoding="utf-8")
    )
    key_map = json.loads(
        (BUILD_DIR / "stage4" / "key_map.json").read_text(encoding="utf-8")
    )
    analyses = json.loads(
        (BUILD_DIR / "stage4" / "analyses.json").read_text(encoding="utf-8")
    )
    english = json.loads(
        (BUILD_DIR / "stage1" / "english_chunks.json").read_text(encoding="utf-8")
    )
    # Used only to curate the grammar signature (see _curated_entries above);
    # absent on a stage6-only rerun predating stage5, in which case the
    # signature falls back to Morpheus's raw analyses, unfiltered.
    lemma_map_path = BUILD_DIR / "stage5" / "lemma_map.json"
    lemma_map = (
        json.loads(lemma_map_path.read_text(encoding="utf-8"))
        if lemma_map_path.exists() else {}
    )

    # Ordered segment list for index keys
    segments = tokens_doc["segments"]
    seg_idx = {s["id"]: i for i, s in enumerate(segments)}

    eng_by_id = {c["id"]: c for c in english["chunks"]}

    # Token fold sequences per segment — needed by the client for phrase search.
    # One space-separated string of fold lemma keys in document order.
    fold_seq_by_id: dict[str, str] = {}
    for seg in segments:
        folds = []
        for line in seg["lines"]:
            for tok in line["tokens"]:
                key = tok.get("k")
                stored = key_map.get(key) if key else None
                if stored:
                    lemmata = [a["lemma"] for a in analyses.get(stored, []) if a["lemma"]]
                    if lemmata:
                        folds.append(fold_lemma(lemmata[0]))
                    else:
                        folds.append(fold_lemma(stored))
                elif key:
                    folds.append(fold_lemma(key))
        fold_seq_by_id[seg["id"]] = " ".join(folds)

    # -- Greek inverted indexes ----------------------------------------------
    # Two parallel indexes, both fold_lemma -> [(seg_idx, token_pos), ...]:
    #   lemma_posts: keyed by each token's dictionary headword(s) — "all forms".
    #   form_posts:  keyed by the token's surface form as written — "exact form".
    lemma_posts: dict[str, list] = defaultdict(list)
    form_posts: dict[str, list] = defaultdict(list)
    for seg in segments:
        si = seg_idx[seg["id"]]
        pos = 0
        for line in seg["lines"]:
            for tok in line["tokens"]:
                key = tok.get("k")
                if key:
                    sf = fold_lemma(key)  # surface form as written
                    if sf:
                        form_posts[sf].append([si, pos])
                stored = key_map.get(key) if key else None
                if stored:
                    for a in analyses.get(stored, []):
                        fl = fold_lemma(a["lemma"]) if a["lemma"] else fold_lemma(stored)
                        if fl:
                            lemma_posts[fl].append([si, pos])
                pos += 1

    # Deduplicate each index (a lemma may repeat from homonym analyses; a
    # surface key is added once per token but dedupe defensively).
    def _dedupe(posts: dict[str, list]) -> dict[str, list]:
        out: dict[str, list] = {}
        for fl, plist in posts.items():
            seen: set[tuple] = set()
            deduped = []
            for pair in plist:
                t = tuple(pair)
                if t not in seen:
                    seen.add(t)
                    deduped.append(pair)
            out[fl] = deduped
        return out

    greek_lemma = _dedupe(lemma_posts)
    greek_form = _dedupe(form_posts)

    # -- English inverted index -----------------------------------------------
    # word -> [[seg_idx, word_pos], ...] in document order; word_pos counts
    # every word of the segment's English as english_words() splits it
    # (aristotle-reader 7ddd67b7ef, stage6_search.py:439-450).
    eng_posts: dict[str, list] = defaultdict(list)
    for seg in segments:
        eng = eng_by_id.get(seg["id"])
        if not eng:
            continue
        si = seg_idx[seg["id"]]
        for pos, word in enumerate(english_words(eng["text"])):
            eng_posts[word].append([si, pos])
    english_idx = dict(eng_posts)

    # -- Segment metadata -----------------------------------------------------
    meta = []
    for seg in segments:
        # Greek head: join first two lines of surface text
        lines = seg["lines"]
        greek_head = " ".join(
            " ".join(t["t"] for t in l["tokens"])
            for l in lines[:2]
        )
        eng = eng_by_id.get(seg["id"])
        # Full English chunk (NOT truncated). Query-time exact-phrase
        # verification and English occurrence counting run against this, so a
        # cap (formerly [:500]) silently dropped matches and undercounted
        # repeats past the cut. It equals the emitted segment's english.text, so
        # char offsets found here map straight onto the rendered passage.
        english_head = eng["text"] if eng else ""
        meta.append(
            {
                "id": seg["id"],
                "book": seg["book"],
                "column": seg["column"],
                "greek_head": greek_head,
                "greek_tokens": fold_seq_by_id.get(seg["id"], ""),
                "english_head": english_head,
            }
        )

    # -- Offset primitive ------------------------------------------------------
    # One running word number per work, assigned in the same document order the
    # index loop above walks. The global offset of any existing posting is
    # seg_base_offset[seg_idx] + token_pos, so no posting has to change and no
    # reverse map is needed. Counts EVERY stage3 token, keyless ones included,
    # so it stays in step with token_pos. Homer's segments are books, not
    # Bekker columns: book_bounds is nearly the whole segment list.
    # chapter_bounds are the reader's scenes (scene_chapter_bounds).
    seg_base_offset: list[int] = []
    seg_coords: list[dict] = []
    running = 0
    for seg in segments:
        seg_base_offset.append(running)
        # line_runs lets the client turn an offset back into a book.line
        # citation without fetching the whole book-NN.json — the vulgate
        # lineation is sacred, so these are the EMITTED line numbers, gaps and
        # bracketed lines included, never a renumbered enumeration index.
        line_runs = [[l["n"], len(l["tokens"])] for l in seg["lines"]]
        running += sum(n for _, n in line_runs)
        seg_coords.append(
            {"book": seg["book"], "column": seg["column"], "line_runs": line_runs}
        )
    token_count = running

    # A segment is keyed (book, column) and so never straddles a book: each
    # book begins at its first segment's base.
    book_bounds: list[dict] = []
    for i, seg in enumerate(segments):
        if not book_bounds or book_bounds[-1]["book"] != seg["book"]:
            book_bounds.append({"book": seg["book"], "start": seg_base_offset[i]})

    scenes_path = SCENES_DIR / f"{manifest.work_id}.json"
    if not scenes_path.exists():
        raise ValueError(
            f"stage6: {scenes_path} is missing; the search counts hits by scene "
            "and needs every book's scenes"
        )
    scene_books = json.loads(scenes_path.read_text(encoding="utf-8"))["books"]
    chapter_bounds = scene_chapter_bounds(scene_books, segments, seg_base_offset)

    offsets = {
        # Doubles as a build fingerprint: every artifact indexed by global
        # offset must agree on it, or they were built from different runs.
        "token_count": token_count,
        "seg_base_offset": seg_base_offset,
        "segments": seg_coords,
        "book_bounds": book_bounds,
        "chapter_bounds": chapter_bounds,
    }

    # -- Grammatical index -----------------------------------------------------
    # A signature dictionary plus a packed column, not an inverted index:
    # grammatical predicates are anti-selective (case=gen matches ~10% of every
    # token in the corpus), so postings would go near-dense and dwarf the lexical
    # indexes. Interning readings instead gives a table of a few thousand
    # signatures and one small int per token, indexed by GLOBAL OFFSET — so the
    # column joins directly onto the offset primitive above.
    sig_ids: dict[tuple, int] = {}
    sig_list: list[tuple] = [(), ()]  # slots 0 and 1 are the reserved kinds
    column: list[int] = []
    # The n-gram source, gathered in the same walk. Two fold streams indexed by
    # global offset, keyed exactly as greek_form.json and greek_lemma.json are —
    # so a phrase found here is a phrase the search can find. null marks a token
    # no index can key, which breaks the stream: an n-gram may not span it.
    form_stream: list[str | None] = []
    lemma_stream: list[list[str] | None] = []
    for seg in segments:
        for line in seg["lines"]:
            for tok in line["tokens"]:
                key = tok.get("k")
                form_stream.append(fold_lemma(key) or None if key else None)
                if not key:
                    column.append(SIG_UNKEYED)
                    lemma_stream.append(None)
                    continue
                stored = key_map.get(key)
                entries = analyses.get(stored, []) if stored else []
                # Every lemma this token licenses, not a chosen one: which lemma
                # an ambiguous position contributes is a policy the corpus pass
                # settles, and deciding it here would hide the choice.
                lemmas = sorted({
                    fold_lemma(a["lemma"]) if a["lemma"] else fold_lemma(stored)
                    for a in entries
                } - {""})
                lemma_stream.append(lemmas or None)
                # Every parse word must be a known feature value or a listed
                # ignored qualifier, or the build fails now rather than the
                # tag silently vanishing from grammar search (F2).
                for a in entries:
                    for word in (a.get("parse") or "").replace("(", " ").replace(")", " ").split():
                        check_known_tag(
                            word,
                            work_id=manifest.work_id,
                            surface=tok.get("t") or key,
                            key=key,
                        )
                sig = signature(_curated_entries(entries, lemma_map))
                if not sig:
                    column.append(SIG_UNANALYSED)
                    continue
                sid = sig_ids.get(sig)
                if sid is None:
                    sid = len(sig_list)
                    sig_ids[sig] = sid
                    sig_list.append(sig)
                column.append(sid)

    # Uint16 covers a few thousand signatures with room to spare; widen rather
    # than silently truncate if a work ever exceeds it.
    width = 4 if len(sig_list) > 0xFFFF else 2
    grammar_dict = {
        "token_count": token_count,  # must match offsets.json — same build
        "width": width,
        "categories": sorted(set(_FEATURES.values())),
        "reserved": {"unkeyed": SIG_UNKEYED, "unanalysed": SIG_UNANALYSED},
        "sigs": [
            [{category: list(values) for category, values in reading} for reading in sig]
            for sig in sig_list
        ],
    }

    # The check_grammar re-derivation must agree with how the column was
    # actually built above (curated, not raw Morpheus) or every legitimately
    # filtered token would report as a false "semantic mismatch".
    def _signature_fn(entries: list[dict]) -> tuple:
        return signature(_curated_entries(entries, lemma_map))

    streams_check = check_ngram_streams(
        form_stream, lemma_stream, greek_form, greek_lemma, seg_base_offset, token_count
    )
    offsets_check = check_offsets(
        offsets, segments, manifest.data.get("expected_line_gaps") or []
    )
    grammar_check = check_grammar(
        grammar_dict, column, offsets, segments, key_map, analyses, _signature_fn
    )
    for name, check in (("offset", offsets_check), ("grammar", grammar_check),
                        ("n-gram stream", streams_check)):
        if not check["ok"]:
            raise ValueError(
                f"stage6: {name} validation failed —\n  "
                + "\n  ".join(check["problems"][:20])
            )

    out_dir = BUILD_DIR / "stage6"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "offsets.json").write_text(
        json.dumps(offsets, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "grammar-dict.json").write_text(
        json.dumps(grammar_dict, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "grammar-col.bin").write_bytes(
        struct.pack(f"<{len(column)}{'I' if width == 4 else 'H'}", *column)
    )

    # The n-gram source goes OUTSIDE build/stage6, which is per-work scratch and
    # is overwritten by the next work. The corpus n-gram pass is a separate
    # cross-work stage and needs every work's stream present at once.
    ngram_dir = BUILD_DIR / "ngrams"
    ngram_dir.mkdir(parents=True, exist_ok=True)
    (ngram_dir / f"{manifest.work_id}.json").write_text(
        json.dumps(
            {
                "work": manifest.work_id,
                # Fingerprint: the corpus pass refuses to merge streams that
                # disagree with the offsets they are supposed to index.
                "token_count": token_count,
                "book_bounds": book_bounds,
                "chapter_bounds": chapter_bounds,
                "form": form_stream,
                "lemma": lemma_stream,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out_dir / "greek_lemma.json").write_text(
        json.dumps(greek_lemma, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "greek_form.json").write_text(
        json.dumps(greek_form, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "english.json").write_text(
        json.dumps(english_idx, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    summary = {
        "greek_lemmata": len(greek_lemma),
        "greek_forms": len(greek_form),
        "english_terms": len(english_idx),
        "chapter_bounds": len(chapter_bounds),
        "segments": len(meta),
        "tokens": token_count,
        "signatures": grammar_check["signatures"],
        "tokens_unanalysed": grammar_check["tokens_unanalysed"],
        "ngram_form_tokens": streams_check["form_tokens"],
        "ngram_multi_lemma": streams_check["multi_lemma_tokens"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    (out_dir / "grammar_report.json").write_text(
        json.dumps({"offsets": offsets_check, "grammar": grammar_check}, indent=1)
    )

    # Fold these results into Homer's stage2 report (see
    # stage2_validate.merge_search_checks): stage2's own early run() executes
    # before stage6 and cannot see these artifacts, so this is the first point
    # they can be recorded in the one document a human or preflight gate reads.
    # A stage6-only rerun with no stage2 report on disk skips this merge rather
    # than failing — the checks above have already gated the artifacts either
    # way.
    stage2_dir = BUILD_DIR / "stage2"
    report_path = stage2_dir / "validation_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        merge_search_checks(
            report,
            offsets=offsets_check,
            grammar=grammar_check,
            ngram_streams=streams_check,
        )
        write_report(report, stage2_dir)

    return out_dir
