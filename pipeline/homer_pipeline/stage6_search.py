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

  english.json — {word: [seg_idx, ...]}
                 Lowercased, punctuation-stripped English words.
                 Phrase search is handled at query time via string inclusion
                 on the (small) English chunk texts in meta.json, so
                 positions are not stored here.

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
                 bearing for this corpus, not an optimization. Homer has no
                 chapter concept, so chapter_bounds is always [].

  grammar-dict.json / grammar-col.bin — the grammatical index: a signature
                 dictionary (distinct whole morphological readings, keyed by
                 small int id) plus a packed column of one id per token,
                 indexed by GLOBAL OFFSET so it joins directly onto
                 offsets.json. Not an inverted index — grammatical predicates
                 (case=gen, etc.) are anti-selective and would make postings
                 near-dense.

All of these are copied to build/dist/{work}/search/ by stage7. Stage 6 also
writes a per-work n-gram fold-stream file to build/ngrams/{work}.json (NOT
copied to dist by stage7 — it is cross-work scratch consumed by the separate
stage8 phrase-index build).
"""

from __future__ import annotations

import json
import re
import struct
from collections import defaultdict
from pathlib import Path

from .config import BUILD_DIR, Manifest
from .parse_filter import filter_parses
from .stage2_validate import (
    check_grammar,
    check_ngram_streams,
    check_offsets,
    merge_search_checks,
    write_report,
)

_FOLD = re.compile(r"[^a-z']")  # keep only base letters and apostrophe
_EN_WORD = re.compile(r"[a-z']+")


def fold_lemma(beta_key: str) -> str:
    """Strip all Beta Code diacritics; keep only base letters + apostrophe."""
    return _FOLD.sub("", beta_key.lower())


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
    # word -> sorted list of unique seg_idxs
    eng_posts: dict[str, set] = defaultdict(set)
    for seg in segments:
        eng = eng_by_id.get(seg["id"])
        if not eng:
            continue
        si = seg_idx[seg["id"]]
        for word in _EN_WORD.findall(eng["text"].lower()):
            eng_posts[word].add(si)
    english_idx = {w: sorted(idxs) for w, idxs in eng_posts.items()}

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
    # Bekker columns: book_bounds is nearly the whole segment list, and
    # chapter_bounds has no Homeric analogue, so it is always emitted empty
    # rather than faked.
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

    offsets = {
        # Doubles as a build fingerprint: every artifact indexed by global
        # offset must agree on it, or they were built from different runs.
        "token_count": token_count,
        "seg_base_offset": seg_base_offset,
        "segments": seg_coords,
        "book_bounds": book_bounds,
        "chapter_bounds": [],  # no Homeric analogue; never faked
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
                "chapter_bounds": [],
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
