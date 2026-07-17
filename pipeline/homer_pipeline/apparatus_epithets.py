"""Computed apparatus stage (Phase 4d, docs/APPARATUS-SCHEMAS.md): per-work
noun-epithet formula detection.

Emits build/dist/<work>/epithets.json: a JSON array of
`{entity, formulas: [{text, lemmaKeys, count, refs: [{book, line}]}]}`, one
entry per apparatus/characters.json entity that has at least one qualifying
formula. Fully mechanical n-gram counting over lemma sequences -- no
authored/hand-curated content, no philological judgment beyond the
deterministic algorithm below.

Algorithm
---------
1. For each line of the work, resolve every token's lemma. Ordinary
   (lowercase-surface) tokens use the work's own build/dist/<work>/
   analyses.json (already emitted by stage4/stage7). CAPITALIZED tokens are
   re-resolved via `_capitalized_lemma_overrides` instead -- see that
   function's docstring for why: stage4's own resolution silently prefers a
   homonymous common-word reading over a proper name for some tokens
   (Τηλέμαχος/τηλέμαχος is a real example in this corpus), which would make
   this stage miss real characters. That override is local to this stage and
   does not touch stage4/analyses.json.
2. Each apparatus/characters.json entity's headword (`greek`, nominative) is
   resolved to a Diogenes lemma the same way, so entity and token lemmas are
   directly comparable regardless of dialect-spelling normalization (e.g.
   Ἥρη -> Diogenes' Attic-normalized lemma, not a literal re-encoding of the
   Ionic spelling).
3. For every line containing an occurrence of an entity's lemma, every
   contiguous window of MIN_FORMULA_LEN..MAX_FORMULA_LEN tokens that covers
   that occurrence is a formula candidate (windows never cross line
   boundaries). Candidates are grouped by their LEMMA sequence (inflection-
   insensitive matching, per the phase brief) and kept when they recur
   MIN_FORMULA_COUNT+ times within the work. `text` is the most frequent
   concrete surface rendering among that lemma-sequence's occurrences (ties
   broken by first occurrence in corpus reading order, which is
   deterministic).
4. Maximal-formula pruning (explosion control): a shorter candidate is
   dropped when a strictly longer *accepted* candidate contains it as a
   contiguous sub-sequence AND has the IDENTICAL set of (book, line) refs --
   i.e. it adds no information beyond the longer entry. A shorter candidate
   whose ref set differs (even partially) from any longer super-sequence is
   kept, since it represents a genuinely broader recurring collocation.
   MAX_FORMULA_LEN caps window growth; no Homeric noun-epithet formula in
   this corpus needs more than a handful of words to see the effect, and the
   cap keeps the per-entity scan bounded.

Determinism: the only per-run-varying Python feature this module touches is
`set` object identity/iteration (hash-seed-dependent in CPython); every set
built here is used solely for O(1) membership tests, never iterated to
produce output order, so results are byte-identical across runs (see the
stage's determinism test).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .beta import lookup_variants, to_beta_key
from .config import BUILD_DIR, REPO_ROOT, Manifest
from .stage4_morphology import scan_analyses

APPARATUS_DIR = REPO_ROOT / "apparatus"
CHARACTERS_PATH = APPARATUS_DIR / "characters.json"

MIN_FORMULA_LEN = 2
MAX_FORMULA_LEN = 6
MIN_FORMULA_COUNT = 3


def load_characters() -> list[dict]:
    return json.loads(CHARACTERS_PATH.read_text(encoding="utf-8"))["characters"]


def entity_head_word(greek: str) -> str:
    """The name itself, for entities whose `greek` field disambiguates a
    homonym with a trailing epithet/patronymic (e.g. 'Αἴας Τελαμώνιος' /
    'Αἴας Ὀϊλῆος' -- the two Ajaxes). Known, reported (not hacked around)
    limitation: such entries share their head lemma, so this stage cannot
    mechanically tell their formulas apart by name alone."""
    return greek.split()[0]


def _load_book_lines(dist_dir: Path) -> list[tuple[int, int, list[dict]]]:
    """[(book, line_n, tokens)] for every line in the work, in the corpus's
    own emitted order (book-NN.json filename order, then line order --
    already ascending)."""
    out = []
    for path in sorted(dist_dir.glob("book-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        book_n = doc["book"]
        for seg in doc["segments"]:
            for line in seg["greek"]:
                out.append((book_n, line["n"], line["tokens"]))
    return out


def _capitalized_variants(key: str) -> list[str]:
    """Capitalized ('*'-prefixed) Beta Code lookup variants for a key,
    dropping any plain-lowercase alternatives lookup_variants would also try
    -- see capitalized_lemma_overrides' docstring for why the plain variant
    must never be consulted here."""
    return [v for v in lookup_variants(key, capitalized=True) if v.startswith("*")]


def token_capitalized_variant_map(
    lines: list[tuple[int, int, list[dict]]],
) -> dict[str, list[str]]:
    """Token Beta Code key -> ranked capitalized lookup variants, for every
    token whose surface text is capitalized in the source."""
    cap_keys = {
        tok["k"] for _, _, tokens in lines for tok in tokens if tok["t"][:1].isupper()
    }
    return {k: _capitalized_variants(k) for k in cap_keys}


def entity_capitalized_variant_map(characters: list[dict]) -> dict[str, list[str]]:
    """Entity id -> ranked capitalized lookup variants for its nominative
    headword (entity_head_word)."""
    return {
        char["id"]: _capitalized_variants(to_beta_key(entity_head_word(char["greek"])))
        for char in characters
    }


def resolve_lemma_map(
    variant_map: dict[str, list[str]], found: dict[str, list[dict]]
) -> dict[str, str]:
    """id/key -> lemma, taking the first variant (in each entry's own ranked
    order) present in `found`. Pure and testable without touching Diogenes:
    `found` is whatever scan_capitalized_variants (or a fixture) returned."""
    resolved: dict[str, str] = {}
    for key, variants in variant_map.items():
        hit = next((v for v in variants if v in found), None)
        if hit is not None:
            resolved[key] = found[hit][0]["lemma"]
    return resolved


def scan_capitalized_variants(manifest: Manifest, needed: set[str]) -> dict[str, list[dict]]:
    """One targeted pass over Diogenes' greek-analyses.txt for every needed
    capitalized Beta Code key -- shared by token-key and entity-headword
    resolution so a work needs exactly one scan of the (120MB) source file,
    not one per entity.

    Why the override exists at all: build/dist/<work>/analyses.json
    (stage4/stage7) tries the plain lowercase variant of a token's key FIRST
    regardless of whether the token was actually capitalized in the source
    text (see beta.lookup_variants / stage4_morphology.run's "first variant
    wins" resolution). So a proper name that happens to share a Beta Code
    key with an ordinary word loses to the common-word reading corpus-wide
    -- e.g. Τηλέμαχος ('Telemachus') and τηλέμαχος ('fighting from afar')
    share the key 'thle/maxos', and every occurrence resolves to the
    adjective in analyses.json even where the source text plainly
    capitalizes the name. That is stage4's correct, general-purpose,
    corpus-wide behavior and out of this stage's blast radius to change;
    this function instead does its own narrower, capitalized-only
    resolution against the same Diogenes source (reusing
    stage4_morphology.scan_analyses), used only by this stage.

    Keys not found in Diogenes at all are simply absent from the result;
    callers fall back to the work's regular analyses.json lemma for token
    keys (ordinary capitalized common words, sentence-initial happenstance,
    etc.), or report the entity as unresolved (run()'s report), never
    patched over with a hand-curated override."""
    analyses_path = manifest.diogenes_data() / "greek-analyses.txt"
    return scan_analyses(analyses_path, needed)


def _line_lemmas(
    tokens: list[dict], analyses: dict[str, list[dict]], cap_overrides: dict[str, str]
) -> tuple[list[str], list[str]]:
    """Per-token (lemma, surface) sequences for one line. Capitalized tokens
    prefer cap_overrides (proper-noun-first resolution); everything else
    uses the work's regular analyses.json. A token with no resolvable
    analysis anywhere falls back to its own raw Beta Code key so it still
    occupies a slot in the sequence -- harmless, since an unresolved key is
    effectively unique and cannot spuriously match a real lemma."""
    lemmas: list[str] = []
    surfaces: list[str] = []
    for tok in tokens:
        k = tok["k"]
        surfaces.append(tok["t"])
        if tok["t"][:1].isupper() and k in cap_overrides:
            lemmas.append(cap_overrides[k])
            continue
        entries = analyses.get(k)
        lemmas.append(entries[0]["lemma"] if entries else k)
    return lemmas, surfaces


def _formula_windows(
    lemmas: list[str], surfaces: list[str], book_n: int, line_n: int, target_lemma: str
) -> list[tuple[tuple[str, ...], tuple[str, ...], int, int]]:
    """Every (lemma_tuple, surface_tuple, book, line) window of
    MIN_FORMULA_LEN..MAX_FORMULA_LEN tokens, within this one line, that
    covers an occurrence of target_lemma."""
    length = len(lemmas)
    out = []
    for i, lemma in enumerate(lemmas):
        if lemma != target_lemma:
            continue
        max_n = min(MAX_FORMULA_LEN, length)
        for n in range(MIN_FORMULA_LEN, max_n + 1):
            start_lo = max(0, i - n + 1)
            start_hi = min(i, length - n)
            for start in range(start_lo, start_hi + 1):
                out.append(
                    (
                        tuple(lemmas[start:start + n]),
                        tuple(surfaces[start:start + n]),
                        book_n,
                        line_n,
                    )
                )
    return out


def _is_contiguous_subsequence(short: tuple, long: tuple) -> bool:
    ls, ll = len(short), len(long)
    if ls >= ll:
        return short == long and ls == ll
    return any(long[i:i + ls] == short for i in range(ll - ls + 1))


def formulas_from_occurrences(
    occurrences: list[tuple[tuple[str, ...], tuple[str, ...], int, int]],
) -> list[dict]:
    """Group formula-window occurrences by lemma sequence, keep those
    recurring MIN_FORMULA_COUNT+ times, apply maximal-formula pruning (see
    module docstring), and shape the result per docs/APPARATUS-SCHEMAS.md."""
    by_lemma: dict[tuple[str, ...], list[tuple[tuple[str, ...], int, int]]] = defaultdict(list)
    for lemma_tuple, surface_tuple, book_n, line_n in occurrences:
        by_lemma[lemma_tuple].append((surface_tuple, book_n, line_n))

    candidates = {lt: occ for lt, occ in by_lemma.items() if len(occ) >= MIN_FORMULA_COUNT}

    def ref_set(occ) -> frozenset[tuple[int, int]]:
        return frozenset((b, l) for _, b, l in occ)

    # Domination only ever fires between candidates sharing the IDENTICAL
    # ref set (see module docstring), so bucketing already-accepted lemma
    # sequences by their ref set turns the pruning pass from
    # O(candidates^2) into O(one small-bucket scan per candidate) -- the
    # same result, without re-checking every unrelated accepted formula.
    accepted: list[tuple[tuple[str, ...], list]] = []
    accepted_by_refset: dict[frozenset, list[tuple[str, ...]]] = defaultdict(list)
    for lemma_tuple in sorted(candidates, key=lambda t: (-len(t), t)):
        occ = candidates[lemma_tuple]
        rs = ref_set(occ)
        dominated = any(
            _is_contiguous_subsequence(lemma_tuple, acc_lt)
            for acc_lt in accepted_by_refset.get(rs, ())
        )
        if not dominated:
            accepted.append((lemma_tuple, occ))
            accepted_by_refset[rs].append(lemma_tuple)

    formulas = []
    for lemma_tuple, occ in accepted:
        surface_counts = Counter(" ".join(surface_tuple) for surface_tuple, _, _ in occ)
        text = surface_counts.most_common(1)[0][0]
        formulas.append(
            {
                "text": text,
                "lemmaKeys": list(lemma_tuple),
                "count": len(occ),
                "refs": [{"book": b, "line": l} for _, b, l in occ],
            }
        )
    formulas.sort(key=lambda f: (-f["count"], f["text"]))
    return formulas


def run(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    dist_dir = BUILD_DIR / "dist" / work_id
    analyses_out_path = dist_dir / "analyses.json"

    lines_raw = _load_book_lines(dist_dir)
    analyses = json.loads(analyses_out_path.read_text(encoding="utf-8"))
    characters = load_characters()

    # One combined Diogenes scan for every capitalized token variant AND
    # every entity headword variant this work could need -- see
    # scan_capitalized_variants' docstring. Scanning per-entity here would
    # mean re-reading the 120MB source file up to 101 times.
    token_variants = token_capitalized_variant_map(lines_raw)
    entity_variants = entity_capitalized_variant_map(characters)
    needed = {v for vs in token_variants.values() for v in vs}
    needed |= {v for vs in entity_variants.values() for v in vs}
    found = scan_capitalized_variants(manifest, needed)

    cap_overrides = resolve_lemma_map(token_variants, found)
    entity_lemma = resolve_lemma_map(entity_variants, found)
    unresolved_entities = [c["id"] for c in characters if c["id"] not in entity_lemma]

    lines: list[tuple[int, int, list[str], list[str], set[str]]] = []
    for book_n, line_n, tokens in lines_raw:
        lemmas, surfaces = _line_lemmas(tokens, analyses, cap_overrides)
        lines.append((book_n, line_n, lemmas, surfaces, set(lemmas)))

    entities_out = []
    for char in characters:
        target = entity_lemma.get(char["id"])
        if target is None:
            continue
        occurrences = []
        for book_n, line_n, lemmas, surfaces, lemma_set in lines:
            if target not in lemma_set:
                continue
            occurrences.extend(_formula_windows(lemmas, surfaces, book_n, line_n, target))
        formulas = formulas_from_occurrences(occurrences)
        if formulas:
            entities_out.append({"entity": char["id"], "formulas": formulas})

    entities_out.sort(key=lambda e: e["entity"])
    out_path = dist_dir / "epithets.json"
    out_path.write_text(
        json.dumps(entities_out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return {
        "work": work_id,
        "path": out_path,
        "entities_total": len(characters),
        "entities_with_formulas": len(entities_out),
        "entities_unresolved": unresolved_entities,
        "total_formulas": sum(len(e["formulas"]) for e in entities_out),
    }
